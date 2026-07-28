using System.Security.Cryptography;
using System.Xml.Linq;
using Orbyss.ProgramKit.Architecture.Schemas;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;
using Orbyss.ProgramKit.Development.Schemas;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Quality.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.ConformanceTests.Governance;

[TestClass]
public sealed class SelfHostedBootstrapConformanceTests
{
    private static readonly IReadOnlyDictionary<string, string> ExpectedArtifactDigests =
        new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["architecture-design.json"] =
                "c5ed7f0d4f278181f138dd5a4dcb9300502dd85aea8be7271c7da15762439327",
            ["implementation-plan.json"] =
                "0b03457928ae0b7bfb917c0b6024ea56cf2451d14ba540b8cfe00f60cc64823b",
            ["architecture-design.md"] =
                "947ddb574fb8d9ffe94fe7fa94f7c543af90e159a9bf609283510dc21f74f6b2",
            ["implementation-plan.md"] =
                "b1e60623624ced9ede4c529d1c6d80022a6894923425d384c5863c22db5f595b",
            ["dependency-graph.dot"] =
                "2169b8582faa0819545cfbbe2890bb19ec1c870169a1d0bf4432f463dec7bd77",
            ["forbidden-reference-graph.dot"] =
                "194a8498eb3d68a76cd32700acfaa4f7959fa003daba029d2db4cfff5c818ed9",
            ["version-map-graph.dot"] =
                "d23d6efbb98a6722c60bfac7f6d5ff57617ca3e293353e96f915788b45633c9d",
            ["bootstrap-comparison.json"] =
                "b95742ad58a221f9a38bef3fcd2ca3496bc0f4bab2caf5e86e04c802e7ff2c6c",
            ["approval-relationship.json"] =
                "8dc3908aa7d5693d9e6af4ad8b597f4a243eaf61ac40c2c47c6ab9bf44467834",
            ["request-evidence.md"] =
                "f0bd9c1aab4b78c82345dfa7c6714e3df59cb540aa66454121cc701893afec30",
            ["development-receipt.json"] =
                "0e1713d680e8052484f35bf9819a6fd945a0c629fe3e16ecbd5e03c0b61868ff",
        };

    [TestMethod]
    public void CanonicalSelfHostedInstancesValidateAgainstExactProgramKitSchemas()
    {
        SelfHostedCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
            new QualitySchemaModule(),
            new PlanningSchemaModule(),
            new DevelopmentSchemaModule(),
        ]);
        JsonSchemaWorkbenchValidator validator = new(
            new ProgramKitJsonCanonicalizer(),
            new ProgramKitSchemaModuleValidator());

        AssertValid(
            validator,
            schemas,
            "architecture-design.json",
            "architecture-design");
        AssertValid(
            validator,
            schemas,
            "implementation-plan.json",
            "implementation-plan");
        AssertValid(
            validator,
            schemas,
            "development-receipt.json",
            "development-receipt");
    }

    [TestMethod]
    public void SelfHostedArtifactsAndHistoricalReceiptRemainExact()
    {
        foreach (var expected in ExpectedArtifactDigests)
        {
            Assert.AreEqual(
                expected.Value,
                Digest(ConformanceInputs.ReadBytes(
                    string.Concat("SelfHosted/", expected.Key))),
                expected.Key);
        }

        var requestDigest = Digest(ConformanceInputs.ReadBytes(
            "SelfHosted/request-evidence.md"));
        var receipt = ConformanceInputs.Read("SelfHosted/development-receipt.json");

        Assert.Contains(
            "\"digest\": \"sha256:ba64247ac92a24b750d4dd2537efed517189c1497dc3ec64930201e8e612d034\"",
            receipt,
            StringComparison.Ordinal);
        Assert.Contains(
            string.Concat("\"digest\": \"sha256:", requestDigest, "\""),
            receipt,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"suppliedAt\": \"2026-07-24T23:51:48.573Z\"",
            receipt,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"kind\": \"completed\"",
            receipt,
            StringComparison.Ordinal);
    }

    [TestMethod]
    public void DependencyProjectionMatchesCurrentProgramKitProjectReferences()
    {
        var expectedEdges = ConformanceInputs
            .Files("Projects", "*.csproj")
            .SelectMany(ProjectEdges)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var projectedEdges = ConformanceInputs
            .Read("SelfHosted/dependency-graph.dot")
            .Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Select(static line => line.Trim())
            .Where(static line =>
                line.Contains(" -> ", StringComparison.Ordinal) &&
                !line.Contains('[', StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(expectedEdges, projectedEdges);
    }

    [TestMethod]
    public void ComparisonAndRelationshipReportsPreserveHistoryAndAuthority()
    {
        var comparison = ConformanceInputs.Read(
            "SelfHosted/bootstrap-comparison.json");
        var relationship = ConformanceInputs.Read(
            "SelfHosted/approval-relationship.json");

        Assert.Contains(
            "\"bootstrapRemainsIntact\": true",
            comparison,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"retroactiveCapabilityAuthorshipClaimed\": false",
            comparison,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"newApprovalMinted\": false",
            comparison,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"classification\": \"implementation-finding\"",
            comparison,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"relationshipKind\": \"derived-from-approved-bootstrap-without-new-approval\"",
            relationship,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"createsApproval\": false",
            relationship,
            StringComparison.Ordinal);
        Assert.Contains(
            "\"supersessionState\": \"active\"",
            relationship,
            StringComparison.Ordinal);
    }

    private static void AssertValid(
        JsonSchemaWorkbenchValidator validator,
        SelfHostedCompositeSchemaModule schemas,
        string instanceName,
        string schemaName)
    {
        var schemaReference = schemas.Resources.Single(resource =>
            string.Equals(
                resource.SchemaReference.Identity.Name,
                schemaName,
                StringComparison.Ordinal) &&
            string.Equals(
                resource.SchemaReference.Version.Value,
                "1.0.0",
                StringComparison.Ordinal)).SchemaReference;
        var result = validator.Validate(
            ConformanceInputs.ReadBytes(
                string.Concat("SelfHosted/", instanceName)),
            schemas,
            schemaReference,
            JsonSerializationLimits.Default);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        ": ",
                        diagnostic.Message))));
    }

    private static IEnumerable<string> ProjectEdges(string projectPath)
    {
        var projectName = ProgramKitName(
            Path.GetFileNameWithoutExtension(projectPath));
        var document = XDocument.Load(projectPath, LoadOptions.None);
        return document
            .Descendants("ProjectReference")
            .Where(reference =>
                reference.Attribute("Include") is not null &&
                !string.Equals(
                    reference.Attribute("OutputItemType")?.Value,
                    "Analyzer",
                    StringComparison.Ordinal))
            .Select(reference => string.Concat(
                "\"",
                projectName,
                "\" -> \"",
                ProgramKitName(Path.GetFileNameWithoutExtension(
                    reference.Attribute("Include")!.Value)),
                "\";"));
    }

    private static string ProgramKitName(string projectName)
    {
        const string prefix = "Orbyss.ProgramKit.";
        return projectName.StartsWith(prefix, StringComparison.Ordinal)
            ? projectName[prefix.Length..]
            : projectName;
    }

    private static string Digest(byte[] bytes) =>
        Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

}

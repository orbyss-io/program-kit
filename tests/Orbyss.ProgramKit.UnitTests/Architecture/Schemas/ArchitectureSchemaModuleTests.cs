using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Architecture.Schemas;

[TestClass]
public sealed class ArchitectureSchemaModuleTests
{
    private static readonly string[] ExpectedResourceNames =
    [
        "architecture-design.schema.json",
        "artifact-decision.schema.json",
        "dotnet-target-profile.schema.json",
        "structural-pattern-catalog.schema.json",
        "architecture-design-2.0.0.schema.json",
        "architecture-design-0.1.0-alpha.2.schema.json",
        "static-conformance-disposition.schema.json",
        "static-conformance-disposition-0.1.0-alpha.1.schema.json",
    ];

    [TestMethod]
    public void ModuleExplicitlyRegistersEveryOwnedSchemaInStableOrder()
    {
        ArchitectureSchemaModule module = new();
        ProgramKitSchemaModuleValidator sut = new();

        var result = sut.Validate(module);

        Assert.AreSequenceEqual(
            ExpectedResourceNames,
            module.Resources.Select(static resource => resource.ResourceName));
        Assert.IsTrue(result.IsValid);
    }

    [TestMethod]
    public void EveryRegisteredResourceOpensByItsExactReferenceAndMatchesItsDigest()
    {
        ArchitectureSchemaModule module = new();

        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var actualDigest = Convert.ToHexString(SHA256.HashData(stream));
            var expectedDigest =
                resource.SchemaReference.Digest.Value["sha256:".Length..].ToUpperInvariant();

            Assert.AreEqual(expectedDigest, actualDigest, resource.ResourceName);
        }
    }

    [TestMethod]
    public void DispositionSchemaAcceptsExplicitEmptyAndRejectsBlockedAsEmpty()
    {
        ArchitectureCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
        ]);
        var schema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:static-conformance-disposition" &&
            resource.SchemaReference.Version.Value == "1.0.0");
        JsonSchemaWorkbenchValidator sut = CreateValidator();
        var acceptedEmpty = Encoding.UTF8.GetBytes(
            DispositionJson(
                "not-justified",
                "[]",
                "[]",
                ReferenceJson(
                    "pkid:decision:consumer:accepted-empty-static-conformance"),
                "[]"));
        var blockedAsEmpty = Encoding.UTF8.GetBytes(
            DispositionJson(
                "blocked-unavailable",
                "[]",
                "[]",
                ReferenceJson(
                    "pkid:decision:consumer:accepted-empty-static-conformance"),
                "[]"));
        var programKitReuse = File.ReadAllBytes(Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "migrations",
            "fixtures",
            "program-kit-reuse-existing.static-conformance-disposition.json"));

        var acceptedResult = Validate(sut, acceptedEmpty, schemas, schema);
        var blockedResult = Validate(sut, blockedAsEmpty, schemas, schema);
        var reuseResult = Validate(sut, programKitReuse, schemas, schema);

        Assert.IsTrue(acceptedResult.IsValid, Format(acceptedResult));
        Assert.IsTrue(reuseResult.IsValid, Format(reuseResult));
        Assert.IsFalse(blockedResult.IsValid);
    }

    [TestMethod]
    public void ArchitectureV2RequiresOneNonNullExactDispositionReference()
    {
        ArchitectureCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
        ]);
        var schema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:architecture-design" &&
            resource.SchemaReference.Version.Value == "2.0.0");
        JsonSchemaWorkbenchValidator sut = CreateValidator();
        var designPath = Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "architecture-design.json");
        var source = JsonNode.Parse(File.ReadAllBytes(designPath))!.AsObject();
        var missing = Encoding.UTF8.GetBytes(source.ToJsonString());
        source["staticConformanceDisposition"] = JsonNode.Parse(
            ReferenceJson(
                "pkid:static-conformance-disposition:program-kit:reusable-csharp-build-gates"));
        var exact = Encoding.UTF8.GetBytes(source.ToJsonString());
        source["staticConformanceDisposition"] = null;
        var explicitNull = Encoding.UTF8.GetBytes(source.ToJsonString());

        var missingResult = Validate(sut, missing, schemas, schema);
        var exactResult = Validate(sut, exact, schemas, schema);
        var nullResult = Validate(sut, explicitNull, schemas, schema);

        Assert.IsFalse(missingResult.IsValid);
        Assert.IsTrue(exactResult.IsValid, Format(exactResult));
        Assert.IsFalse(nullResult.IsValid);
    }

    [TestMethod]
    public void AlphaAliasesResolveExactLegacyWireShapes()
    {
        ArchitectureCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
        ]);
        var designSchema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:architecture-design" &&
            resource.SchemaReference.Version.Value == "0.1.0-alpha.2");
        var dispositionSchema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:static-conformance-disposition" &&
            resource.SchemaReference.Version.Value == "0.1.0-alpha.1");
        var root = FindProgramKitRoot();
        var designSource = JsonNode.Parse(File.ReadAllBytes(Path.Combine(
            root.FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "architecture-design.json")))!.AsObject();
        designSource["staticConformanceDisposition"] = JsonNode.Parse(
            ReferenceJson(
                "pkid:static-conformance-disposition:program-kit:alpha-version-transition"));
        var design = Encoding.UTF8.GetBytes(designSource.ToJsonString());
        var disposition = File.ReadAllBytes(Path.Combine(
            root.FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "migrations",
            "fixtures",
            "program-kit-reuse-existing.static-conformance-disposition.json"));
        JsonSchemaWorkbenchValidator sut = CreateValidator();

        var designResult = Validate(sut, design, schemas, designSchema);
        var dispositionResult =
            Validate(sut, disposition, schemas, dispositionSchema);

        Assert.IsTrue(designResult.IsValid, Format(designResult));
        Assert.IsTrue(dispositionResult.IsValid, Format(dispositionResult));
    }

    [TestMethod]
    public void DispositionNormalizationAndDigestAreDeterministic()
    {
        var path = Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "migrations",
            "fixtures",
            "program-kit-reuse-existing.static-conformance-disposition.json");
        var bytes = File.ReadAllBytes(path);
        ProgramKitJsonCanonicalizer sut = new();
        var limits = new JsonSerializationLimits(
            MaxUtf8Bytes: 1_000_000,
            MaxDepth: 64,
            MaxTokens: 100_000,
            MaxObjectMembers: 100_000,
            MaxBufferedObjectBytes: 1_000_000);

        var first = sut.Canonicalize(bytes, limits);
        var second = sut.Canonicalize(bytes, limits);

        Assert.AreEqual(first, second);
        Assert.AreEqual(first.Digest, second.Digest);
        Assert.AreSequenceEqual(first.ToArray(), second.ToArray());
    }

    private static JsonSchemaWorkbenchValidator CreateValidator() =>
        new(
            new ProgramKitJsonCanonicalizer(),
            new ProgramKitSchemaModuleValidator());

    private static ProgramKitValidationResult Validate(
        JsonSchemaWorkbenchValidator validator,
        byte[] value,
        IProgramKitSchemaModule module,
        ProgramKitSchemaResource schema) =>
        validator.Validate(
            value,
            module,
            schema.SchemaReference,
            new JsonSerializationLimits(
                MaxUtf8Bytes: 1_000_000,
                MaxDepth: 64,
                MaxTokens: 100_000,
                MaxObjectMembers: 100_000,
                MaxBufferedObjectBytes: 1_000_000));

    private static string DispositionJson(
        string disposition,
        string selections,
        string linkedDesigns,
        string emptyAcceptance,
        string blockers) =>
        $$"""
        {
          "softwareDesign": {{ReferenceJson("pkid:design:consumer:software")}},
          "invariantAllocations": [
            {
              "identity": "pkid:invariant:consumer:boundary",
              "invariant": "Consumer boundaries are explicit.",
              "layer": "architecture-test",
              "rationale": "The architecture graph is the reliable source."
            }
          ],
          "disposition": "{{disposition}}",
          "gateSelections": {{selections}},
          "linkedGateDesigns": {{linkedDesigns}},
          "rationale": "The human selected this exact disposition.",
          "residualRisks": ["Runtime behavior remains outside static proof."],
          "nonStaticClaims": ["Business correctness is not statically proven."],
          "decisionSource": {
            "source": {{ReferenceJson("pkid:decision-source:consumer:design")}},
            "jsonPointer": "/staticConformanceDisposition"
          },
          "emptySelectionAcceptance": {{emptyAcceptance}},
          "blockers": {{blockers}}
        }
        """;

    private static string ReferenceJson(string identity) =>
        $$"""
        {
          "identity": "{{identity}}",
          "version": "1.0.0",
          "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
        """;

    private static DirectoryInfo FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Program Kit root was not found.");
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}

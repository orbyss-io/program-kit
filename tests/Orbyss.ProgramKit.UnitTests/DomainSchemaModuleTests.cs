using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Development;
using Orbyss.ProgramKit.Planning;
using Orbyss.ProgramKit.Quality;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class DomainSchemaModuleTests
{
    [TestMethod]
    public void DomainSchemaModulesRegisterExactReadableResourcesWithCompleteSidecars()
    {
        (IProgramKitSchemaModule Module, string Owner, int Count)[] modules =
        [
            (
                QualitySchemaModule.Instance,
                "pkid:package:program-kit:quality",
                5),
            (
                PlanningSchemaModule.Instance,
                "pkid:package:program-kit:planning",
                3),
            (
                DevelopmentSchemaModule.Instance,
                "pkid:package:program-kit:development",
                4),
        ];

        foreach (var (module, owner, count) in modules)
        {
            var validation = new ProgramKitSchemaModuleValidator().Validate(module);
            Assert.IsTrue(validation.IsValid, Format(validation));
            Assert.HasCount(count, module.Resources);

            foreach (var resource in module.Resources)
            {
                Assert.AreEqual(owner, resource.OwnerId.Value);
                Assert.AreEqual(ArtifactStatus.Implemented, resource.Status);
                Assert.IsFalse(resource.Consumers.IsDefaultOrEmpty);
                Assert.IsNotNull(resource.Provenance);
                Assert.IsFalse(resource.Provenance.SourceInputs.IsDefaultOrEmpty);
                Assert.IsFalse(string.IsNullOrWhiteSpace(resource.Provenance.Producer.Value));
                Assert.IsFalse(string.IsNullOrWhiteSpace(resource.Provenance.CorrelationId));
                Assert.IsNotNull(resource.Compatibility);
                Assert.IsFalse(resource.Compatibility.Dimensions.IsDefaultOrEmpty);
                Assert.IsFalse(resource.Compatibility.MigrationReferences.IsDefault);

                using var stream = module.OpenRead(resource.SchemaReference);
                var digest = string.Concat(
                    "sha256:",
                    Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant());
                Assert.AreEqual(resource.SchemaReference.Digest.Value, digest);
            }
        }
    }

    [TestMethod]
    public void DomainDiagnosticCatalogsPublishOnlyCanonicalStableFamilies()
    {
        AssertCatalog(
            QualityDiagnosticIds.All,
            QualityDiagnosticCatalog.Definitions,
            "PKQLT");
        AssertCatalog(
            PlanningDiagnosticIds.All,
            PlanningDiagnosticCatalog.Definitions,
            "PKPLN");
        AssertCatalog(
            DevelopmentDiagnosticIds.All,
            DevelopmentDiagnosticCatalog.Definitions,
            "PKDEV");
    }

    private static void AssertCatalog(
        IReadOnlyCollection<string> identifiers,
        IReadOnlyCollection<ProgramKitDiagnosticDefinition> definitions,
        string prefix)
    {
        Assert.IsTrue(identifiers.Count > 0);
        Assert.AreEqual(identifiers.Count, identifiers.Distinct(StringComparer.Ordinal).Count());
        Assert.IsTrue(identifiers.All(identifier =>
            identifier.StartsWith(prefix, StringComparison.Ordinal)));
        CollectionAssert.AreEqual(
            identifiers.ToArray(),
            definitions.Select(definition => definition.Id).ToArray());
        Assert.IsTrue(definitions.All(definition =>
            definition.DefaultSeverity == ProgramKitDiagnosticSeverity.Error));
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}

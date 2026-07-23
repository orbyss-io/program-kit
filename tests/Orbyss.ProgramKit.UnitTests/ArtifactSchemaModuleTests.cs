using System.Collections.Immutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArtifactSchemaModuleTests
{
    [TestMethod]
    public void ArtifactSchemaModuleOpensEveryExactDigestBoundResource()
    {
        var module = ArtifactsSchemaModule.Instance;
        var validation = new ProgramKitSchemaModuleValidator().Validate(module);

        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(diagnostic => diagnostic.Message)));
        Assert.HasCount(8, module.Resources);
        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var actual = string.Concat(
                "sha256:",
                Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant());
            Assert.AreEqual(
                resource.SchemaReference.Digest.Value,
                actual,
                resource.ResourceName);
        }
    }

    [TestMethod]
    public void SchemaSidecarRequiresConsumersAndSourceProvenance()
    {
        var resource = ArtifactsSchemaModule.Instance.Resources[0];
        var incomplete = resource with
        {
            Consumers = [],
            Provenance = resource.Provenance with { SourceInputs = [] },
        };

        var result = new ProgramKitSchemaModuleValidator().Validate(
            new TestSchemaModule(incomplete));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidSchemaModule &&
            diagnostic.Path == "/resources/0/consumers"));
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidSchemaModule &&
            diagnostic.Path == "/resources/0/provenance/sourceInputs"));
    }

    private sealed class TestSchemaModule(
        ProgramKitSchemaResource resource) : IProgramKitSchemaModule
    {
        public ProgramKitIdentifier Identity { get; } =
            ProgramKitIdentifier.Parse("pkid:catalog:program-kit:test-schemas");

        public SemanticVersion Version { get; } = SemanticVersion.Parse("1.0.0");

        public ImmutableArray<ProgramKitSchemaResource> Resources { get; } =
            [resource];

        public Stream OpenRead(ArtifactReference schemaReference) =>
            throw new NotSupportedException(
                string.Concat("No stream is available for ", schemaReference.Identity.Value));
    }
}

using System.Security.Cryptography;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Schemas;

[TestClass]
public sealed class ArtifactsVersioningSchemaModuleTests
{
    private static readonly string[] VersioningResourceNames =
    [
        "version-intent-inventory-0.1.0-alpha.1.schema.json",
        "version-intent-inventory-0.1.0-alpha.2.schema.json",
        "alpha-version-progression-0.1.0-alpha.1.schema.json",
    ];

    [TestMethod]
    public void ModuleRegistersExactAlphaVersioningSchemas()
    {
        ArtifactsSchemaModule module = new();
        ProgramKitSchemaModuleValidator validator = new();
        var resources = module.Resources
            .Where(resource => VersioningResourceNames.Contains(
                resource.ResourceName,
                StringComparer.Ordinal))
            .ToArray();

        var result = validator.Validate(module);

        Assert.IsTrue(result.IsValid, Format(result));
        Assert.AreSequenceEqual(
            VersioningResourceNames,
            resources.Select(static resource => resource.ResourceName));
    }

    [TestMethod]
    public void VersioningSchemaStreamsMatchTheirRegisteredDigests()
    {
        ArtifactsSchemaModule module = new();
        var resources = module.Resources
            .Where(resource => VersioningResourceNames.Contains(
                resource.ResourceName,
                StringComparer.Ordinal))
            .ToArray();

        foreach (var resource in resources)
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

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(
                    diagnostic.Id,
                    " ",
                    diagnostic.Path,
                    " ",
                    diagnostic.Message)));
}

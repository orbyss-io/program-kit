using System.Security.Cryptography;

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
}

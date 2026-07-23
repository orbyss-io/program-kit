using System.Security.Cryptography;
using Orbyss.ProgramKit.Architecture;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

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
        var module = ArchitectureSchemaModule.Instance;

        CollectionAssert.AreEqual(
            ExpectedResourceNames,
            module.Resources.Select(static resource => resource.ResourceName).ToArray());
        Assert.IsTrue(new ProgramKitSchemaModuleValidator().Validate(module).IsValid);
    }

    [TestMethod]
    public void EveryRegisteredResourceOpensByItsExactReferenceAndMatchesItsDigest()
    {
        var module = ArchitectureSchemaModule.Instance;

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

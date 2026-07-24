using System.Security.Cryptography;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Schemas;

[TestClass]
public sealed class TasksCoreSchemaModuleTests
{
    [TestMethod]
    public void ModuleRegistersEightExactReadableDigestBoundResources()
    {
        TasksCoreSchemaModule module = new();
        ProgramKitSchemaModuleValidator validator = new();

        var validation = validator.Validate(module);

        Assert.IsTrue(validation.IsValid);
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
}

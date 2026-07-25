using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Operations.Contracts;

[TestClass]
public sealed class OperationsSchemaModuleTests
{
    [TestMethod]
    public void ModuleRegistersOnlyExactReadableOperationsSchemas()
    {
        OperationsSchemaModule module = new();
        ProgramKitSchemaModuleValidator validator = new();

        var validation = validator.Validate(module);

        Assert.IsTrue(validation.IsValid);
        Assert.HasCount(7, module.Resources);
        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var digest = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(stream)));
            Assert.AreEqual(resource.SchemaReference.Digest.Value, digest);
        }
    }
}

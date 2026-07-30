using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts.Schemas;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
public sealed class OpenConsoleContractTests
{
    [TestMethod]
    public void NeutralSchemaRegistrationAndSemanticDocumentAreValid()
    {
        OpenConsoleSchemaModule module = new();
        ProgramKitSchemaModuleValidator schemaValidator = new();
        OpenConsoleDocumentValidator documentValidator = new();

        var schemaValidation = schemaValidator.Validate(module);
        var documentValidation = documentValidator.Validate(
            DotNetTestContractFactory.ConsoleDocument(
                DotNetTestContractFactory.Shell()));

        Assert.IsTrue(schemaValidation.IsValid);
        Assert.IsTrue(documentValidation.IsValid);
        Assert.HasCount(2, module.Resources);

        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var actualDigest = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(stream)));
            Assert.AreEqual(
                resource.SchemaReference.Digest.Value,
                actualDigest);
        }
    }

    [TestMethod]
    public void NormativeDocumentContainsNoHostImplementationVocabulary()
    {
        OpenConsoleSchemaModule module = new();
        var resource = module.Resources.Single(candidate =>
            candidate.SchemaReference.Version.Value == "1.0.0");
        using var stream = module.OpenRead(resource.SchemaReference);
        using StreamReader reader = new(
            stream,
            Encoding.UTF8,
            detectEncodingFromByteOrderMarks: true);
        var schema = reader.ReadToEnd();
        string[] forbiddenTerms =
        [
            "dotnet",
            "clr",
            "spectre",
            "cshell",
            "assembly",
            "constructor",
            "projectreference",
        ];

        foreach (var forbiddenTerm in forbiddenTerms)
        {
            Assert.DoesNotContain(
                forbiddenTerm,
                schema,
                StringComparison.OrdinalIgnoreCase);
        }
    }
}

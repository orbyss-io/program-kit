using System.Text;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Schemas;

[TestClass]
public sealed class JsonSchemaWorkbenchValidatorTests
{
    [TestMethod]
    public void ValidateUsesTheExactModuleSchemaWithoutExposingDomValues()
    {
        IProgramKitJsonCanonicalizer canonicalizer =
            new ProgramKitJsonCanonicalizer();
        IProgramKitSemanticValidator<IProgramKitSchemaModule> moduleValidator =
            new ProgramKitSchemaModuleValidator();
        var sut = new JsonSchemaWorkbenchValidator(canonicalizer, moduleValidator);
        ArtifactsSchemaModule schemaModule = new();
        var schemaReference = schemaModule.Resources.Single(static resource =>
            resource.SchemaReference.Identity.Name == "version-map").SchemaReference;

        var result = sut.Validate(
            Encoding.UTF8.GetBytes("{}"),
            schemaModule,
            schemaReference,
            JsonSerializationLimits.Default);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.SchemaValidationFailed &&
            diagnostic.Message == "The JSON value does not conform to the selected schema."),
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static diagnostic =>
                    string.Concat(diagnostic.Id, " ", diagnostic.Path, " ", diagnostic.Message))));
    }
}

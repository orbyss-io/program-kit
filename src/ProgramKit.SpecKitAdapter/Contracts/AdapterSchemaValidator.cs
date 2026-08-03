using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public static class AdapterSchemaValidator
{
    public static void Validate(string schemaName, JsonObject document)
    {
        string schemaText = AdapterSchemaResources.ReadAll().TryGetValue(schemaName, out string? found)
            ? found
            : throw new InvalidDataException("The adapter schema is not embedded.");
        using JsonDocument schemaDocument = JsonDocument.Parse(schemaText);
        JsonSchema schema = JsonSchema.Build(schemaDocument.RootElement.Clone(), new BuildOptions
        {
            Dialect = Dialect.Draft202012,
            SchemaRegistry = new Json.Schema.SchemaRegistry(),
        });
        using JsonDocument instance = JsonDocument.Parse(CanonicalDocument.Encode(document));
        EvaluationResults result = schema.Evaluate(instance.RootElement, new EvaluationOptions { OutputFormat = OutputFormat.List });
        if (!result.IsValid) throw new InvalidDataException($"The document does not conform to {schemaName}.");
    }
}

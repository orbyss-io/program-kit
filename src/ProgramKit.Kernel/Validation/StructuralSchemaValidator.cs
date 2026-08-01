using System.Collections.Generic;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Kernel.Validation;

public sealed class StructuralSchemaValidator
{
    private readonly SchemaRegistry registry;

    public StructuralSchemaValidator(SchemaRegistry registry)
    {
        this.registry = registry;
    }

    public IReadOnlyList<string> ValidateRequiredShape(string schemaId, JsonObject instance)
    {
        JsonNode schema = registry.Get(schemaId);
        List<string> failures = new();
        if (schema["required"] is JsonArray required)
        {
            foreach (JsonNode? item in required)
            {
                string name = item?.GetValue<string>() ?? string.Empty;
                if (!instance.ContainsKey(name))
                {
                    failures.Add($"Missing required property: {name}");
                }
            }
        }

        return failures;
    }
}

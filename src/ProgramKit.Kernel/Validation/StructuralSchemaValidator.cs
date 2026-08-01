using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;

namespace Orbyss.ProgramKit.Kernel.Validation;

public sealed class StructuralSchemaValidator
{
    private const int MaximumFailures = 20;
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

    public IReadOnlyList<string> Validate(string schemaId, JsonObject instance)
    {
        JsonSchema schema = registry.GetCompiled(schemaId);
        using JsonDocument document = JsonDocument.Parse(Canonicalization.CanonicalJson.Encode(instance));
        EvaluationResults result = schema.Evaluate(document.RootElement, new EvaluationOptions
        {
            OutputFormat = OutputFormat.List,
        });
        if (result.IsValid)
        {
            return Array.Empty<string>();
        }

        List<string> failures = new();
        Collect(result, failures);
        return failures.Count == 0
            ? new[] { $"The document does not conform to the exact offline schema {schemaId}." }
            : failures;
    }

    private static void Collect(EvaluationResults result, List<string> failures)
    {
        if (failures.Count >= MaximumFailures || result.IsValid)
        {
            return;
        }

        EvaluationResults[] invalidDetails = (result.Details ?? new List<EvaluationResults>()).Where(static detail => !detail.IsValid).ToArray();
        foreach (EvaluationResults detail in invalidDetails)
        {
            Collect(detail, failures);
            if (failures.Count >= MaximumFailures)
            {
                break;
            }
        }

        if (invalidDetails.Length == 0 && result.Errors is { Count: > 0 })
        {
            string errors = string.Join(" | ", result.Errors.OrderBy(static item => item.Key, StringComparer.Ordinal)
                .Select(static item => $"{item.Key}:{item.Value}"));
            failures.Add($"{result.InstanceLocation}: {errors}.");
        }
    }
}

using System;
using System.Collections;
using System.IO;
using System.Text.Json.Nodes;
using YamlDotNet.Serialization;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public static class RestrictedYaml
{
    public static JsonObject Parse(string text)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(text);
        if (text.Contains("!!", StringComparison.Ordinal) ||
            text.Contains('&') ||
            text.Contains('*') ||
            text.Contains("${", StringComparison.Ordinal) ||
            text.Contains('\t'))
        {
            throw new InvalidDataException("Restricted YAML forbids tags, anchors, aliases, substitutions, and tabs.");
        }

        object? value = new DeserializerBuilder().Build().Deserialize<object>(text);
        return ConvertValue(value, 0) as JsonObject
            ?? throw new InvalidDataException("Restricted YAML must have one mapping root.");
    }

    private static JsonNode? ConvertValue(object? value, int depth)
    {
        if (depth > 32)
        {
            throw new InvalidDataException("Restricted YAML nesting exceeds 32 levels.");
        }

        if (value is null) return null;
        if (value is string text) return JsonValue.Create(text);
        if (value is bool boolean) return JsonValue.Create(boolean);
        if (value is int integer) return JsonValue.Create(integer);
        if (value is long longValue) return JsonValue.Create(longValue);
        if (value is double doubleValue && double.IsFinite(doubleValue)) return JsonValue.Create(doubleValue);
        if (value is IDictionary dictionary)
        {
            JsonObject result = new();
            foreach (DictionaryEntry entry in dictionary)
            {
                string name = entry.Key as string ?? throw new InvalidDataException("Restricted YAML keys must be strings.");
                if (result.ContainsKey(name)) throw new InvalidDataException($"Duplicate restricted YAML key: {name}");
                result.Add(name, ConvertValue(entry.Value, depth + 1));
            }

            return result;
        }

        if (value is IEnumerable sequence)
        {
            JsonArray result = new();
            foreach (object? item in sequence) result.Add(ConvertValue(item, depth + 1));
            return result;
        }

        throw new InvalidDataException($"Unsupported restricted YAML value type: {value.GetType().Name}");
    }
}

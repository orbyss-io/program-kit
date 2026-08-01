using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Validation;

public sealed class SchemaRegistry
{
    private readonly IReadOnlyDictionary<string, JsonNode> schemas;
    private readonly IReadOnlyDictionary<string, JsonSchema> compiledSchemas;
    private readonly IReadOnlyDictionary<string, string> digests;

    public SchemaRegistry()
    {
        Dictionary<string, JsonNode> parsed = new(StringComparer.Ordinal);
        Dictionary<string, JsonSchema> compiled = new(StringComparer.Ordinal);
        Dictionary<string, string> parsedDigests = new(StringComparer.Ordinal);
        foreach ((string name, string content) in ContractSchemaResources.ReadAll())
        {
            JsonNode schema = CanonicalJson.Parse(System.Text.Encoding.UTF8.GetBytes(content));
            string id = schema["$id"]?.GetValue<string>()
                ?? throw new InvalidOperationException($"Schema {name} has no $id.");
            if (!parsed.TryAdd(id, schema))
            {
                throw new InvalidOperationException($"Duplicate schema identity: {id}");
            }

            parsedDigests.Add(id, CanonicalJson.Digest(schema));
        }

        Json.Schema.SchemaRegistry localRegistry = new();
        BuildOptions buildOptions = new()
        {
            Dialect = Dialect.Draft202012,
            SchemaRegistry = localRegistry,
        };
        foreach ((string id, JsonNode schema) in parsed.OrderBy(static item => item.Key, StringComparer.Ordinal))
        {
            using JsonDocument document = JsonDocument.Parse(CanonicalJson.Encode(schema));
            compiled.Add(id, JsonSchema.Build(document.RootElement.Clone(), buildOptions));
        }

        compiledSchemas = compiled;
        schemas = parsed;
        digests = parsedDigests;
    }

    public IReadOnlyDictionary<string, string> Digests => digests;

    public JsonNode Get(string id) => schemas.TryGetValue(id, out JsonNode? schema)
        ? schema.DeepClone()
        : throw new KeyNotFoundException($"Schema is not in the offline exact registry: {id}");

    public JsonSchema GetCompiled(string id) => compiledSchemas.TryGetValue(id, out JsonSchema? schema)
        ? schema
        : throw new KeyNotFoundException($"Schema is not in the offline exact registry: {id}");
}

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterContractTests
{
    [TestMethod]
    public void Adapter_schemas_are_closed_unique_embedded_and_exactly_versioned()
    {
        var schemas = AdapterSchemaResources.ReadAll();
        Assert.AreEqual(8, schemas.Count);
        string[] ids = schemas.Values.Select(static content => JsonNode.Parse(content)!["$id"]!.GetValue<string>()).ToArray();
        Assert.AreEqual(ids.Length, ids.Distinct(StringComparer.Ordinal).Count());
        foreach (string content in schemas.Values)
        {
            JsonObject schema = JsonNode.Parse(content)!.AsObject();
            Assert.AreEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"]!.GetValue<string>());
            Assert.AreEqual(false, schema["additionalProperties"]!.GetValue<bool>());
            Compile(content);
        }
    }

    [TestMethod]
    public void Release_owned_compatibility_and_diagnostic_resources_conform_to_their_schemas()
    {
        AssertValid("compatibility.schema.json", ReadResource("compatibility.json"));
        AssertValid("diagnostic-catalog.schema.json", ReadResource("diagnostic-catalog.json"));
    }

    [TestMethod]
    public void Canonical_adapter_bytes_and_digests_ignore_object_insertion_order_only()
    {
        JsonObject first = new() { ["z"] = new JsonObject { ["b"] = 2, ["a"] = 1 }, ["a"] = true };
        JsonObject second = new() { ["a"] = true, ["z"] = new JsonObject { ["a"] = 1, ["b"] = 2 } };
        CollectionAssert.AreEqual(CanonicalDocument.Encode(first), CanonicalDocument.Encode(second));
        Assert.AreEqual(CanonicalDocument.Digest(first), CanonicalDocument.Digest(second));

        JsonObject changed = (JsonObject)second.DeepClone();
        changed["z"]!["b"] = 3;
        Assert.AreNotEqual(CanonicalDocument.Digest(first), CanonicalDocument.Digest(changed));
    }

    [TestMethod]
    public void Adapter_schemas_reject_open_top_level_documents()
    {
        foreach ((string name, string content) in AdapterSchemaResources.ReadAll())
        {
            JsonObject schemaNode = JsonNode.Parse(content)!.AsObject();
            JsonObject instance = new() { ["unexpected"] = true };
            Assert.IsFalse(Evaluate(schemaNode, instance).IsValid, name);
        }
    }

    private static void AssertValid(string schemaName, JsonObject instance)
    {
        JsonObject schema = JsonNode.Parse(AdapterSchemaResources.ReadAll()[schemaName])!.AsObject();
        Assert.IsTrue(Evaluate(schema, instance).IsValid, schemaName);
    }

    private static EvaluationResults Evaluate(JsonObject schema, JsonObject instance)
    {
        using JsonDocument schemaDocument = JsonDocument.Parse(CanonicalDocument.Encode(schema));
        JsonSchema compiled = JsonSchema.Build(schemaDocument.RootElement.Clone(), new BuildOptions { Dialect = Dialect.Draft202012, SchemaRegistry = new Json.Schema.SchemaRegistry() });
        using JsonDocument instanceDocument = JsonDocument.Parse(CanonicalDocument.Encode(instance));
        return compiled.Evaluate(instanceDocument.RootElement, new EvaluationOptions { OutputFormat = OutputFormat.List });
    }

    private static void Compile(string content)
    {
        using JsonDocument document = JsonDocument.Parse(content);
        _ = JsonSchema.Build(document.RootElement.Clone(), new BuildOptions { Dialect = Dialect.Draft202012, SchemaRegistry = new Json.Schema.SchemaRegistry() });
    }

    private static JsonObject ReadResource(string suffix)
    {
        Assembly assembly = typeof(AdapterSchemaResources).Assembly;
        string name = assembly.GetManifestResourceNames().Single(item => item.EndsWith($".Resources.{suffix}", StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException(name);
        return JsonNode.Parse(stream)!.AsObject();
    }
}

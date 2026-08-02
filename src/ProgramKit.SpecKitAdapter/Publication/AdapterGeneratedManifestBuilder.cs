using System;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public static class AdapterGeneratedManifestBuilder
{
    public static JsonObject Build(BoundHandoff handoff, string reviewDigest, TranslationResult translation, TraceResolution trace)
    {
        JsonArray outputs = new(translation.Bytes.OrderBy(static item => item.Key, StringComparer.Ordinal).Select(item => new JsonObject
        {
            ["logicalPath"] = item.Key,
            ["digest"] = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(item.Value)).ToLowerInvariant(),
            ["ownership"] = "adapter-generated-owned",
        }).ToArray());
        JsonObject invalidation = new();
        string[] inputs = trace.DependencyDigests.OrderBy(static item => item.Key, StringComparer.Ordinal).Select(static item => $"{item.Key}:{item.Value}").ToArray();
        foreach (JsonNode? output in outputs) invalidation[output!["logicalPath"]!.GetValue<string>()] = new JsonArray(inputs.Select(static value => JsonValue.Create(value)).ToArray());
        JsonObject manifest = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-manifest/v1",
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = new JsonObject { ["logicalPath"] = "compatibility.json", ["release"] = "0.1.0" },
            ["feature"] = handoff.Document["feature"]!.DeepClone(),
            ["inputs"] = new JsonArray(
                new JsonObject { ["kind"] = "handoff", ["digest"] = handoff.Digest },
                new JsonObject { ["kind"] = "review", ["digest"] = reviewDigest }),
            ["outputs"] = outputs,
            ["ownership"] = "adapter-generated-owned",
            ["invalidationSets"] = invalidation,
        };
        manifest["digest"] = CanonicalDocument.Digest(manifest);
        AdapterSchemaValidator.Validate("generated-manifest.schema.json", manifest);
        return manifest;
    }
}

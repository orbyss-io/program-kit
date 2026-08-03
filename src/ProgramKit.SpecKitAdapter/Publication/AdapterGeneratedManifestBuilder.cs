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
        AdapterCompatibilityDocument compatibility = AdapterCompatibility.Load();
        JsonArray outputs = new(translation.Bytes.OrderBy(static item => item.Key, StringComparer.Ordinal).Select(item => new JsonObject
        {
            ["logicalPath"] = item.Key,
            ["digest"] = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(item.Value)).ToLowerInvariant(),
            ["ownership"] = "adapter-generated-owned",
            ["retention"] = item.Key.Contains("/definitions/", StringComparison.Ordinal) ? "regenerable-candidate" : "retained-evidence",
            ["state"] = "current",
        }).ToArray());
        JsonObject invalidation = TraceInvalidationEngine.Build(handoff, reviewDigest, translation, trace, compatibility.Digest);
        JsonObject manifest = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-manifest/v1",
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = new JsonObject { ["logicalPath"] = AdapterCompatibility.LogicalPath, ["release"] = "0.1.0", ["digest"] = compatibility.Digest },
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

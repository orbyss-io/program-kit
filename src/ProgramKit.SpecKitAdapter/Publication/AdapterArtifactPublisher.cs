using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public sealed class AdapterArtifactPublisher
{
    public PublicationResult Publish(string workspaceRoot, TranslationResult translation, JsonObject generatedManifest)
    {
        string manifestLogicalPath = $"{translation.FeatureRoot}/adapter-manifest.json";
        Dictionary<string, byte[]> outputs = new(translation.Bytes, StringComparer.Ordinal)
        {
            [manifestLogicalPath] = CanonicalDocument.Encode(generatedManifest),
        };
        Dictionary<string, string> expected = new(StringComparer.Ordinal);
        string manifestPath = LogicalPathPolicy.Resolve(workspaceRoot, manifestLogicalPath);
        if (File.Exists(manifestPath))
        {
            JsonObject previous = CanonicalDocument.Parse(File.ReadAllBytes(manifestPath)).AsObject();
            AdapterSchemaValidator.Validate("generated-manifest.schema.json", previous);
            foreach (JsonObject artifact in previous["outputs"]!.AsArray().OfType<JsonObject>())
                expected[artifact["logicalPath"]!.GetValue<string>()] = artifact["digest"]!.GetValue<string>();
            expected[manifestLogicalPath] = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(manifestPath))).ToLowerInvariant();
        }

        return new AtomicArtifactPublisher().Publish(workspaceRoot, outputs, expected);
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public sealed record AdapterCleanupResult(IReadOnlyList<string> Removed, IReadOnlyList<string> Preserved, bool Changed);

public sealed class AdapterCleanupService
{
    public AdapterCleanupResult Cleanup(string workspaceRoot, string featureKey, string outputRoot)
    {
        string expectedRoot = $"specs/{featureKey}/program-kit/generated";
        if (!string.Equals(outputRoot, expectedRoot, StringComparison.Ordinal))
            throw new InvalidDataException("Cleanup outputRoot must be the exact feature-generated root.");
        string manifestLogical = $"{expectedRoot}/adapter-manifest.json";
        string manifestPath = LogicalPathPolicy.Resolve(workspaceRoot, manifestLogical);
        if (!File.Exists(manifestPath)) return new AdapterCleanupResult(Array.Empty<string>(), Array.Empty<string>(), Changed: false);
        byte[] manifestBytes = File.ReadAllBytes(manifestPath);
        JsonObject manifest = CanonicalDocument.Parse(manifestBytes).AsObject();
        AdapterSchemaValidator.Validate("generated-manifest.schema.json", manifest);
        string declaredDigest = manifest["digest"]?.GetValue<string>() ?? throw new AdapterPublicationException("The cleanup manifest has no exact digest.");
        JsonObject digestMaterial = (JsonObject)manifest.DeepClone();
        digestMaterial.Remove("digest");
        if (!string.Equals(declaredDigest, CanonicalDocument.Digest(digestMaterial), StringComparison.Ordinal))
            throw new AdapterPublicationException("The cleanup manifest digest is stale.");

        JsonObject[] declaredOutputs = manifest["outputs"]!.AsArray().OfType<JsonObject>().ToArray();
        string[] declaredPaths = declaredOutputs.Select(static output => output["logicalPath"]!.GetValue<string>()).ToArray();
        LogicalPathPolicy.ValidateDistinct(declaredPaths);
        if (declaredPaths.Any(path => !path.StartsWith(expectedRoot + "/", StringComparison.Ordinal)))
            throw new AdapterPublicationException("Cleanup manifest output escapes the exact feature-generated root.");
        JsonObject[] candidates = declaredOutputs
            .Where(static output => output["retention"]?.GetValue<string>() == "regenerable-candidate"
                && output["ownership"]?.GetValue<string>() == "adapter-generated-owned")
            .ToArray();
        List<string> preserved = declaredOutputs
            .Except(candidates)
            .Select(static output => output["logicalPath"]!.GetValue<string>())
            .OrderBy(static path => path, StringComparer.Ordinal)
            .ToList();
        foreach (JsonObject candidate in candidates.Where(static output => output["state"]?.GetValue<string>() != "removed"))
        {
            string path = LogicalPathPolicy.Resolve(workspaceRoot, candidate["logicalPath"]!.GetValue<string>());
            if (!File.Exists(path) || !string.Equals(Digest(File.ReadAllBytes(path)), candidate["digest"]!.GetValue<string>(), StringComparison.Ordinal))
                throw new AdapterPublicationException("Cleanup refuses a missing or drifted candidate before changing the manifest.");
        }

        bool manifestChanged = candidates.Any(static output => output["state"]?.GetValue<string>() != "removed");
        if (manifestChanged)
        {
            foreach (JsonObject candidate in candidates) candidate["state"] = "removed";
            manifest.Remove("digest");
            manifest["digest"] = CanonicalDocument.Digest(manifest);
            Dictionary<string, byte[]> output = new(StringComparer.Ordinal) { [manifestLogical] = CanonicalDocument.Encode(manifest) };
            Dictionary<string, string> expected = new(StringComparer.Ordinal) { [manifestLogical] = Digest(manifestBytes) };
            new AtomicArtifactPublisher().Publish(workspaceRoot, output, expected, manifestLogical);
        }

        List<string> removed = new();
        foreach (JsonObject candidate in candidates.OrderBy(static output => output["logicalPath"]!.GetValue<string>(), StringComparer.Ordinal))
        {
            string logicalPath = candidate["logicalPath"]!.GetValue<string>();
            string path = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            if (!File.Exists(path)) continue;
            if (!string.Equals(Digest(File.ReadAllBytes(path)), candidate["digest"]!.GetValue<string>(), StringComparison.Ordinal))
            {
                preserved.Add(logicalPath);
                continue;
            }

            File.Delete(path);
            removed.Add(logicalPath);
        }

        preserved.Sort(StringComparer.Ordinal);
        return new AdapterCleanupResult(removed, preserved, manifestChanged || removed.Count > 0);
    }

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(bytes)).ToLowerInvariant();
}

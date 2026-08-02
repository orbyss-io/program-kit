using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Handoff;

public sealed record TraceResolution(IReadOnlyDictionary<string, string> DependencyDigests);

public static class TraceResolver
{
    private static readonly string[] AllowedKinds = { "spec-block", "plan-decision", "task-row", "human-decision", "compatibility-fixed" };

    public static TraceResolution Validate(string workspaceRoot, BoundHandoff handoff)
    {
        Dictionary<string, string> dependencies = new(StringComparer.Ordinal);
        foreach (JsonObject trace in handoff.Document["trace"]!.AsArray().OfType<JsonObject>())
        {
            string target = Required(trace, "targetPointer");
            string kind = Required(trace, "sourceKind");
            if (!AllowedKinds.Contains(kind, StringComparer.Ordinal)) throw new InvalidDataException("The trace source kind is unsupported.");
            JsonNode observed = trace["observedValue"] ?? throw new InvalidDataException("Trace observedValue is required.");
            JsonNode actual = ResolvePointer(handoff.Document, target);
            if (!CanonicalDocument.Encode(observed).SequenceEqual(CanonicalDocument.Encode(actual)))
                throw new InvalidDataException("The traced observed value differs from the handoff target.");
            if (kind is "human-decision" or "compatibility-fixed")
            {
                dependencies[target] = CanonicalDocument.Digest(observed);
                continue;
            }

            JsonObject source = trace["sourceArtifact"]?.AsObject() ?? throw new InvalidDataException("File-backed trace requires sourceArtifact.");
            string logicalPath = source["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("Trace source logicalPath is required.");
            string anchor = Required(trace, "sourceAnchor");
            string path = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) throw new InvalidDataException("The traced source artifact is unavailable.");
            string block = ExtractNamedBlock(File.ReadAllText(path), anchor);
            string digest = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(block))).ToLowerInvariant();
            if (!string.Equals(digest, Required(trace, "sourceBlockDigest"), StringComparison.Ordinal))
                throw new InvalidDataException("A traced named source block changed.");
            dependencies[target] = digest;
        }

        foreach (JsonObject implementation in handoff.Document["implementation"]!.AsArray().OfType<JsonObject>())
        {
            string logicalPath = Required(implementation, "logicalPath");
            string expected = Required(implementation, "digest");
            string path = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) throw new InvalidDataException("A referenced implementation artifact is unavailable.");
            string observed = "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
            if (!string.Equals(expected, observed, StringComparison.Ordinal)) throw new InvalidDataException("Referenced implementation bytes changed.");
            dependencies[$"implementation:{logicalPath}"] = observed;
        }

        return new TraceResolution(dependencies);
    }

    public static string ExtractNamedBlock(string text, string anchor)
    {
        string normalized = text.Replace("\r\n", "\n", StringComparison.Ordinal);
        string start = $"<!-- program-kit:{anchor} -->";
        string end = $"<!-- /program-kit:{anchor} -->";
        int startIndex = normalized.IndexOf(start, StringComparison.Ordinal);
        int secondStart = startIndex < 0 ? -1 : normalized.IndexOf(start, startIndex + start.Length, StringComparison.Ordinal);
        int endIndex = startIndex < 0 ? -1 : normalized.IndexOf(end, startIndex + start.Length, StringComparison.Ordinal);
        if (startIndex < 0 || secondStart >= 0 || endIndex < 0) throw new InvalidDataException("A traced named source block is missing or ambiguous.");
        int contentStart = startIndex + start.Length;
        return normalized[contentStart..endIndex].Trim();
    }

    private static JsonNode ResolvePointer(JsonNode root, string pointer)
    {
        if (!pointer.StartsWith('/')) throw new InvalidDataException("Trace targetPointer must be a JSON Pointer.");
        JsonNode? current = root;
        foreach (string raw in pointer.Split('/').Skip(1))
        {
            string segment = raw.Replace("~1", "/", StringComparison.Ordinal).Replace("~0", "~", StringComparison.Ordinal);
            current = current switch
            {
                JsonObject obj => obj[segment],
                JsonArray array when int.TryParse(segment, out int index) && index >= 0 && index < array.Count => array[index],
                _ => null,
            };
            if (current is null) throw new InvalidDataException("Trace targetPointer does not resolve.");
        }

        return current;
    }

    private static string Required(JsonObject document, string name) => document[name]?.GetValue<string>() is { Length: > 0 } value
        ? value
        : throw new InvalidDataException($"Trace field {name} is required.");
}

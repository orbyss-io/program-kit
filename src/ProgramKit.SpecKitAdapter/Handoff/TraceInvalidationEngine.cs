using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Handoff;

public static class TraceInvalidationEngine
{
    public static JsonObject Build(
        BoundHandoff handoff,
        string reviewDigest,
        TranslationResult translation,
        TraceResolution trace,
        string compatibilityDigest)
    {
        string compatibility = $"compatibility:{compatibilityDigest}";
        JsonObject sets = new();
        sets["$claims"] = Values(trace.DependencyDigests.Values
            .Append(compatibility)
            .Append($"review:{reviewDigest}"));

        foreach ((string logicalPath, byte[] bytes) in translation.Bytes.OrderBy(static item => item.Key, StringComparer.Ordinal))
        {
            IEnumerable<string> dependencies = SelectDependencies(logicalPath, trace.DependencyDigests).Append(compatibility);
            if (logicalPath.Contains("/results/", StringComparison.Ordinal))
                dependencies = dependencies.Append($"retained-evidence:{logicalPath}:{Digest(bytes)}");
            sets[logicalPath] = Values(dependencies);
        }

        return sets;
    }

    public static IReadOnlyList<string> ChangedClaims(JsonObject previousSets, JsonObject currentSets) => previousSets
        .Select(static item => item.Key)
        .Concat(currentSets.Select(static item => item.Key))
        .Distinct(StringComparer.Ordinal)
        .Where(key => !Equivalent(previousSets[key] as JsonArray, currentSets[key] as JsonArray))
        .OrderBy(static key => key, StringComparer.Ordinal)
        .ToArray();

    private static IEnumerable<string> SelectDependencies(string logicalPath, IReadOnlyDictionary<string, string> dependencies)
    {
        string[] targets = logicalPath switch
        {
            _ when logicalPath.EndsWith("/definitions/dotnet-component-api.json", StringComparison.Ordinal) => new[] { "/definition", "/definitionFamily" },
            _ when logicalPath.EndsWith("/definitions/software-bundle.json", StringComparison.Ordinal) => new[] { "/feature", "/definition", "/definitionFamily", "/effectiveSelection", "/implementation" },
            _ when logicalPath.EndsWith("/requests/prepare.json", StringComparison.Ordinal) || logicalPath.EndsWith("/results/prepare.json", StringComparison.Ordinal) => new[] { "/feature", "/definition", "/definitionFamily", "/effectiveSelection", "/implementation", "/evaluationContext", "/maximumEffect", "/constructionMode" },
            _ when logicalPath.EndsWith("/requests/explain.json", StringComparison.Ordinal) || logicalPath.EndsWith("/results/explain.json", StringComparison.Ordinal) => new[] { "/feature", "/definition", "/definitionFamily", "/effectiveSelection", "/implementation", "/evaluationContext" },
            _ => dependencies.Keys.ToArray(),
        };
        return dependencies
            .Where(item => targets.Contains(item.Key, StringComparer.Ordinal)
                || (targets.Contains("/implementation", StringComparer.Ordinal) && item.Key.StartsWith("implementation:", StringComparison.Ordinal)))
            .Select(static item => $"{item.Key}:{item.Value}");
    }

    private static JsonArray Values(IEnumerable<string> values) => new(values
        .Distinct(StringComparer.Ordinal)
        .OrderBy(static value => value, StringComparer.Ordinal)
        .Select(static value => JsonValue.Create(value))
        .ToArray());

    private static bool Equivalent(JsonArray? left, JsonArray? right) => left is not null
        && right is not null
        && CanonicalDocument.Encode(left).SequenceEqual(CanonicalDocument.Encode(right));

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(bytes)).ToLowerInvariant();
}

using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

internal static class CSharpBuildGateValidation
{
    public static void Error(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string path,
        string message) =>
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));

    public static void Require(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool condition,
        string id,
        string path,
        string message)
    {
        if (!condition)
        {
            diagnostics.Error(id, path, message);
        }
    }

    public static bool IsExactRepositoryPath(string? value)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            value != value.Trim() ||
            Path.IsPathRooted(value) ||
            value.Contains('\\', StringComparison.Ordinal) ||
            value.Contains('*', StringComparison.Ordinal) ||
            value.Contains('?', StringComparison.Ordinal) ||
            value.Contains('[', StringComparison.Ordinal) ||
            value.Contains(']', StringComparison.Ordinal))
        {
            return false;
        }

        var segments = value.Split('/');
        return segments.All(static segment =>
            segment.Length > 0 &&
            !string.Equals(segment, ".", StringComparison.Ordinal) &&
            !string.Equals(segment, "..", StringComparison.Ordinal));
    }

    public static void ValidateStableUnique<T>(
        ImmutableArray<T> values,
        Func<T, string> key,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool requireOne = true)
    {
        if (values.IsDefault || (requireOne && values.Length == 0))
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg002,
                path,
                "The finite collection is required.");
            return;
        }

        var keys = values.Select(key).ToArray();
        var duplicate = keys
            .GroupBy(static value => value, StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() > 1);
        if (duplicate is not null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg002,
                path,
                string.Concat(
                    "The finite collection contains duplicate composite key '",
                    duplicate.Key,
                    "'."));
        }

        for (var index = 1; index < keys.Length; index++)
        {
            if (string.CompareOrdinal(keys[index - 1], keys[index]) <= 0)
            {
                continue;
            }

            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg002,
                path,
                string.Concat(
                    "Stable ordinal ordering by the exact composite key is required; adjacent key '",
                    keys[index - 1],
                    "' must follow '",
                    keys[index],
                    "'."));
            break;
        }
    }

    public static bool SameReference(
        ArtifactReference left,
        ArtifactReference right) =>
        left == right;
}

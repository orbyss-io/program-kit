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
        diagnostics.Require(
            keys.Distinct(StringComparer.Ordinal).Count() == keys.Length,
            CSharpBuildGateDiagnosticIds.Pkcg002,
            path,
            "The finite collection contains duplicate identities.");
        diagnostics.Require(
            keys.SequenceEqual(keys.Order(StringComparer.Ordinal)),
            CSharpBuildGateDiagnosticIds.Pkcg002,
            path,
            "The finite collection must use stable ordinal ordering.");
    }

    public static bool SameReference(
        ArtifactReference left,
        ArtifactReference right) =>
        left == right;
}

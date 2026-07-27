using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Diagnostics;

/// <summary>Provides fixed operations over an explicit architecture diagnostic collection.</summary>
internal static class ArchitectureDiagnosticOperations
{
    public static void Add(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitValidationResult result)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        diagnostics.AddRange(result.Diagnostics);
    }

    public static void Error(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string path,
        string message)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));
    }

    public static void Required(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string? value,
        string path,
        string description)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc001, path, $"{description} is required.");
        }
    }

    public static void Identifier(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitIdentifier value,
        string path)
    {
        if (!ProgramKitIdentifier.TryParse(value.Value, out _))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc002,
                path,
                "A valid Program Kit identifier is required.");
        }
    }

    public static void Version(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        SemanticVersion value,
        string path)
    {
        if (!SemanticVersion.TryParse(value.Value, out _))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc003,
                path,
                "A valid full semantic version is required.");
        }
    }

    public static void Reference(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ArtifactReference? value,
        string path)
    {
        if (value is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc004,
                path,
                "An exact artifact reference is required.");
            return;
        }

        diagnostics.Identifier(value.Identity, $"{path}/identity");
        diagnostics.Version(value.Version, $"{path}/version");
        if (!Sha256Digest.TryParse(value.Digest.Value, out _))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc005,
                $"{path}/digest",
                "A valid SHA-256 digest is required.");
        }
    }

    public static void DuplicateIdentifiers<T>(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ImmutableArray<T> values,
        Func<T, ProgramKitIdentifier> selector,
        string path)
    {
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var value in OrEmpty(values))
        {
            var identity = selector(value).Value;
            if (!string.IsNullOrWhiteSpace(identity) && !seen.Add(identity))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc006,
                    path,
                    $"Duplicate identity '{identity}'.");
            }
        }
    }

    public static ProgramKitValidationResult ToResult(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    public static ImmutableArray<T> OrEmpty<T>(ImmutableArray<T> values) =>
        values.IsDefault ? ImmutableArray<T>.Empty : values;
}

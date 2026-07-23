using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>Provides fixed operations over an explicit diagnostic collection.</summary>
internal static class ArtifactDiagnosticOperations
{
    /// <summary>Adds all diagnostics from a semantic validation result.</summary>
    public static void Add(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitValidationResult result)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        diagnostics.AddRange(result.Diagnostics);
    }

    /// <summary>Adds an error diagnostic to the supplied collection.</summary>
    public static void Error(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string message,
        string path)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));
    }

    /// <summary>Creates an immutable result from the supplied collection.</summary>
    public static ProgramKitValidationResult ToResult(
        this ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }
}

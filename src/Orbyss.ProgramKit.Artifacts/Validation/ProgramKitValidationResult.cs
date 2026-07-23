using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>The immutable result of semantic validation.</summary>
public sealed record ProgramKitValidationResult
{
    private ProgramKitValidationResult(ImmutableArray<ProgramKitDiagnostic> diagnostics)
    {
        Diagnostics = diagnostics;
    }

    /// <summary>A valid result with no diagnostics.</summary>
    public static ProgramKitValidationResult Valid { get; } =
        new(ImmutableArray<ProgramKitDiagnostic>.Empty);

    /// <summary>Gets diagnostics in deterministic discovery order.</summary>
    public ImmutableArray<ProgramKitDiagnostic> Diagnostics { get; }

    /// <summary>Gets whether the result contains no error diagnostics.</summary>
    public bool IsValid =>
        Diagnostics.IsDefaultOrEmpty ||
        !Diagnostics.Any(static diagnostic =>
            diagnostic.Severity == ProgramKitDiagnosticSeverity.Error);

    /// <summary>Creates a result from diagnostics while preserving their supplied order.</summary>
    public static ProgramKitValidationResult From(
        IEnumerable<ProgramKitDiagnostic> diagnostics)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        return new ProgramKitValidationResult(diagnostics.ToImmutableArray());
    }

    /// <summary>Combines results in the supplied order.</summary>
    public static ProgramKitValidationResult Combine(
        params ProgramKitValidationResult[] results)
    {
        ArgumentNullException.ThrowIfNull(results);

        if (results.Length == 0)
        {
            return Valid;
        }

        var builder = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        foreach (var result in results)
        {
            ArgumentNullException.ThrowIfNull(result);
            builder.AddRange(result.Diagnostics);
        }

        return new ProgramKitValidationResult(builder.MoveToImmutable());
    }
}

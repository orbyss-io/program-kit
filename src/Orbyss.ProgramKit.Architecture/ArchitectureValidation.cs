using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

internal sealed class ArchitectureDiagnosticBag
{
    private readonly List<ProgramKitDiagnostic> diagnostics = [];

    public void Error(string id, string path, string message) =>
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));

    public void Required(string? value, string path, string description)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            Error(ArchitectureDiagnosticIds.Pkarc001, path, $"{description} is required.");
        }
    }

    public void Identifier(ProgramKitIdentifier value, string path)
    {
        if (!ProgramKitIdentifier.TryParse(value.Value, out _))
        {
            Error(ArchitectureDiagnosticIds.Pkarc002, path, "A valid Program Kit identifier is required.");
        }
    }

    public void Version(SemanticVersion value, string path)
    {
        if (!SemanticVersion.TryParse(value.Value, out _))
        {
            Error(ArchitectureDiagnosticIds.Pkarc003, path, "A valid full semantic version is required.");
        }
    }

    public void Reference(ArtifactReference? value, string path)
    {
        if (value is null)
        {
            Error(ArchitectureDiagnosticIds.Pkarc004, path, "An exact artifact reference is required.");
            return;
        }

        Identifier(value.Identity, $"{path}/identity");
        Version(value.Version, $"{path}/version");
        if (!Sha256Digest.TryParse(value.Digest.Value, out _))
        {
            Error(ArchitectureDiagnosticIds.Pkarc005, $"{path}/digest", "A valid SHA-256 digest is required.");
        }
    }

    public void DuplicateIdentifiers<T>(
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
                Error(ArchitectureDiagnosticIds.Pkarc006, path, $"Duplicate identity '{identity}'.");
            }
        }
    }

    public ProgramKitValidationResult ToResult() =>
        ProgramKitValidationResult.From(diagnostics);

    public static ImmutableArray<T> OrEmpty<T>(ImmutableArray<T> values) =>
        values.IsDefault ? ImmutableArray<T>.Empty : values;
}

internal static class ArchitectureValidation
{
    public static ImmutableArray<T> OrEmpty<T>(ImmutableArray<T> values) =>
        ArchitectureDiagnosticBag.OrEmpty(values);

    public static bool IsDeclared(
        ProgramKitIdentifier identity,
        HashSet<string> declaredIds) =>
        !string.IsNullOrWhiteSpace(identity.Value) && declaredIds.Contains(identity.Value);

    public static void RequireDeclared(
        ArchitectureDiagnosticBag diagnostics,
        ProgramKitIdentifier identity,
        HashSet<string> declaredIds,
        string path,
        string description)
    {
        diagnostics.Identifier(identity, path);
        if (!IsDeclared(identity, declaredIds))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc007,
                path,
                $"{description} '{identity.Value}' is not declared by this design.");
        }
    }
}

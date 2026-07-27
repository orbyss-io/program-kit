using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Development.Diagnostics;

namespace Orbyss.ProgramKit.Development.Validation;

internal static class DevelopmentValidation
{
    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static void RequireText(
        string? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev006, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev007, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
        }
    }
}

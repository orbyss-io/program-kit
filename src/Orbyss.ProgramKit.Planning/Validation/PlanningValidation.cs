using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Planning.Diagnostics;

namespace Orbyss.ProgramKit.Planning.Validation;

internal static class PlanningValidation
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
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateProfileReference(
        ProfileReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln006, "An exact profile reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln007, "An exact profile version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln008, "An exact profile digest is required.", $"{path}.digest"));
        }

        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                PlanningDiagnosticIds.Pkpln016,
                "The exact reference must have PKID kind 'profile'.",
                $"{path}.identity"));
        }
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln009, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln010, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
        }
    }

    internal static void RequireReferenceKind(
        ArtifactReference? value,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string diagnosticId = PlanningDiagnosticIds.Pkpln013)
    {
        if (value is not null
            && !string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                diagnosticId,
                $"The exact reference must have PKID kind '{expectedKind}'.",
                $"{path}.identity"));
        }
    }

    internal static void RequireReferenceKinds(
        ImmutableArray<ArtifactReference> values,
        string expectedKind,
        string path,
        string diagnosticId,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            RequireReferenceKind(
                values[index],
                expectedKind,
                $"{path}[{index}]",
                diagnostics,
                diagnosticId);
        }
    }

    internal static void RequireUniqueText(
        ImmutableArray<string> values,
        string path,
        string emptyDiagnosticId,
        string emptyMessage,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(Error(emptyDiagnosticId, emptyMessage, path));
            return;
        }

        ValidateTextArray(values, path, diagnostics);
    }

    internal static void ValidateTextArray(
        ImmutableArray<string> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool allowDuplicates = false)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln011, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            RequireText(value, $"{path}[{index}]", diagnostics);
            if (!allowDuplicates && !string.IsNullOrWhiteSpace(value) && !seen.Add(value))
            {
                diagnostics.Add(Error(PlanningDiagnosticIds.Pkpln012, $"Value '{value}' occurs more than once.", $"{path}[{index}]"));
            }
        }
    }
}

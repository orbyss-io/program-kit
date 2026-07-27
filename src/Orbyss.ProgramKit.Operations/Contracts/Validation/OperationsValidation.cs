using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

internal static class OperationsValidation
{
    internal static void RequireText(
        string? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "A non-empty value is required.",
                path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "A Program Kit identifier is required.",
                path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string? expectedKind = null)
    {
        if (value is null ||
            string.IsNullOrWhiteSpace(value.Identity.Value) ||
            string.IsNullOrWhiteSpace(value.Version.Value) ||
            string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.InvalidReference,
                "An exact artifact reference is required.",
                path));
            return;
        }

        if (expectedKind is not null &&
            !string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.InvalidReferenceKind,
                string.Concat("The exact reference must have PKID kind '", expectedKind, "'."),
                string.Concat(path, ".identity")));
        }
    }

    internal static void ValidateReferenceSet(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string? expectedKind = null)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "The reference collection must be initialized.",
                path));
            return;
        }

        var exact = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, string.Concat(path, "[", index, "]"), diagnostics, expectedKind);
            if (value is not null && !exact.Add(ExactKey(value)))
            {
                diagnostics.Add(Error(
                    OperationsDiagnosticIds.DuplicateRegistration,
                    "Exact references must be unique.",
                    string.Concat(path, "[", index, "]")));
            }
        }
    }

    internal static void ValidateCompatibility(
        ArtifactCompatibility? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "Compatibility metadata is required.",
                path));
            return;
        }

        RequireIdentifier(value.Policy, string.Concat(path, ".policy"), diagnostics);
        if (value.Dimensions.IsDefault ||
            string.IsNullOrWhiteSpace(value.ReaderRange.Value) ||
            string.IsNullOrWhiteSpace(value.WriterRange.Value) ||
            value.MigrationReferences.IsDefault)
        {
            diagnostics.Add(Error(
                OperationsDiagnosticIds.InvalidPolicyCombination,
                "Compatibility collections and version ranges must be initialized.",
                path));
        }

        ValidateReferenceSet(
            value.MigrationReferences,
            string.Concat(path, ".migrationReferences"),
            diagnostics,
            "migration");
    }

    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static string StableKey(ArtifactReference reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    internal static string ExactKey(ArtifactReference reference) =>
        string.Concat(StableKey(reference), "#", reference.Digest.Value);
}

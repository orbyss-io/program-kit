using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Validation;

internal static class SecretResolutionValidation
{
    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "A stable Program Kit identifier is required.",
                path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null ||
            string.IsNullOrWhiteSpace(value.Identity.Value) ||
            string.IsNullOrWhiteSpace(value.Version.Value) ||
            string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.InvalidReference,
                "An exact artifact reference is required.",
                path));
            return;
        }

        if (!string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.InvalidReference,
                string.Concat("The exact reference must have PKID kind '", expectedKind, "'."),
                string.Concat(path, ".identity")));
        }
    }

    internal static void ValidateClassification(
        SecretReferenceClassification value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ValidateEnum(value, path, diagnostics);
        if (value == SecretReferenceClassification.Unspecified)
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.UnclassifiedReference,
                "Reference metadata must be explicitly classified and redacted by default.",
                path));
        }
    }

    internal static void ValidateEnum<TEnum>(
        TEnum value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
        where TEnum : struct, Enum
    {
        if (!Enum.IsDefined(value))
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.InvalidEnumValue,
                "The enum value must belong to its finite set.",
                path));
        }
    }

    internal static void ValidateFiniteSet<TEnum>(
        ImmutableArray<TEnum> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        TEnum unspecified)
        where TEnum : struct, Enum
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "At least one finite capability is required.",
                path));
            return;
        }

        var seen = new HashSet<TEnum>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = string.Concat(path, "[", index, "]");
            ValidateEnum(value, itemPath, diagnostics);
            if (EqualityComparer<TEnum>.Default.Equals(value, unspecified))
            {
                diagnostics.Add(Error(
                    SecretResolutionDiagnosticIds.InvalidEnumValue,
                    "An unspecified value is not a capability.",
                    itemPath));
            }

            if (!seen.Add(value))
            {
                diagnostics.Add(Error(
                    SecretResolutionDiagnosticIds.DuplicateCapability,
                    "Finite capabilities must be unique.",
                    itemPath));
            }
        }
    }

    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}

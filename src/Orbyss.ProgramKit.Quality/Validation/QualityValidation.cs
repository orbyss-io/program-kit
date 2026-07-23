using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Diagnostics;
using Orbyss.ProgramKit.Quality.Execution;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

internal static class QualityValidation
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
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateProfileReference(
        ProfileReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt006, "An exact profile reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt007, "An exact profile version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt008, "An exact profile digest is required.", $"{path}.digest"));
        }

        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                QualityDiagnosticIds.Pkqlt033,
                "An exact profile reference must have PKID kind 'profile'.",
                $"{path}.identity"));
        }
    }

    internal static void ValidateTestReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ValidateReference(value, path, diagnostics);
        if (value is not null &&
            !string.Equals(value.Identity.Kind, "test", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                QualityDiagnosticIds.Pkqlt032,
                "An exact test specification reference must have PKID kind 'test'.",
                $"{path}.identity"));
        }
    }

    internal static void RequireReferenceKind(
        ArtifactReference? value,
        string expectedKind,
        string path,
        string diagnosticId,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is not null &&
            !string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                diagnosticId,
                $"The exact reference must have PKID kind '{expectedKind}'.",
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
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt009, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt010, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
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
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt011, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            RequireText(value, $"{path}[{index}]", diagnostics);
            if (!string.IsNullOrWhiteSpace(value) && !seen.Add(value))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt012, $"Value '{value}' occurs more than once.", $"{path}[{index}]"));
            }
        }
    }

    internal static void ValidateRequirements(
        TestExecutionRequirements? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt013, "Execution requirements are required.", path));
            return;
        }

        RequireUniqueText(
            value.RunnerClasses,
            $"{path}.runnerClasses",
            QualityDiagnosticIds.Pkqlt014,
            "At least one runner class is required.",
            diagnostics);
        RequireUniqueText(
            value.Platforms,
            $"{path}.platforms",
            QualityDiagnosticIds.Pkqlt015,
            "At least one platform is required.",
            diagnostics);
        ValidateTextArray(value.EnvironmentAssumptions, $"{path}.environmentAssumptions", diagnostics);
        ValidateReferences(value.RequiredDependencyClosure, $"{path}.requiredDependencyClosure", diagnostics);
        ValidateAccess(value.Access, $"{path}.access", diagnostics);
        ValidateTimeoutAndRetry(value.Timeout, value.Retry, path, diagnostics);
    }

    internal static void ValidateAccess(
        TestExecutionAccessPolicy? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt016, "An execution access policy is required.", path));
            return;
        }

        ValidateTextArray(value.AllowedNetworkDestinations, $"{path}.allowedNetworkDestinations", diagnostics);
        ValidateTextArray(value.AllowedWriteRoots, $"{path}.allowedWriteRoots", diagnostics);
        ValidateTextArray(value.AllowedSecretReferences, $"{path}.allowedSecretReferences", diagnostics);
        if (!Enum.IsDefined(value.Network))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt028, "Network access policy must be a defined value.", $"{path}.network"));
        }

        if (!Enum.IsDefined(value.Writes))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt029, "Write access policy must be a defined value.", $"{path}.writes"));
        }

        if (!Enum.IsDefined(value.Restore))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt030, "Restore access policy must be a defined value.", $"{path}.restore"));
        }

        if (!Enum.IsDefined(value.Secrets))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt031, "Secret access policy must be a defined value.", $"{path}.secrets"));
        }

        ValidateAllowList(
            value.Network == NetworkAccessPolicy.ExplicitAllowList,
            value.AllowedNetworkDestinations,
            "network",
            $"{path}.allowedNetworkDestinations",
            diagnostics);
        ValidateAllowList(
            value.Writes == WriteAccessPolicy.ExplicitRoots,
            value.AllowedWriteRoots,
            "write-root",
            $"{path}.allowedWriteRoots",
            diagnostics);
        ValidateAllowList(
            value.Secrets == SecretAccessPolicy.ExplicitReferencesOnly,
            value.AllowedSecretReferences,
            "secret-reference",
            $"{path}.allowedSecretReferences",
            diagnostics);
    }

    internal static void ValidateTimeoutAndRetry(
        TimeSpan timeout,
        TestRetryPolicy? retry,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (timeout <= TimeSpan.Zero)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt017, "Timeout must be positive.", $"{path}.timeout"));
        }

        if (retry is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt018, "A retry policy is required.", $"{path}.retry"));
            return;
        }

        if (retry.MaximumAttempts < 1)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt019, "Maximum attempts must be at least one.", $"{path}.retry.maximumAttempts"));
        }

        if (retry.Delay < TimeSpan.Zero)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt020, "Retry delay cannot be negative.", $"{path}.retry.delay"));
        }
    }

    internal static void ValidateAccessDoesNotExceed(
        TestExecutionAccessPolicy? allowed,
        TestExecutionAccessPolicy? selected,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (allowed is null || selected is null)
        {
            return;
        }

        if (!IsNetworkSelectionAllowed(allowed.Network, selected.Network))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt021, "Selected network access exceeds the specification.", $"{path}.network"));
        }

        if (!IsWriteSelectionAllowed(allowed.Writes, selected.Writes))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt022, "Selected write access exceeds the specification.", $"{path}.writes"));
        }

        if (selected.Restore != RestoreAccessPolicy.Denied
            && selected.Restore != allowed.Restore)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt023, "Selected restore access exceeds the specification.", $"{path}.restore"));
        }

        if (selected.Secrets != SecretAccessPolicy.Denied
            && selected.Secrets != allowed.Secrets)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt024, "Selected secret access exceeds the specification.", $"{path}.secrets"));
        }

        RequireSubset(
            selected.AllowedNetworkDestinations,
            allowed.AllowedNetworkDestinations,
            "network destination",
            $"{path}.allowedNetworkDestinations",
            diagnostics);
        RequireSubset(
            selected.AllowedWriteRoots,
            allowed.AllowedWriteRoots,
            "write root",
            $"{path}.allowedWriteRoots",
            diagnostics);
        RequireSubset(
            selected.AllowedSecretReferences,
            allowed.AllowedSecretReferences,
            "secret reference",
            $"{path}.allowedSecretReferences",
            diagnostics);
    }

    private static void ValidateAllowList(
        bool required,
        ImmutableArray<string> values,
        string kind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            return;
        }

        if (required && values.IsEmpty)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt025, $"An explicit {kind} allow-list cannot be empty.", path));
        }
        else if (!required && !values.IsEmpty)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt026, $"{kind} entries require the corresponding explicit policy.", path));
        }
    }

    private static void RequireSubset(
        ImmutableArray<string> selected,
        ImmutableArray<string> allowed,
        string kind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (selected.IsDefault || allowed.IsDefault)
        {
            return;
        }

        foreach (var value in selected)
        {
            if (!allowed.Contains(value, StringComparer.Ordinal))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt027, $"Selected {kind} '{value}' is not permitted.", path));
            }
        }
    }

    private static bool IsNetworkSelectionAllowed(
        NetworkAccessPolicy allowed,
        NetworkAccessPolicy selected) =>
        selected == NetworkAccessPolicy.Denied ||
        selected == allowed;

    private static bool IsWriteSelectionAllowed(
        WriteAccessPolicy allowed,
        WriteAccessPolicy selected) =>
        selected == WriteAccessPolicy.Denied ||
        selected == allowed;
}

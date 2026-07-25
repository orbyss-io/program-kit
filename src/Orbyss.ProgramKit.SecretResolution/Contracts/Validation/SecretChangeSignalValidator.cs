using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Validation;

/// <summary>Validates safe generation, expiry, revocation, and failure metadata.</summary>
public sealed class SecretChangeSignalValidator :
    IProgramKitSemanticValidator<SecretChangeSignal>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(SecretChangeSignal value)
        => ValidateSignal(value);

    /// <summary>Validates one metadata-only signal without a runtime service instance.</summary>
    public static ProgramKitValidationResult ValidateSignal(SecretChangeSignal value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        SecretResolutionValidation.RequireIdentifier(
            value.ReferenceIdentity,
            "$.referenceIdentity",
            diagnostics);
        SecretResolutionValidation.ValidateEnum(value.Kind, "$.kind", diagnostics);
        if (value.Kind == SecretChangeKind.Unspecified)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "A material-free change kind is required.",
                "$.kind"));
        }

        if (value.PreviousGeneration < 0)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "The previous generation cannot be negative.",
                "$.previousGeneration"));
        }

        ValidateLifecycle(value, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateLifecycle(
        SecretChangeSignal value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Lifecycle is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "Lifecycle metadata is required.",
                "$.lifecycle"));
            return;
        }

        var lifecycle = value.Lifecycle;
        SecretResolutionValidation.ValidateEnum(lifecycle.Status, "$.lifecycle.status", diagnostics);
        if (lifecycle.Generation < 0 ||
            lifecycle.Generation < value.PreviousGeneration)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "Safe generation must be non-negative and cannot move backwards.",
                "$.lifecycle.generation"));
        }

        if (lifecycle.Status == SecretResolutionStatus.Available &&
            lifecycle.ExpiresAt is not null &&
            lifecycle.ExpiresAt <= lifecycle.ObservedAt)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "An available capability cannot already be expired.",
                "$.lifecycle.expiresAt"));
        }

        if ((value.Kind == SecretChangeKind.Expired ||
             lifecycle.Status == SecretResolutionStatus.Expired) &&
            lifecycle.ExpiresAt is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "Expiry status requires an explicit expiry boundary.",
                "$.lifecycle.expiresAt"));
        }

        if (!StatusMatchesKind(value.Kind, lifecycle.Status))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "The change kind and lifecycle status are inconsistent.",
                "$.lifecycle.status"));
        }
    }

    private static bool StatusMatchesKind(
        SecretChangeKind kind,
        SecretResolutionStatus status) =>
        kind switch
        {
            SecretChangeKind.GenerationChanged or SecretChangeKind.Expiring =>
                status == SecretResolutionStatus.Available,
            SecretChangeKind.Expired => status == SecretResolutionStatus.Expired,
            SecretChangeKind.Revoked => status == SecretResolutionStatus.Revoked,
            SecretChangeKind.Denied => status == SecretResolutionStatus.Denied,
            SecretChangeKind.ProviderUnavailable =>
                status == SecretResolutionStatus.ProviderUnavailable,
            SecretChangeKind.Failed => status == SecretResolutionStatus.Failed,
            _ => false,
        };
}

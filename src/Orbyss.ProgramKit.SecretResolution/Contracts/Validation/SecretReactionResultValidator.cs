using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Validation;

/// <summary>Rejects false application-success reports and unsafe diagnostics.</summary>
public sealed class SecretReactionResultValidator :
    IProgramKitSemanticValidator<SecretReactionResult>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(SecretReactionResult value)
        => ValidateResult(value);

    /// <summary>Validates one result without requiring a runtime service instance.</summary>
    public static ProgramKitValidationResult ValidateResult(SecretReactionResult value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        SecretResolutionValidation.RequireIdentifier(
            value.ReferenceIdentity,
            "$.referenceIdentity",
            diagnostics);
        SecretResolutionValidation.ValidateEnum(value.Reaction, "$.reaction", diagnostics);
        SecretResolutionValidation.ValidateEnum(value.Status, "$.status", diagnostics);
        if (value.SafeDiagnosticCode is not null)
        {
            SecretResolutionValidation.RequireIdentifier(
                value.SafeDiagnosticCode.Value,
                "$.safeDiagnosticCode",
                diagnostics);
        }

        if (value.Generation < 0)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidLifecycle,
                "The safe generation cannot be negative.",
                "$.generation"));
        }

        if (value.Status == SecretReactionStatus.Succeeded &&
            value.Reaction is (SecretConsumerReaction.Manual or
                SecretConsumerReaction.Unsupported))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.FalseSuccess,
                "Manual or unsupported rotation cannot be reported as successful application reconfiguration.",
                "$.status"));
        }

        if (value.Status is (SecretReactionStatus.Failed or SecretReactionStatus.Rejected) &&
            value.SafeDiagnosticCode is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "Failed or rejected reactions require a stable safe diagnostic code.",
                "$.safeDiagnosticCode"));
        }

        if (value.Status is (SecretReactionStatus.Pending or SecretReactionStatus.Succeeded) &&
            value.SafeDiagnosticCode is not null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.FalseSuccess,
                "Pending or successful reactions cannot carry a failure diagnostic.",
                "$.safeDiagnosticCode"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}

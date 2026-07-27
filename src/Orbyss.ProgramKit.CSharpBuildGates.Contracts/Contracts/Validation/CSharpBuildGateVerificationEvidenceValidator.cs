using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>Pure verification-evidence validation.</summary>
public sealed class CSharpBuildGateVerificationEvidenceValidator :
    IProgramKitSemanticValidator<CSharpBuildGateVerificationEvidenceDocument>
{
    private static readonly SemanticVersion Version = new("1.0.0");

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        CSharpBuildGateVerificationEvidenceDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$",
                "C# build-gate verification evidence is required.");
        }
        else
        {
            diagnostics.Require(
                value.Version == Version && value.SelectionLock is not null,
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$",
                "Verification evidence 1.0.0 requires an exact selection lock.");
            diagnostics.Require(
                value.Succeeded
                    ? value.FailureLayer is null
                    : value.FailureLayer is not null,
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$.failureLayer",
                "Successful evidence has no failure layer; failed evidence identifies exactly one layer.");
            CSharpBuildGateValidation.ValidateStableUnique(
                value.ParticipationReceipts,
                static receipt => string.Concat(
                    receipt.Identity.Value,
                    "@",
                    receipt.Version.Value,
                    "#",
                    receipt.Digest.Value),
                "$.participationReceipts",
                diagnostics);
            CSharpBuildGateValidation.ValidateStableUnique(
                value.ExceptionUseReceipts,
                static receipt => string.Concat(
                    receipt.Identity.Value,
                    "@",
                    receipt.Version.Value,
                    "#",
                    receipt.Digest.Value),
                "$.exceptionUseReceipts",
                diagnostics,
                requireOne: false);
            CSharpBuildGateValidation.ValidateStableUnique(
                value.ConsumedSuppressionIds,
                static identity => identity.Value,
                "$.consumedSuppressionIds",
                diagnostics,
                requireOne: false);
        }

        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }
}

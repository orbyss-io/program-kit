using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>Pure same-assembly receipt validation.</summary>
public sealed class CSharpGateParticipationReceiptValidator :
    IProgramKitSemanticValidator<CSharpGateParticipationReceiptDocument>
{
    private static readonly SemanticVersion Version = new("1.0.0");

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        CSharpGateParticipationReceiptDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$",
                "A participation receipt is required.");
        }
        else
        {
            diagnostics.Require(
                value.Version == Version &&
                value.SelectionLock is not null &&
                !string.IsNullOrWhiteSpace(value.CompilationNonce),
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$",
                "Participation receipt 1.0.0 requires an exact lock and compilation nonce.");
            diagnostics.Require(
                value.ValidatedCompilerInputDigest ==
                    value.ExecutedCompilerInputDigest,
                CSharpBuildGateDiagnosticIds.Pkcg012,
                "$.executedCompilerInputDigest",
                "Validated and executed compiler inputs must match exactly.");
        }

        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }
}

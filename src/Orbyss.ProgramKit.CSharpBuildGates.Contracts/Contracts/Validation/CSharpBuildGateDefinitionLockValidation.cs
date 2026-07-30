using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>Cross-checks a definition against its exact materialized lock.</summary>
public static class CSharpBuildGateDefinitionLockValidation
{
    /// <summary>Validates exact reference and receipt cardinality relationships.</summary>
    public static ProgramKitValidationResult Validate(
        CSharpBuildGateDefinitionDocument definition,
        ArtifactReference definitionReference,
        CSharpBuildGateSelectionLockDocument selectionLock)
    {
        ArgumentNullException.ThrowIfNull(definition);
        ArgumentNullException.ThrowIfNull(definitionReference);
        ArgumentNullException.ThrowIfNull(selectionLock);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Require(
            selectionLock.GateDefinition == definitionReference,
            CSharpBuildGateDiagnosticIds.Pkcg011,
            "$.gateDefinition",
            "The selection lock must bind the exact definition identity, version, and digest.");
        var expected = definition.ActivationMatrix.Activations
            .SelectMany(activation =>
                activation.AnalyzerComponentIds.Select(component =>
                    ReceiptScopeKey(
                        activation.ProjectProfileId,
                        component,
                        activation.VerificationProfile)))
            .ToHashSet(StringComparer.Ordinal);
        var observed = selectionLock.ExpectedReceipts
            .Select(static receipt => ReceiptScopeKey(
                receipt.ProjectProfileId,
                receipt.AnalyzerComponentId,
                receipt.VerificationProfile))
            .ToArray();
        diagnostics.Require(
            observed.Length == observed.Distinct(StringComparer.Ordinal).Count() &&
            expected.SetEquals(observed),
            CSharpBuildGateDiagnosticIds.Pkcg011,
            "$.expectedReceipts",
            "The selection lock requires exactly one expected same-assembly receipt per selected analyzer and covered compilation profile.");
        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }

    private static string ReceiptScopeKey(
        ProgramKitIdentifier projectProfileId,
        ProgramKitIdentifier analyzerComponentId,
        CSharpGateVerificationProfileKind verificationProfile) =>
        string.Join(
            "|",
            projectProfileId.Value,
            analyzerComponentId.Value,
            CSharpBuildGateOrdering.Kebab(verificationProfile));
}

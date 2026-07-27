using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>Fail-closed reconciliation for source-local suppressions.</summary>
public static class CSharpGateSuppressionReconciliationValidation
{
    /// <summary>Rejects stale, duplicate, unknown, or unconsumed ledger entries.</summary>
    public static ProgramKitValidationResult Validate(
        CSharpGateSuppressionLedger ledger,
        CSharpGateSuppressionReconciliation reconciliation)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        ArgumentNullException.ThrowIfNull(reconciliation);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var known = ledger.Entries
            .Select(static entry => entry.Identity)
            .ToHashSet();
        var consumed = reconciliation.ConsumedEntryIds.IsDefault
            ? []
            : reconciliation.ConsumedEntryIds;
        diagnostics.Require(
            consumed.Length == consumed.Distinct().Count() &&
            known.SetEquals(consumed),
            CSharpBuildGateDiagnosticIds.Pkcg010,
            "$.consumedEntryIds",
            "Suppression reconciliation requires every exact entry once and no unknown entry.");
        diagnostics.Require(
            ledger.Entries.All(entry =>
                entry.ExpiresAt is null ||
                entry.ExpiresAt > reconciliation.EvaluationInstant),
            CSharpBuildGateDiagnosticIds.Pkcg010,
            "$.evaluationInstant",
            "Expired suppression entries fail closed.");
        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }
}

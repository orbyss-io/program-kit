using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Execution reconciliation for exact suppression consumption.</summary>
public sealed record CSharpGateSuppressionReconciliation(
    ImmutableArray<ProgramKitIdentifier> ConsumedEntryIds,
    DateTimeOffset EvaluationInstant);

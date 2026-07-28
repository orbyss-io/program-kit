using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// StaticConformanceDisposition 0.1.0-alpha.1 preserves the five explicit
/// human decision states of the legacy 1.0.0 contract.
/// </summary>
public sealed record StaticConformanceDispositionAlpha1(
    ArtifactReference SoftwareDesign,
    ImmutableArray<StaticInvariantAllocation> InvariantAllocations,
    StaticConformanceDispositionKind Disposition,
    ImmutableArray<StaticConformanceGateSelection> GateSelections,
    ImmutableArray<ArtifactReference> LinkedGateDesigns,
    string Rationale,
    ImmutableArray<string> ResidualRisks,
    ImmutableArray<string> NonStaticClaims,
    StaticConformanceDecisionSource DecisionSource,
    ArtifactReference? EmptySelectionAcceptance,
    ImmutableArray<string> Blockers);

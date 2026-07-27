using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// The independently versioned static-conformance decision incorporated into
/// one exact software-design revision.
/// </summary>
public sealed record StaticConformanceDisposition(
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

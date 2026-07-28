using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Implementation Plan 0.1.0-alpha.3 preserves Planning 3.0 execution
/// semantics while selecting alpha design-flow contracts.
/// </summary>
public sealed record ImplementationPlanDocumentAlpha3(
    ArtifactReference Design,
    ProgramKitIdentifier OwnerId,
    ImplementationPlanState State,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<PlanWorkUnitV3> WorkUnits,
    ImmutableArray<PlanParallelGroup> ParallelGroups,
    ImmutableArray<RequirementTrace> Trace,
    ImmutableArray<PlanUnresolvedDecision> UnresolvedDecisions,
    ArtifactReference StaticConformanceDisposition,
    StaticConformancePlanState StaticConformanceState,
    ArtifactReference? GateDesign,
    PlannedArtifactReference? GateDefinition,
    PlannedArtifactReference? SelectionLock,
    PlannedArtifactReference? ActivationEvidence);

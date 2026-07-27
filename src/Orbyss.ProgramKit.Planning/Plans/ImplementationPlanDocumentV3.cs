using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Planning 3.0 binds an exact static disposition and the gate artifacts needed
/// to admit work without changing the existing plan execution authority.
/// </summary>
public sealed record ImplementationPlanDocumentV3(
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

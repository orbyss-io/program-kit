using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Describes implementation separately from, and by exact reference to, its source design.
/// </summary>
public sealed record ImplementationPlanDocument(
    ArtifactReference Design,
    ProgramKitIdentifier OwnerId,
    ImplementationPlanState State,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<PlanWorkUnit> WorkUnits,
    ImmutableArray<PlanParallelGroup> ParallelGroups,
    ImmutableArray<RequirementTrace> Trace,
    ImmutableArray<PlanUnresolvedDecision> UnresolvedDecisions);

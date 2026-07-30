using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Current Implementation Plan alpha writer with an exact schema identity.</summary>
public sealed record ImplementationPlanDocumentAlpha4(
    [property: JsonPropertyName("$schema")] string Schema,
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
    PlannedArtifactReference? ActivationEvidence)
{
    /// <summary>The only schema URI emitted by this writer.</summary>
    public const string SchemaUri =
        "https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.4/schema.json";
}

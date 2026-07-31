using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Current Implementation Plan writer with explicit approval and execution
/// binding modes.
/// </summary>
public sealed record ImplementationPlanDocumentAlpha5(
    [property: JsonPropertyName("$schema")] string Schema,
    ArtifactReference Design,
    ProgramKitIdentifier OwnerId,
    ImplementationPlanState State,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<PlanWorkUnitAlpha5> WorkUnits,
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
        "https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.5/schema.json";
}

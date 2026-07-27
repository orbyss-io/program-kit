using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Exact human-supplied decisions required to migrate a Planning 2.0 document.
/// No value is inferred from sequence, paths, names, or repository state.
/// </summary>
public sealed record ImplementationPlanV3MigrationInput(
    ArtifactReference StaticConformanceDisposition,
    StaticConformancePlanState StaticConformanceState,
    ArtifactReference? GateDesign,
    PlannedArtifactReference? GateDefinition,
    PlannedArtifactReference? SelectionLock,
    PlannedArtifactReference? ActivationEvidence,
    ImmutableArray<PlanWorkUnitV3Binding> WorkUnitBindings);

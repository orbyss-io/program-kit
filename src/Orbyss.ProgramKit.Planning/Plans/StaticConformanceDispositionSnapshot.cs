using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Observed state of the exact disposition artifact bound by a plan. Callers
/// derive this snapshot from the validated disposition; Planning does not
/// duplicate or interpret the Architecture artifact.
/// </summary>
public sealed record StaticConformanceDispositionSnapshot(
    ArtifactReference Disposition,
    StaticConformancePlanState State);

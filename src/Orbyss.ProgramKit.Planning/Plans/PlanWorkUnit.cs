using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Defines one bounded and independently verifiable implementation unit.</summary>
public sealed record PlanWorkUnit(
    string WorkUnitId,
    string RequiredOutcome,
    int Sequence,
    string? ParallelGroupId,
    ImmutableArray<string> DependsOn,
    ImmutableArray<ArtifactReference> Inputs,
    ImmutableArray<PlannedArtifactReference> Outputs,
    ImmutableArray<string> AllowedEdits,
    ImmutableArray<PlanDependency> SourceDependencies,
    ImmutableArray<PlanDependency> ExternalDependencies,
    ImmutableArray<ArtifactReference> Migrations,
    ImmutableArray<PlanCompatibilityRequirement> Compatibility,
    ImmutableArray<string> StopConditions,
    ImmutableArray<PlanVerificationCommand> Verification,
    ImmutableArray<TestSpecificationSelection> SelectedTests);

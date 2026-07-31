using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Planning alpha.5 work unit with explicit approval-time or execution-time
/// artifact binding semantics.
/// </summary>
public sealed record PlanWorkUnitAlpha5(
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
    ImmutableArray<TestSpecificationSelection> SelectedTests,
    PlanWorkUnitKind WorkUnitKind,
    PlanArtifactBinding? ActivationMatrix,
    PlanArtifactBinding? VerificationProfile);

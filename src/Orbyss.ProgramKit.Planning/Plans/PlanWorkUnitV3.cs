using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Planning 3.0 work unit with an explicit role and exact gate activation
/// references. Existing Planning 2.0 work units remain independently readable.
/// </summary>
public sealed record PlanWorkUnitV3(
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
    ArtifactReference? ActivationMatrix,
    ArtifactReference? VerificationProfile);

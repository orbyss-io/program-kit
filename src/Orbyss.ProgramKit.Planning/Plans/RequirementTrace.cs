using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Provides the required end-to-end trace for one design requirement.</summary>
public sealed record RequirementTrace(
    string RequirementId,
    ProgramKitIdentifier OwnerId,
    ArtifactReference ContractOrArtifact,
    ImmutableArray<string> WorkUnitIds,
    string ImplementationOutcome,
    ImmutableArray<ArtifactReference> DependencyOrExtensionImpact,
    ImmutableArray<TestSpecificationSelection> Tests,
    ImmutableArray<ArtifactReference> Evidence,
    string ObservableAcceptanceOutcome);

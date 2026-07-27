using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Evidence;

/// <summary>Binds observations to the exact specification, profile, and tested subject.</summary>
public sealed record TestEvidence(
    ArtifactReference Specification,
    ProfileReference Profile,
    ArtifactReference Subject,
    TestEvidenceOutcome Outcome,
    ImmutableArray<TestObservation> Observations,
    ProgramKitIdentifier ProducerId,
    DateTimeOffset ObservedAt,
    string CorrelationId);

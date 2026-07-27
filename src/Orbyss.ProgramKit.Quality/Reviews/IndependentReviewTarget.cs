using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Reviews;

/// <summary>Identifies the independently reviewed artifact or exact delta.</summary>
public sealed record IndependentReviewTarget(
    IndependentReviewTargetKind Kind,
    ArtifactReference Artifact,
    ArtifactReference? BaseArtifact);

using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Reviews;

/// <summary>
/// Records review performed by a principal other than the producer without implying approval authority.
/// </summary>
public sealed record IndependentReview(
    IndependentReviewTarget Target,
    ProgramKitIdentifier ProducerId,
    ProgramKitIdentifier ReviewerId,
    IndependentReviewDisposition Disposition,
    ImmutableArray<ArtifactReference> Evidence,
    string Summary,
    DateTimeOffset ReviewedAt);

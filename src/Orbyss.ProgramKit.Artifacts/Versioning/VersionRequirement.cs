using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>A required exact resolution constrained by an accepted version range.</summary>
/// <param name="Identity">The required semantic identity.</param>
/// <param name="AcceptedRange">The accepted range.</param>
/// <param name="Resolution">The exact resolved revision.</param>
/// <param name="Exposure">Whether the requirement is publicly exposed.</param>
/// <param name="Dimensions">Compatibility dimensions relevant to the requirement.</param>
/// <param name="EvidenceReferences">Exact evidence supporting the requirement.</param>
public sealed record VersionRequirement(
    ProgramKitIdentifier Identity,
    SemanticVersionRange AcceptedRange,
    ArtifactReference Resolution,
    DependencyExposure Exposure,
    ImmutableArray<CompatibilityDimension> Dimensions,
    ImmutableArray<ArtifactReference> EvidenceReferences);

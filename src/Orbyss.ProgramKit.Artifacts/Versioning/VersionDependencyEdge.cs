using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>A typed, exactly resolved dependency edge.</summary>
/// <param name="Id">The stable edge identity.</param>
/// <param name="Source">The exact dependent revision.</param>
/// <param name="TargetIdentity">The required semantic identity.</param>
/// <param name="Kind">The semantic dependency kind.</param>
/// <param name="AcceptedRange">The accepted target range.</param>
/// <param name="Resolution">The exact target resolution.</param>
/// <param name="Exposure">Whether the edge is publicly exposed.</param>
/// <param name="CompatibilityDimensions">Dimensions relevant to the dependency.</param>
/// <param name="EvidenceReferences">Exact evidence supporting the edge.</param>
public sealed record VersionDependencyEdge(
    ProgramKitIdentifier Id,
    ArtifactReference Source,
    ProgramKitIdentifier TargetIdentity,
    VersionDependencyKind Kind,
    SemanticVersionRange AcceptedRange,
    ArtifactReference Resolution,
    DependencyExposure Exposure,
    ImmutableArray<CompatibilityDimension> CompatibilityDimensions,
    ImmutableArray<ArtifactReference> EvidenceReferences);

using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>A revision node in an immutable version-map snapshot.</summary>
/// <param name="Revision">The exact node revision.</param>
/// <param name="Kind">The represented boundary kind.</param>
/// <param name="OwnerId">The owner responsible for migration decisions.</param>
/// <param name="EvidenceReferences">Exact evidence describing the revision.</param>
public sealed record VersionRevisionNode(
    ArtifactReference Revision,
    VersionBoundaryKind Kind,
    ProgramKitIdentifier OwnerId,
    ImmutableArray<ArtifactReference> EvidenceReferences);

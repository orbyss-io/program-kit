using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>A closed classification of version-bearing repository sources.</summary>
/// <param name="RepositoryRoot">Explicit normalized inventory root.</param>
/// <param name="SourceRoots">Finite normalized roots included by observation.</param>
/// <param name="Entries">Exact observed and classified version-bearing sources.</param>
/// <param name="CompletenessEvidence">Evidence proving the observation boundary.</param>
public sealed record VersionIntentInventoryDocument(
    string RepositoryRoot,
    ImmutableArray<string> SourceRoots,
    ImmutableArray<VersionIntentInventoryEntry> Entries,
    ImmutableArray<ArtifactReference> CompletenessEvidence);

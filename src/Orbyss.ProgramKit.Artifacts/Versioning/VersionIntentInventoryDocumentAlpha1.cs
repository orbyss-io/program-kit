using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Immutable inventory document shape from contract 0.1.0-alpha.1.</summary>
public sealed record VersionIntentInventoryDocumentAlpha1(
    string RepositoryRoot,
    ImmutableArray<string> SourceRoots,
    ImmutableArray<VersionIntentInventoryEntryAlpha1> Entries,
    ImmutableArray<ArtifactReference> CompletenessEvidence);

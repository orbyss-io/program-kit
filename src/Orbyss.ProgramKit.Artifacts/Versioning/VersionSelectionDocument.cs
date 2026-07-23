using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>An immutable set of observed and human-selected exact revisions.</summary>
/// <param name="InputVersionMap">The immutable version map used for selection.</param>
/// <param name="Selections">Selections keyed by stable identity.</param>
public sealed record VersionSelectionDocument(
    ArtifactReference InputVersionMap,
    ImmutableArray<VersionSelection> Selections);

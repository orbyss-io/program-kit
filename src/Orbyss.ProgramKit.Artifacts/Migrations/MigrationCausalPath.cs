using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>A retained causal path from a changed root to an impacted revision.</summary>
/// <param name="ChangedRoot">The changed root revision.</param>
/// <param name="EdgeIds">Ordered version-map edge identities.</param>
public sealed record MigrationCausalPath(
    ArtifactReference ChangedRoot,
    ImmutableArray<ProgramKitIdentifier> EdgeIds);

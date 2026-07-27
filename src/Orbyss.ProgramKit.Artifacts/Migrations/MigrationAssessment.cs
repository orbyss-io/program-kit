using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>An immutable, action-complete migration impact assessment.</summary>
/// <param name="VersionMapReference">The exact immutable version map.</param>
/// <param name="VersionSelectionReference">The exact immutable selection.</param>
/// <param name="ChangedRevisions">All changed root revisions.</param>
/// <param name="Impacts">One terminal impact per reached revision.</param>
/// <param name="Waves">Dependency-safe migration waves.</param>
public sealed record MigrationAssessment(
    ArtifactReference VersionMapReference,
    ArtifactReference VersionSelectionReference,
    ImmutableArray<ArtifactReference> ChangedRevisions,
    ImmutableArray<MigrationImpact> Impacts,
    ImmutableArray<MigrationWave> Waves);

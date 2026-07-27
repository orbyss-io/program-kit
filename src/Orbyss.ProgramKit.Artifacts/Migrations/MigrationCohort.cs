using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>An atomic migration cohort, including a strongly connected component when necessary.</summary>
/// <param name="Id">The stable cohort identity.</param>
/// <param name="Members">Exact target revisions migrated atomically.</param>
public sealed record MigrationCohort(
    ProgramKitIdentifier Id,
    ImmutableArray<ArtifactReference> Members);

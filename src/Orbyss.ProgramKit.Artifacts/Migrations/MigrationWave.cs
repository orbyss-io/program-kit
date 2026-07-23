using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>One dependency-safe migration wave.</summary>
/// <param name="Ordinal">The zero-based wave ordinal.</param>
/// <param name="Cohorts">Atomic cohorts in deterministic order.</param>
public sealed record MigrationWave(
    int Ordinal,
    ImmutableArray<MigrationCohort> Cohorts);

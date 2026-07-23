using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>An ordered action required by a migration assessment.</summary>
public enum MigrationRequiredAction
{
    /// <summary>Repeat relevant tests.</summary>
    Retest,

    /// <summary>Regenerate derived outputs.</summary>
    Regenerate,

    /// <summary>Recompile affected source.</summary>
    Recompile,

    /// <summary>Repackage or recreate an immutable lock.</summary>
    RepackageOrRelock,

    /// <summary>Transform a durable artifact.</summary>
    MigrateArtifact,

    /// <summary>Transform configuration.</summary>
    MigrateConfiguration,

    /// <summary>Add an explicit compatibility adapter.</summary>
    AddAdapter,

    /// <summary>Drain or migrate pending work.</summary>
    DrainOrMigratePendingWork,
}

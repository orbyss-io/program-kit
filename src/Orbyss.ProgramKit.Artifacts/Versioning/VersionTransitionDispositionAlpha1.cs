namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Immutable transition dispositions from inventory contract 0.1.0-alpha.1.</summary>
public enum VersionTransitionDispositionAlpha1
{
    /// <summary>Project one explicit coordinated product release.</summary>
    CoordinateProductRelease,

    /// <summary>Create and select an explicit migrated owned-artifact revision.</summary>
    MigrateOwnedRevision,

    /// <summary>Retain an external owner's exact selected value.</summary>
    PreserveExternalSelection,

    /// <summary>Retain immutable historical evidence bytes and version meaning.</summary>
    PreserveHistoricalEvidence,

    /// <summary>Retain an explicit synthetic fixture value.</summary>
    PreserveFixture,
}

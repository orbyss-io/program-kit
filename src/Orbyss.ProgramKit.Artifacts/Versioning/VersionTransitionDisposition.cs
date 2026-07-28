namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Declares the approved transition treatment for one inventory entry.</summary>
public enum VersionTransitionDisposition
{
    /// <summary>Project one explicit coordinated product release.</summary>
    CoordinateProductRelease,

    /// <summary>Create and select an explicit migrated owned-artifact revision.</summary>
    MigrateOwnedRevision,

    /// <summary>Retain an owned artifact that already uses the selected alpha revision.</summary>
    RetainOwnedRevision,

    /// <summary>Retain an external owner's exact selected value.</summary>
    PreserveExternalSelection,

    /// <summary>Retain immutable historical evidence bytes and version meaning.</summary>
    PreserveHistoricalEvidence,

    /// <summary>Retain an explicit synthetic fixture value.</summary>
    PreserveFixture,
}

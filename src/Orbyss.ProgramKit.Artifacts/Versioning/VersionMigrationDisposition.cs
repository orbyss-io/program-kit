namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Declares whether an explicit revision migration is required.</summary>
public enum VersionMigrationDisposition
{
    /// <summary>No migration is required for the explicit proposal.</summary>
    NotRequired,

    /// <summary>At least one exact migration definition is required.</summary>
    Required,
}

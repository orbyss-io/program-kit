namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Classifies compatibility without assigning stable SemVer significance.</summary>
public enum VersionCompatibilityDisposition
{
    /// <summary>The proposal introduces the first revision of a new identity.</summary>
    NewIdentity,

    /// <summary>Canonical bytes and the exact revision remain unchanged.</summary>
    Unchanged,

    /// <summary>The changed revision is explicitly classified as compatible.</summary>
    Compatible,

    /// <summary>The changed revision is explicitly classified as incompatible.</summary>
    Incompatible,
}

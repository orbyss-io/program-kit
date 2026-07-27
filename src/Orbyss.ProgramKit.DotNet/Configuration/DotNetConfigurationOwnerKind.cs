namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Authority that owns configuration meaning and compatibility.</summary>
public enum DotNetConfigurationOwnerKind
{
    /// <summary>Program Kit owns the definition.</summary>
    ProgramKit,
    /// <summary>An external component owner supplies the definition.</summary>
    External,
}

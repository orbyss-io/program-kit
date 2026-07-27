namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Controls whether explicitly selected contributions may extend a profile.</summary>
public enum JsonProfileExtensibility
{
    /// <summary>The profile accepts no contributions.</summary>
    None,

    /// <summary>The host may select explicit, compatible contributions.</summary>
    ExplicitContributions,
}

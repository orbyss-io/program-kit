namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Classifies the mechanics bound by one digest-source document.</summary>
public enum JsonProfileSourceKind
{
    /// <summary>A typed serialization profile.</summary>
    Serialization,

    /// <summary>The fixed canonicalization profile.</summary>
    Canonicalization,
}

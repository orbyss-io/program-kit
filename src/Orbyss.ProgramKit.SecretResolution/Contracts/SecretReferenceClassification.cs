namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Disclosure classification for non-secret reference metadata.</summary>
public enum SecretReferenceClassification
{
    /// <summary>No disclosure classification was selected.</summary>
    Unspecified,
    /// <summary>Metadata is non-secret but must be redacted from normal output.</summary>
    RestrictedMetadata,
    /// <summary>Metadata can reveal sensitive operational topology and must be redacted.</summary>
    SensitiveMetadata,
}

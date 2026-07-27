namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Projection and diagnostic handling for one value.</summary>
public enum DotNetConfigurationValueClassification
{
    /// <summary>Non-sensitive material may appear in generated examples.</summary>
    Public,
    /// <summary>Sensitive material is never emitted by Program Kit.</summary>
    Sensitive,
    /// <summary>An opaque reference is not considered safe to emit or log.</summary>
    SecretReference,
}

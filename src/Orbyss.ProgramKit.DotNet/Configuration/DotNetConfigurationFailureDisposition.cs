namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Failure behavior after an explicitly configured source operation fails.</summary>
public enum DotNetConfigurationFailureDisposition
{
    /// <summary>Fail the host operation.</summary>
    Fail,
    /// <summary>Continue only when the source is explicitly optional.</summary>
    ContinueWithoutSource,
}

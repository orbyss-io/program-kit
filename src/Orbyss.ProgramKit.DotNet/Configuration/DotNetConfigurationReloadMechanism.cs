namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Finite mechanism by which a provider can emit configuration change tokens.</summary>
public enum DotNetConfigurationReloadMechanism
{
    /// <summary>The provider has no automatic reload mechanism.</summary>
    None,
    /// <summary>A file provider emits change tokens from watched filesystem changes.</summary>
    FileProviderChangeToken,
}

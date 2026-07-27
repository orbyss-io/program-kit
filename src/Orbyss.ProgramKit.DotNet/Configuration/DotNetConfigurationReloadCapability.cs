namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Provider reload signal available to Options consumers.</summary>
public enum DotNetConfigurationReloadCapability
{
    /// <summary>No reload signal exists.</summary>
    None,
    /// <summary>The provider emits an IConfiguration change token.</summary>
    ChangeToken,
    /// <summary>The provider polls its external source and emits a change token.</summary>
    ProviderPolling,
    /// <summary>An explicitly bound refresh operation emits a change token.</summary>
    ExplicitRefresh,
}

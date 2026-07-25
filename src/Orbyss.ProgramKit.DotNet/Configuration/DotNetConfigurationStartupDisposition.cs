namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Startup behavior when a configuration source cannot be loaded.</summary>
public enum DotNetConfigurationStartupDisposition
{
    /// <summary>Startup must fail.</summary>
    Required,
    /// <summary>The explicitly optional source may be absent.</summary>
    Optional,
}

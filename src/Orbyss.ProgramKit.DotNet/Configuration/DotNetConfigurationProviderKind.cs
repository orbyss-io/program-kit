namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Closed built-in provider kinds supported by the configuration compiler.</summary>
public enum DotNetConfigurationProviderKind
{
    /// <summary>JSON file provider.</summary>
    JsonFile,
    /// <summary>Environment-variable provider.</summary>
    EnvironmentVariables,
    /// <summary>Command-line provider.</summary>
    CommandLine,
    /// <summary>Key-per-file provider.</summary>
    KeyPerFile,
}

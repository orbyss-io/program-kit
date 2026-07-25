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
    /// <summary>Explicit secret-free in-memory provider.</summary>
    InMemory,
    /// <summary>Development-only user-secrets provider.</summary>
    UserSecrets,
    /// <summary>Key-per-file provider.</summary>
    KeyPerFile,
    /// <summary>Explicit chained configuration built from secret-free in-memory data.</summary>
    ChainedConfiguration,
    /// <summary>An exact explicitly registered provider adapter; never an arbitrary type name.</summary>
    RegisteredAdapter,
}

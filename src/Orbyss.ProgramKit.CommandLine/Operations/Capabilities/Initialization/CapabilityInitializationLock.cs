namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Exact multi-provider ownership and payload evidence for one workspace.</summary>
public sealed record CapabilityInitializationLock(
    string LockVersion,
    string CliVersion,
    string BundleVersion,
    string ManifestVersion,
    string ManifestSha256,
    CapabilityInitializationProviderLock[] Providers,
    CapabilityInitializationResourceLock[] Resources);

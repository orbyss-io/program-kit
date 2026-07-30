namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Exact source and output ownership for one reviewed provider binding.
/// </summary>
public sealed record CapabilityProviderInitializationLock(
    string Provider,
    string BundleVersion,
    string ProgramKitRoot,
    string ManifestSha256,
    CapabilityInitializationLockEntry[] Capabilities);

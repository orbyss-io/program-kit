namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Read-only legacy single-provider lock accepted only by explicit refresh.</summary>
public sealed record LegacyCapabilityInitializationLock(
    string LockVersion,
    string BundleVersion,
    string Provider,
    string ProgramKitRoot,
    string ManifestSha256,
    LegacyCapabilityInitializationLockEntry[] Capabilities);

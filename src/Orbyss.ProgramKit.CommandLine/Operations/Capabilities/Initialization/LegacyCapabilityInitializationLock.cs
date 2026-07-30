namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Legacy single-provider wire shape retained only for exact migration.
/// </summary>
internal sealed record LegacyCapabilityInitializationLock(
    string LockVersion,
    string BundleVersion,
    string Provider,
    string ProgramKitRoot,
    string ManifestSha256,
    CapabilityInitializationLockEntry[] Capabilities);

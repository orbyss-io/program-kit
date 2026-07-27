namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Exact ownership evidence for one workspace provider initialization.</summary>
public sealed record CapabilityInitializationLock(
    string LockVersion,
    string BundleVersion,
    string Provider,
    string ProgramKitRoot,
    string ManifestSha256,
    CapabilityInitializationLockEntry[] Capabilities);

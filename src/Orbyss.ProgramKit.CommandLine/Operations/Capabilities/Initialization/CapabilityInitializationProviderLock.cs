namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>All Program Kit-owned wrappers for one initialized provider.</summary>
public sealed record CapabilityInitializationProviderLock(
    string Provider,
    CapabilityInitializationLockEntry[] Capabilities);

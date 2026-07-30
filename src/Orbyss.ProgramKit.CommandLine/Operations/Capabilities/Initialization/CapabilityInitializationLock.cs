namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Exact ownership evidence for every Program Kit provider binding in one
/// workspace.
/// </summary>
public sealed record CapabilityInitializationLock(
    string LockVersion,
    CapabilityProviderInitializationLock[] Providers);

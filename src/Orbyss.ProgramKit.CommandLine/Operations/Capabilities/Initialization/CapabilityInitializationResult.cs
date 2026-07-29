namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Deterministic initialization outcome for audit-friendly CLI output.</summary>
public sealed record CapabilityInitializationResult(
    string Provider,
    int Created,
    int Updated,
    int Unchanged,
    string LockPath);

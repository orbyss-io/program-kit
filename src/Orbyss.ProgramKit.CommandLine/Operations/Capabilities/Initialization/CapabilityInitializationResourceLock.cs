namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Exact supporting-resource evidence captured at initialization.</summary>
public sealed record CapabilityInitializationResourceLock(
    string ResourceId,
    string Sha256);

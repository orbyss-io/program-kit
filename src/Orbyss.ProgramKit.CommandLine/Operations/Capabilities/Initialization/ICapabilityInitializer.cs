namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Initializes one exact provider adapter in a human-led workspace.</summary>
public interface ICapabilityInitializer
{
    /// <summary>
    /// Verifies canonical source bytes and writes only provider-owned wrappers
    /// plus their ownership lock.
    /// </summary>
    ValueTask<CapabilityInitializationResult> InitializeAsync(
        string provider,
        string workspaceRoot,
        CancellationToken cancellationToken);
}

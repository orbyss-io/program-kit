namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;

/// <summary>Removes one exact provider binding from a human-led workspace.</summary>
public interface ICapabilityUninitializer
{
    /// <summary>
    /// Removes only exact lock-owned wrapper bytes for one selected provider.
    /// </summary>
    ValueTask UninitializeAsync(
        string provider,
        string workspaceRoot,
        CancellationToken cancellationToken);
}

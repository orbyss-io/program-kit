namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Owns recoverable exact file mutation for capability workspace operations.
/// </summary>
public interface ICapabilityWorkspaceTransaction
{
    /// <summary>Recovers one interrupted prior transaction when present.</summary>
    ValueTask RecoverAsync(
        string workspaceRoot,
        CancellationToken cancellationToken);

    /// <summary>Applies one complete ordered mutation set or restores it.</summary>
    ValueTask ApplyAsync(
        string workspaceRoot,
        IReadOnlyList<CapabilityWorkspaceMutation> mutations,
        CancellationToken cancellationToken);
}

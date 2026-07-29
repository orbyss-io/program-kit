using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Readiness;

/// <summary>Fail-closed workspace readiness and exact-byte capability retrieval.</summary>
public interface ICapabilityReadinessService
{
    /// <summary>Evaluates one release-catalog capability without repairing setup.</summary>
    ValueTask<CapabilityReadinessResult> EvaluateAsync(
        string capabilityId,
        string workspaceRoot,
        CancellationToken cancellationToken);

    /// <summary>Evaluates every release-catalog row.</summary>
    ValueTask<ImmutableArray<CapabilityReadinessResult>> CatalogAsync(
        string workspaceRoot,
        CancellationToken cancellationToken);

    /// <summary>Reads canonical bytes only after exact readiness succeeds.</summary>
    ValueTask<ReadOnlyMemory<byte>> ReadCapabilityAsync(
        string capabilityId,
        string workspaceRoot,
        CancellationToken cancellationToken);

    /// <summary>Reads one inert resource after exact workspace setup succeeds.</summary>
    ValueTask<ReadOnlyMemory<byte>> ReadResourceAsync(
        string resourceId,
        string workspaceRoot,
        CancellationToken cancellationToken);
}

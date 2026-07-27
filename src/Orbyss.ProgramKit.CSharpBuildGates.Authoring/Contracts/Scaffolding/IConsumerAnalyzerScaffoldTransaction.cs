namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>
/// Stages finite scaffold files and exposes explicit commit and rollback.
/// </summary>
public interface IConsumerAnalyzerScaffoldTransaction : IAsyncDisposable
{
    /// <summary>Stages one validated relative output without overwriting it.</summary>
    ValueTask WriteAsync(
        string relativePath,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken);

    /// <summary>Atomically publishes the complete staged scaffold.</summary>
    ValueTask CommitAsync(CancellationToken cancellationToken);

    /// <summary>Removes all unpublished staged output.</summary>
    ValueTask RollbackAsync(CancellationToken cancellationToken);
}

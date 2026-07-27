using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation.TestSupport;

internal sealed class RecordingScaffoldTransaction(
    int? failWriteAt = null,
    CancellationTokenSource? cancelAfterFirstWrite = null) :
    IRecordingScaffoldTransaction
{
    private int writes;

    public bool Committed { get; private set; }

    public bool RolledBack { get; private set; }

    public ValueTask WriteAsync(
        string relativePath,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        writes++;
        if (writes == 1)
        {
            cancelAfterFirstWrite?.Cancel();
        }

        if (writes == failWriteAt)
        {
            throw new IOException("Injected scaffold write failure.");
        }

        return ValueTask.CompletedTask;
    }

    public ValueTask CommitAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Committed = true;
        return ValueTask.CompletedTask;
    }

    public ValueTask RollbackAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        RolledBack = true;
        return ValueTask.CompletedTask;
    }

    public ValueTask DisposeAsync()
    {
        return ValueTask.CompletedTask;
    }
}

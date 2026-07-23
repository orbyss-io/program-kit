namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation.TestSupport;

internal sealed class TestOutputTransaction : IWorkbenchOutputTransaction
{
    private readonly List<GeneratedOutput> staged = [];
    private readonly bool failCommit;
    private readonly bool failRollback;

    internal TestOutputTransaction(
        bool failCommit = false,
        bool failRollback = false)
    {
        this.failCommit = failCommit;
        this.failRollback = failRollback;
    }

    internal bool Committed { get; private set; }

    internal bool RolledBack { get; private set; }

    internal IReadOnlyList<GeneratedOutput> Staged => staged;

    public ValueTask StageAsync(
        GeneratedOutput output,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        staged.Add(output);
        return ValueTask.CompletedTask;
    }

    public ValueTask CommitAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (failCommit)
        {
            throw new IOException("Commit failed before publication.");
        }

        Committed = true;
        return ValueTask.CompletedTask;
    }

    public ValueTask RollbackAsync(CancellationToken cancellationToken)
    {
        if (failRollback)
        {
            throw new IOException("Private staging cleanup failed.");
        }

        RolledBack = true;
        Committed = false;
        staged.Clear();
        return ValueTask.CompletedTask;
    }
}

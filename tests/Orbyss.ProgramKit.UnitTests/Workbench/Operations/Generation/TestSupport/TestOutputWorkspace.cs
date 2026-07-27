namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation.TestSupport;

internal sealed class TestOutputWorkspace : IWorkbenchOutputWorkspace
{
    private readonly IWorkbenchOutputTransaction transaction;

    internal TestOutputWorkspace(IWorkbenchOutputTransaction transaction)
    {
        this.transaction = transaction ??
            throw new ArgumentNullException(nameof(transaction));
    }

    public ValueTask<IWorkbenchOutputTransaction> BeginAsync(
        string writeRoot,
        GenerationCollisionPolicy collisionPolicy,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult(transaction);
}

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class TestTaskExecutionLatch : ITestTaskExecutionLatch
{
    private readonly TaskCompletionSource entered =
        new(TaskCreationOptions.RunContinuationsAsynchronously);
    private readonly TaskCompletionSource released =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    public Task Entered => entered.Task;

    public async ValueTask WaitAsync(CancellationToken cancellationToken)
    {
        entered.TrySetResult();
        await released.Task.WaitAsync(cancellationToken).ConfigureAwait(false);
    }

    internal void Release() => released.TrySetResult();
}

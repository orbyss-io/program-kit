using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class TestBlockingTaskHandler :
    ITaskHandler<TestTaskRequestModel, TestTaskResponseModel>
{
    private readonly ITestTaskExecutionLatch latch;

    public TestBlockingTaskHandler(ITestTaskExecutionLatch latch)
    {
        this.latch = latch ??
            throw new ArgumentNullException(nameof(latch));
    }

    public async ValueTask<TestTaskResponseModel> HandleAsync(
        TaskHandlerContext context,
        TestTaskRequestModel request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(request);
        await latch.WaitAsync(cancellationToken).ConfigureAwait(false);
        return new TestTaskResponseModel(request.Subject);
    }
}

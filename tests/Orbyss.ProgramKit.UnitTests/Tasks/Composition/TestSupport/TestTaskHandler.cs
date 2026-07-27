using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Execution;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;

internal sealed class TestTaskHandler :
    ITaskHandler<TestTaskRequestModel, TestTaskResponseModel>
{
    public ValueTask<TestTaskResponseModel> HandleAsync(
        TaskHandlerContext context,
        TestTaskRequestModel request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(
            new TestTaskResponseModel(request.Subject));
    }
}

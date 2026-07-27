using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Middleware;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class UnselectedTestDispatchMiddleware :
    ITaskDispatchMiddleware
{
    private readonly TestTaskMiddlewareTracker tracker;

    public UnselectedTestDispatchMiddleware(
        TestTaskMiddlewareTracker tracker)
    {
        this.tracker = tracker ??
            throw new ArgumentNullException(nameof(tracker));
    }

    public ValueTask<TaskDispatchResult> InvokeAsync(
        TaskDispatchContext context,
        ProgramKitMiddlewareNext<TaskDispatchContext, TaskDispatchResult>
            continuation,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        tracker.UnselectedInvocations++;
        return continuation(context);
    }
}

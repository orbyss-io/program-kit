using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Middleware;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class SelectedTestDispatchMiddleware :
    ITaskDispatchMiddleware
{
    private readonly TestTaskMiddlewareTracker tracker;

    public SelectedTestDispatchMiddleware(
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
        tracker.SelectedInvocations++;
        return continuation(context);
    }
}

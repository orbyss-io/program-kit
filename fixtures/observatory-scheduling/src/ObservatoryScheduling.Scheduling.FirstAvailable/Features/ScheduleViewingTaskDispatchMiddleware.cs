using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Middleware;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Ensures the task pipeline receives the exact typed fixture request.</summary>
public sealed class ScheduleViewingTaskDispatchMiddleware : ITaskDispatchMiddleware
{
    /// <inheritdoc />
    public ValueTask<TaskDispatchResult> InvokeAsync(
        TaskDispatchContext context,
        ProgramKitMiddlewareNext<TaskDispatchContext, TaskDispatchResult> continuation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(continuation);
        cancellationToken.ThrowIfCancellationRequested();
        if (context.RequestType != typeof(ScheduleViewingTaskRequest) ||
            context.Request is not ScheduleViewingTaskRequest)
        {
            throw new InvalidOperationException(
                "The schedule-viewing task received an incompatible request contract.");
        }

        return continuation(context);
    }
}

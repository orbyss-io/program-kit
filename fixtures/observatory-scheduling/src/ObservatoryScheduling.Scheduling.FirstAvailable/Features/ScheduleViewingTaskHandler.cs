using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Injected handler used by immediate-background and scheduled task paths.</summary>
public sealed class ScheduleViewingTaskHandler :
    ITaskHandler<ScheduleViewingTaskRequest, ScheduleViewingTaskResponse>
{
    private readonly IFirstAvailableScheduler scheduler;

    /// <summary>Initializes the handler with consumer-owned scheduling behavior.</summary>
    public ScheduleViewingTaskHandler(IFirstAvailableScheduler scheduler)
    {
        this.scheduler = scheduler ??
            throw new ArgumentNullException(nameof(scheduler));
    }

    /// <inheritdoc />
    public async ValueTask<ScheduleViewingTaskResponse> HandleAsync(
        TaskHandlerContext context,
        ScheduleViewingTaskRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(request);
        var session = await scheduler.ScheduleAsync(
            request.Viewing,
            cancellationToken).ConfigureAwait(false);
        return new ScheduleViewingTaskResponse(session);
    }
}

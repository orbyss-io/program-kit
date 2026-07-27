namespace ObservatoryScheduling.Core.Contracts.Scheduling;

/// <summary>Schedules the first explicitly acceptable fictional viewing window.</summary>
public interface IFirstAvailableScheduler
{
    /// <summary>Schedules one request or returns no session when no window qualifies.</summary>
    ValueTask<ViewingSession?> ScheduleAsync(
        ViewingRequest request,
        CancellationToken cancellationToken);
}

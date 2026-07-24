using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Core.Tasks;

/// <summary>Typed response from fictional viewing work.</summary>
public sealed record ScheduleViewingTaskResponse(ViewingSession? Session);

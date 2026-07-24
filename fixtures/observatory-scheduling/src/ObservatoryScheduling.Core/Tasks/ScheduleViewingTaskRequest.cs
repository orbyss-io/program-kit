using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Core.Tasks;

/// <summary>Typed payload for background or scheduled fictional viewing work.</summary>
public sealed record ScheduleViewingTaskRequest(ViewingRequest Viewing);

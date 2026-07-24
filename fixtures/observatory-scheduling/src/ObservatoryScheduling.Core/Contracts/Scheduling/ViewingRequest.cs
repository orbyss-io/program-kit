namespace ObservatoryScheduling.Core.Contracts.Scheduling;

/// <summary>Fictional request to schedule one observatory viewing session.</summary>
public sealed record ViewingRequest(
    string Target,
    DateTimeOffset EarliestStart,
    DateTimeOffset LatestEnd,
    TimeSpan RequiredDuration);

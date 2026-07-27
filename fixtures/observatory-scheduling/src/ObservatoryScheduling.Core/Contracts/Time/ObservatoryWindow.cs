namespace ObservatoryScheduling.Core.Contracts.Time;

/// <summary>One bounded fictional observatory time window.</summary>
public sealed record ObservatoryWindow(
    DateTimeOffset StartsAt,
    DateTimeOffset EndsAt);

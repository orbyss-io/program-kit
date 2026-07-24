using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Core.Contracts.Scheduling;

/// <summary>Fictional accepted viewing session.</summary>
public sealed record ViewingSession(
    string Target,
    ObservatoryWindow Window);

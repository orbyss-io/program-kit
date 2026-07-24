namespace Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

/// <summary>Typed fixed-duration interval intent anchored to an exact instant.</summary>
public sealed record AnchoredFixedIntervalScheduleDescriptor(
    DateTimeOffset Anchor,
    TimeSpan Period);

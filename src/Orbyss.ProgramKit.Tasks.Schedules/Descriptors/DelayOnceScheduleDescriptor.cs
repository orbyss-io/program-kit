namespace Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

/// <summary>Typed intent for one occurrence after a non-negative delay.</summary>
public sealed record DelayOnceScheduleDescriptor(TimeSpan Delay);

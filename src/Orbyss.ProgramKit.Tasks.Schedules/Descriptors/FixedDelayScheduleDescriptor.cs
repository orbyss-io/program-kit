namespace Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

/// <summary>
/// Typed intent for one next occurrence after terminal completion, preventing
/// self-overlap.
/// </summary>
public sealed record FixedDelayScheduleDescriptor(TimeSpan Delay);

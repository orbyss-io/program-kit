using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Factories;

/// <summary>Default validated provider-neutral descriptor factory.</summary>
public sealed class TaskScheduleDescriptorFactory :
    ITaskScheduleDescriptorFactory
{
    /// <inheritdoc />
    public DelayOnceScheduleDescriptor CreateDelayOnce(TimeSpan delay)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(delay, TimeSpan.Zero);
        return new DelayOnceScheduleDescriptor(delay);
    }

    /// <inheritdoc />
    public FixedDelayScheduleDescriptor CreateFixedDelay(TimeSpan delay)
    {
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(delay, TimeSpan.Zero);
        return new FixedDelayScheduleDescriptor(delay);
    }

    /// <inheritdoc />
    public AnchoredFixedIntervalScheduleDescriptor CreateAnchoredFixedInterval(
        DateTimeOffset anchor,
        TimeSpan period)
    {
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(period, TimeSpan.Zero);
        return new AnchoredFixedIntervalScheduleDescriptor(anchor, period);
    }
}

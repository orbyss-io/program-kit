using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Factories;

/// <summary>Creates validated provider-neutral schedule descriptors.</summary>
public interface ITaskScheduleDescriptorFactory
{
    /// <summary>Creates one non-negative delayed occurrence descriptor.</summary>
    DelayOnceScheduleDescriptor CreateDelayOnce(TimeSpan delay);

    /// <summary>Creates a positive delay-after-terminal-completion descriptor.</summary>
    FixedDelayScheduleDescriptor CreateFixedDelay(TimeSpan delay);

    /// <summary>Creates a positive fixed-duration anchored interval descriptor.</summary>
    AnchoredFixedIntervalScheduleDescriptor CreateAnchoredFixedInterval(
        DateTimeOffset anchor,
        TimeSpan period);
}

using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Explicit registration of one exact typed task schedule.</summary>
public sealed class TaskScheduleRegistration<TDescriptor> :
    ITaskScheduleRegistration
    where TDescriptor : notnull
{
    /// <summary>Initializes the typed schedule registration.</summary>
    public TaskScheduleRegistration(
        TaskScheduleDefinition schedule,
        TDescriptor descriptor)
    {
        Schedule = schedule ??
            throw new ArgumentNullException(nameof(schedule));
        Descriptor = descriptor ??
            throw new ArgumentNullException(nameof(descriptor));
    }

    /// <inheritdoc />
    public TaskScheduleDefinition Schedule { get; }

    /// <inheritdoc />
    public Type DescriptorType => typeof(TDescriptor);

    /// <inheritdoc />
    public object Descriptor { get; }
}

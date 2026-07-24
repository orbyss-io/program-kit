using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Runtime-neutral bridge for one typed task schedule descriptor.</summary>
public interface ITaskScheduleRegistration
{
    /// <summary>Gets the exact schedule definition.</summary>
    TaskScheduleDefinition Schedule { get; }

    /// <summary>Gets the typed descriptor model type.</summary>
    Type DescriptorType { get; }

    /// <summary>Gets the typed descriptor instance as an opaque runtime value.</summary>
    object Descriptor { get; }
}

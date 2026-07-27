using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Runtime-neutral bridge for one typed occurrence request factory.</summary>
public interface ITaskOccurrenceRequestFactoryRegistration
{
    /// <summary>Gets the exact schedule revision.</summary>
    ArtifactReference ScheduleRevision { get; }

    /// <summary>Gets the consumer request model.</summary>
    Type RequestType { get; }

    /// <summary>Gets the factory implementation type.</summary>
    Type FactoryType { get; }

    /// <summary>Creates and dispatches one normal request.</summary>
    ValueTask<TaskDispatchResult> DispatchAsync(
        IServiceProvider services,
        ITaskDispatcher dispatcher,
        TaskOccurrence occurrence,
        CancellationToken cancellationToken);
}

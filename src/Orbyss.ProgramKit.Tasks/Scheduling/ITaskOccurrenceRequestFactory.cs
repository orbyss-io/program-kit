using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Scheduling;

/// <summary>Projects one occurrence into a normal typed task request.</summary>
public interface ITaskOccurrenceRequestFactory<TRequest>
    where TRequest : notnull
{
    /// <summary>Creates the normal request proposed by one occurrence.</summary>
    ValueTask<TaskRequest<TRequest>> CreateAsync(
        TaskOccurrence occurrence,
        CancellationToken cancellationToken);
}

using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Evaluates explicitly selected task schedules.</summary>
public interface ITaskScheduler
{
    /// <summary>
    /// Evaluates a schedule through the supplied instant and submits accepted
    /// occurrences through normal task acceptance.
    /// </summary>
    ValueTask<TaskScheduleEvaluationResult> EvaluateAsync(
        TaskScheduleEvaluationRequest request,
        CancellationToken cancellationToken);
}

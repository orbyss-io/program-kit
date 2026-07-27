using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Scheduling;
using ObservatoryScheduling.Core.Configuration;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Projects each schedule occurrence into a normal typed task request.</summary>
public sealed class ScheduledViewingRequestFactory :
    ITaskOccurrenceRequestFactory<ScheduleViewingTaskRequest>
{
    /// <inheritdoc />
    public ValueTask<TaskRequest<ScheduleViewingTaskRequest>> CreateAsync(
        TaskOccurrence occurrence,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(occurrence);
        cancellationToken.ThrowIfCancellationRequested();
        var viewing = new ViewingRequest(
            "fixture-target",
            occurrence.ScheduledFor,
            occurrence.ScheduledFor.AddHours(8),
            TimeSpan.FromHours(1));
        var request = new TaskRequest<ScheduleViewingTaskRequest>(
            ObservatoryRevisions.Reference(
                string.Concat(
                    "pkid:task-request:fixture:scheduled-viewing-",
                    occurrence.Sequence)),
            FirstAvailableTaskContracts.Definition.Revision,
            FirstAvailableTaskContracts.Definition.RequestContract,
            FirstAvailableTaskContracts.Definition.ResponseContract,
            FirstAvailableTaskContracts.Definition.FailureContract,
            new ProgramKitIdentifier(
                "pkid:principal:fixture:observatory-scheduler"),
            occurrence.EvaluatedAt,
            new ScheduleViewingTaskRequest(viewing),
            string.Concat(
                "nightly-viewing/",
                occurrence.Sequence),
            [],
            occurrence.Revision);
        return ValueTask.FromResult(request);
    }
}

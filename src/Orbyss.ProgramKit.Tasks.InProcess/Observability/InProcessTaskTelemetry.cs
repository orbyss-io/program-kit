using System.Diagnostics;
using System.Diagnostics.Metrics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Instances;

namespace Orbyss.ProgramKit.Tasks.InProcess.Observability;

internal sealed class InProcessTaskTelemetry :
    IInProcessTaskTelemetry,
    IDisposable
{
    private readonly ActivitySource activitySource =
        new("Orbyss.ProgramKit.Tasks.InProcess");
    private readonly Meter meter =
        new("Orbyss.ProgramKit.Tasks.InProcess");
    private readonly Counter<long> accepted;
    private readonly Counter<long> rejected;
    private readonly Counter<long> terminal;

    public InProcessTaskTelemetry()
    {
        accepted = meter.CreateCounter<long>("programkit.task.accepted");
        rejected = meter.CreateCounter<long>("programkit.task.rejected");
        terminal = meter.CreateCounter<long>("programkit.task.terminal");
    }

    public IDisposable? StartAttempt(
        TaskInstance instance,
        ArtifactReference attemptRevision)
    {
        var activity = activitySource.StartActivity(
            "task.attempt",
            ActivityKind.Internal);
        activity?.SetTag(
            "programkit.task.definition",
            instance.DefinitionRevision.Identity.Value);
        activity?.SetTag(
            "programkit.task.instance",
            instance.Revision.Identity.Value);
        activity?.SetTag(
            "programkit.task.attempt",
            attemptRevision.Identity.Value);
        return activity;
    }

    public void RecordAccepted() => accepted.Add(1);

    public void RecordRejected(string reason) =>
        rejected.Add(1, new KeyValuePair<string, object?>("reason", reason));

    public void RecordTerminal(TaskInstanceState state) =>
        terminal.Add(
            1,
            new KeyValuePair<string, object?>(
                "state",
                state.ToString()));

    public void Dispose()
    {
        activitySource.Dispose();
        meter.Dispose();
    }
}

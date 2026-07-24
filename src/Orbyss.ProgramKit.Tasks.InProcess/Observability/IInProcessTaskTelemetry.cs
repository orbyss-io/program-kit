using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Instances;

namespace Orbyss.ProgramKit.Tasks.InProcess.Observability;

internal interface IInProcessTaskTelemetry
{
    IDisposable? StartAttempt(
        TaskInstance instance,
        ArtifactReference attemptRevision);

    void RecordAccepted();

    void RecordRejected(string reason);

    void RecordTerminal(TaskInstanceState state);
}

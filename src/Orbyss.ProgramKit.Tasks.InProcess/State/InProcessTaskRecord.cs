using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Instances;

namespace Orbyss.ProgramKit.Tasks.InProcess.State;

internal sealed class InProcessTaskRecord
{
    internal InProcessTaskRecord(TaskInstance instance)
    {
        Instance = instance;
        State = TaskInstanceState.Waiting;
    }

    internal Lock Gate { get; } = new();

    internal TaskInstance Instance { get; }

    internal TaskInstanceState State { get; set; }

    internal int AttemptCount { get; set; }

    internal bool CancellationRequested { get; set; }

    internal ArtifactReference? LatestAttemptRevision { get; set; }

    internal ArtifactReference? TerminalOutcomeRevision { get; set; }

    internal DateTimeOffset? TerminalAt { get; set; }

    internal CancellationTokenSource ExecutionCancellation { get; } = new();
}

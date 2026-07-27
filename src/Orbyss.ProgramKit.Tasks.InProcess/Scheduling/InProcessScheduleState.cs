using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.InProcess.Scheduling;

internal sealed class InProcessScheduleState : IDisposable
{
    internal InProcessScheduleState(DateTimeOffset initialCursor)
    {
        ReferenceInstant = initialCursor;
        CursorExclusive = initialCursor;
    }

    internal SemaphoreSlim Gate { get; } = new(1, 1);

    internal DateTimeOffset ReferenceInstant { get; }

    internal DateTimeOffset CursorExclusive { get; set; }

    internal ArtifactReference? LatestInstanceRevision { get; set; }

    internal TaskOccurrence? PendingOccurrence { get; set; }

    public void Dispose() => Gate.Dispose();
}

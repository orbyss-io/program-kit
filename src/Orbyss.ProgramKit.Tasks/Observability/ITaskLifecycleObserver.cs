namespace Orbyss.ProgramKit.Tasks.Observability;

/// <summary>Observes authoritative task state transitions.</summary>
public interface ITaskLifecycleObserver
{
    /// <summary>Observes a completed transition without owning it.</summary>
    ValueTask ObserveAsync(
        TaskLifecycleContribution contribution,
        CancellationToken cancellationToken);
}

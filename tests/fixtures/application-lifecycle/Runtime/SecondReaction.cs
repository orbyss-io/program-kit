using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
public sealed class SecondReaction(ReactionObservation observed) : IDomainEventHandler<NoteSaved>
{
    public ValueTask HandleAsync(
        NoteSaved fact,
        DomainEventContext context,
        CancellationToken cancellation
    )
    {
        cancellation.ThrowIfCancellationRequested();
        observed.Events.Add("observer:" + fact.Id);
        return ValueTask.CompletedTask;
    }
}

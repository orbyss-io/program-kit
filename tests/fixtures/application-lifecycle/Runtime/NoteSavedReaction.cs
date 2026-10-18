using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
public sealed class NoteSavedReaction(ReactionObservation observed) : IDomainEventHandler<NoteSaved>
{
    public async ValueTask HandleAsync(
        NoteSaved fact,
        DomainEventContext context,
        CancellationToken cancellation
    )
    {
        await Task.Yield();
        cancellation.ThrowIfCancellationRequested();
        observed.Events.Add("reaction:" + fact.Id);
    }
}

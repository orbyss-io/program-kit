using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
public sealed class WaitingReaction(ReactionObservation observed) : IDomainEventHandler<WaitingFact>
{
    public async ValueTask HandleAsync(
        WaitingFact fact,
        DomainEventContext context,
        CancellationToken cancellation
    )
    {
        observed.HandlerEntered.TrySetResult();
        await Task.Delay(Timeout.Infinite, cancellation);
    }
}

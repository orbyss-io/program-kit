using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
public sealed class FaultingReaction : IDomainEventHandler<ReactionFault>
{
    public ValueTask HandleAsync(
        ReactionFault fact,
        DomainEventContext context,
        CancellationToken cancellation
    ) => throw new InvalidOperationException("fictional reaction failure");
}

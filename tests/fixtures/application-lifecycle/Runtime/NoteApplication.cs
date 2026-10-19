using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
/// <summary>Runtime publication point; the aggregate/value never receives a dispatcher.</summary>
public sealed class NoteApplication(IDomainEventPublisher publisher)
{
    public string? SavedId { get; private set; }
    public async Task SaveAsync(string identity, CancellationToken cancellation)
    {
        cancellation.ThrowIfCancellationRequested();
        if (string.IsNullOrWhiteSpace(identity)) throw new ArgumentException("A note identity is required.");
        SavedId = identity;
        var fact = new NoteSaved(identity);
        await publisher.PublishAsync(fact, cancellation);
    }
}

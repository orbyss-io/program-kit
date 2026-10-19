using Orbyss.Foundation.DomainEvents;
namespace ProgramKit.Examples.Events;
/// <summary>Immutable Core-owned fact, independent of runtime dispatch or persistence.</summary>
public sealed record NoSubscribers(string Value) : IDomainEvent;

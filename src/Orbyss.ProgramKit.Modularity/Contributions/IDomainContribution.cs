namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>
/// Marks an event-like fact published by domain code.
/// </summary>
/// <remarks>
/// This marker claims no persistence, queue, retry, replay, outbox,
/// transaction, or cross-process delivery semantics.
/// </remarks>
public interface IDomainContribution;

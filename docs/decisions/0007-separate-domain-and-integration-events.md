# ADR-0007: Separate in-process domain events from durable integration events

- Status: Accepted
- Date: 2026-09-03
- Decision owners: User and Codex

## Context

Modules need typed publish/subscribe for internal business facts, but an in-memory dispatcher cannot
promise delivery after commit or process termination. Treating both concerns as one event bus hides
transaction, durability, compatibility, retry, and failure semantics.

## Decision

Publish `ProgramKit.DomainEvents.Abstractions` for domain-owned event and handler contracts and
`ProgramKit.DomainEvents` for the default awaited, scoped, sequential, non-durable dispatcher.
Handlers are independent; required ordering, returned results, retries, or compensation use an
explicit capability or orchestrator. Technical dispatch metadata remains separate from immutable
past-tense business events.

Reliable post-commit, background, broker, and cross-process events are Integration Events. They will
use distinct versioned contracts and a durable outbox-capable design. Domain events are mapped to
integration contracts rather than published externally unchanged.

## Consequences

Domain Core packages may depend on the lightweight abstractions without referencing CShells or a
broker. The default dispatcher propagates failure and cancellation and bounds nested publication.
Any feature requiring durable delivery is blocked on the Integration Events architecture backlog;
fire-and-forget domain-event handlers are not an interim substitute.

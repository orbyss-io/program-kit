# Software language

Use this technology-neutral model for meaningful application and domain behavior:

`Identity + Intent + Context -> Policies -> Decision -> Transition -> Effects -> Admission -> Outcome`

## Identity

Anything that must be correlated, authorized, audited, retried, deduplicated, addressed, or evolved has an explicit stable identity. Do not add identity to values that are genuinely interchangeable.

## Policies and decisions

A policy is a named, side-effect-free evaluation over explicit inputs. Its result is a typed decision such as `Allow`, `Deny`, `Require`, `Defer`, or `NotApplicable`, with reasons and evidence where needed. Empty or truthy/falsey ambiguity is forbidden at domain boundaries.

Authorization is a policy evaluated before protected effects. Authentication establishes identity; it does not itself grant authority.

## Transition path

Commands, queries, triggers, and messages enter a guarded path. Every path ends with an explicit outcome: success, rejection, failure, cancellation, or durable asynchronous acceptance with an operation identity. Unexpected exceptions are defects or infrastructure failures, not a control-flow language.

## Lifecycle

A lifecycle is the durable map of states, invariants, legal transitions, terminal states, and externally visible consequences across one or many requests. APIs move identified subjects through that map; endpoints are not the lifecycle itself.

## Effects and admission

Effects are described before adapters perform them. An admission is an outward handover contract:

- Required admission: the transition is not successful until the destination acknowledges or durably commits the handover.
- Optional observation: observers may opt in; the transition does not depend on them.

Every admission declares requirement level, consistency, acknowledgement, idempotency, retry, ordering, timeout, and failure ownership. Event sourcing, transition journals, and transactional outboxes solve different problems and require separate decisions.

Cross-domain process managers consume published contracts or events. They do not coordinate by reaching into multiple domain stores. A multi-domain database transaction requires an explicit ADR.


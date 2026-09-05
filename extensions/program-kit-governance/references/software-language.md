# Software language

Use this technology-neutral model for meaningful application and domain behavior:

`Identity + Intent + Context -> Policies -> Decision -> Transition -> Effects -> Admission -> Outcome`

## Identity

Anything that must be correlated, authorized, audited, retried, deduplicated, addressed, or evolved has an explicit stable identity. Do not add identity to values that are genuinely interchangeable.

## Policies and decisions

A policy is a named, side-effect-free evaluation over explicit inputs. Its result is a typed decision such as `Allow`, `Deny`, `Require`, `Defer`, or `NotApplicable`, with reasons and evidence where needed. Empty or truthy/falsey ambiguity is forbidden at domain boundaries.

Authorization is a policy evaluated before protected effects. Authentication establishes identity; it does not itself grant authority.

Authorization has proportional boundaries. Provider roles, scopes, and token shapes are normalized
once at the authentication boundary; transport endpoints name stable application permission
requirements; application/domain policies decide genuine resource, state, and effect rules. A
bodyless or no-effect access probe ends at the transport permission decision and does not justify a
second application service or claim parser. A protected business effect still requires both the
transport permission gate and its real application/domain authorization rule.

## Transition path

Commands, queries, triggers, and messages enter a guarded path. Every path ends with an explicit outcome: success, rejection, failure, cancellation, or durable asynchronous acceptance with an operation identity. Unexpected exceptions are defects or infrastructure failures, not a control-flow language.

This guarded path is the semantic spine of a vertical slice. The slice owns the boundary adaptation,
policies, decision, transition, effects, admissions, outcome, and verification needed for that intent.
Framework handlers and endpoints expose the path; they do not replace its domain language.

## Lifecycle

A lifecycle is the model of a subject's existence and evolution: its inception or admission,
possible states, governing invariants, legal transitions, observable effects and outcomes, and
termination or retirement. A lifecycle definition describes every permitted trajectory; a
lifecycle history records the trajectory actually taken by one identified subject. A lifecycle
may be ephemeral within one execution or durable across many executions.

An execution path is one traversal through a lifecycle or control-flow model, not the lifecycle
itself. A lifetime is the interval between creation or acquisition and destruction or release.
Persistence preserves identity, state, or history across execution boundaries; it does not create
the lifecycle. APIs move identified subjects through lifecycle transitions, and endpoints merely
expose those paths.

## Effects and admission

Effects are described before adapters perform them. An admission is an outward handover contract:

- Required admission: the transition is not successful until the destination acknowledges or durably commits the handover.
- Optional observation: observers may opt in; the transition does not depend on them.

Every admission declares requirement level, consistency, acknowledgement, idempotency, retry, ordering, timeout, and failure ownership. Event sourcing, transition journals, and transactional outboxes solve different problems and require separate decisions.

Cross-domain process managers consume published contracts or events. They do not coordinate by reaching into multiple domain stores. A multi-domain database transaction requires an explicit ADR.

Interfaces and schemas live at owned boundaries. Consumer-owned ports express required capabilities;
provider-owned published contracts express offered capabilities. Domain entities are not transport,
persistence, configuration, or event schemas.

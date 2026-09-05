# Vertical slicing

## Default delivery unit

A meaningful delivery slice follows one actor, trigger, or intent through policies, decisions,
state transitions, effects, and verification to an observable outcome. Organize specifications,
plans, tasks, code, and tests around that outcome rather than around technical layers.

Vertical slicing is the default Program Kit delivery method. It does not prescribe a folder layout,
CQRS, a mediator, one project per endpoint, or a particular framework. Physical organization and
technology choices remain project-specific architecture decisions.

## Slice contract

For every non-trivial slice, identify:

- stable slice identity, actor or trigger, intent, and observable outcome;
- owning bounded context and module;
- input, output, public contracts, and compatibility obligations;
- policies, authorization, validation, invariants, and legal transitions;
- data ownership, consistency boundary, effects, admissions, and failure ownership;
- timeouts, cancellation, retries, idempotency, concurrency, and terminal outcomes where relevant;
- logging, metrics, tracing, audit, deployment, migration, and recovery concerns where relevant;
- verification at the cheapest reliable levels, including contract and architecture checks.

A slice is complete only when its supported success and material failure paths are usable and
verifiable. A route, UI component, database migration, or handler alone is not a complete slice.
An explicitly bodyless/no-effect authorization probe is a proportional transport proving slice: its
observable `401`/`403`/success outcomes come from managed endpoint permission metadata, so it must not
invent an inner application service. A real protected operation remains a full slice and carries its
resource/state/effect authorization beyond the endpoint gate.

## Cohesion and coupling

Maximize cohesion inside a slice and minimize coupling between slices. A slice may cross internal
presentation, application, domain, persistence, and integration concerns, but it must not bypass
bounded-context, module, security, or data-ownership boundaries.

Prefer adding slice-local behavior over modifying broad shared mechanisms. Promote code to a shared
contract or capability only after its semantics, owner, consumers, compatibility policy, and reason
for sharing are explicit. Direct access to another slice's implementation or store is forbidden.

## Horizontal enabling work

Platform, migration, security, observability, and other horizontal work is allowed when it:

1. names the slices or quality scenarios it enables;
2. has an explicit owner and bounded completion condition;
3. does not defer all observable value to an indefinite later phase; and
4. is followed by a thin end-to-end proving slice before broad expansion.

Plans must not use controllers, services, repositories, database, frontend, or infrastructure as
the primary delivery phases for feature behavior.

## Proportional exceptions

Pure libraries, generated code, trivial adapters, presentation-only changes, migrations, and
infrastructure-only changes may use a documented proportional exception. The exception must name
the missing slice elements and explain why they are not meaningful. It cannot bypass security,
public-contract, data-integrity, lifecycle, tenancy, or recovery obligations.

## Traceability

Trace each slice through design evidence, architecture decisions, specification, plan, tasks,
implementation, and verification. When a slice exposes a new architecture choice, stop at the
decision boundary, propose the ADR, obtain human acceptance, and update the architecture before
implementation depends on it.

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

Tie each enabling dependency to the first operation that proves it. A policy create/list operation
may need authorization, owned durable storage and its migration; it must not wait for later upload,
OCR or processing-worker infrastructure. Upload admission still needs its real storage/security
gates, and evidence processing still needs its provider, lease and recovery prerequisites. Shared
work can enable several operations without making all future infrastructure a blanket barrier.

Distinguish task-level enabling dependencies from retained roadmap-feature authority gates. An
approved bootstrap prerequisite due before implementation still blocks that feature's preflight,
even when an operation is otherwise independent. Expose that retained scope during planning/tasks;
never change its trigger, affected slices or evidence requirement through operation declarations.
If its approved scope prevents the desired operation order, resolve that architecture/authority
choice through normal reviewed design before claiming the operation is ready. A delivery-due proof
remains mandatory at delivery without becoming an invented global implementation dependency.

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

For an existing approved plan with coarse layer tasks, preserve its task IDs, checked states,
requirements and accepted architecture. Add operation substeps mapped to those parent IDs, then
identify the smallest usable operation and the actual dependencies needed to prove it. Leave each
parent task open until all its obligations are complete. Review any proposed prerequisite changes
against security, data integrity, provider and authority constraints before updating the approved
graph; neither an upgrade nor a resume may silently rewrite it. Preserve unfinished work and real
failures, and do not turn simulated or scoped verification into feature acceptance.

At a consumer checkpoint, first save the working tree and the original implementation baseline,
current behavior, next operation and unresolved failure artifact references. Upgrade the maintained
commands/templates and verification wrapper through the normal reviewed consumer upgrade path,
preserving consumer-owned customizations and its accepted runner/toolchain. Map a custom VSTest or
offline/provider runner to the supported adapter contract before relying on scoped result reuse.
Replan only the affected coarse tasks using the substeps above, inspect needed/reusable/unresolved
verification, and run the checks invalidated by the repair before continuing that operation.

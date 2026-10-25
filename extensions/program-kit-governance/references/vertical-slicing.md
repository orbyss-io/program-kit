# Vertical slicing

## Default delivery unit

<!-- program-kit:knowledge-rule principle.vertical-outcome-unit -->
A meaningful delivery slice follows one actor, trigger, or intent through policies, decisions,
state transitions, effects, and verification to an observable outcome. Organize specifications,
plans, tasks, code, and tests around that outcome rather than around technical layers.

Vertical slicing is the default Program Kit delivery method. It does not prescribe a folder layout,
CQRS, a mediator, one project per endpoint, or a particular framework. Physical organization and
technology choices remain project-specific architecture decisions.
<!-- /program-kit:knowledge-rule -->

## Slice contract

<!-- program-kit:knowledge-rule principle.vertical-slice-contract -->
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
<!-- /program-kit:knowledge-rule -->

## Cohesion and coupling

<!-- program-kit:knowledge-rule principle.vertical-cohesion-boundaries -->
Maximize cohesion inside a slice and minimize coupling between slices. A slice may cross internal
presentation, application, domain, persistence, and integration concerns, but it must not bypass
bounded-context, module, security, or data-ownership boundaries.

Prefer adding slice-local behavior over modifying broad shared mechanisms. Promote code to a shared
contract or capability only after its semantics, owner, consumers, compatibility policy, and reason
for sharing are explicit. Direct access to another slice's implementation or store is forbidden.
<!-- /program-kit:knowledge-rule -->

## Horizontal enabling work

<!-- program-kit:knowledge-rule principle.first-operation-enabling-work -->
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

Keep actual product, security, authority and engineering prerequisites visible beside their
dependent tasks. If an agreed constraint prevents the desired order, resolve the substantive
choice through normal design review. Old workflow ledgers or missing toolkit status do not create
new phase gates. A runtime check needed only at delivery does not become a global coding prerequisite.
<!-- /program-kit:knowledge-rule -->

## Proportional exceptions

<!-- program-kit:knowledge-rule principle.vertical-proportional-exceptions -->
Pure libraries, generated code, trivial adapters, presentation-only changes, migrations, and
infrastructure-only changes may use a documented proportional exception. The exception must name
the missing slice elements and explain why they are not meaningful. It cannot bypass security,
public-contract, data-integrity, lifecycle, tenancy, or recovery obligations.
<!-- /program-kit:knowledge-rule -->

## Traceability

<!-- program-kit:knowledge-rule principle.slice-authority-traceability -->
Trace each slice through design evidence, architecture decisions, specification, plan, tasks,
implementation, and verification. When a slice exposes a new architecture choice, stop at the
decision boundary, propose the ADR, obtain human acceptance, and update the architecture before
implementation depends on it.

Adoption of story-delivery-v1 requires abandoning the affected unfinished feature, retaining its
history/failed evidence, amending and normally ratifying the constitution and rerunning all Spec Kit
phases from fresh specification. Do not map partial code/checkmarks into new progress. Review the
concrete owned reset inventory; shared source, outputs, migrations and data need clear ownership.
Preserve unchanged confirmed bootstrap/intake intent, accepted architecture, foundations/tooling,
consumer locks and delivered features. Toolkit installation/recovery remains the supported updater.
<!-- /program-kit:knowledge-rule -->

## Story and operation boundaries

<!-- program-kit:knowledge-rule principle.story-operation-review-boundary -->
The story is the human acceptance unit; operations are internal implementation/integration checks.
One coherent actor intent, useful outcome, explicit non-goals and an independent walkthrough through
the supported interface/effects define the story. Include success/material failures and necessary
authorization, ownership, persistence and recovery. Estimate preparation, integration and verification
to human-reviewable behavior. Reconsider oversized stories before tasks; split by useful journeys,
never layer/endpoint counts. Larger coherent stories disclose rationale/effort. Two hours is advisory.
Internal operation completion needs no repeated human review. Earlier checkpoints require explicit
agreement. Present exercised runnable story behavior and relevant passing checks, prepared account/
data, walkthrough and limitations. Pause further product work until acceptance or explicit scoped
deferral; deferred reviews remain due at feature acceptance. See `phase-evidence.md` for state,
review assignments, decision freshness, resume, no-hook closure and advisory active effort.
<!-- /program-kit:knowledge-rule -->

---
artifact-kind: program-kit-design-category
category: consumer-planning-and-delivery
status: active
last-updated: 2026-07-31
active-batch: PLN-B01
parent-ledger: DESIGN.md
product-surface: consumer-facing
development-method: spec-kit
---

# Program Kit Design — Consumer Planning and Delivery

## 1. Category objective

Define the planning contracts, CLI workflows, and capability seams Program Kit
offers to consumers for turning approved intent and design into bounded,
traceable, executable work.

This is a Program Kit product surface, not the development method used to build
Program Kit. This repository continues to use Spec Kit directly. Program Kit
planning artifacts cannot govern, authorize, or become source truth for Program
Kit's own redesign or implementation. Product tests may use isolated consumer
fixtures to prove the planning surface without introducing self-hosting.

The category must preserve these accepted constraints:

- consumers receive an integrated Program Kit planning experience and do not
  need a separate Spec Kit CLI (`DEC-001`);
- Program Kit itself is developed with Spec Kit and does not consume its own
  planning facilities as development authority (`DEC-002`, `DEC-027`);
- Program Kit owns stable public commands, artifacts, diagnostics, and
  compatibility promises independently of any internally reused technique
  (`DEC-010`);
- planning artifacts link into the portable software-definition bundle but do
  not replace its root manifest or duplicate linked semantic truth (`DEC-015`);
- exact references, canonical representation, explicit unknowns, and bounded
  evaluation preserve the accepted semantic decisions (`DEC-024`–`DEC-026`);
  and
- capabilities may help propose, validate, project, or execute consumer plans
  only through explicit public contracts and human-authorized invocation.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `PLN-B00` | Product/development-method boundary | `completed` | Preserve consumer-facing planning without Program Kit self-hosting. |
| `PLN-B01` | `PLN-001`–`PLN-002` | `active` | Define the minimal canonical planning vocabulary and determine the disposition of archived planning concepts. |
| `PLN-B02` | `PLN-003`–`PLN-004` | `queued` | Define stable artifact links, drift, orchestration, execution, and capability boundaries. |

## 3. Non-authoritative archive review

Archived commit `0cc3950bb75f5704f7b0c58784ba691f942c8a81` was
reviewed as prior art only. Useful ideas include:

- outcome-oriented work units;
- exact links to approved designs, requirements, inputs, outputs, and evidence;
- explicit dependency paths rather than ordering inferred from filenames;
- stop conditions, verification expectations, compatibility and migration
  references, requirement trace, and unresolved decisions; and
- separation between a plan and observations produced while executing it.

The archive also exposed design pressure that should not be imported blindly:

- gate-establishment, product, and closure roles encoded one implementation's
  workflow as general planning truth;
- mutable plan state and execution authority encouraged self-hosting;
- sequence numbers and parallel-group identifiers duplicated dependency meaning;
- direct executable commands and raw allowed-edit strings mixed portable intent
  with workspace-specific execution;
- planned outputs sometimes looked like already-observed artifacts with digests;
  and
- several schema generations and migrations reflected historical churn rather
  than a stable minimum product vocabulary.

## 4. Active batch: Minimal planning vocabulary

`PLN-B01` resolves:

- `PLN-001`: the canonical planning concepts and their lifecycle relations; and
- `PLN-002`: which archived concepts to retain, re-specify, or discard.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### PLN-001A — Five planning artifacts, with other truth referenced

**Recommendation:** Program Kit's minimum planning vocabulary contains five
distinct artifact kinds:

1. **Program goal** — a human-owned desired outcome, rationale, success measures,
   and governing constraints. It says why an outcome matters, not how to code it.
2. **Roadmap** — a human-owned, revisable view of intended delivery progression
   across program goals and prospective implementation scopes. It expresses
   priority and dependency where known; it is not a sprint, calendar, issue
   tracker, or execution queue.
3. **Implementation plan** — the approved strategy for realizing one exact set
   of design, semantic, contract, and component revisions.
4. **Work unit** — the smallest independently reviewable and verifiable outcome
   node in an implementation plan.
5. **Execution receipt** — an immutable observation of one explicitly authorized
   attempt to execute or evaluate a work unit, including actual artifacts,
   evidence, diagnostics, and disposition.

Requirements, decisions, designs, contracts, components, approvals, policies,
capabilities, artifacts, evidence, and evaluation reports retain their own
artifact identities. Planning references them exactly instead of copying their
content into a second source of truth.

### PLN-001B — Immutable definitions; progress comes from receipts and evidence

**Recommendation:** Goals, roadmaps, plans, and work units are immutable at an
exact revision. Human approval binds an exact revision and digest. Execution
does not mutate a plan or work unit from `pending` to `complete`.

Current progress and readiness are derived from the approved plan, dependency
closure, applicable approvals, execution receipts, artifact state, and fresh
evidence. A material planning change creates a new revision or explicit
amendment relationship and triggers impact evaluation; the prior revision
remains inspectable.

The work-unit dependency graph is authoritative. Readiness and possible
parallelism are derived from it. Sequence numbers, array position, filenames,
and parallel-group labels have no ordering authority. This avoids introducing a
general planning lifecycle engine while still producing deterministic CLI
classifications.

### PLN-001C — A work unit specifies an outcome contract, not a shell script

**Recommendation:** A canonical work unit minimally records:

- its identity and required observable outcome;
- exact trace links to the governing goal, plan, requirements, design, contracts,
  and profiles;
- explicit dependencies on other work units;
- existing input references and planned output identities or contracts;
- a governed implementation-scope reference;
- required verification, evaluation, and evidence profiles;
- stop or escalation conditions; and
- any required capability contract and support profile.

An output digest belongs in the execution receipt after an artifact exists, not
in the planned output declaration. Portable work-unit semantics contain no raw
shell commands, provider-specific agent instructions, implicit tool selection,
or claim that listing a path grants mutation authority. Workspace-specific
bindings may be resolved later through exact approved capabilities and profiles;
that boundary is finalized in `PLN-B02`.

### PLN-002 — Retain the intent, re-specify the mechanics, discard the old workflow

**Recommendation:** Treat the archived planning model as follows.

**Retain conceptually:**

- goals and required outcomes;
- exact design and requirement trace;
- work-unit dependency graphs;
- explicit inputs and planned outputs;
- compatibility, migration, verification, evidence, and stop requirements;
- unresolved decisions as explicit blockers; and
- separate approval and execution evidence.

**Re-specify:**

- `allowedEdits` as governed implementation-scope bindings;
- direct verification commands as evaluation or capability contract references;
- mutable plan state as derived status from immutable receipts and evidence;
- output artifact references as planned declarations followed by observed
  receipt bindings; and
- workflow-specific work-unit kinds as optional vocabulary/profile extensions.

**Discard from the universal planning core:**

- sequence and parallel-group authority duplicated by the dependency graph;
- built-in gate-establishment/product/closure workflow;
- a planning-owned executor or autonomous agent loop;
- self-hosted Program Kit planning authority;
- compatibility baggage for the archived schema generations; and
- project-management features such as sprints, staffing, estimation, calendars,
  issue synchronization, and portfolio reporting.

### PLN-B01 delivery boundary

This batch defines a small portable planning contract, not a project-management
suite or general workflow engine. It does not yet decide command names,
workspace mutation authority, execution scheduling, receipt trust, drift
propagation, or capability invocation. Those belong to `PLN-B02`.

For the first CLI, the model should be provable with one goal, one approved plan,
a small work-unit dependency graph, and deterministic readiness diagnostics.
Roadmap automation and multi-plan portfolio behavior need not be implemented
until a concrete consumer workflow requires them.

## 5. Revision record

- Created after Semantic Language and Bounded Contexts closed under `DEC-026`.
- Recorded explicitly that Program Kit planning is a consumer-facing CLI and
  capability surface that Program Kit itself does not use.
- Imported archived planning only as prior art; no archived type, state machine,
  executor, schema, or workflow is source truth.

---
artifact-kind: program-kit-design-category
category: consumer-planning-and-delivery
status: closed
last-updated: 2026-07-31
active-batch: none
parent-ledger: DESIGN.md
product-surface: external-orchestration-boundary
development-method: spec-kit
---

# Program Kit Design — Consumer Planning and Delivery

## 1. Category objective

Record the accepted boundary between guided planning and Program Kit's
software-factory responsibilities. Program Kit v1 owns no native planning
system. Spec Kit owns the recommended human-led discovery, specification,
planning, and task workflow; a later external adapter invokes Program Kit's
public factory contracts.

Program Kit core and CLI remain independently callable and have no runtime
dependency on Spec Kit. This repository continues to use Spec Kit directly.
Neither Spec Kit artifacts nor Program Kit factory artifacts grant authority
without the explicit approvals required by their own contracts.

The category must preserve these accepted constraints:

- Program Kit itself is developed with Spec Kit (`DEC-002`);
- Program Kit owns stable public factory commands, artifacts, diagnostics, and
  compatibility promises (`DEC-010`);
- the guided workflow requires a separate Spec Kit installation, while direct
  Program Kit use remains available to humans and other orchestrators
  (`DEC-029`);
- the later Spec Kit adapter uses only public Program Kit contracts and cannot
  create internal coupling or bypass the kernel (`DEC-029`);
- factory protocol artifacts link into the portable software-definition bundle
  without replacing or duplicating its semantic truth (`DEC-015`);
- exact references, canonical representation, explicit unknowns, and bounded
  evaluation preserve the accepted semantic decisions (`DEC-024`–`DEC-026`);
  and
- operation request, resolution lock, execution receipt, and evaluation report
  are factory contracts, not a hidden planning system.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `PLN-B00` | Product/development-method boundary | `completed` | Preserve consumer-facing planning without Program Kit self-hosting. |
| `PLN-B01` | `PLN-001`–`PLN-002` | `withdrawn` | Native planning-vocabulary proposal preserved as unaccepted discovery. |
| `PLN-B02` | `PLN-003`–`PLN-004` | `superseded` | Native planning execution boundary replaced by the external-orchestration decision. |
| `PLN-B03` | `PLN-001`–`PLN-004` | `completed` | Spec Kit owns guided planning; Program Kit exposes only factory-operation contracts. |

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

## 4. Withdrawn draft: Native planning vocabulary

`PLN-B01` resolves:

- `PLN-001`: the canonical planning concepts and their lifecycle relations; and
- `PLN-002`: which archived concepts to retain, re-specify, or discard.

**Status:** Withdrawn before decision. The following recommendations were never
accepted. They remain recorded to preserve the reasoning that exposed the
duplication with Spec Kit and may be reconsidered only if evidence later proves
that an adapter cannot satisfy consumer needs.

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

## 5. Accepted pivot: Spec Kit plans; Program Kit builds

The software-factory identity reopened all four planning questions. The
human accepted the complete pivot. It is governed by `DEC-029`.

### PLN-P01 — Guided planning belongs to Spec Kit

**Recommendation:** Program Kit v1 does not own program goals, roadmaps,
specifications, implementation plans, work-unit graphs, task readiness, or a
planning lifecycle. The recommended human-led AI workflow uses Spec Kit for
discovery, specification, planning, and tasks.

Users who want that guided workflow install Spec Kit as well as Program Kit.
Program Kit does not copy or wrap Spec Kit's planning artifacts into a second
canonical planning model.

### PLN-P02 — Program Kit remains independently callable as a factory

**Recommendation:** Program Kit core and CLI have no runtime dependency on Spec
Kit. They accept exact, public factory-operation requests that identify approved
semantic inputs, the desired operation, target and evaluation profiles, and
explicit authority. Humans, automation, Spec Kit, or another orchestrator may
submit the same request.

Program Kit owns only factory protocol artifacts:

- an operation request describing the authorized factory action;
- the exact resolution lock produced before construction;
- an execution receipt recording what the factory attempted and produced; and
- an evaluation report recording conformance, incompatibility, unknowns, and
  remediation.

These are not a roadmap or planning system. They are the input, reproducibility,
observation, and quality-control contracts of the software factory.

### PLN-P03 — A thin external adapter performs the guided handoff

**Recommendation:** After the public Program Kit CLI contracts are implemented
and stable, a separately versioned Spec Kit adapter maps an approved Spec Kit
plan or task into a Program Kit operation request, invokes only public CLI or
API contracts, and returns structured artifacts, evidence, status, and
diagnostics to the Spec Kit workflow.

The adapter owns the translation and declares the exact Spec Kit and Program Kit
versions it supports. It cannot grant authority, bypass kernel gates, reinterpret
unknown intent, or make Program Kit depend internally on Spec Kit. Other
orchestrators can implement the same public handoff contract.

### PLN-P04 — Accepted decision consequences

- `DEC-001` is superseded because the guided planning experience requires a
  separate Spec Kit installation;
- `DEC-027` is superseded because Program Kit no longer exposes a native
  planning product surface, while its non-self-hosting constraint remains;
- `DEC-002` and `DEC-010` remain accepted;
- `DEC-011` is revised from an optional post-publication idea to the selected
  guided-workflow architecture, while adapter implementation still waits for a
  stable, independently usable Program Kit CLI;
- `PLN-B01` remains recorded as withdrawn discovery and `PLN-B02` is
  superseded; and
- factory request, lock, receipt, and report details move into the categories
  that own construction, determinism, diagnostics, and governance.

### PLN-B03 delivery boundary

No Spec Kit adapter is designed or implemented during current core-CLI
construction. The CLI first proves stable public factory contracts through
direct calls and fixtures. Adapter work begins only after those contracts are
tangible enough to integrate without coupling either product's internals.

## 6. Revision record

- Created after Semantic Language and Bounded Contexts closed under `DEC-026`.
- Recorded explicitly that Program Kit planning is a consumer-facing CLI and
  capability surface that Program Kit itself does not use.
- Imported archived planning only as prior art; no archived type, state machine,
  executor, schema, or workflow is source truth.
- Withdrew the unaccepted native planning proposal after the software-factory
  identity exposed duplication with Spec Kit.
- Activated `PLN-B03` with a candidate boundary in which Spec Kit owns guided
  planning, Program Kit remains an independently callable factory, and a later
  external adapter connects their public contracts.
- Accepted `PLN-B03` under `DEC-029`, superseded the native-planning decisions,
  retained only factory protocol artifacts, and closed Consumer Planning and
  Delivery.

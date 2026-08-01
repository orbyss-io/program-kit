---
description: "Outcome- and proof-oriented task list for Program Kit features"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: spec.md, plan.md, and every plan artifact referenced by the
Requirement and Proof Matrix

**Proof rule**: Tests and other proof are mandatory for every public contract,
negative path, applicable constitutional MUST, and evidence-backed claim.

**Organization**: Group work by independently testable user story. Keep proof
next to the outcome it proves. Reserve the complete slow assurance gate for CI.

## Task Format

`- [ ] T### [P?] [US?] Outcome | Refs: ... | Proof: ... | Tier: ... | Done: ...`

- **[P]** means no incomplete dependency and no overlapping file ownership.
- **[US]** maps the task to an independently testable user story.
- **Refs** names every FR, SC, plan decision, or constitutional MUST served.
- **Proof** names the executable check, evidence, or human review.
- **Tier** is `edit`, `story`, `pre-pr`, `ci`, or `human`.
- **Done** states the observable completion condition.
- Paths may identify likely edit locations, but an outcome is not superseded
  merely because the implementation was consolidated into another file.

Every applicable requirement and planned proof must map to at least one task.
Do not mark work complete through a synthetic factory call, placeholder fixture,
README-only directory, or test that does not invoke the production boundary.

## Phase 1: Setup

**Purpose**: The smallest shared setup required by the accepted plan.

- [ ] T001 [outcome] | Refs: [plan/requirement] | Proof: [check] | Tier: edit | Done: [observable condition]

---

## Phase 2: Foundational Boundaries

**Purpose**: Blocking contracts, ownership, and test seams required by stories.

- [ ] T002 [outcome] | Refs: [references] | Proof: [focused proof] | Tier: story | Done: [condition]

**Checkpoint**: Every story can now be implemented without unresolved authority,
contract, ownership, dependency, or proof questions.

---

## Phase 3: User Story 1 - [Title] (Priority: P1)

**Goal**: [Value delivered]

**Independent Test**: [Smallest public-boundary demonstration]

### Proof for User Story 1

- [ ] T003 [P] [US1] [production-boundary unit/contract/acceptance proof] | Refs: FR-001, SC-001 | Proof: [command/test] | Tier: story | Done: [expected positive and negative result]

### Implementation for User Story 1

- [ ] T004 [US1] [observable implementation outcome] | Refs: FR-001 | Proof: T003 | Tier: edit | Done: [condition]

**Checkpoint**: Story 1 is independently functional and its mapped proof passes.

---

[Add further user-story phases with the same outcome/proof structure.]

---

## Phase N: Cross-Cutting Completion

- [ ] TXXX [P] Reconcile Requirement and Proof Matrix coverage | Refs: all applicable rows | Proof: `$speckit-analyze` reports no CRITICAL/HIGH coverage gap | Tier: pre-pr | Done: every row has implementation and proof ownership
- [ ] TXXX Run repository pre-PR verification | Refs: plan verification strategy | Proof: `./eng/Invoke-Verification.ps1 -Mode PrePr` | Tier: pre-pr | Done: command passes without changing generated evidence
- [ ] TXXX Obtain authoritative protected CI evidence | Refs: cross-platform and final assurance obligations | Proof: required Windows/Linux checks | Tier: ci | Done: exact merge candidate is green
- [ ] TXXX Record named human validation where required | Refs: human-review obligations | Proof: explicit bounded decision | Tier: human | Done: accepted claim and invalidation scope are recorded

## Dependencies and Execution Order

- Setup precedes foundational boundaries.
- Foundational boundaries precede dependent stories.
- Within a story, create the nearest useful failing proof before implementation
  when practical; otherwise record why a different order is safer.
- Run edit/story checks while building. Run PrePr once when the candidate is
  locally complete. CI owns the full acceptance/conformance/platform matrix.
- Do not rerun an equivalent full gate when its declared inputs are unchanged.
- `converge` is recovery for a discovered gap, not a routine completion phase.

## Resolution Semantics

- `[X]` means the stated outcome and proof are both satisfied.
- A superseded task remains unchecked and names the replacing task/outcome.
- Deferred work remains unchecked and requires explicit human approval.
- If implementation reveals material ambiguity, changed authority, broadened
  effects, or a missing dependency, return to spec/plan/tasks before continuing.

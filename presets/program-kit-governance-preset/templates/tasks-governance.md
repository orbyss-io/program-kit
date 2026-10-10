# Tasks: [FEATURE NAME]

**Inputs**: spec.md, plan.md and constitution; optional design sections only as needed.
**Format**: `- [ ] T001 [P] [US1] Description with concrete file path`.
`[P]` means independent writes and satisfied prerequisites. IDs and checked boxes survive resume.

## Outcome order and coverage

[List prioritized stories, independent operations and requirement/acceptance-scenario mappings.
Each operation provides a demonstrable user outcome; split a broad story into several operations.
No technical-layer phase or blanket foundation barrier. Put only minimal enabling prerequisites
beside the first operation that proves them; each prerequisite names its actual consumers.]

## [US1] [operation-id]: [independent user outcome]

**Independent test**: [observable behavior including ownership/security and failure scenarios].
**Prerequisites**: [exact task IDs and why each is required; none when independent].
**Verification**: [test level, projects/filter/command and required shared-boundary tests].

- [ ] T001 [US1] [One owned prerequisite needed by this operation, concrete path]
- [ ] T002 [US1] [Test the operation's intended missing behavior, concrete test path]
- [ ] T003 [US1] [Implement that behavior end-to-end, concrete paths]
- [ ] T004 [US1] [Refactor and verify the operation's affected boundaries, concrete paths]

[Repeat an operation group for each independently testable outcome; test and implementation pairs
stay together. Security, storage/provider and admission prerequisites precede their consumers.
Do not complete future OCR/worker infrastructure before an independent create/list operation.]

## Closure

[Story regression tasks at story closure, then full application acceptance and required delivery
guidance/settings at feature closure. Shared contracts/generators retain their necessary checks.]

## Operation dependency map

| Operation | Depends on operations |
|-----------|-----------------------|
| [operation-id] | none |

Declare only necessary cross-operation dependencies. Use `none` for independent outcomes.
Minimal enabling tasks share their first proving operation; a reusable prerequisite can have its
own operation only when actual consumers explicitly depend on it. Closure depends on delivered
operations. These declarations are reviewed against spec/plan, never inferred from layer names.

## Task dependency map

| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | [operation-id] | none | none | [prerequisite-kind] |
| T002 | [operation-id] | T001 | [prerequisite-kind] | none |
| T003 | [operation-id] | T002 | [prerequisite-kind] | none |
| T004 | [operation-id] | T003 | none | none |

Use exact IDs and comma-separated items or `none`. Every task has one row. `Requires` names
the obligations that must already be established by an ancestor task's `Provides`, such as
`authorization`, `ownership`, `storage`, `real-provider`, `ocr-admission`. These are planned
dependencies, not evidence that a task has passed. Do not claim a prerequisite for unrelated
operations; a missing required gate or unexplained cross-operation dependency blocks finalization.
Semantic review verifies that the declarations include every actual gate from governing inputs.
Retained roadmap-feature prerequisites due before implementation still gate feature preflight.
Operation dependency rows cannot defer or waive approved ledger gates, authority, approvals or pins;
distinguish them from ordinary scoped enabling-task prerequisites.

## Parallel examples

[Name only independent tasks with disjoint writes and satisfied dependencies. Complete one current
outcome before spreading work across future operations; parallel flags grant no extra authority.]

## Incremental task generation

Follow the before_tasks phase-context draft/resume procedure. Persist tasks.md immediately
after required inputs and save each completed phase before preparing the next. On interruption,
resume completed phases from the existing draft and inspect only changed inputs or missing
phases; preserve task IDs, checked boxes and consumer edits. This overrides whole-document
assembly before the first write. Complete dependencies, parallel examples and coverage/format
review before finalizing, then run mandatory after_tasks hooks and read-only speckit.analyze once.
An incomplete draft is not ready for analysis or implementation.

Generate prerequisite tasks for unresolved compatibility/admission inputs and decisions with
an owner and dependency before affected implementation/proof tasks. Drafting does not execute
those prerequisites, start services or bootstrap, change approvals/pins or fabricate evidence.
The constitution requires applicable tests even when upstream task instructions call tests
optional. Retain security, ownership and real-provider verification before completion.
Carry reviewed feature-plan resolutions and their precise plan sections into the affected tasks.
Report unresolved/stale decisions and conflicting adopted constraints with their owners; resolve
design prerequisites before dependent implementation. Recheck only changed decision inputs.
A drafted task or plan never closes a compatibility/delivery execution obligation.

## Engineering verification

Deliver thin end-to-end outcomes with their actual tests. Carry applicable architecture and
coding choices from the plan into implementation tasks. Run compiler/analyzer checks and
relevant tests while coding. Use Focused for the operation and Affected for changed responsibilities
and reverse dependencies; name projects/filters and retain the implementation Git baseline in normal
progress output. Include committed, staged, unstaged, untracked, deleted and generated inputs in the
complete delta. Unknown ownership needs an explicit correction, not a silent full-suite fallback.
Progress saves, task batches, story checkpoints and resumes do not run full acceptance. Story closure
uses story regression coverage. Run complete application acceptance once at feature/domain closure
or formal review handoff, then reuse its current result in the final report. Recheck relevant changes.
Restore only when dependency inputs or preparation require it; pack/stage when affected tests consume
those artifacts or at delivery. Keep new and previously failing cases in scope. Successful results
can be reused only while source/configuration/generated/toolchain and relevant environment inputs
remain unchanged; failures/interruption never establish acceptance. A scoped pass is not full acceptance.
Map test tasks to each user story's requirements and acceptance scenarios; place them before their
corresponding implementation tasks. Observe the intended failing behavior before writing the fix,
then retain those tests as regression coverage. Preserve scoped constitutional exceptions.
Preserve contract generation, security boundaries and release composition checks when applicable.
Associate each test task with its operation/story, required scenarios, cheapest reliable level and
actual command. Distinguish compiler/analyzer, behavior, architecture, provider, contract and review
owners; do not schedule every category after each small task. Preserve required shared-boundary tests.

Update the user-owned roadmap when the outcome changes. Do not create extra review receipts,
proof attestations, metadata-repair notes or nonapplicability dossiers. Test output belongs in
ignored artifacts/ or retained CI artifacts; substantive decisions stay in the plan or ADRs.
During implementation use `task_draft.py checkpoint` to replace one compact current checkpoint
in tasks.md. Retain the original baseline, current outcome/task IDs, relevant check references,
decision references, unresolved failures and next action. Do not append a progress journal.
Use `task_draft.py current` on resume; it supplies current state without rereading the whole plan.

---
description: Generate dependency-ordered, operation-sized feature tasks with resumable drafting.
scripts:
  sh: scripts/bash/setup-tasks.sh --json
  ps: scripts/powershell/setup-tasks.ps1 -Json
  py: scripts/python/setup_tasks.py --json
---

## User Input

```text
$ARGUMENTS
```

Apply user scope and constraints. Drafting tasks never executes implementation or prerequisite proofs.

## Hook dispatch

Read `.specify/extensions.yml` if it exists. At each named boundary select enabled hooks in
configured YAML order; missing `enabled` means enabled. Invalid YAML or an unavailable mandatory
hook prevents claiming that boundary complete. Do not sort by priority or evaluate `condition`:
report nonempty conditions as not executed by this adapter. For `optional: false`, emit
`EXECUTE_COMMAND: <command>`, then **MUST actually invoke the hook** using the session's skill/command
mechanism and wait for its result. Stop affected work on failure. Optional hooks execute only when
selected. Dispatch `hooks.before_tasks` before drafting and `hooks.after_tasks` only after final review.
Dispatch each once per invocation; do not repeat a hook's work independently.

## Preparation and resume

Run `{SCRIPT}` once, or reuse the before_tasks hook's setup_tasks result from this invocation.
Retain FEATURE_DIR, AVAILABLE_DOCS and TASKS_TEMPLATE_CONTENT; use that resolved template, falling
back to TASKS_TEMPLATE only for older scripts. Inspect existing tasks.md before reading optional
documents. Read spec.md, plan.md and constitution once when not current in context. Follow the
before_tasks task_draft.py prepare/save-phase/finalize protocol: save the initial draft immediately,
then each completed operation group. Resume saved groups without renumbering IDs, losing checked
boxes or consumer edits, or repeating unchanged preparation. Only read a contract/data-model/research
section needed for the current operation or unresolved choice. Changed inputs require scoped review.
An incomplete draft is not ready for implementation or read-only analysis.

## Generate the operation plan

1. Extract prioritized user stories, their requirements and acceptance scenarios. Confirm each
   coherent actor journey, observable outcome, non-goals, independent walkthrough, connected
   integration and success/material failure paths. Estimate preparation/integration/verification
   to human review; split oversized stories by useful journeys before tasks, or disclose larger-story
   effort and rationale. Operations are internal units; human acceptance is per runnable story.
   One task must have one reviewable
   behavior or prerequisite; do not bundle all models, services or endpoints in separate layer tasks.
2. Establish each operation's exact prerequisite graph. Minimal setup/enabling work belongs to the
   first operation that proves it. Shared prerequisites block only their named consumers. Do not make
   all stories depend on every foundation task or future owner's infrastructure. Preserve required
   authorization, security, ownership, storage/migration, real-provider, contracts and admission gates
   for the operations that need them; no operation bypasses its real prerequisite to appear smaller.
   Retained roadmap-feature prerequisites due before implementation still gate that feature's
   preflight. Operation dependencies cannot defer or waive approved ledger gates, approvals or pins.
   Distinguish those retained authority gates from ordinary scoped enabling-task dependencies.
   For an existing foundation composition, consume the read-only `eng/foundation_setup.py
   --repository . --status` projection supplied by phase context and its latest named result.
   Reuse maintained infrastructure and already established unchanged proof; put changed-input,
   failed or live service checks beside the operation needing them. Do not start setup during drafting.
3. For each operation, state its independent test, required scenarios, cheapest reliable test level
   and actual verification command. Record risk and verification sequence briefly. Generate known
   scaffolds coherently first, run maintained checks before dependent behavior, then add missing
   consumer-specific tests. Prefer test-first for critical/uncertain behavior and regression-first
   for bugs; wiring uses immediate checks and refactoring existing regressions. Observe intended
   missing behavior when test-first is selected; labels alone do not prove low risk. Tests required by the
   constitution are mandatory. Story closure has story regressions; feature closure has complete
   acceptance. Do not schedule every verification category after every task.
4. Use checklist lines `- [ ] T001 [P] [US1] Description with concrete file path`, omitting `[P]`
   unless tasks have independent writes and prerequisites. Continue unique IDs. Group by operation
   within story priority, with coherent verification/implementation batches, followed by closure work.
5. Populate the template's operation and task dependency tables. Name required prerequisite kinds
   and the tasks establishing them. Prerequisites are obligations until executed; draft rows never
   establish approval, provider proof or authority. Map all tasks to a proving operation or closure.
   Include valid parallel examples and trace every requirement/scenario to its tasks. Populate
   `Story delivery map` with operation ownership, useful outcome, walkthrough, effort and rationale.
   Required reviews pause per completed story; earlier checkpoints require explicit human agreement.
   Carry reviewer/owner assignments and scoped deferrals through the existing compact checkpoint.
6. Final review checks unique IDs, task paths, operation-sized outcomes, full requirement coverage,
   acyclic dependencies, required gates and risk-selected verification ordering. For a new marked draft,
   task_draft.py finalize checks the declared dependency tables. Semantic review must still confirm
   their declarations against plan/spec/constitution. Preserve scoped constitutional exceptions.

## Existing approved plans

Never automatically rewrite an approved graph. Preserve IDs, checkboxes, failures and obligations.
Within an existing fresh story-delivery feature, identify precise prerequisites and review changed
dependencies against its approved plan before adopting them. Follow
`.specify/extensions/program-kit-governance/references/vertical-slicing.md` for story boundaries.
An installed toolkit update alone grants no new consumer design or implementation authority.
Adoption of story-delivery-v1 abandons the affected unfinished feature: archive it, amend/ratify the
constitution, review its owned reset inventory and rerun all Spec Kit phases from fresh specification.
Old partial code/tasks/checkmarks cannot become progress under this policy.

## Completion

Save all groups and dependency/coverage review, finalize marked drafts, then dispatch
`hooks.after_tasks`. Read-only speckit.analyze runs once on complete tasks through its configured
hook; if absent, invoke it once explicitly. Never run it after each group write. Preserve its
STRICTLY READ-ONLY boundary and unresolved findings. Report operation order, actual prerequisites,
coverage and concrete unresolved decisions. Task generation claims no implementation acceptance.

---
description: Deliver runnable stories with risk-selected verification and required human review.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

## User Input

```text
$ARGUMENTS
```

Apply user scope and constraints. A progress request, task batch or resume does not close the feature.

## Hook dispatch

For each boundary below, read `.specify/extensions.yml` if it exists. Select the named event's
enabled hooks in configured YAML order. Missing `enabled` means enabled. Never sort by priority
or evaluate `condition`: report a nonempty condition as not executed, because this adapter cannot
evaluate it. Invalid YAML or an unavailable mandatory hook prevents claiming the boundary complete.

For `optional: false`, emit `EXECUTE_COMMAND: <command>`, then **MUST actually invoke the hook**
using this session's command/skill mechanism and wait for its result. A printed marker is not execution.
Stop affected work on hook failure. For optional hooks, show their prompt and execute only if selected.
No hooks or no file requires no extra ceremony. Dispatch each boundary once per invocation;
do not invoke its commands again independently.

## Preparation and resume

1. Run `{SCRIPT}` once and retain FEATURE_DIR and AVAILABLE_DOCS for this invocation. Inspect
   existing tasks.md before preparing work. If its incremental draft is incomplete, resume tasks
   generation; do not implement or analyze the incomplete draft.
2. Read the constitution, spec.md, plan.md and tasks.md once when not already current in context.
   Reuse unchanged context on resume. Consult a contract, data model, research section or quickstart
   only for the operation or unresolved choice that needs it; do not reread every optional document.
3. If checklists exist, inspect their state read-only. Reviewer-owned requirements checklists are
   not implementation completion lists. Preserve upstream's gate: report unchecked criteria and
   obtain the user's decision to proceed before dependent work. Do not tick them on the reviewer's behalf.
4. Initialize fresh delivery state once using `task_draft.py delivery` and the installed
   `phase-evidence.md` protocol. Preserve existing delivery state/roles/reviews on resume. An old
   partial feature needs archived abandonment, constitution amendment/ratification and every Spec
   Kit phase from a fresh specification; never reuse its partial code or checkmarks as new progress.
   Dispatch `hooks.before_implement` once. The combined preflight supplies focused guidance and
   validates the planned graph without restore/build. Reuse its result; do not run phase-context again.
   If that hook is absent, run `implementation_preflight.py --feature-dir <feature>` once explicitly.
   Pending required review pauses entry; only repair/diagnosis of the presented outcome or the
   explicitly deferred operations may proceed. Pass `--operation <id> --repair` only for that repair.
5. Verify necessary setup and ignore patterns for the affected technologies; retain existing
   correct files and accepted pins. Record the initial Git commit as the implementation baseline
   in normal task/progress output. On resume retain the earlier baseline so committed work is included.

## Focused implementation

Execute the dependency order in tasks.md, preserving completed tasks, IDs and consumer edits.
Work in complete vertical outcomes. Do not reinterpret story phases as technical-layer phases.
Choose one current operation and its observable success/material failure outcomes. Identify its
exact enabling dependencies and completion checks before editing. Finish that outcome before
expanding another operation or future infrastructure. Group related invariants into one coherent
behavior batch; verification does not require a separate shell invocation or progress narration for every
small assertion. A newly exposed shared-contract failure can justify expanding the batch.

- Select verification sequence from actual responsibilities/uncertainty. Materialize known scaffold
  batches first, run maintained generation/configuration/build/integration checks before dependent
  behavior, then add missing consumer-specific tests. Prefer meaningful test-first for critical
  authorization, ownership, transactions, concurrency, replay, destructive actions and recovery;
  prefer a demonstrating regression for reproducible bugs. Wiring/presentation can be implemented
  and verified immediately; refactoring uses existing regressions plus missing coverage. Record
  risk/method and an alternative reason briefly in plan/tasks, without routine approval or new ADR.
  When test-first is chosen, missing tools, syntax errors or unrelated setup failures are not valid red.
- Use `eng/Invoke-RepositoryVerification.ps1 -Scope Focused -Projects <test-project>` and the
  framework's supported filter, or the documented equivalent. Build affected targets with their
  analyzers; do not repeatedly restore unchanged dependencies or package the application.
  Use the maintained wrapper's supported runner adapter for accepted VSTest or offline/provider
  consumers; retain managed selection, freshness, failure tracking and logs rather than replacing
  orchestration. An unfiltered multi-project Focused run needs an explicit scope reason in its plan.
- Expand tests through reverse dependencies when public Core/API contracts, persistence,
  registration/lifetimes, security, generators or shared build inputs change. Use `-Scope Affected`
  with `-ChangedFrom <implementation-baseline>` to include committed, staged, unstaged and untracked work.
  Inspect `-Plan` first when selecting a new blast radius. Unknown mappings require an owned
  correction or a deliberate broader verification boundary; there is no silent full-suite fallback.
- A progress save, handful of tasks, story checkpoint, interruption or resume runs only checks
  made necessary by changed inputs. Story closure uses story regression coverage. Whole-feature/domain
  closure and an explicit formal review handoff earn complete application acceptance.
- Reuse successful checks only while their source, generated/configuration/toolchain inputs and
  relevant environment remain unchanged. Keep new and previously failing tests in scope. Never
  reuse a failure/interruption or present reused output as newly executed tests.
  Inspect the wrapper's needed/reusable/unresolved plan with its prior run references. Preserve the
  original implementation baseline for coverage; do not advance it to hide earlier work. Unknown
  dynamic inputs need a supported adapter or a deliberate broader boundary. Complete acceptance
  and Release always execute their full current gate.
- Apply rules to changed responsibilities: dependency direction, typed boundaries, actual production
  callers, cancellation, lifetimes, faults, constants and selected Foundation mechanisms. A pure
  helper needs neither an unused interface nor another SOLID report. Keep decisions in plan/ADRs,
  tests and normal review; add no proof/approval dossier.
- Mark a task `[X]` only after its behavior and relevant checks are satisfied. Preserve failures
  and dependencies, save progress, and state remaining work when stopping early.
  Preserve the current fresh-feature graph and leave each task open until all its obligations pass.
  Do not silently regenerate or weaken an approved graph; repair guidance is in the installed
  `vertical-slicing.md` reference.

## Human story checkpoint

Before each operation use the maintained `task_draft.py delivery` start transition. Internal operations
within a story need no human pause. At the completed story or explicitly agreed early checkpoint,
exercise its integrated journey, pass relevant checks and present the actual runnable entry point,
prepared account/data, short walkthrough, expected results and material limitations. Disclose simulated
externals; a mockup cannot establish implemented acceptance. Use the present transition to bind its
implementation/configuration basis and keep separate engineering/human dispositions.
Pause before another product operation/story. Repair/diagnosis of that outcome remains allowed.
Explicit acceptance permits progression; deferral lists only authorized operations or a bounded batch
and leaves review due before feature acceptance. Silence, time, screenshots and tests grant no authority.
Corrections to agreed requirements stay in the story; new scope needs the owner's decision and affected
artifact updates. Required technical failures cannot be waived. Backlog optional improvements explicitly.
Use actual reviewer assignments and decision sources. Optional GitHub roles need verified account identity
and human confirmation; retrieve only explicitly supplied references and verify exact author/checkpoint/
basis. Generic PR approval cannot accept every story. On outage/ambiguity leave the new decision pending,
preserve prior decisions and use only explicit owner reassignment to the conversation reviewer.
No automatic posting, polling or monitoring is authorized. Reopen affected acceptance on material outcome/
workflow/authorization/persistence changes; unrelated commits/tests preserve accepted behavior.

Use delivery status on progress/resume and wait before explicit human waiting. Defaults warn at 60 active
minutes per operation/120 per story, including preparation/builds/integration/tests/repairs and excluding
human waiting. Preserve accumulated elapsed effort; never sum parallel command durations or reset by
renaming/saving/reassigning. Report crossing once with what works/remains, cause and smallest corrective
action; update materially changed diagnosis/scope. Continue bounded authorized work when appropriate:
time alone never blocks. Only explicit owner decisions revise budgets.

## Current checkpoint

Keep one compact replacement-style checkpoint inside tasks.md. Prepare a small JSON input in
existing ignored artifacts with `baseline`, `outcome`, `next`, and applicable `taskIds`, `checks`,
`decisions`, `failures`; invoke `.specify/extensions/program-kit-governance/scripts/task_draft.py
checkpoint --feature-dir <feature> --content-file <ignored-json>`. Use `current --feature-dir <feature>`
for read-only resume context. Add `resolvedFailures` only for failures resolved with actual evidence.
It records the original baseline, current outcome, delivered substeps, next
action, unresolved failures with existing artifact references, and retained decisions. Replace the
current checkpoint on save/resume; do not append an execution journal or create a governance
dossier. Keep task IDs, checkboxes, approved dependencies and decisions outside the checkpoint
unchanged. Detailed commands, streams and failure history belong in existing ignored artifacts.
Read this checkpoint and the affected task group on resume; reread broader inputs only if changed
or needed for an unresolved choice. Never drop an unresolved failure merely to keep notes small;
resolve it with actual evidence, or keep its concise reference in the checkpoint.

## Delivery boundary

Progress saves and resumes are not full acceptance boundaries.
Always dispatch `hooks.after_implement` once before the final progress/completion report. The
architecture-check hook uses `finish --feature-dir <feature>`: open tasks or an unfinished draft
return in-progress without running full acceptance. An explicitly requested formal review handoff
uses `finish --handoff`, even when intentionally unfinished work remains.

The after-implement hook owns complete application acceptance at feature/domain closure or formal
handoff. Do not run acceptance independently before dispatching that hook. If no acceptance hook
is configured, invoke `phase_obligations.py finish --feature-dir <feature>` (or `finish --handoff`
for an explicit formal handoff) once at that boundary. This consumes the same required review state
before invoking the documented application acceptance command,
including applicable compiled architecture, contracts, real-provider/runtime, security and delivered
guides/settings checks. Reuse that invocation's current result rather than calling acceptance again
to produce the final message. New changes require the relevant checks again. Publication retains its
separate full Release gate and does not follow from implementation acceptance.

Report delivered behavior, actual or explicitly reused test scope/results, concrete review findings,
remaining tasks and limitations. A scoped pass or green compiler never establishes full acceptance.

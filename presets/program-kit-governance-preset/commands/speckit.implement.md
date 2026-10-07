---
description: Implement and resume a feature using focused TDD and explicit delivery acceptance.
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
4. Dispatch `hooks.before_implement` once. The combined preflight supplies focused guidance and
   validates the planned graph without restore/build. Reuse its result; do not run phase-context again.
5. Verify necessary setup and ignore patterns for the affected technologies; retain existing
   correct files and accepted pins. Record the initial Git commit as the implementation baseline
   in normal task/progress output. On resume retain the earlier baseline so committed work is included.

## Focused implementation

Execute the dependency order in tasks.md, preserving completed tasks, IDs and consumer edits.
Work in complete vertical outcomes. Do not reinterpret story phases as technical-layer phases.

- For each new or changed behavior, write its smallest meaningful test, observe the intended
  missing behavior, implement, then refactor with nearby regression tests passing. A missing tool,
  syntax error or unrelated setup failure does not prove the intended red behavior.
- Use `eng/Invoke-RepositoryVerification.ps1 -Scope Focused -Projects <test-project>` and the
  framework's supported filter, or the documented equivalent. Build affected targets with their
  analyzers; do not repeatedly restore unchanged dependencies or package the application.
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
- Apply rules to changed responsibilities: dependency direction, typed boundaries, actual production
  callers, cancellation, lifetimes, faults, constants and selected Foundation mechanisms. A pure
  helper needs neither an unused interface nor another SOLID report. Keep decisions in plan/ADRs,
  tests and normal review; add no proof/approval dossier.
- Mark a task `[X]` only after its behavior and relevant checks are satisfied. Preserve failures
  and dependencies, save progress, and state remaining work when stopping early.

## Delivery boundary

Progress saves and resumes are not full acceptance boundaries.
Always dispatch `hooks.after_implement` once before the final progress/completion report. The
architecture-check hook uses `finish --feature-dir <feature>`: open tasks or an unfinished draft
return in-progress without running full acceptance. An explicitly requested formal review handoff
uses `finish --handoff`, even when intentionally unfinished work remains.

The after-implement hook owns complete application acceptance at feature/domain closure or formal
handoff. Do not run acceptance independently before dispatching that hook. If no acceptance hook
is configured, invoke the documented application acceptance command once at that boundary,
including applicable compiled architecture, contracts, real-provider/runtime, security and delivered
guides/settings checks. Reuse that invocation's current result rather than calling acceptance again
to produce the final message. New changes require the relevant checks again. Publication retains its
separate full Release gate and does not follow from implementation acceptance.

Report delivered behavior, actual or explicitly reused test scope/results, concrete review findings,
remaining tasks and limitations. A scoped pass or green compiler never establishes full acceptance.

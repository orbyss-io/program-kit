---
description: Add coherent vertical outcomes and explicit review notes to native task generation.
---

## Program Kit task guidance

Keep the native task-generation flow, its setup/template resolution and configured hooks. Use the
existing spec, plan and constitution; inspect tasks.md before making changes. Preserve task IDs,
checked boxes, consumer edits and unfinished work on resume. Save useful groups as they are ready.

Group work around small runnable user outcomes. Put minimal enabling work beside its first consumer;
name real dependencies instead of imposing a blanket foundation phase. Security, authorization,
ownership, persistence/migration and provider prerequisites belong before the tasks that need them.
A larger coherent journey can remain intact when its scope and rationale are explicit.
These scoped dependencies take precedence over blanket layer-first/foundation examples in the core
command. The constitution's testing policy takes precedence over generic optional-test examples.

Carry the plan/research/ADR decisions into the tasks that use them: intended responsibility,
selected method or pattern, semantic commitments, local adaptation and focused checks. Link the
relevant decision section instead of copying it when sufficient. Preserve the source/version facts
and constraints behind consequential choices; do not turn every private file or class into a fixed
blueprint. No mandatory decision table, file map or coding-unit manifest is needed.

Choose tests and their sequence by risk and the constitution. Use test-first for consequential or
uncertain behavior and a demonstrating regression for bugs. Materialize known scaffolds together,
check them, then add the missing consumer behavior and tests. A missing tool or unrelated compilation
error is not a meaningful failing behavioral test. Put the first compiler/analyzer/focused check at
the first coherent increment, and retain affected regressions for shared changes.
For a new or uncertain approach, put source review and the focused checks on its first coherent
case before widespread replication. This is a technical review; add a human pause only where one
has actually been agreed. Qualified catalog patterns and generators are optional.

Record any agreed human review point in plain tasks.md notes: outcome, reviewer, when to pause and
any explicitly permitted work while waiting. Requester acceptance is separate from test results.
Earlier or additional pauses need agreement; do not turn every task into a new approval gate.
Make the independent walkthrough and expected result concrete. Preserve the user's decision in a
short note when received; no hidden JSON checkpoint, receipt or extra state initialization is needed.

Before reporting task generation complete, finish the native `hooks.after_tasks` dispatch from
`.specify/extensions.yml`. Invoke each enabled unconditional mandatory command in priority order
and wait for its result; a printed `EXECUTE_COMMAND:` line or a recommendation to run it later is
not execution. With the standard Program Kit hooks this means architecture review, then
`speckit.analyze` (`$speckit-analyze` in Codex skills mode). Returning from architecture-check
does not finish the outer tasks command. If a hook needs a human decision, pause and resume the
remaining hooks after that decision; do not silently drop analysis. Never start another coding agent.

Run native read-only analysis once on the completed task plan; do not duplicate it when the hook
already ran for these tasks. Respect explicitly disabled/removed hooks and native condition handling;
do not force-enable or bypass consumer configuration. If analysis was disabled, unavailable or
blocked, report that disposition and the next action instead of claiming it ran. In the final task
report, name the hooks actually invoked, their results and unresolved findings. Only then report
task generation complete. This is conversational dispatch, not a new execution ledger or runner.

Keep Analyze read-only: report its findings before any authorized correction in a separate explicit
step. Use the shared [engineering feedback method](.specify/extensions/program-kit-governance/references/engineering-feedback.md)
to correct the owning spec, research, plan/ADR or tasks, preserving unrelated decisions and completed
IDs/checkmarks. Resolve material questions before dependent implementation and rerun affected review
after corrections; missing bookkeeping is not itself a reason to block native delivery.

Report coverage, dependencies and unresolved choices. Drafting tasks never starts services, runs application acceptance or authorizes
implementation, provider operations or publication.

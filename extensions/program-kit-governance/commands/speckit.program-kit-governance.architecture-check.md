---
description: Review current work against relevant architecture and substantive decisions.
scripts:
  py: scripts/phase_obligations.py
---

Before a feature directory exists, review the request and relevant constitutional/architectural
context directly. Do not create a feature or require toolkit metadata merely to run a hook.
For after-plan or after-tasks, `{SCRIPT} check --feature-dir <feature> --phase after-plan`
(or `after-tasks`) supplies relevant references without changing files or running engineering.

Compare actual responsibilities, boundaries, contracts and important failure paths across spec,
plan, tasks and changed code. Preserve accepted decisions; reopen substantive contradictions with
source locations and a concrete correction. Missing toolkit history is not an application failure.
Use compiler/architecture/security/behavior checks appropriate to the selected technology and action.
Optional .NET graph and SDK helpers remain with their engineering owner; a graph pass alone cannot
establish that ownership labels match real behavior.

Keep unresolved findings and agreed human review pauses in normal task/review notes. Independent
ready work remains available. After implementation, report actual checks, semantic review, remaining
work and human dispositions separately. Run complete applicable acceptance at feature closure;
do not run a whole-app command for each progress update or infer acceptance from checked tasks.
Use normal native analysis and its read-only output; do not create approval/proof dossiers.

For .NET host/exporter choices, apply `principle.dotnet-host-default` in
references/tool-selection.md. Review a custom-host proposal against actual human opt-out,
keep unresolved choices visible, and resolve the effective profile before reading versioned
package knowledge. A proposal, helper pass or profile listing supplies no human acceptance.

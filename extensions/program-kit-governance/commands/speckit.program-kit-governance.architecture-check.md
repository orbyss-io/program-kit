---
description: Review actual work against applicable architectural decisions and checks.
scripts:
  py: scripts/phase_obligations.py
---
Choose the current event explicitly; do not emit planning context at every boundary.
After planning run `{SCRIPT} check --feature-dir <feature> --phase after-plan`; after tasks run
`{SCRIPT} check --feature-dir <feature> --phase after-tasks`. These commands validate the planned
roles, dependency edges and bindings in ordinary `eng/architecture.json` without building or
changing design files. Correct confirmed structural violations before affected implementation.
Before a feature directory exists, review the request and existing constitutional/architectural
context directly; do not require a feature-dependent command or create a feature on the hook's behalf.
Compare the specification, plan, tasks or changed code with the constitution, domain design,
architecture model and relevant Accepted ADRs when available. Missing governance history is not
an application failure. Preserve accepted choices; request a decision only for substantive changes.
Report concrete conflicts with source locations and corrective actions. Check dependency direction,
Core purity, cohesive domain capabilities, typed public boundaries, security, lifecycle ownership,
and the selected host/package/composition contract. Apply conditional guidance proportionally.
During specification review only the request, ownership and relevant accepted constraints.
After-plan and after-tasks use the commands above once; their summaries are the default context.
Do not first run project and then check for the same event, or reread entire reference inventories.
During specification and planning, present design findings without requiring application builds,
tests or completion evidence. At after-implement run `{SCRIPT} finish --feature-dir <feature>`.
Pending tasks or a draft return progress without full engineering acceptance. State remaining work;
do not claim completion. An explicit formal review handoff adds `--handoff`; neither a status request
nor a task batch is a handoff. Completed feature/domain work runs the full engineering command once.
Reuse its current result in the final report; do not separately invoke verify or that command again.
Compiler diagnostics, architecture tests, contract checks and
behavioral tests must pass. Assess semantic judgments for changed responsibilities in normal code review; a green compiler
alone does not prove them. Do not create separate proof attestations or hash-bound reviews.
Spec Kit analyze findings stay in its normal output. Do not save an extra approval dossier.

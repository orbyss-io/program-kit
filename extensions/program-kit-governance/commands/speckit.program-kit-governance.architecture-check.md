---
description: Review actual work against applicable architectural decisions and checks.
scripts:
  py: scripts/phase_obligations.py
---
Choose the current event explicitly; do not emit planning context at every boundary.
After planning run `{SCRIPT} check --feature-dir <feature> --phase after-plan`; after tasks run
`{SCRIPT} check --feature-dir <feature> --phase after-tasks`. These commands validate the planned
roles, dependency edges and bindings in ordinary `eng/architecture.json` without building or
changing design files. Describe actual responsibility names/kinds/effects and provided capabilities in
each declared project's `responsibilities`. Correct confirmed structural violations before affected implementation.
For example, a persistence-calling NotesService is runtime even when its project was called Core.
Reconcile its responsibility and capability inventory with the plan and relevant ADRs; do not merely
repeat role labels. A passing declared graph is structural evidence and never a semantic PASS.
Address material `lifecycleFindings` with their concrete owner/source evidence. Review whether a
composition project owns real reusable selection or merely registers foreign tasks/calls provider
preparation. Apply the selected publisher lifecycle mechanisms and retain legitimate presets and
independent business-event reactions. Record corrections in the current plan/tasks and ordinary review,
preserving approved history; the findings create no new proof or approval dossier.
Before a feature directory exists, review the request and existing constitutional/architectural
context directly; do not require a feature-dependent command or create a feature on the hook's behalf.
When a consumer upgrade record exists, run the lightweight compatibility scan with a
request/brief JSON carrying known architectureScope, contracts and affectedPaths:
`python .specify/extensions/program-kit-governance/scripts/consumer_upgrade.py scan --input <request.json> --phase specification`.
Use the existing intake brief when available; an ignored temporary request is a regenerable
view, not a feature or approval packet. Resolve due ownership/contract findings and carry
matching migrations into existing plan/tasks. Unknown scope is explicitly limited.
Refine the same scope during planning. A new discovery immediately enters the local
upgrade discovery/pickup route; keep unaffected work available and preserve prior findings.
Compare the specification, plan, tasks or changed code with the constitution, applicable canonical constraints, domain design,
architecture model and relevant Accepted ADRs when available. Missing governance history is not
an application failure. Preserve accepted choices; request a decision only for substantive changes.
Acceptance is not an implicit exception to applicable constraints. Surface conflicts and preserve
history until a scoped governed correction or valid exception resolves them. Report concrete conflicts
with source locations and corrective actions. Check dependency direction,
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
Report the engineering command's actual scope separately from semantic review, consumer outcomes and
human acceptance. Required unresolved findings prevent overall completion; command success cannot close them.
Compiler diagnostics, architecture tests, contract checks and
behavioral tests must pass. Assess semantic judgments for changed responsibilities in normal code review; a green compiler
alone does not prove them. Do not create separate proof attestations or hash-bound reviews.
Spec Kit analyze findings stay in its normal output. Do not save an extra approval dossier.

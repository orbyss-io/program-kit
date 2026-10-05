---
description: Review actual work against applicable architectural decisions and checks.
scripts:
  py: scripts/phase_obligations.py
---
For the current feature, obtain applicable guidance with `{SCRIPT} project --feature-dir <feature>`.
Compare the specification, plan, tasks or changed code with the constitution, domain design,
architecture model and relevant Accepted ADRs when available. Missing governance history is not
an application failure. Preserve accepted choices; request a decision only for substantive changes.
Report concrete conflicts with source locations and corrective actions. Check dependency direction,
Core purity, cohesive domain capabilities, typed public boundaries, security, lifecycle ownership,
and the selected host/package/composition contract. Apply conditional guidance proportionally.
Before completion run `{SCRIPT} verify --feature-dir <feature>` or the project's documented
engineering verification command. Compiler diagnostics, architecture tests, contract checks and
behavioral tests must pass. Assess semantic judgments in the normal code review; a green compiler
alone does not prove them. Do not create separate proof attestations or hash-bound reviews.
Spec Kit analyze findings stay in its normal output. Do not save an extra approval dossier.

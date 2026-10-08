---
description: Apply relevant architecture and programming knowledge while implementing.
scripts:
  py: scripts/implementation_preflight.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} --feature-dir <feature>` to validate
`eng/architecture.json` and obtain guidance. A structural failure blocks affected implementation;
this check does not restore or build projects and creates no governance receipt.
Reuse current spec.md, plan.md, tasks.md and applicable accepted decisions already loaded by implement.
Read only changed inputs or the relevant operation when resuming. This is the sole pre-implementation
guidance/structural check; do not independently invoke phase-context or repeat preflight afterward.
Apply the contextual programming rules before editing the affected code. Preserve DDD ownership,
allowed dependencies, pure policies, explicit effects, cancellation and resource ownership.
Resolve any reported feature-plan decision in its actual plan section after normal review before
dependent implementation. Preserve approved bootstrap history; a plan cannot close compatibility
or delivery execution. Missing responsibility metadata needs review of the selected projects.
The declared graph checks supplied labels; inspect actual Core/runtime/provider ownership and
canonical-permission versus resource/state/effect authorization in the changed code.
Use native dependency locks and supported composition defaults. Run compiler/analyzer checks and
targeted tests as code changes. Write and run the relevant failing case before its implementation,
then nearby regressions for refactoring. Expand through changed contracts and reverse dependencies.
Progress saves, task batches and resumes do not trigger full acceptance. Restore only for changed
dependency inputs or an explicit preparation need; package only when an affected integration needs it.
A plan disagreement is a finding to resolve, not a reason to
rewrite unrelated design documents. Ask humans only about material choices or scoped exceptions.
Do not require bootstrap completion, ratification receipts, roadmap status, analysis hashes,
artifact ownership dossiers or extra review approvals before ordinary coding.
Confirmed code/architecture violations must be corrected before completion and CI acceptance.
Report the command's stated engineering scope, actual behavior tested and outstanding semantic or
human review separately. A graph or command pass does not establish overall feature acceptance.

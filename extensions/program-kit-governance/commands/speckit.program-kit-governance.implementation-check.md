---
description: Apply relevant architecture and programming knowledge while implementing.
scripts:
  py: scripts/implementation_preflight.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} --feature-dir <feature>` to validate
`eng/architecture.json` and obtain guidance. A structural failure blocks affected implementation;
this check does not restore or build projects and creates no governance receipt.
Read spec.md, plan.md and tasks.md and the relevant accepted architectural decisions.
Apply the contextual programming rules before editing the affected code. Preserve DDD ownership,
allowed dependencies, pure policies, explicit effects, cancellation and resource ownership.
Use native dependency locks and supported composition defaults. Run compiler/analyzer checks and
targeted tests as code changes. A plan disagreement is a finding to resolve, not a reason to
rewrite unrelated design documents. Ask humans only about material choices or scoped exceptions.
Do not require bootstrap completion, ratification receipts, roadmap status, analysis hashes,
artifact ownership dossiers or extra review approvals before ordinary coding.
Confirmed code/architecture violations must be corrected before completion and CI acceptance.

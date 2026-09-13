---
description: Project phase-specific knowledge obligations before producing plans and tasks.
scripts:
  py: scripts/phase_obligations.py
---

Locate the active feature using Spec Kit's current feature pointer. Use a repository-relative
feature directory. Before planning run `{SCRIPT} project --feature-dir <feature> --phase planning`
and `{SCRIPT} check --feature-dir <feature> --phase planning`. Before tasks use `project` with
`--phase after-plan`, then `check --phase after-plan` against the current reviewed plan.

Read `<feature>/phase-context.md` and the relevant referenced sections, not the entire knowledge
library. This projection complements the confirmed scope, accepted architecture and dependency
context. A missing requirement artifact is work to plan, never a reason to skip its requirement.

Before plan acceptance create `obligation-design.json` and `semantic-contract.json` using
`references/phase-evidence.md`. Name owners, applicability, design references and executable check
identities. Review each semantic conclusion; do not declare general correctness from schema success.
Record an attributable design review against `review-basis`. Carry its required checks into tasks
and `verification-plan.json`; plan the actual public mechanism, not just installing its package.

If a selected capability is deferred, record its due phase and owner. Resolve due decisions through
the confirmed intake path. An exception that weakens an accepted applicable rule requires the
owner's actual confirmation and compensating evidence. Do not invent confirmation text or a review
source. Normal supported applicability and routine technical review do not require extra approval.

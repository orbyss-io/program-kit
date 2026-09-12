---
description: Define or refine an epic, feature, requirement or meaningful task.
scripts:
  py: scripts/delivery.py
---

Read `.specify/extensions/program-kit-delivery/references/delivery.md` and the matching
`.specify/extensions/program-kit-delivery/templates/<kind>.md`. Both a business owner's
Program Kit session and imported platform content use the same content contract. Preserve human
text/comments, unknown business decisions, existing local IDs and acceptance IDs.

For initial epic capture ask only for title, problem/outcome and attributable business owner.
Use progressive refinement; do not demand an implementation plan before specification work.
Give each local roadmap/specification entry one primary Requirement binding. A Requirement can
span repositories. Introduce optional Tasks for real independent contributions or handoffs,
not for every coding checklist entry. Choose direct Requirement execution or delegated Tasks;
do not authorize both concurrently.

Validate normalized JSON through `{SCRIPT} validate-work --input <draft> --stage draft`, then
use `refinement` or `implementation` for the requested content check. Empty defaults represent
unknown information, never accepted business facts. The validator checks structural completeness
and accepted-basis consistency; it does not certify prose quality, inspect referenced commits or
grant execution authority. Resolve material ambiguities with the accountable human through the
existing coherent proposal/review flow.

Before a governed transition, use `{SCRIPT} check-admission --activity <activity>` as well as
the mandatory core governance checks. Enabled Azure refinement checks current provider authority;
implementation, delivery and acceptance admission await their later phases. Local
drafting and technical-only validation remain useful; never call their success provider readiness.
Material changed business scope requires explicit intake/planning/architecture reconciliation.

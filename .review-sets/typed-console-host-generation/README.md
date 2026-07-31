# Typed Console host generation

This review set defines Program Kit's deterministic typed Console-host
generation, host-kind-neutral generated-output integrity, and installable
incremental software-maintenance flow.

Review order:

1. `design-intent.md` — reconciled human intent and authority boundary.
2. `architecture-design.json` — canonical machine-readable design.
3. `architecture-design.md` — reviewer-oriented projection.
4. `static-conformance-disposition.json` — exact human-selected disposition.
5. `program-kit-private-gate-selection-lock.json` — exact reused private gate,
   activation, profile, and closure binding.
6. `implementation-plan.json` — canonical bounded Planning `3.0.0` plan.
7. `implementation-plan.md` — reviewer-oriented work-unit projection.
8. `validation-report.md` — validation outcomes and exact canonical digests.
9. `review-manifest.json` — exact approval boundary and artifact inventory.
10. `design-plan-approval.json` — created only after explicit human approval of
   the exact canonical design and plan digests.
11. `implementation-evidence/closure.json` — immutable work-unit, integrated
    consumer, verification, reconciliation, and release-boundary evidence.

`materialize-review-set.ps1` deterministically rebuilds the non-circular design
basis, decision source, disposition, selection lock, canonical design, and
canonical plan from current exact source truth.

Implementation completed without publishing packages, releasing Program Kit,
modifying JTest, or activating distributable capabilities in the Program Kit
authoring workspace.

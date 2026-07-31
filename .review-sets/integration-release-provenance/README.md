# Integration and release provenance review set

State: awaiting exact human approval of the canonical design and implementation
plan. No product implementation has started.

Review in this order:

1. `design-intent.md` — the human outcome, efficiency goal and authority
   boundary.
2. `architecture-design.md` — the readable architecture projection.
3. `architecture-design.json` — the canonical validated design.
4. `implementation-plan.md` — the readable six-unit execution projection.
5. `implementation-plan.json` — the canonical validated plan.
6. `validation-report.md` — validation, source truth and exclusions.
7. `review-manifest.json` — exact review-set identities, digests and approval
   boundary.

Supporting evidence:

- `github-platform-evidence.json` records the official platform contracts used
  by the design.
- `static-conformance-design-basis.json`,
  `static-conformance-decision-source.json` and
  `static-conformance-disposition.json` record the human-selected
  `reuse-existing` decision.
- `program-kit-private-gate-selection-lock.json` binds the exact current private
  gate, activation matrix and exhaustive profile for this review candidate.

The requested implementation is one coherent Program Kit source patch and pull
request. GitHub ruleset, merge-queue, protected-environment and NuGet
trusted-publishing settings remain a finite human-owned activation after the
source patch merges.

Approval must name both exact canonical digests shown in the manifest. Approval
does not extend to external configuration, merge, release or publication.

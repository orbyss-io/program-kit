# Program Kit final baseline evidence

This directory is the canonical `PK-W090` closure set.

- `full-baseline-version-map.json` contains 73 exact selected revisions and 93
  typed edges.
- `full-baseline-version-selection.json` selects every map node exactly.
- `full-baseline-migration-assessment.json` records the selected changed root,
  its terminal impact, action list, evidence, causal path, owner, and wave.
- `out-of-closure-proof.json` gives an explicit proof for all 72 revisions not
  reached from that root.
- The five `.dot` files are deterministic architecture, package, task, version,
  and forbidden-edge projections.
- `status-matrix.json`, `verification-observations.json`, and
  `clean-room-provenance-attestation.json` record completion, verification, and
  source provenance.
- `final-review-report.md` is the human review entry point.

The exact bootstrap design, plan, and approval remain the implementation
authority. The separate `../self-hosted/` set remains the W080 comparison and
lineage record; W090 does not rewrite either history surface.

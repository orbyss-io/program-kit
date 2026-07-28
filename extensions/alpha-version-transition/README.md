# Program Kit alpha version transition review

This directory is the first-stage review set for replacing Program Kit's
pre-stable version drift with explicit version intents and alpha ordinals.

Review in this order:

1. `design-intent.md`
2. `architecture-design.md`
3. `static-conformance-disposition.json`
4. `implementation-plan.md`
5. `validation-report.md`
6. `review-manifest.json`

The canonical machine-readable artifacts are `architecture-design.json` and
`implementation-plan.json`. Their Markdown files are deterministic projections.
`review-manifest.json` binds the exact review bytes.

The set is a candidate awaiting exact human approval. It authorizes no
implementation, package publication, capability activation, consumer mutation,
or JTest change.

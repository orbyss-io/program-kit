# Program Kit 0.9.3 correction evidence

PriceCalculator reproduced a cross-boundary upgrade defect after moving to Program Kit 0.9.2. The
managed tool manifest correctly advanced `ProgramKit.OpenApi.Exporter` to `0.9.2-preview.1`, while a
registered consumer-owned OpenAPI contract and its plan, tasks, and research still named
`0.9.1-preview.1`. Managed sync correctly preserved those consumer files, and lifecycle verification
correctly found unchanged spec/plan/task hashes, but the complete implementation hook then stopped at
`PKA014`. The earlier lifecycle-only post-upgrade check therefore overstated readiness.

The 0.9.3 updater now compares every registered Program Kit exporter contract with the target
release pin before acquiring its mutation lock. A mismatch returns zero-mutation `PKU110` with the
contracts to update and every present spec/plan/tasks/research/quickstart/data-model file requiring
review. Unsupported producers, unsafe paths, non-newer targets, unmapped contracts, malformed state,
and active lifecycles are never guessed or rewritten.

The explicit `--accept-openapi-producer-pin-reconciliation` path installs coherent components first,
then atomically updates only registered producer pins and exact old pin references. It removes each
affected `afterTasksAnalysis` phase and appends audit evidence containing the old/new pins, changed
paths, prior report identity/hash, reason, and timestamp. It returns `PKU111` with the required
analysis/architecture/implementation renewal sequence instead of reporting implementation readiness.

End-to-end regression coverage proves zero mutation before consent, atomic reconciliation, clean
managed sync, clean full artifact ownership, blocked implementation while readiness is invalidated,
successful structured analysis renewal, and success of the combined lifecycle-plus-ownership
implementation preflight afterward.

## Program Kit operation dependency analysis

**Ordering precedence**: This section takes precedence over task-ordering examples in the
upstream Inconsistency pass (F), including integration before foundational setup. It changes
only that ordering interpretation. Retain every other upstream analysis step, detection pass,
coverage mapping, severity rule, constitution authority, report and remediation boundary,
and `hooks.before_analyze` / `hooks.after_analyze` dispatch. Analysis remains **STRICTLY READ-ONLY**
and requires complete `tasks.md`; neither a draft nor a readiness result proves product acceptance.

Read the resolved operation-based tasks template and the `Operation dependency map` and
`Task dependency map` in tasks.md. Judge ordering by those exact dependencies and approved
spec/plan/constitution obligations, not phase names, layer names or task IDs alone. An independent
first operation may integrate before unrelated future foundation work. Do not report that as
an inconsistency or restore a blanket foundation barrier. Minimal enabling work belongs beside
the first operation that needs it; shared prerequisites gate only their named consumers.

Still report missing named prerequisites: authorization, security, ownership, storage/migration,
real-provider tests, TDD, contracts, admission and retained authority/approval gates. Report
unknown task IDs, missing map rows, dependency cycles, contradictions between maps and tasks,
and an operation scheduled before a prerequisite it actually requires. Cite the affected
operation, task IDs and spec/plan/constitution requirement; do not replace a concrete finding
with a generic requirement to finish every foundation task. A map cannot waive a mandated gate,
an unresolved product-specific ownership/replay/recovery test, or a due roadmap prerequisite.
For legacy tasks without maps, derive only dependencies supported by their approved artifacts;
report unclear or missing dependencies without inventing a universal foundation phase.

For example, owned create/list can precede later upload storage and OCR infrastructure when
its own authentication, ownership, persistence and real-provider prerequisites are established.
Missing its required authorization or provider proof remains a finding. An upload operation
requiring that storage cannot precede it; an OCR operation cannot bypass its admission gate.
Report planning coverage separately from actual executed proof: finalized tasks,
unchanged setup readiness or a focused checkpoint never establish full product acceptance.

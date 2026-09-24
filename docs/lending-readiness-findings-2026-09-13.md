# Lending readiness findings after approval

Run `ef606c1a` successfully completed `accept-bootstrap`. Its subsequent readiness
assessment is valid and explicitly NOT READY. The terminal `require-readiness`
exit code 2 correctly prevents completion. No live retry is justified unchanged.

## Confirmed blockers

The consumer's `bootstrap-acceptance-scope.json` omits these already-designed map
elements: `reservation-persistence`, `lifecycle-delivery`, `reservation-database`.
It also omits `claim-delivery`, `deliver-notification`, `complete-delivery`,
`runtime-storage`, and `runtime-recipient`. All eight remain Proposed after
approval. The three components implement durable admission, notification retry
and the real PostgreSQL store; the five relationships claim/complete durable work,
deliver notifications and connect the published runtime to storage/recipient.

They are required by the current combined RM-01 outcome. Its quality system
explicitly prohibits implementation through Proposed edges. Accepted ADRs and
passing mechanism proofs do not independently authorize these excluded semantics.
The approval handler correctly promoted only the enumerated acceptance scope.

The Accepted `decisions/closure-evidence-boundary.md` also retains unmarked current
assertions that the four prerequisites are open, `readyWhenProven` is empty and
RM-01 remains Blocked. Its appended recovery section explicitly supersedes earlier
missing-input guards, but does not reconcile that handoff/status passage. The
actual ledger has four closed proof-backed conditions and the roadmap says Ready.

## Causes and responsibility

`tests/recover_consumer_bootstrap.py` added the conditional Ready transition and
appended the compatibility correction while preserving the existing acceptance
scope. It did not reconcile the retained current-status prose. This was incomplete
recovery preparation; the user's approval did not create the inconsistency.

The deterministic `validate_roadmap` checks ADR status and prerequisite evidence,
but does not establish that the whole selected user outcome fits the reviewed map
scope. `validate_bootstrap_consistency` checks architecture and traceability
narratives, not the contradictory ADR passage. Thus those checks passed before
the agent's readiness review found the omissions. The readiness gate itself is
working as intended; changing its verdict would hide unresolved authority.

## Concrete correction for architecture review

For the existing combined trial, propose acceptance of exactly the three elements
and five relationships listed above, using their existing ownership and design.
This changes the reviewed acceptance boundary, not package choices or domain rules.
Keep production, reporting, real-recipient integration and later feature details
outside this scope. Do not accept every Proposed map item indiscriminately.

Prepare the correction through accepted-bootstrap recovery, which preserves the
completed human approval, ratification, intake, assessment, Accepted ADRs and failed
run as historical evidence. A reviewed follow-on decision must explicitly reconcile
the earlier exclusions and supersede the obsolete closure-status assertions.
Do not silently rewrite hash-bound Accepted ADRs or mark the missing map items
Accepted. The final recovery gate owns approval of the exact changed scope.

Before the next paid readiness assessment, deterministic checks should establish
that required slice dependencies are accepted or explicitly included in the pending
review, that no current-status contradiction survives, and that all preserved
proofs still match. Add regression coverage for a Ready entry with a closed proof
ledger but excluded required map semantics, and for stale status assertions in an
ADR. These checks belong before final review/readiness, using existing authorities.

This connects to the slice-decomposition audit: readiness needs an explicit mapping
from intended outcomes to required architectural dependencies. A split roadmap
would need that mapping per slice, rather than applying the combined RM-01 scope
mechanically to every entry.

## State at diagnosis

This report is a proposed correction, not consumer architecture approval or a
completed recovery. The real consumer's scope, ADRs, roadmap, review, proofs and
workflow state were not modified during this diagnosis. No agent was launched and
no proof was rerun. The 65,972-token readiness run remains useful failed-trial evidence.

## Prepared recovery and validation

Following the user's approval, the real consumer now contains a pending correction,
not a new approval. Proposed `reservation-runtime-acceptance` supersedes the old
closure bookkeeping, includes exactly the three elements and five relationships
above, and preserves the existing design and feature scope. Original Accepted ADRs
remain unchanged. Architecture and traceability narratives were shortened to satisfy
their hard budgets; final architecture/traceability/quality sizes are 10,105/6,042/8,096
bytes. Eight artifacts changed in the recovery review packet.

The recovery snapshot verifies 15 protected files unchanged, including the original
approval and failed run. All four current compatibility proofs still validate.
Review receipt SHA-256 is
`9a9564b32ced3c6fd7ce460facf7c80651c247070839a516cd8dcd8d3337bdc7`.
The consumer has no continuation mapping or bootstrap-completion receipt yet.

Deterministic checks now reject missing accepted/pending scope for explicitly
referenced canonical candidate journeys and contradictory current ADR status claims.
This scope check follows declared journey edges and their endpoints; it does not
infer extra journeys from narrative text. Accepted ADR supersession, or explicitly
scoped pending supersession during review, preserves history without retaining its
obsolete status assertions as current authority.

`--reuse-prepared-recovery` admits only a current, hash-bound prepared review with
passing proof and architecture validations. It omits the correction-authoring step
and retains human review, readiness, eligibility and completion. Missing or stale
review packets fail before dispatch; the flag cannot carry a future approval input.
The updated readiness command was also regenerated into the installed consumer
skill through Spec Kit's own extension-skill generator.

Targeted scope, lifecycle and native-resumption regressions passed. The bounded
Development suite passed (`artifacts/readiness-recovery-development.log`). An isolated
copy of the exact consumer reached `review-recovery` without agent dispatch. With
synthetic approval and an explicitly synthetic readiness result, the remaining native
validators and completion binding passed. This is mechanical recovery validation,
not live readiness evidence. No coding agent or compatibility recipe was run.
Evidence is under `artifacts/readiness-scope-recovery/`, including
`verified-handoff.json` and `native-simulation.json`.

The user can now resume from their own CMD terminal:

```cmd
cd /d C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-3yd5a74k
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id ef606c1a --reuse-prepared-recovery
```

The next checkpoint reviews this exact correction. Approval then allows the native
paid readiness assessment to proceed. It does not repeat intake or the completed
correction-authoring stage. Subsequent resumes of an existing continuation use the
original run ID without `--reuse-prepared-recovery`.

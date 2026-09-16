# Fresh-bootstrap follow-on ADR review repair

## Observed failure and cause

Human-owned trial `9bc5233a` in `program-kit-intake-wv9x2rmd` passed all five
compatibility probes, prerequisite validation and lifecycle synchronization. It
failed at `synchronize-roadmap`: Ready RM-01 required `bootstrap-proof-assignment`,
a Proposed closure ADR explicitly included in the final acceptance scope.

The workflow's final review already supports founding and scoped follow-on ADRs.
Recovery also permits those scoped proposals before review. Fresh bootstrap's
roadmap gate, however, admitted only founding proposals. The result was a circular
dependency: a legitimate decision awaiting final review prevented reaching that
review. This was a deterministic Program Kit authority mismatch, not missing
consumer knowledge or failed provider compatibility.

The earlier controlled rehearsal contained no required follow-on Proposed ADR at
this boundary. Its success did not cover this independently authored case.

## Repair and boundaries

Fresh roadmap validation now obtains pending ADR identities from the existing
`reviewed_adr_records()` authority used by final review. No new instructions,
consumer answers, status edits or alternative approval authority were introduced.
Explicit acceptance scope remains mandatory for follow-on proposals. Unscoped,
Rejected and stale decisions still fail. After bootstrap approval, a Proposed
decision is not accepted authority; the explicit recovery-review path is separate.

Only `governance_state.py` changes in shipped execution. Compatibility recipe,
tooling, selected design and proof hashes are unchanged by this repair.

## Evidence

`tests/validate_readiness_scope.py` now has nine tests. The new positive case first
reproduced the exact unresolved-ADR failure, then passed synchronization, review,
simulated acceptance, readiness and completion validation after the repair.
Negative coverage includes unscoped proposals, Rejected proposals, stale source
bindings and pending proposals after approval; scoped recovery remains supported.
Logs: `artifacts/readiness-follow-on-red.log` and
`artifacts/readiness-follow-on-green.log`.

A separate read-only capture of the actual failed consumer was copied into
`program-kit-follow-on-replay-kc2px12c`. Its original gate failure was reproduced,
then only the copied installed governance script was replaced. Original proof
receipts validated without rerunning probes. Roadmap synchronization, consistency,
bootstrap validation, first-feature handoff, review generation, simulated
acceptance and accepted-authority validation passed. The task-authored replay
readiness report passed all four stage checks: READY, zero blockers, authority
valid and completion eligible.

Evidence is under `artifacts/follow-on-9bc5233a-x8uvxngl/`, including step logs,
source hashes and `result.json`. The original consumer's file hashes were identical
before and after replay. The copy has no consumer authority and started no agents.

Two replay limits are retained explicitly. An earlier attempt used Python 3.13
against the consumer's Python 3.12 schema cache; it stopped at runtime discovery.
The corrected replay used the consumer's installed Python 3.12. The direct CLI
completion attempt was rejected by the native-workflow ownership guard, as intended.
No native workflow completion is claimed for the copied consumer. The deterministic
fixture separately exercises completion; this is not a fresh independent live run
or a guarantee that all future generated artifacts will pass.

The bounded Development suite passed (exit 0); its result is recorded in
`artifacts/readiness-follow-on-development.log`.
The setup-only intake smoke test also passed. Record
`artifacts/intake-sessions/1b2af750f58845e688ca11a2550deefa/` preserves the fresh
installation; its installed governance script matched the repaired source by
SHA-256. It started neither an intake agent nor bootstrap.

## Next consumer attempt

The original failed consumer remains untouched. A new human-owned intake started
from this repaired source receives the change. Its consumer answers and reviews
remain the user's responsibility; no fictional answer or approval is carried over
from the isolated replay.

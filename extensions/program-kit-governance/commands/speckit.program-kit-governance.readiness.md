---
description: Render bootstrap initialization and phase readiness from validated governance authority.
scripts:
  py: scripts/governance_state.py render-readiness
---

## Input and execution

Use the current consumer repository and the native run ID supplied in `$ARGUMENTS`.
Run `{SCRIPT}` with `--run-id <run-id>` when the native run ID is provided. This
deterministic command validates accepted design, ratification, approval hashes,
first-slice scope, prerequisite evidence and outstanding owned questions, then
renders `docs/architecture/readiness-report.md`. Report its result and stop.
Do not independently author a verdict or reinterpret proposal-time status prose.

## Authority and limits

The decision catalog owns decision status; the prerequisite ledger and verified
receipts own proof closure; the specification roadmap owns entry status. Approval
records bind reviewed content. Generated document views are navigation, not new
authority. ADR bodies preserve decisions and proposal-time reasoning. Passing a
proof or approving a proposal does not require a successor ADR merely to retire
an earlier description of that state.

Substantive conflicts must be resolved in the existing closure handoff before
acceptance: identify the affected choice, contract or requirement, its source,
owner and required decision. Unresolved questions must be carried into owned, phase-scoped ledger obligations; they need not be resolved to initialize the repository. Actual changes to accepted design still require reviewed changes;
do not edit accepted documents, waive evidence or suppress a genuine finding.

The native workflow generates final readiness without an agent dispatch. It owns
recovery, approvals and completion. INITIALIZED means the reviewed baseline is complete. Each slice has separate specification, planning and implementation eligibility; no phase is authorized by initialization alone.
No agent-authored report, process exit or standalone completion file establishes
native workflow completion.

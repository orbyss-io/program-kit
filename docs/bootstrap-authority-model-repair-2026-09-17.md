# Bootstrap lifecycle authority repair

## Failure and design change

Run `ec954452` passed four compatibility probes, consistency validation and final
acceptance. Its readiness agent then rejected proposal-time sentences in
`closure-disposition.md`, including “The founding ADRs remain Proposed”. The catalog
already recorded acceptance and the ledger recorded successful proof closure.
The late narrative verdict introduced a second interpretation of current state.

Fresh bootstrap now finishes with three native shell steps: `readiness` renders
the report, `require-readiness` verifies eligibility, and `complete-bootstrap`
records engine-owned completion. The final agent dispatch and four obsolete
readiness context/handoff/output steps were removed. No consumer answer or ADR
supersession is needed merely because an existing proof or approval has completed.

| Fact | Existing authority |
| --- | --- |
| Accepted design and scope | Decision catalog, ADR metadata/content hashes and acceptance scope |
| Unresolved work and proof closure | Owned questions, source-bound prerequisite ledger and verified receipts |
| First specification eligibility | Roadmap entry plus canonical first-slice coverage |
| Human acceptance | Exact approval records and ratified constitution |
| Completion | Validated readiness and the completed native workflow |

ADR narrative preserves decisions and proposal-time history. Its wording no longer
independently sets roadmap status or requires a successor just to retire an old
status sentence. Content hashes, required decisions, canonical scope and actual
proof obligations remain enforced. A substantive change still requires the
existing reviewed correction mechanism.

## Review before approval

The existing closure stage owns first-slice design review before final acceptance.
It receives confirmed first-slice journeys and quality requirements, the existing
first-feature handoff with exact architecture scope, and indexed architecture,
quality-system and traceability sources. Substantive findings use existing owned
design questions and prerequisites. No new approval packet or competing findings
registry was added. Future work keeps its declared trigger.

The context regression measures 11,725 bytes for closure, below the existing
32 KiB bound. An initial whole-portfolio projection exceeded that bound and was
replaced with the exact handoff plus indexed sources; the bound was not increased.

Recovery uses the same readiness renderer. Approval reuse is decided from current
validated authority and recorded questions, not an old report's independent verdict.
The known 0.12.0/0.12.1 continuation suffixes migrate to internal continuation
revision 0.13.0, preserving lineage and accepted prefixes. Unknown suffix changes
still fail. The public component candidate remains the coherent, unreleased 0.12.0
set; this work publishes no release.

## Verification and limits

- Nine scope/authority regressions cover proposal-time wording through acceptance,
  scoped versus unscoped decisions, rejected proposals, post-approval authority,
  stale content and a substantive unreviewed edit.
- Six readiness projection tests include the actual shipped terminal workflow
  reaching native completion with agent dispatch forbidden. Missing approval, an
  open first-slice prerequisite and a recorded substantive design question block.
- Native resumption tests cover interruption of the readiness shell, historical
  suffix migration, preservation of source runs and approvals, real changed-input
  review, idempotency, semantic rejection and completion binding.
- The bounded Development suite passed; the additional context validator passed.
  Logs: `artifacts/authority-development-candidate.log`,
  `artifacts/authority-projection-final.log`, `artifacts/authority-resumption-final.log`,
  `artifacts/authority-context-final.log` and `artifacts/authority-scope.log`.
- Fresh setup-only installation passed after keeping the workflow version aligned
  with the unreleased 0.12.0 bundle. Record
  `artifacts/intake-sessions/0f5b275b6b074127a8205b62767fe1d0/` preserves the installation.
  Installed governance, stage declarations and workflow hashes matched source.
  This check started no intake agent or bootstrap workflow.

The actual failed consumer was copied to `pk-authority-ec954452-kgg22ynh` for a
counterfactual **governance-component replay**. Only its governance script was
replaced; original compatibility tooling was retained so existing receipts were
not relabelled as evidence for changed tooling. The new renderer returned READY
with zero blockers while the ADR, approval, ledger and canonical map stayed byte
identical. The original consumer's hashes remained unchanged. Evidence lives in
`artifacts/authority-ec954452-_nnsw8vl/`; no agents or probes ran in that replay.

This component replay is not an all-new-candidate live trial. The complete current
candidate is covered by deterministic tests, including native terminal execution;
independent intake/closure authoring reliability remains to be measured in a fresh
live trial. Existing proof receipts retain their exact tooling requirements.

One independent readiness dispatch and four fresh terminal shell steps have been
removed. End-to-end token savings, time savings and review quality have not been
measured: closure now performs the substantive review earlier. No universal success
rate or fresh live acceptance is claimed.

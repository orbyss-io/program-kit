---
name: program-kit-release-readiness
description: Assess release readiness for maintaining the Program Kit repository, verify or request exact-candidate CI qualification, and recommend relevant optional AI trials. Does not apply to consumer application delivery or grant paid-worker, tag, or publication authority.
---

Read repository `AGENTS.md`, `docs/releasing.md`, `docs/maintenance/dependency-review.md`
and `release-policy.json`. Scripts and CI enforce the gates; do not invent a second
checklist or substitute prose for verified evidence.

Establish the exact committed candidate and changes since the previous successfully
published release. Inspect dependency-maintenance evidence and report missing or failed
maintenance explicitly. Do not perform unrelated dependency updates as part of an
implementation task. Preserve historical receipts/profiles and consumer locks.

Use `python scripts/release_candidate.py find`, then `download --run-id <id> --output
artifacts/verified/<unique>` to verify an existing complete matching qualification.
When readiness work is authorized and no valid complete run exists, dispatch
`gh workflow run qualify-candidate.yml --ref main -f expected_commit=<exact-SHA>`.
Wait for completion and inspect actual jobs and immutable artifact identities. Main
advancing before dispatch is a source mismatch to resolve, never implicit permission
to select a different candidate. Partial runs cannot be combined into qualification.

Use `recommend --base <previous-successful-release-commit>` for change-based optional
trial recommendations, reasons and gaps. Inspect the actual affected behavior and
scenario/oracle before recommending a phase. CI-only plumbing does not motivate an
unrelated paid trial. Migration recommendations include `upgrade-consumer`, actual
human governance handoff, and separately authorized `upgrade-continuation` using the
active knowledge-application/v3 fixture. Unimplemented scenarios are coverage gaps.

The user selects trials. If selected, `prepare-trial --run-id <id> --output
artifacts/trial-preparation/<unique>` verifies CI bytes, actual local prerequisites
and disposable installation, producing separate local host evidence. It starts no
paid phase. Each phase still requires its own interactive one-use authorization via
`New-LiveAcceptanceAuthorization.ps1 -CiPreparation <record>`, exact parent checkpoint,
model and worker sandbox. Preserve cleanup, redaction and supervisor-owned credentials.
Do not ask about or start paid work merely because publication is being prepared.

Assess local concerns individually; no local execution can be a valid outcome. Preserve
full trial evidence internally. Draft the concise `release-assessment` schema with
recommendations, user selections, actual trial scope/outcomes and internal manifest
references/digests. No run means no AI acceptance claim. Submitted outcomes are human
attested unless independently inspected under an applicable evidence contract. Confirmed
product defects block readiness until repaired; harness/inconclusive results need explicit
disposition. Obtain attributable review of the concrete assessment before dispatching
`record-release-assessment.yml`; do not claim that signing submitted JSON proves a trial.

Run `verify-promotion --run-id <id> --output artifacts/promotion/<unique> --tag v<VERSION>`
without publication. If only security is stale, dispatch `refresh-candidate-security.yml`
for the unchanged candidate, retaining deterministic qualification. Later failed scans
and unresolved findings cannot be hidden by selecting older passes; record explicit
supersession/resolution. Respect policy freshness separately from artifact retention.

Report exact source, qualification run/attempt, artifact IDs/digests, readiness findings,
security age and remaining human/device concerns. Keep the assessment supplemental;
never append to hashed payload assets or upload full worker logs automatically. A dry
verification does not establish publication/public-smoke success. Tagging, publication
and failed-tag correction retain their own explicit exact-candidate user authority.

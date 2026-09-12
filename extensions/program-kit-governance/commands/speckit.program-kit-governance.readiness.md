---
description: Determine whether the repository is ready to begin feature specifications.
scripts:
  py: scripts/governance_state.py validate --require-roadmap --require-ready
---

## Input

`$ARGUMENTS` identifies the bootstrap scope and the workflow-generated bootstrap context path.

Read the compact bootstrap stage brief first. It contains confirmed journeys, compact approved
authority records, decision statuses, and a link to a separate hash-bound evidence index. Read the
ratified constitution in full. Do not print or read the evidence index in full; query one artifact
and heading range only when the brief lacks decisive evidence for a readiness condition. Do not
bulk-read every unchanged artifact, grep every status in the repository, or enumerate installed
files.
Use `governance.paths` and `output_contract` directly. Do not search `.specify`, unrelated
extensions, catalogs, or validator implementation to rediscover paths or validation rules.
Use `output_contract.artifact_target_bytes` as the initial generation target and
`output_contract.artifact_byte_budgets` as the hard boundary after writing the report. Report its
final byte count; do not omit decisive evidence merely to reach a target.
An over-target warning below the hard budget is not a failed check. Do not add ad hoc size
assertions or repeatedly truncate the report.

For an accepted-bootstrap continuation, use its current source paths rather than new intake
or stale historical context. Read the current prerequisite ledger, evidence bindings and
preserved authority. The workflow owns evaluation, eligibility and completion. Produce the
report, then stop; never invoke independent recovery acceptance/completion or claim that a
standalone completion file proves workflow success.

## Constitutional and portfolio prerequisites

Run the governance-state validator with both portfolio requirements:

```text
{SCRIPT}
```

`NOT READY` is mandatory when the constitution is missing, Draft, unratified, hash-mismatched,
contains placeholders or TODOs, lacks semantic version/ratification/amendment governance, or when the
specification roadmap is missing, invalid, or has no Ready entry. Do not repair or ratify either
artifact while evaluating readiness.

## Readiness gate

Evaluate the projected ratified authority, confirmed intake, architecture, decisions, risks,
quality system, roadmap, and traceability evidence from the stage brief. Query one source only when a
decisive readiness fact is omitted or contradictory. Report `READY`, `CONDITIONALLY READY`, or
`NOT READY`.

Write `docs/architecture/readiness-report.md` beginning at byte zero with an exact first line of
`**Status**: READY`, `**Status**: CONDITIONALLY READY`, or `**Status**: NOT READY`, followed by the
evidence, remaining triggered decisions, and next specification. The deterministic workflow
completion step accepts only the exact READY status and independently validates ratification,
bootstrap approval, artifact hashes, and a Ready roadmap entry.
For every blocking item in a non-ready report, write
`- Blocker: <id> | Owner: <owner> | Next: <bounded corrective action>`.
Do not put unresolved blocker lines in a READY report. A valid non-ready assessment is successful
evaluation, not completion eligibility; its terminal batch returns the explicit structured verdict.

`READY` requires that implementation-blocking architecture decisions are Accepted, significant risks have owners and verification, technology statuses are honest, architecture views are internally consistent, and the first specification can be written without smuggling in an unreviewed architecture choice.

Treat `docs/architecture/specification-roadmap.md` as the sole authority for roadmap-entry status.
The marked roadmap views in architecture and traceability are deterministic derived navigation;
report anything else that copies or contradicts roadmap status as not ready.

The first specification must be a viable vertical slice with an actor, trigger or intent, owner,
observable outcome, contracts, material failure paths, and verification, or it must carry a justified
proportional exception. Its module and feature dependencies must fit the accepted graph. A plan that
must first build broad controller, service, repository, database, frontend, or infrastructure layers
is not ready.

For an authenticated browser/API slice, require a selected, versioned secure web profile with an
executable runtime/configuration contract and identity-provider test fixture. Do not report the
slice as blocked merely because it omits authority, client, claims, middleware, CORS, CSP, session,
refresh, logout, health, or browser-test details already owned by that profile. Report it as not
ready when no profile is selected or when the slice contradicts the selected profile without an
Accepted override.

For that browser boundary, `READY` also requires the accepted architecture to inherit
`program-kit-web-threat-model-v1` and `program-kit-web-security-evidence-v1`. Confirm that any
project-specific assumption, residual-risk acceptance, CSP/session/time-budget change, provider or
deployment change is owned and backed by an Accepted ADR and regression evidence. Browser tests are
behavioral evidence, not a security certification; the readiness report must not claim absence of
vulnerabilities or treat local development configuration as production approval.

Unresolved decisions may remain only when they do not block the proposed first specification. List each remaining decision with the earliest lifecycle point at which it must be resolved.

Do not count an explicit intake choice, Program Kit default, derived default, or reviewed override
from the approved bootstrap decision register as unresolved. Do not block early specifications on a
decision explicitly deferred to production or another later trigger.

A roadmap entry cannot be Ready while any required ADR or implementation decision is unresolved.
At least one Ready entry must be suitable for the first feature specification and its complete
planning, task, and implementation lifecycle without introducing an unreviewed architecture choice. A dependency or
recommended sequence that says a Proposed choice, design task, or later ADR must be accepted before
implementation makes the entry Blocked, even if specification drafting could begin. Design tasks
are never reported as feature specifications or implementation-ready work.

Do not change an ADR status while evaluating readiness.

Keep the report decision-oriented: status, blocking evidence, remaining triggered decisions, and
the next specification. For a single Ready entry with no blockers, use the byte target supplied by
`output_contract`. Report the
path, status, and validation counts only; do not print the complete report or repository-wide diffs.
Run the single command in `output_contract.validation_commands` before reporting completion. It
batches the output-budget, exact status syntax, roadmap/approval authority evaluation and structured
completion-eligibility checks. READY alone can complete. CONDITIONALLY READY and NOT READY preserve
the assessment and route to owned recovery; do not alter the verdict to satisfy a validator. Repair only a named
diagnostic and rerun that same batch once. After it passes, stop immediately: do not inspect a diff,
remeasure files, read another source, or run another command.

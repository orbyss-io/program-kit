# Paid repository sync comparison

This is a fixture and review contract, not an executable authorization. No paid run is approved
by generating this packet. The existing v2 bootstrap and building-block phases do not establish
feature-flow or upgrade acceptance, and their authorizations must not be reused for these cases.

## What the human reviews before any paid stage

- The exact baseline and candidate release receipts, source revisions and artifact hashes.
- The sealed starting checkpoint and this fixture's inventory hash.
- The stage's prompt, model, reasoning effort, timeout and maximum paid sessions (one).
- The exact feature brief and its hash when crossing the grilling confirmation boundary.
- Required supervisor operations, registry routes and credential names, with no credential values.

The baseline and candidate use the same request, accepted architecture, catalog/component pins,
toolchain, model, effort and stage limits. Their installed Program Kit versions differ. Create
equivalent accepted checkpoints under each candidate; never rewrite a receipt or transplant
ratification hashes to make an older checkpoint appear current. Record environmental differences
and cold/warm package cache state. Do not compare runs when required bindings differ.

Use this directory's `bootstrap-seed` as `-Scenario` for both bootstrap authorizations and runs.
It is a fixed variant of Internal Forms Workspace v1 with the stock Foundation Dockerfile shared
by 0.11.0 and 0.12.0. The original fixture's `FROM scratch` placeholder conflicts with the managed
Dockerfile in both versions. That original fixture remains unchanged; a deterministic guard test
requires the conflict to preserve all consumer bytes. This comparison isolates setup orchestration
from that separate container migration. Review the seed inventory before authorizing either run.

The baseline feature run supplies the materialized checkpoint for upgrade. Add a fixed
consumer-owned source/configuration change, capture its bytes before upgrade, and assert those
bytes remain afterward. Maintain a planned RM02 placement with no target files. Also exercise a
fresh JavaScript-only consumer deterministically so .NET is not a hidden setup prerequisite.

## Independent oracles

| Assertion | Evidence required |
| --- | --- |
| Human intake confirmed | Current brief/review/confirmation hashes and specification traceability validate. |
| Spec/plan/tasks traceability | Real installed lifecycle hooks pass, with the workflow and command records preserved. |
| Strict package evidence | Exact package metadata, strict npm graph and locked .NET/npm restore receipts bind the current inputs. |
| Mixed stack build and functional smoke | Independent build, test and browser checks verify the requested valid, invalid and reload paths. |
| Future feature unmaterialized | RM02 target inventory remains absent after setup, upgrade and repeated checks. |
| First lookup correct registry | Supervisor request log shows the scoped package first requested from its catalog source. |
| No consumer setup helpers | Changed-file inventory and reviewed commands show no ad hoc registry/CA/toolchain helper. Product files are not helpers. |
| Current phase readiness | Planning readiness does not claim materialization; implementation setup becomes ready only after approved targets and current restore evidence. |
| Same sync coordinator | Upgrade operation receipt names the same coordinator and adapter inputs used by the feature flow. |
| Consumer edits preserved | Before/after hashes for the fixed consumer files match. |
| Offline upgrade no network | Monitored upgrade process tree records zero package-network operations; outstanding restore is explicit. |
| Obsolete command removed | Installed commands/skills contain governance-sync and omit the retired dotnet-sync entry. |
| Stale evidence rejected | A controlled input change invalidates its dependent proof and does not discard unrelated current proof. |
| Unchanged sync no work | Repeated sync/upgrade has no file changes or repeated package operations. |

Failure injection (missing token, denied access, missing CA, unavailable package, incompatible
graph, interruption, changed digest, consumer conflict, partially materialized targets) belongs
in deterministic tests first. Do not spend paid sessions merely to repeat these branches.

## Measurements and acceptance

Count setup discovery commands, wrong registry requests, resolution attempts, repeated unchanged
operations, ad hoc setup helpers, setup failures and human interventions. Every count needs an
evidence reference and classification rationale. Record unavailable measurements as null, never
zero. Preserve redacted worker streams and raw-stream hashes using the v2 evidence store.
Do not infer command counts from a worker's summary. A failed or incomplete run cannot establish
efficiency improvement. Report raw counts and deltas for equivalent successful runs; a single
pair supports a case study, not a general speed claim. Wall-clock duration is descriptive because
model and service latency vary.

Candidate acceptance requires all functional and governance assertions. It also requires zero
wrong-registry requests, consumer setup helpers and repeated unchanged operations. Compare the
remaining setup counts to the successful baseline and explain any increase. Failures remain
visible, including infrastructure/external-service failures; a rerun needs new authorization.

## Running the stages

`New-LiveAcceptanceAuthorization.ps1` supports the paid phases `feature-intake`, `feature-planning`,
`feature-plan-tasks`, `feature-setup`, `feature-delivery`, and `upgrade-consumer`. Use `-Case
fresh-baseline`, `fresh-candidate`, or `upgrade-candidate`, the exact checkpoint, release receipt,
model and effort. `-ReleaseRoot` names the clean checkout owning a baseline receipt when different
from the harness checkout. Every manifest binds one session, current harness and exact parent.
Run only its matching `Test-LiveRepositorySync.ps1` phase/case/authorization/checkpoint tuple.

Start from a v2 accepted bootstrap checkpoint. Intake creates a review checkpoint and stops. In a
human-owned terminal, use `Confirm-LiveFeatureIntake.ps1 -RunManifest <manifest> -ReviewSha256 <hash>`
to read and confirm that exact review. Planning accepts only the human-confirmed checkpoint. The
runner never fabricates confirmation or starts a paid continuation. Reruns need new authorizations.

Planning stops at a structured package-request boundary. The supervisor uses installed metadata and
graph helpers; the baseline observation wrapper uses only the baseline's installed npm runtime and
routing behavior. Setup stops at a hash-bound restore request. Registry credentials never enter worker
environments. Upgrade invokes the release updater offline before the worker checks continuation.

The runner records stage checkpoints, frozen-validator/approval checks, future-path checks and
independent build/verification results. It reports `acceptanceScope: stage-boundary-only` and
`functionalAcceptancePending: true`. Those checkpoints feed the functional/browser review and
evidence-backed comparison above; they are not full-flow success reports. Metrics remain unknown
until streams are classified with evidence references. The review preparer issues no manifest and
starts no worker. Exact receipts, model selection and human confirmations remain prerequisites.

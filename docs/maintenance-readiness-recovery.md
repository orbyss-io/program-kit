# Accepted bootstrap readiness failure: diagnosis and recovery

Program Kit 0.10.2 was published and PriceCalculator completed artifact recovery. This document
also describes the separate candidate workflow-engine resumption integration. The original
`bd6be6ca` native run remains unchanged and historically aborted.

## Causal diagnosis

The readiness terminal batch validated existence/size and governance prerequisites but never
parsed the readiness verdict. `--require-ready` referred to a roadmap record. Thus a valid-sized
NOT READY report appeared to pass, before the independent completion guard correctly rejected it.
The abort-only failure gate then misreported a technical failure as user rejection after approval.

The roadmap also hid an implementation prerequisite in its preamble and redefined Ready as
specification-ready. Per-record prose checks did not reconcile the immutable assessment's
managed-provider-closure or the future conditions retained in an Accepted founding ADR.
Offline placement and package resolution were structural evidence, not runtime/provider proof.
Approval promoted founding metadata and original candidate map scope without reconciling newly
designed semantics and copied lifecycle prose. Ratification metadata was valid; stale constitution
prose does not justify silently editing or reratifying its approved bytes.

## Changed contracts

- A shared exact status parser rejects malformed, missing, duplicate and BOM-prefixed statuses.
  Valid READY, CONDITIONALLY READY and NOT READY assessments return explicit JSON verdicts and
  actionable blockers. Only READY with valid authority is eligible. Hard size validation is
  independent of the advisory generation target. `require-readiness` stops non-ready workflows
  with exit 2 before completion; the abort-only gate is removed.
- A reviewed prerequisite ledger inventories the complete decision register and ADR condition
  sources, binds their substantive hashes, and records affected slices, owners, triggers,
  dispositions and closure evidence. Open architecture prerequisites block only dependent slices.
  Changes to feature/later ownership of unresolved or ADR conditions require explicit decision
  authority. Ordinary feature rules and already-deferred production policy remain at their triggers.
- An executed bootstrap-closure handoff runs bounded compatibility recipes in disposable working
  directories. Receipts retain command/runtime, recipe, selected design/pin bindings, exit status
  and both stream hashes. Windows uses a suspended launch and Job Object for descendant cleanup.
  These are component proofs; feature behavior tests remain owned by the feature lifecycle.
- Explicit acceptance scope governs new and founding map semantics. Deterministic lifecycle views,
  selection bindings, DSL and approval hashes are refreshed together. Failed promotion rolls back
  the mutated ADR/map/selection/narrative/DSL set. Unrelated proposals remain unaccepted.
- The recovery command freezes the original run, approval and artifacts in a flat content-addressed
  archive with a path-to-hash manifest. It never edits state.json or starts a duplicate bootstrap.
  It supports the historical technical abort-only signature and new failed readiness steps,
  rejects semantic rejection, and requires review of the exact corrected architecture bundle.

The detailed shipped authoring contract is
[bootstrap-lifecycle.md](../extensions/program-kit-governance/references/bootstrap-lifecycle.md).

## Workflow-managed continuation

Program Kit 0.10.2 was published and PriceCalculator subsequently completed artifact recovery.
Its original `bd6be6ca` native workflow remains historically aborted. Those completed artifact
checks do not demonstrate native workflow resumption. Preserve both facts and the original evidence.

The workflow integration in this candidate replaces the manual producer/synchronize/review/accept/
evaluate/complete sequence. Install a coherently released candidate containing that integration
before using the following entry point from the consumer's normal human-owned terminal:

```powershell
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id bd6be6ca
```

The lifecycle selects a bounded producer restart or an explicitly linked native continuation.
It preserves successful history, the approved intake, assessment, constitution and Accepted ADRs.
When changed architecture requires approval, it generates an exact review packet and pauses at a
real native review gate. After the human approves that packet, resume the same source run:

```powershell
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id bd6be6ca --input recovery_verdict=approve
```

The source ID resolves to the existing continuation, including on repeated calls. The engine
executes readiness, validation, eligibility and completion. A non-ready verdict remains a failure
with owned blockers. Check both governed artifacts and the bound engine terminal outcome:

```powershell
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py validate-completion
```

Existing independent recovery records remain historical artifact evidence. Do not rewrite the
original aborted run, restart intake, force READY, or claim that those records prove native success.
See the shipped [workflow resumption contract](../extensions/program-kit-governance/references/workflow-resumption.md).

## Regression evidence

`tests/validate_bootstrap_lifecycle.py` exercises the approval transition including an actual Draft
selection, exact scoped semantics, narrative/DSL consistency and final approval hashes; executes an
isolated test-only SQLite port recipe; checks evidence/source/pin staleness; rejects invalid status
forms; proves non-ready routing using the real Spec Kit workflow engine with agent dispatch mocked;
and reaches valid completion in both a fresh deterministic fixture and an approved/aborted recovery
with a reviewed follow-on ADR. The SQLite fixture is not PriceCalculator provider evidence.

The bounded Development suite passed, including component/command manifests, placement, selection,
the new lifecycle regression, schemas and offline bundle validation. Targeted governance-state and
bootstrap-context regressions also passed. No coding agent session is started by these tests.

The read-only probe below passed against a disposable copy of the actual consumer evidence. All
76 watched consumer files were unchanged. It confirmed these prompt identities:

| Evidence | SHA-256 |
| --- | --- |
| Original aborted state | `67e5b1c4da0d8b79401c677b11f5196fe3447b6da29855ce3e698dba58bef7e2` |
| Original bootstrap approval | `e4cc45e5d27acc9a6fdb71840a2937872f902f7b4741879a77d7fa882998f8f5` |
| Original readiness report | `5bfe9636f99e71b215a38507ead9418d1483459d20aa4d6d8df83b4d5219c7ae` |

```powershell
python tests/probe_accepted_bootstrap_recovery.py --consumer C:\Code\Orbyss\PriceCalculator --run-id bd6be6ca
```

The probe proves recovery preparation and preservation for the actual terminal state. It creates
no completion record and establishes no provider compatibility. Firefox remains in CI; its known
local Windows launch limitation is unchanged.

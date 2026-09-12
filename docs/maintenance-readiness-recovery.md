# Accepted bootstrap readiness failure: diagnosis and recovery

This is an upstream maintenance patch, not a claim that a new release is published or that
PriceCalculator has completed recovery. The original `bd6be6ca` consumer run remains untouched.

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

## Exact procedure for bd6be6ca

Run these commands from a normal user-owned PowerShell terminal. Program Kit owns all mechanical
bookkeeping and uses the already confirmed intake. Preparation can be performed immediately with
the patched source command; it starts no agent and does not change the original run or approval:

```powershell
Set-Location C:\Code\Orbyss\PriceCalculator
python C:\Code\Orbyss\_ProgramKit\extensions\program-kit-governance\scripts\bootstrap_recovery.py prepare --run-id bd6be6ca
if ($LASTEXITCODE -ne 0) { throw 'Recovery preparation failed; preserve the diagnostic.' }
```

Preparation writes `.specify/governance/bootstrap-recovery/bd6be6ca/handoff.md` and the immutable
evidence manifest. Repeating preparation verifies and reuses that archive.

Before the producer/validation phases, install a coherently validated Program Kit release containing
this patch through the existing sequential release-owned `upgrade_program_kit.py` procedure.
The old 0.10.1 installed skills/validators do not contain these contracts. Do not overlay individual
skills or assume that resuming the saved 0.10.1 workflow picks up a new definition. Publication and
its Release gate are separate from this maintenance change.

Invoke the installed `$speckit-program-kit-governance-bootstrap-recovery` with
`.specify/governance/bootstrap-recovery/bd6be6ca/handoff.md`. This executes the architecture-closure
instructions on the existing artifacts. The agent must:

1. Scope RM-01 to anonymous hosted estimation and a durable result. Determine which actual runtime
   and persistence choices it requires. Admin form-provider, BFF and identity tests are dependencies
   only of the slices that use them. Synthetic business fixtures do not prove durable persistence.
2. Execute and inspect the corresponding compatibility recipe, or retain an owned open blocker
   with a precise next action. Follow-on Proposed decisions must trace any closure or authorized
   changed disposition of the original retained conditions. Do not rewrite the assessment register
   or Accepted ADRs to erase those conditions.
3. Correct current architecture/quality/traceability narrative claims, preserve dated proposal
   history, and declare exact acceptance scope. Do not alter the ratified constitution. If a
   constitutional amendment is necessary, use its separate governed amendment procedure; the
   bounded recovery deliberately refuses changed ratification authority.
4. Run the supported synchronization and review commands:

```powershell
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py synchronize --run-id bd6be6ca
if ($LASTEXITCODE -ne 0) { throw 'Recovery synchronization failed.' }
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py review --run-id bd6be6ca
if ($LASTEXITCODE -ne 0) { throw 'Recovery validation failed; repair the named producer.' }
```

Review `.specify/governance/bootstrap-recovery/bd6be6ca/review.md`, including every named changed
artifact, before/after hash, prerequisite disposition/evidence and acceptance scope. This is the
renewed decision: changed architecture and follow-on decisions require review; intake, assessment,
ratification and original founding approvals remain preserved. Then the user runs:

```powershell
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py accept --run-id bd6be6ca --verdict approve
if ($LASTEXITCODE -ne 0) { throw 'Recovery approval failed or its review basis changed.' }
```

Invoke the installed readiness producer with the recovery handoff. It evaluates current evidence
and writes its own honest report. It does not edit the original workflow context. Its terminal
batch and final completion commands are:

```powershell
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py evaluate --run-id bd6be6ca
if ($LASTEXITCODE -ne 0) { throw 'Readiness artifact validation failed.' }
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py complete --run-id bd6be6ca
if ($LASTEXITCODE -ne 0) { throw 'Recovery is not complete; inspect the structured blockers.' }
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-completion
if ($LASTEXITCODE -ne 0) { throw 'Completion authority is invalid.' }
```

A non-ready evaluation is retained with `eligible: false`; evaluation exit 0 alone is not success.
The 3,126-byte report's target warning is independent of that verdict. Completion requires valid
current authority and READY, and writes both the canonical completion and a recovery completion
linked to the unchanged historical run. Provider unavailability remains an honest blocker.

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

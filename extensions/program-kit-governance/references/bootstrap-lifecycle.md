# Bootstrap prerequisite, verdict and recovery contract

The architecture owner, followed by the bootstrap-closure command, owns technical bookkeeping.
Roadmap Ready means a slice can proceed through specification, planning and implementation without
an unreviewed external architecture choice. A specification-ready qualifier cannot redefine it.

`docs/architecture/bootstrap-prerequisites.json` has schema_version `1.0`, `sources` and
`prerequisites` arrays. It is part of the reviewed and hash-bound bootstrap artifact bundle.
Source entries have `path`, `sha256` and `prerequisites` (condition IDs). Inventory the complete
approved decision register and every cataloged ADR, including conditions retained in Accepted ADRs.
`bootstrap_lifecycle.py source-hashes` computes these hashes, normalizing only Proposed/Accepted
status metadata so approval cannot silently discharge a future condition. Any substantive source
change requires re-inventory and renewed review. Empty conditions are an explicit reviewed assertion.

Each prerequisite has exactly these fields:

```json
{
  "id": "public-durable-provider",
  "source_ids": ["managed-provider-closure"],
  "affected_slices": ["RM-01"],
  "disposition": "architecture",
  "trigger": "before-implementation",
  "owner": "Architecture maintainer",
  "task": "Prove the pinned anonymous estimation runtime can persist and retrieve its result",
  "rationale": "RM-01 requires a durable result; admin form authoring is independent",
  "status": "open",
  "evidence": []
}
```

Every unresolved/deferred register ID must appear in source_ids. Split a broad prerequisite across
actual affected slices when necessary; use distinct IDs and preserve the common source ID.
Architecture/before-implementation items block only their affected Ready/Active records while open.
Feature/feature-plan items identify ordinary specification/planning decisions inside accepted
boundaries. Later/production and later/later-release items retain later policy triggers. Their
classification, rationale and source-condition inventory require the same review as architecture.
Do not relabel a shared provider dependency as feature-owned to bypass it.

## Assign conditions before drafting proofs

Separate three kinds of work at their originating phase, before placing conditions in an ADR:

- Consumer intent: intake resolves consequential choices such as intended browser/native access.
  Confirmed proposals and applicable defaults remain decisions, not unanswered preferences.
  A genuinely new human constraint returns to the consumer at its owning review; a runtime receipt
  cannot answer it, and a Program Kit maintainer cannot answer on the consumer's behalf.
- External feasibility: research selects supported mechanisms, exact pins and source evidence;
  architecture resolves ownership, contracts and placement. A specific unresolved compatibility
  risk needs a bounded bootstrap probe of that mechanism. Identify the uncertainty and named case;
  do not require building the actual feature to establish the architecture baseline. Generic runtime
  receipts cannot substitute for a required provider or identity interoperability proof.
- Consumer implementation: feature specification/planning resolves policy and admission details;
  implementation/delivery proves the real behavior. Use existing persistence-profile admission,
  secure-web, composition and UI verification gates. Examples include consumer transaction/retry
  policies, membership mapping, actual bundle activation, and actual device/accessibility journeys.
  Confirmed browser intent is not proof those device checks passed. A concrete feasibility concern
  can justify an earlier probe; the mere absence of future application code cannot.

For each retained condition name its source, affected slice, owner, next action and actual gate.
Split a combined external compatibility and consumer behavior condition rather than moving the
whole condition to whichever phase is convenient. Preserve all required verification. Resolve
misassigned conditions through the existing reviewed decision process, never by silently editing
approved intent or treating a Proposed-to-Accepted promotion as test evidence.

Closed items require evidence entries with `path`, `sha256`, `kind` (`compatibility` or `decision`).
Decision evidence uses the same normalized source hash from `source-hashes`; compatibility
receipts use their raw file SHA-256. Disposition of an unresolved assessment item or ADR condition
as feature/later work requires a cataloged decision as explicit authority, Proposed only during
review and Accepted at readiness. Its hash-bound entry in `sources`, listing that exact condition
in `prerequisites`, supplies this authority; a duplicate `kind: decision` entry in `evidence` is
not required. The source ADR must describe the assigned phase and the review must verify that
assignment. This does not close the condition or prove execution. The register alone cannot
authorize moving an unresolved decision to a later phase. Ordinary already-deferred feature policy
needs no invented ADR.
Architecture closure requires at least one successful executed compatibility receipt, including
its bound recipe and both stream hashes. A recipe must contain the exact versions/source identities
and observable compatibility assertions; structural/Draft resolution tests or business fixtures
alone are insufficient. Receipts prove what the recipe executed, not untested feature behavior.
Accepted ADR metadata alone never counts as executed compatibility proof.
Receipts also bind the current decision register and selected composition/pins, normalizing only
selection approval metadata. Changed package selection requires fresh compatibility evidence.

`docs/architecture/bootstrap-acceptance-scope.json` has schema_version `1.0` and a `decisions`
object keyed by every founding decision plus any additional explicitly reviewed catalog decisions.
Each value has `elements` and `relationships` arrays of exact IDs. Every included item must cite
that decision in decision_refs. An empty array accepts no semantics of that kind. Acceptance
promotes only listed semantics and Proposed decisions in this scope, preserving unrelated proposals.
Three narrative documents receive marked deterministic lifecycle views; authors must not duplicate
transient current status claims outside those views. Original proposal history remains dated history.
The constitution has separate authority; new drafts must not bake temporary drafting prose into
ratified content. Correct an existing ratified document only through its amendment procedure.

For a Ready entry whose Scope names a canonical candidate slice, its mapped journey
relationships and endpoints must be Accepted or explicitly covered by the pending
architecture review. Closed mechanism proofs cannot substitute for that scope.
Unrelated future proposals do not block the entry. Keep canonical candidate IDs in
roadmap Scope so this dependency check can use the existing map without guessing.
The validator checks the candidate's primary `journey` and optional `supporting_journeys`;
it does not infer additional journeys from prose or replace the separate decomposition/coverage
review. A cohesive slice may cover several journeys without creating artificial separate candidates.

Current lifecycle facts have one owner: the decision catalog for decision status,
the prerequisite ledger and verified receipts for closure, and the roadmap for entry
status. ADR bodies are decision reasoning and proposal-time history, not another
lifecycle state store. Routine approval or proof completion never requires ADR
supersession. A substantive replacement of accepted design still requires the
existing reviewed `supersedes` relationship. Before acceptance, closure resolves
substantive conflicts through source-bound owned questions and prerequisites.
Native fresh and recovery flows call `governance_state.py render-readiness` after
approval; no final agent reinterprets narrative state. The generated report names
the first handoff and retains deferrals at their recorded triggers.

Readiness begins at byte zero with exactly one status line and a newline:
`**Status**: READY`, `**Status**: CONDITIONALLY READY`, or `**Status**: NOT READY`.
Missing, malformed and BOM-prefixed statuses are invalid artifacts. Non-ready reports contain one
or more actionable lines: `- Blocker: <id> | Owner: <owner> | Next: <action>`.
READY cannot contain unresolved blocker lines. The 3072-byte target is advisory after generation;
4096 bytes is the hard readiness budget. Preserve decisive evidence even when the target is exceeded.

`governance_state.py evaluate-readiness` and the readiness terminal batch exit 0 for a valid
assessment, with `status`, `assessment_valid`, `authority_valid`, `eligible` and `blockers` JSON.
Exit 0 is not completion eligibility. Missing/stale authority is included as a named blocker in a
non-ready assessment. A purported READY assessment with invalid authority fails validation.
`require-readiness` exits 2 for a valid non-ready result; malformed artifacts exit 1 (the context
wrapper exits 2 for its invalid-output contract). `complete-bootstrap` retains independent authority
and exact READY checks. The workflow fails resumably before completion, never at an abort-only gate.

Use the supported `workflow_lifecycle.py resume --run-id <existing-id>` workflow entrypoint;
see [workflow-resumption.md](workflow-resumption.md). The engine owns producers, review gates,
eligibility and successful terminal state. Accepted readiness failures use a linked native
continuation that preserves the historical source. Failed earlier stages rerun the affected
producer with invalidated downstream step results. Technical abort-only history is not semantic
rejection. Internal artifact helpers preserve evidence, but their success or an independent
completion file does not establish workflow success. Completion must bind a completed engine run.


## Executed compatibility cases

Every Python recipe has an adjacent `<recipe-stem>.contract.json` with `schemaVersion: 1`,
`result` (a scratch-relative JUnit XML path; default `compatibility-results.xml`) and `checks`.
Each check names `id`, `kind` and distinct `testCases` using exact `classname.name` identities.
At least one check is `runtime-compatibility`; availability or restore alone is insufficient.
The recipe must perform the assertions before reporting passing cases. A successful process
without the required actual cases is recorded as failed proof, retaining its original process
exit code, streams and diagnostic. Failed/skipped cases block acceptance even if the process
returned zero. The compatibility receipt retains the result file and binds the contract,
recipe, selected design and streams. Existing receipts without named cases remain historical
evidence and need renewed proof before satisfying the new closure requirement.

Example contract for a real selected provider write/read probe:

```json
{"schemaVersion":1,"result":"compatibility-results.xml","checks":[
  {"id":"provider-roundtrip","kind":"runtime-compatibility","testCases":["Provider.write_read"]}
]}
```

This establishes only the tested compatibility claim. Feature domain behavior and complete
component adoption still need their own delivery evidence.


A contract may declare `fixtures`, mapping scratch-relative filenames to repository-owned source
files, and `dependencyTargets`, listing the fixture csproj/package.json files to restore. Setup
copies exact candidate toolchain/source configuration into the fresh scratch workspace, then uses
repository sync's toolchain resolver and the building-block dependency executor for renew and
locked verification. Recipe sources and fixture inputs remain hash-bound. Product targets are not
created by this work. During live acceptance the worker submits a bounded request; the supervisor
uses a frozen installed tool snapshot and preserves redacted restore streams. Failed provisioning
stops the phase. Registry credentials never enter the paid worker environment. Reviewed toolchain
overrides that need a different scratch configuration require the corresponding explicit handoff;
the helper must not silently select a different version.


## Native execution handoff

The closure producer writes `bootstrap-proof-plan.json` with `schemaVersion: 1`, `probes`
(`id`, repository-relative `recipe`, bounded `timeout`) and `readyWhenProven` (`id`, exact
complete architecture `prerequisites`, `rationale`). It leaves blockers open. The following
native shell step runs `bootstrap_proof_plan.py`; no coding agent is dispatched for restore
or execution. It attaches passing receipts, closes only those dependencies and applies only
explicitly prepared conditional Ready transitions. A failed probe stops the workflow with its
receipt preserved. Explicit recovery reuses current successful proofs and renews failed work.
An empty plan explicitly records that no scratch proof is required. Final approval reviews
scope, dispositions and evidence after execution; it never substitutes for a failed probe.

For a selected first slice, closure validation requires every open architecture prerequisite to
have a probe and a complete conditional Ready transition, unless the entry is already Ready.
An empty `readyWhenProven` array with a Blocked first entry is incomplete closure planning, even
when all listed toolchain recipes are valid. Resolve it before executing any probes. Future slices
may retain their scoped blockers. The closure output budget includes its roadmap edits.

After a compatibility failure has been repaired and every planned proof has current passing
evidence, the owner may use `workflow_lifecycle.py resume --run-id <id> --reuse-proven-closure`.
This checks current design, source, contract, tooling and executed-case bindings before retaining
the closure producer's output. It resumes at the native proof shell, preserving downstream
validation and human review. Open, failed, stale or differently planned proofs reject reuse;
ordinary resume still returns to the owning authoring stage when repair requires new design work.

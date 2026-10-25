# Retained prerequisite and proof evidence

The founding workflow and its closure/recovery stages are retired. The supported route is
[product founding](product-founding.md), followed directly by feature intake. Neither a ledger,
proof plan nor runtime compatibility run is mandatory merely to specify a product. Preserve
existing ledger/receipt bytes and their actual obligations; unfinished history is never completed
by installing a skill. Run focused experiments before specification only when their answers change
what should be specified. Actual restore, native/provider/runtime and implementation checks remain
due at their dependent actions.

The following describes retained evidence formats for ordinary phase obligations and historical
audits, not an instruction to recreate an old workflow dossier. Source-bound conditions retain
owners, actual triggers and honest evidence. Existing compatibility failures remain failures.

`docs/architecture/bootstrap-prerequisites.json` has schema_version `1.0`, `sources` and
`prerequisites` arrays. It is part of the reviewed and hash-bound bootstrap artifact bundle.
Source entries have `path`, `sha256` and `prerequisites` (condition IDs). Inventory the complete
approved decision register and every cataloged ADR, including conditions retained in Accepted ADRs.
`bootstrap_lifecycle.py source-hashes` computes these hashes, normalizing only Proposed/Accepted
status metadata so approval cannot silently discharge a future condition. Any substantive source
change requires re-inventory and renewed review. Empty conditions are an explicit reviewed assertion.

Each prerequisite has these fields, with optional `verification` (`compatibility` or `decision`). Architecture and delivery items default to compatibility; explicit decision obligations close with source-bound decision evidence:

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
For an epic with several features, optionally add `affected_features: ["feature-id", ...]` to
restrict the condition to exact named children. Keep their parent epic in `affected_slices`.
Each child must have explicit canonical `epic` membership or a durable v2 intake proving that parent;
unknown, unparented or mismatched IDs reject. Omit `affected_features` for a truly shared epic-wide
condition, preserving historical behavior. A renewal-specific condition must not block independent
policy maintenance simply because both belong to the same epic. Without a selected feature,
eligibility reports a conservative aggregate; it does not waive child conditions.
Architecture/before-implementation items gate affected implementation, not specification. Architecture/before-specification items gate specification. Legacy before-bootstrap-completion obligations conservatively gate specification; do not silently waive them.
Feature/feature-plan items identify ordinary specification/planning decisions inside accepted
boundaries. Later/production and later/later-release items retain later policy triggers. Their
classification, rationale and source-condition inventory require the same review as architecture.
Do not relabel a shared provider dependency as feature-owned to bypass it.

Split "plan and execute" conditions into two source-linked obligations. For example:

| Work | Disposition / trigger | Verification |
| --- | --- | --- |
| Decide device coverage and test cases | feature / feature-plan | decision |
| Execute device/accessibility cases on the implemented feature | feature / delivery | compatibility |
| Define application activation/restart tests | feature / feature-plan | decision |
| Run those tests against the actual release bundle | feature / delivery | compatibility |

Use `verification: decision` for feature-plan and `verification: compatibility` for delivery.
An explicitly typed consumer release-policy decision can still be deferred to delivery; it is not
execution evidence. Do not put an actual test or device result in that decision category.
Here compatibility means the existing source-bound executed-test receipt, also usable for
consumer-specific delivery recipes; it is not restricted to a generic bootstrap smoke test.
Its named tests, inputs, streams and selected design must match. Device verification may require
human-operated equipment; a script or interview must never manufacture that evidence.
Keep delivery prerequisites open and deferred at delivery during specification intake. They do
not block specification, planning or implementation, and an answer/default never closes them.
At delivery run the existing `bootstrap_lifecycle.py proof --id <prerequisite> --recipe <reviewed-recipe>`
against exact consumer inputs. Phase eligibility validates the latest retained native attempt;
failure, missing results or changed inputs do not reuse an older success. A passing current receipt
satisfies the execution gate without rewriting the approved bootstrap ledger or reconfirming an
interview just to say a test passed. The feature's normal verification gates still apply.
Do not put "perform device tests" or "execute the application" in a planning decision. A real
external feasibility concern remains an architecture/before-implementation compatibility obligation.

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
Closing a compatibility prerequisite requires at least one successful executed compatibility receipt, including
its bound recipe and both stream hashes. A recipe must contain the exact versions/source identities
and observable compatibility assertions; structural/Draft resolution tests or business fixtures
alone are insufficient. Receipts prove what the recipe executed, not untested feature behavior.
Accepted ADR metadata alone never counts as executed compatibility proof.
For architecture-disposition conditions, the aggregate `bootstrap_proof_plan.py` executor can
attach the latest passing standalone native receipt for its exact planned recipe without
rerunning it. It preserves Active/Delivered status and promotes only Blocked/Candidate entries.
After bootstrap completion, use the explicit reviewed post-bootstrap continuation in
the scoped decision owner to close a genuinely satisfied obligation with actual evidence.
Do not hand-close the approved ledger, relabel the obligation, or refresh approval hashes.
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

Saved engine records may be inspected read-only. The retired workflow cannot resume, reopen or
claim completion; use product-intake to review useful current artifacts explicitly.

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

For .NET targets, managed setup also writes version 1 standalone `Directory.Build.props`
and `Directory.Build.targets` at the scratch root before any SDK evaluation. This stops upward
consumer build imports and preserves explicit fixture package versions; setting an import flag
inside an SDK project body is too late. Application analyzer/build policy remains in force for
application projects. A conflicting fixture-authored boundary requires a distinct reviewed pickup,
which preserves its original bytes and aligns only the new draft with managed scratch setup.

Fixtures contain only inputs actually consumed at runtime. Do not copy cataloged ADRs into
fixtures: their Proposed-to-Accepted promotion changes raw bytes at approval. Preflight rejects
these declarations before restore/execution. Preserve ADR authority through the canonical
prerequisite source ledger and decision evidence, which normalize only approval metadata and
still reject substantive changes. Put any executable parameters in a separate bound fixture;
do not remove source obligations or relax stream/recipe hashes to make acceptance pass.


## Current execution boundary

Compatibility recipes remain focused tools for concrete provider/runtime questions and ordinary
engineering obligations. Do not invoke an old closure/recovery stage or workflow to run them.
A successful receipt proves only its recorded inputs and assertions. A status/hash or accepted
ADR never proves runtime compatibility, implementation completion or human consent.

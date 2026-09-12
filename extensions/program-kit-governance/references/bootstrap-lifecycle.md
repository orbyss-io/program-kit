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

Closed items require evidence entries with `path`, `sha256`, `kind` (`compatibility` or `decision`).
Decision evidence uses the same normalized source hash from `source-hashes`; compatibility
receipts use their raw file SHA-256. Disposition of an unresolved assessment item or ADR condition
as feature/later work requires a cataloged decision as explicit authority, Proposed only during
review and Accepted at readiness. Ordinary already-deferred feature policy needs no invented ADR.
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

For an already-aborted technical completion failure, use `bootstrap_recovery.py prepare --run-id
<existing-id>`. It validates the abort-only signature and existing approval hashes, freezes the
original run/artifacts, and writes a handoff without editing state.json or launching any agent.
The same command supports fresh failed readiness steps after approval. Semantic rejection and
running or completed workflows are refused. `review`, `accept`, `evaluate`, `complete` implement
the bounded recovery sequence. Only a reviewed replacement architecture bundle receives renewed
approval; intake, assessment and ratification remain unchanged. Original failure evidence is never
reclassified as a human semantic rejection. Recovery completion links to the unchanged original run.

---
description: Create the governed project-level portfolio of candidate feature specifications.
scripts:
  py: scripts/governance_state.py
---

Read the supplied brief with `python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py read-brief --stage roadmap --run-id <run> --page 1`, then each indicated next page in a separate tool response. Read all pages; this is lossless paging, not a summary. For sizing, follow `output_contract.budget_basis`: use its advisory sizing command once after drafting, not ad hoc whole-file byte assertions. Authored limits exclude only verified generated views; preserve their complete content. Do not combine brief, skill and reference dumps in one response or reread already received pages.


## Preconditions

`$ARGUMENTS` identifies the confirmed intake and the workflow-generated bootstrap context path.
Read the compact bootstrap stage brief first. It contains confirmed journeys, candidate slice
signals, the canonical architecture map, and compact ratified
authority records, and a link to a separate hash-bound evidence index. Read the ratified
constitution in full. Do not print or read the evidence index in full; query one artifact and
heading range only when the brief lacks a fact required to define an entry. Do not bulk-read every
unchanged bootstrap artifact, search other artifact directories, or enumerate installed files.
Use `governance.paths` and the exact writes and validation command in `output_contract`. The roadmap
field contract is stated below. Do not search `.specify` or inspect `governance_state.py` to
rediscover either contract; run the supplied validator and respond only to a specific diagnostic.
Use `output_contract.artifact_target_bytes` as the initial generation target and
`output_contract.artifact_byte_budgets` as the hard boundary after every write, including edits to
existing files.
Use `stage_plan.entry_template` for the exact parser syntax and `stage_plan.prerequisite_scope`
to assign every retained condition to real roadmap IDs in bootstrap-prerequisites.json. Preserve
source bindings, ownership and due phases. A before-implementation proof does not make an otherwise
specifiable entry Blocked. Dependencies name/link ledger IDs, never repeat their open/closed status.
Use links to ADR metadata for acceptance state. The generated views own changing status.

Validate the ratified constitution before doing any work:

```text
{SCRIPT} validate
```

Use the validated context to cover the architecture baseline, ADRs, decision backlog, tooling
evaluation, quality system, traceability model, and candidate vertical slices. Stop if ratification
is missing or stale.

Use the compact approved decision and Accepted baseline records from the stage brief. Open a source
only for a decisive field omitted from that projection. Explicit intake choices and adopted Program
Kit defaults do not appear as unresolved ADR prerequisites.
Genuinely unresolved decisions gate only their affected slice and due phase. Ready means specification-ready, not implementation-ready. Deferred
production, scale, retention, recovery, or long-running-operation choices do not block an unrelated
first vertical slice before their named trigger.

## Output

Create or update `docs/architecture/specification-roadmap.md`. This is a portfolio—the specification
of candidate specifications—not an implementable feature specification and never an input to
`speckit.implement`.

For a single confirmed journey, keep the first complete roadmap draft at most 550 words and aim
below 4,500 UTF-8 bytes. Do not repeatedly measure or trim toward the target; run the supplied
terminal validation batch after the write and repair only a named diagnostic.

This file is the sole authoritative source for roadmap-entry lifecycle status. After writing it,
update `docs/architecture/architecture.md` and `docs/architecture/traceability.md` so they contain no
copied status fields or tables for roadmap entries and no stale claims that a roadmap record does not
yet exist. Preserve their design, decision, ownership, and verification traceability. Do not write or
edit the marked `PROGRAM-KIT:ROADMAP-VIEW` section; the deterministic synchronization step owns it.
The terminal validation batch runs that existing synchronization before closure context is built,
refreshes the two documents' canonical hashes and DSL, and checks consistency and final byte budgets.
Do not refresh hashes by hand or run an additional synchronization command after the batch.
Make the smallest link-only edits needed outside the new roadmap, do not restate roadmap fields, and
use the supplied sizing command to check each edited file against `output_contract.artifact_byte_budgets`; it reports authored, generated and total bytes separately.

For each record use the heading `### <ID>: <Title>` and include exactly these list-item forms, with
the colon outside the bold label (for example `- **User-visible outcome**: ...`):

- **User-visible outcome**
- **Scope**
- **Non-goals**
- **Required Accepted ADRs**
- **Dependencies**
- **Owned public contracts**
- **Owned lifecycle portions**
- **Owned data**
- **Quality scenarios**
- **Verification responsibility**
- **Recommended sequence**
- **Status**

Statuses are `Candidate`, `Blocked`, `Ready`, `Active`, `Delivered`, and `Superseded`. Bootstrap may
create Candidate, Blocked, and Ready records. `Ready` means ready to write the feature specification,
Planning, implementation and delivery have separate phase eligibility checks against the same prerequisite ledger. It does not mean every field-level, data-model, business-rule, failure,
or implementation choice was decided during architecture bootstrap.

Put only architecture-significant decisions needed to specify this journey in `Required Accepted ADRs`. Retain later architecture choices in the prerequisite ledger with their actual due phase. Use `None` or a
semicolon-separated list of exact existing ADR identifiers; wrap non-`ADR-*` identifiers in
backticks. The Proposed founding ADRs named by the stage brief are bound to this same bootstrap
review and will be promoted atomically before readiness, so they may be listed without making the
record Blocked. Never invent a future ADR merely to move authorization rules, submission lifecycle,
persistence, consistency, retention, retry, idempotency, or other feature-owned design out of the
vertical slice. A decision-backlog item whose named closing artifact is the feature specification,
feature contract, or feature tests belongs in Scope, Owned lifecycle portions, Owned data, Quality
scenarios, or Verification responsibility and does not block specification readiness. Require a
separate design task or ADR only when the evidence identifies an unresolved architecture choice
outside the slice that changes an accepted boundary, shared store, cross-domain/public contract,
security profile, or deployment topology.

A record is Ready when its outcome, boundary and ownership are sufficient for specification and
its specification-due decisions are resolved. `before-implementation` obligations do not prohibit
Ready or Active: they prohibit dependent implementation. Candidate or Blocked entries may remain
after bootstrap, even when no entry is Ready. Never invent a journey start/end or provider choice
to obtain completion. The final report identifies which phase can proceed for each slice.
Use architecture-map journey `discovery` IDs for unclear boundaries, retaining Proposed status,
empty steps/view and a Candidate roadmap entry with owned `before-specification` obligations.

Design tasks remain separate. They produce evidence, alternatives, Proposed ADRs, updated views, and
unlocked roadmap entries; they are not feature specifications or application implementation work.

After writing the roadmap, run the single command in `output_contract.validation_commands`. It
batches the output-budget and roadmap-governance checks. Repair only a named diagnostic and rerun
that same batch once. After it passes, stop immediately: do not inspect a diff, remeasure files,
read another source, or run another command.

Before that terminal batch, inventory `docs/architecture/bootstrap-prerequisites.json` using
the installed `references/bootstrap-lifecycle.md` contract. It binds all unresolved/deferred
assessment items and retained ADR conditions to exact affected entries, owners, triggers and
closure evidence. Program Kit owns IDs and paths. Read the full roadmap including its preamble;
never redefine Ready as specification-ready or place a global before-code gate outside records.

For a retained ADR condition assigned to feature/later work, bind that cataloged ADR in `sources`
with the exact condition ID. This is phase-assignment authority, not closure evidence: leave the
condition open until its own gate. Cover compound slices through their declared primary and
`supporting_journeys` IDs, never narrative-only claims.
Keep open architecture dependencies Blocked. The subsequent bootstrap-closure command executes
bounded compatibility tasks and reconciles eligibility before final review. An all-Blocked draft
is a valid portfolio assessment and does not authorize implementation or bootstrap completion.

Do not promote a record merely to make bootstrap pass. Keep a record `Candidate` or `Blocked` when
an architecture-significant prerequisite outside the feature slice is unresolved. Do not block it
on decisions the feature specification and plan are supposed to make. The later synchronization
step only copies the status already justified here; it never chooses or promotes a status.

Report blocked records and the exact design task or ADR that can unlock each one.

The approved `first_slice.journey_ids` is one selected specification boundary. Create exactly
one first entry whose Scope includes every canonical candidate ID projected in
`stage_plan.first_entry.candidate_ids`, and no candidate for a future journey. If this boundary
contains several supporting journeys, describe them in that one entry; four separate entries
plus prose saying they share a specification do not satisfy the handoff. Do not enlarge or shrink
the approved boundary. Create separate portfolio entries for the remaining user-visible journeys.
Without a structured first_slice, start with one entry per journey unless accepted architecture
requires another boundary. Reuse the compact authority and normalized brief rather than reconstructing the
design from every downstream document. Report entry IDs, statuses, final byte counts, and validation
counts only; do
not print the complete roadmap or repository-wide diffs.

For `ui-experience-v1`, the first slice renders the consumer's brand, layout and a real user outcome.
Login/logout supports that journey when needed; inherited authentication correctness is Program Kit
contract evidence, not a substitute first product slice. Include page intent and initial metadata
where public discovery matters, and verify the accepted framework adapter against the UI contract.

For authorization journeys, distinguish a bodyless/no-effect access probe from a protected business
effect. The former is Ready with managed endpoint `permission:<identity>` policy evidence and must
not invent an inner service; the latter also owns a resource/state/effect authorization rule.

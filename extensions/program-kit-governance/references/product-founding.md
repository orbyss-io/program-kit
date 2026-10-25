# Focused product founding

The product-intake skill owns the connected conversation and draft. These focused owners validate
actual artifacts and exact decisions; no workflow completion, authoring worker or stage dossier is
required. Paths below are relative to the initialized consumer root.

## Current product and architecture

Use `intake_authoring.py describe` for unfamiliar records and `build-draft --source
 docs/architecture/intake-authoring.json` after writing the settled product-intent record. Then run
`bootstrap_intake.py validate-draft --json`. After explicit confirmation of the synthesis, change
only its status to confirmed and run `bootstrap_intake.py validate --json`.

The canonical map owns domain/context/module meaning, sources, journeys, decision references,
capability ownership and candidate feature seeds. The DSL is a generated C4 review projection.
`architecture_map.py validate --map docs/architecture/architecture-map.json` checks actual model
and reference integrity. `view-c4` offers safe local viewing. No whole-library knowledge projection,
all-pages ceremony or architecture worker brief is required.

## Constitution and consequential decisions

Use the ordinary constitution command and its hooks. Their focused CLI equivalents are:

```text
python .specify/extensions/program-kit-governance/scripts/governance_state.py begin
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-constitution-draft
python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage constitution
```

After presenting the exact constitution review and receiving explicit human ratification:

```text
python .specify/extensions/program-kit-governance/scripts/governance_state.py ratify --verdict ratify
```

Each consequential founding candidate becomes a real Proposed ADR in the canonical catalog with
its original candidate ID and `- **Founding decision candidate**: <id>` marker. Use canonical ADR
status metadata (`- **Status**: Proposed`), genuine alternatives, rationale and consequences. Keep
future options provisional. Intake confirmation is separate from ratification and ADR acceptance.

By default the accepted map scope is precisely each founding candidate's affected elements and
relationships. If an additional consequential decision is ready for acceptance, explicitly name
it in the existing `docs/architecture/bootstrap-acceptance-scope.json` schema 1.0:

```json
{"schema_version":"1.0","decisions":{"founding-example":{"elements":["example-context"],"relationships":[]}}}
```

Include every founding candidate; additional keys must be cataloged decision IDs. Every scoped
map item explicitly references the relevant decision ID. A separately Proposed decision outside
this scope stays Proposed. No automatic acceptance of all ADRs is permitted. Scope is about reviewed
meaning, not proof that runtime conditions executed.

## Technology and qualified capabilities

Keep prose rationale and adopted/provisional/rejected tools in technology-radar.md. The existing
bootstrap-decisions.json is the machine-readable configuration for focused setup consumers:
`selected_profiles`, `choices`, applicable `web`, `dotnet`, `identity`, `persistence`, `toolchain`,
`overrides`, and disclosures in `acknowledgements`. It does not require assessment approval,
research reports or decision-backlog artifacts. Supply explicit choices/overrides, then run:

```text
python .specify/extensions/program-kit-governance/scripts/product_intake.py defaults
```

This resolves missing supported defaults using installed qualified profiles and pin sources. Read
and disclose the consequences. It does not install dependencies, qualify a new profile or grant
provider/account authority. Existing approvals cannot be silently rewritten. Changed accepted
choices require review through their existing decision owners before a fresh baseline review.

For managed capabilities use building_blocks.py draft, validate-draft and its qualification and
placement contracts. Consumer meaning remains consumer-owned. Use exact planned target identities
for missing greenfield files; actual native/resource composition and materialization belong to
planning/setup. Selection acceptance resolves the qualified catalog and Accepted decision refs;
it does not prove runtime interoperability. Existing accepted locks remain preserved.

## One review and direct feature handoff

Keep outcome epics and candidate feature seeds in specification-roadmap.md, using its existing
record fields. Candidates need not be Ready. Do not require a proven first runtime slice before
specifying that slice. Run these focused operations:

```text
python .specify/extensions/program-kit-governance/scripts/product_intake.py review
```

Show the exact artifacts listed in reviews/bootstrap-review.md, the named ADR/map scope, choices
and provenance, remaining assumptions/questions with owners and triggers, and recommended first
outcome. Only after explicit human acceptance:

```text
python .specify/extensions/program-kit-governance/scripts/product_intake.py accept --verdict approve
python .specify/extensions/program-kit-governance/scripts/product_intake.py validate
```

The existing bootstrap-approval.json binds reviewed bytes and allowed status promotion; it is not
an engine completion receipt. Acceptance promotes exact scoped ADR/map metadata and a qualified
Draft selection transactionally. It never marks old workflows complete. A changed review/decision,
configuration or selection fails instead of acquiring authority by retaining an Accepted label.

Continue directly to specification-intake in the same session. Feature intake may begin from an
existing Candidate/non-Ready epic or a new selected feature. Preserve supplied feature seeds and
carry relevant due questions from intent/ADRs into the actual feature. `phase_obligations.py`,
repository_sync.py, composition and native engineering validators own actual downstream actions.
Later feature additions do not require founding completion or blanket reacceptance. Setup retains
exact settled founding ADR/config authority while feature/map/roadmap evolve under their owners.

## Existing consumers and historical evidence

Upgrade removes owned workflow installation/registration while preserving saved runs, old proof
bytes, accepted artifacts and consumer locks. A customized owned workflow must be reconciled by
its owner, not erased. Newly upgraded retired launch/resume commands give a diagnostic pointing
to product-intake. Preserve incomplete old runs as incomplete; explicitly review useful existing
artifacts with the skill. No automatic consumer restart, migration to completion or new worker is
implied. Read-only historical completion validation remains available for auditing old evidence.

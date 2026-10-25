---
description: Understand or resume a product, record human decisions in readable documents, and continue directly to native feature specification.
---

# Product intake

Use this skill from a rough idea through a thoroughly designed application. Reuse supplied design,
existing architecture files and settled answers. Treat 0.x documents as useful inputs to deliberate
re-onboarding, never converted workflow authority. Resume from current intent, consequential ADRs,
constitution, roadmap and the current unanswered frontier rather than replaying old stage briefs.

## Understand and challenge

Read references/intake-method.md, references/functional-discovery.md and the shipped grilling skill
as relevant. Investigate business meaning and consequential external facts. Establish purpose,
actors, success, real journeys and important domain concepts, entities, roles, lifecycles, policies,
invariants, ownership and trust. Use concrete examples to expose contradictions. Ask consequential
questions in dependency order; do not repeat answers or frontload exhaustive future design.
Deepen future behavior vertically when its feature is selected.

Distinguish explicit human decisions, disclosed defaults, researched conclusions, proposals and
unknowns. Preserve their rationale and sources. Curated technology/capability knowledge is a
convenient researched default. The consumer can select another language, stack or pattern; research
its actual contracts and state automation limits without requiring consumer qualification receipts.
Tools never choose consumer business policies or taste.

## Preserve connected intent

Use a few ordinary authored files, proportional to the actual product:

- docs/architecture/project-intent.md: purpose, journeys, scope/non-goals, settled decisions with
  provenance, relevant domain meaning, assumptions, unanswered questions with owner/trigger and next action.
- .specify/memory/constitution.md: substantive principles, testing/review policy and amendment process.
  Use native speckit.constitution when helpful. Ratification is an explicit human decision in this document.
- consequential ADRs: alternatives, rationale, consequences and individual Proposed/Accepted/etc status.
- a small language-neutral docs/architecture/architecture-map.json for domain/C4 identities and relations.
  Use references/architecture-map-minimal.json as a starting example and architecture-map-v2.schema.json.
  Keep optional domain detail readable and add it only when useful. Architecture documents and local
  alternatives remain valid; do not create a map merely to unlock another phase.
- technology choices and outcome roadmap, in the intent or separate short documents when useful.
  Use qualified Foundation capabilities/shells when selected; explain planned ownership and actual
  helper limitations. An independent stack requires its own real checks, not Program Kit qualification.

No assessment, acceptance-scope file, authoring JSON, review packet, confirmation receipt, hash basis,
workflow completion, backlog dossier or installed runtime proof is required for intake. Optional
architecture_map.py validate/export checks actual map shape and relationships; product_intake.py
inspect reports present context. Neither records acceptance. Read references/product-founding.md
for focused helper commands. Existing locks and published dependency knowledge retain their owners.

## Confirm meaning and continue

Present the connected understanding, consequential choices and alternatives, disclosed defaults,
assumptions, unresolved frontier and recommended first useful outcome. Obtain explicit human
confirmation of product meaning and record the actual answer/context in project-intent.md.
Constitution ratification and each Accepted ADR are distinct decisions: obtain and record those
actually settled, preserving other proposals. Silence, generated files and successful checks are
not consent. Reopen substantive changed meaning; formatting and unrelated additions do not
revoke a human decision. A simulated proxy supplies no human acceptance.

Continue directly to speckit.program-kit-governance.specification-intake for the selected feature,
then ordinary native speckit.specify/clarify/plan/tasks/implement. No roadmap ID or Ready status is
an eligibility gate. Carry relevant questions into that feature's normal spec/plan; irrelevant
future detail stays deferred. Run environment, restore, provider or application checks only when
the actual action needs them. A pre-spec experiment is justified only when its answer changes
what should be specified. Preserve failures and evidence limits honestly.

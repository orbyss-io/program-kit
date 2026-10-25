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

Before asking for confirmation, present a **Review overview** with direct links to the actual
documents and a readable walkthrough of each applicable item:

- Product purpose, scope, actors and end-to-end user journeys.
- The outcome roadmap: priorities, dependencies, first useful release/feature and deferred work.
- The domain map: boundaries/owners, important entities, roles, lifecycles, policies and relationships.
- C4 system-context and container views, plus every additional view actually modeled. Show the
  diagrams and explain their boundaries and connections; a raw JSON/DSL file link alone is not a
  walkthrough. Use readable inline diagrams or the supported local view-c4 command. Missing viewer
  prerequisites must not silently erase review: explain the limitation and show a readable diagram
  alternative or obtain an explicit deferral. Never upload private models to an external viewer.
- Technology choices, disclosed defaults/overrides and relevant environment/provider composition.
- Constitution principles and ratification, and consequential ADRs with their individual statuses.
- Assumptions, unanswered questions, proposed deferrals and the recommended first specification.

Keep this proportional: use existing representations and views, do not invent deeper C4 levels,
new mandatory files or exhaustive future design. Reuse earlier substantive reviews and show what
changed. `product_intake.py review` can list available artifact links and review prompts; it cannot
establish that the human saw or approved them.

Explain exactly what product confirmation covers and which proposals/deferrals remain unsettled.
Then ask for the human's explicit decision and **pause before specification intake**. Do not start
the first feature in the same response that requests confirmation. A bare earlier "confirm" without
an inspectable review scope does not establish review of unseen architecture or roadmap: present
the missing overview and resolve its scope with the human. Record the actual answer/context in
project-intent.md; record an explicit decision to defer a view honestly rather than claiming review.
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

For .NET host/exporter choices, apply `principle.dotnet-host-default` in
references/tool-selection.md. Review a custom-host proposal against actual human opt-out,
keep unresolved choices visible, and resolve the effective profile before reading versioned
package knowledge. A proposal, helper pass or profile listing supplies no human acceptance.

For background/queued work or replaceable providers, consult references/asynchronous-workloads.md
before choosing shared contracts. Research the relevant source-map alternatives, explicit environment
closures and failure semantics; keep coordination, execution and exchange separate. Use only the
focused references needed by this journey. Synthetic tests do not qualify an actual platform.

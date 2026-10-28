# Focused product founding

The skill owns the conversation. Ordinary authored documents preserve meaning and actual human
decisions; optional helpers inspect only their supplied input. No founding lifecycle receipt exists.

## Current product and architecture

Accept rough ideas or existing architecture as inputs. Read product intent, relevant design,
constitution and ADRs. A small language-neutral domain/C4 map is the default when a map is useful;
copy architecture-map-minimal.json and adapt it. Its schema2.0 requires only identity, title,
elements and relationships. Add domain concepts, roles, lifecycle, policies, questions, ADR links
and views proportionally. Missing map fields never become an unrelated native phase gate.

Focused commands from the installed governance scripts directory:

```text
python product_intake.py inspect
python architecture_map.py validate --map docs/architecture/architecture-map.json --project-root . --verify-sources
python architecture_map.py export --map docs/architecture/architecture-map.json --output docs/architecture/workspace.dsl
```

Export refuses to overwrite unless --force is explicit. Validation checks actual IDs, parent
relationships, view scope and supplied ADR paths. C4 viewing checks the current generated
projection; it requires no intake confirmation record. Legacy detailed1.1 maps remain readable
inputs to their existing schema/export helpers, not converted approval authority.

When intake authored a canonical map, run validation and export before requesting the founding
review; the generated `workspace.dsl` is part of preparing that review, not an optional viewer
runtime installation. Link the actual DSL and offer **View C4** (Codex:
`$speckit-program-kit-governance-view-c4`) before the confirmation decision. The viewer is read-only
and cannot create a missing projection. Finish any chosen view request, then return to the pending
review. For an established generated projection, deliberately refresh with `--force` after checking
map changes; preserve authored DSL/local alternatives. Exporting requires no Docker/Java, browser,
ratification or architecture approval. Missing viewer runtime still permits readable diagrams or
an explicit scoped deferral; do not silently hide the local viewing option.

## Constitution and consequential decisions

Author a durable decision-guiding agreement for later specifications, architecture, implementation
and review. A product identity, feature list or set of aspirations is not enough. Keep the agreement
small enough to use: each material principle states its obligation or invariant, rationale,
applicability and a concrete way to examine compliance. Explain which later decision the rule
would change or reject; a heading such as "quality" or "SOLID" alone supplies no decision rule.

Choose principles for the actual product and its risks, rather than filling a fixed principle count:

- Define domain and dependency boundaries, ownership of data and effects, and the contracts through
  which independent owners collaborate. Keep business meaning independent of transport and providers
  where that boundary is applicable; explain any deliberately accepted alternative.
- Prefer simple, composable designs and the selected framework's maintained capabilities before
  replacing them. State the responsibility an abstraction or replacement must justify. Keep dependency
  resolution at composition boundaries; make configuration admission, service lifetimes, disposal and
  side-effect ownership explicit where relevant. This is no blanket ban on factories/delegates, no
  interface-per-class rule and no requirement to put every configuration value behind IOptions.
- Address consequential correctness, security/privacy, effects and failure semantics, operability,
  compatibility and evolution. Use relevant quality scenarios: the triggering condition, required
  response and how it will be checked. State measurable limits when actually agreed or researched;
  do not invent SLOs, compliance obligations or production guarantees to make a template look complete.
- Define proportional verification and review: inspect changed source responsibilities, use the
  cheapest reliable behavioral/contract checks, and exercise real boundaries where substitutes cannot
  prove them. Do not mandate universal TDD, a full browser matrix or supplier requalification for every
  change. Preserve the product's agreed human review boundaries.
- Explain how consequential exceptions are justified, owned, bounded and revisited through ordinary
  plans/ADRs and human review. Preserve explicit amendment authority and prior decisions. Do not create
  another approval receipt, scoring system or workflow gate.

Keep product identity, roadmap priorities, feature/UI details and unsettled operational defaults in
intent/specification documents. Exact stack/package versions and local design alternatives belong
in their owning ADR/profile decisions. A constitution can state a durable technology constraint when
that is the actual agreed principle; it should not duplicate the dependency lock or feature backlog.

Synthetic comparison: "Build a modern reporting app with a dashboard and export" describes a product
brief. "Domain contracts must not reference transport or persistence implementations, so business
rules can evolve independently. Check compiled dependency direction and representative domain tests;
record consequential exceptions with rationale, owner and review trigger in the existing ADR process"
is a reviewable principle. This example supplies neither a compulsory architecture nor a semantic
certificate for another document. Walk through the actual draft and challenge vague or inapplicable
rules with the human.

These criteria follow [Spec Kit's guiding-principle role for the constitution](https://github.github.com/spec-kit/reference/agentic-sdd.html)
and its [illustrative principles/constraints/governance template](https://github.com/github/spec-kit/blob/main/templates/constitution-template.md),
with [SEI quality-attribute scenario reasoning](https://www.sei.cmu.edu/library/reasoning-about-software-quality-attributes/).
[ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) concerns architecture descriptions;
it does not prescribe a Program Kit constitution format. These sources establish no universal
principle inventory, mandatory TDD practice or claim of formal standards compliance.

Use ordinary native speckit.constitution or edit the constitution as requested. Present principles,
testing/review policy, amendment process and actual changes. Obtain explicit human ratification
and record its date/context in the constitution. No ratification JSON, review dossier or byte hash
is required. The optional governance_state.py validate-constitution-draft detects unfilled content;
its validate command inspects the document's readable **Status**: Ratified statement only when
that particular check is requested. It cannot independently prove consent.

Record actual consequential ADRs with alternatives, rationale, consequences and individual
Proposed/Accepted/Rejected/etc status. Human acceptance of product synthesis, constitution
ratification and named ADR decisions are distinct. Do not auto-accept every proposal or future
recommendation. Reopen substantive changed meaning, not representation-only edits.

## Technology and qualified capabilities

Defaults are researched starting points with disclosed rationale. Consumers may choose other
languages, tools and patterns. Research their real contracts and disclose automation limits;
there is no compulsory consumer qualification ceremony. Product business semantics remain owned
by the product. Optional managed Foundation selection/scaffolding helpers retain their actual
supported inputs, dependency locks, ownership and engineering checks. Unsupported automation is
not a reason to prohibit independent design or native Spec Kit delivery.

Selected repository setup may consume bootstrap-decisions.json for actual selected_profiles and
toolchain/provider configuration. That historical filename is an engineering input, not a founding
receipt. Do not create it for an unrelated stack or merely to start feature specification.

## One review and direct feature handoff

Use the product-intake skill's **Review overview** before requesting confirmation: linked product
meaning/journeys, outcome roadmap and sequence, domain boundaries/entities/lifecycles/policies,
C4 context/container and all other modeled views, technologies/environment defaults, constitution,
ADRs and unresolved decisions. Walk through the diagrams and roadmap; links to raw models alone
do not show their meaning. Use existing readable diagrams or the supported local viewer; missing
viewer prerequisites need a readable alternative or an explicit deferral, never an external upload.
Do not create extra diagrams or paperwork merely to fill a review list.

Explain the confirmation scope and then pause for the human's actual answer before first-feature
intake. An unscoped earlier "confirm" does not establish review of unseen documents. Preserve
earlier meaningful reviews, show substantive changes and record actual confirmations/deferrals in
project-intent.md. Product confirmation, constitution ratification and named ADR decisions stay
distinct. The optional `product_intake.py review` lists artifact links/prompts, never acceptance.
Make the closing question explicit: ask to confirm the synthesis, ratify the actual linked
constitution draft, and give a disposition for each named consequential ADR after walking through
their contents. Group them in one review round; an explicit answer can settle several presented
scopes together. Product confirmation alone does not ratify the constitution or accept unnamed
ADRs. Reuse earlier actual decisions, without asking again for unchanged meaning. Record actual
ratification as `**Status**: Ratified` plus decision date/context in the constitution, and each
ADR's actual status/rationale in its own document. Leave unanswered drafts/proposals unchanged.
Report the product, constitution, named ADR and unresolved/deferred dispositions separately before
handoff. If continuation reveals that a decision was never requested, show the missing material
and obtain/record that decision at this checkpoint; do not turn the omission into an unexplained
downstream approval error or require the human to restart intake. No new receipt or ledger is due.
Keep only relevant later questions with owners
and triggers; feature intake deepens their detail. No acceptance-scope JSON, authoring schema,
approval receipt or eligibility status is required.

Continue directly to specification-intake and ordinary native specify/clarify/plan/tasks/implement.
A missing or non-Ready roadmap entry does not block useful specification. Preserve agreed story
review pauses in normal plan/tasks/checklist notes. Actual environment, restore, provider and
runtime checks run only when the selected action depends on them.

## Existing consumers and historical evidence

0.x to1.0.0-preview.1 is deliberate re-onboarding. Bring useful existing documents into the new
conversation; do not convert old workflow hashes/statuses into current acceptance. Preserve
historical authored files, proof bytes, locks and user customizations. Future previews preserve
ongoing authored product/specification work subject to explicitly announced changes.

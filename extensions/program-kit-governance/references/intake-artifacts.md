# Intake artifact authoring contract

Use this contract when the conversation has converged. Read the worked
[authoring example](intake-authoring-example.json), then adapt its structure to the user's evidence;
its product and boundaries are illustrative, not defaults. Do not invent filler objects merely
because the example contains them.

## One authoring source

Write `docs/architecture/project-intent.md` and `docs/architecture/intake-authoring.json`.
The authoring JSON contains exactly `map` and `intake`:

- `map` owns the canonical strategic analysis, founding decisions, capability bindings, journey
  steps, and candidate slices. Use stable lowercase IDs everywhere, including the intent's Q&A
  evidence locators. Never invent a new evidence registry while projecting into the intake.
- `intake` holds the product summary, evidence registry, facts, scope, actors, choices, quality
  requirements, integrations, open items, and routing. Its `domain_analysis` contains only
  `boundary_challenges`; the builder derives the remaining fields from the map.
- `intake.capability_assessments` contains only `{ "id": ..., "need": ... }` records matching
  the map's binding assessment IDs. Binding order and shared fields are generated, not copied.
- Omit `intake.artifacts`. `status` defaults to `draft` and cannot request confirmation.
  Journeys and candidate-slice signals may be omitted to derive their statements from the map's
  actor/trigger and outcome; supply them explicitly when preserving exact source wording matters.
  Long statements are diagnosed, never silently truncated.
- Mechanical omissions shown in the example are filled: schema versions, empty metadata and
  decision references, module `parent` from its explicit `context`, dynamic relationship selection
  and order from journey steps, and the project-intent source record. Statuses and architectural
  ownership are not guessed. A bounded-context element needs an explicit application-system
  `parent` (not `properties.parent`). A decomposition view's scope is one bounded context.

For any unfamiliar nested record, get exact required fields, types, allowed values, and bounds:

`python .specify/extensions/program-kit-governance/scripts/intake_authoring.py describe --document map --section context_relationship`

`--document` is `map` or `intake`. `--section` accepts `root`, a top-level collection such as
`elements`, or a schema definition such as `subdomain`, `bounded_context`, `module`, `contract`,
`capability_binding`, `journey`, or `journey_step`. Use the section you need, not the whole schema.
Targeted schema inspection is allowed if the descriptor leaves a question; implementation browsing
is a last resort. Required JSON names and enum spellings must never be inferred from prose.

For an existing canonical JSON, report all structural errors in one read-only operation:

`python .specify/extensions/program-kit-governance/scripts/intake_authoring.py check --document map --input docs/architecture/architecture-map.json`

Structural diagnostics use zero-based JSON paths, missing/extra fields, enum values, and length
bounds. They supplement—not replace—the semantic and cross-artifact validators. Resolve structural
errors as a batch. Never discard affected element references, evidence, or architectural meaning
merely to get validation to pass.

The following sections describe generated output. Do not author its shared fields a second time.

## Bootstrap intake

The interview's compact Q&A and dependency record belongs in `project-intent.md`. Link its stable
evidence IDs from the existing intake collections; do not add an interview tree or transcript field
to either JSON contract. Keep default provenance distinct from explicit user answers and preserve
the rationale and consequences for final review.

`bootstrap-intake.json` has exactly these top-level fields:

`schema_version`, `status`, `project`, `artifacts`, `evidence`, `facts`, `scope`, `actors`,
`journeys`, `quality_requirements`, `integrations`, `choices`, `capability_assessments`,
`domain_analysis`, `open_items`, `candidate_slice_signals`, and `routing`.

- Use schema version `1.1`; status is `draft` before review and becomes `confirmed` only after
  explicit confirmation. Draft viewing does not perform that transition.
- `project` contains `name` and `summary`.
- `artifacts` contains `project_intent`, `architecture_map`, and `c4_projection`; each contains only
  repository-relative `path`, lowercase SHA-256 `sha256`, and integer `bytes`.
- `evidence` items contain `id`, `source`, `locator`, and `summary`. Source is `project_intent`,
  `architecture_map`, or `c4_projection`.
- Items in `facts`, every `scope` collection, `actors`, `journeys`, `quality_requirements`,
  `integrations`, and `candidate_slice_signals` contain only `id`, `statement`, and `evidence`.
- `scope` contains the arrays `included`, `excluded`, and `deferred`.
- `choices` contain `id`, `decision`, `source`, `rationale`, and `evidence`. Source is
  `explicit-intake`, `program-kit-default`, `derived-default`, or `override`.
- `capability_assessments` contain `id`, `need`, `mechanism_coverage`,
  `program_kit_capabilities`, `semantic_owner`, `semantic_profile`, `integration_owner`,
  `provider_selection`, `decision_state`, and `evidence`. Mechanism coverage is `managed`, `guided`, `external`, `conflict`,
  `not-declared`, or `insufficient-evidence`. Disposition is `explicit-user-decision`,
  `program-kit-default`, `derived-default`, `human-answer-required`, `research-required`,
  `project-owned-design`, `deferred`, or `excluded`.
- `domain_analysis` contains non-empty `subdomains`, `candidate_contexts`, and
  `founding_decision_candidates`, plus `boundary_challenges`.
- Subdomains record `id`, `name`, `core`/`supporting`/`generic` `classification`, `vision`, `ownership`,
  `non_ownership`, `language_terms`, `data_ownership`, `invariants`, `lifecycle`, provisional
  `status`, and `evidence`.
- Candidate contexts record `id`, `name`, `boundary_kind`, `vision`, `responsibilities`,
  `non_responsibilities`, `language_terms`, `subdomains`, `data_ownership`, `invariants`,
  `lifecycle`, `separation_rationale`, `split_triggers`, `status`, and `evidence`. Explicitly
  challenge every proposed cross-cutting-concern boundary.
- Founding decision candidates record `id`, `title`, `question`, `recommended_option`, genuine
  `alternatives`, `rationale`, `consequences`, `confidence`, affected element/relationship IDs,
  provisional `status`, and evidence. These are architecture prepwork, not ADRs or approval evidence.
  `affected_elements` may name any existing map element, including systems and modules; all
  candidate contexts must still be covered. Do not narrow the map's references to contexts only.
- `open_items` contain `id`, `question`, `classification`, `disposition`, `blocks`, `trigger`, and
  `evidence`. Classification is `human-decision`, `research`, `project-owned-design`, or `deferred`.
- `routing` contains string arrays named `languages`, `frameworks`, `interfaces`,
  `included_surfaces`, `excluded_surfaces`, and `capabilities`.

Every evidence reference must resolve. Use empty arrays and empty allowed strings where a category
does not apply; do not invent filler records.

## Canonical architecture map

`architecture-map.json` has exactly these top-level fields:

`schema_version`, `model_id`, `title`, `sources`, `decisions`, `documentation`, `constraints`,
`elements`, `relationships`, `views`, `configuration`, `extensions`, and `strategic_model`.

Use schema version `1.1`. All IDs use lowercase letters, digits, and hyphens. Status values for map
facts are `explicit`, `derived`, `proposed`, `unresolved`, and `accepted`; intake-created domain
boundaries remain `proposed` or `unresolved`.

- Sources: `id`, `path`, `sha256`, `format`, and importer `{ "id": ..., "version": ... }`.
- Decisions: `id`, `path`, `sha256`, `title`, ISO `date`, ADR `status`, `scope`, `owner`, and
  `supersedes`. ADR status is `Proposed`, `Accepted`, `Rejected`, `Deprecated`, or `Superseded`.
- Documentation: `id`, `path`, `sha256`, and `scope`.
- Constraints: `id`, `statement`, `status`, `applies_to`, `evidence`, and `decision_refs`.
- Elements: `id`, `type`, `name`, `description`, `status`, `ownership`, `technology`, `evidence`,
  `decision_refs`, `tags`, `properties`, `perspectives`, `url`, `group`, and `archetype`.
  Contained elements also use the top-level `parent` field.
- Relationships: `id`, `source`, `target`, `description`, `technology`, `status`, `evidence`,
  `decision_refs`, `tags`, `properties`, `perspectives`, and `url`.
- Views: `key`, `type`, `title`, `description`, `scope`, `elements`, `relationships`,
  `decision_refs`, `filters`, `order`, `layout`, `animations`, and `properties`.
- Configuration: `styles`, `themes`, `terminology`, `branding`, and `properties`.
- Extensions: `id`, `kind`, `content`, `policy`, and `source`; policy is `preserve`,
  `blocked-executable`, or `approved-external`.

`strategic_model` version `1.0` is mandatory and contains `status`, `decision_refs`, the same
`founding_decisions`, classified `subdomains`, enriched `bounded_contexts`, owned `modules`, typed
`contracts`, typed `context_relationships`, multidimensional `capability_bindings`, traced
`journeys`, and `candidate_slices`. Use the descriptor for exact nested fields before authoring. Every module is
visibly contained in a context; every cross-context dependency is typed; every journey has one
ordered dynamic view; every candidate context is supported by a founding decision candidate.

Element types are `person`, `software-system`, `external-system`, `container`, `component`,
`domain-capability`, `bounded-context`, `data-store`, `deployment-node`, `infrastructure-node`,
`software-system-instance`, and `container-instance`. View types are `system-context`,
`system-landscape`, `container`, `component`, `domain-context`, `domain-landscape`, `context-map`,
`context-decomposition`, `dynamic`, `deployment`, `filtered`, `custom`, and `image`. Perspectives
contain `name`, `description`, and `value`.

Include the required System Context, domain landscape, Context Map, context decomposition, and
dynamic journey views. Use empty collections and
strings for required fields that do not apply. Do not add containers, deployment nodes, integrations,
or decisions without intake evidence.

## Write and validate

Finish edits to the intent record before building; late status-summary edits invalidate its hashes.
Run:

`python .specify/extensions/program-kit-governance/scripts/intake_authoring.py build-draft --source docs/architecture/intake-authoring.json`

The UTF-8-safe builder projects shared fields, exports `workspace.dsl`, binds hashes and byte counts,
and runs the draft semantic validator on staged files. Errors leave current canonical outputs
unchanged. Confirmed intake cannot be overwritten. Make draft repairs in the authoring source and
rebuild; do not maintain ad hoc PowerShell serializers, hash-copy commands, or ASCII substitutions.

Review the emitted cross-context operations against their contracts and atomicity. An explicit
`command` contract cannot be `read-only`. Generic capability descriptions require a human/agent
semantic review: the validator cannot infer all side effects from prose. Resolve ambiguous writes
and historical-version guarantees visibly rather than treating structural validity as acceptance.

After the single explicit synthesis confirmation, make a narrow `status` edit to `confirmed` in
the generated intake and run `bootstrap_intake.py validate --json`. The other files and their
hashes need no changes if the reviewed synthesis is unchanged. A changed intent needs rebuilding
and review before confirmation; confirmed-artifact re-analysis remains a separate staged workflow.

Use validator diagnostics for a targeted repair. Do not print whole artifacts, schemas,
implementations, or repository-wide diffs during verification.

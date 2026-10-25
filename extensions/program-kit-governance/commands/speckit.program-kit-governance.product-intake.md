---
description: Found or resume a Program Kit product from a rough idea or an existing design, establish shared product and architectural understanding, and continue directly to first feature intake.
scripts:
  py: scripts/product_intake.py
---

# Product intake and founding

Use this skill for a new product or a substantive correction to its founding baseline. Accept
anything from a rough idea to a designed application. Preserve supplied decisions, examples,
constraints and open questions; do not make a rich design repeat a generic questionnaire.
Ordinary feature work uses specification-intake. No workflow engine or authoring worker is needed.

## Resume from durable intent

Treat `$ARGUMENTS` and the current message as intent or corrections. Read the existing
`docs/architecture/project-intent.md`, confirmed intake and canonical map when present. Run
`python .specify/extensions/program-kit-governance/scripts/bootstrap_intake.py changes --json`
to identify bound-source drift. If a skill-led approval exists, first use `product_intake.py status`
to validate its durable settled scope. Expected ADR/status promotion and unrelated later feature/map
additions do not invalidate product meaning or require a new founding. Explain consequential changes and review them before replacing
accepted meaning. Saved workflow runs, receipts, consumer locks and prior decisions are evidence;
never restart, complete or convert an old workflow automatically.

Keep the current settled intent, named decisions, provisional assumptions, unanswered frontier,
next action and due obligations in the existing intent/map/ADRs/roadmap. Do not add a session
ledger, transcript, assessment, research report, decision backlog or closure dossier. Resume the
next meaningful action from those artifacts; a missing workflow status is irrelevant.

## Understand the product

Read `references/intake-method.md`, `references/functional-discovery.md`, and the shipped
`speckit.program-kit-governance.grilling` command. Use its dependency-aware frontier questions
in this conversation. Read `references/capability-index.json`, then only the knowledge relevant
to actual needs. Reuse already supplied answers and current research. Research existing business
meaning and current external facts where consequential, preserving sources and uncertainty.
Do not turn research into a mandatory separate authoring stage.

Reflect purpose, actors and observable success. Walk through meaningful journeys in the user's
language. Establish important concepts/entities, identity, roles, relationships, lifecycles,
policies, invariants, ownership, trust, consistency and history broadly enough to understand
shared boundaries. Use examples to expose contradictions. Resolve uncertainty now when its
answer changes the foundation or what should be specified. Deepen future detailed behavior at
its feature intake; preserve supplied detail and rationale as candidate feature seeds.

Apply supported technical defaults transparently when clearly applicable. Distinguish explicit
user decisions, Program Kit defaults, derived conclusions, proposals and unknowns. Tools do not
define consumer policies, product meaning or taste. Preserve exclusions. Explain unmatched needs
as lacking a declared managed capability, without claiming the product cannot support them.
For each actual capability preserve mechanism coverage, consumer semantic ownership/profile,
integration ownership, provider selection and decision state.

Classify identified subdomains as Core, Supporting or Generic. Propose bounded contexts only
where language, ownership, lifecycle, policy or consistency justify a boundary. Challenge suspicious
cross-cutting boundaries. Preserve responsibilities/non-responsibilities, important language,
owned data, invariants, lifecycles, separation rationale and split triggers. Do not invent exhaustive
future entities, endpoints, providers or runtime resources merely to fill a template.

## Author one connected foundation

Read `references/intake-artifacts.md` and its worked example when ready to author. Use the
schema-derived descriptors for unfamiliar records, then `intake_authoring.py build-draft` to
produce the intake, map and DSL from `docs/architecture/intake-authoring.json`. Keep the linked
functional understanding and stable evidence IDs in `project-intent.md`. Use
`Intake status: see bootstrap-intake.json status`; don't duplicate transient state in prose.
Draft boundaries and candidate decisions remain proposed until explicitly accepted.

Produce together, refining contradictions across them:

- product intent, important journeys and candidate features with preserved detail and provenance;
- a constitution governing the product and ordinary delivery;
- consequential named ADRs, with real alternatives, rationale and consequences;
- the canonical domain/C4 map and generated `workspace.dsl`, including source journeys and owned
  context/module relationships;
- `docs/architecture/architecture.md`, a concise explanation of the chosen boundaries and their
  important policies/lifecycles, with references to the canonical map and decisions;
- `docs/architecture/technology-radar.md`, identifying adopted tools/profiles, justified overrides,
  proposals and the relevant evidence;
- `docs/architecture/specification-roadmap.md`, with epic outcomes, candidate feature seeds and
  actual prerequisites. Recommend a first useful outcome without commissioning siblings;
- relevant qualified Foundation capability/shell selections, with explicit consumer ownership,
  decision references and planned placements. Missing greenfield files are planned placements;
  don't scaffold or restore merely to write their paths.

Read `references/product-founding.md` for exact focused commands, acceptance boundaries and
engineering handoff. Reuse `bootstrap-decisions.json` only for supported machine-readable profile,
provider and toolchain choices used by focused setup owners; it is not an assessment approval.
Run `product_intake.py defaults` after supplying the intended selected profiles and overrides.
Do not invent an alternative configuration registry. Existing qualified profiles, native ownership
baselines and accepted locks remain owned by their normal tools.

## Review and acceptance

Before human review, validate the draft intake and actual map/selection/reference contracts.
Present the shared understanding, domain/context challenges, named decisions and alternatives,
applied defaults and consequences, first outcome, provisional assumptions and due questions.
Resolve immediate contradictions; retain genuinely later obligations with an owner and trigger.
Intake confirmation establishes the accuracy of its synthesis, not ADR acceptance. After explicit
confirmation set only intake status to `confirmed` and run `bootstrap_intake.py validate --json`.
Do not refresh changed source hashes to disguise drift.

Draft and ratify the constitution through its existing begin/review/ratify commands, after explicit
human ratification. Then run `product_intake.py review`. Show its exact named artifacts and map
scope. Only after the human explicitly accepts that foundation run
`product_intake.py accept --verdict approve`, then `product_intake.py validate`.
If scope extends beyond the founding candidates, use the existing acceptance-scope contract to
name the additional decision IDs and affected map elements/relationships. A proposal outside
that scope stays provisional. Never infer acceptance from silence, a hash, successful execution,
or an intake confirmation. Proxy answers remain fictional and cannot supply authority.

Acceptance promotes only the reviewed ADR/map scope and qualified Draft selection. It preserves
original intake provenance. No runtime compatibility, feature implementation or delivery result
follows from acceptance. Don't create a completion receipt or call native workflow completion.

## Continue directly to a feature

After acceptance, offer the recommended outcome and invoke the shipped
`speckit.program-kit-governance.specification-intake` skill in this session for the user's selected
first feature. A missing or non-Ready roadmap entry does not prohibit useful feature intake.
Do not interpose assessment/research/backlog/closure stages, runtime proof matrices, repository
restore or fresh authoring workers. Carry relevant unanswered questions to their owning feature
and actual action. A pre-spec feasibility experiment is justified only if its answer changes what
should be specified; state that question and evidence limit first.

At planning, implementation, restore, provider use or delivery, run the checks the actual action
requires through existing phase, repository-sync, composition and engineering owners. Failures,
unavailable prerequisites and stale evidence stay visible. A reviewed founding artifact is never
proof that those checks passed.

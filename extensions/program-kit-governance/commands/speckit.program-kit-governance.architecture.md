---
description: Create or update the living architecture baseline and ADR system.
scripts:
  py: scripts/governance_state.py validate
---

## Input

Create `docs/architecture/bootstrap-acceptance-scope.json` using the installed
`references/bootstrap-lifecycle.md` contract. Enumerate the exact map semantics this review accepts,
including newly designed runtime elements when justified. Leave unfinished providers and unrelated
proposals outside the scope. Keep current lifecycle status in canonical metadata and deterministic
marked views, not duplicated prose. Preserve conditions retained in ADRs; Proposed-to-Accepted
promotion is not evidence those conditions have executed. The later bootstrap-closure command owns
isolated compatibility work before dependent slices become Ready. Architecture drafting still does
not scaffold or restore consumer projects.

`$ARGUMENTS` identifies the confirmed intake and the workflow-generated bootstrap context path.

Read the compact bootstrap stage brief first. It contains the confirmed intake, canonical
architecture-map identity, compact approved decisions and ratification records, a measured
`stage_plan`, and a link to a separate hash-bound evidence index. Follow the stage plan in order.
Read the canonical architecture map and ratified constitution in full exactly once; patch that
validated seed rather than reconstructing a new map from the schema. Do not print or read the
evidence index in full; query one artifact and heading range only when the brief lacks a fact
required for an architecture decision. Do not
bulk-read every unchanged assessment or research artifact or enumerate installed files.
Use `governance.paths` and `output_contract` as the resolved path and validation authority. Do not
search `.specify`, unrelated extensions, catalogs, or validator implementation to rediscover them.
Before the first write, read each file listed by `output_contract.contract_references` exactly once
and shape both JSON outputs from those schemas. Do not use repeated validator failures to discover
required fields, allowed values, or nested record shapes.
Use `output_contract.artifact_target_bytes` as the initial generation target and
`output_contract.artifact_byte_budgets` as the hard boundary after all writes. Report final byte
counts; do not trade away required architecture evidence merely to reach a target.
When `stage_plan.building_blocks` is present, use its exact draft command, composition slot/options
projection, canonical repository convention, observed target inventory, and authorized
`placement_planning` contract. Missing application files are a planning input: architecture owns
the exact future layout and may declare it without creating those files. Do not run `--help`, search or dump the
catalog, or enumerate project files to rediscover those values. When
`stage_plan.managed_web_contract` is present, use its exact applicable control decisions and
verification statements; do not search the installed extensions for `WEB-Cxx` records.

## Constitutional authority

Before reading or writing architecture, run:

```text
{SCRIPT}
```

Read the ratified `.specify/memory/constitution.md` in full. The constitution governs architecture,
ADRs, specifications, plans, tasks, implementation, and verification. Stop if the ratification
record is missing, Draft, invalid, or stale, or if the constitution contains a placeholder or TODO.

The validator confirms `.specify/governance/bootstrap-assessment-approval.json` and
`docs/architecture/bootstrap-decisions.json`. Use their compact records from the stage brief. Open
one source only if a decisive field was omitted. The hash-bound assessment gate is the human
authority for explicit intake choices, Program Kit defaults, derived defaults, disclosed
acknowledgements, and recorded overrides. Do not reopen those choices as Proposed.

## Architecture bootstrap

Preserve existing accepted decisions and user content. Honor the configured ADR and roadmap paths;
create the remaining missing artifacts under `docs/architecture/`:

- `README.md`: navigation, ownership, update rules, and status vocabulary.
- `architecture.md`: goals, constraints, context, building blocks, runtime views, deployment, cross-cutting concepts, risks, and quality scenarios.
- `quality-attributes.md`: measurable scenarios and verification methods.
- `technology-radar.md`: proposed, accepted, deprecated, and rejected technologies with ADR links.
- `traceability.md`: design -> decision -> specification -> plan -> implementation -> verification.
- `specification-roadmap.md`: created later by the roadmap command after tooling; architecture establishes
  slice identity and decision evidence, but never owns or copies roadmap-entry lifecycle status.
- `decisions/README.md` and an ADR template.

Create `decisions/bootstrap-baseline.md` as a consolidated Accepted decision recording the exact
approved decision-register hash, default-profile version, explicit choices, applied defaults,
overrides, material acknowledgements, and easy supersession path. Copy the decision-register
SHA-256 directly from `authorities.assessment_approval.bootstrap_decisions_sha256` in the stage
brief; do not probe or reopen the approval record solely to rediscover that hash. Include the stable
ID of every choice, override, and acknowledgement so validation can prove traceability. Ordinary
reviewed defaults do not need one ADR each. Project-specific choices outside that baseline remain
Proposed until their own human approval.
Write its status using the exact line `- **Status**: Accepted`. For every other ADR, use the same
field syntax with its actual lifecycle value; keep the colon outside the bold marker.

Scale the detail to the system. A one-module local process does not need speculative multi-module,
deployment, persistence, or operations prose. State a not-applicable boundary once, keep catalogs
to existing elements, and avoid inventing identifiers that do not improve traceability. For a
single-interface, dependency-free local application, use the byte target supplied by
`output_contract` for `architecture.md`.
After writing, report paths, sizes, and validation counts only; do not print complete artifacts or
repository-wide diffs.

Do not rewrite `bootstrap-assessment.md`, `decision-backlog.md`, `tooling-evaluation.md`, or
`bootstrap-decisions.json` after their approval. If one is wrong, stop and direct the user back to
the assessment review so the artifacts can be corrected, the packet regenerated, and the exact
contents approved again.

Treat `docs/architecture/architecture-map.json` as the canonical living architecture model and the
confirmed intake map as its provisional starting state. Make the smallest patch that adds accepted
decision and architecture evidence; do not synthesize the model from an empty object or copy a
schema example over it. Preserve every existing element `parent` unless an accepted decision
explicitly changes containment. Refine fields that are not immutable
confirmed-intake projections with accepted assessment choices, the ratified constitution, and
architecture evidence. Maintain its C4 System Context and Domain
Context Map as the first review views. Preserve the intake's domain/subdomain landscape,
context/module decomposition, and one dynamic view for every separately named source journey.
Add C4 container, component, or deployment levels only when evidence supports those physical or
runtime boundaries; a bounded context or capability must never be projected as a peer software
system merely to fit a C4 level. Diagrams are views of the canonical model, never independent
sources of truth.

For every seed dynamic view bound to a confirmed intake journey, preserve its relationship selection
and order exactly. Adding relationships to the model does not authorize appending them to
that seed view; put supported additional detail in a separate view instead.

The confirmed intake remains immutable evidence. Preserve these cross-artifact projections exactly:

- `strategic_model.subdomains` is the intake `domain_analysis.subdomains`; only `decision_refs` may
  be added to a map record.
- Each `strategic_model.bounded_contexts` record is its intake
  `domain_analysis.candidate_contexts` record with `id` and `name` represented by `element`; the
  referenced element must retain the intake name, every other intake field remains identical, and
  only `decision_refs` may be added.
- Each `strategic_model.capability_bindings` record is its intake `capability_assessments` record
  with `id` represented by `assessment` and `need` omitted; only `module`, `status`, and
  `decision_refs` may be added. Preserve all other values exactly.
- `strategic_model.founding_decisions` is exactly the intake
  `domain_analysis.founding_decision_candidates` collection. Map every intake journey separately
  through `source_journey`, and use only evidence IDs declared by the intake.

Do not enrich, rewrite, or normalize those confirmed semantics in the architecture map. Put later
detail in modules, contracts, relationships, constraints, ADRs, narrative documents, or another
non-projection field.

Apply these executable containment rules before the first map write:

- Every `strategic_model.modules[].element` identifies a `domain-capability` element whose `parent`
  equals that module record's `context`; every domain-capability has exactly one module record.
- Every non-empty `strategic_model.capability_bindings[].module` identifies one of those strategic
  modules, never a container or an arbitrary runtime feature.
- Every C4 `component` has a `container` parent. A CShell or host directly owned by the software
  system is a container, not a component. Do not create a component view unless component
  containment actually exists.
- Keep one unique dynamic view for every confirmed intake journey.

Write the founding ADRs and structurally patch the model before generating long narrative files.
Use the stage brief's artifact records to determine which architecture files already exist and
their current byte counts. Do not construct a PowerShell file-inventory command or issue separate
`Get-Item` length probes; the supplied validators report final output sizes.
Run only `stage_plan.structural_validation_command` at that structural checkpoint. It batches the
map validator, building-block draft validator when applicable, DSL export, source revalidation, and
intake alignment into one process. Only after it passes, write the compact narrative set, refresh
its documentation hashes in the map, and run the single command in
`output_contract.validation_commands`. This intentional two-check sequence prevents prose
generation around an invalid model without repeatedly reintroducing the growing diff into agent
context. Additional validation loops must be driven by a specific diagnostic.

Read the intake's founding decision candidates before doing broad architecture research. For each
candidate, verify the evidence and assumptions against the ratified constitution and relevant
technical constraints, retain genuine alternatives and consequences, then materialize the result as
a real Proposed ADR carrying the candidate ID. Research only the uncertainties that remain material;
do not repeat already bounded intake discovery. Every candidate must end as a Proposed ADR,
an explicitly unresolved architecture item, or a documented rejection with rationale. List the exact
founding ADR paths and hashes in the post-architecture approval packet. That approval accepts the
reviewed founding ADR bundle; it does not accept unrelated Proposed ADRs.

Each founding ADR must include a machine-readable line shaped as
`- **Founding decision candidate**: candidate-id` and the exact lifecycle line
`- **Status**: Proposed`. Add it to the canonical map decision catalog using the same candidate ID.
The approval transition changes only that enumerated bundle to Accepted, updates the affected map
semantics and ADR hashes, and regenerates the DSL; never pre-accept these ADRs in the architecture command.

Maintain the model's first-class decision catalog. Every linked ADR records its repository-relative
path, SHA-256, title, date, lifecycle status, scope, owner, and supersession links. Add typed
`decision_refs` to governed elements, relationships, views, constraints, technology and ownership
facts. Reject missing or stale ADRs, broken supersession chains, and accepted architecture governed
only by non-Accepted decisions. Export attached ADR directories through Structurizr `!adrs` while
retaining the provider-neutral canonical links.

Preserve portable Structurizr semantics in the canonical fields and retain unknown statements as
typed extensions. Never execute `!script`, `!plugin`, remote includes, or remote image/theme fetches
during model import or export. Such features require a separate explicit policy decision and
authorization. Generate the DSL projection only through the structural and final validation batches
supplied in the stage plan. They use the canonical exporter and never accept a hand-edited
projection.

After generating the projection, tell the user: "To open the C4 diagrams safely on localhost, ask
`View the C4 projection` or invoke `$speckit-program-kit-governance-view-c4`. Program Kit validates
freshness first and does not change the canonical architecture map."

The supplied batches validate the canonical model with source and ADR hashes and, using the stage
brief run ID, validate the evolved map against the confirmed intake. Repair only a named diagnostic
in architecture-owned artifacts. After the final batch passes, stop immediately: do not inspect a
diff, remeasure files, read another source, or run another command. Report only paths, byte counts,
and validation counts.

The architecture baseline must also define:

- the bounded-context map and ubiquitous language boundaries;
- module and feature ownership, public contracts, data ownership, and allowed dependency graph;
- Core/helper/implementation/provider/bridge/composition roles, semantic capability ownership, and
  selected runtime feature identities without layer-marker project names;
- a compact candidate slice catalog that names the user journey and observable outcome, entry
  point, participating boundaries, owned public contract/data/lifecycle portion, success and
  material failure outcomes, executable verification, and any horizontal prerequisite; each slice
  must cross the required layers end to end rather than becoming a layer or component backlog;
- the distinction between compile-time modules, runtime features, shells, and endpoints;
- shared-kernel and feature-family extension policies, including exact Accepted exceptions;
- the cross-context decision rule for bridges, events, orchestrators, and deliberate Core-to-Core
  published-language/subdomain/shared-kernel edges;
- domain-event ownership and delivery semantics, plus an explicit Integration Events/outbox gate for
  every durable post-commit, background, broker, or cross-process requirement;
- host web-runtime versus `.Api` endpoint ownership, including canonical permission identities and
  provider-claim mapping boundaries;
- proportional authorization ownership: provider mappings belong to deployment, canonical
  `permission:<identity>` policies to the selected Program Kit authentication feature, and only
  genuine resource/state/effect decisions to consumer code; a no-effect probe ends at the endpoint gate;
- how the first specification delivers an observable vertical slice rather than technical layers.

`docs/architecture/specification-roadmap.md` is the sole authority for `Candidate`, `Blocked`,
`Ready`, `Active`, `Delivered`, and `Superseded` roadmap-entry status. Before roadmap generation,
architecture and traceability may describe provisional slice identity, scope, dependencies, and
decision evidence, but must not assign a roadmap status or claim that a future roadmap record is an
authoritative current state. The deterministic post-roadmap synchronization step owns the marked
derived navigation view in both files.

## Decision policy

ADR states are `Proposed`, `Accepted`, `Rejected`, `Deprecated`, and `Superseded`. Only a human may move a project-specific ADR to `Accepted`. Every accepted technology, cross-domain dependency, public contract, data ownership rule, consistency boundary, security boundary, and material exception must cite an Accepted ADR.

Every accepted cross-module implementation reference, feature-family inheritance edge, shared store,
or runtime feature dependency must also cite an Accepted ADR and an executable or reviewable
enforcement location.

Resolve the decision backlog through focused design tasks before implementation depends on those answers. A design task produces evidence, alternatives, consequences, a proposed ADR, updated views, and follow-on specification slices. It does not implement application behavior.

Architecture documents must clearly distinguish facts confirmed by intake evidence, derived constraints, proposals, accepted decisions, and unresolved questions.

When .NET is selected without the recorded opt-out, the architecture, technology radar, and
bootstrap-baseline decision must adopt the application-neutral `Orbyss.Foundation.Host` and runnable-host release model as
Accepted. Do not scaffold or restore packages during this command.

When any capability routes to the installed `program-kit-building-blocks` catalog, create
`docs/architecture/building-block-selection.json` as a complete `Draft` using its shipped schema.
Name every scope, composition instance, choose-one/optional answer, and exact repository/project/
package/shell/host target; never infer placement from project names or apply packages globally. Bind
its authority to the Proposed founding ADR IDs that decide those selections and include the concrete
rationale. For a .NET selection without the recorded Foundation-host opt-out, bind the `api_baseline`
host target and explicitly choose `foundation-host`; an empty optional answer is not the default.
Use the exact draft command supplied by `stage_plan.building_blocks` to initialize suggestions;
it does not decide placement. Derive each path from semantic context/module ownership, deployment
boundaries, repository conventions and explicit preferences. Preserve observed paths, identities
and ownership. Declare new paths explicitly as proposals, never infer a global package drop from
project names. Never ask product users for .csproj paths, package.json locations, shell filenames,
target IDs or other mechanical bookkeeping, including through intake. Ask only about consequential
product constraints or trade-offs that context and applicable defaults cannot resolve.

For every target, author `placement` with `state: observed|planned`, `owner` (canonical architecture
element ID with nonempty ownership), `decisionIds`, and `rationale`. The owner must reference those
decisions through `decision_refs`, and the selection authority must include them. Register each
current Proposed or Accepted ADR with its path and SHA-256 in the map. State records origin at
design time: planned targets may later exist after an approved scaffold. It is not permission to
materialize. Keep kind, role, scope and shell explicit; slot bindings must remain within the
composition's required scope. The validator checks provenance, containment, collisions, slot
compatibility and managed options without creating consumer manifests.

Reconcile research proposals against the projected managed option groups before selecting a stack.
For example, Blazor is not a `forms_runtime.renderer` managed option when that group lists only
Angular, React and Vue. Keep such a proposal unresolved until architecture chooses a compatible
option or produces an explicitly reviewed custom adapter/override design; do not silently replace
the renderer or rewrite approved product semantics.

The
structural and final validation batches run the offline draft validation that proves closure and
placement. The final bootstrap approval promotes those ADRs and the reviewed Draft together; it
still does not restore or materialize dependencies.

If a prerequisite prevents completion, run `stage_plan.blocked_result.command`, supplying its
required `--reason`, `--owner` and `--resolution` arguments, then report BLOCKED. The command exits
2 intentionally and preserves a structured diagnostic for the next output gate. A successful
worker process or dispatch is not completed architecture; only passing the final validation batch
establishes deliverable completion. Rebuilding this run's architecture context archives the prior
blocked report before a deliberate retry.

When the decision register selects a browser UI, the architecture runtime, deployment,
cross-cutting, and verification views must adopt the exact `web.secure_profile` and reference its
versioned Program Kit contract. Do not restate its configuration and middleware decisions as open
questions. Show the same-origin BFF boundary and server-held tokens for `bff-cookie-v1`, or the
separate public client, exact CORS boundary, and browser token exposure for `spa-pkce-v1`.
The baseline and relevant views must also inherit `program-kit-web-threat-model-v1` and
`program-kit-web-security-evidence-v1` by exact ID. Record project additions and deviations in a
small security-assurance section: additional assets/threats/assumptions, overridden defaults,
accepted residual risks, owner, review condition, and verification. Do not call a working-group
draft final, a platform recommendation normative, or a Program Kit operational default
scientifically proven.
Canonical `WEB-Cxx` identifiers retain the decision text and profile applicability from the managed
evidence registry. Project-specific verification cases use another namespace, such as `WEB-Qxx`,
and map explicitly to one or more canonical controls; they never redefine a `WEB-Cxx` identifier.

For `ui-experience-v1`, include consumer-owned branding/content, generated semantic tokens and
initial-render metadata, optional public discovery projection, and independent analytics adapters.
Map each page's public/private/indexing intent; no private body may enter public build artifacts.
Keep .NET endpoints in `Orbyss.Foundation.Web.Discovery` or consumer-owned IWebShellFeature adapters,
never in Orbyss.Foundation.Host. Accepted frontend frameworks consume the same contracts through their
own initial-render adapter. Do not duplicate route/head owners or replace Keycloak flows to share
branding. SVG/logo/icon assets retain license and accessibility semantics.

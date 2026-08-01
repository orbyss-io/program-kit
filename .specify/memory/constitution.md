<!--
Sync Impact Report
- Version change: 0.1.0 proposal -> 1.0.0
- Modified principles:
  - Proposal I and II -> I. Human Authority and Semantic Honesty
  - Proposal III through V -> III. Exact Contracts and Governed Resolution
  - Proposal VI and X -> IV. Honest Determinism and Evidence
  - Proposal VIII -> VI. Explicit Extensions and Composition
  - Proposal XI -> VII. Diagnostics Are an AI-Usable Public Contract
  - Proposal XII -> VIII. Consumer Ownership, Runtime Isolation, and Local Safety
  - Proposal IX and XIII -> IX. Evidence-First Vertical Delivery
- Added principles:
  - II. The Public Product Is an Independent Software Factory
  - V. Artifact Ownership and Atomic Trust
- Removed principles:
  - Native planning obligations; Spec Kit owns the guided development workflow
  - Automated migration obligations; migration design is deferred
  - A universal feature/domain architecture; consumers own architecture
- Added sections:
  - V1 Product Boundary
  - Enforcement Contract
  - Spec Kit Development Workflow
- Template compatibility:
  - .specify/templates/plan-template.md already loads Constitution Check gates
  - No command or task template changes required
- Follow-up TODOs: none
-->

# Program Kit Constitution

## Core Principles

### I. Human Authority and Semantic Honesty

Program Kit MUST preserve human authority over product intent, semantic meaning,
identity-forming choices, policy, ownership, trust, widened effects, external
publication, and release. AI sessions and tools MAY discover, challenge,
translate, and implement approved intent, but MUST NOT approve their own
interpretation, grant themselves authority, or silently broaden scope.

Consumer semantics and architecture MUST remain consumer-owned. Program Kit
MUST provide domain-neutral mechanics and MUST NOT invent business meaning,
guess missing meaning, or present inferred, unknown, stale, unsupported, or
unverified behavior as understood. Every admitted semantic claim MUST be
human-approved, traceable to an authoritative artifact, and supported by the
evidence its declared profile requires.

The governing expression is: **AI builds it. Human intent governs it.**

**Rationale**: Program Kit is valuable only when software created with AI
remains governable by humans and uncertainty cannot masquerade as accepted
meaning.

**Enforcement**: Human reviewers own semantic adequacy and accepted risk; the
kernel owns authority, traceability, unknown-state, and admission invariants.
This principle applies to specifications, selections, evaluations, publication,
and release. Evidence consists of exact approved artifacts, scoped grants, and
trace links. Missing authority or semantic support MUST stop with a structured
request for input, approval, or revision. Kernel invariants are not waivable.

### II. The Public Product Is an Independent Software Factory

Program Kit MUST be an independently callable development- and
construction-time software factory. Its kernel is the trusted core that owns
non-bypassable invariants, exact resolution, and admission. Its CLI is the
public application layer that invokes kernel-controlled workflows through
versioned public contracts. Internal implementation details MUST NOT become
required consumer contracts.

Spec Kit owns the recommended human-led discovery, specification, planning, and
task workflow used to develop Program Kit. Program Kit v1 MUST NOT create a
native goals, roadmap, planning, work-unit, or task-lifecycle system. A future
external Spec Kit adapter MAY invoke only stable public Program Kit contracts
and MUST remain replaceable, separately installed, and unable to elevate
authority or bypass a gate. Other orchestrators MUST be able to use the same
factory contracts.

The repository MUST retain a permanent independent bootstrap through the
standard .NET toolchain and Spec Kit without executing Program Kit against
itself or trusting self-generated governance. Optional future dogfooding MUST be
downstream, removable, non-authoritative, and unable to block repair or release.

**Rationale**: An independently usable public factory avoids the circular
dependency that compromised the archived product and keeps every orchestrator,
including Spec Kit, replaceable.

**Enforcement**: Kernel and CLI maintainers own this boundary. Public contract
tests, clean bootstrap/build proof, forbidden-dependency checks, and package-only
consumer tests provide evidence. Public behavior that requires Spec Kit,
Program Kit self-execution, or private implementation coupling MUST block
release. The independent bootstrap and public-contract boundary are not
waivable.

### III. Exact Contracts and Governed Resolution

Governed meaning MUST use explicit typed, versioned, canonical contracts.
Program Kit's portable unit MUST be a versioned software-definition bundle with
a canonical root manifest and separately governed linked artifacts. Source code
is governed implementation material, not the portable semantic source of truth.
The semantic artifact model MUST remain API-neutral and declarative; executable
derivation belongs to exact selected capabilities.

Identities and revisions MUST be unambiguous within their declared authorities.
Every output-affecting contract, vocabulary, target profile, provider profile,
capability, dependency, policy, and tool MUST resolve exactly and be recorded in
an accepted resolution lock. Installation and discovery MUST NOT imply
selection, compatibility, activation, trust, or authority. Ambient ordering,
best-match selection, floating versions, and silent fallback MUST NOT determine
meaning.

Program Kit's non-negotiable product promise is governed integration
resolution: a relationship MUST resolve as direct contract-conformant
composition, through an exact explicit adapter or available migration, or as a
precise contract-backed incompatibility. Zero matches, multiple matches,
conflicting meaning, representational loss, incomplete support, and unavailable
inputs MUST remain explicit and actionable; ambiguity is failure.

Program Kit MAY use a thin target-specific feature model, but MUST NOT impose a
universal domain architecture. Features, interfaces, contracts, intakes,
bindings, components, and artifacts remain distinct identities and MAY have
many-to-many relationships. The kernel owns integrity; consumers own
architecture and MAY impose stricter rules.

**Rationale**: Reusable software can integrate predictably only when identity,
meaning, selection, and incompatibility are explicit rather than inferred from
code layout, installation, or convention.

**Enforcement**: The kernel owns identity, canonicalization, exact closure,
resolution, and admission; contract-family and vocabulary owners own their
declared meaning. Schemas, typed validation, canonicalization fixtures,
resolution locks, closure reports, and integration-resolution explanations
provide evidence. An invalid, ambiguous, incomplete, or unsupported closure
MUST return no trusted result. Integrity and exact-resolution gates are not
waivable.

### IV. Honest Determinism and Evidence

Program Kit MUST claim deterministic construction only inside an exact named
reproducibility profile whose semantic intent, inputs, selections, providers,
capabilities, tools, templates, dependencies, policies, and relevant environment
properties are complete, supported, accepted, and pinned. Equal construction
identities under that profile MUST produce byte-identical Program Kit-owned
canonical outputs. Cross-platform or external-tool equivalence MAY be claimed
only under an exact verifier and fixtures that prove it.

Custom-authored implementation MUST remain explicitly custom-bounded and
evaluated; it MUST NOT be described as deterministically derived. Semantic
coverage, construction method, conformance, runtime behavior, runtime
availability, and external-system behavior are separate claims. Evidence MUST
bind exact inputs, operation, implementation, outputs, scope, observations,
freshness, and limitations. A digest or receipt MUST NOT substitute for missing
content or current evidence.

Output-affecting ambient time, randomness, locale, path, machine state, process
order, environment, or floating dependency state MUST be normalized, declared
as an identity input, or rejected. Secrets MUST NOT become reproducibility
inputs.

**Rationale**: Scoped reproducibility and fresh evidence create trust; broader
determinism claims would hide the nondeterministic and external behavior that
Program Kit does not control.

**Enforcement**: The kernel owns construction identity and evidence truth;
providers own profile-specific reproducibility and conformance claims.
Repeatability, permutation, clean-environment, digest, conformance, and
freshness fixtures provide evidence. An unproven claim MUST be downgraded to its
honest supported class or blocked; it MUST never pass as deterministic.
Determinism and evidence-truth gates are not waivable.

### V. Artifact Ownership and Atomic Trust

Every materialized artifact MUST be classified as generated-owned,
seeded-handoff, or consumer-owned. Program Kit MUST NOT silently overwrite,
adopt, reinterpret, or repair drift. Generated-owned edits are drift;
seeded-handoff artifacts become consumer-owned after creation; consumer-owned
artifacts MUST NOT be modified. V1 MUST NOT mix generated and editable regions
inside one file.

Construction MUST stage an immutable complete candidate set, validate it, check
live-path ownership and collision preconditions, and publish only after complete
success. Admission and publication receipts MUST apply only to a completely
trusted artifact set. Interrupted or partial publication MUST remain explicit,
recoverable, and untrusted. Evaluation MUST diagnose without mutation; repair
MUST be a separate authorized request with revalidated preconditions.

**Rationale**: Explicit ownership and set-level publication protect consumer
work, prevent partial output from becoming trusted, and make drift safely
diagnosable.

**Enforcement**: The kernel owns artifact-set state, ownership, admission, and
publication safety. Candidate manifests, journals, receipts, collision tests,
interruption tests, and drift/repair fixtures provide evidence. Any uncertain,
colliding, partially published, or drifted set MUST block construction or
remain explicitly untrusted. Ownership and trusted-state atomicity are not
waivable.

### VI. Explicit Extensions and Composition

Extension bundles, factory operation contracts, executable operation providers,
AI-facing session capabilities, declarative vocabulary packages, and provider
profiles MUST remain distinct concepts, identities, trust decisions, and
activation decisions. V1 kernel-invokable operation roles are intake mapping,
construction, and evaluation; resolution and admission remain kernel mechanics.
A new role requires an explicit protocol revision.

Operation providers MUST produce immutable candidate outputs and MUST NOT edit
another provider's artifacts. Contract-declared contribution seams MUST feed one
exact owner/assembler for each final generated artifact. The seam contract MUST
define cardinality, compatibility, identity keys, conflicts, and meaningful
ordering. Filesystem order, registration order, scheduling order, reflection
discovery, or mutable global state MUST NOT carry semantic authority.

V1 MUST execute only exact, explicitly registered first-party providers shipped
with the selected distribution. In-process execution is trusted and MUST NOT be
presented as sandboxed. Dynamic third-party loading, a marketplace, a trust
store, signing infrastructure, and untrusted execution remain outside v1 until
a proven out-of-process isolation profile exists.

**Rationale**: Contract-owned seams enable extensibility without allowing
ambient discovery, execution order, or installed code to acquire semantic or
security authority.

**Enforcement**: The kernel owns role, selection, composition, and execution
admission; providers own complete manifests, diagnostic namespaces, support
claims, and conformance fixtures. Collision, order-independence, seam,
provenance, and support tests provide evidence. An incomplete or unselected
provider is unavailable and MUST NOT execute. Composition and trust-admission
gates are not waivable.

### VII. Diagnostics Are an AI-Usable Public Contract

Every recoverable running public CLI path, including pre-admission refusal, MUST
return one versioned structured operation-result envelope. Machine data is
authoritative; human output MUST be a faithful projection; JSON mode MUST emit
one clean document. Results MUST distinguish outcome, furthest phase, effect
state, primary disposition, artifacts, evidence, receipts, diagnostics, and any
continuation without inventing unknown values or claiming partial success.

Every diagnostic MUST use a permanent authority-qualified identity and exact
catalog revision with typed category, severity, subject, violated rule or
contract, bounded cause and consequence, safe expected/observed data,
remediation, disposition, and evidence references. Automation MUST consume
identities and typed fields, never rendered prose. Remediation MUST be a bounded
preconditioned proposal, never executable prose or authority; the kernel MUST
revalidate a separate exact grant before any effect.

Disclosure MUST be schema-classified and fail closed. Secrets, secret-derived
fingerprints, protected paths, unsafe commands, raw external output, exceptions,
and stack traces MUST NOT enter ordinary results. A minimal independent fallback
MUST return the safest specific faulted envelope after recoverable pipeline
failure. No envelope is promised before process startup, after forced or
unrecoverable termination/resource failure, or when the chosen channel cannot
be written.

**Rationale**: Humans and AI sessions can correct failures safely only when
outcomes are stable, structured, actionable, honest about effects, and safe to
disclose.

**Enforcement**: The diagnostics subsystem owns envelopes, catalogs, ordering,
disclosure, and fallback behavior; each provider owns its namespaced entries.
Schema, golden-result, ordering, truncation, redaction, malformed-input,
provider-failure, and fallback fixtures provide evidence. A recoverable public
path without a safe meaningful result is a contract failure and blocks release.
Diagnostic truth and disclosure floors are not waivable.

### VIII. Consumer Ownership, Runtime Isolation, and Local Safety

Generated projects, packages, source, configuration, hosts, analyzers, and
documentation MUST remain ordinary, inspectable, testable, consumer-owned
software artifacts. Generated products MUST NOT require Program Kit, Spec Kit,
an AI provider, prompts, transcripts, session capabilities, repository state, or
authoring configuration at runtime unless the consumer explicitly selects a
separately governed runtime feature. Program Kit v1 itself MUST provide no
runtime plugin host, runtime semantic interpreter, deployment controller, or
operational-state manager.

Development-session capabilities MUST remain isolated from runtime code and
consumer distributions. Program Kit MUST be local-first: no telemetry, source
upload, or network access by default. External processes, network, credentials,
and filesystem effects MUST be declared, bounded, authorized, and evidenced.
Secrets MUST NOT enter governed outputs, locks, diagnostics, provenance,
fixtures, logs, or SBOMs. Dependencies, sources, tools, templates, and release
inputs MUST be exact, locked, attributable, and drift-detecting.

**Rationale**: A development tool remains adoptable only when its outputs are
ordinary software and its authoring machinery, network behavior, and sensitive
state do not leak into consumer runtimes.

**Enforcement**: Distribution and security maintainers own runtime isolation,
dependency policy, and release provenance; the kernel owns effect authorization
and disclosure. Forbidden-reference, package-closure, offline, secret-scanning,
locked-restore, provenance, SBOM, and consumer-runtime tests provide evidence.
Runtime coupling, undeclared effects, secrets, or unapproved dependency drift
MUST block admission or release. Runtime isolation and the secret/disclosure
floor are not waivable.

### IX. Evidence-First Vertical Delivery

Program Kit MUST be delivered through the smallest end-to-end vertical slice
that proves a real public factory workflow. New projects, packages,
abstractions, protocols, providers, registries, or mechanisms require a concrete
ownership or independently testable consumer reason. General semantic-engine
machinery MUST be deferred until a product workflow proves its need.

Compilation and green tests are necessary but insufficient. A slice MUST also
prove its exact public contracts, negative paths, clean bootstrap, deterministic
claims, diagnostics, artifact ownership, integration explanation, runtime
independence, repeatability, drift behavior, and fresh-consumer usability.
Documentation MUST distinguish implemented behavior, accepted design,
proposal, limitation, and future horizon.

**Rationale**: Real vertical proof exposes mistaken abstractions early and keeps
the product focused on a tangible software-factory workflow instead of
speculative semantic-engine machinery.

**Enforcement**: Maintainers own scope and engineering proof; human product
review owns fitness and comprehensibility. Specifications, plans, dependency-
ordered tasks, contract/negative/adversarial fixtures, consumer walkthroughs,
and review records provide evidence. Unjustified machinery, public-contract
bypass, or missing product proof MUST stop planning or block completion. A
policy exception may be considered only through the finite waiver mechanism;
it cannot override any kernel gate.

## V1 Product Boundary

Program Kit v1 is a human-governed, AI-provider-neutral .NET software factory.
It turns approved intent into contract-bounded ordinary software through
independently callable CLI operations. Deterministic plumbing, projections, and
integration are constructed only inside supported pinned envelopes; custom
business implementation remains consumer-authored and evidence-evaluated.

The initial implementation MUST:

- target `net10.0` and stable C# under one exact reviewed SDK patch;
- support the exact `.NET 10 + CShells 0.0.28` construction profile, with
  CShells used only for selected .NET feature and host-participation mechanics;
- expose intake mapping, construction, and evaluation as the three initial
  provider operation roles;
- use a typed API-neutral artifact model, restricted YAML authoring projection,
  structured JSON automation projections, and one versioned canonical JSON byte
  profile;
- ship only explicitly registered first-party executable providers with exact
  manifests, provenance, diagnostics, support metadata, and conformance
  evidence;
- use `System.Text.Json`, JSON Schema, NuGet, SDK-style MSBuild/`dotnet`, and
  provider-scoped Roslyn only in their declared bounded roles; and
- preserve deterministic workspace views as projections of authoritative
  records, never as a competing global source of truth.

The following remain outside v1 and MUST NOT be introduced incidentally:

- a native planning, roadmap, work-unit, or task system;
- a Program Kit runtime, deployment controller, operational-state manager,
  runtime semantic engine, or required AI runtime;
- automated semantic, implementation, deployment, or runtime-data migration;
- multi-ecosystem implementation, universal domain/feature architecture, or
  general reconstruction, inference, lifecycle, or global-graph machinery;
- dynamic or untrusted third-party provider execution, marketplaces, trust
  stores, signing infrastructure, or sandbox claims; and
- source generators, custom MSBuild extension tasks, weaving, reflection-based
  discovery, or hidden compile-time generation.

These are deferred product boundaries, not assertions that they can never
exist. Crossing one requires explicit human acceptance and an appropriate
constitutional or scoped design amendment before implementation.

## Enforcement Contract

Every normative rule MUST identify one honest enforcement mode:
`executable-invariant`, `evidence-backed`, `human-review`, or
`aspirational`. A rule MUST NOT claim a stronger mode than its evidence can
support. Mechanizable invariants SHOULD be automated at the earliest reliable
layer; subjective adequacy MUST remain visibly human-reviewed.

Kernel gates for integrity, identity, exact closure and resolution, authority,
artifact ownership and publication safety, provenance, evidence truth,
diagnostic truth and disclosure, and trusted-state atomicity are never waivable.
Their status MUST be passed, failed, not-applicable, or not-evaluated; unknown
applicability and not-evaluated mandatory gates block admission.

Only policy rules explicitly declared waivable MAY use a waiver. A waiver MUST
be an exact, authority-backed, identity-forming artifact scoped to named rules,
subjects, operation/profile/effects, risk, controls, evidence, revocation, and a
finite expiry. Wildcards, implicit inheritance, global suppression, force flags,
and non-expiring waivers are invalid. Waived MUST remain distinct from passed
and visible in every applicable result.

## Spec Kit Development Workflow

Program Kit MUST be developed with the repository's Spec Kit workflow and
standard .NET toolchain, never with Program Kit's own factory operations.

Before implementation, every feature specification and plan MUST:

1. state human-owned intent, scope, non-goals, authority, and unresolved meaning;
2. identify affected contracts, identities, ownership, dependencies, public
   operations, artifact classes, and exact product-boundary applicability;
3. distinguish deterministic construction, custom-bounded implementation,
   semantic coverage, conformance, runtime behavior, and external assumptions;
4. complete a Constitution Check against every applicable principle and v1
   boundary, naming its enforcement mode, evidence, failure disposition, and
   waiver status;
5. define actionable result/diagnostic behavior for invalid, ambiguous,
   unavailable, drifted, and faulted paths; and
6. define the smallest vertical proof, including negative paths and human-review
   obligations.

Task generation MUST convert every applicable MUST and planned proof into an
explicit dependency-ordered task. Analysis MUST expose contradictions, missing
proof, boundary violations, or unjustified complexity before implementation.
Implementation MUST stop and return to specification or planning when it
discovers material ambiguity, changed authority, hidden dependency, broadened
effects, unsupported determinism, or a violated constitutional boundary.

## Governance

This constitution is the highest repository governance for Program Kit
specifications, plans, tasks, source, tests, generated artifacts, extensions,
diagnostics, documentation, and contributor workflows. More specific accepted
artifacts MAY add constraints but MUST NOT weaken or silently contradict it.
Historical Program Kit code and archived designs are prior art, not authority.

An amendment requires explicit human approval of the exact change and MUST
record its rationale, affected principles, compatibility and scope impact,
enforcement changes, and semantic version:

- **MAJOR** for removing or incompatibly redefining a principle, authority
  boundary, non-waivable invariant, or product identity;
- **MINOR** for adding a principle or materially expanding a governed obligation
  or supported boundary; and
- **PATCH** for a non-semantic clarification that changes no obligation.

Every specification, plan, task set, and pull request MUST demonstrate
constitutional compliance. Reviewers MUST reject undocumented exceptions,
evidence overclaims, and implementation that uses momentum to redefine accepted
intent. When instructions conflict, the interpretation preserving human
authority, consumer-owned meaning, exact contracts, fail-closed integrity,
actionable diagnostics, runtime isolation, and independent bootstrap prevails.
If a material conflict remains, work MUST stop for human resolution.

**Version**: 1.0.0 | **Ratified**: 2026-08-01 | **Last Amended**: 2026-08-01

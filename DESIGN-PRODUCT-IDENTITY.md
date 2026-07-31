---
artifact-kind: program-kit-design-category
category: product-identity
status: closed
last-updated: 2026-07-31
active-batch: none
parent-ledger: DESIGN.md
---

# Program Kit Design — Product Identity


### 7.1 Category objective

Converge on what Program Kit is, whom it serves, the promise that governs
tradeoffs, the authors and consumers of its semantic input, its initial
ecosystem boundary, its first-hour proof of value, and its deliberate non-goals.

The category is reopened to determine whether Program Kit is also the common,
model-neutral development protocol that removes duplicated AI foundations from
individual applications and makes governed features portable through reusable
target adapters.

### 7.2 Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `PID-B01` | `PID-001`, `PID-002`, `PID-008` | `completed` | Governing identity, promise, and Spec Kit boundary accepted. |
| `PID-B02` | `PID-003`–`PID-005` | `completed` | Authorship, ecosystem scope, and first-hour proof accepted. |
| `PID-B03` | `PID-006`–`PID-007` | `completed` | Deliberate refusals and toolchain identity accepted. |
| `PID-B04` | `PID-009`–`PID-011` | `completed` | Public contract, authority precedence, and integration resolution accepted. |
| `PID-B05` | `PID-012`–`PID-019` | `completed` | Provider-neutral development, instruction ownership, portable software definitions, deterministic capability mappings, canonical platform contracts, and honest compatibility guarantees accepted. |

### 7.3 Product identity questions and decision records

#### PID-001 — Governing product identity

- **Status:** `accepted`
- **Question:** Is Program Kit primarily a semantic compiler/toolchain, an
  SDK/framework, or both? If these identities conflict, which one governs the
  design tradeoff?
- **Why it matters:** This determines whether authored semantics and compiled
  evidence lead the architecture, or whether runtime APIs and framework
  ergonomics do.
- **Human input:** Program Kit is a modular software-development tool that takes
  human intent and produces semi-deterministic, bounded software components that
  evaluate against a contract. When CLI, compiler, SDK, framework, and workflow
  concerns compete, the governing identity is the human contributor in a
  human-led AI session using Spec Kit.
- **Agent synthesis:** The answer is coherent when separated into product
  category and governing authority. The product category is a human-led,
  AI-assisted modular software-development tool; its outputs are bounded,
  contract-evaluated components. The human contributor has final authority, and
  the other technical surfaces serve that human-led workflow.
- **Consequences and tensions:** "Using Spec Kit" should currently be interpreted
  as the way Program Kit itself is developed, because consumers should use the
  integrated Program Kit experience without a second CLI. "Semi-deterministic"
  and the kind of contract used for evaluation remain open questions.
- **Accepted decision:** `DEC-003` captures the product identity and its
  governing human authority.

#### PID-002 — Governing product promise

- **Status:** `accepted`
- **Question:** What is the single most important promise Program Kit must keep:
  reusable features, deterministic system construction, change and migration
  safety, reliable understanding for AI agents, or another promise? The other
  benefits can remain important, but which one wins when they compete?
- **Why it matters:** A product with several equal primary promises cannot make
  hard scope or architecture decisions consistently.
- **Human input:** Program Kit fails if one product built with Program Kit cannot
  be integrated seamlessly with another Program Kit-built product, or if the
  integration between them cannot be resolved. Resolvable integration is the
  proposed non-negotiable promise.
- **Agent synthesis:** The strongest safe formulation is governed integration
  resolution. Program Kit must understand enough of each bounded component's
  contracts and dependencies to determine direct compatibility, produce an
  explicit adapter or migration path, or return a precise contract-backed
  incompatibility result. Ambiguous incompatibility is always product failure.
- **Consequences and tensions:** Proven irreconcilability counts as a governed
  resolution; universal composability is not promised. Ambiguous incompatibility
  or a result without actionable evidence remains product failure.
- **Accepted decision:** `DEC-004` records governed integration resolution as
  the non-negotiable promise.

#### PID-003 — Authors of canonical semantic input

- **Status:** `accepted`
- **Question:** Who is expected to author the canonical semantic input:
  architects, developers, domain experts, AI agents, or a defined collaboration
  among them? Who has final authority when their inputs disagree?
- **Why it matters:** This governs language ergonomics, validation, approvals,
  provenance, diagnostics, and how much judgment automation may exercise.
- **Human input:** The recommended collaborative authorship model was accepted.
- **Agent synthesis:** Architects, developers, domain experts, and AI agents may
  contribute. AI may propose, translate, analyze, and implement; the human owns
  intent and approves identity-forming changes. Currently accepted contracts
  govern admitted outputs.
- **Consequences and tensions:** A human changes a conflicting outcome by
  explicitly revising and reaccepting its contract, not by silently bypassing it.
- **Accepted decision:** `DEC-005`.

#### PID-004 — Initial ecosystem boundary

- **Status:** `accepted`
- **Question:** Is the first product deliberately .NET-specific, or must its
  semantic core be ecosystem-independent from day one even if the first
  projections target .NET?
- **Why it matters:** Premature neutrality can weaken the first proof, while an
  accidental .NET worldview can prevent the intended semantic portability.
- **Human input:** The recommended .NET-first boundary was accepted.
- **Agent synthesis:** Program Kit v1 implements .NET projections while its
  semantic contracts avoid unnecessary .NET-specific meaning.
- **Consequences and tensions:** Multi-ecosystem implementation is out of scope;
  CLR and MSBuild concepts must not accidentally become universal semantics.
- **Accepted decision:** `DEC-006`.

#### PID-005 — First-hour proof of value

- **Status:** `accepted`
- **Question:** What must a consumer accomplish in their first hour with Program
  Kit for the product to have proved that it is useful and meaningfully
  different from ordinary .NET tooling or a template generator?
- **Why it matters:** This defines the earliest honest vertical slice and keeps
  the redesign anchored in observable user value.
- **Human input:** The recommended first-hour proof was accepted.
- **Agent synthesis:** Within one hour, a consumer can express a software goal;
  obtain a linked design, work unit, implementation plan, and bounded component
  contract; implement a real .NET component; evaluate it with actionable
  diagnostics; attempt integration with another component and receive a
  governed resolution; and repeat deterministic portions without drift.
- **Consequences and tensions:** Exact commands, schemas, and examples are
  deferred to Consumer Planning and the First Vertical Slice. The proof must
  demonstrate governed semantics and integration, not merely template output.
- **Accepted decision:** `DEC-007`.

#### PID-006 — Deliberate first-major-version refusals

- **Status:** `accepted`
- **Question:** What must Program Kit explicitly refuse to do in its first major
  version, even if doing it would be attractive or impressive?
- **Why it matters:** Refusals protect the product boundary and prevent future
  ambitions from obscuring the foundational proof.
- **Human input:** The recommended first-major-version refusals were accepted.
- **Agent synthesis:** Program Kit v1 refuses autonomous invention or approval
  of consumer semantics; forced universal composability; silent, best-effort,
  or ambiguous integration; ambient extension discovery or unpinned selection;
  a built-in general business-domain model; multi-ecosystem implementation;
  runtime dependency on development-session tooling; and self-hosting during
  the Spec Kit-led redesign.
- **Consequences and tensions:** These refusals constrain implementation without
  preventing later, evidence-backed expansion. Future self-hosting remains a
  separate governance decision.
- **Accepted decision:** `DEC-008`.

#### PID-007 — Programming language or language toolchain

- **Status:** `accepted`
- **Question:** Is Program Kit itself the programming language, or is it the
  compiler/toolchain for a separately named semantic language or model?
- **Why it matters:** This affects terminology, user expectations, artifact
  ownership, compatibility, and whether the CLI name and language name should
  remain distinct.
- **Human input:** The recommended toolchain identity was accepted.
- **Agent synthesis:** Program Kit v1 is a semantic development toolchain, not a
  new programming language. A language claim requires a formal grammar, type
  system, compiler semantics, and compatibility model.
- **Consequences and tensions:** The semantic model may evolve toward a language.
- **Accepted decision:** `DEC-009`.

#### PID-008 — Responsibility boundary with Spec Kit

- **Status:** `accepted`
- **Origin:** The human first identified scope overlap with Spec Kit, then
  clarified that Program Kit's consumer planning domain remains essential while
  Program Kit's own development process must use Spec Kit rather than
  self-hosting.
- **Revised question:** Are the two known boundaries in `DEC-001` and `DEC-002`
  accurate? The still-unknown internal implementation seam is no longer folded
  into this broad question; it is tracked by `PID-009` and `EXT-012` instead.
- **Why it matters:** Product capability ownership and development methodology
  are different concerns. Conflating them would either impoverish the consumer
  product or recreate the circular self-hosting problem.
- **Human input:** Consumers should install and use Program Kit CLI without also
  installing Spec Kit CLI. Program Kit must expose software design, planning,
  and implementation-plan capabilities. The archived planning domain—including
  work units, roadmaps, implementation-plan artifacts, internal validations,
  component references, and file linking—contains serious product value and
  must not be disregarded. Program Kit may internally extend or reuse Spec Kit
  techniques to deliver this experience. However, Program Kit itself must be
  designed and implemented using Spec Kit, not its own consumer planning
  facilities. The intended consumer outcome is enterprise-grade,
  semi-deterministic software components.
- **Agent synthesis:** Program Kit owns a cohesive consumer product surface; it
  is not merely a downstream tool that begins after a separate Spec Kit session.
  Program Kit's distribution must make its planning and design capabilities
  available without a second CLI installation. Spec Kit may be an internal
  implementation dependency or technique, but that does not automatically make
  Spec Kit's commands, artifact ownership, or lifecycle the public contract.
  The archived planning concepts are prior art to re-evaluate deliberately, not
  functionality to discard and not implementation to copy as source truth.
- **Consequences and tensions:** Two boundaries are now distinct: the consumer
  product boundary and the Program Kit source-development boundary. Public
  artifact schemas, dependency packaging, Spec Kit update policy, and failure
  diagnostics belong to later internal-seam decisions rather than blocking this
  distinction.
- **Accepted decisions:** `DEC-001` and `DEC-002` govern the consumer and
  source-development boundaries. Internal integration remains an extension concern.

#### PID-009 — Public planning contract versus internal engine

- **Status:** `accepted`
- **Origin:** The human requires a single Program Kit CLI consumer experience
  while allowing internal extension or reuse of Spec Kit techniques.
- **Question:** Does Program Kit own stable canonical planning commands and
  artifact contracts with Spec Kit as a replaceable implementation detail, or
  are Spec Kit-compatible commands and artifacts intentionally part of Program
  Kit's public compatibility promise?
- **Why it matters:** A hidden engine and a public protocol impose different
  versioning, migration, packaging, support, and diagnostics obligations.
- **Human input:** The Program Kit-owned public contract was accepted. Consumers
  must not need a separate Spec Kit installation. A possible optional bridge in
  which an existing Spec Kit workflow invokes Program Kit CLI commands should
  be explored only if it adds value without compromising independence.
- **Agent synthesis:** Program Kit owns its public planning commands, canonical
  artifacts, diagnostics, and compatibility promises. Internal Spec Kit reuse
  is pinned and replaceable. A Spec Kit bridge may invoke Program Kit's public,
  non-interactive CLI at explicit handoff points, but remains optional and may
  not become Program Kit's semantic authority.
- **Consequences and tensions:** `EXT-013` records this bridge as a deferred,
  evidence-gated extension rather than a core product commitment.
- **Accepted decision:** `DEC-010`.

#### PID-010 — Human authority versus contract authority

- **Status:** `accepted`
- **Origin:** `PID-001` names the human contributor and human-led AI session as
  the governing identity when technical product surfaces compete.
- **Question:** What is the precedence rule between human authority, accepted
  contracts, the integration promise, workflow ergonomics, and individual
  technical surfaces? May a human override a contract, or must they revise and
  re-accept the contract before Program Kit admits a conflicting result?
- **Why it matters:** Human authority must govern intent without turning
  integrity gates into optional advice.
- **Human input:** The recommended authority hierarchy was accepted.
- **Agent synthesis:** The accepted hierarchy is: the human governs intent and
  may revise accepted contracts; admitted artifacts must still satisfy the
  currently accepted contracts; CLI, compiler, SDK, framework, and workflow
  designs then serve that authority-and-contract model.
- **Accepted decision:** `DEC-005`.

#### PID-011 — Universal composability versus resolved integration

- **Status:** `accepted`
- **Origin:** `PID-002` makes successful integration between Program Kit-built
  products the non-negotiable promise.
- **Question:** Does a precise, evidence-backed result that two contracts are
  irreconcilable count as a resolved integration outcome, or must Program Kit
  guarantee that every pair of Program Kit-built products can ultimately be
  composed through adapters or migrations?
- **Why it matters:** The first promise is strong and feasible; the second may
  require unsafe semantic compromise or constraints so restrictive that they
  defeat modular reuse.
- **Human input:** The governed-resolution recommendation was accepted.
- **Agent synthesis:** Governed resolution means direct composition, an
  explicit adapter or migration, or a precise incompatibility result. The
  product fails when compatibility remains ambiguous or offers no actionable
  resolution—not merely because two valid contracts are intentionally
  irreconcilable.
- **Accepted decision:** `DEC-004`.

### 7.4 Reopened batch: Uniform AI development and portable features

The accepted decisions above remain in force unless this batch explicitly
supersedes one. This new input reopens Product Identity because it adds a
product-level problem and intended network effect that were not captured when
the category was closed.

#### PID-012 — Uniform AI-development protocol as product identity

- **Status:** `accepted`
- **Origin:** The human identified inconsistent, application-local AI
  instructions and development foundations as perhaps the largest problem
  Program Kit should solve.
- **Human input:** Applications built with AI are each developed differently
  because their AI instructions and foundations live inside the application.
  Program Kit should offer a uniform, model-neutral and domain-neutral way to
  develop in a common language, so developers can move between Program Kit-built
  applications and understand how to contribute.
- **Question:** Is a uniform AI-development protocol part of Program Kit's
  primary identity, and how does it relate to the existing non-negotiable promise
  of governed integration resolution?
- **Recommendation:** Expand the identity without replacing `DEC-004`. Program
  Kit standardizes the development protocol through public commands, canonical
  artifacts, identities, lifecycle links, diagnostics, and integration evidence.
  That shared protocol is the means by which contributors and AI sessions work
  consistently; governed integration resolution remains the promise by which
  the result is judged. For now, "common language" means this explicit protocol
  and semantic toolchain, not a claim that Program Kit already has the formal
  programming language required by `DEC-009`.
- **Accepted decision:** `DEC-020`; the consolidated identity wording is
  recorded in section 7.5.

#### PID-013 — Repository-local versus Program Kit-owned AI guidance

- **Status:** `accepted`
- **Origin:** The human wants AI-instruction clutter and duplicated development
  foundations to stop living independently inside every application.
- **Question:** Which information must remain with an application as its
  reviewable source truth, and which reusable instructions and mechanics should
  be supplied by Program Kit?
- **Recommendation:** Program Kit owns versioned development mechanics, reusable
  capability guidance, generation rules, policy engines, diagnostic semantics,
  and provider integrations. Each application retains a thin, declarative,
  reviewable record of its intent, domain semantics, selected policies, targets,
  dependencies, approvals, exceptions, and exact Program Kit inputs. Program Kit
  should be able to materialize the effective guidance and its provenance for
  reproducibility, without copying the reusable instruction corpus into every
  repository.
- **Important tension:** Removing all local truth would replace visible clutter
  with hidden global state and make historical builds difficult to reproduce.
  Keeping generated copies of all generic instructions would preserve the
  duplication problem.
- **Accepted decision:** `DEC-014`; the precise application-local source-truth
  and governed local-guidance boundary is recorded in section 7.5.

#### PID-014 — The portable unit behind the NuGet analogy

- **Status:** `accepted`
- **Origin:** The human compared the desired ecosystem to NuGet and described
  complex products as containers composed from many applications, APIs, and
  technologies.
- **Question:** What is expected to be portable: the development protocol, a
  feature's governed intent and interfaces, its source implementation, its
  generated artifacts, or some combination? In the WordPress example, does
  "translate a feature" mean re-projecting declared intent and contracts or
  transforming an existing .NET implementation?
- **Recommendation:** Promise portability first for governed feature identity,
  declared interfaces, dependency and policy metadata, and integration evidence.
  Target-specific source and runtime artifacts are portable only where an
  explicit adapter declares and validates a mapping. Do not imply that arbitrary
  .NET code can be mechanically converted into an arbitrary ecosystem.
- **Accepted decision:** `DEC-015`; the portable unit is a versioned bundle with
  a canonical root manifest and separately governed linked artifacts.

#### PID-015 — Reusable target-adapter promise

- **Status:** `accepted`
- **Origin:** A WordPress adapter was offered as an example of target knowledge
  implemented once and reused by anyone exporting Program Kit features as
  plugins.
- **Question:** Does a target adapter promise to export every Program Kit feature,
  or only features whose declared capabilities fit a versioned target profile?
- **Recommendation:** An adapter is a deterministic, pinned capability mapping.
  It declares the source concepts and target versions it supports, validates the
  feature against that profile, generates governed target artifacts, and returns
  precise corrective diagnostics or a contract-backed incompatibility result
  for unsupported semantics. Implemented once, it is reusable for every feature
  inside that declared envelope. This is the adapter form of `DEC-004`, not a
  universal-conversion promise.
- **Scope tension:** WordPress and other non-.NET targets can remain future
  stress tests. This does not require changing the accepted .NET-only
  implementation scope of Program Kit v1, but it may impose portability
  requirements on contracts and manifests designed in v1.
- **Accepted decision:** `DEC-016`; deterministic capability mappings are
  explicit, versioned, support-bounded, traceable, and fail closed.

#### PID-016 — AI model and provider neutrality

- **Status:** `accepted`
- **Origin:** The intended development method should work "whatever the model."
- **Question:** Must Program Kit's canonical workflow remain usable through any
  conforming AI provider and also through humans or automation without an AI
  model?
- **Recommendation:** Keep Program Kit's public CLI, artifacts, state
  transitions, policy inputs, and diagnostic schema provider-neutral. Provider
  adapters translate those contracts into model-specific tools or prompting,
  while model, provider, adapter, and version are recorded as execution
  provenance. The deterministic kernel remains operable without a model; AI is a
  collaborating client, not hidden semantic authority.
- **Accepted decision:** `DEC-020`; provider neutrality and non-AI operability
  are synthesized in section 7.5.

#### PID-017 — What contributors may assume across applications

- **Status:** `accepted`
- **Origin:** Developers should contribute more easily to unfamiliar
  Program Kit-built applications because they understand the tool used to
  develop them.
- **Question:** Which development concepts must be uniform across every
  Program Kit-built application, and which must remain consumer-defined?
- **Recommendation:** Standardize capability discovery, lifecycle and artifact
  links, identity and dependency representation, policy selection, generation
  provenance, diagnostic codes and correction guidance, impact and migration
  evidence, and integration outcomes. Do not standardize domain vocabulary,
  application architecture, framework choices, or composition policies unless
  the consumer explicitly adopts a profile.
- **Accepted decision:** `DEC-020`; its contract and guarantee consequences are
  governed by `DEC-016` through `DEC-019`.

### 7.5 Current refinement: deterministic software and canonical platform contracts

This section is the current refinement of `PID-B05`. It records later human
clarification without erasing the initial questions in section 7.4.

#### Clarifications now recorded

- Program Kit is a development-time tool. Its workflow and public contracts are
  AI-provider-neutral.
- Program Kit creates ordinary applications, including UIs, APIs, workers,
  libraries, plugins, configuration, and infrastructure artifacts. A generated
  product has no required AI agent, MCP exposure, or Program Kit runtime
  dependency unless its design explicitly selects one.
- AI-agent hosting, chat exposure, or an agent running Program Kit inside its
  harness may be supported later but is outside the current design.
- Language, runtime, and host mechanics belong to target-specific capabilities.
  CShells is the .NET mechanism for generated components and DI participation;
  another target may use Node modules or another native composition mechanism.
- A WordPress projection is an example of a human invoking a deterministic
  development capability in an AI session to create a plugin from governed
  software they designed and implemented. It is not a universal runtime adapter
  or arbitrary source-to-source converter.
- The desired interoperability layer includes canonical platform contracts for
  recurring software concerns. OpenID Connect is the concrete example: Entra ID,
  Keycloak, and other provider adapters map their mechanics to one governed
  contract so compatible UIs, APIs, middleware, and token flows share stable
  meaning.
- The same philosophy is intended for platform concerns such as APIs,
  middleware, OpenTelemetry, secrets, and configuration. The contract-system
  ownership model is accepted below; exact catalog contents remain later work.

`PID-012`, `PID-016`, and `PID-017` are accepted. The accepted identity
refinement is:

> Program Kit is an AI-provider-neutral software-development tool that turns
> human-approved software definitions into deterministically constructed,
> contract-evaluated applications and supporting artifacts through explicit,
> versioned capabilities. Generated products are ordinary software and require
> neither AI nor Program Kit at runtime unless explicitly selected. Canonical
> platform contracts and target mappings provide governed integration across
> supported implementations.

This wording and the product expression in section 7.6 are governed by
`DEC-020`.

#### Accepted recommendation 1 — Application-local source truth (`PID-013`)

- **Question:** What is the smallest durable Program Kit record that must live
  with an application, and may teams add provider-specific AI instructions
  alongside it?
- **Recommendation:** Keep application intent, domain semantics, selected
  contracts and implementations, target and infrastructure profiles, policy
  choices, approvals, exceptions, dependency references, and exact version pins
  with the application. Keep reusable workflows, capability instructions,
  generators, validators, and provider bindings in versioned Program Kit
  distributions. Record a reproducible effective-capability manifest rather than
  copying their full instruction text into every repository.
- **Accepted decision:** `DEC-014`. Local AI guidance is permitted only as an
  identified, scoped, versioned consumer extension and cannot override Program
  Kit kernel invariants.

#### Accepted recommendation 2 — Canonical portable software definition (`PID-014`)

- **Question:** What exact authored object may one deterministic capability hand
  to another: a design and contract graph, a feature-selection manifest, an
  implementation package, or a defined software definition containing all three?
- **Recommendation:** Define a governed software definition that references
  identity, intended capabilities, selected feature implementations, semantic
  contracts, configuration and infrastructure profiles, target profiles,
  dependencies, policies, source or artifact locations, and evidence. A target
  capability consumes the applicable parts and must report anything it cannot
  map. Source code itself is not universally portable.
- **Example to validate:** A CShells JSON feature selection plus a fully
  identified configuration and infrastructure profile can deterministically
  compile a .NET API using a selected Keycloak implementation of an OpenID
  Connect contract. A future WordPress capability consumes a supported software
  definition and emits a governed plugin.
- **Accepted decision:** `DEC-015`. The portable unit is a versioned bundle with
  a canonical root manifest and separately governed linked design,
  implementation, deployment, and evidence artifacts.

#### Accepted recommendation 3 — Deterministic capability-mapping contract (`PID-015`)

- **Question:** What must every development capability declare so humans and AI
  sessions can invoke it safely and Program Kit can compose it deterministically?
- **Recommendation:** Require stable capability identity and version; accepted
  input contracts and versions; output contracts and artifacts; supported target
  profiles; required tools and dependencies; deterministic and judgment-bearing
  stages; preconditions and postconditions; validation and conformance evidence;
  diagnostic codes with corrective guidance; provenance; compatibility and
  migration rules; and an explicit unsupported result.
- **Accepted decision:** `DEC-016`. Every capability declares this mapping
  contract and may invoke other capabilities only through the same public
  contract; hidden capability coupling is prohibited.

#### Accepted recommendation 4 — Canonical platform contracts (`PID-018`)

- **Status:** `accepted`
- **Origin:** The human wants provider implementations for OpenID Connect and
  other recurring platform concerns to map to global canonical contracts that
  form the glue between software components.
- **Question:** Does Program Kit core own one canonical semantic contract for
  each platform concern, or does it own a contract protocol and registry in
  which versioned first-party, standards-backed, and third-party contract
  families participate? What does "global" mean when standards and provider
  capabilities evolve?
- **Recommendation:** Treat "global" as canonical within the Program Kit
  ecosystem and within an explicitly selected contract family and version.
  Program Kit core owns contract identity, versioning, discovery, selection,
  conformance, compatibility, evidence, and diagnostic mechanics. Separately
  versioned contract packages own the normalized semantics for concerns such as
  OpenID Connect. Provider adapters declare which contract profiles they
  implement and preserve provider-specific capabilities as explicit facets
  rather than collapsing everything into a lowest common denominator.
- **Critical distinction:** OpenID Connect may support a canonical contract
  family. "API," "middleware," "configuration," and "secrets" are broader
  categories that may require several composable contracts rather than one
  universal contract each. External standards should be referenced rather than
  silently redefined.
- **Accepted decision:** `DEC-017`. Core owns the contract system; separately
  versioned packages own platform semantics; Program Kit ships a small
  first-party catalog and permits governed third-party families.

#### SEM-013 — Provider-native intake and canonical normalization

- **Status:** `accepted`
- **Origin:** The human clarified that a provider such as Keycloak exposes a
  consumer-facing contract because every development capability starts from an
  intake and users may describe intent using provider concepts they already
  understand. Once required provider fields are collected, the adapter maps
  that intake to the canonical platform contract.
- **Question:** Must every provider capability distinguish a versioned
  provider-native intake contract from its mapping to a canonical platform
  contract? Must Program Kit also support canonical-first intake in which the
  implementation provider is selected later?
- **Recommendation:** Support both entry paths. Canonical-first intake captures
  provider-neutral intent and permits later provider selection. Provider-first
  intake captures familiar concepts and may bind the selection deliberately.
  The provider capability owns its intake schema, required-field collection,
  version, defaults, and normalization mapping. The canonical contract owns
  shared semantics and invariants. The mapping emits a trace showing every
  supplied, defaulted, derived, transformed, provider-specific, and unmapped
  value. Unrepresentable meaning becomes an explicit extension facet or a
  diagnostic; it is never silently discarded.
- **Migration consequence:** Provider-native intent should remain linked to the
  normalized contract so Program Kit can calculate which meaning is portable
  when changing from Keycloak to Entra ID or another implementation.
- **Accepted decision:** `DEC-016`. Both intake paths are supported;
  provider-first intake binds its provider until explicit migration while all
  portable and provider-specific meaning remains traceable.

#### Accepted recommendation 5A — Compatibility guarantee (`PID-019`)

- **Status:** `accepted`
- **Origin:** The human requires middleware and token exchanges across compatible
  APIs and UIs to remain stable, predictable, and working regardless of whether
  Entra ID, Keycloak, or another provider implements the canonical contract.
- **Question:** What exact guarantee may Program Kit make when external
  providers, credentials, networks, deployment environments, and runtime state
  remain outside its control?
- **Recommendation:** Guarantee deterministic generation and evidence-backed
  conformance for declared contract profiles, mappings, versions, and
  configuration inputs. Before admission, validate both sides of an integration
  and run all applicable static and executable conformance checks. Fail closed
  with corrective diagnostics when the required proof is unavailable. Do not
  promise uninterrupted runtime availability or undocumented provider behavior;
  instead generate explicit health, telemetry, and operational diagnostics where
  the selected contracts require them.
- **Accepted decision:** `DEC-018`. "Always working" means no known or ambiguous
  contract mismatch inside the declared support envelope; it does not promise
  immunity from external runtime failure.

#### Accepted recommendation 5B — Determinism boundary (`DET-010`)

- **Question:** Does "fully deterministic applications" mean that accepted,
  complete, and pinned software definitions produce repeatable graphs, source,
  projects, configuration and infrastructure artifacts, builds, validation, and
  evidence, while human or AI design judgment and environment-driven runtime
  behavior remain outside that deterministic claim?
- **Recommendation:** Use that boundary. Treat secrets and environment values as
  declared parameters, not hidden inputs. Never describe an application's
  business or runtime behavior as deterministic merely because its construction
  was deterministic.
- **Accepted decision:** `DEC-018`; deterministic construction,
  contract-conformant integration, and runtime assurance are distinct claims.

### 7.6 Accepted product expression: human-governed semantic legibility

- **Human input:** "Program Kit enables AI to build software that can truly be
  governed by intent by humans, so that any code implementation can be
  understood by humans semantically without looking at the actual code itself."
  The semantic layer around implementation is intended to make this possible.
- **Assessment:** This is a strong product vision. As a testable promise, "any
  code" and complete understanding without source inspection are too broad.
  Program Kit can govern implementations admitted through its contracts and
  evidence. Semantic legibility supports ordinary design, integration, impact,
  migration, and operational decisions; it does not make debugging, security
  review, performance analysis, or source inspection permanently unnecessary.
- **Accepted product expression:** **AI builds it. Human intent governs it.**
- **Accepted supporting promise:** Every admitted implementation is legible
  through human-approved semantic contracts, traceability, and verifiable
  evidence.
- **Status:** Accepted by `DEC-020`.

#### Accepted recommendation 6 — Semantic legibility and coverage (`SEM-014`)

- **Status:** `accepted`
- **Origin:** The accepted product expression requires humans to understand and
  govern implementation meaning through a semantic layer without routinely
  reading source code.
- **Question:** Which implementation facts must the semantic layer expose for a
  human to govern software confidently, and what evidence proves that relevant
  code behavior is represented rather than omitted or stale?
- **Recommendation:** At minimum, require governed identity and purpose,
  consumers, provided and required interfaces, dependencies, configuration,
  state and side effects, security and operational assumptions, generated and
  owned artifacts, validation evidence, diagnostics, and migration impact where
  applicable. An implementation is admitted only when applicable generators,
  analyzers, tests, and conformance checks link code and artifacts back to those
  declarations. Undeclared, unverified, inferred-only, or drifted behavior
  remains an explicit unknown and may not be presented as understood.
- **Authority rule:** Semantics may be proposed from code, but inferred meaning
  does not become governing intent until a human approves it. Code conformance
  is then evaluated against the accepted semantic contract.
- **Accepted decision:** `DEC-019`. The semantic layer covers governance-relevant
  meaning and admission requires human-approved, traceable, applicable evidence;
  unknown or unverified behavior may not be presented as understood.

### 7.7 Accepted decisions from `PID-B05`

The human explicitly accepted all six consolidated recommendations on
2026-07-31. The preferred product expression and its qualified supporting
promise were accepted with them.

| Decision | Sources | Accepted decision |
|---|---|---|
| `DEC-014` | `PID-013` | Applications retain a thin declarative source of truth for intent, domain semantics, selected contracts, capabilities, implementations, targets, exact versions, configuration and infrastructure profiles, policies, approvals, exceptions, migrations, and effective-capability provenance. Reusable workflows, generators, validators, diagnostics, and generic AI guidance live in versioned Program Kit capabilities. Local guidance is allowed only as an identified, scoped, versioned consumer extension and cannot override kernel invariants. |
| `DEC-015` | `PID-014` | The portable unit is a versioned software-definition bundle with a canonical root manifest and separately governed linked design, implementation, deployment, and evidence artifacts. Source code is a governed artifact, not the canonical portable semantic unit; capabilities consume explicit views of the bundle. |
| `DEC-016` | `PID-015`, `SEM-013` | Capabilities expose explicit, versioned, support-bounded mapping contracts and compose only through public contracts. Canonical-first and provider-first intake are supported. Provider-first intake binds the provider until explicit migration; normalization preserves a trace of supplied, defaulted, derived, transformed, provider-specific, and unmapped meaning and fails closed rather than discarding meaning. |
| `DEC-017` | `PID-018` | Program Kit core owns contract identity, versioning, registration, selection, profiles, compatibility, conformance, evidence, diagnostics, and migration mechanics. Separately versioned packages own platform semantics. Program Kit ships a small first-party platform-contract catalog and permits governed third-party families. Canonical scope is a named family, version, and profile, never an implicit universal lowest common denominator. |
| `DEC-018` | `PID-019`, `DET-010` | Program Kit guarantees deterministic construction from complete, accepted, pinned inputs and evidence-backed contract-conformant integration within declared support profiles. Human or AI judgment precedes acceptance; missing inputs are not guessed; secrets and environment values are declared late-bound parameters. Runtime health and diagnostics are governed where selected, but uninterrupted availability, deterministic business behavior, and external systems are not guaranteed. |
| `DEC-019` | `SEM-014` | An implementation is admitted only when its governance-relevant meaning is human-approved, traceable to its artifacts, and supported by all applicable evidence. Unknown, undeclared, inferred-only, unverified, stale, or drifted behavior may not be presented as semantically understood. Semantic legibility supports governance without making source inspection unnecessary for debugging, security, or performance work. |
| `DEC-020` | `PID-012`, `PID-016`, `PID-017` | Program Kit is an AI-provider-neutral development tool whose generated products are ordinary, deterministically constructed software with no required AI or Program Kit runtime unless selected. Its accepted expression is **AI builds it. Human intent governs it.** Its supporting promise is: **Every admitted implementation is legible through human-approved semantic contracts, traceability, and verifiable evidence.** |

## 8. Accepted software-factory refinement

### PID-020 — Determinism applies within a known construction envelope

**Human input:** Program Kit should focus on building software as a software
factory. It must not claim every software component is deterministic because
human- or AI-authored implementation logic remains nondeterministically
produced. Plumbing, integration, and relationships can be bounded by canonical
contracts, adapters, and projectors where Program Kit knows how to handle the
intent exactly.

**Accepted definition:**

> Program Kit is a human-governed software factory that turns approved intent
> into contract-bounded software. Within an exact supported semantic and
> capability envelope, it constructs plumbing, projections, and integrations
> deterministically. Custom implementation remains explicitly bounded and
> evaluated, while uncertain or unsupported intent remains visible and
> actionable.

Three independent dimensions govern every claim:

1. **Semantic coverage:** whether intent resolves completely to an exact
   canonical contract inside a declared support envelope.
2. **Construction method:** whether an artifact is deterministically projected
   or custom-authored by a human, AI, or external tool.
3. **Conformance:** whether applicable current evidence proves the resulting
   implementation satisfies its contracts.

Intent is classified without conflating those dimensions:

- **covered:** the canonical contract, required approved inputs, capability,
  adapter or projector, provider, target profile, and resolution are exact and
  pinned, so supported construction may proceed deterministically;
- **custom-but-bounded:** Program Kit understands and governs the required
  boundary but does not claim deterministic derivation of the implementation;
  and
- **unresolved or unsupported:** meaning is ambiguous, incomplete, conflicting,
  or outside installed support and remains visible through actionable
  diagnostics rather than being guessed.

Provider discovery is not provider selection. A user need not already know
which providers are installed or supported: the CLI must expose discoverable
capability and provider support information. Construction still requires an
exact selected provider, adapter, versions, profiles, and inputs in the
resolution lock. A proposed or policy-assisted selection becomes authoritative
only through the accepted resolution process.

**Status:** Accepted by `DEC-028` on 2026-07-31.

### Accepted planning consequence

The software-factory identity removed the reason to duplicate Spec Kit's more
mature discovery, specification, planning, and task workflow. Under `DEC-029`,
Program Kit v1 owns no native planning system. It remains independently callable
through exact public factory-operation contracts.

The recommended guided workflow installs Spec Kit separately. After Program
Kit's public CLI is stable, a thin external adapter maps approved Spec Kit work
to Program Kit requests and returns artifacts, evidence, and diagnostics.
`DEC-029` supersedes the planning commitments in `DEC-001` and `DEC-027` and
the prior deferral in `DEC-011`; the historical reasoning remains recorded.

### Accepted runtime and migration scope

Under `DEC-030`, the initial Program Kit CLI is exclusively a development- and
construction-time factory. It may generate and evaluate ordinary software that
runs, but Program Kit provides no runtime, runtime plugin host, deployment
controller, operational-state manager, or runtime semantic interpreter in v1.

Automated migration is also deferred. Exact version mismatches and drift remain
visible and actionable, but migration is designed only after real CLI use
exposes a concrete consumer contract or version-evolution problem.

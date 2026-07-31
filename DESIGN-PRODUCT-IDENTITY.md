---
artifact-kind: program-kit-design-category
category: product-identity
status: active
last-updated: 2026-07-31
active-batch: PID-B05
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
| `PID-B05` | `PID-012`–`PID-017` | `active` | Uniform AI-development protocol, instruction ownership, portable feature unit, target adapters, provider neutrality, and cross-project contributor fluency. |

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

- **Status:** `follow-up`
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
- **Decision needed:** Confirm this relationship or identify which promise should
  govern when workflow uniformity and integration resolution compete.

#### PID-013 — Repository-local versus Program Kit-owned AI guidance

- **Status:** `follow-up`
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
- **Decision needed:** Confirm the thin-local-manifest boundary or state what
  application-specific AI instruction, if any, may exist outside it.

#### PID-014 — The portable unit behind the NuGet analogy

- **Status:** `follow-up`
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
- **Decision needed:** Select the canonical portable unit before Feature Model
  identity, package format, or adapter contracts are finalized.

#### PID-015 — Reusable target-adapter promise

- **Status:** `follow-up`
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
- **Decision needed:** Confirm the capability-profile boundary and whether
  future target portability must constrain v1 contracts.

#### PID-016 — AI model and provider neutrality

- **Status:** `follow-up`
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
- **Decision needed:** Confirm both provider neutrality and non-AI operability,
  or narrow the intended contract.

#### PID-017 — What contributors may assume across applications

- **Status:** `follow-up`
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
- **Decision needed:** Confirm this common-contributor surface and identify any
  missing universal concepts.

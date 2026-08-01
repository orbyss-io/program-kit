---
artifact-kind: program-kit-design-convergence-ledger
status: converged
authority: human-led
implementation-authority: none
created: 2026-07-31
last-updated: 2026-08-01
active-category: none
active-batch: none
constitution-proposal: .specify/memory/constitution.md
---

# Program Kit Design Convergence

## 1. Purpose

This is the durable, repository-root record of the product discovery that must
converge before Program Kit is designed or implemented. It exists so that
questions, answers, contradictions, consequences, and newly discovered
questions survive across sessions.

This ledger is not an implementation specification and does not authorize
implementation. The constitution is also still a proposal. A statement becomes
accepted product design only through the decision process defined below.

## 2. Authority and convergence method

The human product owner has final authority over product intent. The agent may
analyze answers, expose ambiguity, identify conflicts, propose precise wording,
and generate follow-up questions. It may not silently turn an inference into a
decision.

Every discovery item has a stable identifier. Its status is one of:

| Status | Meaning |
|---|---|
| `open` | Asked or queued, with no sufficient answer yet. |
| `answered` | A human answer is recorded, but its consequences have not converged. |
| `follow-up` | The answer created or exposed another blocking question. |
| `candidate-decision` | Precise decision wording is ready for human confirmation. |
| `accepted` | The human explicitly accepted the candidate decision. |
| `rejected` | The human explicitly rejected the candidate decision. |
| `deferred` | Deliberately postponed with a recorded boundary and revisit trigger. |
| `superseded` | Replaced by another identified item; history remains visible. |

The following rules apply:

1. Record human input separately from agent synthesis.
2. Preserve the meaning of human input; quote it when exact wording matters.
3. Record derived implications, tensions, and assumptions as non-authoritative
   until confirmed.
4. Give every emergent question a new stable ID. Never rewrite history to make
   it appear that the question was known earlier.
5. Never mark a decision `accepted` merely because the human answered a
   question. First present the precise decision and its important consequences.
6. Close a category only when it has no blocking `open` or `follow-up` items and
   every candidate decision is accepted or explicitly deferred.
7. If a later answer conflicts with an accepted decision, record the conflict
   and reopen or supersede the decision explicitly.
8. Implementation work begins only after the required product categories and
   the constitution have converged and the human authorizes implementation.

## 3. Evidence, founding intent, and provisional synthesis

Source roles, the recovered founding intent, and non-authoritative synthesis are
recorded in [`DESIGN-FOUNDATIONS.md`](DESIGN-FOUNDATIONS.md).

## 6. Category register

| Category | ID prefix | Status | Known items | Notes |
|---|---:|---|---:|---|
| Product identity | `PID` | `closed` | 20 | Accepted software-factory identity refined by `DEC-028`. |
| Feature model | `FTR` | `closed` | 17 | All four batches are accepted by `DEC-013` and `DEC-021`–`DEC-023`. |
| Semantic language and bounded contexts | `SEM` | `closed` | 14 | All batches are accepted by `DEC-016`, `DEC-019`, and `DEC-024`–`DEC-026`. |
| Consumer planning and delivery | `PLN` | `closed` | 4 | Native planning withdrawn; Spec Kit-to-factory boundary accepted by `DEC-029`. |
| Extensions and composition | `EXT` | `closed` | 13 | All batches are accepted by `DEC-029` and `DEC-031`–`DEC-033`. |
| Determinism and generated artifacts | `DET` | `closed` | 10 | All batches are accepted by `DEC-018`, `DEC-028`, and `DEC-034`–`DEC-036`. |
| Diagnostics and AI guidance | `DIA` | `closed` | 16 | All four batches are accepted by `DEC-037`–`DEC-040`. |
| Dependencies, impact, and migration | `MIG` | `deferred` | 12 | Migration design waits for real consumer version evolution after the CLI is independently usable (`DEC-030`). |
| Governance, enforcement, and self-hosting | `GOV` | `closed` | 12 | All three batches are accepted by `DEC-041`–`DEC-043`. |
| First vertical slice | `VSL` | `closed` | 8 | Both batches are accepted by `DEC-044`–`DEC-045`. |

Counts are a live snapshot, not a quota. New questions are expected.

## 7. Category progression

Product Identity is closed and recorded in
[`DESIGN-PRODUCT-IDENTITY.md`](DESIGN-PRODUCT-IDENTITY.md). The human accepted
the software-factory refinement and qualified deterministic envelope.

Feature Model is closed at its accepted thin target-specific boundary in
[`DESIGN-FEATURE-MODEL.md`](DESIGN-FEATURE-MODEL.md). All four batches are
complete.

Semantic Language and Bounded Contexts is closed in
[`DESIGN-SEMANTIC-LANGUAGE.md`](DESIGN-SEMANTIC-LANGUAGE.md). All three batches
are complete.

Consumer Planning and Delivery is closed in
[`DESIGN-PLANNING.md`](DESIGN-PLANNING.md). Guided planning belongs to Spec Kit;
Program Kit owns independently callable factory-operation contracts.

Extensions and Composition is closed in
[`DESIGN-EXTENSIONS.md`](DESIGN-EXTENSIONS.md). All three batches are complete.

Determinism and Generated Artifacts is closed in
[`DESIGN-DETERMINISM.md`](DESIGN-DETERMINISM.md). All three batches are complete.

Diagnostics and AI Guidance is closed in
[`DESIGN-DIAGNOSTICS.md`](DESIGN-DIAGNOSTICS.md). All four batches are complete.

Governance, Enforcement, and Self-Hosting is closed in
[`DESIGN-GOVERNANCE.md`](DESIGN-GOVERNANCE.md). All three batches are complete.

First Vertical Slice is closed in
[`DESIGN-VERTICAL-SLICE.md`](DESIGN-VERTICAL-SLICE.md). Both batches are complete.
All non-deferred design categories have converged; migration remains deferred.

## 8. Queued question catalog

The complete queued discovery horizon is preserved in
[`DESIGN-QUESTION-CATALOG.md`](DESIGN-QUESTION-CATALOG.md). The live ledger
records active answers, consequences, emergent questions, and decisions.

## 9. Decision register

Decisions `DEC-002`–`DEC-010`, `DEC-013`–`DEC-026`, and `DEC-028`–`DEC-045`
are accepted. `DEC-001`, `DEC-011`, `DEC-012`, and `DEC-027` are superseded.
All non-deferred categories are closed. Migration remains deferred by `DEC-030`.

| Decision ID | Source questions | Status | Decision | Accepted on |
|---|---|---|---|---|
| `DEC-001` | `PID-008` | `superseded` | The one-install native planning commitment was replaced by the Spec Kit-guided external orchestration boundary in `DEC-029`. | — |
| `DEC-002` | `PID-008`, `GOV-001` | `accepted` | Program Kit itself is developed with Spec Kit and does not consume its own planning facilities during this redesign. | 2026-07-31 |
| `DEC-003` | `PID-001` | `accepted` | Program Kit is a human-led, AI-assisted modular software-development tool that translates human intent into bounded, contract-evaluated software components; the human contributor retains final authority. The deterministic construction boundary is refined by `DEC-018`. | 2026-07-31 |
| `DEC-004` | `PID-002`, `PID-011` | `accepted` | Program Kit's non-negotiable promise is governed integration resolution between Program Kit-built products: direct composition, an explicit adapter or migration, or a precise contract-backed incompatibility result; ambiguity is failure. | 2026-07-31 |
| `DEC-005` | `PID-003`, `PID-010` | `accepted` | Humans, domain experts, developers, and AI may collaborate; the human owns intent and identity-forming approval, while admitted outputs must satisfy currently accepted contracts until explicitly revised and reaccepted. | 2026-07-31 |
| `DEC-006` | `PID-004` | `accepted` | Program Kit v1 implements .NET projections while keeping semantic contracts free of unnecessary .NET-specific meaning; multi-ecosystem implementation is out of scope. | 2026-07-31 |
| `DEC-007` | `PID-005`, `VSL-001` | `accepted` | The first-hour proof links intent, design, work, plan, contract, a real .NET component, actionable diagnostics, governed integration resolution, and repeatability evidence. | 2026-07-31 |
| `DEC-008` | `PID-006` | `accepted` | Program Kit v1 refuses autonomous semantic authority, forced universal composability, ambiguous integration, ambient or unpinned selection, built-in business-domain meaning, multi-ecosystem implementation, runtime dependence on development tooling, and self-hosting during the redesign. | 2026-07-31 |
| `DEC-009` | `PID-007` | `accepted` | Program Kit v1 is a semantic development toolchain, not a new programming language; a language claim requires a formal grammar, type system, compiler semantics, and compatibility model. | 2026-07-31 |
| `DEC-010` | `PID-009`, `EXT-012`, `EXT-013` | `accepted` | Program Kit owns independent public commands, artifacts, diagnostics, and compatibility promises; internal Spec Kit reuse is replaceable, and optional Spec Kit integration may invoke only Program Kit's public contract. | 2026-07-31 |
| `DEC-011` | `EXT-013` | `superseded` | The optional-adapter deferral was replaced by `DEC-029`: the adapter is the selected guided-workflow architecture, while its implementation still waits for a stable Program Kit CLI. | — |
| `DEC-012` | `FTR-001`, `FTR-002` | `superseded` | The optional-projection framing overgeneralized the feature model and understated CShells as Program Kit's intended .NET feature mechanism. | — |
| `DEC-013` | `FTR-001`, `FTR-003`, `FTR-004`, `FTR-015`–`FTR-017` | `accepted` | Program Kit uses a thin target-specific feature model: the portable bundle is distinct from implemented features; CShells supplies selected .NET host mechanics; interface, contract, intake, and binding are distinct; relationships are many-to-many; the kernel owns integrity while consumers own architecture; and cross-target reuse uses definitions, contracts, and explicit capabilities rather than a universal runtime model. | 2026-07-31 |
| `DEC-014` | `PID-013` | `accepted` | Applications retain thin declarative intent, selection, profile, policy, migration, and provenance truth; reusable mechanics and generic AI guidance live in versioned Program Kit capabilities; governed local guidance cannot override kernel invariants. | 2026-07-31 |
| `DEC-015` | `PID-014` | `accepted` | The portable unit is a versioned software-definition bundle with a canonical root manifest and separately governed linked design, implementation, deployment, and evidence artifacts; source code is a governed artifact rather than the canonical portable semantic unit. | 2026-07-31 |
| `DEC-016` | `PID-015`, `SEM-013` | `accepted` | Explicit capability contracts support canonical-first and provider-first intake, public-contract-only composition, support-bounded mapping, traceable normalization, provider binding until explicit migration, and fail-closed handling of incomplete or unrepresentable meaning. | 2026-07-31 |
| `DEC-017` | `PID-018` | `accepted` | Core owns contract-system mechanics; separately versioned packages own platform semantics; Program Kit ships a small first-party catalog and permits governed third-party families; canonical scope is always a named family, version, and profile. | 2026-07-31 |
| `DEC-018` | `PID-019`, `DET-010` | `accepted` | Program Kit guarantees deterministic construction from complete accepted pinned inputs and evidence-backed contract-conformant integration within declared profiles, while runtime availability, deterministic business behavior, and external systems remain outside the guarantee. | 2026-07-31 |
| `DEC-019` | `SEM-014` | `accepted` | Implementations are admitted only when governance-relevant meaning is human-approved, traceable, and supported by applicable evidence; unknown or unverified behavior may not be presented as semantically understood. | 2026-07-31 |
| `DEC-020` | `PID-012`, `PID-016`, `PID-017` | `accepted` | Program Kit is an AI-provider-neutral development tool producing ordinary deterministically constructed software with no required AI or Program Kit runtime unless selected. Accepted expression: **AI builds it. Human intent governs it.** | 2026-07-31 |
| `DEC-021` | `FTR-002`, `FTR-005`–`FTR-007` | `accepted` | Program Kit v1 begins with one exact `.NET 10 + CShells 0.0.28` construction profile with role-specific dependencies, explicit activation, conformance evidence, structured diagnostics, and explicit migration. Features may provide or require multiple capability-owned interfaces. Core terms remain non-synonymous, and components carry governed identity distinct from concrete artifacts without duplicating domain contracts. | 2026-07-31 |
| `DEC-022` | `FTR-008`–`FTR-012` | `accepted` | Governed identities are globally unambiguous within authority-owned namespaces and resolve to immutable revisions. Feature semantics and implementation artifacts revise separately. Relations are explicit and contract-typed. Alternative implementations retain distinct identities. Construction selection requires a human-approved request and exact resolution lock; zero or multiple matches yield actionable diagnostics rather than implicit selection. | 2026-07-31 |
| `DEC-023` | `FTR-013`, `FTR-014` | `accepted` | The canonical feature definition is a thin immutable identity-and-reference manifest with explicit dispositions and no duplicated linked records. A bounded component evaluates against an exact named multidimensional evaluation profile. Non-removable kernel gates enforce integrity, closure, provenance, applicability, evidence freshness, and diagnostic truth. Admission requires fresh conformance across every mandatory applicable dimension; all other outcomes remain explicit and actionable. | 2026-07-31 |
| `DEC-024` | `SEM-001`–`SEM-004`, `SEM-007`–`SEM-008` | `accepted` | The semantic layer uses a formal API-neutral typed artifact model, a restricted YAML workspace projection, structured JSON automation projections, and one exact versioned canonical JSON byte profile. V1 definitions are declarative and non-Turing-complete; executable derivation belongs to exact pinned capabilities. Semantic authority is primarily construction-time, generated products have no implicit Program Kit runtime, and optional runtime semantic projections are explicit and purpose-bound. The broader semantic purpose remains, while first-CLI delivery defines only mechanics required by concrete end-to-end workflows and defers unproven semantic-engine machinery. | 2026-07-31 |
| `DEC-025` | `SEM-005`, `SEM-006` | `accepted` | Consumers extend semantics through exact versioned vocabulary packages over a small kernel-owned declarative protocol. Packages own their terms and constraints but cannot redefine kernel invariants or embed executable behavior. Bundles pin package identity, revision, protocol profile, and digest with no ambient discovery or implicit upgrade. Executable validation, mapping, evaluation, migration, and generation remain in separately pinned capabilities. A new vocabulary within supported primitives requires no kernel change; a new primitive requires an explicit protocol and kernel revision. | 2026-07-31 |
| `DEC-026` | `SEM-009`–`SEM-012` | `accepted` | Cross-boundary relationships are separately owned immutable assertions that cannot rewrite endpoint meaning. Identity or digest conflicts fail; semantic differences require an explicit pinned mapping, adapter, or migration with visible loss. There is no global semantic graph as source truth: the kernel resolves and locks a finite graph per operation. A bounded implementation context is the exact operation-scoped closure of semantic references, implementation artifacts, dependencies, policies, approvals, capabilities, evidence, diagnostics, and assertion authorities used for evaluation. | 2026-07-31 |
| `DEC-027` | `PID-008`, `PLN-004`, `GOV-001` | `superseded` | The consumer-facing native planning surface was replaced by the external Spec Kit orchestration boundary in `DEC-029`; the non-self-hosting constraint remains accepted. | — |
| `DEC-028` | `PID-020`, `DET-010`, `SEM-014` | `accepted` | Program Kit is a human-governed software factory that turns approved intent into contract-bounded software. Deterministic construction is claimed only inside an exact supported semantic and capability envelope. Custom implementation remains bounded and evaluated without claiming deterministic derivation; unresolved or unsupported intent remains visible and actionable. Semantic coverage, construction method, and conformance are independent. Provider discovery informs users but never replaces exact accepted selection and a pinned resolution lock. | 2026-07-31 |
| `DEC-029` | `PID-008`, `PID-009`, `PLN-001`–`PLN-004`, `EXT-012`–`EXT-013` | `accepted` | Spec Kit owns the recommended guided discovery, specification, planning, and task workflow. Program Kit v1 owns no native planning system and remains independently callable through exact public factory-operation contracts. A separately installed external adapter, implemented after the Program Kit CLI is stable, maps approved Spec Kit work into Program Kit requests and returns structured results without internal coupling or authority escalation. Other orchestrators may use the same contracts. | 2026-07-31 |
| `DEC-030` | `SEM-007`, `SEM-008`, `MIG-001`–`MIG-012` | `accepted` | Program Kit v1 is exclusively a development- and construction-time factory. It may generate and development-time evaluate ordinary software that runs, but provides no Program Kit runtime, runtime plugin host, deployment controller, operational-state manager, or runtime semantic interpreter. Automated migration design is deferred until an independently usable CLI and real consumer version evolution expose a concrete problem. V1 preserves exact versions and admission artifacts, detects drift or unsupported changes, and returns actionable diagnostics without claiming automatic migration. | 2026-07-31 |
| `DEC-031` | `EXT-001`–`EXT-003` | `accepted` | Normative terminology separates extension bundles, factory operation contracts, executable operation providers, AI-facing session capabilities, declarative vocabulary packages, and provider profiles. V1 kernel invocation has three initial roles: intake mapping, construction, and evaluation. The role set is closed per protocol version but may grow through an explicit revision. Resolution and admission remain kernel mechanics; migration is not a primitive role. Extensions may carry exact vocabularies but cannot invent canonical meaning during execution. | 2026-07-31 |
| `DEC-032` | `EXT-004`–`EXT-007` | `accepted` | Operation providers produce immutable candidate outputs and cannot edit one another's artifacts. Contract-declared contribution seams feed one exact assembler that owns each final generated artifact. Seam contracts own composition, cardinality, conflict, and ordering rules; the kernel enforces them. Meaningful order is explicit and identity-forming. Every executed input resolves exactly in the accepted lock; v1 has no compatibility solver, implicit best match, or automatic upgrade. | 2026-07-31 |
| `DEC-033` | `EXT-008`–`EXT-011` | `accepted` | V1 executes only exact, explicitly registered first-party operation providers shipped with the selected distribution; installation and discovery grant no execution authority, and in-process code carries no sandbox claim. Exact NuGet packages deliver .NET code while canonical extension manifests carry Program Kit semantic identity, contracts, provenance, digests, support, composition, diagnostics, and conformance evidence. Unsupported or incomplete claims remain unavailable. Future third-party or untrusted provider execution requires a proven out-of-process isolation profile. Dynamic loading, a marketplace, trust store, signing infrastructure, and sandbox are outside v1. | 2026-07-31 |
| `DEC-034` | `DET-001`–`DET-003`, `DET-009` | `accepted` | Deterministic construction claims are scoped to exact named reproducibility profiles. Equal construction identities yield byte-identical canonical outputs; portability across platforms or toolchains is claimed only when proven. Results distinguish canonical-byte reproducible, verified-equivalent under an exact named verifier, and custom-bounded with no deterministic derivation claim. Program Kit-owned canonical artifacts require byte reproducibility. Construction identity covers the complete resolved operation closure and every output-affecting input; ambient influence is normalized, explicit, or rejected. | 2026-08-01 |
| `DEC-035` | `DET-004`–`DET-007` | `accepted` | Trust is atomic at the complete artifact-set level: construction stages immutable candidates, validates them, checks live-path preconditions, and issues admission/publication only after complete success. Physical publication is recoverable and partial output is never trusted. Artifacts are generated-owned, seeded-handoff, or consumer-owned, with no mixed generated/editable regions inside a v1 file. Evaluation diagnoses drift without mutation; construction fails closed; repair is separately authorized. Program Kit never silently overwrites, adopts drift, or presents custom bytes as deterministic output. | 2026-08-01 |

| `DEC-036` | `DET-008` | `accepted` | Manifests, locks, receipts, and any future signatures preserve historical identity and authenticity but cannot substitute for unavailable content. While construction is presented as actively supported or reproducible, every identity-forming input, provider, tool artifact, dependency, and required evidence must remain exactly resolvable and digest-verifiable under a declared policy. Eternal retention and repository-local duplication are not required. Missing or expired content makes current reproduction, re-evaluation, or repair explicitly stale or unavailable without rewriting historical receipts. Secrets are never retained as reproducibility inputs. | 2026-08-01 |
| `DEC-037` | `DIA-001`–`DIA-005` | `accepted` | Every running public CLI path returns one versioned structured result envelope with furthest phase and explicit effect state. Machine data is authoritative; human output is a faithful projection; JSON mode emits one clean document; non-canonical execution metadata cannot affect canonical results. V1 outcomes are succeeded, needs-input, blocked, cancelled, and faulted. Diagnostic categories are request, semantic, resolution, policy, conformance, workspace, external, and internal. Results and diagnostics carry stable identities, bounded causes and consequences, rule and subject references, safe expected/observed values, evidence, remediation, and next-action data without guessed fields or raw exception prose. | 2026-08-01 |
| `DEC-038` | `DIA-006`–`DIA-008`, `DIA-015`–`DIA-016` | `accepted` | Remediation is a typed, bounded, preconditioned action proposal, never executable prose or authority. AI automation may act only within a current exact grant independently revalidated by the kernel; identity-forming, selection, dependency, policy, ownership, and out-of-grant publication changes require approval. Every result has one primary disposition: complete, retry, provide-input, request-approval, repair, revise, or stop. Exact explanation resources are structured and offline-resolvable. Needs-input returns a stateless canonical continuation artifact whose authority, exact inputs, lock, workspace, and evidence are fully revalidated on resume. | 2026-08-01 |
| `DEC-039` | `DIA-009`–`DIA-012` | `accepted` | An authority-qualified diagnostic ID's trigger and invariant meaning are permanent and never reused; exact diagnostic catalogs remain independently versioned and digested. Automation consumes IDs and typed fields, never rendered prose. Wording may evolve under exact catalog revision, while material semantic changes require a new ID. V1 ships invariant structured data and English rendering; localization remains exact and pluggable later. Operations retain a complete canonically ordered diagnostic collection with exact duplicate grouping. Any bounded view declares omission counts and a content-bound reference to the full immutable collection without hiding outcome, effect, or disposition causes. | 2026-08-01 |
## 10. Emergent-question register
| `DEC-040` | `DIA-013`–`DIA-014` | `accepted` | Diagnostic disclosure is schema-classified and fail-closed under a non-bypassable kernel floor. Secrets, secret-derived hashes, protected paths, raw external output, exceptions, and stack traces never enter ordinary results; redaction is structured, paths are safe or logical, and sensitive evidence requires separate authority. Every recoverable command-path failure uses a minimal independent fallback to return the most specific safe faulted result with honest effect state. No envelope is promised before process startup, after forced or unrecoverable termination/resource failure, or when the selected output channel cannot be written. | 2026-08-01 |
| `DEC-041` | `GOV-001`–`GOV-004` | `accepted` | Program Kit permanently retains an independent standard .NET and Spec Kit bootstrap without executing itself or trusting self-generated governance. A published CLI may later perform removable, downstream, non-authoritative dogfooding only after explicit recovery, reproducibility, diagnostics, isolation, and human-scope evidence. Humans retain identity, trust, policy, ownership, widened-effect, external-publication, and release decisions while exact grants may pre-authorize bounded deterministic work. Kernel authority comes only from exact scoped grants issued by configured providers and revalidated on use; requesters cannot authorize themselves. The v1 repository-local provider proves record presence and asserted provenance, not cryptographic human identity. | 2026-08-01 |
| `DEC-042` | `GOV-005`–`GOV-009` | `accepted` | Kernel integrity gates are never waivable. Policy exceptions use exact scoped, finite, authority-backed waiver artifacts that remain visibly waived and identity-forming; there is no global suppression or force bypass. Every principle declares executable-invariant, evidence-backed, human-review, or aspirational enforcement and cannot claim more evidence than that mode provides. Human review owns fitness and accepted risk but cannot override kernel invariants. Warnings are permitted only for non-blocking observations or visible approved waivers under an exact locked governance profile; mandatory failed or unevaluated gates block, and profiles cannot downgrade kernel gates or disclosure. | 2026-08-01 |

| `DEC-043` | `GOV-010`–`GOV-012` | `accepted` | V1 is local-first with no secrets in governed outputs, no telemetry/source upload/network by default, exact locked dependencies and sources, complete release provenance, freshness-bound vulnerability/license evidence, and deterministic SBOMs for Program Kit and executable-provider releases. Signing is explicitly deferred. Kernel, CLI, first-party .NET providers, and the initial generated profile target `net10.0` with stable C# and an exact deliberately updated SDK patch. System.Text.Json, JSON Schema, NuGet, SDK-style MSBuild/dotnet, and provider-scoped Roslyn have bounded roles. Source generators, custom build tasks, weaving, reflection discovery, and hidden generation are outside the first CLI. | 2026-08-01 |
| `DEC-044` | `VSL-001`–`VSL-005` | `accepted` | The first slice constructs independent consumer-owned Status component and ASP.NET API bundles. The component supplies a contract, custom-bounded implementation, and CShells feature; the API consumes its exact local package and exposes one endpoint through a provider-owned contribution seam and assembler. The public diagnostics-first flow maps, validates, resolves, constructs, evaluates, publishes, packs, builds/tests, proves repeatability, and diagnoses/repairs drift. Custom code remains consumer-owned, generated plumbing is deterministic, the output has no Program Kit runtime, and larger platform capabilities remain outside the slice. | 2026-08-01 |
| `DEC-045` | `VSL-006`–`VSL-008` | `accepted` | Green tests cannot excuse hard-coded reference semantics, ambient/manual steps, Program Kit runtime coupling, false deterministic claims, weak AI diagnostics, unexplained integration, unreproducibility, public-contract bypass, or bootstrap coupling. The first architect-visible value is a deterministic Integration Resolution Explanation. Every workspace receives a generated-owned canonical `.program-kit/workspace.snapshot.json`, scoped to an exact finite root closure and tracing identity, semantics, bindings, selections, graph, seams, artifacts, ownership, provenance, evidence, gates, waivers, support, and diagnostic state to authoritative sources. It becomes stale visibly and is a reproducible view, not competing truth. | 2026-08-01 |
New items receive the next stable ID within the relevant category and cite the
answer or tension that created them.

| Question ID | Origin | Status | Question |
|---|---|---|---|
| `PID-008` | Human separated Program Kit's consumer capabilities from the workflow used to build Program Kit itself | `accepted` | Governed by `DEC-002` and `DEC-029`: Spec Kit plans; Program Kit builds. |
| `EXT-012` | Program Kit may internally reuse selected Spec Kit techniques | `accepted` | Governed by `DEC-029`: v1 uses no internal Spec Kit product dependency; the adapter remains external. |
| `EXT-013` | Existing Spec Kit users may benefit from invoking Program Kit at explicit handoff points | `accepted` | Governed by `DEC-029`: the later adapter invokes only stable public Program Kit contracts. |
| `PID-009` | Consumers must not install a second CLI while Program Kit may reuse Spec Kit internally | `superseded` | Guided users install Spec Kit separately; Program Kit remains directly callable without it. |
| `DET-010` | Human described generated applications as fully deterministic | `accepted` | Governed by `DEC-018`: deterministic construction and contract-conformant integration are distinct from runtime behavior and availability. |
| `PLN-001` | Archived planning domain retains serious product value | `accepted` | Governed by `DEC-029`: useful ideas remain prior art, but Program Kit v1 owns no native planning vocabulary. |
| `PLN-002` | Archived planning implementation is prior art rather than source truth | `accepted` | Governed by `DEC-029`: the native proposal was withdrawn without importing archived workflow. |
| `PLN-003` | Plans integrate with validations, components, and files | `accepted` | Governed by `DEC-029`: the external adapter maps Spec Kit work to public factory requests and returns results. |
| `PLN-004` | Program Kit enables consumers to design and implement components | `accepted` | Governed by `DEC-029`: Spec Kit orchestrates guided planning; Program Kit performs factory operations. |
| `PID-010` | Human contributor named as governing identity in `PID-001` | `accepted` | Human governs intent; currently accepted contracts govern admitted outputs until explicitly revised and reaccepted. |
| `PID-011` | Resolvable integration named as the non-negotiable promise in `PID-002` | `accepted` | Precise irreconcilability is a resolution; universal composability is not promised. |
| `PID-012` | Per-application AI instructions create inconsistent development methods and contribution friction | `accepted` | Governed by `DEC-020`: Program Kit is an AI-provider-neutral development tool producing ordinary deterministically constructed software. |
| `PID-013` | Reusable AI foundations should not be copied into every application | `accepted` | Governed by `DEC-014`: applications retain thin declarative truth; reusable guidance remains in versioned capabilities. |
| `PID-014` | NuGet analogy and cross-technology composition introduce a portability promise | `accepted` | Governed by `DEC-015`: the portable unit is a versioned software-definition bundle with a canonical root manifest. |
| `PID-015` | Target projection accepted as a deterministic development-capability mapping | `accepted` | Governed by `DEC-016`: capability mappings are explicit, public, support-bounded, traceable, and fail closed. |
| `PID-016` | The common development method should work whatever the AI model | `accepted` | Governed by `DEC-020`: public workflow contracts are provider-neutral and generated products need no AI runtime. |
| `PID-017` | Program Kit familiarity should transfer across otherwise unfamiliar applications | `accepted` | Governed by `DEC-020`: common platform contracts and development mechanics provide cross-application fluency. |
| `PID-018` | Canonical contracts should glue recurring platform concerns across provider implementations | `accepted` | Governed by `DEC-017`: core owns contract mechanics; versioned packages own platform semantics. |
| `PID-019` | Compatible middleware and token exchanges should be stable, predictable, and always working | `accepted` | Governed by `DEC-018`: no ambiguous mismatch inside the declared support envelope; external runtime failure remains possible. |
| `PID-020` | Software-factory identity must not overclaim deterministic implementation | `accepted` | Governed by `DEC-028`: deterministic construction applies only within exact semantic and capability coverage; custom and unresolved intent remain explicit. |
| `SEM-013` | Provider capabilities expose familiar consumer contracts before mapping to canonical contracts | `accepted` | Governed by `DEC-016`: canonical-first and provider-first intake preserve traceable meaning and migration boundaries. |
| `SEM-014` | Human governance should understand admitted implementation meaning through the semantic layer | `accepted` | Governed by `DEC-019`: admission requires human-approved, traceable, applicable evidence. |
| `FTR-014` | Bounded components evaluate against a contract | `accepted` | Governed by `DEC-023`: an exact named evaluation profile supplies applicable dimensions, non-removable kernel gates, structured outcomes, evidence, and remediation. |
| `FTR-015` | The generic contract/implementation/component cardinality model was rejected | `accepted` | Governed by `DEC-013`: feature and interface identities are distinct, relationships may be many-to-many, and consumers may impose stricter cardinality. |
| `FTR-016` | Consumers own architecture rules without control over Program Kit's immutable mechanics | `accepted` | Governed by `DEC-013`: the kernel owns identity, provenance, mapping, evidence, unknown-state, diagnostic, and admission integrity; consumers own architecture. |
| `FTR-017` | Program Kit v1 is specifically .NET/CShells while other targets may be supported later | `accepted` | Governed by `DEC-013`: definitions and contracts cross targets; implementations and runtime mechanics remain target-specific. |

## 11. Session log

### 2026-07-31 — Ledger established

- Recorded the founding product narrative and diagnostics emphasis.
- Established the human-led convergence method and explicit decision states.
- Preserved 100 initial questions across nine categories.
- Activated Product Identity batch `PID-B01` (`PID-001`, `PID-002`, `PID-008`).
- No product-design decision was marked accepted.
- Recorded the human's warning that the archived product crossed into Spec Kit's
  responsibilities. Added `PID-008` for the product boundary and deferred
  `EXT-012` for possible governed composition with Spec Kit techniques.

### 2026-07-31 — Consumer planning boundary refined

- Corrected the earlier assumption that Program Kit necessarily begins after
  Spec Kit planning; Program Kit owns an integrated consumer planning surface.
- Recorded candidate decisions `DEC-001` for the one-install consumer experience
  and `DEC-002` for Spec Kit-only development of Program Kit during the redesign.
- Added Product Identity, Consumer Planning, and semi-determinism follow-ups.
- Did not treat this clarification as an answer to the earlier active batch.

### 2026-07-31 — Product identity answers recorded

- Recorded `PID-001` as answered and created candidate decision `DEC-003`.
- Separated the product category and human authority from the Spec Kit-based
  development method already governed by `DEC-002`.
- Recorded `PID-002` as a follow-up and created candidate `DEC-004` for
  governed integration resolution.
- Revised `PID-008`; it no longer carries the entire internal Spec Kit seam.
- Added `PID-010`, `PID-011`, and `FTR-014` for the remaining ambiguities.
- No candidate decision was marked accepted.

### 2026-07-31 — Product identity closed

- The human explicitly accepted all eight consolidated recommendations.
- Accepted `DEC-001` through `DEC-010`; all eleven Product Identity questions
  are closed.
- Left no active category until the human selects the next discovery category.
- Added `EXT-013` for a possible optional Spec Kit-to-Program Kit bridge.
- Deferred that bridge until standalone Program Kit value is proven; it must
  use only public Program Kit contracts, remain non-circular, and justify its
  cost with measurable workflow value.
- The constitution remains an unratified proposal pending further convergence.

### 2026-07-31 — Feature Model activated

- Accepted `DEC-011`: the Spec Kit adapter is outside the current design and
  may be reconsidered only after Program Kit CLI is independently published.
- Activated Feature Model batch `FTR-B01` with three primitive-defining
  questions; later Feature Model questions remain queued and may be reshaped.

### 2026-07-31 — Feature primitive refined

- Accepted `DEC-012`: CShells remains prior art and selected generation uses a
  versioned projection adapter rather than a canonical core dependency.
- Recorded the human distinction between feature contracts and concrete feature
  implementations, with all semantic dependencies targeting contracts.
- Replaced prescribed messaging mechanisms with a candidate dimensional
  interface-facet model.
- Added `FTR-015` through `FTR-017`; `FTR-003` and `FTR-004` remain follow-ups.

### 2026-07-31 — Feature Model boundary corrected

- The human rejected the generic feature-contract ontology, prescribed
  interface-role taxonomy, bridge-only domain policy, and universal cardinality
  rules as consumer architecture rather than Program Kit mechanics.
- Superseded `DEC-012` and recorded `DEC-013` as a candidate, not an accepted
  decision.
- Reframed Program Kit v1 as a thin .NET/CShells feature identity and governed
  interface boundary with consumer-owned semantic and architecture policies.
- Recorded that consumer rules and adopted defaults cannot override Program
  Kit's immutable deterministic, integrity, provenance, and diagnostic kernel.

### 2026-07-31 — Product Identity reopened for uniform AI development

- Recorded the human's product-level concern that per-application AI instruction
  foundations produce inconsistent development methods, duplicated clutter, and
  contributor friction.
- Reopened Product Identity as batch `PID-B05` and added `PID-012` through
  `PID-017` for the common protocol, local/source-truth boundary, portable
  unit, target adapters, model neutrality, and transferable contributor surface.
- Recorded the NuGet analogy and reusable WordPress adapter as intended ecosystem
  direction while retaining non-.NET targets as future stress tests rather than
  v1 implementation commitments.
- Paused Feature Model batch `FTR-B01` because its identity and adapter fields
  depend on the reopened portability boundary.
- No previously accepted decision was changed, and no new recommendation was
  marked accepted.

### 2026-07-31 — Development/runtime and platform-contract boundary refined

- Recorded that Program Kit is an AI-provider-neutral development tool whose
  outputs are ordinary software with no required AI, MCP, or Program Kit runtime.
- Recorded CShells and DI participation as .NET target mechanics; other targets
  use capability-owned native composition mechanisms.
- Recorded deterministic target projection as an accepted concept while leaving
  the exact capability mapping contract unresolved.
- Added `PID-018` for canonical platform-contract ownership and profiles and
  `PID-019` for the evidence-backed meaning of stable, predictable integration.
- Added `SEM-013` after the human distinguished provider-native consumer intake
  from traceable normalization into a canonical platform contract.
- Reframed `DET-010` around deterministic construction rather than claiming
  deterministic human judgment or runtime behavior.
- Recorded the preferred expression **AI builds it. Human intent governs it.**
  with an evidence-backed promise limited to admitted implementations.
- Added `SEM-014` for semantic coverage, admissibility, and the boundary of
  governance without routine source inspection.
- No new product decision was marked accepted.

### 2026-07-31 — Reopened Product Identity recommendations accepted

- The human explicitly accepted all six consolidated recommendations.
- Accepted `DEC-014` through `DEC-019` for application-local truth, the
  portable software-definition bundle, deterministic capability and intake
  mappings, canonical platform-contract ownership, deterministic construction
  and compatibility guarantees, and semantic admissibility.
- Accepted `DEC-020` for the refined AI-provider-neutral development-tool
  identity and the expression **AI builds it. Human intent governs it.**
- Closed `PID-B05`; all nineteen Product Identity questions are now closed.
- Marked linked `DET-010`, `SEM-013`, and `SEM-014` accepted so later
  category work must preserve their already-set boundaries.
- Resumed Feature Model batch `FTR-B01`; candidate `DEC-013` remains
  unaccepted and requires explicit convergence.

### 2026-07-31 — Thin Feature Model boundary accepted

- The human explicitly accepted all six consolidated `FTR-B01`
  recommendations.
- Accepted `DEC-013` for target-specific implemented features, scoped CShells
  host participation, separate interface/contract/intake/binding vocabulary,
  many-to-many identities, immutable kernel integrity, consumer-owned
  architecture, and software-definition-based cross-target portability.
- Completed `FTR-B01` without selecting exact CShells packages or versions;
  those remain in `FTR-002`.
- Activated `FTR-B02` for the CShells support matrix, exposed-surface
  representation, minimal terminology, and component boundary.

### 2026-07-31 — CShells and component boundary accepted

- The human explicitly accepted all four `FTR-B02` recommendations.
- Accepted `DEC-021` for the exact initial `.NET 10 + CShells 0.0.28` profile,
  explicit activation and migration, capability-owned multiple interfaces,
  non-synonymous core terminology, and separately governed component identity.
- Completed `FTR-B02` and activated `FTR-B03` for identity scope, semantic and
  implementation revisioning, typed relationships, alternative
  implementations, and deterministic selection.

### 2026-07-31 — Feature identity and resolution accepted

- The human explicitly accepted all five `FTR-B03` recommendations.
- Accepted `DEC-022` for authority-scoped globally unambiguous identity,
  separate immutable semantic and implementation revisions, explicit
  contract-typed relations, first-class alternative implementations, and exact
  deterministic resolution locks with actionable ambiguity diagnostics.
- Completed `FTR-B03` and activated final Feature Model batch `FTR-B04` for the
  minimum feature definition and multidimensional component evaluation.

### 2026-07-31 — Feature Model closed

- The human explicitly accepted both `FTR-B04` recommendations.
- Accepted `DEC-023` for the thin immutable feature manifest, explicit
  dispositions, exact evaluation profiles, non-removable kernel admission gates,
  structured dimension outcomes, fresh evidence, and actionable diagnostics.
- Clarified that the kernel is the trusted product core invoked through the CLI
  application layer, not the whole CLI and not an implicit generated-runtime
  dependency.
- Closed Feature Model and activated Semantic Language and Bounded Contexts
  batch `SEM-B01`.

### 2026-07-31 — Semantic representation boundary accepted

- The human explicitly accepted all six `SEM-B01` recommendations.
- Accepted `DEC-024` for the typed artifact model, strict authored and canonical
  projections, declarative boundary, construction-time authority, and optional
  purpose-bound runtime projections.
- Recorded the human's correction that first-CLI pragmatism limits current
  design and implementation depth, not the semantic layer's broader purpose.
- Completed `SEM-B01` and activated `SEM-B02`; its consumer-vocabulary
  recommendations remain unaccepted pending human review.

### 2026-07-31 — Consumer vocabulary boundary accepted

- The human explicitly accepted both `SEM-B02` recommendations.
- Accepted `DEC-025` for versioned consumer vocabulary packages, exact
  resolution, a small declarative kernel protocol, and capability-owned
  executable semantics.
- Completed `SEM-B02` and activated final Semantic Language batch `SEM-B03`.
- Recorded bounded draft recommendations for cross-authority relationships,
  explicit reconciliation, finite graph closure, and evaluation scope.

### 2026-07-31 — Semantic Language closed; Consumer Planning activated

- The human explicitly accepted all four `SEM-B03` recommendations.
- Accepted `DEC-026` for separately owned relationships, explicit
  reconciliation, finite resolved graphs, and bounded implementation contexts.
- Closed Semantic Language and Bounded Contexts with all fourteen questions
  resolved.
- Activated Consumer Planning and Delivery batch `PLN-B01`.
- Recorded the human's explicit boundary that Program Kit offers planning
  through its CLI and capabilities to consumers but does not use that planning
  system to develop itself; Program Kit remains governed by Spec Kit.
- Accepted that boundary as `DEC-027` rather than leaving it as an assumption.
- Reviewed archived planning as non-authoritative prior art and drafted a
  minimal vocabulary rather than restoring its workflow.

### 2026-07-31 — Software-factory identity accepted; planning pivot opened

- Accepted `DEC-028` and the definition of Program Kit as a human-governed
  software factory operating within an exact deterministic construction
  envelope.
- Separated semantic coverage, construction method, and conformance so
  deterministic generation cannot be mistaken for semantic understanding.
- Classified intent as covered, custom-but-bounded, or unresolved/unsupported.
- Recorded that capability and provider discovery must help an uninformed user
  without becoming ambient selection; exact accepted resolution remains pinned.
- Withdrew the unaccepted native planning proposal without deleting its
  reasoning.
- Activated `PLN-B03` with a precise candidate for Spec Kit-owned planning, an
  independently callable Program Kit factory, and a later thin adapter.

### 2026-07-31 — Native planning removed

- The human explicitly accepted the complete `PLN-B03` pivot.
- Accepted `DEC-029`: Spec Kit owns the guided planning workflow; Program Kit
  owns independently callable factory-operation contracts.
- Superseded `DEC-001`, `DEC-011`, and `DEC-027` while preserving their history.
- Closed Consumer Planning and Delivery without implementing a native planning
  vocabulary, lifecycle, or executor.
- Retained operation request, resolution lock, execution receipt, and evaluation
  report as factory protocol artifacts rather than planning artifacts.
- Activated Extensions and Composition without starting Spec Kit adapter design;
  that implementation still waits for a stable Program Kit CLI.

### 2026-07-31 — Runtime and migration deferred

- Accepted `DEC-030` to keep v1 exclusively development- and
  construction-time.
- Program Kit may generate and evaluate software that runs, but owns no runtime
  host, runtime plugin system, deployment state, or operational control plane.
- Deferred the entire migration design until real use of an independently
  working CLI exposes a concrete consumer version-evolution problem.
- V1 still pins exact versions, preserves admissions, detects incompatible
  change and drift, and emits actionable diagnostics.

### 2026-07-31 — Initial factory operation roles accepted

- The human explicitly accepted the factory/session distinction and the three
  initial factory operation roles.
- Accepted `DEC-031` for the normative extension taxonomy, declarative
  vocabulary boundary, and protocol-versioned role set.
- Recorded that additional roles may be introduced deliberately through a later
  protocol revision as real needs emerge.
- Completed `EXT-B01` and activated `EXT-B02` for deterministic contribution,
  ownership, conflict, ordering, and exact-version rules.

### 2026-07-31 — Deterministic extension composition accepted

- The human explicitly accepted all `EXT-B02` recommendations.
- Accepted `DEC-032` for immutable contributions, single-owner artifact
  assembly, contract-owned conflict and ordering rules, and exact locked
  selection without a solver.
- Completed `EXT-B02` and activated final Extensions batch `EXT-B03` for trust,
  isolation, packaging, metadata, diagnostics, and conformance obligations.

### 2026-07-31 — Extensions and Composition closed

- The human explicitly accepted all `EXT-B03` recommendations.
- Accepted `DEC-033` for explicit first-party provider trust, exact NuGet code
  delivery, canonical semantic manifests, mandatory diagnostics, and
  evidence-backed conformance claims.
- Deferred third-party executable loading until a real need justifies and a
  proven out-of-process isolation profile protects it.
- Closed Extensions and Composition and activated Determinism and Generated
  Artifacts batch `DET-B01`.

### 2026-08-01 — Reproducibility contract accepted

- The human explicitly accepted all four `DET-B01` recommendations.
- Accepted `DEC-034` for named reproducibility profiles, distinct
  byte/equivalence/custom claim strengths, and exhaustive construction
  identity.
- Required Program Kit-owned canonical artifacts to be byte reproducible and
  prohibited hidden output-affecting environmental input.
- Completed `DET-B01` and activated `DET-B02` for logical atomicity, generated

### 2026-08-01 — Generated-artifact lifecycle accepted

- The human explicitly accepted all four `DET-B02` recommendations.
- Accepted `DEC-035` for logically atomic artifact sets, recoverable physical
  publication, and explicit generated-owned, seeded-handoff, and consumer-owned
  artifacts.
- Prohibited mixed file ownership and silent overwrite, adoption, or repair of
  drifted generated artifacts.
- Required read-only diagnosis followed by a separately authorized repair.
- Completed `DET-B02` and activated final Determinism batch `DET-B03` for
  retention and evidence sufficiency.

### 2026-08-01 — Determinism and Generated Artifacts closed

- The human accepted the final `DET-B03` recommendation.
- Accepted `DEC-036`: active reproducibility requires every exact referenced
  input and evidence artifact to remain resolvable and digest-verifiable under
  a declared retention policy.
- Rejected both eternal-retention requirements and the claim that manifests,
  hashes, or signatures can substitute for missing bytes.
- Closed Determinism and Generated Artifacts with all ten questions resolved.
- Activated Diagnostics and AI Guidance batch `DIA-B01` for the universal
  operation-result protocol.

### 2026-08-01 — Universal diagnostic result accepted

- The human explicitly accepted all `DIA-B01` recommendations.
- Accepted `DEC-037` for one universal structured result envelope, five closed
  outcomes, eight primary diagnostic categories, explicit effect state, and
  mandatory actionable data.
- Kept human rendering, logs, progress, exit codes, and non-canonical execution
  metadata subordinate to the structured result contract.
- Completed `DIA-B01` and activated `DIA-B02` for typed remediation, session
  disposition, exact explanations, authority-aware automation, and resumable
  input.

### 2026-08-01 — Diagnostic session control accepted

- The human explicitly accepted all `DIA-B02` recommendations.
- Accepted `DEC-038` for typed non-authorizing remediation, exact authority
  revalidation, one primary session disposition, structured offline
  explanations, and stateless resumable input.
- Prohibited raw shell suggestions as execution contracts, inferred authority,
  hidden continuation state, and unbounded agent retry.
- Required continuation resume to revalidate all identity, authority, lock,
  workspace, and evidence preconditions.
- Completed `DIA-B02` and activated `DIA-B03` for catalog compatibility,
  rendering evolution, ordering, grouping, and bounded output.

### 2026-08-01 — Diagnostic catalog contract accepted

- The human explicitly accepted all `DIA-B03` recommendations.
- Accepted `DEC-039` for permanent diagnostic meaning, exact versioned catalogs,
  machine independence from message prose, and deferred pluggable localization.
- Required one complete canonically ordered diagnostic collection, exact
  duplicate grouping, and explicit content-bound retrieval whenever a view is
  truncated.
- Preserved every cause determining outcome, effect state, or disposition in
  bounded AI-facing results.
- Completed `DIA-B03` and activated final Diagnostics batch `DIA-B04` for
  information safety and last-resort host failure.

### 2026-08-01 — Diagnostics and AI Guidance closed

- The human accepted both final `DIA-B04` recommendations.
- Accepted `DEC-040` for schema-governed disclosure, non-bypassable secret and
  protected-path safety, sanitized external failures, and the minimal
  last-resort structured host fault.
- Recorded the honest availability boundary where process startup, forced or
  unrecoverable termination, resource exhaustion, or output-channel failure can
  prevent any result envelope.
- Closed Diagnostics and AI Guidance with all sixteen questions resolved.
- Left Dependencies, Impact, and Migration deferred under `DEC-030` and
  activated Governance, Enforcement, and Self-Hosting batch `GOV-B01`.

### 2026-08-01 — Bootstrap and authority boundary accepted

- The human explicitly accepted all `GOV-B01` recommendations.
- Accepted `DEC-041` for permanent independent bootstrap and only optional,
  downstream, non-authoritative Program Kit dogfooding after explicit evidence.
- Kept identity, trust, policy, ownership, widened effects, publication, and
  release under human authority while allowing exact grants to pre-authorize
  bounded deterministic work.
- Defined kernel authority through exact scoped grants from configured providers
  and recorded the honest identity limitation of the v1 repository-local
  provider.
- Completed `GOV-B01` and activated `GOV-B02` for gates, exact waivers,
  enforcement modes, human review, and warnings.

### 2026-08-01 — Gate and waiver model accepted

- The human explicitly accepted all `GOV-B02` recommendations.
- Accepted `DEC-042` for non-waivable kernel gates, exact finite policy waivers,
  explicit enforcement modes, honest human-review boundaries, and exact warning
  profiles.
- Prohibited global suppression, force bypass, wildcard or non-expiring waivers,
  and profile downgrade of integrity or disclosure.
- Required waived violations to remain visible and every principle to state what
  evidence it can honestly provide.
- Completed `GOV-B02` and activated final Governance batch `GOV-B03` for
  security, privacy, supply chain, .NET target, and bounded technology roles.

### 2026-08-01 — Governance and technology foundation closed

- The human explicitly accepted all `GOV-B03` recommendations.
- Accepted `DEC-043` for the local-first security and supply-chain floor,
  freshness-bound security evidence, release provenance and SBOMs, and an
  explicit no-signing claim in v1.
- Selected .NET 10 LTS with exact reviewed SDK patch updates and no preview
  features.
- Gave System.Text.Json, JSON Schema, NuGet, MSBuild/dotnet, and provider-scoped
  Roslyn bounded roles while excluding hidden generation and convenience-driven
  constitutional dependencies.
- Closed Governance, Enforcement, and Self-Hosting with all twelve questions
  resolved.
- Activated First Vertical Slice batch `VSL-B01`.

### 2026-08-01 — First vertical-slice shape accepted

- The human explicitly accepted all `VSL-B01` recommendations.
- Accepted `DEC-044` for the two-bundle Status component/API proof, exact local
  package integration, diagnostics-first public flow, ASP.NET Core host, and one
  provider-owned HTTP endpoint contribution seam.
- Preserved custom behavior as consumer-owned while deterministic construction
  owns projects, package and CShells plumbing, endpoint assembly, manifests,
  locks, and evidence.
- Deferred authentication, persistence, telemetry, infrastructure, deployment,
  migration, runtime control, marketplaces, and external Spec Kit integration.
- Completed `VSL-B01` and activated the final convergence batch `VSL-B02` for
  semantic product-failure criteria, architect-visible integration explanation,
  and the canonical AI-readable workspace snapshot.

### 2026-08-01 — Design convergence completed

- The human explicitly accepted all final `VSL-B02` recommendations.
- Accepted `DEC-045` for semantic product-failure criteria, the deterministic
  Integration Resolution Explanation, and canonical scoped workspace snapshot.
- Required a one-hour fresh-contributor walkthrough and explicit human product
  review in addition to green automated tests.
- Closed First Vertical Slice and all non-deferred design categories.
- Preserved Dependencies, Impact, and Migration as deliberately deferred under
  `DEC-030`; no unproven migration design was invented to close the ledger.
- Marked the root design and foundations converged and ready for Spec Kit
  constitution synthesis.

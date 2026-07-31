---
artifact-kind: program-kit-design-foundations
status: active
last-updated: 2026-08-01
parent-ledger: DESIGN.md
---

# Program Kit Design Foundations


The following sources inform discovery but have different authority:

| Source | Role | Authority boundary |
|---|---|---|
| Human statements in the Program Kit rebuild conversation | Primary product intent | Authoritative when recorded and subsequently confirmed as a decision. |
| Attached recovered product story, `pasted-text.txt` | Historical problem narrative | Inspiration and evidence of recurring problems; not a specification. |
| `C:\Users\tech_\Code\semanticdomainengine-design-intake` | Advanced future-design stress test | Explicitly non-authoritative for Program Kit and not permission to import its business-domain semantics. |
| Archived Program Kit commit `0cc3950bb75f5704f7b0c58784ba691f942c8a81` | Prior implementation and prior art | Not source truth for the redesign. Preserved on branch and tag `archive/pre-rebuild-2026-07-31`. |
| `.specify/memory/constitution.md` | Initial constitutional synthesis | Proposal only until discovery and ratification converge. |

## 4. Recorded founding intent

These statements faithfully summarize the product intent supplied before this
ledger was created. They are inputs to discovery, not yet a complete accepted
design.

- Program Kit is intended as a real developer tool for architects and software
  developers building and maintaining large, complex, modular software systems.
- Its motivating problem is not merely code generation. Code has become cheap;
  confidence in the semantic correctness, compatibility, impact, and safe
  evolution of generated or changed systems has not.
- Every logical capability is conceived as a feature and therefore as an
  interface, internal, external, or both depending on the feature. The exact
  meaning of "feature" and "interface" still needs convergence.
- A semantic layer should wrap and position features or components
  deterministically, identify their artifacts and relations, and make their
  meaning understandable to other Program Kit-aware tools and AI sessions.
- Domain knowledge is defined by consumers. Consumer-defined logic belongs
  within a bounded implementation context; Program Kit must provide reusable,
  domain-neutral mechanics rather than invent consumer-domain meaning.
- Canonical semantic input should produce deterministic contracts, projects,
  hosts, analyzers, gates, document structures, and other governed artifacts.
- Extensions should hook into explicit deterministic seams. The same canonical
  input and pinned inputs should yield the same result. OpenID Connect provider
  adapters such as Keycloak and Auth0 are an illustrative future example, not
  yet a selected first implementation.
- Dependency maps, impact calculation, drift detection, integrity checks, and
  migration planning/execution are central because changes in large systems
  otherwise create unexpected repercussions.
- Governance must detect contradictions and drift at the earliest reliable
  point, including through compiler, Roslyn, MSBuild, schema, architectural, or
  other static gates where appropriate.
- Program Kit must always return meaningful feedback to an AI session using it.
  A stable diagnostics catalog and corrective guidance are core product
  behavior, not incidental error handling.
- The previous implementation contained valuable problem discovery but was
  shaky, overly restrictive in places, and sometimes masked the actual intent.
  It is prior art, not the redesign's source truth.
- Program Kit previously used itself and thereby created a circular dependency.
  The redesign starts from Spec Kit and must not casually restore self-hosting.
- The archived Program Kit also attempted discovery, specification, planning, or
  convergence work that may properly belong to Spec Kit. The redesign must not
  preserve those responsibilities merely because the old implementation had
  them. Program Kit's identity must state clearly what it is and what it is not.
- A possible future integration is for Program Kit to export explicitly defined
  capabilities that use selected Spec Kit techniques within a governed flow and
  combine them with Program Kit CLI extensions or other Program Kit mechanics.
  This is an exploration candidate, not an accepted responsibility or design.
- AI-assisted applications commonly keep their development instructions and
  foundational guidance inside each application. This creates duplicated prompt
  and instruction clutter, inconsistent development methods, and a steep
  contribution cost when developers move between applications.
- Program Kit is intended to provide a model-neutral and domain-neutral common
  development protocol so human developers and AI sessions can recognize how a
  Program Kit-built application is designed, changed, validated, diagnosed, and
  integrated without every repository reinventing that foundation.
- The desired ecosystem effect resembles package management at a broader
  feature level: complex products compose many applications, APIs, and
  technologies, while reusable target adapters encode integration knowledge
  once. A future WordPress adapter that projects supported Program Kit features
  into governed plugins is an illustrative stress test, not a v1 commitment.
- Program Kit's AI-provider-neutral workflow is a development-time concern.
  Generated products are ordinary software and need no AI agent, MCP surface, or
  Program Kit runtime unless explicitly selected.
- Target composition mechanics are capability-owned: CShells and DI
  participation for .NET are one mechanism; module loading or other native
  patterns apply to other targets.
- Canonical platform contracts are intended to normalize recurring technical
  concerns across implementations. Entra ID, Keycloak, and other providers
  should map to a versioned OpenID Connect contract so compatible UIs, APIs,
  middleware, and token flows share governed meaning.
- APIs, middleware, OpenTelemetry, secrets, and configuration are additional
  platform-contract candidates. Their exact contract families, ownership,
  conformance profiles, and guarantee envelopes remain unresolved.
- Provider capabilities may expose provider-native consumer intake contracts so
  users can express intent through familiar concepts. Required input is collected
  and validated before a traceable mapping into the canonical platform contract.
  Provider-first and canonical-first intent paths, lossless normalization,
  provider-specific extension facets, and migration behavior still need
  convergence.
- The preferred product expression is "AI builds it. Human intent governs it."
  Its supporting promise is that every admitted implementation is legible through
  human-approved semantic contracts, traceability, and verifiable evidence.
  "Admitted" is essential: the semantic layer does not claim complete knowledge
  of arbitrary, undeclared, unverified, inferred-only, stale, or drifted code.

## 5. Accepted foundations and provisional synthesis

Items 1 through 3 and 6 through 31 are accepted decisions governed by the
decision register in `DESIGN.md`. Items 4 and 5 remain provisional until their
respective categories converge.

1. Program Kit is a human-led, AI-assisted modular software-development tool
   that translates human intent into bounded, contract-evaluated software.
   Construction becomes deterministic after the required intent is accepted and
   all construction inputs are complete and pinned.
2. Its non-negotiable promise is governed integration resolution between
   Program Kit-built products: direct compatibility, an explicit adapter or
   migration, or a precise contract-backed incompatibility result.
3. Program Kit uses a thin target-specific feature model. A feature is an
   implemented unit distinct from the portable software-definition bundle.
   CShells supplies selected .NET host-participation mechanics without becoming
   a universal runtime abstraction. Interface, contract, intake, and binding are
   distinct; feature and interface relations may be many-to-many. The kernel
   owns identity, provenance, mapping, evidence, unknown-state, diagnostic, and
   admission integrity. Consumers own architecture and may impose stricter
   composition and cardinality policies.
   Program Kit v1 begins with one exact `.NET 10 + CShells 0.0.28` construction
   profile with role-specific feature and host dependencies, explicit
   activation, conformance evidence, structured diagnostics, and explicit
   migration. Features may expose multiple capability-owned interfaces.
   Components carry governed composition and delivery identity independently
   from their concrete package, project, assembly, container, or other artifacts.
   Governed identities are authority-scoped and globally unambiguous without a
   central registry; construction resolves exact immutable revisions. Semantic
   feature revisions and implementation revisions are distinct. Feature
   relations are explicit and contract-typed rather than inferred from source
   mechanics. Multiple components may satisfy the same contract while retaining
   distinct identities. Construction uses a human-approved request and an exact
   resolution lock; unavailable or ambiguous selection fails with actionable
   diagnostics.
   The canonical feature definition is a thin immutable identity-and-reference
   manifest. It records explicit dispositions without duplicating contracts,
   artifacts, evidence, diagnostics, or migrations. A bounded component is
   admitted through an exact named multidimensional evaluation profile with
   non-removable kernel integrity gates, fresh evidence, structured outcomes,
   and actionable remediation.
   The Program Kit kernel is the actual trusted core software built and executed
   as part of the product. It owns non-bypassable invariant and admission
   mechanics. The CLI is the primary public application layer that invokes and
   exposes kernel-controlled workflows; capabilities and providers execute
   around it through governed contracts. Neither the kernel nor CLI becomes an
   implicit runtime dependency of generated products.
4. Deterministic mechanisms should be executable code; consumer-owned semantics
   should be explicit, typed, versioned, and canonical.
5. Extension discovery and selection should be explicit and pinned rather than
   ambient, order-dependent, or based on an implicit "best match."
6. Unknown, incomplete, incompatible, and unavailable states should remain
   explicit. They should never be disguised as success or guessed into
   certainty.
7. Generated runtime outputs should remain independent of Program Kit's
   development-session capabilities.
8. Product capability ownership and development method are separate boundaries.
   Spec Kit owns the recommended human-led discovery, specification, planning,
   and task workflow. Program Kit owns independently callable public
   factory-operation contracts, construction, artifacts, diagnostics, and
   compatibility results. Program Kit's repository uses Spec Kit directly and
   remains non-self-hosted.
   A separately installed external adapter, implemented only after the Program
   Kit CLI is stable, maps approved Spec Kit work into public Program Kit
   requests and returns structured results. It cannot make Program Kit depend
   internally on Spec Kit or bypass kernel gates. Other orchestrators may invoke
   the same factory contracts. Program Kit v1 owns no native goals, roadmaps,
   implementation plans, work units, task readiness, or planning lifecycle.
9. Applications retain a thin declarative source of truth for human intent,
   domain semantics, selections, profiles, policies, approvals, exceptions,
   migrations, and effective-capability provenance. Reusable mechanics and
   generic AI guidance remain in versioned Program Kit capabilities. Local
   guidance is governed and cannot override kernel invariants.
10. The portable unit is a versioned software-definition bundle with a canonical
    root manifest and separately governed linked design, implementation,
    deployment, and evidence artifacts. Source code is governed but is not the
    canonical portable semantic unit.
11. Capabilities expose explicit, versioned, support-bounded public contracts.
    Canonical-first and provider-first intake are both supported; provider-first
    selection binds until explicit migration. Every normalization is traceable
    and fails closed rather than silently losing meaning.
12. Program Kit core owns contract-system mechanics. Separately versioned
    packages own platform semantics. Program Kit ships a small first-party
    platform-contract catalog and permits governed third-party families.
    Canonical scope always names a contract family, version, and profile.
13. Complete, accepted, pinned inputs deterministically construct software and
    produce evidence-backed contract-conformant integration inside declared
    support profiles. Runtime availability, deterministic business behavior, and
    external systems are outside that guarantee.
14. An implementation is admitted only when its governance-relevant meaning is
    human-approved, traceable to artifacts, and supported by applicable
    evidence. Unknown, undeclared, inferred-only, unverified, stale, or drifted
    behavior may not be presented as understood.
15. Program Kit is AI-provider-neutral and produces ordinary software with no
    required AI or Program Kit runtime unless selected. Its accepted expression
    is **AI builds it. Human intent governs it.** Every admitted implementation
    is legible through human-approved semantic contracts, traceability, and
    verifiable evidence.
16. Program Kit represents governed meaning through a formal, API-neutral typed
    artifact model. V1 provides a restricted YAML workspace projection,
    structured JSON automation projections, and one exact canonical JSON byte
    profile. Semantic definitions remain declarative and non-Turing-complete;
    executable derivation belongs to explicit pinned capabilities.
    Semantic authority is primarily a development- and construction-time
    concern. Generated products have no implicit Program Kit runtime dependency.
    A purpose-bound runtime semantic projection and interpreter remains a
    possible future product selection, but `DEC-030` explicitly defers it
    beyond v1.
    The semantic layer retains its broader purpose of making admitted software
    legible and governable through human-approved meaning. For the first CLI,
    only mechanics required by concrete, end-to-end testable workflows are
    designed and implemented. Reconstruction, generalized authority systems,
    comprehensive lifecycle engines, global knowledge graphs, inference
    platforms, and general semantic runtimes are deferred until a product
    workflow proves their need; they are not permanently prohibited.
17. Consumers and third parties may extend semantic vocabulary through exact,
    versioned packages over a small kernel-owned declarative protocol.
    Vocabulary packages own their terms, fields, relations, and constraints but
    cannot redefine kernel invariants or embed executable behavior. The same
    package mechanics apply to first-party platform-contract vocabularies.
    Software-definition bundles pin vocabulary identity, revision, protocol
    profile, and digest; discovery and upgrade are never ambient. Executable
    validation, mapping, evaluation, migration, and generation belong to
    separately pinned capabilities that cannot mutate approved canonical
    meaning or bypass kernel gates. New vocabularies using supported primitives
    require no kernel change; genuinely new primitives require an explicit
    protocol and kernel revision.
18. Cross-boundary relationships are separately owned immutable assertions and
    cannot rewrite endpoint meaning. Conflicting content for the same identity
    and revision fails integrity; differing valid semantics require an explicit,
    pinned mapping, adapter, or migration with any loss made visible.
    Program Kit does not maintain a global semantic graph as source truth. The
    kernel resolves a finite exact graph for one operation and records its lock.
    A bounded implementation context is that operation's exact closure across
    semantic references, implementation artifacts, dependencies, policies,
    approvals, mappings, capabilities, evidence, diagnostics, and assertion
    authorities. It produces a canonical context descriptor and separate
    evaluation report. It is not a runtime container, DDD framework, security
    sandbox, global graph service, or lifecycle engine.
19. Program Kit is a human-governed software factory that turns approved intent
    into contract-bounded software. Deterministic construction is claimed only
    when semantic intent, required inputs, capability, adapter or projector,
    provider, target profile, and resolution are exact, supported, accepted, and
    pinned. Plumbing, projections, and integrations may then be constructed
    deterministically inside that envelope.
    Custom-authored implementation remains explicitly bounded and evaluated
    without claiming deterministic derivation. Ambiguous, incomplete,
    conflicting, or unsupported intent remains visible and actionable.
    Semantic coverage, construction method, and conformance are independent
    dimensions.
    Provider and capability support must be discoverable to users who do not
    know what is installed, but discovery never authorizes ambient selection.
    Construction uses an exact accepted selection and records it in the
    resolution lock.
20. Program Kit v1 is exclusively a development- and construction-time factory.
    It may generate and development-time evaluate ordinary software that runs,
    but it provides no Program Kit runtime, runtime plugin host, deployment
    controller, operational-state manager, or runtime semantic interpreter.
    Automated semantic, implementation, deployment, and runtime-data migration
    are also outside current scope. V1 preserves exact versions and admission
    artifacts, detects changed, drifted, or unsupported contracts, and returns
    actionable diagnostics without claiming an automatic migration.
    Revisit runtime support or migration design only after an independently
    usable CLI and real consumer version evolution expose a concrete problem.
21. Normative extension terminology distinguishes an extension bundle
    (distribution), factory operation contract (kernel invocation seam),
    operation provider (executable implementation), session capability
    (human-led AI guidance), vocabulary package (declarative meaning), and
    provider profile (selectable provider binding). Installation grants neither
    activation nor authority.
    V1 has three kernel-invokable factory operation roles: intake mapping,
    construction, and evaluation. Resolution and admission remain kernel
    operations. Migration is neither a primitive role nor current scope.
    Provider, adapter, generator, projector, validator, analyzer, gate, and host
    projection are specializations or compositions rather than independent
    plugin mechanisms.
    The role set is closed for each protocol version, not forever. A genuinely
    new role may be added through an explicit protocol and kernel revision.
    Operation providers and session capabilities remain separately identified,
    activated, trusted, and authorized.
22. Operation providers compose through immutable candidate outputs and
    contract-declared contribution seams. Providers cannot edit one another's
    outputs. One exact assembler owns each final generated artifact.
    The seam contract owns cardinality, compatibility, identity-key, conflict,
    and ordering rules; the kernel enforces them. Installation, discovery,
    filesystem, service-registration, and scheduling order carry no semantic
    authority.
    Meaningful order is explicit and identity-forming. Independent scheduling
    cannot change canonical output. Every executed bundle, operation contract,
    provider, vocabulary, provider profile, target profile, and dependency is
    exact in the accepted resolution lock. V1 has no compatibility solver,
    transitive best-match selection, or automatic upgrade.
23. V1 executes only exact, explicitly registered first-party operation
    providers shipped with its selected distribution. Installation or
    discovery never authorizes execution, and in-process code is trusted rather
    than sandboxed. Executing future third-party or untrusted providers first
    requires a proven out-of-process build-time isolation profile.
    Exact NuGet packages deliver .NET provider code, while a canonical Program
    Kit extension manifest is the semantic authority for identity, contracts,
    provenance, digests, support, composition, and conformance. Ordinary NuGet
    metadata and reflection discovery do not define Program Kit meaning.
    Every advertised support claim requires complete metadata, a stable
    diagnostic namespace and catalog with actionable remediation references,
    and conformance fixtures with expected canonical results. An incomplete
    claim is unavailable. V1 has no dynamic third-party loader, marketplace,
    trust store, signing infrastructure, or sandbox.
24. Every deterministic claim is scoped to an exact named reproducibility
    profile. Equal construction identities under that profile produce
    byte-identical canonical outputs. Cross-platform, architecture, runtime,
    SDK, or toolchain portability is claimed only where fixtures prove it;
    otherwise the relevant identity is an explicit construction input.
    Output claims distinguish canonical-byte reproducible, verified-equivalent
    under an exact named verifier, and custom-bounded with no deterministic
    derivation claim. Program Kit-owned canonical artifacts require byte
    reproducibility. External-tool outputs receive only the strongest claim
    their exact provider profile proves.
    Construction identity covers the complete resolved operation closure and
    every output-affecting input, selection, provider, tool, template, option,
    dependency, policy, and declared environment property. Ambient path,
    culture, time, ordering, random, machine, and environment influence is
    normalized, made explicit, or rejected. Late-bound secret values and
    deployment configuration are excluded from generated output and identity;
    their non-secret parameter contracts may be included.
25. Trust is atomic at the artifact-set level. Construction uses an isolated
    immutable candidate, complete manifest, mandatory validation, and
    collision/precondition checks before publication. Only a completely
    published set receives an admission and publication receipt. Physical
    multi-file writes use atomic replacement where possible and an exact plan,
    journal, and explicit incomplete-publication state otherwise; partial
    output is never trusted.
    Every materialized artifact is Program Kit generated-owned, seeded-handoff,
    or consumer-owned. Generated-owned edits are drift. A seeded artifact is
    created only when absent and becomes custom-bounded consumer work after
    handoff. Consumer-owned artifacts are never modified. V1 has no mixed
    generated/editable regions inside one file; composition uses separate files
    or exact structured seams.
    Evaluation diagnoses exact, missing, modified, stale, colliding, and
    interrupted states without mutation. Construction fails closed rather than
    overwriting them. Repair is a separate authorized construction request,
    and reclassification requires a human-approved definition change. Program
    Kit never silently adopts drift, derives canonical intent from edited
    output, or presents custom bytes as deterministically generated.
26. A construction manifest, resolution lock, and receipt are the authoritative
    historical index of what Program Kit used and claimed, but hashes or a
    future signature cannot reproduce or currently verify missing bytes.
    While an admitted construction is presented as actively supported or
    reproducible, every identity-forming canonical input, provider, template,
    tool artifact, dependency, and applicable evidence remains exactly
    resolvable and digest-verifiable under a declared retention and support
    policy. The bytes need not all be duplicated in the consumer repository.
    Program Kit imposes no eternal retention. Expired policy or unavailable
    content preserves historical receipts but makes current reproduction,
    re-evaluation, or repair explicitly stale or unavailable. Evidence
    freshness determines whether admission remains current.
    Secret values are never retained as reproducibility inputs. V1 requires
    complete digest references, availability preflight, and missing-input
    diagnostics, not signing, archival, garbage-collection, or storage systems.
27. Every running public CLI operation, including pre-admission refusal,
    returns one versioned structured operation-result envelope. It reports the
    furthest phase and an effect state of none, candidate-only, committed, or
    indeterminate. Human output is a faithful projection; JSON mode emits one
    clean document, while logs and progress use another channel. Canonical
    result data excludes random identifiers, timing, and other execution
    metadata.
    Top-level outcomes are succeeded, needs-input, blocked, cancelled, and
    faulted. Warning and change indicators remain orthogonal. There is no
    partial-success or unknown outcome and no success for incomplete bytes.
    Every diagnostic has exactly one primary category: request, semantic,
    resolution, policy, conformance, workspace, external, or internal.
    Providers may add namespaced IDs but not categories without a protocol
    revision.
    Results identify operation, available request/construction identities,
    outcome, phase, effect, changes, artifacts, receipts, evidence,
    diagnostics, and applicable continuation. Diagnostics carry stable
    authority-qualified ID and catalog revision, severity, category, phase,
    occurrence key, typed subjects, rule/contract/profile references, message
    key and safe parameters, bounded cause and consequence, safe expected and
    observed values, remediation and next-action kinds, and applicable evidence
    and documentation. Unknown or unsafe fields are absent or redacted, never
    guessed or replaced by raw exception prose.
28. Diagnostics offer typed remediation descriptors with exact preconditions,
    bounded targets, effect class, authority requirements, postconditions, and
    retry phase. Commands are structured requests or argument arrays, never
    executable prose; patches are digested candidates with target and ownership
    preconditions. A remedy proposes action but grants no authority.
    AI automation may consume only an existing exact human or policy grant
    revalidated by the kernel. Read-only work, isolated candidates, and bounded
    declared-transient retry may normally be automated. Identity, definition,
    provider selection, dependency, policy, exception, ownership, or
    out-of-grant publication changes require approval. Instructions and
    confidence cannot elevate authority.
    Every result has one primary disposition: complete, retry, provide-input,
    request-approval, repair, revise, or stop. Retry is conditional and bounded;
    disposition guides but does not authorize.
    Exact authority-qualified catalog, diagnostic, rule, schema, contract,
    provider, profile, evidence, and documentation references are resolvable
    through a structured offline explanation lookup; web links are optional.
    Migration is referenced only when an exact future migration exists.
    Needs-input returns a canonical stateless continuation artifact with typed
    missing inputs, choices, authority, completed work, and freshness
    preconditions. Resume revalidates the digest, authority, inputs, lock,
    workspace, and evidence. Stale state fails visibly; identity-forming answers
    follow normal lock and approval rules; secrets use secure references. Known
    independent missing fields are requested together, without hidden session
    state or serial question loops.
29. An authority-qualified diagnostic ID's trigger and violated-invariant
    meaning are permanent. It may be deprecated, retired, or replaced but never
    recycled or silently redefined, including across catalog majors. Exact
    catalogs retain immutable identity, revision, schema/protocol version, and
    digest; providers own non-colliding namespaces. Compatibility labels inform
    clients but operation locks select exact catalogs.
    Automation consumes IDs, categories, outcomes, dispositions, and typed
    fields, never rendered prose. Wording may improve within a new catalog
    revision without a new ID; materially changing trigger, invariant, primary
    category, subject semantics, or consequence requires a replacement ID.
    Human output always displays the stable ID.
    V1 ships invariant structured data and an English renderer. Future exact
    language resources may localize prose without changing machine meaning,
    ordering, parsing, or canonical bytes. Operating-system locale has no
    ambient semantic effect.
    Every operation has one complete canonically ordered diagnostic collection.
    Exact duplicates group by ID, subject, rule, parameters, and cause while
    preserving occurrence count and evidence. Distinct subjects, observations,
    rules, or causes remain distinct. A bounded view declares total, returned,
    and omitted counts, grouping, full-collection digest and artifact reference,
    and a content-bound retrieval cursor. Every determinant of outcome, effect,
    or disposition remains represented. Truncation and pagination never alter
    semantics, silently omit diagnostics, or query mutable live state.
30. Every diagnostic value has schema-declared disclosure classification and
    permitted rendering. The kernel enforces a non-bypassable floor; policy may
    only restrict it further. Secrets, tokens, protected environment values,
    secret-derived hashes, unsafe command lines, raw external output,
    exceptions, stack traces, and protected absolute paths never enter ordinary
    results. Allowed paths are repository-relative; otherwise logical subject
    identities and non-enumerating responses are used.
    Redaction is structured with a safe reason and policy/classification
    reference but no reversible placeholder or fingerprint. JSON, human,
    verbose, and debug modes share the disclosure floor. External output is
    untrusted and must pass a declared structured adapter and disclosure policy;
    sensitive detail requires separately authorized protected evidence. Missing
    disclosure metadata fails provider conformance and unknown values are
    withheld.
    Every recoverable command-path failure becomes the most specific structured
    faulted result available. A tiny embedded fallback schema, catalog entry,
    filter, and serializer report the furthest phase and proven effect state
    independently of the normal provider and diagnostic pipeline. Unproven
    state is indeterminate and directs recovery. JSON is buffered before output.
    No envelope is guaranteed when the process cannot start, is forcibly
    terminated, suffers unrecoverable runtime/OS or resource failure, or cannot
    write the selected output channel. These are explicit availability limits;
    no catch-all may conceal them or claim workspace safety.
31. The Program Kit kernel and CLI retain a permanent independent bootstrap:
    repository source builds, tests, repairs, and releases through the standard
    .NET toolchain and Spec Kit workflow without executing Program Kit against
    itself or trusting self-generated governance input. A published CLI may
    later dogfood isolated downstream examples or extensions only after the
    independent build and only as removable verification. Dogfooding cannot
    define or block repair of the constitution, kernel protocols, diagnostics,
    gates, build graph, source, or release authority. A changed rule cannot
    generate or approve its own validity evidence.
    Dogfooding requires a stable independently published CLI, clean independent
    build and recovery proof, reproducibility/drift/publication/diagnostic
    fixtures, non-authoritative subject isolation, and explicit human acceptance
    of exact scope and purpose.
    Humans establish or change product and semantic identity, kernel invariants,
    provider/profile/version/dependency/trust selection, governance and
    exceptions, ownership, destructive or widened effects, external
    publication, releases, and future third-party execution. Approved exact
    grants may pre-authorize bounded deterministic work without repetitive
    confirmation; AI prepares evidence but does not make identity-forming
    decisions.
    Kernel authority is an exact canonical scoped grant from a configured
    provider with identity, issuer assertion, subjects, operations, effects,
    request/lock bindings, conditions, validity, revocation, and provenance.
    Requesters cannot grant or broaden their own authority; every use revalidates
    scope, digest, freshness, and revocation. V1's repository-local provider
    proves reviewable record presence and provenance assertion, not a person's
    cryptographic identity. Stronger authority providers can implement the same
    contract later.

# Program Kit Design Question Catalog

This root-level companion preserves the complete queued discovery horizon for
[`DESIGN.md`](DESIGN.md). Question IDs are stable. Status, human answers,
synthesis, emergent questions, and accepted decisions are recorded in the live
ledger.

## 8. Queued question catalog

These questions preserve the current discovery horizon. Their wording is not
frozen; if an earlier decision invalidates an assumption, retain the ID and
record the revision or supersession rather than silently deleting it.

### 8.1 Feature model

- **FTR-001:** Must every Program Kit-generated .NET feature implement
  `CShells.IFeature`, and is CShells a generated-project dependency, a generator
  dependency, or both?
- **FTR-002:** Which CShells package, generator, syntax, conformance, diagnostics,
  compatibility, and migration versions must Program Kit pin and support?
- **FTR-003:** What is the minimum Program Kit-known feature record for a
  concrete .NET implementation, and which additional validity rules remain
  entirely consumer-owned?
- **FTR-004:** What minimum interface descriptor identifies the semantic
  boundary, connects a feature and consumer, enables impact analysis and
  diagnostics, and runs consumer rules without prescribing roles or mechanisms?
- **FTR-005:** Can one feature expose API, CLI, worker, configuration, event, and
  internal facets at the same time?
- **FTR-006:** How are feature, operation, component, module, package, service,
  extension, and application distinguished?
- **FTR-007:** Is a component only an implementation of one or more features, or
  does a component carry semantic meaning of its own?
- **FTR-008:** At what scope is feature identity unique: repository, product,
  organization, ecosystem, or global?
- **FTR-009:** What creates a new feature version instead of merely a new
  implementation version?
- **FTR-010:** May features be nested, composed, specialized, or inherited, and
  which of those relations are safe?
- **FTR-011:** May two components implement the same feature contract?
- **FTR-012:** If multiple implementations exist, how is one selected without
  ambient discovery or an implicit best-match algorithm?
- **FTR-013:** What is the smallest mandatory feature definition: identity,
  purpose, owner, contracts, dependencies, artifacts, diagnostics, migration,
  and what else?
- **FTR-014:** Which explicit contracts must a bounded component evaluate
  against: semantic, behavioral, API, schema, dependency, integration, policy,
  deployment, or a defined multidimensional contract set?
- **FTR-015:** How are concrete feature identity and interface identity kept
  distinct, and should the kernel permit many-to-many declarations while
  consumers govern cardinality?
- **FTR-016:** Which immutable mechanics and evidence rules belong to the
  Program Kit kernel, which composition rules always belong to consumers, and
  when does an explicitly adopted default profile become enforceable?
- **FTR-017:** How much of the current .NET/CShells feature model must constrain
  a possible future React specialization, if anything beyond the shared
  identity-and-interface philosophy?

### 8.2 Semantic language and bounded contexts

- **SEM-001:** Is the semantic layer a formal grammar and type system with a
  validator/compiler?
- **SEM-002:** What is the primary authored form: C# DSL, JSON, YAML, another
  text language, or an API-neutral model with several projections?
- **SEM-003:** What is the single canonical representation when several authored
  syntaxes express the same semantics?
- **SEM-004:** Must semantic definitions remain declarative and non-Turing
  complete?
- **SEM-005:** May consumers introduce their own semantic types and vocabulary?
- **SEM-006:** If so, how are consumer vocabularies versioned and interpreted
  without changing the Program Kit core?
- **SEM-007:** Does the semantic layer exist only at build time, at runtime, or
  at both stages?
- **SEM-008:** Must runtime artifacts carry the semantic model, or may meaning be
  compiled entirely into code, contracts, metadata, and evidence?
- **SEM-009:** Who owns a relationship between features from different consumers
  or bounded domains?
- **SEM-010:** When semantic definitions disagree, must compilation fail, or can
  an explicit adapter reconcile them?
- **SEM-011:** Is there one global semantic graph or a federation of bounded,
  composable graphs?
- **SEM-012:** What precisely bounds a bounded implementation context: feature
  closure, file, package, dependency boundary, authority boundary, or a defined
  combination?

### 8.3 Extensions and composition

- **EXT-001:** Which extension families are foundational: contributions,
  validators, generators, host projections, providers, adapters, analyzers,
  gates, migrations, or others?
- **EXT-002:** Is the set of extension families itself closed and versioned?
- **EXT-003:** May an extension add semantic vocabulary, or may it only implement
  a seam already defined by the core or consumer?
- **EXT-004:** May one extension modify another extension's output?
- **EXT-005:** When multiple extensions target the same host seam, who owns
  conflict resolution?
- **EXT-006:** Is extension ordering ever meaningful, and if so must it be
  explicit and identity-forming?
- **EXT-007:** Are exact version pins mandatory, or may Program Kit eventually
  use a deterministic compatibility solver?
- **EXT-008:** Are extension implementations trusted build inputs initially?
- **EXT-009:** Is isolation or sandboxing of third-party extensions an eventual
  requirement?
- **EXT-010:** Are extensions ordinary NuGet packages, semantic artifacts, both,
  or neither?
- **EXT-011:** Must every extension ship schemas, diagnostics, compatibility and
  migration rules, and conformance fixtures?
- **EXT-012:** If Program Kit internally reuses or extends selected Spec Kit
  techniques, what are the explicit dependency direction, artifact handoff,
  authority boundary, version pinning, diagnostics, and non-circularity rules
  while Program Kit retains independent public contracts?
- **EXT-013:** This integration is outside the current design. Revisit it only
  after Program Kit CLI is implemented, independently usable, and published.
  Then determine whether an optional Spec Kit adapter can invoke Program Kit's
  public CLI at explicit handoffs while proving measurable value, preserving
  diagnostics, and avoiding duplicate truth, core coupling, or callback cycles.

### 8.4 Determinism and generated artifacts

- **DET-001:** Must equal canonical inputs produce byte-identical output across
  operating systems, runtime versions, architectures, cultures, and paths?
- **DET-002:** Which outputs require byte determinism and which, if any, require
  only semantic equivalence?
- **DET-003:** Which variables are identity-forming inputs: Program Kit version,
  extension catalog and order, platform, formatter, SDK, canonicalization rules,
  and what else?
- **DET-004:** Must generation be atomic, yielding a complete validated artifact
  set or no trusted output?
- **DET-005:** May generated files be edited by consumers?
- **DET-006:** If editing is allowed, how is ownership divided between generated
  and consumer-owned regions without obscuring canonical truth?
- **DET-007:** When generated artifacts drift, should Program Kit regenerate,
  diagnose, propose repair, or fail hard?
- **DET-008:** Must canonical inputs be retained forever, or can a signed
  generation manifest be sufficient evidence?
- **DET-009:** Are deterministic claims always byte-level, or may an explicitly
  named semantic-equivalence claim be made?
- **DET-010:** What does "semi-deterministic" mean operationally: which stages
  may use human or AI judgment, and after which acceptance boundary must
  Program Kit guarantee repeatable mechanics, outputs, validation, and evidence?


### 8.5 Diagnostics and AI guidance

- **DIA-001:** Must even pre-admission failures use the structured diagnostic
  envelope?
- **DIA-002:** Must every CLI operation provide both a machine-readable response
  and a human rendering?
- **DIA-003:** What are the top-level outcome states: success, rejected,
  additional input required, incompatible, unavailable, cancelled, faulted,
  unknown, or others?
- **DIA-004:** How must diagnostics distinguish consumer-intent errors, semantic
  input errors, compatibility failures, Program Kit defects, and external-tool
  failures?
- **DIA-005:** Which fields are mandatory beyond stable ID, severity, subject,
  violated rule, cause, and corrective guidance?
- **DIA-006:** Should corrective guidance include an exact suggested command or
  patch when safe, or only describe the next action?
- **DIA-007:** Which corrections, if any, may an AI agent perform automatically
  without renewed human approval?
- **DIA-008:** How does an outcome tell an agent whether to repair and retry,
  request human input, or stop?
- **DIA-009:** Are diagnostic IDs stable forever, or only within a catalog major
  version?
- **DIA-010:** May diagnostic messages evolve independently of semantic IDs?
- **DIA-011:** Is localization required, allowed, or deliberately excluded from
  the first versions?
- **DIA-012:** How are multiple diagnostics ordered, deduplicated, grouped, and
  safely truncated?
- **DIA-013:** How do diagnostics avoid leaking secrets, protected paths,
  topology, or unauthorized existence information?
- **DIA-014:** Must a crash be converted into a last-resort structured host
  diagnostic?
- **DIA-015:** Should diagnostics link directly to rule documentation, schemas,
  contracts, and applicable migrations?
- **DIA-016:** Is "additional input required" a first-class resumable
  continuation rather than an error?

### 8.6 Dependencies, impact, and migration

- **MIG-001:** Must Program Kit maintain separate semantic, source, project,
  package, runtime, deployment, and external-consumer graph layers?
- **MIG-002:** Which graph is authoritative when graph layers disagree?
- **MIG-003:** How are unknown external consumers registered, represented, and
  prevented from disappearing from impact analysis?
- **MIG-004:** Which edge kinds may form valid cycles, if any?
- **MIG-005:** Is compatibility explicitly multidimensional, such as source,
  binary, behavior, schema, configuration, deployment, and policy?
- **MIG-006:** Must every breaking change have an executable migration?
- **MIG-007:** Does Program Kit execute migrations, or plan, generate, validate,
  and collect evidence for execution by another authority?
- **MIG-008:** Which migration scopes are foundational: source, schema, package,
  configuration, generated artifacts, data, runtime activation, deployment?
- **MIG-009:** Does rollback mean restoration of previous bytes or a new
  corrective migration to a known valid state?
- **MIG-010:** What evidence proves that an allegedly unaffected component truly
  requires no change?
- **MIG-011:** What exact conditions close a migration or impact-analysis scope?
- **MIG-012:** When closure is incomplete, must the entire operation stop, or may
  it return a clearly bounded partial result?

### 8.7 Governance, enforcement, and self-hosting

- **GOV-001:** May Program Kit ever self-host again, or must its foundational
  build remain permanently independent of Program Kit?
- **GOV-002:** If self-hosting may return, what evidence threshold must be met
  first?
- **GOV-003:** Which decisions always require human approval: constitution,
  architecture, plan, publication, migration, work-unit scope, or others?
- **GOV-004:** What form makes approval authoritative: repository record, signed
  decision, organization policy, explicit review, or another mechanism?
- **GOV-005:** May gates ever be suppressed?
- **GOV-006:** If suppression exists, must it be exact, versioned, scoped,
  expiring, and explicitly approved?
- **GOV-007:** Must every constitutional principle eventually have executable
  enforcement?
- **GOV-008:** Which constitutional concerns necessarily remain human-review
  obligations?
- **GOV-009:** Are warnings allowed, or must every governed violation be an
  error under an explicitly selected profile?
- **GOV-010:** Which security, privacy, supply-chain, signing, provenance, and
  SBOM obligations belong in the initial constitution?
- **GOV-011:** Is .NET 10 still the intended initial target?
- **GOV-012:** Which technologies are accepted as foundational: Roslyn, MSBuild,
  NuGet, JSON Schema, source generators, or none until justified by a slice?

### 8.8 First vertical slice

- **VSL-001:** What is the smallest real consumer system that can prove the
  Program Kit thesis?
- **VSL-002:** Should the first slice establish feature definition and
  diagnostics before any host generation?
- **VSL-003:** Should the initial proof flow be: consumer feature definition,
  canonical validation, actionable diagnostics, typed dependency map,
  deterministic .NET project/package projection, repeatability and drift proof,
  then isolated consumer execution?
- **VSL-004:** Should the first host projection be an API, console application,
  worker, package, or something else?
- **VSL-005:** Should the first extension prove OpenID Connect, persistence,
  telemetry, or a deliberately smaller seam?
- **VSL-006:** What would make the first slice a product failure even if all its
  automated tests pass?
- **VSL-007:** What is the first thing an architect should see that ordinary
  .NET tooling does not already provide?
- **VSL-008:** What exact artifact should let a new AI session understand the
  governed system without rereading all source code?

### 8.9 Consumer planning and delivery

- **PLN-001:** What are the canonical planning concepts and lifecycle relations
  among program goals, roadmaps, work units, designs, implementation plans,
  tasks, validation evidence, and completed components?
- **PLN-002:** Which archived planning concepts and artifacts remain valuable
  prior art, which must be re-specified, and which restrictions or
  implementation choices must be discarded?
- **PLN-003:** How do plan artifacts link stably to features, components,
  validations, and files, and how is link drift detected across renames and
  structural changes?
- **PLN-004:** When Program Kit says it helps consumers "implement," does the CLI
  orchestrate agent work and source changes, execute validated plans directly,
  or produce governed implementation artifacts for an external executor?

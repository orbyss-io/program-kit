---
artifact-kind: bootstrap-implementation-plan
artifact-id: pkid:plan:program-kit:baseline
artifact-version: 0.1.0
intended-contract: pkid:schema:program-kit:implementation-plan
intended-contract-version: 1
design-ref-id: pkid:design:program-kit:baseline
design-ref-version: 0.1.0
design-digest: sha256:3c753a417a13f577c588551dbba38d96a18049e34941d8f83cb72e8631630751
review-state: awaiting-human-approval
implementation-status: aspirational
bootstrap-exception: true
---

# Program Kit baseline implementation plan

## 1. Plan authority and entry gate

This is the human-authored bootstrap precursor to the proposed
`implementation-plan/v1` contract. It is separate from the architecture design,
has its own identity and version, and is bound with that design by
`review-manifest.json`.

Implementation may start only after an explicit human approval binds the exact
design and plan SHA-256 values. The first implementation action is to record
that decision as a bootstrap approval record with the principal reference,
separate authority reference, decision evidence/correlation, accepted scope,
conditions, and decision time supplied by the human session. The bootstrap
record is preserved when a normal contract instance is later produced.

Approval authorizes the planned paths and outcomes only. Stop and request renewed
design approval before any material change to package/project boundaries,
dependency direction, canonical representation, identity/digest scheme,
authority model, .NET target, capability scope, fixture scope, or Release Cycle
boundary.

## 2. Exact inputs

| Input | Authority and use |
| --- | --- |
| Human mission in attached `pasted-text.txt` | Primary requested outcomes and non-negotiable boundaries |
| `AGENTS.md` | Repository working and capability-use rules |
| Root and boundary README files | Workspace ownership/dependency source truth |
| `.agents/capabilities/INDEX.md` | Sole capability availability authority |
| Approved `architecture-design.md` digest | Architecture implemented by this plan |
| Human bootstrap approval record | Authority to begin only the accepted scope |
| Installed .NET SDK `10.0.302` | Proposed pinned build SDK, subject to approval |
| NuGet.org packages: `MSTest.Sdk` `4.3.2`, `JsonSchema.Net` `9.3.0`, `Microsoft.Extensions.DependencyInjection` and `.Abstractions` `10.0.10` | Exact external test, schema-validation, and fixture-DI allow-list |
| [JSON Schema Draft 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core) and [Validation](https://json-schema.org/draft/2020-12/json-schema-validation) | Program Kit schema dialect, accessed 2026-07-22 |
| [OpenAPI `3.2.0`](https://spec.openapis.org/oas/v3.2.0.html) plus [official schema iteration `3.2/schema/2025-11-23`](https://spec.openapis.org/oas/3.2/schema/2025-11-23.html) | Exact external authority/input for generated OpenAPI projections, accessed 2026-07-22 |

No sibling repository, machine-local `bin/`/`obj/`, unreviewed plugin folder, or
ambient extension is an input. `program-kit/NuGet.Config` clears ambient sources,
allows only NuGet.org for the named packages, and package lock files bind the
resolved closure. The OpenAPI schema is vendored with source URL, license, and
digest so validation is offline and repeatable. No CShells source is an input in
this baseline.

## 3. Planned output set and canonical ownership

| Output | Canonical representation | Projection/evidence |
| --- | --- | --- |
| Contract shapes | Versioned JSON Schema under `program-kit/schemas/` | Typed .NET views plus schema/model drift tests |
| Architecture designs | Canonical `.json` envelope instance | Deterministic Markdown and dependency graphs |
| Implementation plans | Separate canonical `.json` envelope instance | Deterministic Markdown and optional execution packet |
| Test meaning | Canonical test-specification instances | Execution profiles and digest-bound evidence |
| Approval | Human-supplied canonical approval instance | Markdown receipt; tools never mint approval |
| Development transitions | Canonical development-receipt instances | Human Markdown summaries |
| AI artifact | Schema + invariant template + supplied intent instance | Deterministically assembled instance and tests |
| .NET scaffold | Reviewed design/plan/selection inputs | Generated source with provenance manifest and repeat evidence |
| Capability procedure | `.agents/capabilities/<id>/CAPABILITY.md` | Thin wrapper and exact-byte content package |
| Capability availability | `.agents/capabilities/INDEX.md` | Generated/drift-checked `.agents/capabilities/README.md` |
| Bootstrap history | Files in `program-kit/bootstrap/` | Self-hosted comparison finding; history is not rewritten |

Committed canonical and generated review artifacts must carry owner, contract
version, source/provenance references, canonical representation, digest, and
implementation status. Transient build, package, test, and isolated-consumer
outputs use an ignored explicit artifacts directory or an OS temp directory and
are never durable evidence by themselves.

## 4. Requirement trace

| Requirement | Owning component | Contract/artifact identity | Exact implementation outcome | Dependency/extension impact | Test, fixture, and evidence | Observable acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| `PK-R001` Standalone Kit boundary | Build spine + conformance tests | `pkid:test:program-kit:standalone-boundary` | One Program Kit solution; no engine/Lab/runtime capability reference | Enforces engine -> Kit only | project/package graph tests; isolated restore | Packaged universal consumer has no engine, .NET-kit, CLI, CShells, or agent dependency |
| `PK-R002` Stable artifact identity and integrity | Artifacts | `pkid:schema:program-kit:artifact-envelope` | PKID grammar, version/provenance/status/compatibility envelope, canonical bytes and SHA-256 | Base dependency only | positive/negative/culture/repeat fixtures | Same valid input yields same bytes/digest; malformed identity/version fails stably |
| `PK-R003` Universal architecture language | Architecture | `pkid:schema:program-kit:architecture-design` | Domains, vocabulary, contracts, operations, components, references, extensions, boundaries, scenarios, statuses | References Artifacts only | schema, semantic, graph, forbidden-edge tests | Full synthetic design validates and renders all required semantics |
| `PK-R004` Intent-to-artifact decisions | Architecture | `pkid:schema:program-kit:artifact-decision` | Nine-question decision record and supported artifact kinds including integration docs and ephemeral state | No agent/runtime coupling | complete/missing/contradictory decision fixtures | Every fixture outcome has one canonical owner and declared projections |
| `PK-R005` Separate durable design and plan | Planning | `pkid:schema:program-kit:implementation-plan` | Exact design ref, bounded tasks, trace, sequencing, parallel work, edits, gates, commands, observations | Plan links by ID/version/digest | changed-design, incomplete-trace, migration fixtures | Plan validation refuses missing trace or mismatched design digest |
| `PK-R006` Human-only design/plan approval | Planning | `pkid:schema:program-kit:design-plan-approval` | Exact binding, principal/authority/evidence, conditions and supersession; no self-approval | Consumed by Development/Workbench | absent/changed/rejected/superseded/open-condition tests | Only exact, unconditional, non-superseded human approval is implementable |
| `PK-R007` Reusable quality architecture | Quality | `pkid:schema:program-kit:test-specification` | Test categories/scenarios, execution profile, evidence, independent review contract | Planning references Quality; no release state | schema and selection/dependency-closure tests | Fixture plan selects required tests and produces bound evidence |
| `PK-R008` Deterministic library API | Workbench | `pkid:contract:program-kit:workbench` | Parse/validate/normalize/digest/render/analyze/check/generate services with stable diagnostics | Explicit registries only | unit, repeat, cancellation, I/O-boundary tests | Library calls are culture/time-zone independent and side-effect bounded |
| `PK-R009` Scriptable host | CommandLine | `pkid:host:program-kit:command-line` | Commands, JSON/text diagnostics, documented exit codes, explicit paths/registrations | Transport references Workbench and DotNet | command contract and golden-output tests | Shell calls produce specified outputs and exit codes |
| `PK-R010` .NET language kit | DotNet | `pkid:extension-point:program-kit:dotnet-language-kit` | Project/package/namespace/reference/DI/host/config/lifetime/cancellation/diagnostic/serialization/error/resource/API/SemVer/test/pack rules | Kernel unchanged; explicit language registration | .NET rule positive/negative fixtures | Source-ready guidance and scaffold reflect every listed .NET concern |
| `PK-R011` Controlled composition and CShells boundary | DotNet | `pkid:contract:program-kit:feature-composition-adapter` | Exact package selection manifest and provider-neutral adapter seam; no invented CShells package | Later provider may implement seam; no kernel dependency | extra package, wrong digest, duplicate/missing activation tests | Only selected verified packages participate; CShells truth is marked deferred |
| `PK-R012` Synthetic vertical proof | Observatory fixture | `pkid:fixture:observatory-scheduling:vertical-proof` | Intent -> classification -> design -> plan -> validation/projection -> .NET scaffold -> evidence | Fixture vocabulary stays below fixture root | domain-core/default-feature/provider/contribution/host/AI/forbidden-reference tests | Full fixture flow succeeds and generated outputs repeat byte-for-byte |
| `PK-R013` Self-hosted projection | Workbench + self-hosted artifacts | `pkid:design:program-kit:self-hosted-baseline` | Reviewed bootstrap intent encoded and rendered through implemented contracts | Consumes implemented public API/CLI | bootstrap-vs-self-hosted comparison artifact | Differences are recorded as findings; bootstrap history remains intact |
| `PK-R014` Development routing and receipts | Development | `pkid:schema:program-kit:development-receipt` | Three outcomes; only `routed` may select at most one capability; other outcomes select zero; explicit index-digest availability snapshot; digest-bound receipts; no authority implication | Thin capabilities later supply snapshot and consume result; runtime never reads `.agents` | new idea/approved plan/release request/human-decision/zero-selection/no-authority fixtures | Routing is auditable, non-routed results select nothing, and release requests report the index-backed unavailable flow |
| `PK-R015` Three backed human capabilities | `.agents/` + wrappers | reserved stable capability IDs | Canonical procedures, thin Codex wrappers, truthful index state | Runtime source never loads them | capability conformance fixtures and wrapper-thinness checks | Direct and routed design/implementation flows enforce their exact boundaries |
| `PK-R016` Exact-byte capability distribution | Capability bundle + CLI verifier | `pkid:package:program-kit:capability-bundle` | Pack exactly three allow-listed canonical definitions plus separately listed optional Codex wrappers; exclude index/catalog/authoring/unrelated capabilities | No assembly or runtime dependency; consumer registration remains local/human | package-content/digest/tamper/allow-list/catalog-projection tests | Consumer receives verified bytes without importing this workspace's availability or silently registering them |
| `PK-R017` Package and isolated consumption proof | Pack harness | `pkid:test:program-kit:isolated-consumer` | Local pack, explicit source, locked restore, isolated sample build/test | Uses packages rather than project refs; no publication | package dependency inspection and isolated consumer evidence | Fresh temp consumer restores/builds without repository engine references |
| `PK-R018` No Release Cycle behavior | Architecture + conformance | `pkid:test:program-kit:no-release-lifecycle` | No release lifecycle types, states, commands, procedures, or publication | `release-kit/` remains separate/unmodified | source/schema/CLI/capability scans with reviewed allow-list for boundary prose | Program Kit cannot freeze, qualify, promote, publish, or route release into implementation |
| `PK-R019` Provenance and status truth | Artifacts + docs | `pkid:ai-artifact:program-kit:clean-room-attestation` | Every generated artifact binds inputs/owner/version/digest/status; final bounded-source attestation | Cross-cutting | metadata completeness and attestation checks | Final report distinguishes implemented/scaffolded/deferred/aspirational |
| `PK-R020` Revisable structural-pattern catalog | Architecture | `pkid:catalog:program-kit:structural-patterns` | Versioned entries state problem, criteria, trade-offs, examples, mechanical/human checks, and explicit revision decision | Referenced by design; never hard-coded as doctrine | schema/rendering/migration and fixture-use tests | Catalog is reviewable, traceable, and revisable without changing universal identity rules |
| `PK-R021` Integration adapter separation | Architecture + DotNet | `pkid:test:program-kit:adapter-consumption-separation` | Technology adapter owns provider translation; consumer-shape module stays with consumer above public provider contract | Forbids technology/consumer ownership inversion | positive adapter/consumer shape and forbidden-reference fixtures | Graph accepts the bridge pattern and rejects consumer policy inside the provider adapter |
| `PK-R022` Integrator identity projections | Architecture + Workbench | `pkid:contract:program-kit:integration-surface` | Render OpenAPI 3.2.0, Open Console, and Open Worker documents from owned operation contracts; validate external/internal schemas and preserve operation identities | Adds projections only; never a second behavior owner | golden output, official OpenAPI-schema, Program Kit schema, operation-identity/provenance, and migration tests | All three document kinds validate, identify consumable surfaces, and trace every entry to its source operation |

## 5. Work units, sequencing, and allowed edits

### `PK-W000` Record the bootstrap decision

- **Depends on:** explicit human approval of the review-manifest digests.
- **Allowed edits:** `program-kit/bootstrap/` only.
- **Inputs:** approving principal/authority references and decision evidence from
  the human session.
- **Outputs:** immutable bootstrap approval record binding exact design and plan.
- **Bootstrap receipt exception:** because no capability or receipt contract
  exists yet, the contemporaneous approval/provenance record is the audit record
  for `PK-W000`; it is not mislabeled as a DevelopmentReceipt. Approving this
  plan explicitly accepts that one-time bootstrap exception. Normal capability
  handoffs emit receipts only after real capability bytes are registered.
- **Stop:** do not proceed on rejection, requested change, ambiguous scope, open
  condition, or digest mismatch.
- **Observation:** record can be independently compared with the review
  manifest; no tool is said to have granted approval.

### `PK-W010` Establish the build spine and universal contracts

- **Depends on:** `PK-W000`.
- **Allowed edits:** `program-kit/ProgramKit.sln`, repository-root `global.json`,
  `program-kit/NuGet.Config`, `program-kit/Directory.*`,
  `program-kit/src/Orbyss.ProgramKit.{Artifacts,
  Architecture,Quality,Planning,Development}/`, `program-kit/schemas/`, and
  matching unit-test paths.
- **Inputs:** approved architecture Sections 3–6 and requirement IDs R002–R007,
  R014, R019–R022.
- **Outputs:** exact SDK/MSBuild-SDK/package pins, NuGet source clearing/mapping,
  package locks, package metadata, Draft 2020-12 schemas, typed immutable views,
  contract-local construction invariants, contract fixtures, and initial tests.
- **Compatibility:** package versions begin `0.1.0`; schemas begin major `1`;
  prerelease status is explicit. Public breaking changes require a major schema
  or package version plus migration.
- **Observation:** solution restores only from the explicit config and builds
  warning-clean; schema files are well-formed and typed contract unit tests pass.
  Cross-document JSON Schema/semantic validation and stable diagnostic mapping
  become observable in `PK-W020`, their single deterministic owner.

This is the first coherent baseline slice: a standalone contract graph with
real validation tests, not empty project scaffolds. Work may continue through
the accepted plan without another approval unless a material deviation occurs.

### `PK-W020` Implement canonicalization and deterministic Workbench services

- **Depends on:** `PK-W010`.
- **Allowed edits:** `program-kit/ProgramKit.sln`,
  `program-kit/src/Orbyss.ProgramKit.Workbench/`, and matching
  unit/conformance test paths.
- **Inputs:** approved canonical profile, schemas, typed views, explicit source
  collections and registries.
- **Outputs:** stable library API for parse, validate, normalize, digest,
  Markdown projection, graph analysis, conformance, and bounded generation;
  Draft 2020-12 evaluation through pinned `JsonSchema.Net`, cross-field semantic
  validation, stable diagnostic catalog, structural-pattern catalog support, and
  explicit adapter/consumer-shape conformance rules; deterministic OpenAPI 3.2.0,
  Open Console, and Open Worker projection/validation from operation contracts.
- **Failure/cancellation:** no partial output publication on cancellation or
  validation failure; typed failures preserve diagnostic IDs.
- **Observation:** repeated runs across cultures/time zones produce identical
  canonical bytes, Markdown, graph ordering, and digests.

### `PK-W030` Implement the .NET language kit

- **Depends on:** `PK-W020`.
- **Safe parallel group:** may proceed beside `PK-W040` after the Workbench
  public registry is stable; integration waits for both.
- **Allowed edits:** `program-kit/ProgramKit.sln`,
  `program-kit/src/Orbyss.ProgramKit.DotNet/`, and matching
  test/fixture-contract paths only.
- **Inputs:** approved Section 9, universal design/plan/test models.
- **Outputs:** explicit language/platform/composition seams, .NET rules,
  selection-manifest validation, source-ready guidance, deterministic scaffold
  generator, analyzer/SemVer/test/package obligations.
- **External/source dependency:** no CShells dependency; exact integration is
  recorded `deferred` with blocker evidence.
- **Observation:** negative reference/composition cases fail with `PKNET`
  diagnostics and a complete valid design produces expected source shape.

### `PK-W040` Implement the CLI transport

- **Depends on:** `PK-W020`; final composition depends on `PK-W030`.
- **Safe parallel group:** CLI parser, diagnostic transport, and universal
  commands may proceed beside `PK-W030`.
- **Allowed edits:** `program-kit/ProgramKit.sln`,
  `program-kit/src/Orbyss.ProgramKit.CommandLine/`, and matching tests/docs.
- **Outputs:** documented commands and exit codes, stdin/stdout/file support,
  JSON diagnostics, explicit built-in .NET registration, strict
  `capabilities render-catalog` and `verify-bundle` commands, no implicit cwd
  scan.
- **Observation:** command tests match library results and exact golden output;
  usage, conformance, I/O, cancellation, and internal failures remain distinct.

### `PK-W050` Build the isolated synthetic vertical fixture

- **Depends on:** `PK-W030` and `PK-W040`.
- **Allowed edits:** only `program-kit/ProgramKit.sln`,
  `program-kit/fixtures/observatory-scheduling/`, plus fixture-specific
  conformance tests.
- **Inputs:** structured fictional intent, invariant AI instructions, supplied
  prompt values, approved artifact-decision and architecture contracts.
- **Outputs:** canonical fixture artifacts and Markdown projections; `.Core`,
  default feature, provider, additive contribution, host and test projects;
  exact selection manifest; generated provenance manifest.
- **Boundary:** fixture names and behavior may not appear in universal sources,
  schemas, diagnostics, or general capability procedures.
- **Observation:** complete vertical flow validates, builds, tests, catches a
  forbidden reference fixture, and repeats byte-for-byte.

### `PK-W060` Pack and prove isolated consumption

- **Depends on:** `PK-W050`.
- **Safe parallel group:** package metadata inspection and deterministic fixture
  comparisons may run independently in isolated temp roots.
- **Allowed edits:** Program Kit pack metadata, conformance harness, isolated
  fixture template, `program-kit/build/ProgramKit.Pack.proj`, and committed
  evidence definitions. Transient outputs go to an ignored explicit artifacts
  directory or validated temp root.
- **Output-root rule:** `ProgramKit.Pack.proj` resolves its default package root
  to the absolute normalized `program-kit/.artifacts/packages` path from its own
  location and rejects an override outside the repository's Program Kit root.
- **Inputs:** exact solution/project graph and locked external dependencies.
- **Outputs:** explicitly allow-listed local NuGet packages, .NET tool package,
  schema-content reports, fixture-profile packages, package dependency reports,
  and isolated consumer restore/build/test evidence. No feed publication.
- **Observation:** contract-only, DotNet, CLI-tool, schema-discovery, and fixture
  composition consumers succeed independently; universal closure excludes
  DotNet/CLI/CShells/agent assets; every consumer has no engine reference.

### `PK-W070` Author and package the three human-session capabilities

- **Depends on:** working approval, routing, design, plan, CLI, fixture, and
  receipt contracts through `PK-W060`.
- **Capability action:** invoke the repository's
  `author-and-maintain-skills` capability through its active Codex wrapper now,
  and only now.
- **Allowed edits:** `.agents/capabilities/{develop-software,design-software,
  implement-software-plan}/`, `.agents/capabilities/INDEX.md`, generated
  `.agents/capabilities/README.md`, matching `.codex/skills/` wrappers,
  `program-kit/src/Orbyss.ProgramKit.CapabilityBundle/`, and capability
  conformance fixtures/tests plus the solution/central pack allow-list needed to
  include the already approved content-only package.
- **Outputs:** three canonical thin orchestration procedures, three thin Codex
  loaders, truthful index availability, CLI-generated exact catalog, and an
  exact-byte allow-listed content package/manifest. No installer is implemented.
- **Forbidden:** copied architecture manual, alternate provider wrappers,
  release capability definition, hook/watcher/MCP/tool binding, or runtime load.
- **Observation:** all five requested routing/refusal fixtures pass; wrappers
  contain provider trigger metadata and one canonical-loading instruction only;
  packaged bytes and source digests match, excluded files remain absent, and a
  copied definition alone does not become registered in a consumer.

### `PK-W080` Carry the bootstrap design through the Kit

- **Depends on:** `PK-W070` so any capability receipt binds real, registered
  capability bytes.
- **Allowed edits:** `program-kit/artifacts/` and bootstrap comparison tests/docs.
- **Inputs:** unchanged bootstrap design/plan, approval record, implemented
  schemas and Workbench.
- **Outputs:** canonical self-hosted design and separate plan instances,
  deterministic Markdown, an approval relationship report (not a newly minted
  approval), ownership/dependency/forbidden graphs, normal receipts for actual
  post-registration routing/design events, the canonical structural-pattern
  catalog, and a structured comparison artifact.
- **History rule:** the bootstrap approval/provenance records the work that
  predates capabilities. No receipt is backdated and no capability claims to
  have produced already-existing source. Approved-plan implementation receipts
  are demonstrated by an explicitly labeled conformance fixture.
- **Comparison rule:** genuine representation or design differences are findings
  with disposition/status; bootstrap files are never rewritten to manufacture
  equivalence.
- **Observation:** self-hosted instances validate and their Markdown exposes all
  accepted decisions; comparison identifies exact matched and differing claims;
  each normal receipt carries the actual registered capability digest.

### `PK-W090` Run the full closure and publish the review report

- **Depends on:** all preceding work units.
- **Allowed edits:** Program Kit docs/evidence, root/program-kit README links,
  and generated status projections. `core/` and `features/` may be read but not
  changed except to fix an accidental violation before completion.
- **Outputs:** final architecture/package/forbidden graphs, fixture design/plan,
  self-host comparison, approval/receipts, verification observations, status
  matrix, exact blockers, clean-room provenance attestation, and smallest next
  step for engine design.
- **Observation:** every internally implementable mandatory baseline criterion
  is demonstrated by committed artifacts. Only an unavailable required package,
  official API, or external source may produce a truthful scoped blocker; it
  cannot waive unrelated baseline work. Git diff contains no engine semantics or
  Release Cycle behavior.

## 6. Safe parallel work summary

```text
W000 -> W010 -> W020 -> +-> W030 -+
                       |          +-> W050 -> W060 -> W070 -> W080 -> W090
                       +-> W040 -+
```

Within `W010`, schemas/models and contract fixtures may be authored in parallel
only after identity/envelope conventions are fixed. Within `W050`, fixture
source and fixture artifact authoring may be parallel, but generated projections
must come from the final canonical instances. Each worker owns disjoint paths;
integration edits are serialized. No parallel unit may change accepted
architecture or approval state.

## 7. Migration and compatibility rules

1. Schema and artifact versions use SemVer. Readers dispatch by exact schema
   major and reject unknown majors.
2. Adding an optional field with defined default semantics may be minor;
   removing/renaming a field, changing identity, default, cardinality, ordering,
   authority, failure, or canonicalization is major.
3. Package public APIs follow SemVer and record the affected artifact contracts.
   Prerelease package status does not waive explicit migration.
4. Migration is named, versioned, deterministic, fixture-backed, and emits a new
   artifact with old identity/version/digest in provenance. It never mutates or
   silently parses an old artifact as new.
5. Design and plan lifecycle are independent. A design migration invalidates a
   bound plan until a new plan and approval bind the new digest.
6. Generated Markdown carries generator/profile version and source digest. A
   mismatch is detected by `check`; generated files are not hand edited.
7. Capability bundles carry Kit version, canonical source paths, per-file
   digests, and bundle digest. An existing differing consumer file fails closed
   unless a human selects an explicit update operation.

## 8. Verification commands and expected observations

Exact project/package names may be passed through variables in repository test
scripts, but verification remains callable directly and scriptably. The planned
closure is:

```powershell
dotnet --version
dotnet restore program-kit/ProgramKit.sln --configfile program-kit/NuGet.Config --locked-mode
dotnet build program-kit/ProgramKit.sln -c Release --no-restore
dotnet test program-kit/ProgramKit.sln -c Release --no-build --no-restore
dotnet msbuild program-kit/build/ProgramKit.Pack.proj -t:Pack -p:Configuration=Release -p:NoBuild=true
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- validate --manifest program-kit/artifacts/artifact-manifest.json
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- graph program-kit/artifacts/designs/program-kit-baseline.json --format text
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- check --manifest program-kit/artifacts/workspace-manifest.json --profile pkid:test:program-kit:full-development
```

The conformance test host additionally performs these isolated operations in a
validated temp root:

- run normalization/rendering/scaffolding twice and byte-compare declared
  outputs and digests;
- pack to a local folder, verify package hashes/dependency groups, generate an
  explicit `NuGet.Config`, restore a clean consumer with locked dependencies,
  and build/test it without project references;
- separately prove a contract-only consumer closure, a DotNet-kit consumer, an
  installed local `program-kit` tool invocation, embedded/packed schema access,
  fixture-profile composition, and the exact CapabilityBundle allow-list;
- enumerate solution/project/package/namespace edges and compare them with the
  allowed/forbidden graph;
- validate capability source/wrapper/index/catalog/bundle digest equivalence;
- scan Program Kit contracts/commands/procedures for forbidden Release Cycle
  lifecycle concepts while allowing only clearly marked boundary prose and
  negative tests;
- assert `core/` and `features/` each contain only their existing README and
  assert no fixture exists outside `program-kit/fixtures/`.

Expected observations are .NET SDK `10.0.302`, zero compiler/analyzer warnings,
all selected tests passing, stable diagnostic/golden outputs, byte-identical
repeat runs, exact local package identities/digests, successful isolated
consumption, and zero forbidden engine/release references. If a package restore
or external source is unavailable, the expected success is replaced by exact
blocker evidence and no invented integration claim.

## 9. Stop conditions

Stop before further implementation and request human direction when:

- approval is absent, ambiguous, conditional, rejected, superseded, or no longer
  matches exact design/plan bytes;
- a required result needs a new project/package boundary or reverses an accepted
  dependency arrow;
- canonicalization, schema ownership, approval authority, or status semantics
  must change;
- engine/domain vocabulary or behavior appears necessary;
- CShells work would require guessed packages or APIs;
- a fixture would need to escape its designated root;
- a test requires ambient discovery, secrets, network, undeclared writes, or
  unverified machine-local outputs outside its approved execution profile;
- release freeze/candidate/qualification/promotion/publication behavior is
  requested or appears necessary;
- the three capabilities cannot remain thin orchestration over working Program
  Kit contracts/tools.

Ordinary compile failures, validation defects, test failures, or unavailable
package restore are not architectural deviations by themselves: diagnose and
fix within accepted boundaries, or record the exact external blocker.

## 10. Completion observations and status report

Completion requires a human-readable report showing:

1. Program Kit ownership, public contract/package, and forbidden-reference
   graphs;
2. unchanged bootstrap design beside the self-hosted projection and genuine
   comparison findings;
3. synthetic fixture design and separate implementation plan;
4. unit, conformance, architecture, determinism, package, and isolated-consumer
   commands with observations;
5. no engine dependency and README-only `core/` and `features/`;
6. no Release Cycle behavior;
7. artifact owner, contract version, inputs/provenance, canonical representation,
   digest, consumers, compatibility/migration rule, and truthful status;
8. separate `implemented`, `scaffolded`, `deferred`, and `aspirational` lists;
9. the smallest safe next step—invoke design for engine domains—without taking
   that step;
10. exact approval record and digest-bound bootstrap/self-hosted receipts;
11. three implemented development flows and three unavailable Release Cycle
    flows in the generated capability catalog, with the index as authority and
    no root README availability duplication;
12. a clean-room provenance attestation listing every consulted input.

## 11. Human decision requested

Approve, reject, or request changes to this plan together with
`architecture-design.md`, using the exact SHA-256 bindings in
`review-manifest.json`. No source implementation is part of this gate.

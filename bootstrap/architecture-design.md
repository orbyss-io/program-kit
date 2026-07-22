---
artifact-kind: bootstrap-architecture-design
artifact-id: pkid:design:program-kit:baseline
artifact-version: 0.1.0
intended-contract: pkid:schema:program-kit:architecture-design
intended-contract-version: 1
review-state: awaiting-human-approval
implementation-status: aspirational
bootstrap-exception: true
---

# Program Kit baseline architecture

## 1. Bootstrap exception and decision authority

This document is a compact, human-authored precursor to the proposed
`architecture-design/v1` contract. It is not a generated Program Kit output and
does not claim self-hosting. Its headings expose the fields that the implemented
contract will require. The exact review bytes are bound by
`review-manifest.json`.

Only an explicit human decision may approve this design and its linked plan.
Validation, rendering, routing, design, and implementation tools may recommend
or report; none may grant approval. Source implementation is prohibited while
this review set remains `awaiting-human-approval`.

The source repository remains authoritative for its code, behavior, tests,
terminology, framework rules, and human decisions. Program Kit advice and
generated projections cannot silently override that truth.

## 2. Intent, scope, and boundaries

### Intent

Build `program-kit/` as a code-first, independently packageable software and AI
architecture toolkit that turns reviewed intent values into precise architecture
designs, executable implementation plans, deterministic machine artifacts, and
conformance evidence while keeping human architectural judgment explicit.

### Included baseline

- a small universal language for artifacts, architecture, plans, approvals,
  development receipts, and quality specifications;
- versioned JSON schemas and typed .NET models for those contracts;
- deterministic JSON canonicalization, digesting, validation, Markdown
  projection, graph analysis, and conformance diagnostics;
- an explicit, registered extension seam and an initial C#/.NET language kit;
- a scriptable CLI separated from the contract and workbench libraries;
- a synthetic fixture proving intake through isolated package consumption;
- exact-byte packaging of canonical capability definitions after the backing
  contracts and tools work;
- three thin, human-session capabilities for development routing, design, and
  approved-plan implementation.

### Non-goals

- no Domain Semantic Engine domain name, contract, namespace, project, feature,
  host, fixture vocabulary, or behavior;
- no runtime dependency on `core/`, `features/`, `lab/`, `.agents/`, `.codex/`,
  or future engine assemblies;
- no React, ASP.NET Core, Console, or other platform kit in the universal
  kernel; a fixture may contain a console executable without making console
  rules universal;
- no real CShells adapter without verified source truth;
- no ambient plugin discovery, assembly scanning, magic-folder lookup, or trust
  in machine-local build outputs;
- no freeze, release candidate, qualification, promotion, publication,
  rollback, or artifact-feed publication behavior;
- no automated architectural judgment masquerading as a deterministic rule.

### Assumptions proposed for approval

1. The build SDK is pinned to the locally available .NET SDK `10.0.302`; public
   libraries and the CLI target `net8.0` for a conservative initial consumer
   surface. The SDK pin lives in repository-root `global.json` so root-invoked
   commands honor it, with `rollForward` disabled and prerelease SDK use
   disabled. Changing either is an architectural deviation requiring review.
2. The one repository solution is `program-kit/ProgramKit.sln` and contains only
   Program Kit source, tests, and the synthetic fixture projects.
3. JSON contract instances are authoritative. Markdown is a deterministic,
   read-only human projection. The bootstrap Markdown files are the one-time
   exception and will remain as historical inputs.
4. The repository path `release-kit/` is the existing source-truth location for
   the future human-started Release Cycle. No competing `release-cycle/` path is
   created by this work.
5. `.agents/capabilities/INDEX.md` remains the sole editable availability
   authority. If `.agents/capabilities/README.md` is needed for the requested
   human catalog, it is generated and drift-checked from the index rather than
   independently edited. The root README contains no availability value.
6. External runtime, fixture, and test packages may be restored only from an explicitly configured
   `program-kit/NuGet.Config` that clears ambient sources and names
   `https://api.nuget.org/v3/index.json`. Versions are pinned centrally and
   locked. The approved external set is `MSTest.Sdk` `4.3.2` for tests,
   `JsonSchema.Net` `9.3.0` for Workbench JSON Schema validation, and
   `Microsoft.Extensions.DependencyInjection` plus `.Abstractions` `10.0.10`
   for the fixture composition proof. No other direct package is added without
   review; the transitive closure is reviewed and locked. If restore is
   unavailable, source-supported work proceeds and the exact package blocker is
   recorded.
7. No authorized CShells API or package source is present in the bounded source
   set. The baseline therefore implements only a provider-neutral composition
   seam and records CShells integration as `deferred`.
8. Program Kit schemas use JSON Schema Draft 2020-12. OpenAPI projection support
   targets specification `3.2.0` and validates generated JSON against the
   explicitly vendored official schema iteration
   `https://spec.openapis.org/oas/3.2/schema/2025-11-23`; the normative OpenAPI
   prose remains authoritative where its informational schema is incomplete.

### Decisions deliberately left to later approved extensions

- the React language/platform kit;
- a source-verified CShells adapter package and its package/API versions;
- specialized ASP.NET Core, Console, worker, desktop, or other platform kits;
- transport for an artifact feed;
- all Release Cycle contracts and capability definitions;
- all Domain Semantic Engine domain architecture.

## 3. Architectural principles

1. A fact has one canonical owner; projections carry source identity and digest.
2. Semantic models are dependency-light and do not reference providers, hosts,
   CLI transport, agent assets, or platform kits.
3. Cross-domain use is through public contracts or an explicit bridge.
4. Features and unrelated providers do not reference one another. A provider
   specialization may intentionally reference its declared base provider.
5. An external-integration adapter wraps its technology behind an owned
   provider boundary. Consumer-specific consumption-shape modules sit with the
   consumer above that provider contract; they are not folded into the adapter
   or used to make the external technology own consumer semantics.
6. A helper has one owner, is non-activatable, is never referenced by a domain
   core, and is consumed only by concrete features in its owner domain or named
   provider-specialization family.
7. Hosts compose selected features, configuration, and routing; policy stays
   with its semantic owner.
8. Extension and activation identities are explicit, stable, versioned, and
   testable. Registration is explicit in code or in a reviewed manifest.
9. Packaging follows compatibility and dependency cohesion. Small duplication
   is preferred when sharing would widen authority, security, comprehension, or
   versioning scope.
10. Code enforces mechanical claims. Human review owns semantic fitness,
   vocabulary quality, purpose clarity, and justified trade-offs.
11. Every rendered claim and graph edge traces to an owning input path and
    artifact digest.

## 4. Universal contract shapes

### 4.1 Stable identity

All semantic entities use a Program Kit identifier with this grammar:

```text
pkid:<kind>:<scope>:<name>
```

`kind`, `scope`, and `name` are lowercase ASCII kebab-case tokens. Kinds include
`domain`, `contract`, `operation`, `feature`, `provider`, `helper`,
`contribution`, `extension-point`, `bridge`, `host`, `schema`, `design`,
`plan`, `project`, `package`, `test`, `fixture`, `catalog`, `ai-artifact`,
`capability`, `approval`, and `receipt`. An identity is stable across display-name and path
changes. Reuse of an identity for different semantics is invalid.

### 4.2 Artifact envelope and canonical bytes

Every durable machine artifact uses this logical envelope:

```text
ArtifactEnvelope<T>
  contract: { schemaId, schemaVersion }
  artifact: { id, kind, version, ownerId, status, consumers[] }
  compatibility: { policy, minimumReaderVersion, migrationRefs[] }
  provenance: { sourceInputs[{ identity, version, digest }], producer, correlationId }
  representation: { canonicalizationProfile, canonicalMediaType }
  integrity: { algorithm, digest }
  document: T
```

`status` is exactly `implemented`, `scaffolded`, `deferred`, or
`aspirational`. Review and approval state is modeled separately and cannot be
smuggled into implementation status.

Canonicalization profile `pk-canonical-json-1` uses UTF-8 without BOM, unique
NFC object names and string values, ordinal Unicode-scalar property ordering,
preserved array order, minimal JSON escaping, invariant booleans/null, and
base-10 signed 64-bit integers without leading zeroes. Floating-point JSON
numbers and duplicate properties are rejected. The SHA-256 digest is calculated
over the canonical envelope with `integrity.digest` omitted, which avoids a
self-reference while binding contract, identity, compatibility, provenance, and
document content. Time, principal, and correlation values are supplied intent;
the deterministic library never invents them from ambient state.

JSON Schema is the canonical owner of serialized field names, requiredness,
types, enums, and structural constraints. Immutable .NET models are compiled
views over that wire contract; semantic validators own cross-field invariants.
Schema/model conformance tests detect any drift, and committed schemas are never
generated back from the compiled views. Markdown, indexes, graphs, and catalogs
are deterministic projections from validated canonical instances.

An old artifact is parsed only by its declared schema/profile version. Unknown
versions fail with a stable diagnostic. Migration is an explicit, versioned
operation that emits a new artifact and provenance reference; it never silently
reinterprets old bytes.

### 4.3 Architecture design

`ArchitectureDesignDocument` contains:

- intent, scope, non-goals, assumptions, unresolved decisions, and source-truth
  authorities;
- domains, each with one verb-led purpose and owned vocabulary;
- public contracts, semantic models, operations, and stable identities;
- components of kind domain core, feature, provider, focused helper, bridge,
  host, design-time source, read projection, or evaluated artifact;
- projects and packages with ownership and compatibility boundaries;
- allowed and forbidden reference rules, each traced to its owner input;
- extension points and contribution semantics;
- configuration ownership and feature activation identities;
- artifact decisions and canonical/projection relationships;
- security, authority, secrets, persistence, failure, concurrency,
  cancellation, observability, and compatibility boundaries;
- caller-visible scenarios and status claims.

Each `OperationDefinition` states input, output, side effects, authority,
failures, cancellation, idempotency, compatibility, observability, and resource
ownership. Each extension definition selects one semantic kind:

| Kind | Required semantics |
| --- | --- |
| Replacement | exactly-one/zero-or-one cardinality, selection rule, fallback, failure |
| Additive contribution | cardinality, stable ordering, aggregation, partial/fail-fast behavior |
| Event/subscription | delivery guarantee, ordering scope, retry, duplication, handler failure |
| Provider specialization | explicit base provider, added contract, compatibility and fallback |
| Adapter/bridge | owned sides, translation/loss policy, authority, failure and observability |

The initial structural-pattern catalog is a versioned artifact whose entries
state problem, applicability criteria, trade-offs, examples, mechanical checks,
and human checks. Revisions require an explicit design decision and migration;
the catalog is guidance, not doctrine.

### 4.4 Intent-to-artifact decisions

Every requested outcome owns an `ArtifactDecision` that records answers to the
nine decision questions in the mission: executable behavior; validated,
exchanged, persisted, compared, or digested values; bounded agent retrieval;
agent judgment/procedure; human explanation/decision; generated navigation;
canonical versus projected representations; identity/owner/schema/provenance/
digest/consumer/compatibility/migration; and redacted, externalized, or
ephemeral data.

Supported artifact kinds are source code; project/package configuration;
schema; schema instance; configuration; generated manifest/catalog/index;
provider-neutral agent instruction/capability; human document/decision record;
test specification/profile/fixture; generated code; generated document;
contract-defined ephemeral state; `open-api-document`; `open-console-document`;
and `open-worker-document`. Ephemeral state may be referenced by a contract but
is forbidden in canonical source instances.

The three integrator-document kinds bind host/service identity and version,
operation identities, endpoint/command/worker trigger names, input/output and
error contracts, authority/authentication requirements, compatibility, and
source design digest. OpenAPI follows its versioned external specification;
Open Console and Open Worker use Program Kit schemas. All are projections of
owned operation contracts rather than independent copies of behavior.

AI machine artifacts additionally separate invariant instruction text from
supplied intent values and declare intent schema, output schema, tool contracts,
context-query contract, redaction and injection boundaries, rendering profile,
fixtures, compatibility, and provenance. Agents interpret bounded intent;
ordinary code validates, assembles, canonicalizes, digests, and tests it.

### 4.5 Implementation plan and trace

`ImplementationPlanDocument` has its own identity and lifecycle. It references
an exact design ID, version, and digest rather than embedding the design. It
contains bounded tasks, sequencing, dependency-safe parallel groups, inputs,
outputs, allowed edits, source/external dependencies, migrations,
compatibility, stop conditions, verification commands, expected observations,
unresolved decisions, and this required trace:

```text
requirement -> owner -> contract/artifact -> implementation outcome
            -> dependency/extension impact -> test/fixture/evidence
            -> observable acceptance outcome
```

Exhaustive workspace assignments, snapshots, hashes, or transport envelopes are
separate, generated execution packets bound to the accepted plan digest.

### 4.6 Human approval and development receipts

`DesignPlanApprovalRecord` binds design and plan IDs, versions, and digests;
accepted scope; approving principal reference; separate authority reference;
human-decision correlation/evidence; decision time supplied by the human
session; decision; conditions; and supersession reference/state.

Allowed decisions are `approved`, `rejected`, and `changes-required`. A plan is
implementable only when the exact design and plan digests have a non-superseded
`approved` record with no open conditions. Changed, absent, rejected,
changes-required, or superseded inputs are not implementable. Tools validate or
render a supplied decision but cannot originate an approving principal,
authority, evidence, or approval decision.

`DevelopmentReceipt` binds capability ID/version/digest, request or intent
identity/digest, consumed artifacts, result, producer, principal, correlation,
and supplied time. Routing results are exactly `routed`,
`human-decision-required`, or `flow-unavailable`. A routed result names at most
one next capability and conveys no authority; the other two outcomes name zero
capabilities. Both zero-capability invariants have negative conformance
fixtures.

Routing consumes an explicit `CapabilityAvailabilitySnapshot` supplied by the
human-session capability. The snapshot lists capability IDs/statuses and binds
the exact source path and SHA-256 of `.agents/capabilities/INDEX.md`. Program Kit
runtime libraries neither read `.agents/` implicitly nor hard-code a second
availability value. The canonical index uses `available`/`unavailable`; those
registration values are never translated into architecture implementation
states.

The bootstrap exception predates those capabilities. Its approval record and
provenance attest the historical work; no later capability may issue a
backdated receipt or claim it produced earlier artifacts. After registration,
the self-hosted routing/design run emits normal receipts with real capability
digests, and conformance fixtures exercise the approved-plan implementation
receipt. This preserves the audit trail without inventing history.

### 4.7 Quality and evidence

`TestSpecification` separates durable meaning from an `ExecutionProfile`.
Specifications support unit, component, contract/conformance,
registration/composition, integration, end-to-end, regression, architecture,
security, performance, reproducibility, compatibility, and human-validation
categories. Scenarios support positive, negative, failure, recovery,
cancellation, concurrency, and migration cases.

Each specification includes requirement IDs, owner, purpose, inputs, fixtures,
environment assumptions, runner class, platform, dependency closure,
network/write/restore/secret policy, timeout/retry policy, expected result, and
evidence shape. Evidence binds the executed specification/profile versions and
digests, exact subject digest, observation, and producer. Independent review,
when selected by a plan, binds the exact artifact or delta and records a reviewer
separate from the producer without assuming an agent dispatcher.

Required conformance coverage includes forbidden references, provider
isolation, feature registration, contract preservation, standalone packaging,
AI schema conformance, missing/extra intent values, deterministic rendering,
injection/redaction boundaries, and explicit migration behavior.

Each ordinary implementation plan selects the specifications required by its
changed surface and dependency closure. A future Release Cycle may consume the
same durable definitions for a frozen qualification closure, but that reuse
adds no release state or release-start decision to Quality or Planning.

### 4.8 Baseline artifact decisions

This is the concrete bootstrap decision set, not merely the model it proposes.
The columns jointly answer the nine required questions for every baseline
outcome: executable code; machine value; bounded agent retrieval; agent policy;
human review; generated navigation; canonical/projection ownership; identity,
provenance, consumers and migration; and redaction/ephemeral state.

| Outcome and canonical owner | Code and machine contract | Agent/human artifact | Projection/navigation | Integrity, compatibility, and ephemeral boundary |
| --- | --- | --- | --- | --- |
| Universal artifact, architecture, quality, plan, approval, and receipt contracts — their named contract package/schema | Typed models and semantic validators execute; Draft 2020-12 schemas own wire shapes; instances are canonical | No agent procedure owns semantics; generated Markdown is for human review | Schema catalog and Markdown are generated from exact schema/instance bytes | PKID/version/owner/consumer/provenance/digest required; major migration explicit; no secrets or ambient state |
| Workbench and CLI operations — Workbench code and command contract | Library code executes deterministic operations; CLI arguments and `open-console-document` describe transport | Human command guide explains use; no instruction file substitutes for code | Command catalog and help are generated from registered command descriptors | Package/API SemVer plus tests; filesystem/network/time are explicit inputs; temporary outputs stay outside canonical source |
| Architecture design, separate implementation plan, approval, and receipts — exact schema instances | Code validates, compares, digests, and renders values; approval decision is supplied, never computed | Design/plan Markdown and approval/receipt summaries support review; design capability supplies bounded judgment | Markdown, graphs, execution packets, and indexes are projections | Each lifecycle/version is separate; changed digest requires new plan/approval; principal, time and correlation are supplied values |
| Structural-pattern catalog — `pkid:catalog:program-kit:structural-patterns` | A schema instance owns entries/criteria/trade-offs/check classes; validators enforce shape only | Human architectural decision owns revisions and semantic fitness | Markdown navigation/catalog is generated | Versioned and digest-bound; explicit decision/migration for revision; not a frozen doctrine |
| .NET rules, selection, scaffold, and packages — DotNet profile/schema plus generated-source provenance | DotNet code executes guidance/scaffold generation; selection manifest is validated; generated source is an output, not a second rule owner | Human .NET guide explains consequences; no CShells instruction or guessed API | Project/package/reference maps, scaffold, SemVer report, and package catalog are generated | Language-kit/profile/package versions bind outputs; exact package digests; build/package folders are ephemeral until explicitly evidenced |
| AI machine artifact — invariant template plus intent/output schemas and supplied fixture intent instance | Code validates missing/extra values, assembles canonical prompt/context bundle, and validates output | Bounded agent interpretation uses a typed context-query result; invariant instruction remains separate from supplied values | Rendered prompt instance and human explanation are projections | Template/schema/intent IDs and digests bind provenance; secrets external, untrusted text delimited, runtime conversation state ephemeral/redacted |
| Quality specifications and evidence — Quality instances and test source | Test runners execute selected definitions/profiles; evidence is a canonical result instance | Human-validation and independent-review records are explicit when selected | Test catalog and evidence summaries are generated | Subject/spec/profile digests required; retries/timeouts/network/writes/secrets explicit; raw transient logs are referenced or redacted |
| Three capability procedures and availability — exact `.agents` definitions and canonical index | Program Kit code only validates receipts/catalog/bundle; it never executes capability prose at runtime | `CAPABILITY.md` is the provider-neutral agent procedure; index is human-session availability authority | Thin wrappers, generated availability catalog, and content bundle are non-authoritative projections/adapters | Exact allow-list and per-file digests; consumer registration separate; no runtime or Release Cycle state |
| Synthetic observatory fixture — fixture artifacts and source under its one root | Fixture code/tests execute; canonical intent/design/plan/selection/AI instances are machine contracts | Fixture Markdown is human-reviewable and explicitly fictional | Scaffold, docs, graphs, package manifests, and evidence are generated | Fixture IDs/versions/digests bind all outputs; build/restore folders ephemeral; vocabulary cannot leak into universal assets |
| Integrator identity documents — owned operation contracts | Operation contracts are canonical; code renders OpenAPI 3.2.0, Open Console, or Open Worker documents | Human prose may explain use but cannot redefine operation identity or behavior | All three integrator documents are deterministic projections | Source design/operation/schema versions and digests carried; auth/secrets referenced, not embedded; migration follows operation compatibility |

## 5. Ownership map

| Semantic owner | Owns | Does not own |
| --- | --- | --- |
| Artifact model | identities, envelope, provenance, status, compatibility, canonical profile | architecture or platform judgment |
| Architecture model | domains, contracts, operations, components, references, extensions, artifact decisions, scenarios | implementation sequencing or CLI transport |
| Planning model | plan identity/lifecycle, trace, tasks, approval records | architecture aggregate or approval authority |
| Quality model | test meaning, profiles, fixtures, evidence and review bindings | release qualification state |
| Development flow model | routing outcomes and development receipts | design, implementation, release, or authority grants |
| Deterministic workbench | parse, validate, normalize, digest, render, analyze, generate, diagnose | arbitrary judgment or ambient discovery |
| .NET language kit | C#/.NET project/package/reference/composition/source guidance | universal semantics or unverified CShells APIs |
| Command-line host | argument/file transport, explicit extension registration, exit codes | semantic policy |
| `.agents/` | canonical human-session capability procedures and availability index | runtime inputs |
| Capability bundle | digest-bound packaging of exact `.agents/` bytes | editable procedure copies or mandatory provider wrappers |
| `release-kit/` | future human-started Release Cycle | Program Kit behavior in this phase |
| `core/`, `features/`, `lab/` | reserved engine/Lab boundaries | any Program Kit implementation or fixture |

## 6. Project and package graph

The proposed source projects and public packages are:

| Project/package | Responsibility | Direct dependencies |
| --- | --- | --- |
| `Orbyss.ProgramKit.Artifacts` | artifact envelope, identity, provenance, compatibility contracts | BCL only |
| `Orbyss.ProgramKit.Architecture` | universal architecture and artifact-decision contracts | Artifacts |
| `Orbyss.ProgramKit.Quality` | reusable test/profile/evidence contracts | Artifacts |
| `Orbyss.ProgramKit.Planning` | plan, trace, acceptance/approval contracts | Artifacts, Quality |
| `Orbyss.ProgramKit.Development` | routing and development-receipt contracts | Artifacts, Planning |
| `Orbyss.ProgramKit.Workbench` | deterministic services, diagnostics, explicit extension registry | all five contract packages; `JsonSchema.Net` `9.3.0` |
| `Orbyss.ProgramKit.DotNet` | .NET language kit, scaffold rules, composition seams | Architecture, Planning, Quality, Workbench |
| `Orbyss.ProgramKit.CommandLine` | scriptable transport and explicit built-in registration | Workbench, DotNet |
| `Orbyss.ProgramKit.CapabilityBundle` | content-only exact-byte capability distribution | canonical `.agents/` source bytes; no assembly dependency |

The first seven libraries are normal NuGet library packages. Each canonical
schema is embedded and packed as content by its semantic owner: artifact-envelope
schemas in Artifacts; architecture/artifact-decision/pattern schemas in
Architecture; test/evidence schemas in Quality; plan/approval schemas in
Planning; routing/receipt schemas in Development. Workbench carries no duplicate
schema authority and loads exact embedded bytes through those public packages.
CommandLine is packed as a .NET tool whose command is `program-kit`.
CapabilityBundle is content-only. Product packing uses an explicit
`program-kit/build/ProgramKit.Pack.proj` allow-list rather than packing the
solution.

```text
Architecture -> Artifacts
Quality -> Artifacts
Planning -> Artifacts, Quality
Development -> Artifacts, Planning
Workbench -> Artifacts, Architecture, Quality, Planning, Development
Workbench -> JsonSchema.Net 9.3.0
DotNet -> Architecture, Quality, Planning, Workbench
CommandLine -> Workbench, DotNet
CapabilityBundle -> canonical .agents bytes (content input only)

fixture Feature / Provider -> fixture Core contracts
fixture Host -> selected fixture Core / Feature / Provider contracts
isolated consumer fixture -> packed Program Kit packages
```

An arrow points from consumer to dependency. No arrow points from universal
contracts to Workbench, .NET, CLI, capability assets, CShells, or a platform
extension. A consumer of universal contracts therefore does not transitively
acquire those packages.

Tests are grouped into `Orbyss.ProgramKit.UnitTests` and
`Orbyss.ProgramKit.ConformanceTests` to avoid a speculative project-per-library
catalog. Fixture projects live only under
`program-kit/fixtures/observatory-scheduling/` and use their fictional domain
vocabulary there.

The non-product project graph is fixed as follows:

| Project identity | Direct project references | Pack rule |
| --- | --- | --- |
| `Orbyss.ProgramKit.UnitTests` | Artifacts, Architecture, Quality, Planning, Development, Workbench, DotNet | never pack |
| `Orbyss.ProgramKit.ConformanceTests` | all product assemblies including CommandLine; reads CapabilityBundle as content | never pack |
| `ObservatoryScheduling.Core` | none | fixture-profile only |
| `ObservatoryScheduling.Scheduling.FirstAvailable` | ObservatoryScheduling.Core | fixture-profile only |
| `ObservatoryScheduling.Visibility.Static` | ObservatoryScheduling.Core | fixture-profile only |
| `ObservatoryScheduling.Constraints.DarknessWindow` | ObservatoryScheduling.Core | fixture-profile only |
| `ObservatoryScheduling.Host` | Core plus the three selected concrete fixture projects | never pack |
| `ObservatoryScheduling.Tests` | Core, the three concrete projects, and Host | never pack |

Test and host projects set `IsPackable=false`. Fixture library packages are
excluded from the product pack allow-list and may be packed only by the named
fixture execution profile into its isolated package folder. No second solution
is created.

## 7. Allowed and forbidden references

### Allowed

- engine code may later reference public Program Kit contract packages or an
  engine-owned adapter;
- a universal contract package may reference only the BCL and the lower
  contract packages shown above;
- concrete language/platform kits may reference universal contracts and the
  explicit Workbench extension seam;
- a provider specialization may reference its declared base implementation;
- a host may reference selected domain core, feature/provider, and composition
  packages;
- a bridge may reference the public contract surfaces it joins.

### Forbidden and mechanically checked

- every Program Kit project -> `core/`, `features/`, `lab/`, future engine
  assembly/namespace, `.agents/`, or `.codex/` at runtime;
- universal contracts -> Workbench, DotNet, CLI, capability bundle, CShells,
  provider, host, or platform package;
- domain core -> concrete feature, provider, host, bridge, or helper;
- unrelated concrete feature/provider -> another implementation;
- helper -> domain core activation or cross-domain consumer;
- host -> domain policy implementation;
- tool/fixture -> ambient scan, unresolved wildcard input, machine-local
  `bin/`/`obj/`, or unverified package bytes;
- Program Kit -> Release Cycle actions or lifecycle state.

Architecture tests inspect solution projects, project/package references,
namespaces, schema enums, fixture boundaries, and package dependency metadata.
They report stable diagnostics rather than inferring semantic quality.

## 8. Deterministic Workbench and CLI

The stable library surface accepts streams/bytes plus explicit registries and
returns values/diagnostics; it does not read a working directory implicitly.
Core operations are `Validate`, `Normalize`, `Digest`, `RenderMarkdown`,
`AnalyzeDependencies`, `CheckConformance`, and `Generate` through an explicitly
selected extension identity. The universal Workbench has no .NET-specific API.
File-system effects sit behind an explicit workspace/output abstraction with a
declared write root and collision policy.

The CLI maps those operations to:

```text
program-kit validate <artifact...> | --manifest <artifact-manifest>
program-kit normalize <artifact> --output <file|->
program-kit digest <artifact>
program-kit render <artifact> --format markdown --output <file|->
program-kit graph <design> [--format text|json|dot]
program-kit check <design|plan> | --manifest <workspace-manifest> [--profile <id>]
program-kit dotnet scaffold <design> <plan> --selection <manifest> --output <dir>
program-kit capabilities render-catalog <index> --output <file|->
program-kit capabilities verify-bundle <bundle>
```

All input paths and registered extensions are explicit. Built-in .NET support is
registered by identity at composition. A later external extension manifest must
name exact extension ID/version, package/assembly identity, SHA-256, entry point,
and compatibility; the loader may load that exact entry point but may not scan
assemblies or folders. Implementing a general external loader is `deferred`;
the baseline proves the explicit in-process registry.

Diagnostics use stable families `PKART`, `PKARC`, `PKPLN`, `PKQLT`, `PKDEV`,
`PKNET`, and `PKCLI` plus a three-digit number. Human text may improve without
changing identity. Exit codes are `0` success, `1` conformance failure, `2`
usage/input/I/O failure, and `3` unexpected internal failure. JSON diagnostic
output is available for scripts.

## 9. .NET language kit

The .NET kit translates approved universal entities into source-ready guidance
and scaffold inputs for:

- one solution and cohesive independently packageable projects;
- per-domain `.Core` contract projects, concrete feature/provider projects,
  optional focused helpers, bridges, and small composition-root hosts;
- namespace ownership based on domain language and validated project/package
  reference direction;
- explicit dependency-injection registrations, service lifetimes, ownership and
  disposal, cancellation, diagnostics, serialization, error contracts, and
  configuration ownership;
- stable feature/extension IDs and selected composition;
- approved package-folder manifests naming exact package ID, version, SHA-256,
  activation ID, and compatibility rather than scanning a directory;
- public API and SemVer consequence classification;
- unit, registration, behavior, integration, architecture, analyzer, warning,
  pack, and isolated-consumer obligations.

`IFeatureCompositionAdapter` and an explicit descriptor/registry define the
provider-neutral seam for a composition language. The contract requires stable
feature identity, exact selection, deterministic registration order,
configuration ownership, duplicate/missing registration behavior, diagnostics,
and failure semantics. CShells is the intended first provider, but no CShells
project, package reference, namespace, registration, or success claim is added
without verified source truth.

`IDotNetPlatformKit` is another explicit, identified registry seam so a later
ASP.NET Core, Console, worker, or desktop kit can add .NET platform rules without
changing the universal kernel. React remains a separate later language/platform
kit through the universal extension model, not a .NET platform implementation.
No platform implementation is included in the baseline.

## 10. Synthetic vertical fixture

All fictional artifacts and projects are contained in
`program-kit/fixtures/observatory-scheduling/`. Its domain purpose is “Schedule
observatory viewing sessions”; its vocabulary is forbidden from Program Kit
universal contracts, source namespaces, schemas, diagnostics, capability
procedures, and generated package documentation.

The fixture proves:

1. structured human intent and an artifact-decision set;
2. an architecture design with `ObservationScheduling.Core`;
3. a default scheduling feature;
4. a replaceable visibility-forecast provider and an ordered additive planning
   constraint;
5. a small host composition selected by an exact package manifest;
6. a structured AI explanation artifact with separate invariant instructions
   and supplied intent values;
7. a human-readable implementation plan and requirement/test trace;
8. forbidden reference, provider isolation, registration, behavior,
   determinism, schema, injection/redaction, and migration tests;
9. locally packed Program Kit packages consumed by an isolated sample that has
   no engine reference.

The fixture is evidence and a conformance input, not universal source truth.

## 11. Capability delivery and session boundaries

Only after the corresponding contracts, CLI operations, and conformance
fixtures work, the existing `author-and-maintain-skills` capability will be used
through its active Codex wrapper to create:

- `develop-software`: classifies request plus accepted artifact state and emits
  exactly one routing outcome; it names at most one next capability and never
  grants authority;
- `design-software`: captures intent and produces design/plan artifacts, then
  stops at human approval; an explicitly human-approved design spike is allowed
  as a bounded artifact, but full implementation never starts silently;
- `implement-software-plan`: requires exact valid approval, implements the
  bounded plan, binds evidence, and stops on an architectural deviation.

The human may invoke design or implementation directly after naming that phase;
the router is a convenience, not a mandatory authority hop.

The procedures remain canonical in `.agents/`; Codex wrappers only load them.
The content-only bundle uses a manifest allow-list containing exactly the three
new canonical `CAPABILITY.md` files and, in a separate optional provider-adapter
section, their three thin Codex wrappers. It excludes the repository-local
authoring capability, capability index, generated catalog, and unrelated future
capabilities. Every payload entry carries source path, Kit version, and SHA-256.
Package copies are non-authoritative.

This baseline verifies and distributes the bundle; it does not implement an
installer. A consumer may explicitly materialize the three canonical files into
its `.agents/`, then separately choose a provider wrapper and update its own
availability authority under human control. Copying definitions or optional
wrappers never imports this workspace's index/status or silently registers a
capability. Provider wrappers are never loaded by runtime libraries.

The CLI owns strict index-to-catalog projection and bundle verification. The
catalog reproduces `available`/`unavailable` values and source digest exactly;
it does not infer an architecture implementation state.

Routing fixtures prove new idea -> design, valid approved plan ->
implementation, release/qualify/promote -> unavailable, recommendation -> no
authority, and absent/changed/superseded/unapproved plan -> refusal. Every
handoff emits a digest-bound development receipt.

This plan creates no procedure or wrapper for the three reserved Release Cycle
IDs. Their current and future availability is reported only by the canonical
capability index and its generated exact projection.

Program Kit may define build/package identities and reusable quality
specifications for future Release Cycle consumers. It does not initiate, freeze,
qualify, promote, publish, supersede, abandon, or roll back any release artifact.

## 12. Security, authority, failure, and compatibility

- Secrets are references to an external secret source, never canonical values.
  Redaction policy is declared and tested before rendering or context assembly.
- Paths are normalized under an explicit read/write root; traversal, symlink
  escape, overwrite, and undeclared writes fail closed.
- Package and extension bytes are verified against reviewed SHA-256 values
  before use. A directory listing confers no trust.
- The Workbench has no network authority. Restore is a separate execution-profile
  concern and is disabled unless explicitly selected.
- Operations accept cancellation and distinguish validation, compatibility,
  authorization, I/O, and internal failures with stable diagnostics.
- Generation is idempotent for identical canonical inputs. Existing differing
  files require an explicit collision policy; default is fail.
- Schema major versions are not silently compatible. Additive compatible change
  rules are documented per contract; migrations produce new versioned artifacts
  with provenance.
- Parallel generation writes to isolated roots and publishes no shared mutable
  state. Artifact ordering is stable and culture/time-zone independent.

## 13. Caller-visible scenarios

1. A designer supplies structured intent. The Workbench validates it, renders a
   design and separate plan, and reports exact IDs/digests; no approval appears.
2. A human supplies an approval record for those exact digests. Validation marks
   the plan implementable; changing one byte makes it non-implementable.
3. An executor generates the fixture scaffold twice from identical inputs. Both
   runs produce byte-identical declared outputs and the same graph/digests.
4. A forbidden feature-to-provider reference produces the same diagnostic ID in
   library and CLI use.
5. A package folder contains extra files. Only exact manifest selections are
   considered; a selected digest mismatch fails before composition.
6. A universal-contract consumer restores an Artifact or Architecture package
   without DotNet, CLI, CShells, capability, or platform dependencies.
7. A user asks to release. Development routing returns `flow-unavailable` and
   does not invoke implementation or create lifecycle state.

## 14. Implementation-claim truth at this gate

These are architecture implementation claims, not capability registration
statuses. `.agents/capabilities/INDEX.md` alone owns availability, and its future
human catalog reproduces index values exactly without mapping them to these
claim states.

| Surface | Implementation claim state | Truth |
| --- | --- | --- |
| Workspace boundary placeholders | `scaffolded` | Existing README-only reservations |
| Canonical capability index and `author-and-maintain-skills` capability | `implemented` | Existing human-session development tooling; not Program Kit runtime |
| This bootstrap review set | `scaffolded` | Human-authored and awaiting approval |
| Universal contracts, schemas, Workbench, CLI, .NET kit | `aspirational` | Designed here; no source exists |
| Synthetic fixture and test evidence | `aspirational` | Designed here; no artifacts exist |
| Three development capabilities and capability bundle | `deferred` | Must wait for working backing contracts/tools |
| CShells adapter | `deferred` | No verified source truth consulted |
| Later language/platform kits | `deferred` | Extension seams only |
| Release Cycle behavior and capabilities | `deferred` | Owned outside Program Kit |
| Engine domains and features | `deferred` | Must remain semantically empty |

## 15. Bootstrap provenance

Consulted inputs are deliberately bounded to:

- the human request in the attached `pasted-text.txt`;
- repository `AGENTS.md`, root `README.md`, `.gitignore`, and the README files in
  `program-kit/`, `core/`, `features/`, `lab/`, and `release-kit/`;
- `.agents/README.md`, `.agents/capabilities/INDEX.md`, and `.codex/README.md`;
- the existing canonical `author-and-maintain-skills` definition and its thin
  Codex wrapper, inspected only to confirm capability-authoring boundaries and
  not invoked to create or modify a capability;
- repository file inventory, Git status/history, Git line-ending configuration,
  and installed `dotnet --info`;
- authoritative NuGet package pages for `MSTest.Sdk` `4.3.2`,
  `JsonSchema.Net` `9.3.0`, and Microsoft dependency-injection `10.0.10`, plus
  Microsoft Learn's MSTest SDK guidance;
- the JSON Schema Draft 2020-12 Core and Validation specifications;
- the official OpenAPI Specification `3.2.0` and official schema iteration
  `3.2/schema/2025-11-23`.

Exact external references:

- [MSTest.Sdk 4.3.2](https://www.nuget.org/packages/MSTest.Sdk/4.3.2),
  [MSTest SDK guidance](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-sdk),
  [JsonSchema.Net 9.3.0](https://www.nuget.org/packages/JsonSchema.Net/9.3.0),
  [Microsoft.Extensions.DependencyInjection 10.0.10](https://www.nuget.org/packages/Microsoft.Extensions.DependencyInjection/10.0.10),
  and [its Abstractions package](https://www.nuget.org/packages/Microsoft.Extensions.DependencyInjection.Abstractions/10.0.10);
- [JSON Schema Draft 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core)
  and [Validation](https://json-schema.org/draft/2020-12/json-schema-validation);
- [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) and its
  [2025-11-23 JSON Schema](https://spec.openapis.org/oas/3.2/schema/2025-11-23.html).

These external pages were accessed on `2026-07-22`; versioned URLs are retained
as provenance rather than replaced by “latest” links.

The canonical `author-and-maintain-skills` procedure was not invoked because no
capability is needed or permitted before its Program Kit backing exists. No
sibling repository, CShells source, Spec Kit source, build output, or
machine-local package artifact was consulted. External lookup was limited to the
authoritative package and specification sources listed above. This is a
clean-room provenance attestation for the bounded source set, not proof of an
unknowable negative.

## 16. Human decision requested

Approve, reject, or request changes to this architecture together with
`implementation-plan.md`, using the exact digests in `review-manifest.json`.
Approval authorizes only the plan's Program Kit work. It does not authorize
engine-domain design, CShells invention, a Release Cycle, publication, or any
material deviation from the accepted architecture and scope.

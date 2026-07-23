---
artifact-kind: bootstrap-architecture-design
artifact-id: pkid:design:program-kit:baseline
artifact-version: 0.2.0
intended-contract: pkid:schema:program-kit:architecture-design
intended-contract-version: 1.0.0
review-state: awaiting-human-approval
implementation-status: scaffolded
bootstrap-exception: true
---

# Program Kit baseline architecture

## 1. Bootstrap exception and decision authority

This document is a compact, human-authored precursor to the proposed
`architecture-design/1.0.0` contract. It is not a generated Program Kit output and
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
- one domain-neutral, `System.Text.Json`-only serialization package with explicit
  converter/type-metadata contributions, immutable profiles, deterministic JSON
  canonicalization, and model-first usage rules;
- digesting, validation, Markdown projection, graph analysis, and conformance
  diagnostics;
- an explicit, registered extension seam and an initial C#/.NET language kit;
- domain-neutral modularity contracts for contributions and middleware, a
  deterministic in-process publisher/pipeline, and explicit metadata primitives
  for consumer-owned code and artifact generation;
- domain-neutral immediate, background, and scheduled-task contracts, bounded
  in-process defaults, Generic Host integration, and pure schedule calculators;
- a scriptable CLI separated from the contract and workbench libraries;
- deterministic API, Console, and Worker host generation from reviewed
  composition and operation contracts;
- a generated version-compatibility graph, mechanically closed migration-impact
  assessment, and exact observed/target selections;
- a synthetic fixture proving intake through isolated package consumption;
- deterministic local package restore and application publish into an explicit
  output root without feed transport;
- exact-byte packaging of canonical capability definitions after the backing
  contracts and tools work;
- three thin, human-session capabilities for development routing, design, and
  approved-plan implementation; plus a separately repository-owned thin local-
  publish capability after its backing operation works, excluded from that
  initial three-capability distribution bundle.

### Non-goals

- no Domain Semantic Engine domain name, contract, namespace, project, feature,
  host, fixture vocabulary, or behavior;
- no runtime dependency on `core/`, `features/`, `lab/`, `.agents/`, `.codex/`,
  or future engine assemblies;
- no React, desktop, or other unapproved platform kit in the universal kernel;
  API, Console, and Worker generation are .NET profiles outside that kernel;
- no ambient plugin discovery, unbounded assembly scanning, magic-folder lookup,
  or trust in machine-local build outputs; CShells may inspect only the exact
  reviewed feature assemblies selected by the generated composition root;
- no durable/distributed task queue or scheduler, broker transport, leases,
  restart recovery, exactly-once claim, or orchestration engine; the baseline
  scheduler is explicitly volatile and process-bound;
- no automatic health endpoint or OpenAPI publication: host health surfaces are
  generated only from explicit reviewed configuration, and become OpenAPI
  operations only when a consumer owns corresponding operation contracts;
- no Newtonsoft.Json compatibility surface, ambient/global mutable JSON options,
  or routine use of `JsonElement`, `JsonNode`, or `JsonDocument` in typed domain,
  feature, host, or public-contract code;
- no freeze, release candidate, qualification, promotion, publication,
  rollback, or artifact-feed publication behavior;
- no automated architectural judgment masquerading as a deterministic rule.

### Assumptions proposed for approval

1. The build SDK is pinned to the locally available .NET SDK `10.0.302`; every
   Program Kit library, tool, test, fixture, and generated host targets
   `net10.0`. There is no `net8.0` or multi-target fallback. The SDK pin lives in
   repository-root `global.json` so root-invoked
   commands honor it, with `rollForward` disabled and prerelease SDK use
   disabled. Changing either is an architectural deviation requiring review.
   Canonical `DotNetTargetProfile`
   `pkid:profile:program-kit:dotnet-10` version `1.0.0` binds SDK `10.0.302`,
   `rollForward: disable`, `allowPrerelease: false`, TFM `net10.0`, and C# 14.
2. The one repository solution is `program-kit/ProgramKit.sln` and contains only
   Program Kit source, tests, and the synthetic fixture projects.
3. JSON contract instances are authoritative. Markdown is a deterministic,
   read-only human projection. The bootstrap Markdown files are the one-time
   exception and will remain as historical inputs. All Program Kit-owned JSON is
   read and written through `Orbyss.ProgramKit.Serialization.JSON` using an exact
   immutable profile; direct `JsonSerializer` calls outside that package are
   rejected by conformance checks. An allow-listed untyped boundary may hold a
   DOM internally but still invokes the Serialization.JSON facade for reads,
   writes, and canonical values.
4. The only JSON runtime is the .NET 10 `System.Text.Json` implementation. There
   is no Newtonsoft.Json support. Typed immutable .NET models are the default
   contract surface. Untyped DOM use is permitted only inside an explicitly
   allow-listed tooling or foreign-JSON boundary whose artifact decision records
   why no typed contract applies, its owner, resource limits, and conversion or
   opaque-canonical-byte boundary; DOM types never appear in a public Program Kit
   signature or durable contract model.
5. The repository path `release-kit/` is the existing source-truth location for
   the future human-started Release Cycle. No competing `release-cycle/` path is
   created by this work.
6. `.agents/capabilities/INDEX.md` remains the sole editable availability
   authority. If `.agents/capabilities/README.md` is needed for the requested
   human catalog, it is generated and drift-checked from the index rather than
   independently edited. The root README contains no availability value.
7. External runtime, fixture, and test packages may be restored only from an explicitly configured
   `program-kit/NuGet.Config` that clears ambient sources and names
   `https://api.nuget.org/v3/index.json`. Versions are pinned centrally and
   locked. The approved external set is `MSTest.Sdk` `4.3.2` for tests,
   `JsonSchema.Net` `9.3.0` for Workbench JSON Schema validation, and
   `Microsoft.Extensions.DependencyInjection`, its abstractions, the required
   Generic Host abstractions, and
   `Microsoft.Extensions.Diagnostics.HealthChecks` plus its abstractions at
   exact `10.0.10` versions.
   Pure cron calculation may use source-verified `Cronos` `0.13.0` only in the
   optional provider package; the locked `net10.0` consumer selects its compatible
   dependency-free `net6.0` asset. That exact asset and package digest are
   recorded in the Version Map; it is not described as a native `net10.0`
   package. The source binding is verified annotated tag object
   `b313eaae11b4909f8c1ea12f1a1c19d640b932c2`, peeled commit
   `aeb3bff2048c551018cdd16ac11951d0d4bc20d5`, and MIT license digest
   `sha256:48e6c7a1b9a9e687391e6613269b4aa81b6c910f8e2bb53bee7a7e86e53b584a`.
   `NCrontab` `3.4.0` was evaluated as the closest mature parser-only
   alternative. It is smaller in grammar and long-lived, but its public guidance
   exposes `DateTime` occurrence calculation without a comparable owned
   time-zone/DST contract; selecting it would move the most failure-prone
   behavior into Program Kit. Quartz is a full scheduler rather than the light
   parser boundary required here. Cronos therefore remains the initial optional
   provider, subject to the explicit conformance gate in Section 4.4.3 and to an
   immutable tag/commit/license/package/asset evidence record. A failed gate
   leaves cron unavailable without changing Tasks.Core or Tasks.Schedules.
   Feature packages directly reference exact `CShells.Abstractions` `0.0.28`;
   API feature packages directly reference exact
   `CShells.AspNetCore.Abstractions` `0.0.28`; generated hosts pin the exact
   matching `CShells` and, for API hosts, `CShells.AspNetCore` runtime packages.
   No other direct package is added without review; the transitive closure is
   reviewed and locked. If restore is unavailable, source-supported work
   proceeds and the exact package blocker is recorded.
8. CShells' published contract is accepted as the .NET feature ABI:
   `IShellFeature` for ordinary features and `IWebShellFeature` for API endpoint
   features. There is no Program Kit feature-composition adapter or duplicate
   feature interface. Because the accepted packages are pre-1.0, every selected
   package and ABI is exact-version/hash locked and source/package verified.
   All four `0.0.28` packages bind to lightweight tag `0.0.28`, verified commit
   `29fe542835696131278fcacc6cdb9a6186fc0447`, and source MIT license digest
   `sha256:9447cc96460b01c8c6ed647705a3423d15b3a9936cb67154cdf26d1dddfb598d`.
   They are each directly pinned to `[0.0.28]` because their internal dependency
   metadata permits later versions.
9. Program Kit schemas use JSON Schema Draft 2020-12. OpenAPI projection support
   targets specification `3.2.0` and validates generated JSON against the
   explicitly vendored official schema iteration
   `https://spec.openapis.org/oas/3.2/schema/2025-11-23`; the normative OpenAPI
   prose remains authoritative where its informational schema is incomplete.
10. The `net10.0`-only rule governs every Orbyss-owned project and generated
    project. A lower-targeted external asset may be selected only when .NET 10
    compatibility, source/tag/license, dependency closure, exact asset, version,
    and digest are explicitly reviewed and locked; such selection never weakens
    the Orbyss target rule.
11. Every baseline Program Kit package begins at exact version
    `0.1.0-alpha.1`; fixture library packages used only by the isolated proof
    begin at exact version `0.1.0-fixture.1`. The initial Open Console and Open
    Worker schemas are respectively
    `pkid:schema:program-kit:open-console@1.0.0` and
    `pkid:schema:program-kit:open-worker@1.0.0`. These are initial selections,
    not one shared version clock: packages, APIs, schemas, serialization
    profiles, generators, documents, configuration, and implementations advance
    independently and are related only through the Version Map and explicit
    compatibility/migration evidence.
12. DotNet shell bootstrap uses fixed profile
    `pkid:profile:program-kit:json-dotnet-shell@1.0.0`, owned by
    `Orbyss.ProgramKit.DotNet`. It is distinct from Serialization.JSON's generic
    `json-meta` profile and from host-selected consumer contributions.

### Decisions deliberately left to later approved extensions

- the React and desktop language/platform kits;
- richer API, Console, or Worker profiles beyond the approved baseline;
- durable/distributed task execution and scheduler providers, rich calendar
  dialects, workflow/orchestration, and task administration surfaces;
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
12. A domain contribution is an event-like fact published by domain code; an
    extension contribution is one implementation registered into an additive
    extension point. Their identities and failure semantics never collapse.
13. A task is requested work, not a contribution and not an implementation-plan
    work item. Converting a contribution into a task requires an explicit,
    consumer-owned handler or bridge.
14. Contract, schema, package, implementation, generator, host-composition, and
    migration versions are independent clocks connected by exact typed edges;
    matching version numbers never imply compatibility.

## 4. Universal contract shapes

### 4.1 Stable identity

All semantic entities use a Program Kit identifier with this grammar:

```text
pkid:<kind>:<scope>:<name>
```

`kind`, `scope`, and `name` are lowercase ASCII kebab-case tokens. Kinds include
`domain`, `contract`, `operation`, `feature`, `provider`, `helper`,
`contribution`, `extension-point`, `bridge`, `host`, `schema`, `design`,
`plan`, `project`, `package`, `test`, `profile`, `fixture`, `catalog`, `ai-artifact`,
`capability`, `approval`, `receipt`, `task-definition`, `task-schedule`,
`version-map`, `version-selection`, and `migration`. An identity is stable across
display-name and path changes. Reuse of an identity for different semantics is
invalid. An identity change creates a new semantic subject plus an explicit
`replaces` or migration edge; it is not a major version of the old identity.

### 4.2 Artifact envelope and canonical bytes

Every durable machine artifact uses this logical envelope:

```text
ArtifactEnvelope<T>
  contract: { schemaId, schemaVersion }
  artifact: { id, kind, version, ownerId, status, consumers[] }
  compatibility: { policy, dimensions[], readerRange, writerRange, migrationRefs[] }
  provenance: { sourceInputs[{ identity, version, digest }], producer, correlationId }
  representation: { serializationProfileRef, canonicalizationProfileRef,
                    canonicalMediaType }
  integrity: { algorithm, digest }
  document: T
```

`status` is exactly `implemented`, `scaffolded`, `deferred`, or
`aspirational`. Review and approval state is modeled separately and cannot be
smuggled into implementation status.

Canonicalization profile
`pkid:profile:program-kit:canonical-json-rfc8785@1.0.0` is a deliberately strict
subset of RFC 8785 JSON Canonicalization Scheme (JCS). It requires I-JSON input,
UTF-8 without BOM, and unique property names. A reader accepts ordinary
insignificant JSON whitespace so `Normalize` can consume valid noncanonical
input; canonical output contains no inter-token whitespace and uses JCS
primitive encoding, UTF-16-code-unit property ordering, and preserved array
order. Program Kit canonical artifact schemas additionally permit only
booleans, null, strings already in NFC, and finite numbers that satisfy JCS's
I-JSON/IEEE-754 requirements; integer values that must remain interoperably
exact stay in `[-(2^53)+1, (2^53)-1]`. Negative zero, non-NFC text, duplicate
properties, invalid Unicode, non-finite values, and numbers requiring greater
precision are rejected rather than normalized. Larger integers and high-
precision decimals are modeled as schema-constrained strings. The canonicalizer
never alters string data and a
serialization converter cannot replace or extend the canonicalization
algorithm.

The SHA-256 digest is calculated over the canonical envelope with
`integrity.digest` omitted, which avoids a self-reference while binding
contract, identity, compatibility, provenance, serialization/canonicalization
profiles, and document content. Time, principal, and correlation values are
supplied intent; the deterministic library never invents them from ambient
state.

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

### 4.3 Version compatibility and migration closure

Every selected, persisted, generated, or independently consumed boundary has a
`VersionedComponentManifest` with identity, kind, owner, independent version,
digest, provided contracts, required contracts, compatibility claims, and
migration references. A reference is always `{ identity, version, digest }`;
the same identity/version with different bytes is an integrity failure.
Schema and artifact versions are full SemVer strings such as `1.0.0`, never
integer shorthand.

JSON serialization profiles, converter/type-metadata contributions, and the
canonicalization profile have independent clocks. Changing an option,
converter's wire behavior or order, generated type metadata, or selected
contribution creates a new revision and participates in migration closure; a
package version alone never substitutes for those selections.

Workbench deterministically generates a `VersionMapDocument` containing exact
revision nodes and typed dependency edges including `implements`, `reads`,
`writes`, `validates`, `uses-contract`, `wire-schema-of`, `serializes-with`,
`contributes-converter`, `canonicalizes-with`, `publicly-exposes`,
`package-depends-on`, `configured-by`, `generated-by`, `projects`, `composes`,
`handles-task`, `schedules`, `migrates`, and `verifies`. Each edge records its
accepted range, exact resolution, resolved digest, public/private exposure,
compatibility dimensions, and evidence references. Public boundaries end in an
explicit external-consumer node rather than pretending unknown consumers were
enumerated.

Immutable `VersionSelectionDocument` instances bind exact `observed` and
human-selected `target` revisions. Observed selection comes from reviewed
manifests, package locks, `shell.lock.json`, and hashes rather than installed or
latest state. `shell.json` owns reviewed composition intent; generated
`shell.lock.json` binds the exact immutable input Version Map/Selection
identity, version, and digest,
complete package closure per TFM, exact CShells ABI,
feature/contract/schema/generator/serialization-profile selections and
converter-contribution digests, and `packages.lock.json` digest.

Version maps are immutable staged revisions, which prevents digest cycles. A
generated lock, host, document, package, or publish manifest references the
exact map/selection revision used to produce it. A later map revision may add
that output as a node and assess its downstream impact, but the output is never
rewritten to reference the later map that contains it. Final closure evidence
therefore includes every output without any artifact directly or indirectly
hashing itself.

Compatibility is classified independently for semantic behavior, wire read,
wire write, source API, binary ABI, configuration, persisted artifacts/data,
generated input/output, CLI surface, and host composition/activation. Allowed
classifications are `editorial`, `compatible-additive`,
`conditionally-compatible`, `breaking`, and `unknown`; `unknown` fails closed
pending human judgment. A migration impact assessment starts from every changed
revision and computes the fixed-point reverse closure over relevant typed edges,
re-enqueuing dependents whose own contract, package, generation, lock, or host
selection changes. Cycles become atomic migration cohorts and the result is
ordered into dependency-safe waves with every causal path retained.

Each impacted node receives exactly one owned terminal disposition:
`unaffected-with-proof`, `compatible-after-actions`, `major-upgrade`, `redesign`,
`manual-review`, or `blocked`, plus an ordered `requiredActions[]` drawn from
`retest`, `regenerate`, `recompile`, `repackage-or-relock`, `migrate-artifact`,
`migrate-configuration`, `add-adapter`, and
`drain-or-migrate-pending-work`. `unaffected-with-proof` requires an empty action
list and explicit proof; `compatible-after-actions` requires at least one
action. Other terminal dispositions may carry the ordered actions needed to
reach or assess that outcome. A plan is invalid while any reached node lacks an
owner, target version, terminal disposition, complete ordered actions, or
required evidence.

`MigrationDefinition` binds identity/version, source range, exact target, mode
(`artifact-transform`, `configuration-transform`, `source-guidance`,
`regenerate`, `package-upgrade`, or `runtime-adapter`),
preconditions, loss policy, determinism, idempotence, failure policy,
implementation reference, and fixtures. Durable values are transformed into
new values with source and migrator provenance; generated outputs are normally
regenerated. Runtime adapters are explicit temporary coexistence mechanisms,
not artifact migrators. Chaining is permitted only when exactly one approved
path exists. Persistent or external contracts default to
expand-readers, migrate, switch-writers, prove-old-selection-absent, then
contract; dual writing is never assumed.

Pending task instances and recurring schedules are part of that closure. Each
pins its exact definition and payload contract revisions and must be disposed by
draining under the old handler, temporarily supporting both exact versions,
running an explicit migrator, cancelling/recreating with provenance, or blocking
the change. A queued or calculated occurrence never silently executes against a
newer handler contract. Incompatible versions of one .NET assembly identity are
not assumed to coexist in one process; the migration cohort must upgrade
atomically or introduce an explicitly named compatibility package.

While first-party or CShells packages are pre-1.0, NuGet dependencies use exact
range syntax such as `[0.1.0-alpha.1]`; a bare version, which means a minimum, is
forbidden. After 1.0, a bounded range is allowed only with compatibility
evidence. Pack-time .NET package validation compares a reviewed previous
baseline for public API, binary, TFM, and asset compatibility, supplemented by
behavioral contract tests for semantic changes that API comparison cannot see.

### 4.4 Architecture design

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

#### 4.4.1 Domain-neutral modularity and metadata

`Orbyss.ProgramKit.Modularity` owns dependency-light contracts for
`IDomainContribution`, typed contribution handlers and publisher, generic
middleware delegates/contracts, immutable explicit registries, and stable
ordering/identity descriptors. A domain contribution is an event-like fact; the
package does not claim persistence, queueing, retries, replay, an outbox,
transactions, or cross-process delivery.

`Orbyss.ProgramKit.Modularity.InProcess` owns the default deterministic
in-process contribution publisher and middleware pipeline. It defines
zero-handler behavior, ordered multi-handler execution, cancellation,
short-circuiting, reentrancy, aggregation, and fail-fast/continue policy without
inventing domain outcomes. Domain `.Core` packages may reference Modularity and
publish contributions; concrete hosts choose the in-process implementation or
another explicitly compatible implementation.

`Orbyss.ProgramKit.DotNet.Metadata` owns primitive C# attributes and normalized
metadata descriptors that consumers may deliberately apply for Workbench code
or artifact generation. The baseline consumes explicitly supplied, dependency-
free `DotNetSourceDescriptor` values; it exposes no Roslyn type and takes no
`Microsoft.CodeAnalysis` dependency. A later compiler adapter may translate
compiler symbols only after its exact package/version is reviewed. Metadata code
never loads arbitrary consumer assemblies or scans output folders. Attributes
describe identity and generation intent but never become a second owner of
operation, schema, task, or domain semantics.

#### 4.4.2 Domain-neutral JSON serialization

`Orbyss.ProgramKit.Serialization.JSON` is the one domain-neutral JSON mechanics
package. It uses only .NET 10 `System.Text.Json` and owns:

- typed `IProgramKitJsonSerializer` read/write operations selected by exact
  `JsonSerializationProfileRef`;
- immutable, digest-bound `JsonSerializationProfile` descriptors and an explicit
  builder/registry that freezes its `JsonSerializerOptions` before first use;
- stable `IJsonSerializationContribution` descriptors for typed
  `JsonConverter<T>`, declared `JsonConverterFactory` target families, and
  source-generated `JsonSerializerContext`/`IJsonTypeInfoResolver` metadata;
- strict UTF-8 input limits and diagnostics, plus canonicalization to
  `pkid:profile:program-kit:canonical-json-rfc8785@1.0.0`; and
- opaque `CanonicalJsonValue` bytes for the rare deliberately untyped boundary,
  without exposing a mutable DOM as contract state.

Bootstrap/profile-selection metadata uses the non-extensible
`pkid:profile:program-kit:json-meta@1.0.0`. Its built-in source-generated context
reads/writes artifact-envelope headers, serialization/canonicalization profile
descriptors, and exact profile selections before any consumer contribution can
be selected. It has the same strict reader limits and canonical output, permits
no contributed converter or reflection fallback, and is changed only through an
approved profile migration. It knows no platform-specific shell type.

`Orbyss.ProgramKit.DotNet` separately owns fixed, non-extensible
`pkid:profile:program-kit:json-dotnet-shell@1.0.0` and its source-generated
context for `DotNetShellDocument`. CLI/generator composition selects that known
profile to read shell intent before applying the shell's host-specific consumer
profile/contribution selections. The profile uses Serialization.JSON mechanics
but neither adds a DotNet dependency to Serialization.JSON nor permits consumer
contributions or reflection fallback. This removes the circular requirement to
deserialize a profile by using the profile being selected while preserving
package ownership.

The baseline typed contract profile is
`pkid:profile:program-kit:json-contracts@1.0.0`. It requires exact
schema-declared property names through source-generated type metadata (no
global property/dictionary naming policy), case-sensitive reads, disallowed
comments/trailing commas/unmapped members, strict numbers, no implicit null
omission, no reference preservation/cycle handling, maximum depth `64`, and
explicit byte/token limits supplied by the operation. Durable contract types
must be present in a selected source-generated context; reflection fallback,
global enum/date/polymorphism conventions, and type-name materialization are
forbidden. A schema may select an exact typed converter/contribution for those
values. Successful writes return canonical bytes; pretty or human-oriented JSON
is a noncanonical projection and never a digest input. The meta profile owns
envelope/profile selection metadata; this contract profile is mandatory
for Program Kit-owned semantic schema instances, integrator documents, Version
Maps/migrations, evidence, locks, and publish manifests.
A consumer needing a genuinely different wire convention creates a separately
owned/versioned profile and migration edges; it cannot mutate the baseline.

Every contribution has an identity, independent version/digest, owning package,
applicable serialization-profile range, declared target type or type family,
and explicit before/after constraints. Registration is explicit; assembly
scanning and global mutable options are forbidden. Serialization.JSON directly
references exact `Microsoft.Extensions.DependencyInjection.Abstractions`
`10.0.10`; its `IServiceCollection` extensions create a shell-scoped
`ProgramKitJsonBuilder`, and selected concrete CShells features call
`AddJsonSerializationContribution` with exact descriptors. After every selected
feature has completed `ConfigureServices`, generated composition glue exports
those descriptors, merges only the shells selected for one host, and freezes one
host-scoped registry before any read/write operation. No mutable registry or
profile is shared across generated hosts. A topological sort with
a stable identity tie-break produces one frozen profile. Two selected converters
claiming the same target without an explicit, valid precedence decision, a
missing ordering dependency, a cycle, or equal identity/version with different
bytes fails composition. The first-match behavior of `System.Text.Json`
converters is therefore never accidental.

Changing options, converter behavior/order, type metadata, or a contribution
selection changes that contribution/profile version and digest. The Version Map
then reaches every `reads`, `writes`, `serializes-with`, generated-document,
lock, host, and publish-manifest consumer; it is never treated as an invisible
implementation detail. Canonicalization remains a separate fixed profile after
typed serialization, so an extensibility contribution cannot change artifact
hashing rules.

Program Kit and fixture code is model-first. `JsonElement`, `JsonNode`, and
`JsonDocument` are forbidden by default in source, public APIs, and durable
models, and code outside Serialization.JSON may not call `JsonSerializer`
directly. Typed converters may use `Utf8JsonReader`/`Utf8JsonWriter`. A reviewed
schema-tooling or foreign pass-through adapter may use a DOM internally only
when no .NET model is a valid contract for that boundary and its artifact
decision records the reason, exact owner, explicit size/depth limits, and the
point at which data becomes a typed model or validated `CanonicalJsonValue`.
Every exception is an exact file/API allow-list entry consumed by architecture
tests; an undocumented occurrence fails. No DOM type crosses a public Program
Kit signature or enters a durable contract. No Newtonsoft.Json package,
namespace, compatibility flag, or migration shim is allowed.

The only baseline DOM exception is Workbench's internal `JsonSchema.Net`
validation adapter: it must inspect arbitrary pre-model JSON while determining
whether a declared schema applies. Its artifact decision, resource limits, and
conversion point are explicit, and no DOM type crosses its public boundary. Any
additional exception is a reviewed architecture change, not a local convenience.
Serialization.JSON canonicalizes with `Utf8JsonReader`/`Utf8JsonWriter` and
bounded per-object member buffers rather than `JsonElement`, `JsonNode`, or
`JsonDocument`.

#### 4.4.3 Domain-neutral task execution and schedule calculation

Task concepts are deliberately separate:

- `TaskDefinition` is stable, versioned requested-work meaning with exact
  input/output/failure contract references and authority, cancellation,
  idempotency, retry, observability, and resource declarations;
- `TaskRequest` is a proposed, validatable, and rejectable invocation before any
  instance exists;
- `TaskInstance` is one accepted request pinned to the exact definition and
  payload revisions;
- `TaskAttempt` is one execution attempt; retry creates another attempt for the
  same instance;
- `TaskActivationBinding` binds an exact task-definition revision to opaque,
  provider-neutral handler/activation identity references, selected runtime,
  and applicable middleware/retry/idempotency policy revisions;
- `TaskScheduleDefinition` is versioned trigger and task-binding intent, not an
  instance or timer; it references an exact typed schedule-descriptor artifact
  by identity/version/digest/schema plus occurrence-calculator profile, never a
  `JsonElement`, dictionary, or provider-owned unversioned configuration bag; and
- `TaskOccurrence` is one calculated firing that the selected scheduler may
  use to propose a normal request.

Rejection occurs before an instance exists. Instance states are `accepted`,
`waiting`, `running`, `retry-wait`, `succeeded`, `failed`, or `cancelled` with
only the last three terminal. `cancellation-requested` is a race-aware fact, not
a promise that cancellation won. Immediate execution awaits a terminal outcome;
background dispatch returns only after bounded volatile acceptance; scheduled
execution occurs only through an explicit activation binding and selected
scheduler.

Every scheduled execution first creates and submits a normal `TaskRequest`
through the same validation, authorization, dispatch-middleware, capacity, and
acceptance path as any caller. The request carries the occurrence identity as a
causal reference and derives any idempotency key from the exact schedule/
occurrence/definition revisions. A skipped, coalesced, or misfired occurrence is
not an accepted request and never becomes a `TaskInstance` or execution attempt
by another path.

`Orbyss.ProgramKit.Tasks.Core` owns those seven named semantic identities,
immutable request/response/outcome/status views, and all public execution
interfaces: typed `ITaskHandler<,>`, `ITaskRunner`, `ITaskDispatcher`,
`ITaskScheduler`, `ITaskOccurrenceCalculator`, `ITaskStatusReader`, and
`ITaskCancellationRequester`. A consumer domain `.Core` references only
Tasks.Core for task use.

`Orbyss.ProgramKit.Tasks` owns implementation-neutral descriptors, immutable
registries, registration extensions, common coordination, task middleware,
retry/idempotency policy coordination, lifecycle-contribution integration, and
the provider-neutral `ITaskActivationScopeResolver` seam. Tasks directly
references exact `Microsoft.Extensions.DependencyInjection.Abstractions`
`10.0.10`; the generated host calls `AddProgramKitTasks` for each selected shell
`IServiceCollection`, and concrete CShells features call
`AddTaskDefinition`, `AddTaskHandler`, `AddTaskActivationBinding`,
`AddTaskMiddleware`, `AddTaskSchedule`, and `AddTaskOccurrenceCalculator` with
exact identities/versions.
In-process selection is explicit through `UseInProcessTaskRuntime`, while
Generic Host integration uses `AddProgramKitTaskHosting`. Repeating the same
exact registration is idempotent; the same identity with different bytes,
multiple handlers for a single binding, missing definition/handler/feature,
unsupported definition range, or cyclic middleware order fails at composition.
After all selected features complete `ConfigureServices`, generated composition
glue exports and merges their descriptors into one host registry. Duplicate
identities across shells obey the same byte/conflict rules. The task, schedule,
JSON, and health-contributor registries freeze together before the host starts;
registration after freeze or execution before freeze fails.

Program Kit never implements a consumer's task handler. The consumer's concrete
CShells feature implements `ITaskHandler<,>` and registers it through these
extensions. Generated CShells-aware composition glue implements
`ITaskActivationScopeResolver` by mapping the exact opaque feature/shell
activation reference to that shell's scope factory and handler registration.
Tasks.InProcess invokes through this seam and Tasks.Hosting requests a fresh
scope for every attempt. The seam contains no CShells type and does not replace,
mirror, or adapt the accepted feature ABI.

Tasks.Core, Tasks, Tasks.InProcess, and Tasks.Hosting do not know CShells.
Generated DotNet composition resolves each opaque
activation reference to the exact owning CShells feature activation selected by
the host entry in `shell.json`; missing, duplicate, or mismatched ownership fails
before runtime. The same glue aggregates schedule calculators and health
contributors from the frozen selected-shell registries so the scheduler and
health system observe exactly the host's reviewed composition.

Dispatch middleware runs once before acceptance; execution middleware runs once
per attempt. Retry orchestration surrounds attempts. No contribution is
implicitly converted into a task; a consumer-owned contribution handler may
dispatch one explicitly and should derive an idempotency key from the source
contribution identity where appropriate.

`Orbyss.ProgramKit.Tasks.InProcess` supplies direct immediate execution, a
bounded volatile background queue and scheduler/trigger loop, explicit maximum
concurrency and retention, injected `TimeProvider`, and in-memory state. Queue
overflow defaults to rejection rather than dropping.
The enqueue token controls acceptance only; accepted work requires an explicit
cancellation request. Default retry is none; any finite retry policy is exact
and versioned, never retries cancellation/validation/authorization failure, and
does not imply idempotent side effects. An optional key is scoped to the exact
task-definition revision and can suppress duplicate acceptance only within the
current process and retention window. The implementation claims no durability,
restart recovery, or exactly-once execution.
The scheduler consumes explicitly registered `ITaskOccurrenceCalculator`
implementations from Tasks.Core; it does not depend on Tasks.Schedules or Cronos.
Task lifecycle observation resolves the optional Modularity
`IDomainContributionPublisher` contract through Tasks; Tasks.InProcess does not
depend on Modularity.InProcess. A generated host selects Modularity.InProcess or
another compatible publisher separately, and absence of a publisher disables
only that optional observation middleware.

`Orbyss.ProgramKit.Tasks.Hosting` integrates any compatible task runtime with
.NET Generic Host lifecycle, fresh dependency-injection scope per attempt,
drain-or-cancel shutdown policy, and named health checks. Queued work never
captures a caller scope, ambient principal, or secret. Runtime state is
authoritative; lifecycle contributions and BCL activities/meters are
post-transition observations. Failure to publish an observation cannot roll a
committed task transition back; atomic task/outbox semantics remain deferred.

`Orbyss.ProgramKit.Tasks.Schedules` contains provider-neutral typed
delay/interval descriptors, factories, and pure calculators; it is not the
scheduler and does not own schedule registration. `Orbyss.ProgramKit.Tasks`
owns `AddTaskSchedule` and calculator registration; a feature explicitly
registers a calculator produced by a selected schedule-helper/provider package.
A feature also registers the exact typed descriptor artifact referenced by its
TaskScheduleDefinition; Tasks.Schedules owns the one-shot/fixed-delay/interval
descriptor schemas and Tasks.Schedules.Cronos owns its cron descriptor schema.
A calculator accepts explicit reference/cursor/evaluation
instants and returns ordered occurrence decisions. It never reads the clock,
creates a timer, queues work, persists state, acquires a lease, or executes a
task. Its built-in schedule profiles are:

- delay-once: one occurrence at an explicit reference instant plus a
  non-negative `TimeSpan`;
- fixed-delay: the next occurrence is a positive `TimeSpan` after the previous
  bound task instance reaches a terminal state, so it cannot overlap itself;
- interval: occurrences at `anchor + n * period` for a positive fixed duration,
  with the next occurrence strictly after the supplied cursor; calendar units
  are forbidden.

`Orbyss.ProgramKit.Tasks.Schedules.Cronos` is the optional initial cron provider;
it alone carries the Cronos dependency. Its named `cronos/0.13` dialect uses
exact Cronos `0.13.0` semantics with `CronFormat.Standard`
  five-field or `CronFormat.IncludeSeconds` six-field explicitly selected.
  Day-of-month and day-of-week are AND when both are restricted; year is not a
  field. Numeric/name syntax, special characters, aliases, and macros are
  accepted exactly when documented by the locked Cronos profile. Any supported
  hashed/jitter form requires an explicit stable seed in the descriptor;
  ambient randomness is forbidden.

Every Cronos-provider descriptor carries the expression, selected format, exact
`TimeZoneInfo` identifier, and the environment/time-zone-data evidence used by
the locked selection. Occurrence calculation delegates DST behavior to Cronos
and `TimeZoneInfo`; Program Kit does not invent an alternative DST rule.
The selection also binds a deterministic zone-rule fingerprint for an explicit
bounded horizon plus the time-zone data source/version used to calculate it.
Composition and host startup recompute that fingerprint from the selected
`TimeZoneInfo`; a mismatch blocks activation and requires a new provider
selection plus migration assessment. A diagnostic-only record of ambient
time-zone data is not sufficient.

The Cronos provider is accepted only after conformance fixtures cover its full
selected grammar, next/previous occurrence boundaries, representative IANA and
Windows zones, spring-forward gaps, fall-back ambiguity, and comparison with
independently enumerated golden timelines. Evidence must also match the verified
`v0.13.0` annotated tag object and peeled commit, source/package MIT license
digest, NuGet catalog/package hashes, dependency-free `net6.0` asset selection,
and selected assembly hash recorded in Section 15. A failure in that gate blocks
the provider selection; it does not leak Cronos types or semantics into
Tasks.Core or require a replacement parser to keep the same package identity.

Misfire and overlap are scheduler activation policies, not cron-expression or
occurrence-calculator semantics. Every scheduled `TaskActivationBinding`
selects misfire `skip`, `fire-once-now`, or `catch-up-bounded` and overlap
`allow`, `skip`, or `queue-one`; bounded catch-up requires a positive maximum
and no policy permits unbounded replay. The volatile in-process scheduler uses
these explicit policies and the selected calculator. Durable/distributed
scheduler semantics remain deferred.

### 4.5 Intent-to-artifact decisions

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
`open-worker-document`; version component/selection/map; migration definition
and impact assessment; JSON serialization profile/contribution and canonical
JSON value; task definition/schedule descriptor; host composition; local
publish manifest; and generated health configuration. Ephemeral state may
be referenced by a contract but is forbidden in canonical source instances.

The three integrator-document kinds bind host/service identity and version,
operation identities, endpoint/command/worker trigger names, input/output and
error contracts, authority/authentication requirements, compatibility, and
source design digest. OpenAPI follows its versioned external specification;
Open Console uses `pkid:schema:program-kit:open-console@1.0.0` and Open Worker
uses `pkid:schema:program-kit:open-worker@1.0.0`. All are projections of owned
operation contracts rather than independent copies of behavior.

`OpenConsoleDocument` contains document/info/host versions, parsing conventions,
global options, and commands with stable operation identity, tokenized command
path, aliases, arguments, flags/value options, arity/occurrence rules,
required/default/schema/configuration bindings, conflicts/prerequisites,
stdin/stdout/stderr contracts, exhaustive exit codes, authority, examples,
deprecation, compatibility, and provenance. Paths are token arrays rather than
prequoted shell strings. Generated `--help` and completion data are projections
of the same descriptor.

`Orbyss.ProgramKit.DotNet` owns the matching descriptor-driven console parser
semantics and emits the parser as generated source into each Console host; no
external command parser or DotNet/Workbench runtime dependency is selected in
the baseline. The generated parser consumes the operating system's token array
rather than re-parsing a shell command string and defines the `--` terminator,
long/short names, `--name=value`, argument/value arity and occurrence, defaults,
conflicts/prerequisites, culture-invariant typed conversion, stable diagnostics,
and exhaustive exit-code mapping. Parsing, help, completion, and
`OpenConsoleDocument` are generated from the same frozen command descriptors so
they cannot acquire independent semantics. Published Console dependency graphs
must exclude Workbench, DotNet.Metadata, DotNet, and CommandLine assemblies.

`OpenWorkerDocument` remains deliberately small: document/info/host versions
and worker entries containing stable operation identity, feature/activation
identity, exact task-definition reference when applicable, versioned trigger
kind/configuration-schema reference, input/output/error contracts, authority,
cancellation, deprecation, compatibility, and provenance. It does not define
broker topics, acknowledgement, delivery guarantees, retry/dead-letter policy,
leases, partitions, checkpoints, concurrency, backpressure, readiness, or
health; those remain selected runtime/configuration concerns until worker
requirements are proven.

Generated liveness, readiness, and startup health endpoints are operational
surfaces owned by explicit `shell.json` host-health configuration. They are not
silently added to OpenAPI. A health endpoint appears there only when the
consumer separately owns and selects a corresponding operation contract.

AI machine artifacts additionally separate invariant instruction text from
supplied intent values and declare intent schema, output schema, tool contracts,
context-query contract, redaction and injection boundaries, rendering profile,
fixtures, compatibility, and provenance. Agents interpret bounded intent;
ordinary code validates, assembles, canonicalizes, digests, and tests it.

### 4.6 Implementation plan and trace

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

### 4.7 Human approval and development receipts

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

### 4.8 Quality and evidence

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
injection/redaction boundaries, typed JSON profile/contribution ordering,
canonicalization and forbidden DOM/Newtonsoft/direct-serializer use,
fixed-point migration impact, task
registration/queue/cancellation/retry/idempotency behavior, controlled-time
schedule calculation, generated host health configuration, local publish
integrity, and explicit migration behavior.

Each ordinary implementation plan selects the specifications required by its
changed surface and dependency closure. A future Release Cycle may consume the
same durable definitions for a frozen qualification closure, but that reuse
adds no release state or release-start decision to Quality or Planning.

### 4.9 Baseline artifact decisions

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
| Version topology and migration — component manifests, exact selections, Version Map, impact assessment, and migration definitions | Workbench constructs typed-edge graphs, computes reverse fixed-point closure, validates terminal dispositions/ordered actions, and verifies migration paths | Humans classify unknown semantic consequences and approve target selection/coexistence | Graphs, migration waves, and compatibility reports are projections | Independent version clocks and exact digests; no mutable current/latest labels; scoped external-consumer boundary is explicit |
| Domain-neutral modularity and metadata — Modularity contracts and metadata descriptors | In-process publisher/pipeline execute; dependency-free `DotNetSourceDescriptor` inputs and primitive annotation values produce normalized descriptors | Domain code owns contribution meaning and consumer annotations | Contribution/metadata catalogs are generated from explicit registration/source inputs | No Roslyn type/dependency, implicit discovery, transport, persistence, replay, transaction, or domain policy claim |
| Domain-neutral JSON mechanics — Serialization.JSON profiles and contributions | Frozen System.Text.Json profiles read/write typed models and canonicalize strict JSON; custom converters/type metadata are explicit registrations | Consumers own their model/wire meaning and justify any untyped boundary | Profile/contribution catalogs and diagnostics are generated | Profile/contribution versions and digests enter the Version Map; no Newtonsoft, ambient options, public DOM state, or converter-defined canonicalization |
| Domain-neutral tasks and schedules — Tasks.Core definitions plus selected runtime/schedule contracts | Immediate/volatile background execution and the volatile scheduler execute; Tasks.Schedules calculators return occurrences but are not a scheduler | Consumers own task meaning, handler behavior, schedules, authority and effect safety | Task/schedule catalogs and lifecycle summaries are generated | Definition/request/instance/attempt/binding/schedule/occurrence versions remain distinct; no durability/exactly-once/distributed claim; payloads and secrets excluded from observations |
| .NET rules, selection, generated hosts, and packages — DotNet profile, `shell.json`, and generated-source provenance | DotNet code validates exact CShells selection and generates `net10.0` API, Console, and Worker composition roots; generated source is an output, not a second rule owner | Human .NET guide explains consequences and direct CShells ABI exposure | Project/package/reference maps, hosts, OpenAPI/Open Console/Open Worker, health config, SemVer report, and package catalog are generated | Profile/package/CShells/feature versions bind outputs and lock; exact package digests; build folders remain ephemeral |
| Local package preparation and application publish — explicit workspace-package manifest, package-root manifest, publish request, and generated manifest | One backed operation packs an explicit project/package allow-list; a separate operation verifies that package root, restores a selected host with explicit source mapping, and project-publishes to a validated output root | Thin repository capability supplies reviewed publish parameters only after both operations work | Package/file hash manifests and human summaries are generated | First-party restore is local-folder-only; reviewed external restore is nuget.org-only; no NuGet push/feed transport/deployment/signing/release state; collision default is fail |
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
| Version compatibility model | independent revisions, typed dependency edges, observed/target selection, impact closure, migration definitions | semantic compatibility judgment or release state |
| Modularity contracts/defaults | contribution and middleware contracts plus deterministic in-process behavior | domain meaning, durable messaging, transactions, or provider discovery |
| JSON serialization | exact immutable System.Text.Json profiles, explicit typed converter/type-metadata contributions, strict reads, and canonical bytes | consumer data meaning, schema ownership, ambient/global options, or a general-purpose mutable JSON DOM |
| Task contracts/defaults | task definitions, requests, instances, attempts, activation bindings, schedule definitions, occurrences, explicit registries, volatile execution, and pure schedule calculation | consumer task meaning, durable/distributed scheduling, workflows, or exactly-once effects |
| .NET metadata | primitive annotations and normalized explicit-source descriptors | consumer semantics, assembly scanning, or runtime activation |
| .NET language kit | C#/.NET project/package/reference/CShells composition/host/source guidance | universal semantics or a duplicate feature ABI |
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
| `Orbyss.ProgramKit.Modularity` | domain-contribution and generic-middleware contracts/registries | Artifacts |
| `Orbyss.ProgramKit.Modularity.InProcess` | deterministic in-process publisher and middleware pipeline | Modularity |
| `Orbyss.ProgramKit.Serialization.JSON` | model-first System.Text.Json facade, immutable profile/contribution registry, strict read rules, and canonical JSON bytes | Artifacts; DI.Abstractions `10.0.10`; .NET 10 `System.Text.Json` |
| `Orbyss.ProgramKit.Tasks.Core` | seven semantic task contracts plus all public handler/runner/dispatcher/scheduler/status/cancel interfaces | Artifacts |
| `Orbyss.ProgramKit.Tasks` | registration extensions/descriptors, activation-scope seam, and common coordination/pipeline implementations | Tasks.Core, Modularity, DI.Abstractions `10.0.10` |
| `Orbyss.ProgramKit.Tasks.InProcess` | immediate, bounded volatile background, and volatile scheduler defaults | Tasks |
| `Orbyss.ProgramKit.Tasks.Hosting` | Generic Host lifecycle, per-attempt scopes, registrations, health contributors | Tasks; exact Microsoft.Extensions DI/Hosting and Diagnostics.HealthChecks 10.0.10 packages |
| `Orbyss.ProgramKit.Tasks.Schedules` | provider-neutral pure delay/interval descriptors, factories, and calculators | Tasks.Core |
| `Orbyss.ProgramKit.Tasks.Schedules.Cronos` | optional source-verified Cronos dialect and occurrence calculator | Tasks.Schedules; `Cronos` `0.13.0` |
| `Orbyss.ProgramKit.DotNet.Metadata` | primitive annotations and normalized explicit-source metadata | Artifacts |
| `Orbyss.ProgramKit.Workbench` | platform-neutral deterministic services, diagnostics, extension registry, Version Map/migration analysis | Artifacts, Architecture, Quality, Planning, Development, Serialization.JSON; `JsonSchema.Net` `9.3.0` |
| `Orbyss.ProgramKit.DotNet` | .NET language kit, fixed DotNet-shell JSON profile, descriptor-driven console parser-source generation, CShells-aware generated composition glue, and API/Console/Worker generators | Architecture, Planning, Quality, Workbench, DotNet.Metadata, Serialization.JSON, Tasks.Core, Tasks, Tasks.Schedules |
| `Orbyss.ProgramKit.CommandLine` | scriptable transport and explicit built-in registration | Workbench, DotNet |
| `Orbyss.ProgramKit.CapabilityBundle` | content-only exact-byte capability distribution | canonical `.agents/` source bytes; no assembly dependency |

All listed assemblies except CommandLine and CapabilityBundle are normal NuGet
library packages. Each canonical schema is embedded and packed as content by its
semantic owner: artifact/version/migration schemas in Artifacts; architecture/
artifact-decision/pattern schemas in Architecture; test/evidence schemas in
Quality; plan/approval schemas in Planning; routing/receipt schemas in
Development; serialization-profile/contribution schemas in Serialization.JSON;
task and schedule schemas in their named task owner packages.
Workbench carries no duplicate schema authority or compile-time reference to
Modularity, Tasks, DotNet.Metadata, or a host. It accepts explicitly supplied
schema/descriptor modules through the Artifacts extension contract; DotNet/CLI
composition registers the exact selected package modules. CommandLine is packed as a .NET tool whose command is
`program-kit`. CapabilityBundle is content-only. Product packing uses an explicit
`program-kit/build/ProgramKit.Pack.proj` allow-list rather than packing the
solution.

```text
Architecture -> Artifacts
Quality -> Artifacts
Planning -> Artifacts, Quality
Development -> Artifacts, Planning
Modularity -> Artifacts
Modularity.InProcess -> Modularity
Serialization.JSON -> Artifacts, DI.Abstractions 10.0.10, .NET 10 System.Text.Json
Tasks.Core -> Artifacts
Tasks -> Tasks.Core, Modularity, DI.Abstractions 10.0.10
Tasks.InProcess -> Tasks
Tasks.Hosting -> Tasks, selected Microsoft.Extensions.* 10.0.10 hosting/health packages
Tasks.Schedules -> Tasks.Core
Tasks.Schedules.Cronos -> Tasks.Schedules, Cronos 0.13.0
DotNet.Metadata -> Artifacts
Workbench -> Artifacts, Architecture, Quality, Planning, Development,
             Serialization.JSON
Workbench -> JsonSchema.Net 9.3.0
DotNet -> Architecture, Quality, Planning, Workbench, DotNet.Metadata,
          Serialization.JSON, Tasks.Core, Tasks, Tasks.Schedules
CommandLine -> Workbench, DotNet
CapabilityBundle -> canonical .agents bytes (content input only)

consumer Domain.Core -> Tasks.Core
consumer Domain.Core -> Modularity (only when independently owning contributions)
consumer Domain.Core -> Serialization.JSON (only when owning typed JSON contributions)
consumer Feature -> consumer Domain.Core, CShells.Abstractions 0.0.28
consumer task Feature -> Tasks (only when contributing tasks)
consumer API Feature -> consumer Domain.Core,
                        CShells.AspNetCore.Abstractions 0.0.28
consumer task API Feature -> Tasks (only when contributing tasks)
consumer schedule Feature -> Tasks.Schedules (only when schedule helpers are selected)
consumer cron schedule Feature -> Tasks.Schedules.Cronos (only when cron is selected)
generated Host -> selected consumer Core / Feature / Provider contracts,
                  selected Modularity/task implementation/hosting,
                  exact CShells runtime
isolated consumer fixture -> packed Program Kit packages
```

An arrow points from consumer to dependency. No arrow points from universal
contracts to Workbench, .NET, CLI, capability assets, CShells, or a platform
extension. A consumer of universal contracts therefore does not transitively
acquire those packages. CShells abstractions are intentionally outgoing
transitive dependencies of concrete feature libraries, but remain absent from
domain `.Core`, Modularity, Tasks contracts, and universal Program Kit packages.

Tests are grouped into `Orbyss.ProgramKit.UnitTests` and
`Orbyss.ProgramKit.ConformanceTests` to avoid a speculative project-per-library
catalog. Fixture projects live only under
`program-kit/fixtures/observatory-scheduling/` and use their fictional domain
vocabulary there.

The non-product project graph is fixed as follows:

| Project identity | Direct project/package references | Pack rule |
| --- | --- | --- |
| `Orbyss.ProgramKit.UnitTests` | all Program Kit library assemblies | never pack |
| `Orbyss.ProgramKit.ConformanceTests` | all product assemblies including CommandLine; reads CapabilityBundle as content | never pack |
| `ObservatoryScheduling.Core` | Modularity, Serialization.JSON, Tasks.Core | fixture-profile only |
| `ObservatoryScheduling.Scheduling.FirstAvailable` | ObservatoryScheduling.Core, Tasks, Tasks.Schedules, Tasks.Schedules.Cronos, CShells.Abstractions `0.0.28` | fixture-profile only |
| `ObservatoryScheduling.Scheduling.Api` | ObservatoryScheduling.Core, CShells.AspNetCore.Abstractions `0.0.28` | fixture-profile only |
| `ObservatoryScheduling.Visibility.Static` | ObservatoryScheduling.Core, CShells.Abstractions `0.0.28` | fixture-profile only |
| `ObservatoryScheduling.Constraints.DarknessWindow` | ObservatoryScheduling.Core, CShells.Abstractions `0.0.28` | fixture-profile only |
| `ObservatoryScheduling.Api` | Core, selected concrete projects, Tasks.Hosting/InProcess, exact CShells API runtime | never pack |
| `ObservatoryScheduling.Console` | Core, selected concrete projects, Tasks.Hosting/InProcess, exact CShells runtime | never pack |
| `ObservatoryScheduling.Worker` | Core, selected concrete projects, Tasks.Hosting/InProcess/Schedules/Schedules.Cronos, exact CShells runtime | never pack |
| `ObservatoryScheduling.Tests` | Core, concrete projects, and all three generated hosts | never pack |

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
- consumer domain `.Core` packages may reference Modularity, task contract
  package Tasks.Core, and Serialization.JSON when they own typed JSON
  contributions. Every concrete feature directly references the accepted
  CShells abstraction package appropriate to its host surface; it references
  Tasks only when it contributes task definitions, handlers, activation
  bindings, middleware, schedules, or occurrence calculators;
- a provider specialization may reference its declared base implementation;
- a host may reference selected domain core, feature/provider, and composition
  packages;
- a bridge may reference the public contract surfaces it joins.

### Forbidden and mechanically checked

- every Program Kit project -> `core/`, `features/`, `lab/`, future engine
  assembly/namespace, `.agents/`, or `.codex/` at runtime;
- universal contracts -> Workbench, DotNet, CLI, capability bundle, CShells,
  provider, host, or platform package;
- Workbench -> Modularity, Tasks, DotNet.Metadata, CShells, or any host/provider
  implementation; package-specific schemas/descriptors enter through explicit
  registered Artifacts modules;
- Modularity, Tasks.Core, Tasks, Tasks.Schedules, or
  Tasks.Schedules.Cronos -> CShells or a concrete host/provider implementation;
- any package -> Newtonsoft.Json;
- Program Kit/fixture code outside Serialization.JSON -> direct `JsonSerializer`
  calls, including inside an allow-listed untyped boundary;
- Program Kit/fixture code outside an exact reviewed untyped-boundary allow-list
  -> any `JsonElement`, `JsonNode`, or `JsonDocument` use; and any public API or
  durable model anywhere -> those DOM types;
- domain core -> concrete feature, provider, host, bridge, or helper;
- unrelated concrete feature/provider -> another implementation;
- helper -> domain core activation or cross-domain consumer;
- host -> domain policy implementation;
- tool/fixture -> ambient scan, unresolved wildcard input, machine-local
  `bin/`/`obj/`, or unverified package bytes;
- Program Kit -> Release Cycle actions or lifecycle state.

Architecture tests inspect solution projects, project/package references,
namespaces, schema enums, JSON API/type use, fixture boundaries, and package
dependency metadata. They report stable diagnostics rather than inferring
semantic quality.

## 8. Deterministic Workbench and CLI

The stable library surface accepts streams/bytes plus explicit registries and
returns values/diagnostics; it does not read a working directory implicitly.
All JSON parsing, typed materialization, serialization, and canonical output
flows through an exact frozen Serialization.JSON profile; Workbench adapters do
not create ad hoc `JsonSerializerOptions` or expose DOM values.
Core operations are `Validate`, `Normalize`, `Digest`, `RenderMarkdown`,
`AnalyzeDependencies`, `BuildVersionMap`, `AssessMigration`,
`CheckConformance`, and `Generate` through an explicitly selected extension
identity. The universal Workbench has no .NET-specific API.
File-system effects sit behind an explicit workspace/output abstraction with a
declared write root and collision policy.

The CLI maps those operations to:

```text
program-kit validate <artifact...> | --manifest <artifact-manifest>
program-kit normalize <artifact> --output <file|->
program-kit digest <artifact>
program-kit render <artifact> --format markdown --output <file|->
program-kit graph <design> [--format text|json|dot]
program-kit versions map --manifest <component-manifest> --output <file|->
program-kit versions assess --observed <selection> --target <selection> --output <file|->
program-kit check <design|plan> | --manifest <workspace-manifest> [--profile <id>]
program-kit packages prepare-local --workspace-manifest <file> --output <package-root>
program-kit dotnet generate-host <api|console|worker> --shell <shell.json> --host <host-id> --artifact-manifest <file> --output <dir>
program-kit dotnet publish-local --shell <shell.json> --host <host-id> --artifact-manifest <file> --package-manifest <file> --output <dir>
program-kit capabilities render-catalog <index> --output <file|->
program-kit capabilities verify-bundle <bundle>
```

All input paths and registered extensions are explicit. Built-in .NET support is
registered by identity at composition. A later external extension manifest must
name exact extension ID/version, package/assembly identity, SHA-256, entry point,
and compatibility; the loader may load that exact entry point but may not scan
assemblies or folders. Implementing a general external loader is `deferred`;
the baseline proves the explicit in-process registry.

For host generation/publish, the explicit artifact manifest maps the shell's
exact Version Map/Selection references to normalized relative input paths below
its explicitly declared read root and repeats their identities, versions, and
digests. Resolution outside that manifest/root or a path/digest mismatch fails;
the shell remains free of machine-local paths.

Diagnostics use stable families `PKART`, `PKARC`, `PKPLN`, `PKQLT`, `PKDEV`,
`PKMOD`, `PKJSN`, `PKTSK`, `PKVER`, `PKNET`, `PKPUB`, and `PKCLI` plus a three-digit
number. Human text may improve without changing identity. Exit codes are `0`
success, `1` conformance failure, `2` usage/input/I/O failure, and `3`
unexpected internal failure. JSON diagnostic output is available for scripts.

## 9. .NET language kit

The .NET kit translates approved universal entities into deterministic
`net10.0` source and guidance for:

- one solution and cohesive independently packageable projects;
- per-domain `.Core` contract projects, concrete feature/provider projects,
  optional focused helpers, bridges, and small composition-root hosts;
- namespace ownership based on domain language and validated project/package
  reference direction;
- explicit dependency-injection registrations, service lifetimes, ownership and
  disposal, cancellation, diagnostics, serialization, error contracts, and
  configuration ownership;
- stable feature/extension IDs and selected composition;
- domain contributions, middleware, metadata, and task definition/handler
  registration without assembly or output-folder scanning;
- approved package-folder manifests naming exact package ID, version, SHA-256,
  activation ID, and compatibility rather than scanning a directory;
- API, Console, and Worker composition-root profiles, their integrator
  documents, explicit configuration schemas, and optional operational health
  listeners;
- public API and SemVer consequence classification;
- unit, registration, behavior, integration, architecture, analyzer, warning,
  pack, and isolated-consumer obligations.

CShells is the accepted .NET feature ABI, not an adapted provider. Every ordinary
concrete feature directly implements `IShellFeature` from exact
`CShells.Abstractions`; an API feature that maps endpoints implements
`IWebShellFeature` from exact `CShells.AspNetCore.Abstractions`. Generated hosts
reference the matching full runtime packages and pass only the reviewed selected
feature assemblies to CShells' explicit assembly-selection API. Domain `.Core`,
universal contracts, Modularity, and task-contract packages remain CShells-free.
Duplicate/missing feature or activation identities, incompatible ABI claims,
extra packages, digest mismatch, or unselected assemblies fail before host
composition.

Program Kit-owned `shell.json` is reviewed composition intent. It contains a
schema/version, exact immutable input Version Map/Selection references, shared
composition provider/exact ABI and selected feature
package/activation references, exact JSON serialization profile/contribution
selections, and one or more explicit host entries. Each host owns its identity,
version/kind, exact DotNet target/generator profiles, selected shells/features,
host packages, operation/configuration bindings, compatibility requirements,
task runtime requirements, and optional explicit health configuration. It
contains no
secret, machine-local package folder, publish path, or ambient-discovery rule.
The baseline fixture has exactly one API, Console, and Worker entry in the same
reviewed document. Generated `shell.lock.json` contains shared selection locks
plus one `hostLocks[]` entry per host and binds the resolved closures/digests as
specified in Section 4.3.

The CLI reads the shell itself through fixed
`pkid:profile:program-kit:json-dotnet-shell@1.0.0`; that profile is part of the
DotNet generator selection and is not chosen by values inside the document it
must parse.

Its logical shape is:

```text
DotNetShellDocument
  schema, version
  inputVersionMapRef { identity, version, digest }
  inputVersionSelectionRef { identity, version, digest }
  composition { provider: cshells, abiVersion, shells[] }
  features[] { id, activationId, packageRef { id, version, sha256 } }
  jsonSerialization { profileRefs[], contributionRefs[] }
  hosts[] {
    id, version, kind: api|console|worker
    dotNetTargetProfileRef, generatorProfileRef
    shellRefs[], featureActivationRefs[]
    hostPackages[] { id, version, sha256 }
    operationBindings[]
    configurationSchemaRefs[]
    taskRuntimeRequirements[]
    health? {
      endpoints[] { kind, path, listenerRef, includeTags[], excludeTags[],
                    statusCodes, responseProfileRef, cachePolicy,
                    authorizationRef, documentationPolicy }
      listeners[] { id, scheme, address, port, exposure,
                    authenticationRef, tlsRef, hostFilterRef }
    }
    compatibility
  }
  compatibility
```

`documentationPolicy` is `excluded` or an exact owned operation reference; it
is never an automatic inclusion switch.

The command's `--host` must resolve exactly one entry whose kind matches the
requested generator; absence, ambiguity, or mismatch fails. The generator
also verifies the shell's exact input Version Map/Selection references before
producing a lock; a missing, stale, or digest-mismatched input fails. The generator
materializes that host's target-profile identity/digest, SDK, TFM, and language
version into its `hostLocks[]` entry, repository/host `global.json`, and
Directory.Build enforcement. Generated build checks reject `TargetFrameworks`,
any `TargetFramework` other than `net10.0`, or an SDK/language/profile mismatch.

The three baseline profiles are:

- **API:** generates a small ASP.NET Core/CShells composition root, explicit
  selected feature assemblies, endpoint mapping owned by `IWebShellFeature`,
  configuration binding/validation, optional explicitly configured health
  mappings, and OpenAPI 3.2.0 from owned operation contracts;
- **Console:** generates a Generic Host/CShells composition root, exact command
  registration, DotNet-owned descriptor-driven parser source/configuration
  bindings, exhaustive exit-code mapping, help/completion projection, and
  `OpenConsoleDocument`; the generated project does not reference DotNet,
  Workbench, DotNet.Metadata, or CommandLine at runtime; and
- **Worker:** generates a Generic Host/CShells composition root, selected hosted
  and task-runtime components, cancellation/shutdown behavior, configuration
  validation, optional explicitly configured operational health listener, and
  the deliberately small `OpenWorkerDocument`. When scheduled activation
  bindings exist, it explicitly selects and wires the approved in-process
  scheduler/trigger loop and calculators; it does not invent trigger, misfire,
  overlap, or task semantics.

Health registration and endpoint mapping are separate. Tasks.Hosting may add
named checks for runtime-started/accepting state, queue readiness, registry
validity, and schedule-definition validity; `AddHealthChecks` alone maps no
endpoint. A generated host emits an actual health listener and
`MapHealthChecks` calls only when `shell.json` names every enabled
`liveness`/`readiness`/`startup` path, listener scheme/address/port,
exposure, check-tag selector, health-to-HTTP status map, cache policy, response
profile/redaction, authentication/authorization policy reference, and TLS/host
filter where applicable. Baseline listener ports are explicit integers from
`1` through `65535`; dynamic port `0` is rejected so the reviewed selection,
generated configuration, startup evidence, and documented endpoint cannot
diverge. The fixture uses process-only liveness and `ready`
tag-filtered readiness; ordinary task failure never becomes a liveness failure,
while an explicitly readiness-critical startup task may contribute readiness.
Default ASP.NET status mapping, if selected rather than overridden, is recorded
as Healthy `200`, Degraded `200`, and Unhealthy `503`, with response caching
suppressed. Console and Worker hosts acquire ASP.NET Core listener dependencies
only under that explicit selection. A wildcard or non-loopback listener without
reviewed transport and authorization policy fails validation, and `RequireHost`
alone is not treated as a secure management-port boundary: the generated host
must bind the declared listener and verify that the actual local port equals the
declared port. Each health mapping is isolated to its listener by a dedicated
management pipeline/server or an early `Connection.LocalPort` predicate that
rejects the request before the health handler; the same route on an API listener
must not execute. Host-header filtering is additive only and never substitutes
for local-port isolation. Documentation
policy is either `excluded` or an exact owned operation reference; health is
never automatically added to OpenAPI.

### 9.1 Local package consumption and application publish

Local package preparation and application publishing are separate backed
operations. `packages prepare-local` accepts an explicit workspace-package
manifest and output root. That manifest names the source root and every allowed
source project path, package ID, exact version, package role, and expected
target plus exact immutable input Version Map/Selection identity, version, and
digest references and normalized locator paths beneath the declared source
root; the operation never discovers projects from the current
directory or a solution. It packs only that allow-list into the output root and
writes a
canonical `local-package-root-manifest.json` containing every first-party
package ID/version, relative nupkg path and SHA-256, source-project identity, and
immutable input Version Map/Selection identity, version, and digest references.

`dotnet publish-local` separately accepts exact `shell.json`, `--host`, artifact
manifest, package-root manifest, and output-root parameters. It validates every manifest package
before generating the selected host in an isolated temporary workspace,
restores in locked mode with an initially empty `RestorePackagesPath` under that
validated temporary root and HTTP caching disabled, then runs project-level
`dotnet publish --no-restore`. The operation clears fallback-package folders and
does not read the machine-global packages folder.
Its generated `NuGet.Config` clears ambient sources and uses package-source
mapping: first-party Program Kit and selected fixture package IDs resolve only
from the manifest-bound local folder; exact reviewed external dependencies
and their locked transitive closure resolve only from
`https://api.nuget.org/v3/index.json`. Mapping enumerates the approved external
package IDs and contains no catch-all that could resolve a first-party ID
remotely. The local folder is a restore source, not a feed service. No push,
feed transport, publication, deployment, signing, or Release Cycle state is
created.

Conformance pre-seeds conflicting bytes in a test-controlled temporary path
configured to simulate the ambient global package cache; it never writes the
user's real cache. The operation must ignore those bytes, and every restored
first-party package must still match the manifest-bound local nupkg hash while
every external package matches its lock/source evidence.

Output is rooted at:

```text
<output-root>/publish/<host-id>/<host-version>/
  <configuration>_<tfm>_<rid-or-portable>_<deployment-mode>/
```

Each leaf contains `local-publish-manifest.json` with host/project identity,
SDK/TFM/RID/configuration/deployment mode, shell/generator/Version Map/lock and
package-root/package-selection digests (using the immutable input-map revision
that produced the publish), and every relative output path, size, and SHA-256.
That file table covers every published application output except the manifest
itself; the manifest instead carries the standard envelope integrity digest
computed with `integrity.digest` omitted. It is written through the selected
Program Kit JSON profile and canonicalized before that digest is recorded.
Paths are normalized below the explicit root; collision default is fail and no
operation performs arbitrary cleanup. A repository-owned
`publish-dotnet-application-locally` capability is authored only after this
deterministic operation and its conformance tests work; it remains a thin
human-session wrapper and is not initially added to the distributable
three-capability bundle.

`IDotNetPlatformKit` remains the explicit seam for later desktop or richer
platform profiles. React remains a separate later language/platform kit through
the universal extension model, not a .NET platform implementation.

## 10. Synthetic vertical fixture

All fictional artifacts and projects are contained in
`program-kit/fixtures/observatory-scheduling/`. Its domain purpose is “Schedule
observatory viewing sessions”; its vocabulary is forbidden from Program Kit
universal contracts, source namespaces, schemas, diagnostics, capability
procedures, and generated package documentation.

The fixture proves:

1. structured human intent and an artifact-decision set;
2. an architecture design with `ObservatoryScheduling.Core`;
3. a default scheduling feature implementing the accepted CShells ABI;
4. a replaceable visibility-forecast provider and an ordered additive planning
   constraint;
5. domain contribution publication, ordered middleware, metadata extraction,
   an explicitly registered typed JSON converter/source-generation contribution,
   and one immediate, one volatile background, and one in-process scheduled-task
   path with controlled time;
6. generated API, Console, and Worker host compositions selected by exact
   `shell.json`/lock manifests, including explicit health configuration;
7. a structured AI explanation artifact with separate invariant instructions
   and supplied intent values;
8. a human-readable implementation plan and requirement/test trace;
9. before/after Version Maps and a real schema/contract/handler/host migration
   whose complete reverse closure, terminal dispositions, and ordered actions
   are verified;
10. forbidden reference, provider isolation, registration, JSON model-first/
    canonicalization/contribution, task, schedule, health, behavior,
    determinism, schema, injection/redaction, and migration tests; and
11. locally packed Program Kit packages consumed and locally published by
    isolated samples: first-party packages come only from the manifest-bound
    folder, reviewed external packages come only from the explicit NuGet source,
    and there is no engine reference or feed transport.

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

The separately repository-owned `publish-dotnet-application-locally`
capability is authored at the same later capability work only after the backed
operation passes. It requires explicit shell, host, artifact-manifest, package-
manifest, and output parameters, invokes that operation without redefining it,
and reports its manifest;
it cannot push, deploy, sign, or create release state and is not included in the
initial three-capability bundle.

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
- JSON readers apply explicit byte/depth/token limits, reject duplicate names
  and invalid Unicode, and permit polymorphism only through an allow-listed,
  schema-owned discriminator. Type-name materialization and global converter or
  options mutation are forbidden.
- Package and extension bytes are verified against reviewed SHA-256 values
  before use. A directory listing confers no trust.
- The Workbench has no network authority. Restore is a separate execution-profile
  concern and is disabled unless explicitly selected.
- Operations accept cancellation and distinguish validation, compatibility,
  authorization, I/O, and internal failures with stable diagnostics.
- Delayed/background task requests carry immutable authority/correlation
  references rather than credentials or captured service scopes. Acceptance
  cancellation and execution cancellation are distinct, and cancellation of a
  schedule never silently cancels an already accepted instance.
- In-process task capacity, maximum concurrency, retention, shutdown, retry,
  idempotency, misfire, and overlap policies are explicit. No volatile runtime
  can satisfy a durable or exactly-once requirement.
- Generation is idempotent for identical canonical inputs. Existing differing
  files require an explicit collision policy; default is fail.
- Compatibility is not inferred from SemVer alone, particularly for pre-1.0
  packages. Exact observed/target selections and multi-dimensional evidence
  govern; schema majors are not silently compatible and migrations produce new
  versioned artifacts with provenance.
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
7. A consumer `.Core` defines contributions and task definitions without
   selecting an implementation; a concrete CShells feature registers handlers,
   while the generated host selects exact in-process defaults.
8. A typed consumer model is serialized twice through the same frozen profile
   and produces identical canonical bytes; an ambiguous converter contribution,
   direct DOM-shaped public contract, or Newtonsoft dependency fails before use.
9. Controlled schedule inputs produce the same ordered delay/interval/cron
   occurrences without starting a timer or task.
10. API, Console, and Worker generators consume one reviewed `shell.json`, emit
   exact locks and their respective integrator documents, and map no health
   listener unless explicitly configured. Configured health remains outside
   OpenAPI absent an owned operation reference.
11. A schema or serialization-profile change reaches its contracts, converters,
    handlers, features, documents,
    generated hosts, package locks, and local publish outputs through the
    Version Map reverse closure; removing one terminal disposition or required
    action invalidates the plan.
12. A generated host restores first-party packages only from the
    manifest-bound local folder and exact reviewed external packages only from
    the explicit nuget.org source, then publishes into the supplied output root
    with a verified per-file manifest; no package is pushed and no deployment or
    release state appears.
13. A user asks to release. Development routing returns `flow-unavailable` and
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
| Universal/modularity/serialization/task contracts, schemas, Workbench, CLI, .NET/host/publish kit | `aspirational` | Designed here; no source exists |
| Synthetic fixture and test evidence | `aspirational` | Designed here; no artifacts exist |
| Three development capabilities and capability bundle | `deferred` | Must wait for working backing contracts/tools |
| Repository local-publish capability | `deferred` | Must wait for the backed local-publish operation and remains outside the initial bundle |
| Direct CShells feature ABI and generated composition | `aspirational` | Accepted exact packages/source model; implementation awaits approval |
| Durable/distributed tasks and scheduler | `deferred` | Baseline provides volatile execution/scheduling and pure calculation only |
| React, desktop, and richer platform kits | `deferred` | Approved baseline includes only API/Console/Worker profiles |
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
- authoritative NuGet/package/source pages for `MSTest.Sdk` `4.3.2`,
  `JsonSchema.Net` `9.3.0`, Microsoft Extensions `10.0.10`, accepted CShells
  `0.0.28` packages/source, Cronos `0.13.0` verified tag-object and hash-bound
  package evidence, evaluated
  alternative `NCrontab` `3.4.0`, and Quartz `3.18.2`, plus
  relevant Microsoft Learn guidance;
- .NET 10 `System.Text.Json` custom-converter, contract-customization,
  source-generation, options-reuse/freeze guidance, and RFC 8785 JCS;
- the JSON Schema Draft 2020-12 Core and Validation specifications;
- the official OpenAPI Specification `3.2.0` and official schema iteration
  `3.2/schema/2025-11-23`.

Exact external references:

- [MSTest.Sdk 4.3.2](https://www.nuget.org/packages/MSTest.Sdk/4.3.2),
  [MSTest SDK guidance](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-sdk),
  [JsonSchema.Net 9.3.0](https://www.nuget.org/packages/JsonSchema.Net/9.3.0),
  [Microsoft.Extensions.DependencyInjection 10.0.10](https://www.nuget.org/packages/Microsoft.Extensions.DependencyInjection/10.0.10),
  [its Abstractions package](https://www.nuget.org/packages/Microsoft.Extensions.DependencyInjection.Abstractions/10.0.10),
  [Hosting.Abstractions 10.0.10](https://www.nuget.org/packages/Microsoft.Extensions.Hosting.Abstractions/10.0.10),
  [Microsoft.Extensions.Diagnostics.HealthChecks 10.0.10](https://www.nuget.org/packages/Microsoft.Extensions.Diagnostics.HealthChecks/10.0.10),
  and [its Abstractions package](https://www.nuget.org/packages/Microsoft.Extensions.Diagnostics.HealthChecks.Abstractions/10.0.10);
- [CShells source and feature guidance](https://github.com/valence-works/cshells),
  [release tag `0.0.28`](https://github.com/valence-works/cshells/releases/tag/0.0.28),
  [verified commit `29fe542835696131278fcacc6cdb9a6186fc0447`](https://github.com/valence-works/cshells/commit/29fe542835696131278fcacc6cdb9a6186fc0447),
  [source MIT license](https://raw.githubusercontent.com/valence-works/cshells/29fe542835696131278fcacc6cdb9a6186fc0447/LICENSE),
  [CShells.Abstractions 0.0.28](https://www.nuget.org/packages/CShells.Abstractions/0.0.28),
  [CShells.AspNetCore.Abstractions 0.0.28](https://www.nuget.org/packages/CShells.AspNetCore.Abstractions/0.0.28),
  [CShells 0.0.28](https://www.nuget.org/packages/CShells/0.0.28), and
  [CShells.AspNetCore 0.0.28](https://www.nuget.org/packages/CShells.AspNetCore/0.0.28);
- [Cronos 0.13.0](https://www.nuget.org/packages/Cronos/0.13.0),
  [release tag `v0.13.0`](https://github.com/HangfireIO/Cronos/releases/tag/v0.13.0),
  [peeled commit `aeb3bff2048c551018cdd16ac11951d0d4bc20d5`](https://github.com/HangfireIO/Cronos/commit/aeb3bff2048c551018cdd16ac11951d0d4bc20d5),
  and [source/package MIT license](https://raw.githubusercontent.com/HangfireIO/Cronos/aeb3bff2048c551018cdd16ac11951d0d4bc20d5/LICENSE);
- [NCrontab 3.4.0](https://www.nuget.org/packages/NCrontab/3.4.0) and its
  [source release](https://github.com/atifaziz/NCrontab/releases/tag/v3.4.0),
  and [Quartz 3.18.2](https://www.nuget.org/packages/Quartz/3.18.2), consulted
  only as alternative schedule-library evidence;
- [JSON Schema Draft 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core)
  and [Validation](https://json-schema.org/draft/2020-12/json-schema-validation);
- [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html),
  [.NET custom converters](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/converters-how-to),
  [contract customization](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/custom-contracts),
  [source generation](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/source-generation),
  and [options reuse/freeze behavior](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/configure-options);
- [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) and its
  [2025-11-23 JSON Schema](https://spec.openapis.org/oas/3.2/schema/2025-11-23.html);
- [.NET 10 ASP.NET Core health checks](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-10.0)
  and [OpenAPI inclusion/exclusion metadata](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/include-metadata?view=aspnetcore-10.0);
- [.NET package validation](https://learn.microsoft.com/en-us/dotnet/fundamentals/apicompat/package-validation/overview),
  [NuGet version ranges](https://learn.microsoft.com/en-us/nuget/concepts/package-versioning),
  and [`dotnet publish`](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish).

The exact selected package/assembly bytes are additionally bound as follows;
restore evidence must also match each immutable NuGet catalog SHA-512 and
repository commit:

| Selection | `.nupkg` SHA-256 | Selected assembly SHA-256 |
| --- | --- | --- |
| `CShells.Abstractions` `0.0.28`, `net10.0` | `ae1a15e770445b9b9e912312e6ba3257b7ec3ea63559a5be71ac6065c0d2c7c4` | `758829021180f6642c4307b1b27ad71ec50f3349646e866b6a5bb842b377d2e2` |
| `CShells.AspNetCore.Abstractions` `0.0.28`, `net10.0` | `2770a11cae2d9d6e1537ddae8d7757bd7b8af3aa548f3e2d94cc16feaf43d01d` | `344bba7a15aef0178d808414d416821e97a365d6502c2b68b8d1939e13a53ad4` |
| `CShells` `0.0.28`, `net10.0` | `ac99877eea0132799e0a55c0b351480067dad34f9166fc835acb73cc77fe7ab0` | `b3ef22f666403cb8e020b5beab69f054b8bd2adb9fba21b398eb93430766ba0b` |
| `CShells.AspNetCore` `0.0.28`, `net10.0` | `3fd728566376da2a7cbf7ebd12a2a7fa9171e35c756ab261e45680c37131658e` | `8efe299a0070c95dbe247e9e4d95678f1be39422fe24793fbd6b54515a530e77` |
| `Cronos` `0.13.0`, selected `net6.0` | `6612c6605dc3d16f613052da3c5b22ba9e80c08253ccc5c91bb40b4c3a0939f7` | `e0ad7c799904f1b663ab090b32665e0e90ede27699937588900845383064ba03` |

Immutable NuGet catalog evidence is linked for
[CShells.Abstractions](https://api.nuget.org/v3/catalog0/data/2026.06.12.22.07.24/cshells.abstractions.0.0.28.json),
[CShells.AspNetCore.Abstractions](https://api.nuget.org/v3/catalog0/data/2026.06.12.22.07.59/cshells.aspnetcore.abstractions.0.0.28.json),
[CShells](https://api.nuget.org/v3/catalog0/data/2026.06.12.22.07.59/cshells.0.0.28.json),
[CShells.AspNetCore](https://api.nuget.org/v3/catalog0/data/2026.06.12.22.07.24/cshells.aspnetcore.0.0.28.json),
and [Cronos](https://api.nuget.org/v3/catalog0/data/2026.04.29.09.29.32/cronos.0.13.0.json).

NuGet metadata for CShells retains the historical
`github.com/sfmskywalker/cshells` repository identity, which redirects to
`github.com/valence-works/cshells`; both identities plus the immutable commit are
recorded so a future redirect cannot change the binding.

These external pages were accessed on `2026-07-22` and `2026-07-23`; versioned URLs are retained
as provenance rather than replaced by “latest” links.

The canonical `author-and-maintain-skills` procedure was not invoked because no
capability is needed or permitted before its Program Kit backing exists. No
sibling repository, Spec Kit source, build output, or machine-local package
artifact was consulted. CShells, Cronos, NCrontab, and Quartz consultation was
limited to the authoritative sources named above. External lookup was limited
to the package, source, documentation, and specification references listed
above. This is a
clean-room provenance attestation for the bounded source set, not proof of an
unknowable negative.

## 16. Human decision requested

Approve, reject, or request changes to this architecture together with
`implementation-plan.md`, using the exact digests in `review-manifest.json`.
Approval authorizes only the plan's Program Kit work. It does not authorize
engine-domain design, an unreviewed CShells/API change, a Release Cycle,
artifact-feed publication/deployment, or any material deviation from the
accepted architecture and scope.

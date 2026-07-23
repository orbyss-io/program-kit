---
artifact-kind: bootstrap-implementation-plan
artifact-id: pkid:plan:program-kit:baseline
artifact-version: 0.2.0
intended-contract: pkid:schema:program-kit:implementation-plan
intended-contract-version: 1.0.0
design-ref-id: pkid:design:program-kit:baseline
design-ref-version: 0.2.0
design-digest: sha256:829407d25e7cb637d036031134989095308c0ee31b600523982c4a9252048d5e
review-state: awaiting-human-approval
implementation-status: scaffolded
bootstrap-exception: true
---

# Program Kit baseline implementation plan

## 1. Plan authority and exact-digest gate

This document is the human-authored bootstrap precursor to the proposed
`implementation-plan/1.0.0` contract. It is separate from the architecture design,
has its own identity and version, and is bound to the design by
`review-manifest.json`.

The frontmatter `design-digest` MUST equal the SHA-256 of the exact reviewed
`architecture-design.md`, and `review-manifest.json` MUST repeat that binding and
the SHA-256 of this plan. A placeholder, mismatch, or stale manifest makes the
review set unapprovable and unimplementable. No approval record may be created
and no source implementation may start while any binding is invalid.

After those exact bytes are available, implementation may start only when an
explicit human approval binds both exact design and plan SHA-256 values. The
first implementation action records that decision as a bootstrap approval
record with the principal reference, separate authority reference, decision
evidence/correlation, accepted scope, conditions, and decision time supplied by
the human session. The bootstrap record remains part of provenance after normal
contract instances exist.

Approval authorizes only the paths and outcomes in this plan. Renewed design and
plan approval is required before any material change to package/project
boundaries, dependency direction, canonical representation, identity/digest
rules, authority semantics, the `.NET 10`-only target, direct CShells ABI use,
task semantics, generator surfaces, migration closure, capability scope,
fixture scope, or the Release Cycle boundary.

## 2. Exact inputs

| Input | Authority and use |
| --- | --- |
| Human mission and accepted review comments | Primary requested outcomes and non-negotiable boundaries, including `.NET 10` only, domainless modularity, System.Text.Json-only serialization and tasks, direct CShells feature ABI, all three host generators, local publish, and migration closure |
| Repository `AGENTS.md` and boundary README files | Workspace rules, ownership, and dependency source truth |
| `.agents/capabilities/INDEX.md` | Sole authority for capability availability once capability work begins |
| Final approved `architecture-design.md` `0.2.0` exact digest | Architecture implemented by this plan |
| Final approved `implementation-plan.md` `0.2.0` exact digest | Exact work authorization and trace |
| Human bootstrap approval record | Authority to begin only the accepted scope |
| .NET SDK `10.0.302` | Pinned build SDK; every Program Kit-owned and generated project targets only `net10.0` |
| Canonical DotNet target profile | `pkid:profile:program-kit:dotnet-10` version `1.0.0`, binding SDK `10.0.302`, `rollForward: disable`, `allowPrerelease: false`, TFM `net10.0`, and C# 14 |
| Initial first-party package selections | Every baseline Program Kit package is exactly `0.1.0-alpha.1`; fixture library packages used only by the isolated proof are exactly `0.1.0-fixture.1` |
| NuGet.org exact packages | `MSTest.Sdk` `4.3.2`, `JsonSchema.Net` `9.3.0`, and exact `10.0.10` Microsoft Extensions DI, Hosting abstractions, Diagnostics.HealthChecks, and HealthChecks abstractions packages |
| Direct CShells packages `0.0.28` | `CShells.Abstractions` for ordinary features, `CShells.AspNetCore.Abstractions` for API features, and matching `CShells`/`CShells.AspNetCore` host runtimes; all bind lightweight tag `0.0.28`, verified commit `29fe542835696131278fcacc6cdb9a6186fc0447`, source MIT license SHA-256 `9447cc96460b01c8c6ed647705a3423d15b3a9936cb67154cdf26d1dddfb598d`, and the exact package/assembly hashes in the design |
| Cronos `0.13.0` source/package selection | Candidate implementation for optional `Tasks.Schedules.Cronos` only; binds verified annotated tag object `b313eaae11b4909f8c1ea12f1a1c19d640b932c2`, peeled commit `aeb3bff2048c551018cdd16ac11951d0d4bc20d5`, MIT license SHA-256 `48e6c7a1b9a9e687391e6613269b4aa81b6c910f8e2bb53bee7a7e86e53b584a`, nupkg SHA-256 `6612c6605dc3d16f613052da3c5b22ba9e80c08253ccc5c91bb40b4c3a0939f7`, and selected dependency-free `net6.0` DLL SHA-256 `e0ad7c799904f1b663ab090b32665e0e90ede27699937588900845383064ba03`; grammar, boundary, timezone/DST, and golden-timeline conformance remains mandatory and no native `net10.0` asset is claimed |
| NCrontab `3.4.0` and Quartz `3.18.2` source/package evidence | Reviewed alternatives only: NCrontab is not selected because it exposes occurrence calculation without a comparable owned timezone/DST contract; Quartz is not selected because it is a full scheduler rather than the required parser/calculator boundary |
| JSON Schema Draft 2020-12 Core and Validation | Program Kit schema dialect |
| .NET 10 `System.Text.Json` and RFC 8785 | Only JSON runtime plus authoritative custom-converter/type-metadata/options behavior and canonical-byte algorithm for exact profiles `pkid:profile:program-kit:json-meta@1.0.0`, `pkid:profile:program-kit:json-contracts@1.0.0`, and `pkid:profile:program-kit:canonical-json-rfc8785@1.0.0`; no Newtonsoft.Json compatibility surface |
| Fixed DotNet shell JSON profile | `pkid:profile:program-kit:json-dotnet-shell@1.0.0`, owned by DotNet and used before host-selected contributions to parse `DotNetShellDocument` without reversing the Serialization.JSON dependency |
| Initial Program Kit integrator schemas | Open Console is `pkid:schema:program-kit:open-console@1.0.0`; Open Worker is `pkid:schema:program-kit:open-worker@1.0.0` |
| OpenAPI `3.2.0` and official schema iteration `3.2/schema/2025-11-23` | Exact external authority for generated OpenAPI projections; schema is vendored with source, license, and digest |

`program-kit/NuGet.Config` clears ambient sources and permits only the reviewed
source and package set. Lock files bind the resolved closure. A sibling
repository, ambient plugin, machine-local `bin/`/`obj/`, unreviewed package, or
machine-local build output is not source truth. Local folder packages and
published application outputs are test inputs/outputs only when their explicit
roots and digests are named by the operation.

## 3. Planned outputs and canonical ownership

| Output | Canonical owner/representation | Projection or evidence |
| --- | --- | --- |
| Artifact, design, plan, quality, development, and approval contracts | Versioned Draft 2020-12 schemas under `program-kit/schemas/` | Immutable .NET views, semantic validation, and schema/model drift tests |
| Architecture designs and implementation plans | Separate canonical JSON envelopes linked by exact ID/version/digest | Deterministic Markdown and dependency/trace graphs |
| Version topology and selection | `VersionedComponentManifest`, `VersionMapDocument`, and `VersionSelectionDocument` | Compatibility classification, reverse-impact closure, migration plan, and `shell.lock.json` |
| Domainless contribution and middleware semantics | `Orbyss.ProgramKit.Modularity` | Deterministic in-process implementation in `.Modularity.InProcess` |
| Domainless JSON mechanics | `Orbyss.ProgramKit.Serialization.JSON` owns model-first System.Text.Json operations, frozen versioned profiles, explicit converter/source-generation contributions, strict reads, and RFC 8785-compatible canonical bytes | Typed/contribution/canonicalization fixtures plus model-first and forbidden-dependency/API scans |
| Primitive generator metadata | `Orbyss.ProgramKit.DotNet.Metadata` attributes and dependency-free descriptors derived from explicit `DotNetSourceDescriptor` values | Generator inputs and conformance evidence; never Roslyn/assembly/output scanning |
| Task meaning and public execution contracts | `Orbyss.ProgramKit.Tasks.Core` owns definitions, request/response contracts, instances, attempts, activation bindings, schedules, occurrences, and every public handler/runner/dispatcher/scheduler/occurrence-calculator/status/cancel interface | Typed artifacts, lifecycle projections, fixture instances, and compatibility evidence |
| Task registration and common coordination | `Orbyss.ProgramKit.Tasks` | Explicit registration extensions, frozen registries, middleware, retry/idempotency coordination, and contribution integration |
| Volatile task execution and host integration | `.Tasks.InProcess` and `.Tasks.Hosting` respectively | Controlled-time lifecycle tests and task health checks |
| Provider-neutral schedule helpers | `.Tasks.Schedules` owns pure one-shot-delay, fixed-delay, and fixed-interval descriptors/factories/calculators without registration ownership or a third-party parser | Boundary and controlled-time tests |
| Optional cron occurrence provider | `.Tasks.Schedules.Cronos` alone owns the exact accepted Cronos dialect, adapter, dependency, and provider evidence | Acceptance-gate report and independently enumerated golden timelines |
| .NET composition intent | Reviewed Program Kit-owned `shell.json` with shared selections and explicit `hosts[]` | Exact `shell.lock.json` shared locks plus one `hostLocks[]` entry per selected host, generated `net10.0` API/Console/Worker source, package locks, and provenance |
| .NET target selection | Canonical `DotNetTargetProfile` `pkid:profile:program-kit:dotnet-10@1.0.0` | Exact `dotNetTargetProfileRef` per `hosts[]` entry; identity/version/digest, SDK, TFM, and C# version materialized in the matching `hostLocks[]`, `global.json`, and Directory.Build enforcement |
| Integrator documentation | Owned operation contracts | OpenAPI 3.2.0, comprehensive `pkid:schema:program-kit:open-console@1.0.0`, and deliberately small `pkid:schema:program-kit:open-worker@1.0.0` projections |
| Local package and application proof | Explicit workspace/artifact manifests, package root/manifest, host selection, and publish root | Hash-bound package/content/dependency reports and per-host application publish manifests; no ambient discovery, feed transport, or deployment |
| CLI transport | `Orbyss.ProgramKit.CommandLine` over Workbench/.NET services | Stable diagnostics, exit codes, and golden command tests |
| Synthetic proof | Observatory Scheduling fixture below its fixture root | API, Console, Worker, task scheduling, version migration, package, and publish evidence |
| Development capabilities | Canonical procedures in `.agents/capabilities/<id>/CAPABILITY.md`, including the separately backed local-publish procedure | Thin active-provider wrappers; exact-byte bundle contains only the three initial development-flow definitions |
| Bootstrap history | Files in `program-kit/bootstrap/` | Self-hosted comparison finding; bootstrap history is never rewritten to manufacture equivalence |

The mechanically enforced package direction is:

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
             Serialization.JSON, JsonSchema.Net 9.3.0
DotNet -> Architecture, Quality, Planning, Workbench, DotNet.Metadata,
          Serialization.JSON, Tasks.Core, Tasks, Tasks.Schedules
CommandLine -> Workbench, DotNet
CapabilityBundle -> canonical .agents bytes (content input only)

consumer Domain.Core -> Tasks.Core
consumer Domain.Core -> Modularity (only for independently owned contributions)
consumer Domain.Core -> Serialization.JSON (only for owned typed JSON contributions)
consumer Feature -> Domain.Core, CShells.Abstractions 0.0.28
consumer task Feature -> Tasks (only when contributing tasks)
consumer API Feature -> Domain.Core, CShells.AspNetCore.Abstractions 0.0.28
consumer task API Feature -> Tasks (only when contributing tasks)
consumer schedule Feature -> Tasks.Schedules (only when selected)
consumer cron schedule Feature -> Tasks.Schedules.Cronos (only when selected)
generated Host -> selected Core/Feature/provider contracts,
                  selected Modularity/task implementation/hosting,
                  exact CShells runtime
```

Committed canonical and generated review artifacts carry owner, contract/schema
version, source/provenance references, canonical representation, digest,
compatibility/migration state, and truthful implementation status. Transient
build, package, test, and isolated-consumer output lives only in an ignored
explicit artifact root or validated temporary root and is not durable evidence
by itself.

## 4. Requirement trace

The work-unit column names the first unit that must make the requirement true;
later closure units may add proof but may not move ownership.

| ID | Required outcome and canonical owner | First work unit | Observable proof |
| --- | --- | --- | --- |
| `PK-R001` | Standalone Program Kit solution and package boundary; engine depends on Kit, never the reverse | `PK-W010` | Project/package/namespace graph and isolated contract consumer exclude engine, fixture, CShells, CLI, and agent dependencies |
| `PK-R002` | Stable PKID, envelope, canonical-profile/digest, provenance, status, compatibility contracts, and RFC vector fixtures live in Artifacts | `PK-W010` | Schema/model and official-vector fixture bytes are committed and drift-checked; operational serialization/canonical-byte proof is owned by `PK-R035`/`PK-W015` |
| `PK-R003` | Universal architecture language for domains, vocabulary, contracts, operations, components, references, extensions, boundaries, and scenarios | `PK-W010` | Full synthetic design validates and renders every semantic category |
| `PK-R004` | Nine-question intent-to-artifact decision and supported artifact-kind ownership | `PK-W010` | Missing, contradictory, and complete decision fixtures resolve to one canonical owner |
| `PK-R005` | Design and implementation plan remain separate durable artifacts linked by exact identity/version/digest and complete trace | `PK-W010` | A changed design digest or missing requirement disposition invalidates the plan |
| `PK-R006` | Human-only exact design/plan approval, conditions, evidence, and supersession | `PK-W000` | Absent, conditional, mismatched, rejected, and superseded approval cases fail closed |
| `PK-R007` | Reusable quality/test-specification architecture with execution profiles and digest-bound evidence | `PK-W010` | Test selection and dependency-closure fixtures validate deterministically |
| `PK-R008` | Deterministic Workbench APIs for parse, validate, normalize, digest, render, graph, version, migration, check, and bounded generation | `PK-W020` | Repeat runs across culture/time-zone settings are byte-identical |
| `PK-R009` | Scriptable CLI with explicit inputs/outputs, stable diagnostic families, and exit codes | `PK-W050` | CLI golden tests match library outcomes and distinguish conformance, usage/I/O, and internal failure |
| `PK-R010` | Canonical `pkid:profile:program-kit:dotnet-10@1.0.0` and complete `.NET 10`-only API, Console, and Worker generation from explicit `shell.json` `hosts[]`; no `net8.0` or multitargeting | `PK-W040` | Exact `--host` selection, per-host lock, profile/SDK/TFM/language scans, and negative builds prove SDK `10.0.302`, roll-forward disabled, prerelease disabled, `net10.0`, C# 14, and exact profile digest |
| `PK-R011` | CShells' published feature contracts are the direct outgoing ABI: no Program Kit adapter or duplicate `IFeature` | `PK-W040` | Feature packages expose exact abstractions `0.0.28`; hosts resolve matching exact runtimes; forbidden-reference tests keep core/universal packages CShells-free |
| `PK-R012` | Synthetic Observatory Scheduling vertical proves contracts through generated hosts and evidence | `PK-W060` | All three hosts build/test from the same reviewed shell and repeat deterministically |
| `PK-R013` | Bootstrap design/plan carried through implemented contracts without rewriting history | `PK-W080` | Self-hosted artifacts validate and a structured comparison records real differences |
| `PK-R014` | Development routing has three outcomes and digest-bound receipts without granting authority | `PK-W010` | Routed/non-routed/unavailable/no-authority fixtures enforce zero-or-one capability selection |
| `PK-R015` | Three backed human-session capabilities for develop, design, and implement-plan flows | `PK-W070` | Canonical definitions, thin wrappers, index truth, and direct/routed refusal fixtures agree |
| `PK-R016` | Exact-byte content-only capability bundle with three allow-listed definitions and separately listed optional wrappers | `PK-W070` | Package allow-list, per-file digest, tamper, exclusion, and copied-but-unregistered tests pass |
| `PK-R017` | Explicit-manifest local pack, source-mapped locked isolated restore, build/test, and API/Console/Worker publish proof without feed transport | `PK-W065` | Fresh consumers use hash-bound package manifests rather than project refs; all three publish manifests hash every application output and carry a separate canonical envelope digest |
| `PK-R018` | No Release Cycle states, procedures, commands, publication, deployment, promotion, or feed transport | `PK-W010` | Reviewed source/schema/CLI/capability scans find no lifecycle behavior |
| `PK-R019` | Truthful provenance and implemented/scaffolded/deferred/aspirational status on artifacts and final report | `PK-W010` | Metadata completeness checks and clean-room attestation pass |
| `PK-R020` | Revisable structural-pattern catalog with criteria, trade-offs, examples, and mechanical/human checks | `PK-W020` | Catalog schema/render/migration and fixture-use tests pass |
| `PK-R021` | Provider adapter and consumer-shape separation remains explicit where adapters exist; direct CShells ABI is not wrapped | `PK-W020` | Graph accepts consumer policy above provider contracts and rejects ownership inversion |
| `PK-R022` | OpenAPI 3.2.0, `pkid:schema:program-kit:open-console@1.0.0`, and `pkid:schema:program-kit:open-worker@1.0.0` are deterministic projections of owned operation identities; DotNet owns descriptor-driven Console parser-source generation | `PK-W040` | Official/internal-schema, parser/help/completion, provenance, identity, golden, migration, and published-dependency-closure tests pass |
| `PK-R023` | Domainless contribution, typed publisher, middleware pipeline, immutable registry, ordering, and identity contracts live in Modularity | `PK-W015` | Zero/many-handler, ordering, cancellation, reentrancy, aggregation, and registration tests define the contract |
| `PK-R024` | Deterministic default contribution publisher and middleware runner live only in Modularity.InProcess | `PK-W015` | Fail-fast/continue and short-circuit tests pass without persistence, queue, retry, outbox, transaction, or cross-process claims |
| `PK-R025` | Primitive attributes and normalized dependency-free metadata descriptors for generation live in DotNet.Metadata | `PK-W015` | Explicit descriptor-input tests prove deterministic results and reject Roslyn, assembly, or output discovery |
| `PK-R026` | Local application publish accepts exact shell/host/artifact-manifest/package-manifest/output inputs and emits deterministic, collision-safe manifests | `PK-W065` | Source-mapped locked restore through a fresh operation-local package cache plus project-level `dotnet publish --no-restore` for API, Console, and Worker produces the required rooted layout, hashes every application output, and gives each manifest a non-self-referential envelope digest |
| `PK-R027` | The Version Map/Selection contracts and engine represent every approved boundary kind and typed dependency edge with exact revision/digest selections | `PK-W020` | Boundary-kind, edge-kind, exact-selection, digest, compatibility, and stale-lock engine fixtures pass |
| `PK-R028` | The migration engine computes fixed-point reverse impact, atomic cycle cohorts, causal paths, one terminal disposition, and ordered required actions per impacted node | `PK-W020` | Synthetic engine fixtures prove every terminal/action class and reject incomplete, ambiguous, contradictory, or unknown closure |
| `PK-R029` | Tasks.Core owns all seven task semantic identities, task request/response contracts, and every public typed handler, runner, dispatcher, scheduler, occurrence-calculator, status-reader, and cancellation-requester contract | `PK-W025` | A consumer Domain.Core uses task meaning through Tasks.Core alone; dependency scans reject Tasks/CShells/runtime imports |
| `PK-R030` | Tasks owns implementation-neutral descriptors, immutable registries, DI registration, the activation-scope resolver seam, common coordination, task middleware, retry/idempotency coordination, and optional lifecycle-contribution integration | `PK-W030` | Exact duplicate registration is idempotent; conflicts, gaps, ambiguity, incompatible ranges, post-freeze mutation, and middleware cycles fail composition |
| `PK-R031` | Tasks.InProcess and Tasks.Hosting provide bounded volatile execution and Generic Host integration with fresh attempt scopes and controlled shutdown | `PK-W030` | Overflow, status, cancellation boundary, retry, idempotency, concurrency, retention, drain/cancel, activity/meter, and health-check tests pass |
| `PK-R032` | Tasks.Schedules provides provider-neutral pure one-shot-delay, fixed-delay, and fixed-interval descriptors/factories/calculators with no third-party parser or registration ownership | `PK-W030` | Boundary/controlled-time tests pass; package contains no cron-provider semantics, registry, timer, queue, lease, persistence, host, or executor |
| `PK-R033` | Optional Tasks.Schedules.Cronos alone owns the exact Cronos dependency/dialect and must pass the provider and time-zone-rule-fingerprint gates before selection | `PK-W030` | Full selected grammar, next/previous boundaries, IANA/Windows zones, DST gaps/ambiguity, deterministic zone ID/tzdata source/version/horizon fingerprints, independently enumerated golden timelines, and package/source/hash/asset checks pass |
| `PK-R034` | Host health is explicit composition intent and separate from registration; documentation inclusion is explicit per operation | `PK-W040` | No implicit endpoint/listener exists; unsafe exposure fails; Console/Worker acquire ASP.NET only for configured listeners; OpenAPI includes health only by exact owned operation reference |
| `PK-R035` | Serialization.JSON is the sole System.Text.Json mechanics boundary with non-extensible meta profile `pkid:profile:program-kit:json-meta@1.0.0`, model-first contract profile `pkid:profile:program-kit:json-contracts@1.0.0`, deterministic converter/type-metadata contributions, exact canonical profile `pkid:profile:program-kit:canonical-json-rfc8785@1.0.0`, exact reviewed file/API DOM exceptions, and no Newtonsoft support | `PK-W015` | Meta-bootstrap, typed round-trip/canonical vectors, source-generation/profile/contribution order/conflict/version, resource-limit, and forbidden reflection/direct-serializer/non-allow-listed-DOM tests pass |
| `PK-R036` | A repository-owned `publish-dotnet-application-locally` capability is a thin wrapper over the proven `dotnet publish-local` operation and remains outside the initial three-capability bundle | `PK-W070` | Canonical definition/wrapper/index/catalog tests bind exact shell/host/artifact-manifest/package-manifest/output parameters while bundle allow-list and scans reject packing, feed/deploy/release behavior |
| `PK-R037` | The complete selected baseline—including serialization profiles/converters, task/schedule/provider revisions, CShells, generated documents/hosts, locks, packages, local publishes, and capabilities—has a recomputed Version Map and action-complete migration assessment | `PK-W090` | Final map contains every selected node; closure contains every node reachable from changed roots, retains every causal path, and fails when any reached owner, target, terminal disposition, required action, or evidence item is removed; unrelated nodes have explicit out-of-closure proof when claimed unaffected |

## 5. Work units, sequencing, and allowed edits

### `PK-W000` Record the exact bootstrap decision

- **Depends on:** final design and plan bytes, recomputed SHA-256 values, and an
  updated `review-manifest.json` with no placeholder or stale digest.
- **Allowed edits:** `program-kit/bootstrap/` only.
- **Output:** immutable bootstrap approval record binding the exact design and
  plan, approving principal/authority references, evidence/correlation, accepted
  scope, conditions, and decision time supplied by the human session.
- **Bootstrap exception:** because normal capability and receipt contracts do
  not exist yet, this contemporaneous record is the audit record; it is not
  mislabeled as a DevelopmentReceipt or attributed to a future capability.
- **Stop:** do not proceed on mismatch, rejection, ambiguity, an open condition,
  or anything other than explicit human approval.

### `PK-W010` Establish the `.NET 10` build spine and universal contracts

- **Depends on:** `PK-W000`.
- **Allowed edits:** repository `global.json`; `program-kit/ProgramKit.sln`;
  `program-kit/NuGet.Config`; `program-kit/Directory.*`;
  `program-kit/src/Orbyss.ProgramKit.{Artifacts,Architecture,Quality,Planning,Development}/`;
  `program-kit/schemas/`;
  `program-kit/tests/Orbyss.ProgramKit.UnitTests/`; and
  `program-kit/tests/Orbyss.ProgramKit.ConformanceTests/`.
- **Outputs:** canonical `DotNetTargetProfile`
  `pkid:profile:program-kit:dotnet-10` version `1.0.0`, binding SDK `10.0.302`,
  `rollForward: disable`, `allowPrerelease: false`, TFM `net10.0`, and C# 14;
  deterministic build/package settings; exact central versions and lock files;
  universal Draft 2020-12 schemas—including VersionedComponentManifest,
  VersionMap, VersionSelection, migration-definition/assessment contracts owned
  by Artifacts—immutable typed views; canonical-profile/digest contracts and RFC
  vector fixtures (not yet a canonicalizer); stable diagnostic catalog;
  approval and receipt contracts; Release Cycle exclusion.
- **Compatibility:** every baseline Program Kit package begins at exact version
  `0.1.0-alpha.1`; fixture library packages begin at exact
  `0.1.0-fixture.1`; schema contracts begin at `1.0.0`. Pre-1.0 packages still
  use exact NuGet constraints and explicit migration classification.
- **Observation:** locked restore and warning-clean build succeed from the
  explicit NuGet config; scans find neither `net8.0` nor multitargeting; universal
  package closure excludes Workbench, DotNet, CLI, Tasks implementations,
  CShells, capabilities, hosts, fixture, engine, and release behavior. Tests
  reject a free-form TFM, `TargetFrameworks`, a mismatched SDK/language/profile,
  roll-forward, or prerelease SDK selection.

This is the first coherent implementation slice. It creates working contracts
and validation tests, not empty project shells.

### `PK-W015` Implement domainless modularity, JSON mechanics, and generator metadata

- **Depends on:** `PK-W010`.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.Modularity/`;
  `program-kit/src/Orbyss.ProgramKit.Modularity.InProcess/`;
  `program-kit/src/Orbyss.ProgramKit.Serialization.JSON/`;
  `program-kit/src/Orbyss.ProgramKit.DotNet.Metadata/`;
  `program-kit/schemas/serialization/`; matching unit/conformance tests and
  contract fixtures.
- **Modularity outputs:** `IDomainContribution`, typed contribution handlers and
  publisher contracts, generic middleware pipeline contracts, immutable
  registries, stable identities, ordering descriptors, cancellation and failure
  semantics. A domain `.Core` may reference Modularity to declare its own
  contributions; the host selects an implementation.
- **In-process outputs:** deterministic publisher/pipeline behavior for zero or
  many handlers, explicit ordering, reentrancy, short-circuit, cancellation,
  result aggregation, and fail-fast/continue policies.
- **Metadata outputs:** primitive attributes and normalized immutable descriptors
  based only on explicitly supplied `DotNetSourceDescriptor` values. The package
  exposes no Roslyn type/dependency and performs no assembly, `bin/`/`obj/`,
  output-folder, or ambient AppDomain scanning; any compiler-symbol adapter is a
  later separately reviewed package.
- **JSON outputs:** `IProgramKitJsonSerializer`, exact
  `JsonSerializationProfileRef`, immutable profile registry/builder, explicit
  stable `IJsonSerializationContribution` support for typed converters,
  declared converter-factory target families, and source-generated
  contexts/type-info resolvers. Serialization.JSON directly references exact
  `Microsoft.Extensions.DependencyInjection.Abstractions` `10.0.10`; its
  `IServiceCollection` extensions create one shell-scoped
  `ProgramKitJsonBuilder`. Explicitly selected features call
  `AddJsonSerializationContribution`; generated composition exports and merges
  only the descriptors selected for one host after every feature completes
  `ConfigureServices`, then freezes the host-scoped registry and options before
  any read/write. Contributions are ordered topologically with stable identity
  tie-breaks, and composition fails on
  duplicate claims, gaps, cycles, or changed bytes under one identity/version.
- **Baseline typed profile:**
  non-extensible `pkid:profile:program-kit:json-meta@1.0.0` uses a built-in
  source-generated context for envelope headers and profile descriptors/
  selections only; it knows no platform-specific shell type and accepts no
  contributed converter or reflection fallback. The separate
  `pkid:profile:program-kit:json-contracts@1.0.0` uses exact schema/source-generated
  names, case-sensitive reads, no comments/trailing commas/unmapped members,
  strict numbers, no implicit null omission, no reference preservation/cycles,
  maximum depth `64`, explicit byte/token limits, and no reflection fallback or
  global enum/date/polymorphism convention. Successful durable writes are
  canonical bytes; pretty JSON is projection only. Meta selection documents use
  json-meta; Program Kit semantic documents select json-contracts. A different
  consumer convention requires a new owned/versioned profile and migration edges
  rather than baseline mutation.
- **Canonical JSON:** implement
  `pkid:profile:program-kit:canonical-json-rfc8785@1.0.0` as the design's
  strict JCS subset after typed serialization. Strict readers reject duplicate
  names, invalid Unicode, non-NFC canonical strings, negative zero, non-finite
  or out-of-JCS-precision numeric values, and configured byte/depth/token limit
  violations. Larger exact integers/high-precision decimals use
  schema-constrained strings. Canonicalization is not a converter extension
  point.
- **Model-first policy:** `JsonElement`, `JsonNode`, and `JsonDocument` are
  forbidden by default in Program Kit/fixture source, public APIs, and durable
  models; code outside Serialization.JSON cannot call `JsonSerializer` directly.
  A reviewed untyped boundary requires an exact file/API allow-list entry with
  owner, justification, byte/depth limits, and its typed-model or validated
  `CanonicalJsonValue` conversion point. The sole baseline DOM exception is
  Workbench's internal `JsonSchema.Net` adapter for arbitrary pre-model JSON; no
  DOM type crosses its public boundary. Typed converters and all other mechanics
  use `Utf8JsonReader`/`Utf8JsonWriter`; canonicalization additionally uses
  bounded per-object member buffers rather than a BCL DOM. Newtonsoft.Json is
  forbidden everywhere.
- **Exclusions:** no persistence, durable queue, retry, replay, outbox,
  transaction boundary, cross-process delivery, ambient/global JSON options,
  type-name polymorphism, general mutable JSON document model, code generator,
  or host policy.
- **Observation:** standalone package tests and forbidden-reference scans prove
  deterministic typed round trips/canonical vectors, contribution ordering and
  source-generation composition, stable limits/diagnostics, and that contracts
  do not acquire Workbench, Tasks, CShells, Newtonsoft, or host dependencies.

### `PK-W020` Implement deterministic Workbench, Version Map, and migration closure

- **Depends on:** `PK-W015` for the stable Serialization.JSON mechanics only.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.Workbench/`; version/migration fixtures;
  matching unit/conformance tests.
- **Workbench outputs:** parse, schema/semantic validate, normalize, digest,
  render, dependency analysis, conformance check, bounded generation, and stable
  typed diagnostics. All JSON flows through exact frozen Serialization.JSON
  profiles. Workbench references only Artifacts, Architecture, Quality, Planning,
  Development, Serialization.JSON, and JsonSchema.Net; it accepts explicitly
  supplied schema/descriptor modules through the Artifacts extension contract
  and has no compile-time Modularity, Tasks, DotNet.Metadata, CShells, or host
  dependency. Failure or cancellation publishes no partial declared output.
- **Version outputs:**
  `VersionedComponentManifest` for every selected, persisted, generated, or
  consumed boundary; typed `VersionMapDocument` edges; exact observed/target
  `VersionSelectionDocument`; and a migration assessment containing complete
  causal paths, exactly one terminal disposition, and ordered required actions
  for every impacted node. DotNet owns `shell.lock.json` creation in W040.
- **Acyclic map rule:** Version Maps are immutable staged revisions. Each
  generated lock/host/document/package/publish manifest binds the exact input
  map/selection that produced it; a later map may add that output as a node but
  never causes the output to be rewritten to reference a map containing itself.
- **Edge vocabulary:** at least `implements`, `reads`, `writes`, `validates`,
  `uses-contract`, `wire-schema-of`, `serializes-with`,
  `contributes-converter`, `canonicalizes-with`, `publicly-exposes`,
  `package-depends-on`, `configured-by`, `generated-by`, `projects`, `composes`,
  `handles-task`, `schedules`, `migrates`, and `verifies`.
- **Closure rule:** compute fixed-point reverse impact; treat cycles as atomic
  migration cohorts; classify each boundary dimension as `editorial`,
  `compatible-additive`, `conditionally-compatible`, `breaking`, or `unknown`;
  retain all causal paths.
- **Disposition/action rule:** assign exactly one terminal disposition from
  `unaffected-with-proof`, `compatible-after-actions`, `major-upgrade`,
  `redesign`, `manual-review`, or `blocked`, plus ordered actions selected from
  `retest`, `regenerate`, `recompile`, `repackage-or-relock`,
  `migrate-artifact`, `migrate-configuration`, `add-adapter`, and
  `drain-or-migrate-pending-work`. Unaffected requires proof and no actions;
  compatible-after-actions requires at least one.
- **Observation:** repeat runs are byte-identical across culture/time-zone
  settings; incomplete/unknown closure fails closed; generated projections are
  detected as stale; forbidden-reference scans prove the platform-neutral graph.

### `PK-W025` Implement Tasks.Core semantic and public execution contracts

- **Depends on:** `PK-W010`; may proceed beside `PK-W015` after artifact identity
  rules are fixed.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.Tasks.Core/`; task schemas and fixtures;
  matching unit/conformance tests.
- **Seven owned identities:** `TaskDefinition` (stable requested work and its
  authority/cancellation/idempotency/retry/observability/resource policy),
  `TaskRequest` (rejectable proposal before acceptance), `TaskInstance`
  (accepted work pinned to definition and payload contracts), `TaskAttempt`
  (one execution attempt), `TaskActivationBinding` (definition revision to
  opaque handler and owning feature/activation identities, selected runtime,
  middleware, retry, idempotency, and—when scheduled—exact misfire/overlap
  policy references), `TaskScheduleDefinition` (exact typed descriptor artifact
  identity/version/digest/schema plus calculator profile, never DOM/dictionary
  configuration), and `TaskOccurrence`.
- **Public interfaces:** typed `ITaskHandler<TRequest,TResponse>` plus immediate
  runner, background dispatcher, scheduler, `ITaskOccurrenceCalculator`, status
  reader, and cancellation requester contracts. Tasks.Core owns the request and
  response contract references used by those interfaces. Definitions, requests,
  and responses reference explicit artifact/schema versions; task payloads are
  not hidden behind runtime-owned unversioned dictionaries.
- **Lifecycle:** accepted, waiting, running, retry-wait, succeeded, failed, and
  cancelled, with the last three terminal. Cancellation-requested is a fact,
  separate from terminal cancellation and from acceptance cancellation.
- **Boundary:** a consumer Domain.Core references only Tasks.Core for task use.
  Tasks.Core references Artifacts only and contains no DI registration,
  middleware implementation, queue, scheduler loop, clock, persistence, host,
  health, CShells, or transport code.
- **Observation:** a standalone domain-core fixture defines versioned immediate,
  background, and scheduled work without importing `Orbyss.ProgramKit.Tasks`,
  Microsoft Extensions, Cronos, or CShells.

### `PK-W030` Implement task registration, volatile runtime, hosting, and schedules

- **Depends on:** `PK-W015` and `PK-W025`.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.Tasks/`;
  `program-kit/src/Orbyss.ProgramKit.Tasks.InProcess/`;
  `program-kit/src/Orbyss.ProgramKit.Tasks.Hosting/`;
  `program-kit/src/Orbyss.ProgramKit.Tasks.Schedules/`;
  `program-kit/src/Orbyss.ProgramKit.Tasks.Schedules.Cronos/`; exact package
  metadata, locks, provider evidence, and matching tests/fixtures.
- **Tasks outputs:** implementation-neutral descriptors, immutable registries,
  registration extensions, common coordination, dispatch/execution middleware,
  retry/idempotency coordination, the provider-neutral
  `ITaskActivationScopeResolver` seam, and optional domain-contribution lifecycle
  integration. Tasks directly references exact
  `Microsoft.Extensions.DependencyInjection.Abstractions` `10.0.10`. The
  generated host calls `AddProgramKitTasks` for each selected shell
  `IServiceCollection`; a concrete task-contributing feature calls
  `AddTaskDefinition`, `AddTaskHandler`, `AddTaskActivationBinding`,
  `AddTaskMiddleware`, `AddTaskSchedule`, and `AddTaskOccurrenceCalculator`.
- **Handler ownership:** Program Kit defines, registers, invokes, and hosts the
  handler contract but never implements consumer work. Each concrete consumer
  CShells feature implements its own `ITaskHandler<,>` and registers it
  explicitly. Generated CShells-aware DotNet glue implements
  `ITaskActivationScopeResolver` by mapping the opaque feature/shell activation
  reference to the selected shell's scope factory and handler registration;
  Tasks.InProcess invokes only through that CShells-free seam and Tasks.Hosting
  requests a fresh scope for every attempt.
- **Composition rules:** byte-identical repeat registration is idempotent.
  Conflicting bytes, multiple handlers, missing definition/handler/feature,
  incompatible version range, or cyclic middleware fail composition before
  registries freeze. After every selected feature completes `ConfigureServices`,
  generated composition exports and merges the selected-shell descriptors; the
  task, schedule, JSON, and health-contributor registries freeze together before
  host start; registration after freeze or execution before freeze fails. Dispatch
  middleware runs once before acceptance; execution middleware runs per attempt;
  retry surrounds attempts.
- **InProcess outputs:** immediate execution and a bounded volatile queue and
  scheduler loop; explicit maximum concurrency/retention; `TimeProvider`;
  in-memory lifecycle state; overflow rejection; separate acceptance/execution
  cancellation; default no retry; and optional exact-definition/process/window
  idempotency. It claims no durability, recovery, exactly-once, distributed
  execution, broker, lease, or cross-process coordination. Its scheduler
  consumes explicitly registered `ITaskOccurrenceCalculator` contracts from
  Tasks.Core and depends on neither Tasks.Schedules nor a cron provider.
  Every occurrence that is to run creates a normal `TaskRequest` carrying the
  occurrence causal reference, derives any idempotency key from the exact
  schedule/occurrence/definition revisions, and passes the same validation,
  authorization, dispatch middleware, capacity, and acceptance path.
  Skipped/coalesced/misfired occurrences create no instance or attempt.
  Tasks.InProcess depends only on Tasks. Optional lifecycle observation resolves
  Modularity's `IDomainContributionPublisher` contract through Tasks; the
  generated host separately selects Modularity.InProcess or another compatible
  publisher, and absence disables only that observation middleware.
- **Hosting outputs:** `UseInProcessTaskRuntime` selects the implementation and
  `AddProgramKitTaskHosting` integrates Generic Host. Every attempt receives a
  fresh DI scope. Shutdown has explicit drain/cancel behavior; caller scope,
  principal, and secrets are never captured. State changes are authoritative;
  contributions, activities, and meters are post-transition observations.
- **Provider-neutral schedule outputs:** Tasks.Schedules owns pure one-shot
  delay, fixed-delay-after-terminal-completion, and anchored fixed-interval
  descriptors/factories/calculators only; Tasks owns `AddTaskSchedule` and
  occurrence-calculator registration, and features register the selected helper
  plus exact typed descriptor artifact/schema explicitly. No schedule definition
  stores `JsonElement`, dictionary, or provider-owned unversioned configuration.
  Durations are explicit
  `TimeSpan` values and fixed delay cannot overlap itself. Interval occurrences
  are `anchor + n * period` for a positive fixed duration, with the next
  occurrence strictly after the cursor; calendar units are invalid. It has no
  third-party schedule-parser dependency or cron semantics.
- **Optional Cronos provider:** Tasks.Schedules.Cronos alone carries Cronos and
  implements the named `cronos/0.13` dialect. It explicitly selects exact
  Cronos `0.13.0`, `CronFormat.Standard` five-field or
  `CronFormat.IncludeSeconds` six-field input, DOM/DOW AND when both are
  restricted, and no year field. Numeric/name syntax, special characters,
  aliases, and macros are accepted exactly when the locked Cronos profile
  documents them. Any supported hashed/jitter form requires an explicit stable
  descriptor seed; ambient randomness is forbidden. Its descriptor records the
  expression, format, exact `TimeZoneInfo` identifier, profile, and environment/
  timezone-data/selection evidence. DST behavior is delegated to Cronos and
  `TimeZoneInfo`, not reinvented in Program Kit. The selection binds a
  deterministic zone-rule fingerprint to the exact zone identifier, time-zone
  data source/version, and explicit bounded evaluation horizon. Composition and
  host startup recompute it from the selected `TimeZoneInfo`; a mismatch blocks
  activation and requires a new provider selection plus migration assessment.
- **Policies:** misfire is exactly skip, fire-once-now, or bounded catch-up;
  overlap is exactly allow, skip, or queue-one; every catch-up/queue bound is
  explicit. These are scheduler activation-binding policies, not occurrence
  calculator or cron-expression semantics. Neither schedule package contains a
  clock, timer, queue, persistence, lease, host, scheduler loop, or executor.
- **Cronos acceptance gate:** before selection, conformance covers the complete
  selected grammar, next and previous occurrence boundaries, representative
  IANA and Windows zones, spring-forward gaps, fall-back ambiguity, and
  independently enumerated golden timelines. It also verifies package `0.13.0`,
  verified annotated tag object `b313eaae11b4909f8c1ea12f1a1c19d640b932c2`,
  peeled commit `aeb3bff2048c551018cdd16ac11951d0d4bc20d5`, exact
  source/package MIT license digest, immutable NuGet catalog/package hashes, and
  the actual selected dependency-free `net6.0` asset/assembly digest for the
  `net10.0` consumer. It also independently verifies the bound zone-rule
  fingerprint over its declared horizon and rejects ambient-only time-zone
  evidence. Documentation
  must not call it net10-native. A failed gate blocks this provider and triggers
  design review; it does not leak Cronos types/semantics into Tasks.Core or
  Tasks.Schedules and does not force a replacement parser under the same package
  identity. NCrontab `3.4.0` remains unselected for lack of a comparable owned
  timezone/DST contract; Quartz `3.18.2` remains unselected as a full scheduler.
- **Health contracts:** Tasks.Hosting registers named checks for runtime started,
  acceptance readiness, bounded-queue readiness, registry validity, and schedule
  validity. Registration maps no listener or endpoint.
- **Observation:** controlled-time concurrency, overflow, cancellation, retry,
  idempotency, state, scope, shutdown, provider-neutral schedule, provider-gate,
  time-zone fingerprint/startup mismatch, DST, misfire, overlap, optional
  lifecycle publishing, registry freeze, health, and forbidden-reference tests
  pass.

### `PK-W040` Implement the .NET kit, direct CShells composition, and host generators

- **Depends on:** `PK-W020` and `PK-W030`; this is the join between the generic
  Workbench and the stable task/composition registrations.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.DotNet/`; DotNet schemas/templates/assets;
  API/Console/Worker generator tests and fixture-contract paths; the vendored
  OpenAPI schema location and its provenance record.
- **Direct feature ABI:** ordinary feature packages directly reference exact
  `CShells.Abstractions` `0.0.28` and implement its accepted `IShellFeature`
  contract. Endpoint-mapping features directly reference exact
  `CShells.AspNetCore.Abstractions` `0.0.28` and implement its accepted
  `IWebShellFeature` contract. No Program Kit feature adapter, mirror interface, or
  provider-neutral replacement is created. Hosts pin matching `CShells` and,
  for API hosts, `CShells.AspNetCore` `0.0.28` runtime packages.
- **Boundary:** Domain.Core, universal contracts, Modularity, Tasks.Core, Tasks,
  Serialization.JSON, Tasks.Schedules, and Tasks.Schedules.Cronos remain
  CShells-free. Only concrete feature packages and generated composition hosts
  acquire the relevant CShells dependencies.
- **`shell.json`:** owns exact immutable input Version Map/Selection identity,
  version, and digest references, shared exact CShells provider/ABI/shell and feature
  package/activation selections, exact JSON serialization profiles/contributions,
  and one or more `hosts[]` entries. Each host entry owns identity, version,
  `api|console|worker` kind, exact
  `pkid:profile:program-kit:dotnet-10@1.0.0` and generator-profile references,
  selected shell/feature activations, pinned host packages, operation and
  configuration bindings, task-runtime requirements, optional explicit health,
  and compatibility. It contains no secret, local package root, publish-output
  root, or ambient-discovery rule. The fixture uses one API, Console, and Worker
  entry in the same reviewed document. Every generated JSON document flows
  through exact frozen Serialization.JSON profiles.
- **Input resolution:** `generate-host` requires an explicit artifact manifest
  that maps the shell's exact Version Map/Selection references to normalized
  relative input paths below its explicitly declared read root and repeats their
  identities, versions, and digests. Missing, unlisted, path-escaping, stale, or
  digest-mismatched inputs fail; the shell contains no machine-local locator.
- **Shell bootstrap profile:** DotNet owns fixed, non-extensible
  `pkid:profile:program-kit:json-dotnet-shell@1.0.0` and its source-generated
  `DotNetShellDocument` context. CLI/generator composition uses it before reading
  host-selected profile/contribution values. It uses Serialization.JSON
  mechanics but permits neither consumer converters nor reflection fallback;
  Serialization.JSON remains unaware of DotNet.
- **Lock:** DotNet generates deterministic `shell.lock.json` with shared
  selection locks and exactly one `hostLocks[]` entry per selected host. Each
  entry binds that host's complete package closure per TFM, exact CShells ABI,
  features, contracts, schemas, generators, serialization selections, exact
  immutable input Version Map/Selection identity/version/digest, and package-lock
  digest. The requested `--host` must resolve exactly one entry whose kind
  matches the requested generator; absence, ambiguity, or mismatch fails. Its
  exact input Version Map/Selection references must also resolve with matching
  digests before generation. Its
  host lock materializes the target-profile identity/version/digest, SDK
  `10.0.302`, TFM `net10.0`, and C# 14; generated repository/host `global.json`
  and Directory.Build policy enforce the same values.
- **API generator:** emits a small ASP.NET Core/CShells composition root,
  selected features/providers/task hosting, owned route mappings, and OpenAPI
  3.2.0 projection.
- **Console generator:** emits a Generic Host/CShells composition root, command
  mappings/help, selected task runtime, and comprehensive Open Console
  documentation conforming to
  `pkid:schema:program-kit:open-console@1.0.0`, with document/info/host versions
  and parsing conventions, plus
  global options and commands carrying stable operation IDs, token-array command
  paths, aliases, arguments, flags/value options, arity/occurrence,
  required/default/schema/configuration bindings, conflicts/prerequisites,
  stdin/stdout/stderr contracts, exhaustive exit codes, authority, examples,
  completion/help data, deprecation, compatibility, and provenance.
- **Console parser source:** DotNet owns the descriptor-driven semantics and
  emits the parser as generated source into each Console host; no external
  command parser or DotNet/Workbench runtime dependency is selected. It consumes
  the operating system token array and never reparses a shell command string. It
  defines the `--` terminator, long/short names, `--name=value`, argument/value
  arity and occurrence, defaults, conflicts/prerequisites, culture-invariant
  typed conversion, stable diagnostics, and exhaustive exit-code mapping.
  Parsing, help, completion, and Open Console are generated from the same frozen
  descriptors. Published Console dependency graphs exclude Workbench,
  DotNet.Metadata, DotNet, and CommandLine assemblies.
- **Worker generator:** emits a Generic Host/CShells composition root, selected
  hosted/task runtime and schedules, and a deliberately small Open Worker
  document conforming to `pkid:schema:program-kit:open-worker@1.0.0`, with
  document/info/host versions and worker entries carrying stable
  operation identity, feature/activation identity, exact task-definition
  reference when applicable, versioned trigger kind/configuration-schema
  reference, input/output/error contracts, authority, cancellation,
  deprecation, compatibility, and provenance. Broker topics, acknowledgement,
  delivery guarantees, retry/dead-letter policy, leases, partitions,
  checkpoints, concurrency, backpressure, readiness, runtime health, scaling,
  and deployment topology are not standardized by this first schema.
- **Explicit health:** health registration and exposure are separate. Each
  enabled surface in `shell.json` names kind, path, `listenerRef`, include and
  exclude tags, status-code map, cache policy, response/redaction profile,
  authorization, and documentation policy. Each listener names
  scheme/address/port/exposure, authentication, TLS, and host-filter policy.
  `AddHealthChecks` alone maps nothing. Only explicit health configuration emits
  a listener and `MapHealthChecks`; wildcard or non-loopback exposure without
  complete transport/auth policy fails. Port `0` and values outside `1..65535`
  fail because baseline endpoints must be reviewable before startup.
  `RequireHost` alone is insufficient: generated code binds the declared
  listener, verifies the actual local port equals the declared port, and uses a
  dedicated management pipeline/server or early `Connection.LocalPort` predicate
  so the same route cannot execute on another listener. Host-header checks are
  additive only. The fixture proves wrong-port rejection, process-only liveness,
  `ready`-tag readiness,
  Healthy/Degraded/Unhealthy mapping to `200`/`200`/`503`, suppressed caching,
  startup-task readiness, and that ordinary task failure is not liveness.
  Console/Worker hosts acquire ASP.NET only when an explicit health listener
  requires it. Health appears in OpenAPI only through an exact owned operation
  reference; otherwise documentation policy is `excluded`.
- **Observation:** exact `--host` selection from the same reviewed shell generates
  all three deterministic, warning-clean `net10.0` hosts and matching host locks;
  negative missing/ambiguous/kind-mismatched host, missing/stale input map or
  selection, feature/package/lock/health/parser/doc cases fail with stable
  `PKNET` diagnostics. Field-specific golden/
  negative fixtures prove every Open Console and Open Worker field, identity,
  parser, compatibility, and provenance rule above. Generated checks reject
  `TargetFrameworks`, a free-form or non-`net10.0` `TargetFramework`, and any
  SDK, language-version, or target-profile mismatch.

### `PK-W050` Implement the CLI transport

- **Depends on:** `PK-W020` and `PK-W040`.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/src/Orbyss.ProgramKit.CommandLine/`; matching tests and command
  documentation.
- **Commands:** `validate`, `normalize`, `digest`, `render`, `graph`,
  `versions map`, `versions assess`, `check`,
  `dotnet generate-host <api|console|worker> --shell <file> --host <id>
  --artifact-manifest <file> --output <dir>`, `capabilities render-catalog`, and
  `capabilities verify-bundle`. W065 adds
  `packages prepare-local --workspace-manifest <file> --output <package-root>`
  and `dotnet publish-local --shell <file> --host <id> --artifact-manifest
  <file> --package-manifest <file> --output <dir>` only when their backing
  operations and tests exist.
- **Diagnostics:** stable `PKART`, `PKARC`, `PKPLN`, `PKQLT`, `PKDEV`, `PKMOD`,
  `PKJSN`, `PKTSK`, `PKVER`, `PKNET`, `PKPUB`, and `PKCLI` families. Exit `0`
  is success, `1` conformance failure, `2` usage/input/I/O failure, and `3`
  internal failure.
- **Boundary:** all paths and registrations are explicit; no implicit current
  directory/solution scan, external Console parser, package feed push,
  deployment, or capability discovery.
- **Observation:** text/JSON diagnostics and file/stdin/stdout behavior match
  library results and golden tests.

### `PK-W060` Build the Observatory Scheduling vertical proof

- **Depends on:** `PK-W030`, `PK-W040`, and `PK-W050`.
- **Allowed edits:** `program-kit/ProgramKit.sln`;
  `program-kit/fixtures/observatory-scheduling/`; fixture-specific tests and
  canonical fixture artifacts only.
- **Projects:** `ObservatoryScheduling.Core`,
  `.Scheduling.FirstAvailable`, `.Scheduling.Api`, `.Visibility.Static`,
  `.Constraints.DarknessWindow`, generated `.Api`, `.Console`, `.Worker`, and
  `.Tests`. Core directly references Modularity, Serialization.JSON, and
  Tasks.Core. Every ordinary concrete feature directly references Core and
  CShells.Abstractions; only task-contributing FirstAvailable additionally
  references Tasks, Tasks.Schedules, and the selected Cronos provider.
  Scheduling.Api directly references Core and CShells.AspNetCore.Abstractions,
  owns endpoint mappings, and does not acquire Tasks because it contributes no
  task. Hosts select the matching Modularity/Tasks/CShells runtimes explicitly.
  Every fixture library package is exactly `0.1.0-fixture.1`.
- **Outputs:** structured fictional intent, decisions, design, separate plan,
  exact Version Map/selection, one shell with API/Console/Worker `hosts[]`, a
  lock with matching `hostLocks[]`, direct CShells feature registration,
  contribution/middleware use, an owned typed JSON converter/source-generation
  contribution, immediate/background/scheduled tasks, explicit health
  configuration, all three integrator documents, and generated-source
  provenance.
- **Migration fixture:** enact a real v1-to-v2 schema/serialization-profile/
  contract/handler/host change. Compute reverse closure, terminal dispositions,
  and ordered actions; regenerate/rebuild/relock
  dependents, and demonstrate an explicit pending-instance/schedule policy:
  drain, coexist, migrate, cancel-and-recreate, or block. A pending task never
  runs silently against a newer handler.
- **Boundary:** Observatory vocabulary/behavior stays below the fixture root and
  never enters universal sources, schemas, diagnostics, or capabilities.
- **Observation:** API, Console, and Worker validate/build/test and their
  declared generated outputs repeat byte-for-byte.

### `PK-W065` Pack, restore, and publish applications locally

- **Depends on:** `PK-W060`.
- **Allowed edits:** Program Kit package metadata;
  `program-kit/build/ProgramKit.Pack.proj`; local-consumption/publish harnesses;
  isolated fixture templates;
  fixture package/publish/version-selection evidence below
  `program-kit/fixtures/observatory-scheduling/`;
  `program-kit/src/Orbyss.ProgramKit.CommandLine/` for the backed
  `packages prepare-local` and `dotnet publish-local` commands; matching tests
  and evidence definitions.
- **Package preparation:** `packages prepare-local --workspace-manifest <file>
  --output <package-root>` consumes an explicit source root plus an allow-list of
  source-project paths, package IDs, exact versions, package roles, expected
  targets, intended output paths, and exact immutable input Version Map/Selection
  identity, version, digest, and normalized locator paths beneath the declared
  source root. It packs every
  baseline Program Kit package as exactly `0.1.0-alpha.1` and selected fixture
  libraries as exactly `0.1.0-fixture.1`; it never discovers projects from the
  current directory, a solution, a wildcard, or a package-folder listing. The
  resulting `local-package-root-manifest.json` records every selected source-
  project identity, package ID/version/role, dependency/content report, relative
  `.nupkg` path, size, SHA-256, and immutable input Version Map/Selection
  identity, version, and digest references.
- **Restore source policy:** publish generates an explicit NuGet configuration
  with package-source mapping: only the allow-listed first-party package IDs map
  to the manifest-bound local folder, and the enumerated exact reviewed external
  dependency IDs and locked transitive closure map only to
  `https://api.nuget.org/v3/index.json`. There is no catch-all mapping that could
  resolve a first-party ID remotely. Restore is locked; an unlisted ID, source,
  version, package hash, or dependency-closure change fails.
- **Publish flow:** `dotnet publish-local --shell <shell.json> --host <host-id>
  --artifact-manifest <file> --package-manifest <file> --output <dir>` resolves
  exactly one host entry and its matching `hostLocks[]`, verifies the shell's
  Version Map/Selection through the artifact manifest and every package-manifest hash, restores that
  generated host in locked mode through the emitted source mapping, and runs
  project-level `dotnet publish --no-restore`. Restore uses an initially empty
  `RestorePackagesPath` below the validated temporary workspace, clears fallback
  package folders, disables HTTP caching, and never reads the machine-global
  packages folder. It neither prepares packages,
  discovers an ambient solution/current directory, cleans the output root, nor
  resolves collisions by overwrite.
- **Layout:**
  `<output-root>/publish/<host-id>/<host-version>/<configuration>_<tfm>_<rid-or-portable>_<deployment-mode>/`.
- **Manifest:** record host/project, SDK, TFM, RID/portable, configuration,
  deployment mode, shell/generator/producing-input-Version-Map/lock/package
  digests, and every
  published application output file's normalized relative path, size, and
  SHA-256. The file table excludes the manifest itself; its standard canonical
  envelope digest is calculated with `integrity.digest` omitted. Paths must
  remain below the validated root; existing conflicting output fails closed.
  The manifest is written and canonicalized through the selected
  Serialization.JSON profiles.
- **Version-closure extension:** add exact package, isolated-consumer,
  publish-profile, publish-leaf, and local-publish-manifest revisions/typed edges
  to a later immutable Version Map revision, then rerun the v1-to-v2 assessment.
  Published outputs retain their producing input-map reference. Every newly
  reached output receives an owner, target, terminal disposition, ordered
  actions, and evidence; W060's
  earlier closure is not treated as final after publish outputs exist.
- **Exclusions:** no NuGet/server feed transport, push, publication, deployment,
  signing, promotion, or Release Cycle behavior.
- **Observation:** separate contract-only, DotNet, CLI tool, schema discovery,
  and fixture-composition consumers succeed from the hash-bound local package
  manifest. Exact API, Console, and Worker host selections each restore and
  publish from packages with complete reproducible manifests; source-mapping,
  ambient-discovery, conflicting bytes pre-seeded in a test-controlled temporary
  path configured to simulate the ambient global cache, missing/extra/tampered-
  package, host-selection, and collision negatives fail, and the
  extended migration closure is action-complete.

### `PK-W070` Author and package the development capabilities

- **Depends on:** working contracts, routing, CLI, generators, fixture, package,
  and publish operations through `PK-W065`.
- **Capability action:** invoke the repository-owned
  `author-and-maintain-skills` capability through its active-provider wrapper at
  this point and follow its canonical guidance. Do not improvise a capability
  path if that wrapper is absent.
- **Allowed edits:** `.agents/capabilities/{develop-software,design-software,implement-software-plan,publish-dotnet-application-locally}/`;
  `.codex/skills/{develop-software,design-software,implement-software-plan,publish-dotnet-application-locally}/`;
  `.agents/capabilities/INDEX.md`; its generated README projection;
  `program-kit/src/Orbyss.ProgramKit.CapabilityBundle/`, and capability
  conformance tests/fixtures plus package allow-lists.
- **Outputs:** backed `develop-software`, `design-software`, and
  `implement-software-plan` procedures; thin provider wrappers; truthful index;
  exact-byte allow-listed bundle. Once the publish operation and tests exist,
  add the separately repository-owned
  `publish-dotnet-application-locally` capability as an operation-specific
  wrapper over the backed `dotnet publish-local` operation. It requires explicit
  shell, host, artifact-manifest, package-manifest, and output parameters, does
  not prepare packages, and is not silently inserted into the initial
  three-capability bundle.
- **Forbidden:** copied architecture manuals, alternate speculative wrappers,
  hook/watcher/MCP/tool bindings, a release capability, feed transport, or
  runtime loading of `.agents` content.
- **Observation:** definitions, wrappers, index, catalog, and bundle digests
  agree; the catalog truthfully lists the backed local-publish capability while
  the bundle manifest contains only the three initial distributable definitions;
  copied bytes alone do not register a capability in a consumer.

### `PK-W080` Carry the bootstrap design through the Kit

- **Depends on:** `PK-W070`, so normal receipts bind real registered capability
  bytes.
- **Allowed edits:** `program-kit/artifacts/` and bootstrap comparison
  tests/documentation.
- **Outputs:** canonical self-hosted design and separate plan instances;
  deterministic Markdown; dependency/forbidden/Version Map graphs; an approval
  relationship report rather than a newly minted approval; normal receipts for
  actual post-registration events; and a structured bootstrap comparison.
- **History rule:** no receipt is backdated and no capability claims authorship
  of pre-existing bootstrap source. Representation/design differences remain
  findings with explicit dispositions.
- **Observation:** all self-hosted instances validate; every receipt carries the
  actual registered capability digest; bootstrap files remain intact.

### `PK-W090` Run the full closure and publish the review report

- **Depends on:** every preceding work unit.
- **Allowed edits:** Program Kit documentation/evidence, root and Program Kit
  README links, generated status projections, canonical final maps/assessments
  under `program-kit/artifacts/`, and fixture version/evidence artifacts below
  `program-kit/fixtures/observatory-scheduling/`. Existing engine-domain source
  and previously generated locks/hosts/publishes are not rewritten and are not
  implementation targets.
- **Outputs:** final architecture, package, task, version, and forbidden-edge
  graphs; fixture artifacts; self-host comparison; approval/receipts; verification
  observations; local package/publish evidence; exact blockers; clean-room
  provenance attestation; status matrix; a recomputed full-baseline Version Map
  and migration assessment including serialization profiles/contributions,
  generated outputs, packages, publishes, and capabilities; and the smallest
  safe next step.
- **Observation:** every mandatory in-scope criterion has committed evidence;
  removing any selected revision, typed edge, reached owner/target/terminal
  disposition/required action, causal path, or evidence reference invalidates
  the final map/assessment;
  no `.NET 8`, engine semantic, durable/distributed task claim, feed/deployment,
  or Release Cycle behavior appears.

## 6. Safe parallel work summary

```text
W000 -> W010 -> +-> W015 -> +-> W020 --+
                |          |            +-> W040 -> W050 -> W060 -> W065
                |          +-> W030 ----+                            |
                |              ^                                     v
                +-> W025 -------+        W090 <- W080 <- W070 <-------+
```

`W015` and `W025` may proceed in parallel only after W010 fixes identity,
envelope, target-framework, and package conventions. W020 follows W015 only for
Serialization.JSON and remains generic; it consumes Modularity/task/metadata
modules only through the Artifacts extension contract at composition. W030
follows W015 and W025 without waiting for W020. W040 is the explicit join after
both W020 and W030, owns shell locks/OpenAPI schema provenance, and adds the
.NET/task registrations to the generic Workbench. CLI parser/diagnostic transport
tests may start beside W040; host commands cannot complete before generator APIs
stabilize, and local package preparation/publish completes in W065. Within W060,
the three generated host projects may build/test in parallel after one final
multi-host shell/lock is fixed. Within W065, isolated consumers and deterministic
publish profiles may execute in separate validated roots after one package
manifest is fixed.

Each worker owns disjoint paths. Solution, central package, schema catalog,
shell-lock, capability index, and evidence-manifest integration edits are
serialized. No parallel unit may change approved architecture, manufacture an
approval, loosen exact package selection, or add a target framework.

## 7. Versioning, compatibility, and migration rules

1. Every contract, schema, package, generator/profile, configuration schema,
   JSON serialization profile/contribution, integrator document schema, host,
   feature, handler binding, task definition, schedule, capability definition,
   and persisted/generated artifact has its own
   full SemVer and digest. Versions are not inferred from an assembly or parent
   package and schema versions are never integer shorthand. Initial selections
   are exact: baseline Program Kit packages `0.1.0-alpha.1`, fixture library
   packages `0.1.0-fixture.1`, Open Console schema
   `pkid:schema:program-kit:open-console@1.0.0`, and Open Worker schema
   `pkid:schema:program-kit:open-worker@1.0.0`, plus fixed DotNet shell profile
   `pkid:profile:program-kit:json-dotnet-shell@1.0.0`.
2. Every selected/persisted/generated/consumed revision has a
   `VersionedComponentManifest`. A reference is exactly identity, version, and
   digest; equal identity/version with unequal bytes is an integrity failure.
3. The Version Map is the migration authority for dependency topology. Public
   surfaces terminate in explicit external-consumer nodes, because unknown
   consumers cannot truthfully be enumerated.
4. Compatibility is classified independently for semantic behavior, wire read,
   wire write, source API, binary ABI, configuration, persisted artifact/data,
   generated input/output, CLI surface, and host composition/activation. The
   only classifications are `editorial`, `compatible-additive`,
   `conditionally-compatible`, `breaking`, and `unknown`; unknown fails closed
   for human judgment.
5. A change assessment starts from every changed revision and computes the
   fixed-point reverse closure over typed edges. A dependent is re-enqueued when
   its own contract, package, generation, lock, or host selection changes.
   Cycles form atomic cohorts ordered into dependency-safe waves, and every
   causal path remains evidence.
6. Every impacted node has an owner, target version, exactly one terminal
   disposition from the approved set in W020, ordered required actions, and
   evidence. An assessment missing any field/action or violating the
   unaffected/compatible action rules is incomplete and blocks implementation.
7. `MigrationDefinition` binds its own identity/version, source range, exact
   target, mode (`artifact-transform`, `configuration-transform`,
   `source-guidance`, `regenerate`, `package-upgrade`, or `runtime-adapter`),
   preconditions, loss policy, determinism, idempotence, failure policy,
   implementation reference, and fixtures. Migration emits a new value with
   source/migrator provenance; it never mutates old bytes or reads them as new.
8. A migration chain is valid only when exactly one approved path exists.
   Persistent/external contracts default to expand readers, migrate, switch
   writers, prove the old selection absent, then contract. Dual writing is not
   assumed. Runtime adapters are named temporary coexistence mechanisms, not
   artifact migrators.
9. Generated output normally migrates by regeneration from an explicitly
   migrated input and selected generator/profile. `check` detects source,
   generator, profile, Version Map, shared lock, matching host lock, or output
   digest drift; generated projections are never hand-edited as canonical truth.
10. A schema/contract change therefore reaches every reader, writer, validator,
    serialization profile/converter contribution, public exposure, package,
    generator, generated host/document, fixture, selection, lock, and migration
    test through typed edges. A claim that an
    reached dependent is unchanged requires `unaffected-with-proof`, not omission
    from the assessment. A selected node outside the causal closure is not
    artificially marked reached; any reported unaffected claim for it carries
    explicit out-of-closure proof.
11. A JSON option, converter behavior/order, generated type-metadata, or profile
    selection change creates a new contribution/profile revision. It reaches
    every `reads`, `writes`, `serializes-with`, canonical artifact, generated
    document, host lock, package, and local publish output; canonicalization
    itself changes only through a separately approved canonical-profile revision.
12. Pending task instances and recurring schedules pin exact definition,
    request/response schema, and activation-binding revisions. Before changing a
    handler cohort, each pending item must drain under the old handler, coexist
    under both exact versions, migrate explicitly, cancel/recreate with
    provenance, or block. Silent execution against the newly selected handler is
    forbidden.
13. Incompatible revisions of one .NET assembly identity are not presumed to
    coexist in one process. The cohort upgrades atomically or introduces an
    explicitly named and versioned compatibility package.
14. Pre-1.0 NuGet dependencies, including `[0.1.0-alpha.1]` first-party Program
    Kit packages, `[0.1.0-fixture.1]` fixture libraries, `[0.0.28]` CShells
    packages, and `[0.13.0]` Cronos, use exact range syntax. A bare version is
    forbidden because it means a minimum. After 1.0, a bounded range requires
    recorded compatibility evidence.
15. Pack-time comparison against the reviewed previous package baseline checks
    public API, binary ABI, TFM, and assets. Behavior tests cover semantic and
    lifecycle compatibility that API comparison cannot detect.
16. W065 extends and reruns the closure after package/publish nodes exist; W090
    regenerates it after capability nodes exist. An earlier partial map is never
    accepted as the complete baseline closure. These are later immutable map
    revisions; no output is rewritten to hash a map that contains that output.
17. Design and plan lifecycles remain independent. A design-byte change makes
    the plan binding stale; it requires a recomputed plan/manifest and new human
    approval. No migration grants implementation authority.

## 8. Verification commands and expected observations

The final repository may wrap these calls for repeatability, but each operation
remains directly scriptable with explicit roots:

```powershell
dotnet --version
dotnet restore program-kit/ProgramKit.sln --configfile program-kit/NuGet.Config --locked-mode
dotnet build program-kit/ProgramKit.sln -c Release --no-restore
dotnet test program-kit/ProgramKit.sln -c Release --no-build --no-restore
dotnet msbuild program-kit/build/ProgramKit.Pack.proj -t:Pack -p:Configuration=Release -p:NoBuild=true

dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- validate --manifest program-kit/artifacts/artifact-manifest.json
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- graph program-kit/artifacts/designs/program-kit-baseline.json --format text
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- versions map --manifest program-kit/fixtures/observatory-scheduling/versioned-component-manifest.json
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- versions assess --observed program-kit/fixtures/observatory-scheduling/selection-v1.json --target program-kit/fixtures/observatory-scheduling/selection-v2.json

dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet generate-host api --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:api --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --output program-kit/.artifacts/generated/api
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet generate-host console --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:console --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --output program-kit/.artifacts/generated/console
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet generate-host worker --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:worker --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --output program-kit/.artifacts/generated/worker

dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- packages prepare-local --workspace-manifest program-kit/fixtures/observatory-scheduling/workspace-package-manifest.json --output program-kit/.artifacts/packages
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet publish-local --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:api --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --package-manifest program-kit/.artifacts/packages/local-package-root-manifest.json --output program-kit/.artifacts/local-publish
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet publish-local --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:console --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --package-manifest program-kit/.artifacts/packages/local-package-root-manifest.json --output program-kit/.artifacts/local-publish
dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- dotnet publish-local --shell program-kit/fixtures/observatory-scheduling/shell.json --host pkid:host:observatory-scheduling:worker --artifact-manifest program-kit/fixtures/observatory-scheduling/artifact-manifest.json --package-manifest program-kit/.artifacts/packages/local-package-root-manifest.json --output program-kit/.artifacts/local-publish

dotnet run --project program-kit/src/Orbyss.ProgramKit.CommandLine -c Release --no-build --no-restore -- check --manifest program-kit/artifacts/workspace-manifest.json --profile pkid:test:program-kit:full-development
```

The conformance closure also:

- scans all owned/generated project files for `net8.0`, multitargeting, SDK
  roll-forward, prerelease SDK use, non-C#-14 language selection, target-profile
  drift, and undeclared dependency sources; expected result is exact profile
  `pkid:profile:program-kit:dotnet-10@1.0.0` and its digest, SDK `10.0.302`, only
  `net10.0`, C# 14, and zero undeclared selections;
- repeats normalize/render/Version Map/migration/generate operations under
  varied culture and timezone settings and byte-compares every declared output;
- verifies typed System.Text.Json round trips, frozen profile/contribution
  ordering/conflicts/versioning, source-generated metadata composition, strict
  RFC 8785-compatible canonical vectors, resource limits, and opaque canonical
  values; scans reject Newtonsoft, direct serializer calls outside
  Serialization.JSON, and every DOM occurrence outside the exact file/API
  allow-list whose sole baseline entry is Workbench's bounded internal
  JsonSchema.Net adapter; reader/writer/bounded-buffer paths contain no DOM;
- verifies exact CShells abstraction/runtime resolution and the direct feature
  ABI against tag `0.0.28`, commit/license, immutable NuGet catalog, nupkg, and
  selected `net10.0` assembly hashes while proving universal, Domain.Core,
  Modularity, Serialization.JSON, and task-contract packages remain CShells-free;
- verifies the Cronos provider's complete locked grammar (including only the
  documented alias/macro/special forms), five/six-field formats, DOM/DOW AND,
  year-field rejection, next/previous boundaries, IANA/Windows zones, DST
  outcomes, independent golden timelines, deterministic fingerprints binding
  zone ID plus time-zone-data source/version plus bounded horizon, startup
  mismatch rejection, selected asset/digest, and absence of Cronos/provider
  semantics or execution infrastructure in Tasks.Schedules; its evidence also
  matches the exact annotated tag object, peeled commit, license, NuGet catalog,
  nupkg, and selected `net6.0` assembly hashes;
- exercises bounded queue overflow, status transitions, both cancellation
  boundaries, retry per attempt, scoped idempotency, normal TaskRequest handling
  for occurrences, generated activation-scope resolution, fresh DI attempt
  scopes, optional lifecycle publisher absence/selection, coordinated registry
  freeze, shutdown drain/cancel, misfire/overlap, and deterministic health checks;
- proves no health route/listener exists by registration alone and validates
  every configured listener's tag selection, status mapping, cache/response,
  exposure/security/documentation decision, explicit nonzero port, and actual
  port equality;
- validates OpenAPI against the vendored official 3.2 schema, validates
  `pkid:schema:program-kit:open-console@1.0.0` and
  `pkid:schema:program-kit:open-worker@1.0.0`, and proves the DotNet parser's
  token arrays, `--`, long/short forms, `--name=value`, arity/occurrence/default/
  conflict/prerequisite rules, invariant conversion, stable errors/exit codes,
  help, and completion all share the same descriptors with no shell-string or
  external-parser path; published Console dependency graphs contain no
  Workbench, DotNet.Metadata, DotNet, or CommandLine assembly;
- prepares packages only from the explicit workspace-manifest allow-list,
  verifies exact `0.1.0-alpha.1`/`0.1.0-fixture.1` identities and every package
  hash/content/dependency report, rejects ambient solution/current-directory/
  folder discovery, and proves source mapping sends first-party IDs only to the
  local folder and exact reviewed external IDs only to NuGet.org; restore uses a
  fresh operation-local packages path with fallback folders and HTTP caching
  disabled, and ignores conflicting bytes pre-seeded in a test-controlled
  temporary path configured as the simulated ambient global cache without
  writing the user's real cache;
- restores and builds clean locked consumers without repository project
  references, then selects and publishes exact API, Console, and Worker hosts
  from matching `hostLocks[]` below the required output layout; path escape,
  collision/overwrite, host mismatch, missing/extra/tampered package, and source
  drift fail, while every application-output hash and each manifest's separate
  canonical envelope digest verify;
- executes the v1-to-v2 closure and proves every reached version node has one
  terminal disposition, ordered actions, owner, target, evidence, and a safe
  pending-task/schedule policy;
  extends it after package/publish outputs, regenerates it after capabilities,
  and proves the final closure contains every selected baseline revision;
- compares solution/project/package/namespace edges with allowed and forbidden
  graphs, checks capability definition/wrapper/index/catalog/bundle digest
  equivalence—including the backed local-publish capability's deliberate bundle
  exclusion—and scans for forbidden Release Cycle behavior.

Expected observations are zero compiler/analyzer warnings, all selected tests
passing, stable diagnostics and golden outputs, exact hash-bound local package
identities, successful isolated consumption, complete API/Console/Worker
local-publish manifests, and zero forbidden engine/release references. An
unavailable external package or source
produces exact scoped blocker evidence; it never permits an invented API,
unverified adapter, loosened version, or waived unrelated test.

## 9. Stop conditions

Stop before further implementation and request human direction when:

- this plan still contains the design-digest placeholder, the review manifest
  is stale, or approval is absent, ambiguous, conditional, rejected,
  superseded, or does not match the exact design/plan bytes;
- a required result needs a new project/package boundary, changes an owner,
  reverses an accepted dependency arrow, adds a target other than `net10.0`, or
  changes canonicalization, identity, authority, status, or migration semantics;
- the direct CShells `0.0.28` ABI cannot be implemented from verified public
  packages/source, or work would require guessing or wrapping a different API;
- the optional Cronos provider fails any selected-grammar, next/previous,
  IANA/Windows timezone, DST gap/ambiguity, golden-timeline, package/source/hash,
  tag/commit/license/catalog, selected-asset, or zone-ID/time-zone-data-source/
  version/horizon fingerprint or startup-recomputation check; stop and review the
  provider instead of moving its types or semantics into Tasks.Core or
  Tasks.Schedules;
- a domain core would need `Orbyss.ProgramKit.Tasks`, a task implementation, or
  CShells rather than Tasks.Core (with optional Modularity and Serialization.JSON
  only for independently owned contributions);
- JSON work would require Newtonsoft.Json, ambient/global mutable options,
  converter-defined canonicalization, an unversioned profile/contribution,
  direct serializer use outside Serialization.JSON, or any DOM use outside the
  exact reviewed file/API allow-list (whose sole baseline entry is the internal
  Workbench JsonSchema.Net adapter);
- requested task behavior needs durability, restart recovery, distributed
  execution, exactly-once delivery, broker/lease infrastructure, or another
  guarantee deliberately outside this baseline;
- a schema/contract/handler/schedule change has unknown compatibility, incomplete
  reverse closure, no owner/target/terminal disposition/ordered actions/evidence,
  or no safe pending-work policy;
- a generated host would expose health implicitly or without complete listener,
  exact nonzero port/tag selection/status mapping, authentication/authorization,
  TLS, redaction, and documentation policy;
- host generation/publish cannot resolve exactly one requested `hosts[]` entry
  and matching `hostLocks[]`, or its host kind, closure, or digest differs;
- local package preparation would require current-directory/solution/folder
  discovery, an unlisted project/package/version/path, a package hash mismatch,
  or source mapping that permits a first-party ID from NuGet.org or a reviewed
  external dependency from the local folder;
- a fixture would escape its root or leak its vocabulary into universal code;
- a test needs ambient discovery, secrets, undeclared network access, destructive
  cleanup, unapproved writes, or trust in unhashed machine-local output;
- package feed transport, signing, deployment, release freeze/candidate/
  qualification/promotion/publication behavior, or engine-domain implementation
  appears necessary;
- a required active-provider capability wrapper is missing, or a capability
  cannot remain thin over working Program Kit operations.

Ordinary compile, validation, conformance, or package-restore failures are not
architectural deviations by themselves. Diagnose and fix them within approved
boundaries, or record the exact external blocker without waiving other work.

## 10. Completion report

Completion requires one human-readable report with:

1. Program Kit ownership, public-contract/package, task, Version Map, and
   forbidden-reference graphs;
2. exact `.NET 10` SDK/TFM/package/lock observations and an explicit statement
   that no owned/generated project targets `.NET 8` or multitargets;
3. unchanged bootstrap artifacts beside self-hosted design/plan projections and
   genuine comparison findings;
4. the Observatory fixture design, separate plan, shell/lock, API/Console/Worker
   sources, and all three integrator documents;
5. contribution/middleware/metadata, Serialization.JSON model-first/profile/
   converter/canonicalization mechanics, and Tasks.Core/Tasks/runtime/schedule
   ownership demonstrated by package graphs and behavioral evidence;
6. the real v1-to-v2 Version Map, complete final causal closure through
   packages/publishes/capabilities, migration waves, terminal dispositions,
   ordered required actions, and pending task/schedule outcome;
7. unit, conformance, architecture, determinism, host-health, package,
   isolated-consumer, and local-publish commands with observed results;
8. exact CShells selection and the optional Cronos provider's gate result,
   immutable tags/commits/licenses/catalogs/package and resolved-asset digests,
   public-source/alternative-evaluation evidence, golden timelines, and the
   claims those selections do and do not support;
9. no engine dependency, no fixture leakage, no durable/distributed task claim,
   no implicit health exposure, no feed/deployment, and no Release Cycle behavior;
10. every durable artifact's owner, independent version, inputs/provenance,
    exact serialization/canonical representation, digest, consumers,
    compatibility/migration rule, and truthful status;
11. separate `implemented`, `scaffolded`, `deferred`, and `aspirational`
    implementation-status lists—never using one status to imply another—plus a
    separately named blocker section that is not an implementation status;
12. exact bootstrap approval and digest-bound normal receipts, with no backdated
    capability claim;
13. the three implemented development flows, the separately backed local-publish
    capability, and unavailable Release Cycle flows in the generated catalog,
    with the capability index as availability authority;
14. clean-room provenance listing every consulted input and any unavailable
    evidence; and
15. the smallest safe next step without taking it or silently creating engine
    runtime architecture.

## 11. Human decision requested

This restored `0.2.0` plan incorporates the accepted direction: `.NET 10` only;
domainless modularity, model-first System.Text.Json serialization, metadata, and
task facilities; Tasks.Core as the only task
dependency required by domain cores; direct transitive CShells abstractions for
feature libraries; full API/Console/Worker generation and integrator documents;
explicit health exposure; local package/publish testing; and fixed-point
version/migration closure.

The frontmatter design digest and `review-manifest.json` bindings must match the
final exact bytes. Approve, reject, or request changes to the two exact artifacts
together. No source implementation is authorized by this review set or by
agreement with its direction alone.

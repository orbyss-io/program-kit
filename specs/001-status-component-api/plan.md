# Implementation Plan: Status Component and API Vertical Slice

**Branch**: `codex/initialize-spec-kit` | **Date**: 2026-08-01 |
**Spec**: [spec.md](spec.md)

**Spec Kit Feature**: `001-status-component-api`

**Input**: Feature specification from
`/specs/001-status-component-api/spec.md`

## Summary

Build the first independently callable Program Kit software-factory slice. A
thin CLI invokes a trusted kernel through versioned public contracts; exact
first-party .NET providers map restricted authoring input, construct a
consumer-owned Status component package and separate API, and evaluate the
complete result. Before live writes, the kernel emits a deterministic
Integration Resolution Explanation. Construction uses an exact resolution
lock, sealed candidate sets, whole-file ownership, recoverable publication, and
admission only after complete live verification. Every recoverable command path
returns a structured AI-usable result and the admitted workspace receives one
traceable canonical snapshot.

The implementation is greenfield and permanently bootstraps through the
standard .NET/Spec Kit path. It contains no native planning, Program Kit runtime,
automatic migration, provider marketplace, or application-domain Status
semantics.

## Technical Context

**Language/Version**: C# 14.0, exact .NET SDK `10.0.302`, target framework
`net10.0`, stable language only

**Primary Dependencies**:

- .NET 10 BCL/shared framework: `System.Text.Json`, cryptography, filesystem,
  PE metadata, ASP.NET Core;
- `JsonSchema.Net [9.4.0]` behind the structural-schema adapter;
- `YamlDotNet [18.1.0]` behind the restricted-YAML adapter;
- generated component: `CShells.AspNetCore.Abstractions [0.0.28]`;
- generated API: `CShells.AspNetCore [0.0.28]`;
- tests: `MSTest.TestFramework [4.3.3]`,
  `MSTest.TestAdapter [4.3.3]`, and
  `Microsoft.NET.Test.Sdk [18.8.1]`;
- no `System.CommandLine`, source generator, custom MSBuild task, weaving,
  reflection-based Program Kit provider discovery, or hidden generation

**Storage**: Repository/local-workspace files only: restricted YAML authoring,
canonical JSON contracts/locks/results/receipts/snapshots, isolated candidate
directories, durable publication journals, two explicit local NuGet sources,
and clean local package caches. No database, remote service, telemetry, or
secret store.

**Testing**: MSTest on Microsoft.TestingPlatform through normal `dotnet test`;
unit, schema/public-contract/provider-conformance, real-filesystem fault
injection, end-to-end local package consumption, path/culture/order
repeatability, dependency/PE allowlisting, relocated-runtime, and black-box API
tests on Windows and Linux

**Target Platform**: .NET 10 developer workstations on Windows x64 and Linux
x64. Program Kit-owned canonical bytes are platform-neutral only where fixtures
prove equality. External compiler/NuGet outputs retain an exact platform/tool
profile and the strongest proven verifier class.

**Project Type**: Command-line development tool with public contract library,
trusted kernel library, exact first-party provider distribution, and generated
ordinary .NET component/API consumer products

**Performance Goals**: Reference `explain` completes in under 2 seconds after
process start when exact local inputs are available; internal validation and
resolution remain bounded by the finite two-bundle closure; the complete
documented valid/invalid/repeatability/drift/repair walkthrough is achievable by
a fresh contributor within 60 minutes. External build/pack time is reported as
evidence, not included in canonical semantics.

**Constraints**:

- exact SDK/package/source/lock selection and locked restore;
- UTF-8/LF Program Kit text; canonical JSON profile
  `program-kit.canonical-json/v1`;
- local-first and offline after the governed dependency mirror is available;
- no secrets in governed records, diagnostics, fixtures, logs, or outputs;
- no ambient current-directory selection, provider discovery, source order,
  locale, time, random, machine, or global-cache semantics;
- whole-file ownership only; no mixed generated/editable files;
- atomic trust through complete admission, not an atomic multi-file filesystem
  claim;
- generated products have no Program Kit, Spec Kit, or AI runtime dependency;
- Program Kit never runs against its own repository as bootstrap or authority

**Scale/Scope**: One exact root closure containing two bundles
(`Reference.Status`, `Reference.Status.Api`), one Status contract/custom
implementation, one package relationship, one HTTP endpoint contribution, one
owning host assembler, exact first-party providers, and bounded diagnostic
fixtures. The protocol is designed for extension but no generalized semantic
engine, migration graph, marketplace, or multi-ecosystem implementation enters
this slice.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

No constitutional exception or waiver is planned. Every non-waivable kernel
gate below remains blocking.

| Principle / boundary | Enforcement mode and owner | Planned evidence | Failure disposition / waiver | Pre-research | Post-design |
|---|---|---|---|---|---|
| I. Human Authority and Semantic Honesty | Human review owns Status intent/fitness; kernel executable invariants own grant, trace, unknown-state, and admission | Accepted spec/design, local grant fixtures, semantic trace tests, no-Status-in-production scan, human review record | Stop for input/approval/revision; kernel checks not waivable | PASS | PASS |
| II. Independent Public Software Factory | Evidence-backed; CLI/kernel maintainers | Public CLI contract/golden tests, clean standard build, forbidden Program Kit self-use/dependency tests, package-only consumer proof | Block release; not waivable | PASS | PASS |
| III. Exact Contracts and Governed Resolution | Kernel executable invariants; contract/vocabulary owners | Draft 2020-12 schemas, typed validators, canonical fixtures, exact resolution lock, direct/incompatible fixtures, Integration Resolution Explanation | No trusted result; not waivable | PASS | PASS |
| IV. Honest Determinism and Evidence | Kernel owns construction identity; providers own named profile evidence | Canonical JSON golden vectors, path/culture/order repeatability, exact manifests/digests, external-output verifier, fresh evidence | Downgrade honest claim or block; never mislabel; not waivable | PASS | PASS |
| V. Artifact Ownership and Atomic Trust | Kernel executable invariants | Whole-file ownership manifest, sealed candidate tests, live preconditions, fault-injected journal/publication/recovery tests, receipt-last admission | Block/untrusted/repair; not waivable | PASS | PASS |
| VI. Explicit Extensions and Composition | Kernel owns exact role/selection/admission; providers own manifests/conformance | Explicit fixed provider registry, distinct provider manifests, immutable endpoint contributions, collision/order/missing-assembler fixtures | Provider unavailable or construction blocked; not waivable | PASS | PASS |
| VII. AI-Usable Diagnostics | Diagnostics subsystem and provider catalogs | Result/schema golden tests, stable catalog IDs, deterministic ordering/grouping, continuation/remediation, redaction and independent fallback tests | Public contract failure blocks release; disclosure not waivable | PASS | PASS |
| VIII. Consumer Ownership, Runtime Isolation, Local Safety | Distribution/security maintainers plus kernel effect/disclosure checks | Locked sources/dependencies, offline tests, secret scan, provenance/SBOM tasks, relocated allowlisted runtime, PE reference inspection | Block admission/release; not waivable | PASS | PASS |
| IX. Evidence-First Vertical Delivery | Maintainers plus human product review | Small two-bundle slice, negative/adversarial fixtures, public-contract-only flow, one-hour fresh-contributor walkthrough | Return to spec/plan or block completion; no kernel override | PASS | PASS |
| V1 `.NET 10 + CShells 0.0.28` profile | Evidence-backed provider conformance | Exact SDK/packages/source commit, explicit `FromAssemblies`, compile/run fixture | Stop provider support claim | PASS | PASS |
| Three provider roles only | Kernel protocol invariant | Intake-mapping, construction, evaluation manifests; resolution/admission remain kernel operations | Protocol revision required for a new role | PASS | PASS |
| Typed model + restricted YAML + JSON automation/canonical bytes | Executable invariant and contract evidence | Low-level restricted YAML parser, shared JSON Schema path, typed binding, canonical encoder fixtures | Refuse invalid input | PASS | PASS |
| First-party providers only | Kernel trust-admission invariant | Distribution allowlist and exact manifests; no scanning/dynamic loading | Refuse execution; not waivable | PASS | PASS |
| Deferred product boundaries | Human-review plus forbidden-reference/scope checks | No planning/runtime/migration/marketplace/multi-ecosystem/reconstruction projects or contracts | Stop and amend before scope expansion | PASS | PASS |
| Enforcement/waiver contract | Kernel invariant and human review | Closed gate status, applicability checks, no waivers in first slice, tests rejecting force/global/non-finite waivers | Mandatory failed/unknown/not-evaluated gate blocks | PASS | PASS |
| Spec Kit development workflow | Repository process evidence | This spec/plan/research/model/contracts/quickstart; later tasks/analyze; standard `dotnet` bootstrap | Return to prior phase on ambiguity or boundary drift | PASS | PASS |

### Post-design gate notes

- Research resolves every planning unknown.
- Schemas close public structural contracts but do not move semantic authority
  into JSON Schema.
- The pre-construction explanation does not guess package bytes: it identifies
  exact package ID/version and producer construction identity; the API sub-lock
  binds the produced digest before API generation.
- `.nupkg` begins as `verified-equivalent` external-tool output unless the exact
  pack fixture proves byte identity. Program Kit-owned canonical bytes remain
  byte-reproducible.
- Publication promises recoverability and receipt-gated atomic trust, not a
  physically atomic multi-file or power-loss-safe transaction.
- Explicit CShells `FromAssemblies` is isolated inside the selected 0.0.28
  provider and covered by a conformance fixture; Program Kit itself performs no
  reflection-based provider discovery.

## Project Structure

### Documentation (this feature)

```text
specs/001-status-component-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── authority-grant.schema.json
│   ├── cli.md
│   ├── common.schema.json
│   ├── construction-receipt.schema.json
│   ├── diagnostics.md
│   ├── factory-request.schema.json
│   ├── operation-result.schema.json
│   ├── resolution.schema.json
│   ├── software-definition-bundle.schema.json
│   └── workspace-snapshot.schema.json
└── tasks.md                         # created only by $speckit-tasks
```

### Source Code (repository root)

```text
ProgramKit.slnx
global.json
Directory.Build.props
Directory.Packages.props
NuGet.Config

src/
├── ProgramKit.Contracts/
│   ├── ProgramKit.Contracts.csproj
│   ├── Canonical/
│   ├── Diagnostics/
│   ├── Identity/
│   ├── Operations/
│   ├── Providers/
│   ├── Resolution/
│   ├── Schemas/
│   └── Workspace/
├── ProgramKit.Kernel/
│   ├── ProgramKit.Kernel.csproj
│   ├── Artifacts/
│   ├── Authority/
│   ├── Canonicalization/
│   ├── Diagnostics/
│   ├── Evaluation/
│   ├── Evidence/
│   ├── Intake/
│   ├── Operations/
│   ├── Publication/
│   ├── Resolution/
│   └── Validation/
├── ProgramKit.Providers.DotNet/
│   ├── ProgramKit.Providers.DotNet.csproj
│   ├── Composition/
│   │   └── HttpEndpoints/
│   ├── Construction/
│   │   ├── AspNetCore/
│   │   ├── CShells028/
│   │   ├── MsBuild/
│   │   └── NuGet/
│   ├── Evaluation/
│   ├── Intake/
│   ├── Manifests/
│   └── Templates/
└── ProgramKit.Cli/
    ├── ProgramKit.Cli.csproj
    ├── Commands/
    ├── Composition/
    ├── Parsing/
    ├── Rendering/
    └── Program.cs

tests/
├── ProgramKit.UnitTests/
│   ├── ProgramKit.UnitTests.csproj
│   ├── Contracts/
│   ├── Kernel/
│   └── Providers/
├── ProgramKit.ContractTests/
│   ├── ProgramKit.ContractTests.csproj
│   ├── Canonical/
│   ├── Cli/
│   ├── Diagnostics/
│   ├── Providers/
│   └── Schemas/
├── ProgramKit.AcceptanceTests/
│   ├── ProgramKit.AcceptanceTests.csproj
│   ├── Publication/
│   ├── Repeatability/
│   ├── RuntimeIsolation/
│   └── VerticalSlice/
└── Fixtures/
    └── Reference.Status/
        ├── Valid/
        │   ├── authority/
        │   ├── definitions/
        │   ├── implementation/
        │   └── requests/
        ├── Invalid/
        │   ├── AmbiguousSelection/
        │   ├── ConflictingIdentity/
        │   ├── DuplicateRoute/
        │   ├── IncompatibleContract/
        │   ├── MissingAssembler/
        │   ├── MissingSelection/
        │   └── UnsafeDisclosure/
        └── Golden/
            ├── canonical/
            ├── diagnostics/
            ├── explanation/
            └── snapshot/
```

**Structure Decision**: Four production projects express four necessary
boundaries: stable public contract/SPI, trusted kernel, target-specific
first-party provider distribution, and public application. Two logical .NET
providers remain distinct by exact manifest inside one distribution until
independent packaging is needed. Three test projects separate fast invariants,
public/provider contract conformance, and real end-to-end/filesystem/runtime
evidence. Consumer Status meaning exists only in fixtures and generated
consumer workspaces.

Dependency direction is fixed:

```text
ProgramKit.Cli -> ProgramKit.Kernel + ProgramKit.Contracts
ProgramKit.Cli -> ProgramKit.Providers.DotNet (composition root only)
ProgramKit.Kernel -> ProgramKit.Contracts
ProgramKit.Providers.DotNet -> ProgramKit.Contracts

ProgramKit.Kernel -X-> ProgramKit.Providers.DotNet
ProgramKit.Contracts -X-> ProgramKit.Kernel/provider/CLI
generated consumer -X-> any ProgramKit/SpecKit/AI assembly
```

Architecture tests enforce the forbidden edges. Provider execution is passed
through contract interfaces and an explicit immutable registry created by the
CLI composition root.

## Design Sequence

### 1. Bootstrap and public contracts

Create exact SDK/package/source policy, four empty production boundaries, three
test boundaries, typed immutable contract records, JSON Schemas, canonical
profile vectors, diagnostic catalog, CLI parser/result/fallback, and
forbidden-reference tests. This leaves a working CLI that returns honest
structured refusal before providers exist.

### 2. Kernel explain path

Implement restricted YAML/strict JSON intake, structural/typed/semantic
validation, local authority records, exact provider/profile registry,
deterministic resolution lock, and Integration Resolution Explanation. Prove
valid, missing, ambiguous, conflicting, incompatible, and unavailable paths
with zero live consumer writes.

### 3. Sealed .NET candidate

Implement version-specific CShells 0.0.28 component generation, consumer-owned
custom-source preservation, exact endpoint contributions, one ASP.NET
assembler, component build/pack, exact local feed binding, API generation, and
candidate sealing. Provider code creates immutable contributions; only the
assembler owns final host artifacts.

### 4. Evaluation, publication, and admission

Implement ownership/precondition validation, mandatory gates, real external
tool evidence, same-volume publication groups, durable journal/fault injection,
post-publication verification, receipt-last admission, read-only evaluation,
explicit complete/rollback repair, and stale snapshot behavior.

### 5. Product proof

Complete path/culture/order repeatability, external-package verifier,
dependency/runtime allowlisting, relocated locked restore/build/test/publish,
black-box Status observation, offline operation, no-self-host bootstrap, safe
diagnostic/fallback disclosure, and the timed fresh-contributor walkthrough.

Each sequence stage must leave a usable public contract or independently
testable behavior. Task generation must not parallelize work across an
unestablished contract/ownership dependency.

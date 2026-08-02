# Implementation Plan: Independent CLI Distribution and AI-Session Integration Proof

**Branch**: `codex/002-session-integration-proof` | **Date**: 2026-08-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-session-integration-proof/spec.md`

## Summary

Prove Program Kit as an independently packaged and callable .NET tool, then add
a provider-neutral development-session integration that projects the exact
public factory contract into one real Codex workspace skill. The vertical slice
adds explicit `session explain|install|verify|remove` application operations,
request-bound human effect grants, a namespaced atomic publisher, versioned
canonical integration and provider manifests, exact installation records, and
structured diagnostics. Deterministic neutral tests prove the abstraction and
an explicitly authorized human-reviewed live Codex exercise assesses the real session
experience. The design introduces no MCP server, plugin marketplace, native
planning system, Program Kit self-hosting, or generated-application runtime
dependency.

## Technical Context

**Language/Version**: C# 14 on .NET 10, pinned by SDK `10.0.302`; PowerShell 7 for packaging and end-to-end validation scripts

**Primary Dependencies**: Existing `System.Text.Json`, JsonSchema.Net `9.4.0`, YamlDotNet `18.1.0`, the .NET SDK/NuGet tool packaging model, and MSTest; no new third-party runtime dependency is planned

**Storage**: Canonical JSON contracts and records plus Markdown/YAML provider projections in the consumer filesystem; no database or remote state

**Testing**: MSTest `4.3.3`, Microsoft.NET.Test.Sdk `18.8.1`, JSON Schema validation, golden contract/result fixtures, package-and-install smoke tests, a provider-neutral conformance harness, Windows/Linux CI, and an explicitly authorized exact-version live Codex review required for product acceptance

**Target Platform**: Windows and Linux development workspaces with .NET 10; Codex is the first real session provider

**Project Type**: Multi-project .NET library and CLI repository

**Performance Goals**: A first-time developer completes exact CLI installation, session projection, verification, and first governed invocation within 10 minutes; read-only explain/verify work remains bounded by the small local artifact set

**Constraints**: Workspace-local effects only; explicit provider and exact identities; local-first with no telemetry or implicit network; clean JSON stdout; no global configuration, MCP binding, plugin marketplace, Program Kit self-execution, Spec Kit runtime dependency, or generated runtime coupling

**Scale/Scope**: One exact CLI package, two focused production projects, four session lifecycle commands, one provider-neutral definition family, one real Codex adapter, one neutral conformance adapter, and the Feature 002 deterministic and human-review evidence set

## Change Risk and Boundaries *(mandatory)*

**Risk Level**: High — `main` changed Feature 001 authority closure, the public
diagnostic/result contract, CLI dispatch, and final evidence generation after
Feature 002's rejected review.

**Affected Public Boundaries**: Session lifecycle commands, canonical session
definition and guidance, provider projections, structured diagnostics/results,
Feature 001 authority references, distribution evidence, and live-session
review evidence.

**Affected Authority/Ownership**: The product owner owns intent and scope; the
kernel owns executable authority and diagnostic invariants; provider adapters
own lossless projection; the human operator owns effect grants; an independent
human reviewer owns final product acceptance.

**Dependencies and External Assumptions**: The branch consumes Feature 001's
merged factory contracts from `main`. The selected Codex version and model are
recorded external review inputs, not deterministic product dependencies. A live
review requires explicit authorization and fresh isolated sessions.

**Explicitly Unaffected Areas**: Consumer-domain semantics, additional provider
products, runtime hosting, provider-global installation, autonomous planning,
release publication, and Program Kit self-hosting remain outside this recovery.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design gate

| Principle / MUST | Status | Enforcement Mode | Owner | Evidence / Boundary | Failure Disposition | Planned Task/Proof |
|------------------|--------|------------------|-------|---------------------|---------------------|--------------------|
| I. Human Authority and Semantic Honesty | covered | executable-invariant / human-review | Human operator / independent reviewer | Exact grants, authority-negative proof, fresh live review | Block effects or keep acceptance pending | Authority regression; SC-003/SC-005 review |
| II. Independent Software Factory | covered | executable-invariant / evidence-backed | Maintainer | Package-only black-box CLI and source-marker proof | Block admission or release | Protected CI isolation proof |
| III. Exact Contracts and Governed Resolution | covered | executable-invariant | Kernel owner | Exact identities, schemas, and zero/multiple/stale fixtures | Return no trusted result | Contract and resolution matrices |
| IV. Honest Determinism and Evidence | covered | executable-invariant / evidence-backed / human-review | Kernel owner / reviewer | Declared profiles, exact evidence, honest live status | Downgrade claim or block | Evidence regeneration; fresh review |
| V. Artifact Ownership and Atomic Trust | covered | executable-invariant | Kernel owner / consumer | Ownership, staging, interruption, drift, removal proof | Preserve bytes and leave untrusted | Publication/removal matrices |
| VI. Explicit Extensions and Composition | covered | executable-invariant / evidence-backed | Adapter owner | Exact first-party adapter and neutral conformance | Reject unavailable or nonconforming provider | Conformance proof |
| VII. AI-Usable Diagnostics | covered | executable-invariant | Kernel owner | Complete schema-valid diagnostics, bounded remediation, exact evidence | Safest specific envelope; block release | Session diagnostic recovery task |
| VIII. Consumer Ownership, Runtime Isolation, and Local Safety | covered | executable-invariant / evidence-backed | Consumer / maintainer | Offline lifecycle, disclosure, package and runtime closure | Block admission or release | CI disclosure/runtime proof |
| IX. Evidence-First Vertical Delivery | covered | evidence-backed / human-review | Maintainer / product owner | Quickstart, platform matrix, fresh 10-session review, independent decision | Keep feature incomplete | CI and human recovery gates |
| V1 product boundary | covered | executable-invariant / human-review | Product owner | Dependency/API boundary and forbidden-symbol proof | Stop for scoped amendment | Architecture and review proof |
| Enforcement contract / Spec Kit workflow | covered | executable-invariant / evidence-backed | Maintainer | Analyze, owned proof matrix, tiered verification, explicit pending human gate | Stop on unowned MUST or overclaim | Convergence recovery phase |

**Pre-design result**: PASS. Phase 0 may proceed. No constitutional violation,
waiver, unresolved meaning, or product-boundary amendment is required.

### Post-design gate

Phase 1 preserves every pre-design decision:

- [research.md](research.md) separates documented Codex behavior from observed
  tool-version evidence and rejects an invented MCP or tool-registration API.
- [data-model.md](data-model.md) makes identities, request-bound authority,
  artifact ownership, publication state, installation validity, and session
  availability independently explicit.
- The [contracts](contracts/) preserve the existing operation-result envelope,
  distinguish provider-neutral definitions from Codex projections, and assign
  stable diagnostic namespaces.
- [quickstart.md](quickstart.md) proves package-only use outside Program Kit
  source, negative paths, runtime isolation, deterministic conformance, safe
  removal, and a separately reported human review.

**Post-design result**: PASS. No new constitutional violation or unjustified
abstraction was introduced. No waiver is requested.

## Project Structure

### Documentation (this feature)

```text
specs/002-session-integration-proof/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── cli.md
│   ├── codex-projection.md
│   ├── diagnostics.md
│   ├── session-installation-record.schema.json
│   ├── session-integration-definition.schema.json
│   ├── session-integration-request.schema.json
│   └── session-provider-manifest.schema.json
└── tasks.md                         # Created by $speckit-tasks, not this plan
```

### Source Code (repository root)

```text
.program-kit-source.json             # Authoring marker: reject self-integration
src/
├── ProgramKit.Contracts/
│   ├── SessionIntegration/          # Public types and exact identities
│   └── Schemas/                     # Embedded session schemas
├── ProgramKit.Kernel/
│   └── Artifacts/                   # General namespaced atomic set publisher
├── ProgramKit.SessionIntegration/
│   ├── Definitions/                 # Canonical definition loading/identity
│   ├── Providers/                   # Provider contract and conformance logic
│   ├── Publication/                 # Candidate, record, verify, remove workflows
│   └── Diagnostics/                 # Neutral PKSES catalog
├── ProgramKit.SessionIntegration.Providers.Codex/
│   ├── Projection/                  # Exact repository skill projection
│   └── Diagnostics/                 # Codex-specific PKCDX catalog
├── ProgramKit.Cli/
│   ├── Commands/Session/            # explain/install/verify/remove application commands
│   └── ProgramKit.Cli.csproj        # Exact packable .NET tool metadata
└── ProgramKit.Providers.DotNet/     # Existing factory provider; no session coupling

tests/
├── ProgramKit.UnitTests/            # Identity, authority, ownership, publisher tests
├── ProgramKit.ContractTests/        # Schema, diagnostic, result, provider conformance
├── ProgramKit.AcceptanceTests/      # Isolated package/session/runtime proof
├── Shared/                          # Shared deterministic test helpers
└── Fixtures/SessionIntegration/
    ├── Valid/
    ├── Invalid/
    ├── Drifted/
    ├── Colliding/
    └── Providers/

eng/
├── Pack-ProgramKitTool.ps1
├── Invoke-SessionIntegrationQuickstart.ps1
└── Invoke-CodexSessionReview.ps1
```

**Structure Decision**: Preserve the existing layered CLI/kernel/provider
solution and add two projects because the provider-neutral session lifecycle is
an independently testable development subsystem while the Codex projection is
replaceable provider-specific behavior. Public data contracts stay in
`ProgramKit.Contracts`; atomic filesystem mechanics stay in the kernel; the CLI
composes the exact first-party adapter explicitly. This prevents the CLI,
factory providers, and generated applications from depending on Codex or on
session guidance.

## Phase 0: Research Outcome

All technical unknowns are resolved in [research.md](research.md):

1. Current Codex guidance supports an installed CLI plus a repository-scoped
   skill; a dedicated MCP server or undocumented native tool registration is
   unnecessary for the first proof.
2. CLI acquisition is separate from session projection lifecycle. The exact
   tool package is `Orbyss.ProgramKit.Cli` version `1.0.0-alpha.1`, with command
   `program-kit`; its release identity includes a package digest and published
   metadata.
3. Canonical session meaning lives in a provider-neutral versioned definition.
   Codex receives only an exact generated projection under
   `.agents/skills/program-kit/`.
4. Install/remove authority is bound to the complete canonical request and
   expected live state. Explain/verify remain read-only.
5. Deterministic neutral conformance is release-blocking; live Codex interaction
   is exact-version, explicitly authorized, mandatory for Feature 002 product
   acceptance, and never an implicit CI dependency.

## Phase 1: Design Decisions

### Public contract changes

- Add versioned session definition, provider manifest, request, installation
  record, and typed public contract models with the schemas in `contracts/`.
- Preserve `program-kit.operation-result/v1` and add stable operation identities
  `session-explain`, `session-install`, `session-verify`, and `session-remove`.
- Add neutral `program-kit.session/PKSESxxxx` and Codex
  `program-kit.session.codex/PKCDXxxxx` diagnostics; reuse kernel diagnostics
  only when the underlying trigger is genuinely identical.
- Represent installation validity separately from provider session availability;
  an installed projection does not prove that a provider loaded it.

### Publication and ownership

- Generalize the existing recoverable publisher into a namespace-aware kernel
  mechanism without changing existing factory publication behavior.
- The Codex adapter owns only `.agents/skills/program-kit/`; session state lives
  under `.program-kit/session-integrations/codex/`. Existing content outside
  those exact paths is consumer-owned.
- Candidate artifacts are staged, canonicalized, validated, collision-checked,
  and journaled as one set before admission. Interrupted work remains explicit
  and untrusted.
- Removal compares exact recorded bytes and deletes only unchanged integration-
  owned artifacts. Drift causes a refusal and preserves every byte.

### Distribution and dependency boundary

- Configure `ProgramKit.Cli` as a packable .NET tool with exact package ID,
  command name, package version, and package readme. Its internal assemblies are
  delivered in the tool package; consumers do not restore Program Kit source.
- The session subsystem may depend on Contracts and Kernel. The Codex adapter
  depends on the neutral subsystem. The CLI composes both. Existing factory
  providers and generated applications must not reference session projects.
- The root authoring marker makes every session lifecycle operation against the
  Program Kit source repository fail closed. Acceptance tests use isolated
  temporary consumer repositories.

### Validation strategy

1. Unit tests prove exact identities, request/grant binding, canonical bytes,
   path safety, ownership, atomic staging, interruption recovery, verification,
   and drift-safe removal.
2. Contract tests prove every schema, diagnostic, JSON envelope, Codex
   projection, and neutral-provider normalization rule, including malformed,
   ambiguous, stale, unavailable, and disclosure-negative cases.
3. Acceptance tests pack and install the exact tool from a local feed into a
   workspace-local tool path, invoke it as a black box, perform the session
   lifecycle, run ten deterministic fresh-workspace trials, and verify generated
   runtime independence on Windows and Linux.
4. The explicitly authorized live script runs ten fresh Codex sessions at the
   recorded exact provider version. It records observations and human decisions,
   never silently promotes missing or partial review to success, is mandatory
   for Feature 002 product acceptance, and is not required for the independent
   source build or protected executable CI.
5. Final product review remains a named human gate. CI success is execution
   evidence, not semantic approval, publication authority, or release approval.

## Requirement and Proof Matrix *(mandatory)*

Every Feature 002 requirement is owned below exactly once. Historical proof may
remain evidence, but only proof whose declared inputs remain unchanged can be
reused for the remediated candidate.

| Requirement | Implementation Boundary | Proof Obligation | Proof Owner | Verification Tier | Invalidated By |
|-------------|-------------------------|------------------|-------------|-------------------|----------------|
| FR-001–FR-006 | Independent packaged CLI and runtime isolation | Isolated acquisition, direct invocation, source separation, post-removal runtime proof | Maintainer / protected CI | ci | Packaging, CLI entry point, dependencies, or runtime closure |
| FR-007–FR-014 | Canonical definition and exact provider projection | Definition/manifest identity, drift, round-trip, and incompatibility contract proof | Kernel and adapter owners | story / ci | Definition, manifest, projection, public operations, or support envelope |
| FR-015–FR-023 | Exact authorized installation lifecycle | Selection, authority, preflight, atomic publication, verification, interruption, and result proof | Kernel owner | story / ci | Authority, publication, record, CLI binding, or result contract |
| FR-024–FR-032 | Human-led session guidance and public journey | Focused guidance/authority regression plus ten fresh sessions completing the full journey | Product owner / independent reviewer | story / human | Guidance, authority, diagnostics, provider projection, CLI behavior, or model/provider review inputs |
| FR-033–FR-038 | Provider-neutral conformance | Direct/neutral/Codex parity and fail-closed conformance proof | Adapter owner / protected CI | story / ci | Adapter, canonical definition, normalization, operations, authority, or disclosure |
| FR-039–FR-043 | Diagnostics, disclosure, and local safety | Schema-valid production diagnostics with exact evidence plus adversarial disclosure/local-safety proof | Kernel owner / protected CI | story / ci | Diagnostic catalog/factory/schema/projector, disclosure classification, or external effects |
| FR-044–FR-046 | Exact safe removal | Authorized exact-record removal, drift refusal, byte preservation, and absent-state proof | Kernel owner / protected CI | story / ci | Record, ownership, publication, removal, verification, or path handling |
| SC-001 | Ten-minute documented setup | Timed isolated supported-platform quickstart | Protected CI | ci | Packaging, documentation steps, installation, or verification |
| SC-002 | Ten consecutive complete-or-safe installations | Current Windows/Linux deterministic matrix | Protected CI | ci | Installation/admission/publication behavior or platform inputs |
| SC-003 | Ten consecutive successful fresh sessions | New bounded 10/10 live review after current CI candidate | Independent reviewer | human | Any product/API/authority/guidance/provider/model input affecting the journey |
| SC-004 | Exact negative next-action/effect classes | Packaged and production negative matrices | Kernel owner / protected CI | story / ci | Diagnostics, disposition, effects, authority, or failure handling |
| SC-005 | Missing input requested within two turns | Focused guidance proof and new bounded 10/10 live review | Product owner / independent reviewer | story / human | Guidance, diagnostics, authority, provider/model input, or scenario protocol |
| SC-006 | Direct/provider/neutral semantic parity | Shared conformance corpus | Adapter owner / protected CI | story / ci | Adapter, normalization, result, diagnostic, or canonical contract |
| SC-007 | Exact installation record | Record/schema/current-binding proof | Kernel owner / protected CI | story / ci | Identity, CLI/package/executable, provider, projection, or record schema |
| SC-008 | Removal preserves unrelated bytes | Removal fixture corpus and packaged removal proof | Kernel owner / protected CI | story / ci | Ownership, record, removal, publication, or path handling |
| SC-009 | Zero protected disclosure or hidden effects | Adversarial result/projection/evidence/package scan | Security proof owner / protected CI | story / ci | Disclosure, diagnostics, evidence fields, packaging, network, telemetry, or provider launch |
| SC-010 | Generated runtime remains independent | Restore/build/start/status after integration removal | Protected CI | ci | Generated output, dependencies, runtime entry point, or package closure |
| Constitution VII | Complete AI-usable diagnostic contract | Every production diagnostic schema-valid with typed disposition, expected/observed, bounded remediation, and exact evidence | Kernel owner | story / ci | Diagnostic catalog/factory/schema/projector/fallback |
| Constitution IX / Spec Kit workflow | Honest closure and proportional proof | No unresolved high finding; only invalidated proof reruns; human decision remains explicit | Maintainer / product owner | pre-pr / ci / human | Requirement, proof ownership, invalidation classification, or accepted claim |

## Verification Strategy *(mandatory)*

| Tier | Purpose | Required Checks | Explicitly Excluded |
|------|---------|-----------------|---------------------|
| Edit | Seconds-scale feedback | Affected project build and focused unit test | Restore, evidence regeneration, full contract/acceptance |
| Story | Prove the repaired boundary | Relevant unit/contract plus narrowly scoped authority, diagnostic, guidance, and session acceptance proof | Unrelated suites, packaging matrix, live sessions |
| Pre-PR | Catch local integration errors once | Isolated locked restore/build, complete unit/contract, changed-file formatting and diff hygiene | Full acceptance/conformance, repeated workspaces, cross-platform matrix, live sessions |
| CI | Authoritative executable merge proof | Full acceptance/conformance/evidence and required Windows/Linux matrix for the exact candidate | Duplicate local full-gate rerun |
| Human | Decide subjective fitness | Ten fresh sessions and a named independent review of bounded claims/limitations | Repeating mechanizable proof already established by CI |

**Evidence Reuse Rule**: Evidence is reusable only while its declared source,
contracts, provider/model inputs, platform profile, and scenario remain unchanged.
The rejected 8/10 review remains historical evidence and can never be reused as
acceptance. Merge-invalidated generated evidence is refreshed once at the final
candidate boundary; timestamps and unrelated documentation commits alone do not
force executable reruns.

**Acceptance Invalidation Rule**: Changes to public behavior, canonical guidance,
provider projection, authority, diagnostics/results, disclosure, security, or
runtime/session semantics invalidate applicable executable proof and the live
human review. Proof-only changes require new executable evidence and human
review only if the accepted claim or limitation changes. Documentation,
formatting, and metadata changes do not invalidate product acceptance unless
they change reviewed guidance, evidence bytes, or claims.

## Complexity Tracking

No constitutional violation requires justification. The two new projects are
the smallest structure that makes the provider-neutral contract independently
testable and keeps provider-specific Codex behavior out of both the kernel and
generated software.

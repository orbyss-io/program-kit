# Implementation Plan: Claude Code Session Adapter

**Branch**: `codex/003-claude-code-adapter` | **Date**: 2026-08-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-claude-code-adapter/spec.md`

## Summary

Add a first-party Claude Code adapter that consumes Feature 002's accepted
provider-neutral session contract unchanged. The adapter deterministically
projects a minimal repository skill at `.claude/skills/program-kit/SKILL.md`,
invokes the exact workspace-local Program Kit CLI through Claude Code's existing
shell capability, adds only Claude-specific diagnostics and conformance
evidence, and registers its exact manifest explicitly in the CLI catalog. A
sealed review kit proves the integration on a separate consumer machine with
Claude Code `2.1.220`, while deterministic CI remains independent of provider
credentials, live models, and network availability.

## Technical Context

**Language/Version**: C# 14 on .NET 10 pinned by SDK `10.0.302`; PowerShell 7 for review-kit export and external-machine validation

**Primary Dependencies**: Feature 002's `ProgramKit.Contracts`, `ProgramKit.Kernel`, `ProgramKit.SessionIntegration`, CLI lifecycle, schemas, neutral harness, and existing System.Text.Json/JsonSchema.Net/YamlDotNet/MSTest dependencies; exact external Claude Code `2.1.220` for live review only; no new third-party Program Kit runtime package

**Storage**: One generated-owned Markdown skill in the consumer repository, Feature 002 generic JSON lifecycle records, and a provider-specific safe JSON machine-review record; no database or remote Program Kit state

**Testing**: Existing MSTest and schema/golden fixture infrastructure, shared Feature 002 conformance corpus, Windows/Linux deterministic tests, sealed-kit validation, ten clean-workspace repetitions, ten exact-version live Claude trials, and one independent interactive human review

**Target Platform**: Windows and Linux development workspaces; one separate clean Windows or Linux machine/equivalent boundary for accepted live evidence; Claude Code CLI `2.1.220`

**Project Type**: Multi-project .NET library and CLI repository with one provider-adapter project and external validation scripts

**Performance Goals**: A new consumer completes exact CLI bootstrap, Claude adapter explanation/installation/verification, fresh-session discovery, and first governed explanation within 10 minutes; adapter projection and verification remain bounded by one skill plus small lifecycle records

**Constraints**: Feature 002 contracts are immutable dependencies unless a surfaced upstream gap stops the feature; exact workspace scope; no settings/CLAUDE.md/global/plugin/MCP edits; no skill tool preapproval; no live-provider dependency in build/CI; no transcripts, credentials, telemetry, source upload, self-hosting, or generated runtime coupling

**Scale/Scope**: One exact provider release, one adapter project, one projected skill file, one provider manifest/catalog, eight provider diagnostics, one conformance profile, one safe review schema, one sealed external-machine kit, and the required deterministic/live trial corpus

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design gate

| Principle or boundary | Applicability and decision | Enforcement mode | Planned evidence | Failure disposition | Waiver |
|---|---|---|---|---|---|
| I. Human Authority and Semantic Honesty | Applies. Claude may discover guidance and invoke read-only explanation, but cannot create meaning, trust, selection, or grants. Live fitness remains human-reviewed. | `executable-invariant` and `human-review` | Shared authority corpus, no-permission skill fixture, exact trial evidence, human review | Block effects or leave review pending/failed | Kernel authority gates not waivable |
| II. Independent Software Factory | Applies. The adapter calls only the exact packaged CLI in a clean external consumer workspace; Program Kit source/Spec Kit/live Claude are absent from bootstrap. | `executable-invariant` and `evidence-backed` | Package-only review kit, source-marker refusal, forbidden dependency tests | Block admission/release | Not waivable |
| III. Exact Contracts and Governed Resolution | Applies. Provider `2.1.220`, adapter, canonical definition, CLI, surface, catalog, corpus, workspace, and skill bytes resolve exactly. | `executable-invariant` | Manifest/schema/identity fixtures and zero/multiple/stale cases | Adapter unavailable or incompatible; no trusted result | Not waivable |
| IV. Honest Determinism and Evidence | Applies. Skill bytes and normalized bindings are deterministic; Claude/model behavior is external human-reviewed observation, never deterministic proof. | `executable-invariant`, `evidence-backed`, `human-review` | Repeatability/permutation tests, sealed digests, live review statuses | Downgrade claim, fail, or leave not evaluated | Evidence truth not waivable |
| V. Artifact Ownership and Atomic Trust | Applies. One dedicated skill directory is generated-owned and published/removed through Feature 002's namespaced atomic lifecycle. | `executable-invariant` | Collision, interruption, drift, journal, and exact-removal fixtures | Preserve bytes and keep integration untrusted | Not waivable |
| VI. Explicit Extensions and Composition | Applies. Claude adapter is an exact first-party session adapter, not a factory provider role or dynamic extension. | `executable-invariant` and `evidence-backed` | Project dependency tests, explicit catalog, shared conformance corpus | Reject missing/nonconforming adapter | Not waivable |
| VII. AI-Usable Diagnostics | Applies. Shared Program Kit results remain authoritative; only exact Claude triggers receive PKCLD identities. | `executable-invariant` | Catalog/golden/redaction/transport/provider-contradiction fixtures | Safe structured fault or release block | Not waivable |
| VIII. Consumer Ownership, Runtime Isolation, and Local Safety | Applies. No global/provider settings are modified; provider credentials/output are excluded; generated software has no session/provider runtime dependency. | `executable-invariant` and `evidence-backed` | Ownership, disclosure, offline lifecycle, package closure, generated runtime tests | Block admission/release | Not waivable |
| IX. Evidence-First Vertical Delivery | Applies. A second real provider plus isolated-machine journey directly tests neutrality; plugins/MCP/broader Claude surfaces remain deferred. | `evidence-backed` and `human-review` | Quickstart, cross-provider corpus, 10+10 trials, external human decision | Keep feature incomplete or claim pending | No waiver planned |
| V1 product boundary | Applies. No planning, migration, runtime engine, dynamic provider loading, marketplace, source generator, MSBuild extension, or universal semantic machinery is added. | `executable-invariant` and `human-review` | Dependency/API/fixture review and plan acceptance | Stop for explicit amendment before crossing boundary | Not applicable |
| Enforcement contract and Spec Kit workflow | Applies. Every claim has an honest mode; feature is specified/planned through Spec Kit and implemented only after Feature 002. | `evidence-backed` and `executable-invariant` | This gate, dependency precondition, source marker, task traceability | Stop on upstream ambiguity or missing gate evidence | Kernel gates not waivable |

**Pre-design result**: PASS. Phase 0 may proceed. The second-provider project is
justified by a concrete portability proof. No waiver, unresolved meaning, or
constitutional amendment is required.

### Post-design gate

Phase 1 preserves the pre-design boundary:

- [research.md](research.md) selects only documented project skills and rejects
  settings, CLAUDE.md, plugins, MCP, global scope, and permission-granting skill
  metadata.
- [data-model.md](data-model.md) references rather than duplicates Feature 002
  canonical entities and separates provider permission, Program Kit authority,
  installation integrity, skill discovery, live observation, and human review.
- [contracts](contracts/) bind exact Claude Code `2.1.220`, one skill file,
  provider-only diagnostics, shared semantic conformance, and safe external
  evidence.
- [quickstart.md](quickstart.md) proves package-only use on a clean machine,
  negative paths, actual provider discovery, exact removal, disclosure, and
  generated runtime independence.

**Post-design result**: PASS. No Feature 002 contract change, constitutional
violation, or waiver is planned. An implementation-discovered canonical gap
must stop this feature and return to upstream specification/design.

## Project Structure

### Documentation (this feature)

```text
specs/003-claude-code-adapter/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── claude-code-adapter.md
│   ├── conformance.md
│   ├── diagnostics.md
│   └── isolated-machine-review.schema.json
└── tasks.md                         # Created later by $speckit-tasks
```

### Source Code (repository root)

```text
src/
├── ProgramKit.Contracts/            # Feature 002 public contracts; no Claude vocabulary
├── ProgramKit.Kernel/               # Feature 002 authority/publication invariants; unchanged
├── ProgramKit.SessionIntegration/   # Feature 002 neutral lifecycle; unchanged unless upstream gap accepted
├── ProgramKit.SessionIntegration.Providers.Codex/
├── ProgramKit.SessionIntegration.Providers.ClaudeCode/
│   ├── Manifest/                    # Exact first-party provider manifest
│   ├── Projection/                  # Canonical .claude skill projection
│   ├── Invocation/                  # Executable + argument-array normalization
│   ├── Diagnostics/                 # PKCLD catalog
│   ├── Conformance/                 # Provider profile and safe observations
│   └── Schemas/                     # Embedded isolated-machine review schema
└── ProgramKit.Cli/                  # Explicit adapter registration/help/version catalog

tests/
├── ProgramKit.UnitTests/
│   └── SessionIntegration/ClaudeCode/
├── ProgramKit.ContractTests/
│   └── SessionIntegration/ClaudeCode/
├── ProgramKit.AcceptanceTests/
│   └── SessionIntegration/ClaudeCode/
├── Shared/SessionIntegration/       # Feature 002 corpus reused by all adapters
└── Fixtures/SessionIntegration/ClaudeCode/
    ├── Valid/
    ├── Invalid/
    ├── Drifted/
    ├── Colliding/
    └── Evidence/

eng/
├── Export-ClaudeCodeReviewKit.ps1
└── ClaudeCodeReview/
    ├── Initialize-ConsumerWorkspace.ps1
    ├── Invoke-DeterministicConsumerProof.ps1
    ├── Invoke-ClaudeCodeTrials.ps1
    └── Complete-HumanReview.ps1
```

**Structure Decision**: Add one provider project because Claude-specific skill
paths, front matter, exact version support, invocation behavior, and diagnostics
must be mechanically absent from neutral contracts and other providers. Reuse
Feature 002's contracts, lifecycle, publisher, authority, result envelope, and
conformance corpus. The CLI adds only explicit first-party catalog composition.
Review scripts remain engineering evidence tooling and never enter generated
consumer runtime artifacts.

## Phase 0: Research Outcome

All technical unknowns are resolved in [research.md](research.md):

1. Claude Code project skills are the documented workspace-only capability
   surface; the exact projection is `.claude/skills/program-kit/SKILL.md`.
2. Claude Code `2.1.220` is the exact initial support target and is installed,
   authenticated, and version-pinned outside Program Kit ownership.
3. The skill grants no provider tools. Model discovery may load guidance, while
   Program Kit independently enforces request-bound effect authority.
4. Deterministic tests never launch Claude. External trials use normal
   `claude -p`, not `--bare`, because bare mode skips project skills.
5. A sealed review kit provides exact source-free artifacts to the isolated
   machine and returns only safe classified evidence.

## Phase 1: Design Decisions

### Dependency and public contract boundary

- Feature 002 is a hard implementation prerequisite. Its generic lifecycle
  grammar, requests, grants, provider manifest schema, installation record,
  structured result, session states, and neutral diagnostics remain unchanged.
- Feature 003 adds a manifest instance, adapter assembly, embedded
  provider-specific evidence schema, PKCLD catalog, and CLI catalog entry.
- If Claude Code exposes a mandatory capability that the accepted provider
  manifest cannot represent, implementation stops and raises an upstream design
  change rather than extending the adapter privately.

### Projection and ownership

- Generate exactly one UTF-8/LF `SKILL.md` with minimal front matter and
  canonical guidance plus Claude invocation mechanics.
- Own only the exact absent-at-install `.claude/skills/program-kit/` directory.
  All parents and other provider files remain consumer-owned.
- Publish, verify, journal, and remove through Feature 002's namespaced atomic
  artifact-set lifecycle. No provider adapter writes directly.
- Never emit `allowed-tools`, dynamic commands, scripts, settings, CLAUDE.md,
  plugins, MCP, credentials, approval, or consumer semantics.

### Conformance and diagnostics

- Reuse the complete neutral scenario corpus and add Claude-specific fixtures
  for version, skill discovery/trust, invocation permission/transport, live
  review, and provider/Program Kit result contradiction.
- Compare direct CLI, neutral harness, Codex adapter, and Claude adapter
  canonical meaning. Provider-specific reasons may add diagnostics but cannot
  change underlying outcome/effect/disposition semantics.
- Reuse kernel/neutral IDs for identical triggers and add only the eight stable
  PKCLD entries defined in `contracts/diagnostics.md`.

### Isolated-machine evidence

- Export a sealed directory containing the exact Program Kit tool package,
  public schemas, requests/fixtures, safe scripts, and complete digest manifest;
  exclude source, Spec Kit, credentials, grants, and transcripts.
- On the external machine, separately verify Claude Code `2.1.220`, bootstrap
  the exact CLI from the local sealed feed, execute lifecycle and negative
  proofs, run an interactive walkthrough, and run ten fresh print-mode trials.
- Parse provider output transiently against a bounded schema, then discard it.
  Derive verdicts from actual Program Kit results, receipts, and filesystem
  identities. Store only the safe review schema.
- Live review may be accepted, rejected, pending, failed, incompatible,
  inconclusive, or not evaluated. Missing external prerequisites never break
  the independent source build or become a pass.

### Validation sequence

1. Unit tests: manifest identity, exact skill bytes, front-matter allowlist,
   invocation arrays, diagnostics, safe record canonicalization, and no provider
   permission grant.
2. Contract tests: manifest/schema resolution, common reference closure,
   diagnostic golden results, cross-provider corpus parity, provider-symbol
   isolation, disclosure/redaction, and exact-version incompatibility.
3. Acceptance tests: package-only lifecycle in temporary consumer repositories,
   ten repeatability trials, collision/interruption/drift/removal/source-marker
   negatives, and generated runtime independence on Windows/Linux.
4. Review-kit tests: deterministic export, manifest digest verification,
   source/secret exclusion, tamper refusal, and safe review-record validation.
5. External review: exact provider version, clean-boundary attestation,
   interactive human walkthrough, ten fresh Claude trials, actual-effect checks,
   and explicit human product decision.

## Complexity Tracking

No constitutional violation requires justification. The single new provider
project and external review kit each have a concrete independently testable
purpose: keeping Claude vocabulary out of canonical contracts and proving the
adapter on a source-free consumer machine.

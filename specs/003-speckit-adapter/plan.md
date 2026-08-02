# Implementation Plan: Program Kit Adapter for Spec Kit

**Branch**: `codex/003-speckit-adapter` | **Date**: 2026-08-02 | **Spec**: [spec.md](spec.md)

**Input**: Human-approved feature specification and accepted `DEC-046` design.

**Planning status**: Human-approved; implementation authorized.

## Summary

Deliver the first separately installed Program Kit Adapter for Spec Kit as one
complete consumer-only vertical slice. Program Kit gains exact workspace
initialization, local catalog, manifest/lock restore, effect-free preparation,
and repository authority recording through new versioned public CLI contracts.
A separate framework-dependent adapter executable, shipped inside a Spec Kit
0.15.1 extension, converts a reviewed feature handoff into existing public
factory inputs without kernel/provider coupling or heuristic prose admission.

The smallest complete proof starts from two clean consumer workspaces, installs
the exact local Program Kit tool and Spec Kit extension, creates all manifest,
handoff, definitions, requests, grants, and products through supported public
flows, completes construct/evaluate for two distinct .NET examples, and proves
the non-factory, authority, ownership, diagnostic, offline, lifecycle, and
runtime-isolation boundaries. Local work uses focused edit/story checks; one
pre-PR integration pass precedes authoritative Windows/Linux CI and three
fresh human journeys.

## Technical Context

**Language/Version**: C# 14 on `net10.0`; extension command/config/handoff
documents in Markdown, restricted YAML, and canonical JSON

**Primary Dependencies**: .NET SDK `10.0.302`; `System.Text.Json`; JsonSchema.Net
`9.4.0`; YamlDotNet `18.1.0`; existing Program Kit public contracts/kernel/.NET
provider; Spec Kit exactly `0.15.1`

**Storage**: Repository-local files only: .NET tool manifest, consumer-owned
`program-kit.yaml`, generated `program-kit.lock.json`, `.program-kit/` state and
authority records, Spec Kit extension registration, consumer-owned exact
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`,
and feature-local handoff/generated evidence

**Testing**: MSTest unit, contract, and acceptance suites; schema/golden,
repeatability/permutation, dependency architecture, package inspection,
black-box child-process, negative/adversarial, cross-platform lifecycle, two
clean consumer journeys, and three named human journeys

**Target Platform**: Exact Spec Kit 0.15.1 consumer workspaces on Windows and
Linux with .NET 10 runtime; no macOS support claim in V1

**Project Type**: Multi-project .NET CLI/software factory plus a separately
packaged Spec Kit extension containing one framework-dependent .NET executable

**Performance Goals**: Base doctor, config/handoff validation, and translation
complete in under two seconds for the reference feature excluding invoked
factory/external build work; no repository-wide hashing; unchanged evidence is
reused by declared invalidation set

**Constraints**: Exact versions and identities; offline after declared package
acquisition; no telemetry/source upload; no PATH/global fallback; no shell
evaluation; public-contract-only adapter dependency; field-level trace;
canonical deterministic adapter outputs; atomic ownership-aware writes; no
automatic authority/construction; consumer products have zero authoring-tool
runtime dependency

**Scale/Scope**: One Spec Kit release, one Program Kit release, one compiled
first-party .NET provider/profile, five new Program Kit commands, ten extension
commands, two factory examples, one documentation-only/mixed-workspace proof,
and no marketplace/dynamic provider/migration/global graph/Claude adapter

## Change Risk and Boundaries *(mandatory)*

**Risk Level**: High — this slice adds public contracts, workspace state,
authority materialization, an external child-process adapter, package lifecycle,
and cross-platform proof. Kernel authority, ownership, diagnostic, disclosure,
and atomicity gates are non-waivable.

**Affected Public Boundaries**:

- Program Kit CLI grammar/help/version and package identity;
- public request/result, workspace manifest/lock, catalog, preparation,
  authority-decision, adapter, and diagnostic schemas;
- Program Kit distribution descriptor/provider catalog;
- repository authority-provider recording interface;
- Spec Kit extension manifest, commands, hooks, configuration, archive layout;
- feature-local handoff/review/generated artifact layout; and
- package-only consumer quickstart/evidence.

**Affected Authority/Ownership**:

- the human owns applicability, semantic fields, profile choice, handoff review,
  authority decision, custom implementation, and plan acceptance;
- Program Kit kernel owns exact resolution, preparation, authority validation,
  construction admission, Program Kit state/product ownership, and diagnostics;
- the repository authority provider owns grant/revocation recording;
- Spec Kit owns extension registration/managed integration files;
- the adapter owns only its release files and generated feature candidates;
- .NET owns the local tool manifest/package installation; and
- the consumer owns project config, accepted handoffs/reviews, and custom code.

**Dependencies and External Assumptions**:

- Spec Kit 0.15.1 extension add/update/enable/disable/remove and hook registration
  behave according to its exact published contract; mismatch fails closed.
- .NET local tools acquire exactly `Orbyss.ProgramKit.Cli@1.0.0-alpha.2`; package
  sources are explicit during acquisition and are not adapter semantic inputs.
- Program Kit advances its one operation-result contract to v2 for every public
  command; no parallel v1 result type or execution path remains current.
- The first-party DotNet provider remains compiled and explicitly registered.
- The authority provider records declared human provenance but makes no
  cryptographic identity claim.

**Explicitly Unaffected Areas**:

- existing v1 explain/construct/evaluate request semantics and factory-request
  schema identities; their single current operation-result surface advances to
  v2 as recorded in R003;
- provider construction templates and CShells semantics except exact new
  adapter-produced inputs exercising the already supported profile;
- Codex session integration domain behavior, provider interface, lifecycle, and
  human UX; its exact result/guidance/definition bindings advance with the
  containing CLI contract;
- generated consumer runtime architecture;
- Spec Kit managed core templates/scripts/skills; and
- deferred marketplace, dynamic provider loading, migration, runtime hosting,
  deployment, operational state, global graph, and Claude adapter work.

## Constitution Check

*GATE: Completed before Phase 0 and re-evaluated after Phase 1. No waiver is
requested or permitted for any kernel gate.*

| Principle / MUST | Status | Enforcement Mode | Owner | Evidence / Boundary | Failure Disposition | Planned Task/Proof |
|---|---|---|---|---|---|---|
| I. Human Authority and Semantic Honesty | covered | executable-invariant + human-review | Human reviewer; kernel/adapter maintainers | Explicit handoff/review; no heuristic admission; separate decision/grant | needs-input/request-approval; no effect | Handoff/trace/authority slices; negative matrix; human review |
| II. Independent Software Factory | covered | executable-invariant + evidence-backed | CLI and adapter maintainers | Adapter references Contracts only and invokes public CLI; downstream package-only proof; no self-use | stop/release block | Architecture tests; clean bootstrap; package consumer proof |
| III. Exact Contracts and Governed Resolution | covered | executable-invariant | Kernel/contracts owners | Closed schemas; exact catalog/manifest/lock; no ranges/fallback/implicit selection | blocked; no trusted lock/result | Schema, restore, ambiguity, and closure tests |
| IV. Honest Determinism and Evidence | covered | evidence-backed | Adapter translator; provider owner | Deterministic scope limited to adapter projection; custom source remains custom-bounded | revise/block or downgraded claim | Repeated/permuted golden proof and evidence invalidation tests |
| V. Artifact Ownership and Atomic Trust | covered | executable-invariant | Kernel and adapter publishers | Three ownership classes, staged set publication, digest-checked cleanup, no mixed files | repair/stop; no partial trust | Collision, drift, interruption, cleanup, lifecycle tests |
| VI. Explicit Extensions and Composition | covered | executable-invariant | CLI composition/provider owners | One explicitly registered shipped provider; adapter not a provider; no dynamic loading | stop/release block | Dependency/registry/unsupported-package tests |
| VII. AI-Usable Diagnostics | covered | executable-invariant | Diagnostic catalog owners | Operation-result v2 and adapter result; typed catalogs; exact embedded PK result; safe fallback | faulted/blocked with typed continuation | Schema/golden/production-trigger/disclosure tests |
| VIII. Runtime Isolation and Local Safety | covered | executable-invariant + evidence-backed | Distribution/security owners | No adapter network/telemetry/upload/shell; consumer product has no authoring runtime dependency | stop/release block | Offline/process/secret/package/runtime inspection |
| IX. Evidence-First Vertical Delivery | covered | evidence-backed + human-review | Feature proof owner | Two clean distinct examples, non-factory/mixed flow, negatives, package proof, human validation | implementation/release block | Story/CI/human proof packet |
| V1 product boundary | covered | executable-invariant | Product/architecture owners | net10, exact CShells profile, three provider roles unchanged, no deferred machinery | stop and return to design | Boundary/dependency tests and scope audit |
| Enforcement contract | covered | executable-invariant | Kernel/feature proof owners | Every FR/SC/negative/constitutional row has mode, owner, proof, invalidation; no waiver | planning/implementation block | Matrix below; analyze before implementation |
| Spec Kit workflow/integrity | covered | evidence-backed | Repository workflow owner | This packet uses Spec Kit; adapter never self-hosts; extension/project layers survive upgrade without force | planning/release block | Integrity check and manifest-aware upgrade acceptance |

**Post-design re-evaluation**: Research, data model, contracts, project
structure, and quickstart introduce no unowned MUST, new provider role, private
coupling, ambient semantic default, or waiver. All rows remain `covered`.

## Requirement and Proof Matrix *(mandatory)*

### Functional requirements

| Requirement | Implementation Boundary | Proof Obligation | Proof Owner | Verification Tier | Invalidated By |
|---|---|---|---|---|---|
| FR-001 | CLI distribution resolver | Exact local manifest invocation; global shadow refused | CLI owner | Story + CI matrix | resolver, tool package, release binding |
| FR-002 | Kernel workspace bootstrap | Neutral zero-selection absent-file init; exact rerun unchanged | Workspace owner | Story + CI | init schema/service/publication |
| FR-003 | Bootstrap admission/evidence | Forbidden effects absent; explicit invocation/effect evidence; conflict atomic | Workspace owner | Story + CI | init contract, ownership, disclosure |
| FR-004 | Distribution catalog command | Offline exact inventory; listing never selects or writes | Distribution owner | Story + CI | descriptor, catalog schema/command |
| FR-005 | Workspace manifest contract | Empty/multiple exact named selections/default; ranges/best match refused | Contracts owner | Unit + Contract | manifest schema/binder |
| FR-006 | Restore/resolution service | Exact base/factory lock; semantic invalidation only | Resolution owner | Story + CI | restore, lock, descriptor/evidence |
| FR-007 | State model/result projection | Installed/available/selected/activated/authorized stay distinct | Kernel owner | Contract + CI | state enums, result/help/diagnostics |
| FR-008 | Extension archive/manifest | Exact command installs extension/executable; managed core unchanged | Extension owner | CI matrix | extension manifest/layout/Spec Kit line |
| FR-009 | Adapter project/process client | Binary dependency closure contains no private/kernel/provider/test/eng/Spec Kit module | Adapter owner | Pre-PR + CI | project/package references, process client |
| FR-010 | Adapter doctor | Base doctor accepts zero profile; feature doctor requires complete feature closure | Adapter owner | Story + CI | doctor/config/compatibility/lock checks |
| FR-011 | Adapter config resolver | Exact override > repo default > off; ambient layers ignored | Adapter config owner | Unit + Story | config schema/resolver |
| FR-012 | Applicability/hook dispatcher | Non-factory/disabled: zero profile, process, artifact, authority, block | Hook owner | Story + CI | applicability resolver/hooks |
| FR-013 | Effective selection resolver | Exact override/default locked and inheritance source recorded | Adapter owner | Unit + Story | config, lock, handoff projection |
| FR-014 | Handoff staleness/default drift | Existing reviewed handoff never silently rebinds | Trace owner | Story + CI | default resolver, handoff/trace |
| FR-015 | Spec Kit hooks | Conditional proposal/validation only; never init/authority/construct | Hook owner | Contract + CI | extension manifest/command instructions/hooks |
| FR-016 | Extension/feature lifecycle | Update/disable/re-enable/remove/cleanup preserve ownership; upgrade no force | Extension owner | CI matrix | lifecycle manifest, publisher, Spec Kit version |
| FR-017 | Handoff schema/binder | Complete projection, four disposition lists, exact trace, no grant | Adapter contracts owner | Contract + Story | handoff schema/binder |
| FR-018 | Handoff proposal boundary | AI proposal never admitted as authority; no heuristic fields | Adapter owner + human | Contract + Human | command guidance, proposal/validation |
| FR-019 | Review validator | Exact named review separate from grant; handoff edit stales | Review owner | Unit + Story | review schema/digest validator |
| FR-020 | Trace resolver | Named-block field-level invalidation; unrelated edits reuse evidence | Trace owner | Unit + Story | trace grammar/resolver/invalidation map |
| FR-021 | Translator/canonical publisher | Equal relevant inputs emit byte-identical outputs | Translator owner | Story + CI | translator, schemas, canonical profile, compat manifest |
| FR-022 | Kernel preparation operation | Exact ungranted proposal/explanation/live state; zero publication | Kernel owner | Contract + Story + CI | preparation schemas/resolution/live-state logic |
| FR-023 | Repository authority record operation | Exact human decision materializes atomic non-broadened grant/revocation | Authority owner | Story + CI + Human | authority request/decision/provider/store |
| FR-024 | Adapter authority guard | Adapter never issues/populates/broadens/infers/selects grant | Adapter owner | Unit + Story + CI | adapter request/projector/hooks |
| FR-025 | Construct orchestration | Reviewed/fresh prepared/explained/current exact grant/preflight all required | Kernel + adapter owners | Story + CI | construct projector/preflight/authority validator |
| FR-026 | Adapter result projector | Versioned result, honest stage/effect, exact unmodified PK result | Adapter result owner | Contract + Story | result schema/projector |
| FR-027 | Adapter diagnostic catalog | Typed exact diagnostics and actionable continuations; no prose parsing | Diagnostics owner | Contract + CI | catalog/factory/production triggers |
| FR-028 | Adapter artifact publisher | Atomic owned set; unsafe/colliding/escape/overwrite/interruption refused | Publisher owner | Unit + Story + CI | logical paths, staging, journal/manifest |
| FR-029 | Adapter disclosure/fallback | Secrets/fingerprints/paths/raw output/exceptions/commands withheld | Security owner | Contract + CI | disclosure classifier/process/fallback |
| FR-030 | Consumer runtime closure | Generated products contain no Program Kit/Spec Kit/adapter/AI runtime refs | Provider/product proof owner | CI | provider output/package graph |
| FR-031 | Compatibility manifest | Exact Spec Kit/PK/profile/runtime/contracts/OS; deferred capabilities absent | Product owner | Contract + CI | release/version/schema/provider/platform metadata |
| FR-032 | Complete proof harness | Two clean, non-code, mixed, lifecycle, negative, package, human; production authority | Feature proof owner | CI + Human | scenarios, public commands, UX/claims |
| FR-033 | Verification tooling/CI | Five tiers, invalidation sets, no duplicate local full matrix | Workflow owner | Pre-PR + CI | verification scripts/workflow/evidence policy |
| FR-034 | Repository architecture guard | No adapter install/self-construction; downstream behavior only in packages | Architecture owner | Pre-PR + CI | references, scripts, consumer harness |
| FR-035 | CLI composition/registry | Only exact shipped explicitly registered first-party provider executes | CLI composition owner | Contract + CI | composition root, package graph, provider registry |
| FR-036 | Translator output closure | Required definition/bundle/refs/trace/requests; identities only approved sources | Translator owner | Contract + Story | output projector/compat manifest/prepare result |
| FR-037 | Adapter process/offline guard | Zero telemetry/upload/network; exact argv, no shell | Security/process owner | Unit + CI | process runner, environment/network harness |

### Success criteria

| Requirement | Implementation Boundary | Proof Obligation | Proof Owner | Verification Tier | Invalidated By |
|---|---|---|---|---|---|
| SC-001 | Clean consumer E2E harness | Two distinct natural-language-to-evaluate journeys; no prohibited preseed | Acceptance owner | CI | package/extension/public flow/scenario bytes |
| SC-002 | Non-factory/mixed hook harness | Exactly zero PK child launches and feature artifacts | Hook acceptance owner | Story + CI | applicability/config/hooks/process recorder |
| SC-003 | Translator golden harness | Five repeats/permutations per handoff byte-identical | Translator proof owner | Story + CI | translator/schema/compat/fixture bytes |
| SC-004 | Negative/adversarial matrix | Every case exact result/diagnostic/effect and zero unauthorized writes | Negative proof owner | Story + CI | relevant boundary/fixture/catalog |
| SC-005 | Packaged lifecycle matrix | Full install/select/restore/update/disable/remove on Windows/Linux; no force | Release proof owner | CI matrix | package/extension/Spec Kit/OS lifecycle |
| SC-006 | Default/lifecycle preservation | Zero reviewed rebinds and zero consumer/PK artifact rewrites | Adapter lifecycle owner | Story + CI | config/default/lifecycle/ownership |
| SC-007 | Consumer runtime inspection | Both products build, test, start, perform their demonstrated behavior, and have zero authoring-tool runtime references | Runtime proof owner | CI | generated package/runtime graph |
| SC-008 | Guided consumer review | Three uncoached journeys locate every named workspace/product/evidence artifact, distinguish all five states plus ownership/default/override/non-factory behavior, find missing-input and authority requests actionable, and identify the product responsible for each decision | Human review owner | Human | shipped instructions/commands/handoff/authority UX |
| SC-009 | Protected merge workflow | One authoritative candidate matrix; no routine duplicate full local run | Workflow owner | Pre-PR + CI | workflow/tier policy |
| SC-010 | Evidence invalidation engine | Unrelated docs/format/time/branch change invalidates zero factory claims | Evidence owner | Unit + Story | trace/invalidation schema/rules |
| SC-011 | Offline/process harness | Zero telemetry/upload/network/shell evaluation after acquisition | Security proof owner | CI | process runner, extension/adapter dependencies |

### Constitutional and public negative obligations

| Requirement | Implementation Boundary | Proof Obligation | Proof Owner | Verification Tier | Invalidated By |
|---|---|---|---|---|---|
| CON-I | Handoff/review/authority gates | Human meaning and authority cannot be self-approved | Human + kernel owners | Contract + Human | semantic/authority boundaries |
| CON-II | Public adapter dependency boundary | Replaceable public CLI adapter; independent bootstrap | Architecture owner | Pre-PR + CI | project/package graph/bootstrap scripts |
| CON-III | Schema/canonical resolution | Typed exact identities/closure; ambiguity explicit | Contracts/kernel owners | Contract + CI | schemas/canonicalization/resolution |
| CON-IV | Determinism/evidence claims | Only adapter-owned projection claimed deterministic; custom remains bounded | Evidence owner | Story + CI | claim metadata/translator/provider |
| CON-V | Ownership/publication | No consumer overwrite or partial trust | Publisher owners | Unit + CI | ownership/path/publication code |
| CON-VI | Provider composition | No new role/dynamic provider/ambient order | Composition owner | Contract + CI | provider interfaces/registry |
| CON-VII | Diagnostic truth/disclosure | Every recoverable path typed/safe; production trigger closure | Diagnostics owner | Contract + CI | results/catalog/disclosure/fallback |
| CON-VIII | Runtime/local safety | No authoring runtime coupling, secrets, undeclared network/process | Security owner | CI | packages/process/environment/disclosure |
| CON-IX | Vertical proof/documentation truth | Small complete public slice and honest limitations | Feature owner | CI + Human | feature scope/proof/docs |
| CON-V1 | Product-boundary guard | No planning/migration/runtime/global/dynamic/session expansion | Product owner | Analyze + CI | dependencies/public surface |
| CON-ENF | Enforcement/waiver guard | All gates named and non-waivable; no force/wildcard waiver | Kernel owner | Contract + Analyze | gate/waiver/result contracts |
| CON-WF | Spec Kit workflow integrity | Project layers preserved; no self-use; analyze before implementation | Workflow owner | Pre-PR + Analyze | Spec Kit integration/workflow files |
| NEG-001 | Bootstrap boundary | Repeat/conflict/unsafe/global/hook/forbidden-effect matrix | Workspace proof owner | Story + CI | init/path/invocation code |
| NEG-002 | Catalog/selection/restore | Remote/implicit/range/duplicate/stale/unavailable/zero-profile-factory matrix | Resolution proof owner | Story + CI | catalog/manifest/restore |
| NEG-003 | Applicability/defaults | Modes, unresolved required, disabled/non-code, incompatible inheritance, rebind | Hook proof owner | Story + CI | config/resolver/hooks |
| NEG-004 | Handoff/trace | Missing/unknown/conflicting/unreviewed/stale/changed/unrelated edit matrix | Trace proof owner | Story + CI | schemas/review/trace |
| NEG-005 | Provider/compatibility | Unsupported versions/profile and dynamic/private dependency attempts | Architecture proof owner | Contract + CI | compat/composition/package graph |
| NEG-006 | Authority/preflight | Missing/multiple/stale/revoked/widened/mismatch/hook construct matrix | Authority proof owner | Story + CI | proposal/decision/grant/preflight |
| NEG-007 | Filesystem/ownership | Escape/collision/drift/interruption/unowned cleanup matrix | Publisher proof owner | Unit + CI | path/publisher/manifest/lifecycle |
| NEG-008 | Process/disclosure | Opaque/secret/exception/malformed/timeout/stderr/shell/network matrix | Security proof owner | Contract + CI | parser/process/disclosure/fallback |
| NEG-009 | Lifecycle/upgrade | Incompatible/interrupted update, stale re-enable, drifted removal, upgrade | Release proof owner | CI matrix | extension lifecycle/package |
| NFR-001 | Adapter latency budget | Base doctor, config/handoff validation, and translation each complete in under two seconds for the reference fixture, excluding invoked factory/external build work | Adapter proof owner | Story + CI | adapter command/process/fixture/performance harness |

## Verification Strategy *(mandatory)*

| Tier | Purpose | Required Checks | Explicitly Excluded |
|---|---|---|---|
| Edit | Seconds-scale feedback for one changed boundary | Affected source build; focused unit/schema/diagnostic/golden test; canonical text/Spec Kit integrity when relevant | Restore, package assembly, consumer install, full suites, evidence regeneration, cross-platform |
| Story | Prove one independent user outcome | Relevant unit/contract tests and one focused acceptance scenario for that story; exact negative siblings | Unrelated stories, all package lifecycle, both-OS matrix, human review |
| Pre-PR | Catch local integration once | Locked restore only when dependency inputs changed; isolated release-equivalent builds for all affected projects; all unit/contract tests; one staged local extension + local CLI smoke; changed-file formatting; whitespace/integrity | Full acceptance/conformance/evidence, two clean E2E scenarios, full negative matrix, Windows/Linux matrix, human trials |
| CI | Authoritative exact merge-candidate proof | Ubuntu core job: locked restore, release build, all unit/contract/acceptance/conformance/evidence/package inspections; platform matrix: only package/process/path/install/update/disable/remove and both clean E2E scenarios on Windows/Linux; upload bounded evidence | Duplicate local full rerun and subjective human review |
| Human | Subjective intent/fitness | Three fresh package consumer journeys on green candidate; each reviewer locates the tool declaration, manifest, lock, adapter registration, handoff, generated inputs, product files, and evidence; distinguishes installation, availability, selection, activation, authority, custom/generated ownership, workspace defaults, feature overrides, and non-factory behavior; finds missing-input and authority requests actionable; and identifies the product responsible for each decision | Mechanizable regression already proven by CI |

**Evidence Reuse Rule**:

- Contract/schema proof depends on exact schema/model/projector bytes.
- Distribution/init/catalog/restore proof depends on CLI package layout, release
  binding, explicit provider registry, distribution descriptor, workspace
  schemas/services, and retained catalog/conformance resources.
- Extension install/lifecycle proof depends on extension archive bytes,
  `extension.yml`, command/hook/config files, adapter publish closure, and exact
  Spec Kit version.
- Translation proof depends on handoff/review/trace schemas, translator,
  canonicalization, compatibility manifest, and fixture semantic/implementation
  bytes.
- Authority/E2E proof depends on preparation/decision/grant contracts, authority
  provider, adapter projection, Program Kit factory/provider, and scenario bytes.
- Human evidence depends only on user-visible commands/instructions, handoff and
  review shape, defaults/applicability behavior, authority interaction, produced
  layout, limitations, and claims.
- Unchanged declared inputs reuse evidence. Time, branch head, unrelated commit,
  prose outside traced blocks, formatting, and regenerated unrelated digests do
  not invalidate a claim.

**Acceptance Invalidation Rule**:

- Product behavior, public API/schema, security/disclosure, authority,
  ownership, compatibility, runtime semantics, or user-visible guided-flow
  changes invalidate the applicable human product acceptance.
- Proof-only/test/CI changes require fresh executable evidence; human review is
  repeated only if the accepted claim, limitation, or interaction changed.
- Documentation/format/metadata changes preserve product acceptance unless they
  alter a traced semantic block, shipped instruction, accepted evidence byte, or
  public claim.
- Final release provenance may bind the green accepted candidate to its final
  commit without representing that as renewed product validation.

## Project Structure

### Documentation (this feature)

```text
specs/003-speckit-adapter/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── adapter-extension.md
│   ├── diagnostics.md
│   ├── public-cli.md
│   └── schemas-and-artifacts.md
├── checklists/
│   └── requirements.md
├── reviews/                         # implementation/human evidence later
└── tasks.md                         # generated only after plan approval
```

### Source Code (repository root)

```text
src/
├── ProgramKit.Contracts/
│   ├── Distribution/                # binding/catalog typed contracts
│   ├── Workspace/                   # init/manifest/restore/lock contracts
│   ├── Preparation/                 # request/proposal contracts
│   ├── Authority/                   # decision/record request additions
│   ├── Operations/                  # evolve the single public result contract
│   └── Schemas/                     # new Program Kit JSON schemas
├── ProgramKit.Kernel/
│   ├── Distribution/                # immutable explicit distribution descriptor
│   ├── Workspace/                   # bootstrap, catalog, restore services
│   ├── Preparation/                 # effect-free prospective resolution
│   ├── Authority/                   # production repository record operation
│   └── Operations/                  # public operation orchestration/result projection
├── ProgramKit.Cli/
│   ├── Commands/                    # init/catalog/restore/prepare/authority dispatch
│   ├── Composition/                 # exact release/distribution/provider binding
│   ├── Parsing/                     # nested public grammar, no token echo
│   └── Resources/                   # packaged distribution/support evidence
├── ProgramKit.Providers.DotNet/     # existing provider; only manifest exposure if needed
└── ProgramKit.SpecKitAdapter/
    ├── Commands/                    # ten adapter operation coordinators
    ├── Configuration/               # repository config/applicability/defaults
    ├── Contracts/                   # adapter DTOs and binders
    ├── Diagnostics/                 # catalog, factory, disclosure, fallback
    ├── Handoff/                     # proposal/review/trace/staleness
    ├── Invocation/                  # exact local-tool child process boundary
    ├── Publication/                 # staged atomic adapter artifact set/cleanup
    ├── Resources/                   # compatibility/catalog/help resources
    ├── Schemas/                     # adapter JSON schemas
    └── Translation/                 # bounded .NET definition/request projection

extensions/
└── orbyss-program-kit-adapter/
    ├── extension.yml
    ├── README.md
    ├── commands/                    # namespaced AI-facing command instructions
    ├── config/
    │   └── orbyss-program-kit-adapter-config.template.yml # project config template
    └── package-manifest.json        # source package inputs; generated release binds bytes

tests/
├── ProgramKit.UnitTests/            # workspace/trace/translation/path/process mechanics
├── ProgramKit.ContractTests/        # schemas/catalogs/dependency/command/golden closure
├── ProgramKit.AcceptanceTests/      # public/package/E2E/lifecycle/negative/runtime proof
├── Fixtures/
│   └── SpecKitAdapter/              # two factory, non-factory, mixed, invalid fixtures
└── Shared/                          # isolated consumer/package harness additions

eng/
├── Pack-ProgramKitTool.ps1          # exact CLI package (existing, release updated)
├── Pack-SpecKitAdapter.ps1          # publish/stage/archive extension
├── Invoke-SpecKitAdapterSmoke.ps1   # single local pre-PR smoke
├── Invoke-SpecKitAdapterQuickstart.ps1 # authoritative consumer scenarios
├── Generate-DistributionEvidence.ps1   # expanded exact release evidence
└── Invoke-Verification.ps1          # existing tier implementation, extended

.github/workflows/vertical-slice.yml # core proof once + platform-sensitive matrix
ProgramKit.slnx                      # add adapter project
Directory.Build.targets             # preserve/extend dependency architecture guards
```

**Structure Decision**: Extend the existing Contracts → Kernel/Provider → CLI
architecture for orchestrator-neutral factory capabilities. Add exactly one new
source project for the independently packaged adapter because its public-only
dependency and extension lifecycle require a separately testable binary. Keep
Spec Kit packaging in a top-level `extensions/` source directory and generate
complete binary archives only under ignored `artifacts/` staging. Do not add an
adapter provider, plugin loader, general package manager, migration layer, or a
second test solution.

## Delivery Slices

1. **Public workspace foundation**: one current v2 result, release identity,
   distribution descriptor, init, manifest/catalog/restore, base lock, CLI/help,
   schema/diagnostic/negative proof.
2. **Public preparation and authority**: preparation proposal, live-state
   binding, repository authority recording, exact construct closure, public
   contract and package acceptance.
3. **Adapter core**: project boundary, compatibility/config, handoff/review/
   trace, translator, result/diagnostic/process/publisher, focused deterministic
   and adversarial proof.
4. **Spec Kit extension and non-factory flow**: archive, commands/hooks/config,
   base/feature doctor, applicability/defaults/disable/cleanup, local smoke.
5. **Complete consumer proof**: two clean factory scenarios, production
   authority path, documentation-only/mixed workspaces, runtime isolation,
   install/update/remove on Windows/Linux, efficient CI evidence.
6. **Human validation and closure**: three fresh guided journeys, limitations,
   named acceptance, final evidence/README/release provenance.

Each slice ends with its story-level proof only. Pre-PR runs once after slices
1–5 are locally complete; CI and human validation are final gates.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because | Removal/Revisit Trigger |
|---|---|---|---|
| Separate `ProgramKit.SpecKitAdapter` executable project | Replaceable consumer product must ship in extension and depend only on public contracts | Prompt-only or in-CLI adapter cannot prove deterministic external integration and would couple Program Kit to Spec Kit | Revisit only if a general public adapter host is separately designed and proven |
| Extension publish/staging archive | Published Spec Kit package must contain one closed cross-platform executable/schema/instruction set without checked-in binaries | Source-only dev install cannot prove the consumer distribution | Remove staging only if Spec Kit gains an equivalent reproducible native package builder |

No other architectural complexity is justified. In particular there is no
dynamic provider loader, marketplace, general graph, custom workflow, runtime
host, source generator, reflection discovery, or migration system.

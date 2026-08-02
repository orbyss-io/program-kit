---
description: "Outcome- and proof-oriented task list for the Program Kit Adapter for Spec Kit"
---

# Tasks: Program Kit Adapter for Spec Kit

**Input**: Design documents from `specs/003-speckit-adapter/`

**Prerequisites**: Approved `spec.md`; `plan.md`, `research.md`, `data-model.md`,
`quickstart.md`, and every contract under `contracts/`

**Proof rule**: Tests and other proof are mandatory for every public contract,
negative path, applicable constitutional MUST, and evidence-backed claim.

**Organization**: Work is grouped by independently testable user story. Focused
edit/story proof runs while building. The complete slow assurance gate remains
at protected CI and human validation.

## Task Format

`- [ ] T### [P?] [US?] Outcome | Refs: ... | Proof: ... | Tier: ... | Done: ...`

- **[P]** means no incomplete dependency and no overlapping file ownership.
- **[US]** maps the task to an independently testable user story.
- **Refs** names the requirements, success criteria, negative group, or
  constitutional obligation served.
- **Proof** names the executable check, evidence, or human review.
- **Tier** is `edit`, `story`, `pre-pr`, `ci`, or `human`.
- **Done** states the observable completion condition.

## Phase 1: Setup

**Purpose**: Establish the separately packaged adapter and extension source
boundaries without changing public behavior.

- [X] T001 Scaffold the public-contract-only adapter project and add it to the solution/test graph in `src/ProgramKit.SpecKitAdapter/ProgramKit.SpecKitAdapter.csproj`, `src/ProgramKit.SpecKitAdapter/Program.cs`, `src/ProgramKit.SpecKitAdapter/packages.lock.json`, `ProgramKit.slnx`, `tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj`, `tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj`, and `tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj` | Refs: FR-009, FR-034, CON-II, CON-V1 | Proof: isolated locked restore/build plus project-reference inspection | Tier: edit | Done: the adapter builds as a framework-dependent `net10.0` executable, the test projects can exercise it, and its production project references no kernel, provider, session, test, eng, or private Spec Kit surface
- [X] T002 [P] Create the extension source-package skeleton in `extensions/orbyss-program-kit-adapter/extension.yml`, `extensions/orbyss-program-kit-adapter/README.md`, `extensions/orbyss-program-kit-adapter/config/orbyss-program-kit-adapter-config.template.yml`, and `extensions/orbyss-program-kit-adapter/package-manifest.json` | Refs: FR-008, FR-016, R009 | Proof: manifest/schema lint | Tier: edit | Done: the versioned extension declares its exact ID, version, Spec Kit requirement, config template/consumer-config ownership, and no checked-in binary
- [X] T003 [P] Create adapter fixture and consumer-harness roots in `tests/Fixtures/SpecKitAdapter/README.md` and `tests/Shared/SpecKitAdapterTestWorkspace.cs` | Refs: FR-032, SC-001, CON-IX | Proof: test-project build | Tier: edit | Done: tests can create isolated clean consumers without copying repository bootstrap, selections, handoffs, requests, or products
- [X] T004 Bind the planned Program Kit and adapter release identities in `src/ProgramKit.Cli/ProgramKit.Cli.csproj`, `src/ProgramKit.Cli/Composition/CliReleaseIdentityProvider.cs`, `src/ProgramKit.Kernel/Operations/ProgramKitKernel.cs`, `tests/Shared/SessionIntegrationFixture.cs`, current-release package/session tests under `tests/ProgramKit.ContractTests/` and `tests/ProgramKit.AcceptanceTests/`, and `extensions/orbyss-program-kit-adapter/package-manifest.json` | Refs: FR-031, R001 | Proof: focused release-identity contract plus repository search distinguishing current bindings from historical Feature 002 evidence | Tier: edit | Done: every current executable/test binding uses Program Kit `1.0.0-alpha.2`, the adapter is `0.1.0`, current contracts use their planned identities, and immutable Feature 002 evidence continues to truthfully record its historical `alpha.1` candidate
- [X] T005 Add adapter packaging entry points in `eng/Pack-SpecKitAdapter.ps1` and `eng/Invoke-SpecKitAdapterSmoke.ps1` | Refs: FR-008, FR-034, SC-005 | Proof: scripts parse and produce only ignored staging output | Tier: edit | Done: a complete extension can later be staged and smoke-tested without installing it into this repository

---

## Phase 2: Foundational Boundaries

**Purpose**: Close the shared public contracts, adapter result/diagnostic
surface, dependency boundary, and safe process/publication seams required by all
stories.

- [X] T006 [P] Define failing public schema/model closure tests for distribution, workspace, preparation, authority recording, and the one current operation-result contract in `tests/ProgramKit.ContractTests/AdapterPublicContractTests.cs` and `tests/ProgramKit.ContractTests/SchemaClosureTests.cs` | Refs: FR-005, FR-022, FR-023, FR-026, CON-III, CON-VII | Proof: focused contract test reaches every public schema through production registry | Tier: story | Done: tests reject open properties, unknown enums, missing exact bindings, and any parallel legacy result surface
- [X] T007 Implement distribution/workspace/preparation/authority DTOs and closed schemas while evolving `src/ProgramKit.Contracts/Operations/OperationResult.cs` and `src/ProgramKit.Contracts/Schemas/operation-result.schema.json` as the single current result contract | Refs: FR-005, FR-022, FR-023, FR-026, R003 | Proof: T006 | Tier: edit | Done: all public documents bind exact identities and every command uses one current v2 result model without a parallel v1 type or path
- [X] T008 [P] Define failing adapter schema, compatibility, result, and canonicalization closure tests in `tests/ProgramKit.ContractTests/SpecKitAdapterContractTests.cs` | Refs: FR-017, FR-021, FR-026, FR-031, FR-036, CON-III | Proof: focused adapter contract test | Tier: story | Done: every adapter resource is closed, embedded, reachable, exact-versioned, and has deterministic canonical bytes
- [X] T009 Implement adapter contracts and embedded resources in `src/ProgramKit.SpecKitAdapter/Contracts/`, `src/ProgramKit.SpecKitAdapter/Schemas/`, and `src/ProgramKit.SpecKitAdapter/Resources/compatibility.json` | Refs: FR-017, FR-021, FR-026, FR-031, FR-036, R008 | Proof: T008 | Tier: edit | Done: config, handoff, review, request, result, compatibility, generated-manifest, and diagnostic-catalog documents bind the planned models exactly
- [X] T010 [P] Define failing adapter diagnostic aggregation, production-trigger, and safe-fallback tests in `tests/ProgramKit.ContractTests/SpecKitAdapterDiagnosticTests.cs` | Refs: FR-027, FR-029, NEG-008, CON-VII | Proof: focused contract test | Tier: story | Done: all 12 public adapter IDs have exact definitions and real production-boundary trigger expectations
- [X] T011 Implement typed adapter diagnostics, disposition aggregation, disclosure classification, and independent fallback in `src/ProgramKit.SpecKitAdapter/Diagnostics/` and `src/ProgramKit.SpecKitAdapter/Resources/diagnostic-catalog.json` | Refs: FR-027, FR-029, R013, CON-VII | Proof: T010 | Tier: edit | Done: no automation parses prose and no unsafe unknown value reaches an ordinary channel
- [X] T012 [P] Define failing dependency-architecture and package-closure tests in `tests/ProgramKit.ContractTests/SpecKitAdapterArchitectureTests.cs` and `tests/ProgramKit.ContractTests/ProviderNeutralityArchitectureTests.cs` | Refs: FR-009, FR-034, FR-035, NEG-005, CON-II, CON-VI, CON-V1 | Proof: project/assets/archive dependency inspection | Tier: story | Done: tests reject unsupported exact compatibility, private/kernel/provider/session/test/eng/Spec Kit implementation coupling, and dynamic provider loading
- [X] T013 Enforce the adapter and provider composition boundaries in `Directory.Build.targets`, `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs`, and `src/ProgramKit.Kernel/Operations/ProviderRegistry.cs` | Refs: FR-009, FR-034, FR-035, R008, CON-II, CON-VI | Proof: T012 | Tier: edit | Done: only exact compiled first-party providers are registered and the adapter remains an external public-CLI consumer
- [X] T014 [P] Define hostile path, argument-vector process, timeout, canonical-write, and interrupted-publication unit tests in `tests/ProgramKit.UnitTests/SpecKitAdapterBoundaryTests.cs` | Refs: FR-028, FR-029, FR-037, NEG-007, NEG-008, CON-V, CON-VIII | Proof: focused unit test | Tier: story | Done: tests cover traversal/reparse/case collision, shell-shaped values, bounded output, cancellation, drift, and atomic refusal
- [X] T015 Implement adapter logical paths, exact child-process runner, canonical restricted-YAML binding, staging publisher, journal, and ownership manifest primitives in `src/ProgramKit.SpecKitAdapter/Invocation/`, `src/ProgramKit.SpecKitAdapter/Publication/`, and `src/ProgramKit.SpecKitAdapter/Contracts/RestrictedYaml.cs` | Refs: FR-028, FR-029, FR-037, R012, CON-V, CON-VIII | Proof: T014 | Tier: edit | Done: all adapter effects use safe logical paths, argument arrays with shell disabled, bounded classified output, and complete atomic owned sets
- [X] T016 [P] Define nested-command parser and single-current-result rendering tests in `tests/ProgramKit.ContractTests/AdapterCliContractTests.cs` | Refs: FR-001, FR-026, NEG-001, NEG-008 | Proof: black-box and parser contract tests | Tier: story | Done: all five new commands, duplicate/missing options, opaque tokens, exit codes, stdout/stderr rules, and absence of a parallel legacy result path are exact
- [X] T017 Add the five new public command identities, nested grammar, dispatch seams, help text, and shared renderer in `src/ProgramKit.Cli/Parsing/CliInvocation.cs`, `src/ProgramKit.Cli/Parsing/CliParser.cs`, `src/ProgramKit.Cli/Commands/CommandDispatcher.cs`, `src/ProgramKit.Cli/Commands/HelpCommand.cs`, and `src/ProgramKit.Cli/Rendering/ResultRenderer.cs` | Refs: FR-001, FR-026, R003, R004 | Proof: T016 | Tier: edit | Done: every command reaches typed handlers and one `OperationResult` factory/projector/renderer path

**Checkpoint**: Public and adapter contracts, exact composition, safe execution,
ownership, and proof seams are closed. User-story implementation may proceed.

---

## Phase 3: User Story 1 - Initialize an exact consumer workspace (Priority: P1)

**Goal**: Install one exact local Program Kit distribution, initialize neutral
state, inspect availability, create a base lock, install the extension, and run
base health checking with zero profile selection or factory authority.

**Independent Test**: From a clean consumer, complete local acquisition, init,
base restore, catalog list, extension installation, and base doctor; repeat init
and exercise unsafe/conflicting/global-shadow cases.

### Proof for User Story 1

- [X] T018 [P] [US1] Add public init/catalog/restore contract and state-separation tests in `tests/ProgramKit.ContractTests/WorkspaceBootstrapContractTests.cs` | Refs: FR-001 through FR-007, CON-III | Proof: focused contract suite | Tier: story | Done: exact requests/results distinguish installed, available, selected, activated, and authorized without implication
- [X] T019 [P] [US1] Add bootstrap/catalog/restore negative tests in `tests/ProgramKit.AcceptanceTests/WorkspaceBootstrapNegativeAcceptanceTests.cs` | Refs: FR-001 through FR-006, NEG-001, NEG-002 | Proof: public packaged CLI attempts | Tier: story | Done: repeat, conflict, drift, unsafe/colliding/reparse/global shadow, range, implicit choice, stale catalog, and zero-profile factory paths have exact no-effect results

### Implementation for User Story 1

- [X] T020 [US1] Implement immutable distribution binding, descriptor, and exact packaged catalog in `src/ProgramKit.Kernel/Distribution/DistributionDescriptor.cs`, `src/ProgramKit.Kernel/Distribution/DistributionCatalogService.cs`, and `src/ProgramKit.Cli/Resources/distribution-catalog.json` | Refs: FR-001, FR-004, FR-007, FR-031, FR-035 | Proof: T018 | Tier: edit | Done: the invoked package exposes only its exact offline provider/profile/contracts/support/evidence inventory
- [X] T021 [US1] Implement neutral idempotent atomic bootstrap in `src/ProgramKit.Kernel/Workspace/WorkspaceInitializationService.cs` and `src/ProgramKit.Cli/Commands/InitCommand.cs` | Refs: FR-002, FR-003, NEG-001, CON-V | Proof: T018, T019 | Tier: edit | Done: absent neutral files are seeded with zero selections and explicit bounded invocation evidence; reruns are unchanged and conflicts publish nothing
- [X] T022 [US1] Implement manifest binding and exact base/factory resolution in `src/ProgramKit.Kernel/Workspace/WorkspaceManifestBinder.cs`, `src/ProgramKit.Kernel/Workspace/WorkspaceRestoreService.cs`, and `src/ProgramKit.Cli/Commands/RestoreCommand.cs` | Refs: FR-005, FR-006, FR-007, NEG-002 | Proof: T018, T019 | Tier: edit | Done: exact selections/default resolve to reviewable locks and only declared semantic closure inputs invalidate them
- [X] T023 [US1] Implement the read-only catalog command in `src/ProgramKit.Cli/Commands/CatalogCommand.cs` | Refs: FR-004, FR-007 | Proof: T018, T019 | Tier: edit | Done: catalog JSON is exact and the operation performs zero writes, acquisition, selection, restore, activation, authority, or network
- [X] T024 [US1] Implement adapter base configuration and doctor in `src/ProgramKit.SpecKitAdapter/Configuration/AdapterConfigResolver.cs`, `src/ProgramKit.SpecKitAdapter/Commands/DoctorCommand.cs`, and `src/ProgramKit.SpecKitAdapter/Program.cs` | Refs: FR-010, FR-011, FR-012 | Proof: focused adapter command test in T025 | Tier: edit | Done: base doctor validates exact CLI/manifest/base-lock/extension/config with zero selected profiles and reports all five states distinctly
- [X] T025 [US1] Add clean package-only bootstrap and base-doctor acceptance in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterBootstrapAcceptanceTests.cs` and `tests/Shared/SpecKitAdapterTestWorkspace.cs` | Refs: US1, FR-001 through FR-012, SC-005, NFR-001, CON-IX | Proof: staged tool plus extension in a clean consumer with bounded stopwatch evidence | Tier: story | Done: the complete independent story passes without repository-generated semantic preseed or global fallback and base doctor completes in under two seconds for the reference fixture
- [X] T026 [US1] Complete the installable extension archive and base-doctor instruction in `extensions/orbyss-program-kit-adapter/extension.yml`, `extensions/orbyss-program-kit-adapter/commands/doctor.md`, and `eng/Pack-SpecKitAdapter.ps1` | Refs: FR-008, FR-010, SC-005 | Proof: T025 plus archive inspection | Tier: story | Done: `specify extension add orbyss-program-kit-adapter` installs exact commands/executable without modifying managed core
- [X] T027 [US1] Run the focused User Story 1 verification set through `eng/Invoke-Verification.ps1` | Refs: US1, FR-001 through FR-012 | Proof: bootstrap contract and acceptance filters | Tier: story | Done: all US1 positive and negative proof passes without running unrelated full suites

**Checkpoint**: User Story 1 is independently installable, understandable, and
safe with zero selected profiles.

---

## Phase 4: User Story 2 - Turn approved planning into an authorizable proposal (Priority: P1)

**Goal**: Create and review a bounded feature handoff, deterministically
translate approved meaning into public factory inputs, and obtain an exact
effect-free preparation/explanation.

**Independent Test**: From approved Spec Kit artifacts and one exact selected
profile, create/review/validate a handoff, translate it five times under
meaning-preserving permutations, then prepare/explain with zero product effect.

### Proof for User Story 2

- [X] T028 [P] [US2] Add complete valid and invalid handoff/config/review fixtures in `tests/Fixtures/SpecKitAdapter/Reference.Status/` and `tests/Fixtures/SpecKitAdapter/Invalid/Handoff/` | Refs: FR-017 through FR-021, NEG-003, NEG-004 | Proof: fixture schema/canonical validation | Tier: story | Done: fixtures cover every required field, ownership class, trace kind, unresolved list, review state, ordering permutation, and ambiguity
- [X] T029 [P] [US2] Add config, applicability, handoff, review, and field-level trace contract tests in `tests/ProgramKit.ContractTests/SpecKitAdapterHandoffContractTests.cs` | Refs: FR-011 through FR-020, NEG-003, NEG-004, CON-I | Proof: focused contract suite | Tier: story | Done: heuristic sources are rejected, exact source blocks resolve, handoff edits stale review, and unrelated prose does not stale traced meaning
- [X] T030 [P] [US2] Add deterministic translation golden tests in `tests/ProgramKit.ContractTests/SpecKitAdapterTranslationContractTests.cs` | Refs: FR-021, FR-036, SC-003, CON-IV | Proof: five repeats and permutations per handoff | Tier: story | Done: all adapter-owned definitions and requests are byte-identical and every identity comes from compatibility/preparation authority
- [X] T031 [P] [US2] Add effect-free preparation public-boundary tests in `tests/ProgramKit.ContractTests/PreparationOperationContractTests.cs` | Refs: FR-022, FR-025, CON-I, CON-III | Proof: public kernel and CLI requests | Tier: story | Done: exact proposal, request/closure/live-state bindings, explanation, and authority requirements return with zero candidate/live publication

### Implementation for User Story 2

- [X] T032 [US2] Implement exact project-config, applicability, and effective-selection resolution in `src/ProgramKit.SpecKitAdapter/Configuration/AdapterConfigResolver.cs`, `src/ProgramKit.SpecKitAdapter/Configuration/ApplicabilityResolver.cs`, and `src/ProgramKit.SpecKitAdapter/Configuration/SelectionResolver.cs` | Refs: FR-011, FR-012, FR-013, FR-014, NEG-003 | Proof: T029 | Tier: edit | Done: mode resolves feature override then project defaultMode then off; applicable profile resolves feature selection override then current Program Kit lock default; no second/ambient profile default is admitted
- [X] T033 [US2] Implement handoff binding/proposal and heuristic-source exclusion in `src/ProgramKit.SpecKitAdapter/Handoff/HandoffBinder.cs` and `src/ProgramKit.SpecKitAdapter/Handoff/HandoffProposalBuilder.cs` | Refs: FR-017, FR-018, CON-I | Proof: T029 | Tier: edit | Done: an absent bounded handoff may be proposed but free prose/names/order/time/transcripts/LLM inference never become admitted meaning
- [X] T034 [US2] Implement named-block trace and review validation in `src/ProgramKit.SpecKitAdapter/Handoff/TraceResolver.cs` and `src/ProgramKit.SpecKitAdapter/Handoff/HandoffReviewValidator.cs` | Refs: FR-019, FR-020, SC-010, NEG-004 | Proof: T029 | Tier: edit | Done: review binds exact handoff and field dependencies invalidate only on changed approved values or implementation bytes
- [X] T035 [US2] Implement the bounded .NET definition/bundle/request translator in `src/ProgramKit.SpecKitAdapter/Translation/DotNetHandoffTranslator.cs`, `src/ProgramKit.SpecKitAdapter/Translation/TranslationIdentityResolver.cs`, and `src/ProgramKit.SpecKitAdapter/Translation/CanonicalArtifactWriter.cs` | Refs: FR-021, FR-036, CON-IV | Proof: T030 | Tier: edit | Done: one .NET semantic definition, one bundle, implementation references, selection/trace, and permitted request sequence are canonical and complete
- [X] T036 [US2] Implement effect-free preparation in `src/ProgramKit.Kernel/Preparation/PreparationService.cs`, `src/ProgramKit.Kernel/Operations/PrepareOperation.cs`, and `src/ProgramKit.Cli/Commands/PrepareCommand.cs` | Refs: FR-022, FR-025 | Proof: T031 | Tier: edit | Done: public preparation resolves current prospective closure/live state and returns an ungranted proposal without publication
- [X] T037 [US2] Implement adapter handoff/validate/prepare/explain orchestration in `src/ProgramKit.SpecKitAdapter/Commands/HandoffCommand.cs`, `src/ProgramKit.SpecKitAdapter/Commands/ValidateCommand.cs`, `src/ProgramKit.SpecKitAdapter/Commands/PrepareCommand.cs`, and `src/ProgramKit.SpecKitAdapter/Commands/ExplainCommand.cs` | Refs: FR-017 through FR-022, FR-026 | Proof: T029 through T031 | Tier: edit | Done: reviewed exact meaning reaches only public CLI commands and adapter results preserve the exact Program Kit document
- [X] T038 [US2] Implement feature-local staged artifact publication in `src/ProgramKit.SpecKitAdapter/Publication/AdapterArtifactPublisher.cs` and `src/ProgramKit.SpecKitAdapter/Publication/AdapterGeneratedManifestBuilder.cs` | Refs: FR-028, FR-036, CON-V | Proof: T014 plus T039 | Tier: edit | Done: the conditional generated closure publishes atomically without overwriting the consumer handoff/review or Program Kit-owned files
- [X] T039 [US2] Add package-only handoff-to-preparation acceptance in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterPreparationAcceptanceTests.cs` | Refs: US2, FR-017 through FR-022, SC-003, NFR-001, NEG-004 | Proof: staged package consumer story with bounded stopwatch evidence | Tier: story | Done: Reference Status config/handoff validation and translation each complete in under two seconds, translate repeatedly, and prepare/explain exactly with zero construction authority or product publication
- [X] T040 [US2] Run the focused User Story 2 verification set through `eng/Invoke-Verification.ps1` | Refs: US2, FR-011 through FR-022 | Proof: handoff, translation, preparation contract and acceptance filters | Tier: story | Done: all US2 positive, staleness, ambiguity, and determinism proof passes without unrelated suites

**Checkpoint**: User Story 2 creates one exact reviewed, deterministic,
authorizable proposal but cannot construct.

---

## Phase 5: User Story 3 - Authorize and construct without authority confusion (Priority: P1)

**Goal**: Record a separate exact human decision through the production
repository authority provider, then explicitly construct/evaluate with one
caller-supplied current grant.

**Independent Test**: Record one production authority decision, construct and
evaluate the Reference Status product, then repeat the construction boundary
with every absent/stale/ambiguous/revoked/widened/mismatched grant case.

### Proof for User Story 3

- [X] T041 [P] [US3] Add authority-decision/recording and exact grant/revocation contract tests in `tests/ProgramKit.ContractTests/RepositoryAuthorityRecordingContractTests.cs` | Refs: FR-023, FR-024, FR-025, NEG-006, CON-I, CON-ENF | Proof: public operation production-boundary test | Tier: story | Done: denial, widening, ambiguity, stale live state, invalid validity, and partial record attempts are refused
- [X] T042 [P] [US3] Add adapter construct authority-guard tests in `tests/ProgramKit.ContractTests/SpecKitAdapterAuthorityGuardTests.cs` | Refs: FR-024, FR-025, NEG-006 | Proof: focused adapter command test | Tier: story | Done: adapter cannot issue/populate/select/broaden grants or reinterpret review/hook events as authority

### Implementation for User Story 3

- [X] T043 [US3] Implement repository authority recording in `src/ProgramKit.Kernel/Authority/RepositoryAuthorityRecordOperation.cs`, `src/ProgramKit.Kernel/Authority/RepositoryAuthorityProvider.cs`, and `src/ProgramKit.Cli/Commands/AuthorityRecordCommand.cs` | Refs: FR-023, NEG-006, CON-I, CON-ENF | Proof: T041 | Tier: edit | Done: exact proposal plus separate human decision atomically creates the bounded grant/revocation pair or no authority files
- [X] T044 [US3] Enforce preparation/explanation/artifact-review/grant/live-state preflight in `src/ProgramKit.Kernel/Authority/RepositoryAuthorityProvider.cs`, `src/ProgramKit.Kernel/Authority/RepositoryAuthorityRecordOperation.cs`, and `src/ProgramKit.Kernel/Operations/ConstructOperation.cs` | Refs: FR-025, NEG-006, CON-ENF | Proof: T041, T042 | Tier: edit | Done: every named precondition is current and exact before any construction effect
- [X] T045 [US3] Implement explicit adapter construct/evaluate commands in `src/ProgramKit.SpecKitAdapter/Commands/ConstructCommand.cs` and `src/ProgramKit.SpecKitAdapter/Commands/EvaluateCommand.cs` | Refs: FR-024 through FR-026 | Proof: T042 | Tier: edit | Done: construct requires exactly one caller-supplied grant and evaluate preserves the unmodified public result
- [X] T046 [US3] Add production-authority package-only construct/evaluate acceptance in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterConstructionAcceptanceTests.cs` | Refs: US3, FR-023 through FR-026, FR-032, SC-001 | Proof: staged package clean consumer using repository authority provider | Tier: story | Done: authorized Reference Status construction/evaluation succeeds and all grant-negative siblings perform zero construction
- [X] T047 [US3] Add generated-product execution and runtime-isolation proof in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterProductRuntimeAcceptanceTests.cs` | Refs: FR-030, SC-007, CON-II, CON-VIII | Proof: build, test, start, demonstrated HTTP behavior, package/runtime graph inspection | Tier: story | Done: the product works and has zero runtime references to Program Kit, Spec Kit, adapter, AI tooling, prompts, transcripts, or authoring configuration
- [X] T048 [US3] Run the focused User Story 3 verification set through `eng/Invoke-Verification.ps1` | Refs: US3, FR-023 through FR-030 | Proof: authority, construction, evaluation, and runtime acceptance filters | Tier: story | Done: 7 unit, 29 contract, and 2 package/runtime acceptance checks pass in 74 seconds with zero build warnings or errors; unrelated lifecycle/platform suites remain deferred

**Checkpoint**: User Story 3 completes the first full factory journey while
authority remains external, explicit, exact, and revocable.

---

## Phase 6: User Story 4 - Apply workspace defaults safely (Priority: P1)

**Goal**: Make off/assist/required policy and exact defaults convenient without
allowing non-factory work, inherited assist, or later default changes to create
effects or rewrite reviewed meaning.

**Independent Test**: Exercise every mode, overrides, a documentation-only
feature, a mixed workspace, default drift, and disable/re-enable while recording
zero process/artifact effects for inactive features.

### Proof for User Story 4

- [X] T049 [P] [US4] Add mode/default/applicability/inheritance tests in `tests/ProgramKit.UnitTests/SpecKitAdapterConfigurationTests.cs` | Refs: FR-011 through FR-015, NEG-003 | Proof: focused unit tests | Tier: story | Done: feature/project mode precedence, explicit/locked selection precedence, no sole-choice or adapter-profile fallback, unresolved-required, inherited-assist, disable, and exact pinned-default drift are covered
- [X] T050 [P] [US4] Add documentation-only and mixed-workspace acceptance in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterApplicabilityAcceptanceTests.cs` | Refs: US4, FR-012 through FR-015, SC-002, SC-006 | Proof: hook harness with child-process recorder and filesystem snapshot | Tier: story | Done: documentation-only and inherited-assist hooks launch zero Program Kit processes, write zero bytes, preserve adjacent factory state, and only unresolved required requests input

### Implementation for User Story 4

- [X] T051 [US4] Implement activate/disable commands and pinned-default divergence behavior in `src/ProgramKit.SpecKitAdapter/Commands/ActivateCommand.cs`, `src/ProgramKit.SpecKitAdapter/Commands/DisableCommand.cs`, and `src/ProgramKit.SpecKitAdapter/Configuration/SelectionResolver.cs` | Refs: FR-011 through FR-014 | Proof: T049 | Tier: edit | Done: effect-free proposals carry exact explicit/inherited selections; reviewed handoffs retain the complete pinned lock entry and later defaults only report divergence for explicit re-handoff
- [X] T052 [US4] Publish all ten AI-facing command instructions and exact project-configuration guidance in `extensions/orbyss-program-kit-adapter/commands/` and `extensions/orbyss-program-kit-adapter/config/orbyss-program-kit-adapter-config.template.yml` | Refs: FR-008, FR-011 through FR-015, FR-018 | Proof: instruction contract/lint test in T054 | Tier: edit | Done: all commands bind the exact project config, reject ambient semantic layers, distinguish proposals from deterministic validation, and forbid automatic initialization, authority, grant selection, or construction
- [X] T053 [US4] Register conditional after-plan/after-tasks/before-implement/after-implement hooks in `extensions/orbyss-program-kit-adapter/extension.yml` | Refs: FR-012, FR-015, CON-WF | Proof: hook manifest contract test in T054 | Tier: edit | Done: the exact handoff/validate/prepare hooks resolve applicability first; inactive and inherited-assist work is nonblocking while unresolved required requests input at the configured gate
- [X] T054 [US4] Add extension command/hook contract tests in `tests/ProgramKit.ContractTests/SpecKitAdapterExtensionContractTests.cs` | Refs: FR-008, FR-012, FR-015, FR-024, CON-WF | Proof: installed extension manifest/instruction inspection | Tier: story | Done: exact command/hook registrations, config binding, ambient-layer rejection, and non-initializing/non-authorizing/non-constructing hook instructions are enforced
- [X] T055 [US4] Add default-drift and disable/re-enable preservation acceptance in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterDefaultLifecycleAcceptanceTests.cs` | Refs: FR-014 through FR-016, SC-006, NEG-003, NEG-009 | Proof: packaged mixed-workspace lifecycle | Tier: story | Done: default drift reports re-handoff without rebinding, and disable/proposed re-enable delete, rewrite, invoke, or silently resume nothing
- [X] T056 [US4] Run the focused User Story 4 verification set through `eng/Invoke-Verification.ps1` | Refs: US4, FR-011 through FR-016 | Proof: configuration, hook, applicability, and preservation filters | Tier: story | Done: 3 unit, 2 contract, and 2 acceptance tests pass in 10 seconds with zero build warnings/errors; unselected acceptance and platform proof remain CI-owned

**Checkpoint**: User Story 4 makes repository defaults useful while inactive
and existing reviewed work remain harmless and pinned.

---

## Phase 7: User Story 5 - Diagnose and recover without unnecessary proof (Priority: P2)

**Goal**: Provide disclosure-safe typed recovery and invalidate only claims
whose declared semantic, implementation, compatibility, or evidence inputs
changed.

**Independent Test**: Run the complete diagnostic/adversarial matrix and prove
that unrelated prose/format/time/branch changes invalidate zero factory claims
while traced or implementation changes stale only their dependents.

### Proof for User Story 5

- [X] T057 [P] [US5] Add named-block trace and evidence-invalidation tests in `tests/ProgramKit.UnitTests/SpecKitAdapterEvidenceInvalidationTests.cs` | Refs: FR-020, FR-033, SC-010, NEG-004, CON-IV | Proof: focused unit matrix | Tier: story | Done: unrelated prose and whitespace-normalized traced blocks reuse every claim; semantic, implementation, compatibility, review, and retained-evidence changes invalidate only exact downstream sets
- [X] T058 [P] [US5] Add disclosure/process/fallback adversarial tests in `tests/ProgramKit.ContractTests/SpecKitAdapterDisclosureContractTests.cs` | Refs: FR-027, FR-029, FR-037, SC-004, SC-011, NEG-008 | Proof: black-box adapter with opaque/secret/exception/stderr/malformed/timeout/shell/network fixtures | Tier: story | Done: authoritative valid results survive unchanged; malformed, truncated, timed-out, exceptional, exit-mismatched, shell-shaped, secret, path, stderr, and network-shaped cases fail closed without disclosure or launch
- [X] T059 [P] [US5] Add publication interruption, drift, collision, and recovery tests in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterPublicationRecoveryAcceptanceTests.cs` | Refs: FR-028, SC-004, NEG-007, CON-V | Proof: hostile filesystem and interruption harness | Tier: story | Done: trust marker publishes last, interruption restores the prior set, recovery preflights the whole transaction, and drift/collision/foreign staging is preserved and refused

### Implementation for User Story 5

- [X] T060 [US5] Implement exact output/claim invalidation sets in `src/ProgramKit.SpecKitAdapter/Handoff/TraceInvalidationEngine.cs` and `src/ProgramKit.SpecKitAdapter/Publication/AdapterGeneratedManifestBuilder.cs` | Refs: FR-020, FR-033, SC-010, R011 | Proof: T057 | Tier: edit | Done: named blocks normalize whitespace and each manifest output/claim names only its trace, implementation, compatibility, review, or retained-evidence dependencies
- [X] T061 [US5] Complete disclosure-safe external failure and result aggregation in `src/ProgramKit.SpecKitAdapter/Invocation/ProgramKitProcessClient.cs`, `src/ProgramKit.SpecKitAdapter/Diagnostics/AdapterResultFactory.cs`, and `src/ProgramKit.SpecKitAdapter/Diagnostics/DisclosureFilter.cs` | Refs: FR-026, FR-027, FR-029, FR-037, NEG-008 | Proof: T058 | Tier: edit | Done: valid Program Kit results remain authoritative; the exact catalog-backed typed fallback reports honest furthest stage/effect/disposition while withholding stdout, stderr, exceptions, secrets, paths, and commands
- [X] T062 [US5] Complete staged publication recovery and explicit ownership refusal in `src/ProgramKit.SpecKitAdapter/Publication/AdapterArtifactPublisher.cs` and `src/ProgramKit.SpecKitAdapter/Publication/AdapterPublicationRecovery.cs` | Refs: FR-028, NEG-007, CON-V | Proof: T059 | Tier: edit | Done: a canonical staging journal makes interrupted output untrusted and recoverable, the manifest trust marker publishes last, and whole-recovery preflight prevents partial rollback or unproven overwrite
- [X] T063 [US5] Implement the edit/story/pre-PR/CI/human verification modes and declared invalidation inputs in `eng/Invoke-Verification.ps1` and `.github/workflows/vertical-slice.yml` | Refs: FR-033, SC-009, CON-WF | Proof: verification-mode contract test in T064 | Tier: story | Done: Edit/Story/PrePr remain bounded; protected CI runs the complete neutral proof once on Ubuntu and only platform-sensitive proof on Windows/Linux; Human performs no automated replay
- [X] T064 [US5] Add verification-tier and evidence-reuse contract tests in `tests/ProgramKit.ContractTests/VerificationTierContractTests.cs` | Refs: FR-033, SC-009, SC-010 | Proof: script/workflow static plus simulated changed-input assertions | Tier: story | Done: tier aliases/boundaries, protected CI ownership, filtered platform proof, one evidence generation, and absence of time/branch/head invalidation inputs are enforced
- [X] T065 [US5] Run the focused User Story 5 verification set through `eng/Invoke-Verification.ps1` | Refs: US5, FR-020, FR-026 through FR-029, FR-033, FR-037 | Proof: evidence, diagnostic, disclosure, process, and publication filters | Tier: story | Done: 2 unit, 8 contract, and 3 acceptance tests pass in 19 seconds with zero build warnings/errors; unrelated acceptance, evidence, and platform proof remain CI-owned

**Checkpoint**: User Story 5 reports exact safe recovery and reuses unaffected
evidence instead of triggering convergence churn.

---

## Phase 8: User Story 6 - Upgrade or remove without losing work (Priority: P2)

**Goal**: Update, disable, re-enable, remove, and explicitly clean the adapter
without taking ownership of consumer or Program Kit artifacts.

**Independent Test**: On packaged consumers, perform compatible and failed
updates, disable/re-enable, manifest-aware Spec Kit upgrade, removal, and exact
versus drifted cleanup while comparing ownership snapshots.

### Proof for User Story 6

- [ ] T066 [P] [US6] Add extension package lifecycle and ownership tests in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterLifecycleAcceptanceTests.cs` | Refs: FR-008, FR-016, SC-005, SC-006, NEG-009, CON-V | Proof: staged extension install/update/disable/re-enable/remove harness | Tier: story | Done: only unchanged extension-owned installation files change, failed update retains the prior selectable release, and `--keep-config` preserves the exact consumer-owned project configuration
- [ ] T067 [P] [US6] Add cleanup ownership tests in `tests/ProgramKit.UnitTests/SpecKitAdapterCleanupTests.cs` | Refs: FR-016, FR-028, NEG-007, NEG-009 | Proof: focused exact/drifted/differently-owned matrix | Tier: story | Done: only unchanged manifest-proven regenerable adapter candidates may be removed

### Implementation for User Story 6

- [ ] T068 [US6] Implement explicit cleanup in `src/ProgramKit.SpecKitAdapter/Commands/CleanupCommand.cs` and `src/ProgramKit.SpecKitAdapter/Publication/AdapterCleanupService.cs` | Refs: FR-016, FR-028, CON-V | Proof: T067 | Tier: edit | Done: cleanup preserves handoffs, reviews, Program Kit requests/results/state/products/evidence, consumer source, and unknown/drifted files
- [ ] T069 [US6] Complete versioned extension update/disable/re-enable/remove ownership declarations in `extensions/orbyss-program-kit-adapter/extension.yml`, `extensions/orbyss-program-kit-adapter/package-manifest.json`, and `eng/Pack-SpecKitAdapter.ps1` | Refs: FR-008, FR-016, NEG-009 | Proof: T066 | Tier: edit | Done: installation ownership distinguishes template from consumer config, removal uses supported `--keep-config`, failed staging is non-activating, and re-enable revalidates before use
- [ ] T070 [US6] Add manifest-aware Spec Kit upgrade acceptance to `tests/ProgramKit.AcceptanceTests/SpecKitAdapterLifecycleAcceptanceTests.cs` using `eng/Invoke-SpecKitUpgrade.ps1` | Refs: FR-016, SC-005, NEG-009, CON-WF | Proof: clean compatible upgrade without force | Tier: story | Done: registration and project-owned layers remain exact across the supported upgrade path
- [ ] T071 [US6] Add platform-sensitive extension lifecycle jobs to `.github/workflows/vertical-slice.yml` | Refs: FR-008, FR-016, SC-005, SC-006 | Proof: Windows/Linux packaged matrix definition | Tier: ci | Done: only package/process/path/install/update/disable/remove/upgrade/clean-E2E checks are duplicated across operating systems
- [ ] T072 [US6] Run the focused User Story 6 verification set through `eng/Invoke-Verification.ps1` | Refs: US6, FR-008, FR-016, FR-028 | Proof: cleanup and single-platform lifecycle filters | Tier: story | Done: all locally provable lifecycle/ownership outcomes pass without running the protected two-OS matrix

**Checkpoint**: User Story 6 makes the adapter optional and upgradable without
losing or silently resuming work.

---

## Phase 9: Cross-Cutting Completion

**Purpose**: Close the complete release claim once, then hand the exact candidate
to authoritative CI and human acceptance.

- [ ] T073 [P] Add a second semantically distinct clean factory fixture in `tests/Fixtures/SpecKitAdapter/Inventory.Health/` | Refs: FR-032, SC-001, CON-IX | Proof: schema/canonical fixture validation | Tier: story | Done: feature, contract, route, namespace, custom behavior, definitions, and requests are distinct from Reference Status
- [ ] T074 Complete the two clean natural-language-to-evaluate package journeys in `eng/Invoke-SpecKitAdapterQuickstart.ps1` and `tests/ProgramKit.AcceptanceTests/SpecKitAdapterQuickstartAcceptanceTests.cs` | Refs: FR-032, SC-001, SC-007, CON-IX | Proof: two separately initialized packaged consumers | Tier: ci | Done: neither journey is pre-seeded and both use explicit production authority, build, test, start, demonstrate behavior, and pass runtime isolation
- [ ] T075 Reconcile all nine negative groups into one executable matrix in `tests/ProgramKit.AcceptanceTests/SpecKitAdapterNegativeMatrixAcceptanceTests.cs` | Refs: FR-032, SC-004, NEG-001 through NEG-009, CON-VII | Proof: every retained case invokes its production boundary and asserts exact outcome/stage/effect/disposition/ID/safe expected-observed/evidence/no unauthorized effects | Tier: ci | Done: no diagnostic is proven only by catalog synthesis and no negative scenario is README-only
- [ ] T076 [P] Extend distribution/package evidence generation in `eng/GenerateDistributionEvidence.cs`, `eng/Generate-DistributionEvidence.ps1`, and `artifacts/evidence/` inputs | Refs: FR-031, FR-032, FR-035, CON-IV, CON-IX | Proof: generated evidence/schema/staleness contract tests | Tier: ci | Done: exact release, compatibility, public schema/catalog, provider support, adapter archive, dependency, and claim invalidation bindings are retained
- [ ] T077 [P] Add complete tool/extension package inspection in `tests/ProgramKit.ContractTests/SpecKitAdapterPackageClosureTests.cs` | Refs: FR-008, FR-009, FR-031, FR-034, FR-035, FR-037 | Proof: packed nupkg/archive contents, dependencies, executable, schemas, licenses, and forbidden-file inspection | Tier: ci | Done: the shipped sets are closed, exact, offline-capable after acquisition, and contain no private/self-hosting/dynamic-provider dependency
- [ ] T078 Update product guidance and honest limitations in `README.md`, `extensions/orbyss-program-kit-adapter/README.md`, and `specs/003-speckit-adapter/quickstart.md` | Refs: FR-031, FR-032, SC-008, CON-IX | Proof: documentation claim-to-evidence review | Tier: pre-pr | Done: install/selection/applicability/handoff/authority/ownership/lifecycle/limitations and deferred capabilities match the executable product exactly
- [ ] T079 Reconcile requirement, constitution, negative, and proof ownership against implementation in `specs/003-speckit-adapter/tasks.md` | Refs: FR-001 through FR-037, SC-001 through SC-011, CON-I through CON-WF, NEG-001 through NEG-009 | Proof: `$speckit-analyze` reports no CRITICAL/HIGH coverage or inconsistency finding | Tier: pre-pr | Done: every row has a production implementation and non-synthetic proof task with honest completion state
- [ ] T080 Run the repository pre-PR integration pass through `eng/Invoke-Verification.ps1` | Refs: FR-033, SC-009, CON-WF | Proof: `./eng/Invoke-Verification.ps1 -Mode PrePr` | Tier: pre-pr | Done: locked restore as applicable, release builds, unit/contract suites, staged local tool/extension smoke, formatting, and integrity pass without regenerating final CI evidence
- [ ] T081 Obtain the authoritative exact-candidate Ubuntu core and Windows/Linux platform-sensitive evidence from `.github/workflows/vertical-slice.yml` | Refs: FR-032, FR-033, SC-001 through SC-007, SC-009 through SC-011 | Proof: protected CI artifacts and checks | Tier: ci | Done: one exact candidate passes full core acceptance/conformance/evidence once and only the planned platform-sensitive subset on both operating systems
- [ ] T082 Record three fresh named human validation journeys in `specs/003-speckit-adapter/reviews/` | Refs: FR-032, SC-008, CON-I, CON-IX | Proof: shipped-instructions-only review records | Tier: human | Done: every reviewer locates all named artifacts; distinguishes five states, ownership, defaults, overrides, non-factory behavior, and responsible product; and acts on missing-input and authority requests without terminal coaching
- [ ] T083 Record final human feature acceptance and its exact invalidation scope in `specs/003-speckit-adapter/reviews/final-acceptance.md` | Refs: FR-032, SC-008, CON-I, CON-IX | Proof: explicit bounded human decision after T081 and T082 | Tier: human | Done: accepted claims, limitations, exact candidate, evidence set, and semantic invalidation triggers are recorded without inferring acceptance from automation

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 precedes Phase 2.
- Phase 2 blocks all user stories because it closes public contracts, adapter
  schemas, dependency boundaries, diagnostics, process safety, and publication.
- User Story 1 establishes the exact local distribution, manifest, lock, and
  installed adapter needed by User Stories 2–6.
- User Story 2 establishes reviewed translation and preparation needed by User
  Story 3. User Story 4 can proceed after User Story 1 and the Phase 2 config
  contracts, but must merge before cross-cutting consumer proof.
- User Story 5 hardens shared recovery/evidence after the P1 flows exist.
- User Story 6 uses the packaged extension from User Stories 1 and 4 and may
  proceed alongside late User Story 5 work where file ownership does not overlap.
- Phase 9 begins only after all six story checkpoints pass.

### Parallel opportunities

- Phase 1: T002 and T003 can proceed in parallel after T001 scope is known.
- Phase 2: proof tasks T006, T008, T010, T012, T014, and T016 own distinct test
  files and may proceed in parallel; each implementation follows its nearest
  proof.
- User Story 1: T018 and T019 are parallel proof authoring.
- User Story 2: T028–T031 are parallel fixture/contract/golden/preparation proof
  authoring before the dependent implementation sequence.
- User Story 3: T041 and T042 are parallel public-authority and adapter-guard
  proof authoring.
- User Story 4: T049 and T050 are parallel unit and acceptance proof authoring.
- User Story 5: T057–T059 are parallel evidence, disclosure, and publication
  proof authoring.
- User Story 6: T066 and T067 are parallel lifecycle and cleanup proof authoring.
- Phase 9: T073, T076, and T077 own separate fixture/evidence/package files.

### Independent story criteria

- **US1**: Clean local acquisition through base doctor with zero selected
  profiles; exact repeat and negative bootstrap/catalog/restore proof.
- **US2**: Reviewed handoff through deterministic translation and effect-free
  prepare/explain; no grant or product publication.
- **US3**: Production authority record through explicit construct/evaluate and
  working isolated product; all grant negatives perform no construction.
- **US4**: Every policy/default/override/non-factory/mixed/default-drift path;
  inactive work has zero child launches/artifacts and no silent rebind.
- **US5**: Exact typed safe diagnostics/recovery and field-level evidence reuse;
  unrelated edits invalidate zero factory claims.
- **US6**: Packaged update/disable/re-enable/remove/cleanup/upgrade preserves
  every differently owned file and failed update retains the working release.

## Implementation Strategy

1. Complete Setup and Foundational Boundaries with their focused proof.
2. Deliver User Story 1 as the smallest installable MVP.
3. Deliver User Stories 2 and 3 as the first complete governed factory journey.
4. Close workspace-default/non-factory behavior in User Story 4 before treating
   hooks as generally usable.
5. Harden evidence, diagnostics, disclosure, and recovery in User Story 5.
6. Close optional lifecycle behavior in User Story 6.
7. Run the pre-PR pass once after local implementation is complete. Protected CI
   owns the full core/platform evidence; human validation starts only on green.

Within each story, establish the nearest useful failing proof before its
implementation when practical. Do not mark a task complete through a synthetic
factory call, placeholder fixture, catalog-only trigger, or README-only negative
directory. If implementation reveals changed authority, broadened effect,
material ambiguity, or a missing dependency, return to specification/planning
rather than silently expanding the task.

## Resolution Semantics

- `[X]` means the stated outcome and proof are both satisfied.
- A superseded task remains unchecked and names the replacing task/outcome.
- Deferred work remains unchecked and requires explicit human approval.
- Cross-platform CI and human tasks remain unchecked until their external proof
  actually exists; local implementation does not infer those results.

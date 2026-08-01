# Tasks: Provider-Neutral AI Session Integration Proof

**Input**: Design documents from `specs/002-session-integration-proof/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Contract, unit, acceptance, packaging, negative-path, conformance, and runtime-isolation tests are required by the specification and constitution. In every phase below, add the listed tests first, confirm that they fail for the intended reason, and then implement the behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and demonstrated as an independently meaningful increment. Requirement identifiers in parentheses provide direct traceability for the later Spec Kit analysis.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase because it changes different files and has no unfinished dependency
- **[Story]**: User story served by the task (`[US1]` through `[US5]`)
- Every task names the exact file or directory it changes or uses for recorded evidence

## Phase 1: Setup (Shared Project Structure)

**Purpose**: Add the project and packaging skeleton needed by every user story without implementing session behavior.

- [X] T001 [P] Create the provider-neutral class-library project with locked restore and references to Contracts and Kernel in `src/ProgramKit.SessionIntegration/ProgramKit.SessionIntegration.csproj`
- [X] T002 [P] Create the Codex provider class-library project with locked restore and a one-way reference to SessionIntegration in `src/ProgramKit.SessionIntegration.Providers.Codex/ProgramKit.SessionIntegration.Providers.Codex.csproj`
- [X] T003 Add both session-integration projects to `ProgramKit.slnx`
- [X] T004 Add SessionIntegration and Codex provider project references to `src/ProgramKit.Cli/ProgramKit.Cli.csproj`
- [X] T005 Add the new source-project references required for contract, unit, and acceptance coverage to `tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj`, `tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj`, and `tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj`
- [X] T006 Configure the CLI as package `Orbyss.ProgramKit.Cli` version `1.0.0-alpha.1` with tool command `program-kit`, symbols, source metadata, and package README in `src/ProgramKit.Cli/ProgramKit.Cli.csproj` (FR-001, FR-002)
- [X] T007 Add a deterministic local-pack entry point that accepts an explicit output directory and performs locked restore in `eng/Pack-ProgramKitTool.ps1` (FR-001, FR-003)
- [X] T008 Add the repository-owned source-authoring marker and schema version in `.program-kit-source.json` (FR-006)
- [X] T009 Restore the new projects in locked mode and commit their generated lock files in `src/ProgramKit.SessionIntegration/packages.lock.json` and `src/ProgramKit.SessionIntegration.Providers.Codex/packages.lock.json`

---

## Phase 2: Foundational Contracts and Trusted Mechanics (Blocking)

**Purpose**: Establish canonical schemas, request-bound authority, namespaced atomic publication, provider boundaries, and source-workspace rejection before any lifecycle command is implemented.

**CRITICAL**: No user-story implementation starts until this phase passes.

### Tests first

- [X] T010 [P] Add schema-validation and canonical round-trip tests for all four session contracts in `tests/ProgramKit.ContractTests/SessionIntegrationSchemaContractTests.cs` (FR-007 through FR-010, FR-015, FR-019)
- [X] T011 [P] Add compatibility tests proving session operations extend `operation-result/v1` rather than introducing another envelope in `tests/ProgramKit.ContractTests/SessionOperationResultContractTests.cs` (FR-039, FR-040)
- [X] T012 [P] Add denial, mismatch, expiration, reuse, and exact-operation/path tests for request-bound authority grants in `tests/ProgramKit.UnitTests/SessionAuthorityGrantTests.cs` (FR-020, FR-026, FR-027)
- [X] T013 [P] Add collision, interruption, rollback, stale-staging, and byte-preservation tests for namespaced atomic publication in `tests/ProgramKit.UnitTests/NamespacedArtifactSetPublisherTests.cs` (FR-021, FR-022, FR-043)
- [X] T014 [P] Add architectural tests prohibiting provider symbols in canonical contracts, runtime dependencies on session projects, dynamic provider discovery, production provider-process launching, telemetry/source-upload clients, provider-global registration, and source self-integration in `tests/ProgramKit.ContractTests/SessionIntegrationBoundaryTests.cs` (FR-006, FR-011 through FR-014, FR-033, FR-043, SC-009, SC-010)

### Canonical contracts and kernel mechanics

- [X] T015 Define immutable records, enums, identity fields, lifecycle states, ownership entries, disclosure entries, and version fields in `src/ProgramKit.Contracts/SessionIntegration/SessionIntegrationContracts.cs` (FR-007 through FR-010, FR-015, FR-019)
- [X] T016 Define stable session operation identifiers and typed lifecycle request/result payloads in `src/ProgramKit.Contracts/SessionIntegration/SessionOperationContracts.cs` (FR-016, FR-039, FR-040)
- [X] T017 [P] Add the canonical integration-definition JSON Schema in `src/ProgramKit.Contracts/Schemas/session-integration-definition.schema.json` (FR-007, FR-011)
- [X] T018 [P] Add the provider-manifest JSON Schema, including compatibility and projection ownership declarations, in `src/ProgramKit.Contracts/Schemas/session-provider-manifest.schema.json` (FR-008, FR-012, FR-034)
- [X] T019 [P] Add the lifecycle-request JSON Schema with explicit provider, workspace, operation, and authority binding in `src/ProgramKit.Contracts/Schemas/session-integration-request.schema.json` (FR-010, FR-016, FR-020)
- [X] T020 [P] Add the installation-record JSON Schema with canonical/provider versions, owned artifacts, fingerprints, state, and journal metadata in `src/ProgramKit.Contracts/Schemas/session-installation-record.schema.json` (FR-009, FR-019, FR-045)
- [X] T021 Register the four schemas through stable resource identifiers in `src/ProgramKit.Contracts/Schemas/ContractSchemaResources.cs`
- [X] T022 Extend the existing envelope schema and typed result projection with session payloads and disclosure metadata in `src/ProgramKit.Contracts/Schemas/operation-result.schema.json`, `src/ProgramKit.Contracts/Operations/OperationResult.cs`, `src/ProgramKit.Kernel/Operations/OperationResultProjector.cs`, and `src/ProgramKit.Kernel/Operations/OperationResultFactory.cs` (FR-039 through FR-042)
- [X] T023 Implement exact request-bound grant validation and extend the authority schema/provider without ambient approval in `src/ProgramKit.Contracts/Schemas/authority-grant.schema.json`, `src/ProgramKit.Kernel/Authority/RequestBoundAuthorityValidator.cs`, and `src/ProgramKit.Kernel/Authority/RepositoryAuthorityProvider.cs` (FR-020, FR-026, FR-027)
- [X] T024 Implement reusable namespace ownership, collision checks, staging, verification, atomic commit, and recoverable rollback in `src/ProgramKit.Kernel/Artifacts/NamespacedArtifactSetPublisher.cs` (FR-021, FR-022, FR-043)
- [X] T025 Preserve Feature 001 behavior by adapting its publication path to the namespaced publisher in `src/ProgramKit.Kernel/Publication/RecoverablePublisher.cs`
- [X] T026 Define the explicit provider adapter interface and provider-owned projection boundary in `src/ProgramKit.SessionIntegration/Providers/ISessionProviderAdapter.cs` (FR-012, FR-013, FR-033)
- [X] T027 Implement explicit in-process provider registration with duplicate, missing, and incompatible-provider diagnostics in `src/ProgramKit.SessionIntegration/Providers/SessionProviderRegistry.cs` (FR-012, FR-034, FR-038)
- [X] T028 Implement canonical-definition loading, schema validation, fingerprinting, and version compatibility in `src/ProgramKit.SessionIntegration/Definitions/SessionIntegrationDefinitionLoader.cs` (FR-007, FR-014, FR-035)
- [X] T029 Define the provider-neutral diagnostic catalog version, reserve identifiers `PKSES0001` through `PKSES0009`, and implement the stable metadata shape and lookup invariants in `src/ProgramKit.SessionIntegration/Diagnostics/SessionDiagnosticCatalog.cs` (FR-039, FR-040)
- [X] T030 Implement fail-closed source-marker detection shared by explain, install, verify, catalog, preflight, read, and remove paths in `src/ProgramKit.SessionIntegration/Policy/SourceAuthoringGuard.cs` (FR-006)
- [X] T031 Add isolated repository, package-feed, denied-network, interruption, fingerprint, process-observation, and byte-comparison helpers in `tests/Shared/SessionIntegrationTestWorkspace.cs` (FR-003, FR-043)
- [X] T032 Run the foundational contract and unit filters and record passing command/output evidence in `specs/002-session-integration-proof/verification.md`

**Checkpoint**: Canonical types and schemas round-trip, authority is request-bound, publication is recoverable, source self-integration fails closed, and provider code cannot leak into the canonical layer.

---

## Phase 3: User Story 1 - Connect Program Kit to an AI Workspace (Priority: P1) - MVP

**Goal**: A user can install the pinned CLI in an isolated consumer repository, explain the intended changes, install the Codex projection atomically, and verify an exact installation record.

**Independent Test**: From a fresh repository with no Program Kit source checkout, install `Orbyss.ProgramKit.Cli` from an isolated feed, run `program-kit session explain --provider codex`, grant the exact request, run `install`, start a fresh Codex-visible workspace view, and run `verify`; repeat the deterministic install/verify path ten times with identical canonical inputs.

### Tests first

- [X] T033 [P] [US1] Add CLI grammar tests for `session explain|install|verify|remove`, required options, JSON output, and invalid nesting in `tests/ProgramKit.ContractTests/SessionCliContractTests.cs` (FR-016, FR-017)
- [X] T034 [P] [US1] Add lifecycle state-transition, idempotency, drift, stale record, incompatible-version, already-running-session, reload-required, and fresh-session-available tests in `tests/ProgramKit.UnitTests/SessionLifecycleTests.cs` (FR-018, FR-019, FR-022, FR-023)
- [X] T035 [P] [US1] Add golden projection and ownership tests for `.agents/skills/program-kit/SKILL.md` and optional `agents/openai.yaml` in `tests/ProgramKit.ContractTests/CodexProjectionContractTests.cs` (FR-012, FR-013, FR-021)
- [X] T036 [P] [US1] Add an acceptance test that packs the CLI, installs it from an isolated local feed, denies network access after acquisition, invokes only the installed `program-kit` command, and proves no source checkout, SDK assembly dependency, telemetry, source upload, or provider-global registration in `tests/ProgramKit.AcceptanceTests/PackagedToolAcceptanceTests.cs` (FR-001 through FR-005, FR-043, SC-001, SC-009)
- [X] T037 [P] [US1] Add ten-trial fresh-workspace explain/install/verify acceptance coverage with exact record assertions and explicit distinction between already-running-session availability, reload-required state, and fresh-session discovery in `tests/ProgramKit.AcceptanceTests/SessionInstallationAcceptanceTests.cs` (FR-015 through FR-023, SC-002, SC-007)

### Implementation

- [X] T038 [US1] Implement CLI/package release-identity evaluation so records and results report the invoked package version, not source-build identity, in `src/ProgramKit.Cli/Composition/CliReleaseIdentityProvider.cs` (FR-002, FR-004)
- [X] T039 [US1] Implement request parsing, canonical input normalization, target inspection, deterministic candidate construction, and pre-publication ownership checks in `src/ProgramKit.SessionIntegration/Publication/SessionIntegrationCandidateBuilder.cs` (FR-015 through FR-018, FR-021)
- [X] T040 [US1] Implement the read-only explain operation with an exact change set, authority request, provider selection, diagnostics, and disclosure in `src/ProgramKit.SessionIntegration/Publication/ExplainSessionIntegrationOperation.cs` (FR-015 through FR-017, FR-020)
- [X] T041 [US1] Implement install admission, exact-grant consumption, recoverable publication, record persistence, and idempotent replay in `src/ProgramKit.SessionIntegration/Publication/InstallSessionIntegrationOperation.cs` (FR-018 through FR-022)
- [X] T042 [US1] Implement verify for record/schema/version/fingerprint/ownership/drift checks without mutation, separately reporting installation validity, already-running-session availability, reload requirements, and fresh-session readiness in `src/ProgramKit.SessionIntegration/Publication/VerifySessionIntegrationOperation.cs` (FR-019, FR-022, FR-023)
- [X] T043 [US1] Implement atomic installation-record and transaction-journal persistence under the Program Kit-owned workspace namespace in `src/ProgramKit.SessionIntegration/Publication/SessionInstallationStore.cs` (FR-019, FR-022, FR-045)
- [X] T044 [P] [US1] Define the pinned Codex provider manifest, compatibility range, owned paths, and projection version in `src/ProgramKit.SessionIntegration.Providers.Codex/Resources/codex-provider-manifest.json` (FR-012, FR-034, FR-035)
- [X] T045 [US1] Implement deterministic Codex artifact projection from canonical definitions without placing Codex symbols in neutral assemblies in `src/ProgramKit.SessionIntegration.Providers.Codex/CodexSessionProviderAdapter.cs` (FR-012 through FR-014, FR-033)
- [X] T046 [P] [US1] Define stable `PKCDX0001` through `PKCDX0003` provider diagnostics in `src/ProgramKit.SessionIntegration.Providers.Codex/Diagnostics/CodexDiagnosticCatalog.cs` (FR-038 through FR-040)
- [X] T047 [US1] Extend nested command parsing, provider/workspace/authority options, and canonical JSON mode in `src/ProgramKit.Cli/Parsing/CliParser.cs` and `src/ProgramKit.Cli/Parsing/CliInvocation.cs` (FR-016, FR-017)
- [X] T048 [US1] Route session lifecycle verbs while preserving existing factory verbs in `src/ProgramKit.Cli/Commands/Session/SessionCommandDispatcher.cs` and `src/ProgramKit.Cli/Commands/CommandDispatcher.cs` (FR-016)
- [X] T049 [US1] Register the neutral lifecycle services and explicit Codex provider in `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs` (FR-012, FR-016)
- [X] T050 [US1] Document stable session syntax and package/release identity in CLI help and version output in `src/ProgramKit.Cli/Commands/HelpCommand.cs` (FR-002, FR-016)
- [X] T051 [P] [US1] Add valid lifecycle fixtures under `tests/Fixtures/SessionIntegration/Valid/`, collision fixtures under `tests/Fixtures/SessionIntegration/Colliding/`, and interrupted, stale-record, drifted, and source-authoring fixtures under `tests/Fixtures/SessionIntegration/Invalid/` and `tests/Fixtures/SessionIntegration/Drifted/` (FR-006, FR-021 through FR-023)
- [X] T052 [US1] Run the US1 test filters and record the packaged-tool hash, ten trial records, deterministic fingerprints, already-running/reload/fresh-session observations, and expected negative outcomes in `specs/002-session-integration-proof/verification.md` (SC-001, SC-002, SC-007)

**Checkpoint**: US1 is an MVP that can be demonstrated entirely from the packaged CLI in an isolated consumer repository.

---

## Phase 4: User Story 2 - Build Safely from Imperfect Human Intent (Priority: P2)

**Goal**: The installed provider projection teaches a human-led, provider-neutral AI session to distinguish known from unknown intent, clarify materially incomplete input, obtain exact authority, invoke factory operations, and interpret typed results without pretending that generated domain code is deterministic.

**Independent Test**: Give a fresh test session a supported but incomplete component request; it must explain the gap, ask only relevant questions, preserve the approved answers in the exact request, request a scoped grant, invoke the CLI, and report the typed result while leaving unknown implementation intent explicitly unresolved.

### Tests first

- [X] T053 [P] [US2] Add canonical guidance contract tests for known/unknown intent, clarification, explicit provider resolution, authority, result interpretation, and semantic honesty in `tests/ProgramKit.ContractTests/SessionGuidanceContractTests.cs` (FR-024 through FR-032)
- [X] T054 [P] [US2] Add exact-request binding tests proving changed answers, targets, operations, or provider choices invalidate construction authority in `tests/ProgramKit.UnitTests/ConstructAuthorityBindingTests.cs` (FR-026, FR-027)
- [X] T055 [P] [US2] Add a deterministic public-integration acceptance harness covering the complete explain-to-construct-to-evaluate journey, incomplete intent resolved within two interaction turns, declined authority, unknown intent, exact grant preservation, typed result preservation, and read-only drift evaluation in `tests/ProgramKit.AcceptanceTests/HumanLedSessionWorkflowAcceptanceTests.cs` (FR-024 through FR-032, SC-003, SC-005)
- [X] T056 [P] [US2] Add an acceptance test that generates the reference application, restores and builds it, removes the provider projection and Program Kit session integration, starts it, exercises accepted `/status` behavior, and proves its dependency closure contains no Program Kit, Spec Kit, Codex provider, or development-session asset in `tests/ProgramKit.AcceptanceTests/SessionRuntimeIsolationAcceptanceTests.cs` (FR-003, FR-005, FR-014, SC-010)

### Implementation

- [X] T057 [US2] Define provider-neutral explain-to-construct-to-evaluate workflow steps, bounded clarification points, input preservation rules, read-only evaluation rules, and typed result semantics in `src/ProgramKit.SessionIntegration/Definitions/CanonicalSessionGuidance.cs` (FR-024 through FR-032)
- [X] T058 [US2] Implement an exact invocation binding that carries canonical input fingerprint, provider resolution, operation, targets, and grant identity into CLI requests in `src/ProgramKit.SessionIntegration/Providers/SessionInvocationBinding.cs` (FR-025 through FR-027)
- [X] T059 [US2] Replace ambient construction approval with request-bound authority validation while preserving Feature 001 results in `src/ProgramKit.Kernel/Operations/ConstructOperation.cs` (FR-026, FR-027)
- [X] T060 [US2] Project the complete canonical journey and static invocation-transport guidance into the Codex skill with provider-local syntax only and no copied source truth in `src/ProgramKit.SessionIntegration.Providers.Codex/Projection/CodexSkillProjector.cs` (FR-024 through FR-032, FR-039)
- [X] T061 [P] [US2] Add valid explain-construct-evaluate and corrected-intent corpora under `tests/Fixtures/SessionIntegration/Valid/Guidance/` and incomplete-known-intent, unknown-intent, explicit-provider-choice, and declined-authority corpora under `tests/Fixtures/SessionIntegration/Invalid/Guidance/` (FR-024 through FR-030)
- [X] T062 [US2] Execute ten isolated deterministic full-journey harness trials and record clarification-turn counts, preserved request fingerprints, authority outcomes, construct results, read-only evaluation results, drift non-mutation, application startup/behavior, and runtime dependency closure in `specs/002-session-integration-proof/verification.md` (FR-029, FR-030, SC-003, SC-005, SC-010)
- [X] T063 [US2] Run the complete US2 contract, unit, and acceptance filters and record their command/output evidence in `specs/002-session-integration-proof/verification.md`

**Checkpoint**: The projected skill guides the session, but the CLI and kernel remain the only authorities for contract validation, admission, publication, and diagnostics.

---

## Phase 5: User Story 3 - Recover Through Actionable Diagnostics (Priority: P3)

**Goal**: Every expected failure returns a stable, structured, disclosure-safe result that tells an AI session what failed, where it failed, what can be retried, and which corrective action is safe.

**Independent Test**: Run the documented malformed input, ambiguous resolution, missing provider, incompatible provider, denied authority, ownership collision, interrupted publication, drift, disclosure, and provider-transport failures and compare each typed result with the golden diagnostic contract.

### Tests first

- [X] T064 [P] [US3] Add uniqueness, severity, location, retryability, remediation, ordering, truncation, and version tests for every `PKSES` and `PKCDX` diagnostic in `tests/ProgramKit.ContractTests/SessionDiagnosticCatalogContractTests.cs` (FR-039 through FR-043)
- [X] T065 [P] [US3] Add golden operation-result tests for every specified negative scenario in `tests/ProgramKit.ContractTests/SessionNegativeResultGoldenTests.cs` (FR-039 through FR-043, SC-004)
- [X] T066 [P] [US3] Add secret, path, stack-trace, tool-output, malformed-value, and size-limit disclosure tests in `tests/ProgramKit.UnitTests/SessionDisclosureTests.cs` (FR-041, FR-042, SC-009)
- [X] T067 [P] [US3] Add contract tests proving projected guidance classifies unavailable CLI, shell timeout, non-zero exit without a valid envelope, malformed JSON, and missing result as integration-layer transport failures without launching a provider or fabricating a Program Kit result in `tests/ProgramKit.ContractTests/InvocationTransportGuidanceContractTests.cs` (FR-038 through FR-040)

### Implementation

- [X] T068 [US3] Populate reserved identifiers `PKSES0001` through `PKSES0009` with scenario-specific subjects, expectations, consequences, safe observed/expected data, retryability, bounded remediation actions, and deterministic ordering in `src/ProgramKit.SessionIntegration/Diagnostics/SessionDiagnosticCatalog.cs` (FR-039 through FR-043)
- [X] T069 [US3] Define static provider-neutral guidance for classifying pre-result shell invocation failures without product code launching the provider or CLI in `src/ProgramKit.SessionIntegration/Definitions/InvocationTransportGuidance.cs` (FR-038 through FR-040)
- [X] T070 [US3] Implement canonical next-action projection that never asks an AI session to infer success or correction from prose in `src/ProgramKit.SessionIntegration/Diagnostics/SessionRemediationProjector.cs` (FR-040, FR-043)
- [X] T071 [US3] Extend allowlisted disclosure, stable redaction, bounded tool output, and safe fallback behavior in `src/ProgramKit.Kernel/Diagnostics/DisclosureFilter.cs` (FR-041, FR-042, SC-009)
- [X] T072 [P] [US3] Add malformed, ambiguous, missing-provider, incompatible-provider, denied-authority, interruption, secret, and transport fixtures under `tests/Fixtures/SessionIntegration/Invalid/Diagnostics/` and collision/drift fixtures under `tests/Fixtures/SessionIntegration/Colliding/` and `tests/Fixtures/SessionIntegration/Drifted/` (SC-004)
- [X] T073 [US3] Add end-to-end negative-path orchestration using only packaged CLI JSON results in `tests/ProgramKit.AcceptanceTests/SessionDiagnosticsAcceptanceTests.cs` (FR-039 through FR-043, SC-004, SC-005, SC-009)
- [X] T074 [US3] Implement a valid `operation-result/v1` fallback for unexpected internal failures and serialization failures in `src/ProgramKit.SessionIntegration/Diagnostics/SessionFailureBoundary.cs` (FR-039, FR-040)
- [X] T075 [US3] Run the US3 test filters and record golden-result hashes, disclosure audit results, and corrective-action outcomes in `specs/002-session-integration-proof/verification.md` (SC-004, SC-005, SC-009)

**Checkpoint**: Expected and unexpected failures produce bounded, versioned, AI-usable results without exposing undeclared data.

---

## Phase 6: User Story 4 - Project the Same Contract to Another Provider (Priority: P4)

**Goal**: Prove provider neutrality with a provider-independent harness and corpus, without implementing a speculative second provider.

**Independent Test**: Execute the same canonical corpus directly against the neutral lifecycle, through the neutral test adapter, and through the Codex adapter; compare normalized semantic outcomes, diagnostics, authority boundaries, and deterministic artifacts across input permutations and repeated runs.

### Tests first

- [X] T076 [P] [US4] Add conformance-profile contract tests for required operations, compatibility, ownership, diagnostics, and semantic comparison fields in `tests/ProgramKit.ContractTests/SessionProviderConformanceContractTests.cs` (FR-033 through FR-038)
- [X] T077 [P] [US4] Add assembly and schema inspection tests proving canonical artifacts contain no Codex paths, command names, payloads, or types in `tests/ProgramKit.ContractTests/ProviderNeutralityArchitectureTests.cs` (FR-011, FR-013, FR-033)
- [X] T078 [P] [US4] Add repeated-run and semantically irrelevant input-permutation determinism tests in `tests/ProgramKit.UnitTests/SessionProjectionDeterminismTests.cs` (FR-036, FR-037)

### Implementation

- [X] T079 [US4] Define normalized conformance inputs, observations, semantic equivalence rules, and failure reports in `src/ProgramKit.SessionIntegration/Providers/Conformance/SessionProviderConformance.cs` (FR-033 through FR-038)
- [X] T080 [US4] Implement the provider-neutral conformance evaluator over the public adapter contract in `src/ProgramKit.SessionIntegration/Providers/Conformance/SessionProviderConformanceEvaluator.cs` (FR-033 through FR-038)
- [X] T081 [P] [US4] Implement a test-only neutral adapter and invocation harness without provider-local assumptions in `tests/Shared/NeutralSessionProviderHarness.cs` (FR-033, FR-036)
- [X] T082 [P] [US4] Add the provider-neutral canonical input, authority, result, diagnostic, and artifact golden corpus under `tests/Fixtures/SessionIntegration/Providers/Conformance/` (FR-035 through FR-038)
- [X] T083 [US4] Add Codex adapter conformance coverage for valid, stale, incompatible, and corrupted projection cases in `tests/ProgramKit.AcceptanceTests/CodexProviderConformanceAcceptanceTests.cs` (FR-034, FR-035, FR-038)
- [X] T084 [US4] Add direct-neutral-Codex semantic equivalence acceptance coverage with normalized provider-local differences in `tests/ProgramKit.AcceptanceTests/SessionProviderParityAcceptanceTests.cs` (FR-033 through FR-038, SC-006)
- [X] T085 [US4] Run all conformance modes and record corpus hashes, repeated-run hashes, permutation results, and semantic comparisons in `specs/002-session-integration-proof/verification.md` (SC-006)

**Checkpoint**: The canonical contract is demonstrably provider-neutral, and Codex is one explicit projection rather than hidden source truth.

---

## Phase 7: User Story 5 - Remove the Integration Safely (Priority: P5)

**Goal**: Remove only recorded Program Kit-owned session artifacts, preserve user/provider state, and fail safely when drift prevents exact deletion.

**Independent Test**: Install the projection, add unrelated workspace files and modify one owned artifact, run remove, and prove unchanged owned artifacts are removed, drifted/user files are preserved with diagnostics, the installed CLI remains available, and the final record accurately describes the outcome.

### Tests first

- [X] T086 [P] [US5] Add absent, installed, partial, drifted, interrupted, and already-removed state-transition tests in `tests/ProgramKit.UnitTests/RemoveSessionIntegrationTests.cs` (FR-044 through FR-046)
- [X] T087 [P] [US5] Add byte-for-byte preservation acceptance coverage for unrelated files, drifted owned files, provider/global state, and the installed CLI in `tests/ProgramKit.AcceptanceTests/SessionRemovalAcceptanceTests.cs` (FR-044 through FR-046, SC-008)

### Implementation

- [X] T088 [US5] Implement record-driven removal planning, exact fingerprint checks, scoped authority, and fail-closed drift handling in `src/ProgramKit.SessionIntegration/Publication/RemoveSessionIntegrationOperation.cs` (FR-044 through FR-046)
- [X] T089 [US5] Implement recoverable removal journaling and final-state receipts without broad directory deletion in `src/ProgramKit.SessionIntegration/Publication/SessionRemovalJournal.cs` (FR-044, FR-045)
- [X] T090 [US5] Extend verification to distinguish absent, removed, partially removed, drifted, and corrupt-record states in `src/ProgramKit.SessionIntegration/Publication/VerifySessionIntegrationOperation.cs` (FR-023, FR-045, FR-046)
- [X] T091 [P] [US5] Add exact-removal fixtures under `tests/Fixtures/SessionIntegration/Valid/Removal/`, drifted and unrelated-state fixtures under `tests/Fixtures/SessionIntegration/Drifted/Removal/`, and absent, partial, and interrupted-removal fixtures under `tests/Fixtures/SessionIntegration/Invalid/Removal/` (FR-044 through FR-046)
- [X] T092 [US5] Add packaged-tool removal coverage that invokes the CLI after projection removal and compares all preserved bytes in `tests/ProgramKit.AcceptanceTests/PackagedToolRemovalAcceptanceTests.cs` (FR-003, FR-044 through FR-046, SC-008)
- [X] T093 [US5] Run the US5 test filters and record owned/preserved artifact hashes and final lifecycle states in `specs/002-session-integration-proof/verification.md` (SC-008)

**Checkpoint**: Removal is exact and recoverable; it never treats provider directories, global configuration, the CLI installation, or drifted consumer files as disposable.

---

## Phase 8: Polish, Cross-Cutting Proof, and Review Gates

**Purpose**: Complete distribution, documentation, CI, deterministic proof, disclosure proof, and explicitly human-owned product acceptance.

- [x] T094 [P] Implement the isolated-feed package/install/explain/grant/install/verify/negative/remove quickstart with explicit temporary-root safety, denied network after acquisition, and assertions for zero telemetry, source upload, or provider-global registration in `eng/Invoke-SessionIntegrationQuickstart.ps1` (FR-001 through FR-006, FR-043, SC-001, SC-002, SC-004, SC-007 through SC-009)
- [x] T095 [P] Implement the sole opt-in provider-process launcher: a pinned Codex `0.137.0` ten-session review harness that records bounded evidence without placing provider launching in product assemblies or making live Codex a CI dependency in `eng/Invoke-CodexSessionReview.ps1` (SC-003)
- [x] T096 Add Windows and Linux locked restore, build, test, pack, quickstart, conformance, runtime-isolation, and disclosure jobs to `.github/workflows/vertical-slice.yml` (SC-001, SC-002, SC-004, SC-006 through SC-010)
- [x] T097 [P] Update current product status, isolated CLI installation, session lifecycle, source-workspace prohibition, provider-neutral boundary, Codex adapter scope, and non-goals in `README.md` (FR-001 through FR-006, FR-011 through FR-014)
- [x] T098 Refresh and verify complete locked dependency closure in `src/ProgramKit.Cli/packages.lock.json`, `src/ProgramKit.SessionIntegration/packages.lock.json`, `src/ProgramKit.SessionIntegration.Providers.Codex/packages.lock.json`, `tests/ProgramKit.UnitTests/packages.lock.json`, `tests/ProgramKit.ContractTests/packages.lock.json`, and `tests/ProgramKit.AcceptanceTests/packages.lock.json`
- [x] T099 Run formatting, locked restore, build, full tests, package inspection, and forbidden-dependency scans and record exact commands, versions, and outcomes in `specs/002-session-integration-proof/verification.md`
- [ ] T100 Execute the deterministic quickstart for ten fresh workspaces on supported platforms and record package hashes, elapsed installation times, records, diagnostics, removal proofs, and failures in `specs/002-session-integration-proof/reviews/deterministic-session-review.json` (SC-001, SC-002, SC-004, SC-007, SC-008)
- [ ] T101 Execute the pinned live Codex ten-session review when explicitly authorized and store raw bounded evidence in `specs/002-session-integration-proof/reviews/codex-session-review.json` (SC-003, SC-005)
- [ ] T102 Obtain an independent human product-review decision over the fresh-session evidence and record approval, rejection, findings, reviewer identity, and timestamp in `specs/002-session-integration-proof/reviews/product-review.md` (SC-003)
- [x] T103 Perform a final disclosure, secret, telemetry, source-upload, undeclared-network, and provider-global-registration scan of packaged artifacts, projections, results, journals, and review evidence and record the zero-finding assertion in `specs/002-session-integration-proof/verification.md` (FR-043, SC-009)
- [x] T104 Re-run generated-application restore, build, startup, accepted `/status` behavior, post-integration-removal behavior, and dependency closure, then record that no Program Kit, Spec Kit, session integration, or provider assembly is required at runtime in `specs/002-session-integration-proof/verification.md` (FR-005, SC-010)
- [ ] T105 Reconcile every FR/SC below to passing automated evidence or an explicitly pending human gate, and record the final feature disposition without self-approving semantics in `specs/002-session-integration-proof/verification.md`

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks every user story.
- **US1 (P1)**: Depends on Phase 2; this is the MVP and establishes the installable lifecycle used by later end-to-end stories.
- **US2 (P2)**: Depends on the US1 installed projection and request lifecycle, but its contract/unit work can begin once Phase 2 is complete.
- **US3 (P3)**: Depends on the canonical envelope from Phase 2 and lifecycle paths from US1; its catalog contract work can begin after Phase 2.
- **US4 (P4)**: Depends on the neutral adapter contract, US1 lifecycle behavior, US2 guidance semantics, and US3 normalized diagnostics.
- **US5 (P5)**: Depends on the US1 installation record and publication mechanics; its unit tests can begin after Phase 2.
- **Phase 8 (Polish/Proof)**: Depends on all implemented user stories. T101 and T102 are external evidence gates: they are mandatory for full SC-003 acceptance, never fabricated, and deliberately excluded from deterministic CI.

### User-story dependency graph

`Setup -> Foundation -> US1 -> {US2, US3, US5} -> US4 -> Cross-cutting proof -> Independent human review`

### Within each user story

1. Add contract/unit/acceptance tests and confirm the intended failure.
2. Implement neutral contract and kernel behavior before provider projection behavior.
3. Implement provider-local projection without moving canonical truth into provider code.
4. Run the story's focused tests and record evidence before starting dependent work.
5. Do not mark a story complete when its required external evidence gate is still pending.

### Parallel opportunities

- T001 and T002 can run in parallel.
- T010 through T014 can run in parallel; T017 through T020 can run in parallel after T015 establishes the model names.
- In US1, T033 through T037 can run in parallel, and T044/T046/T051 can run in parallel with neutral implementation after their prerequisite contracts exist.
- In US2, T053 through T056 can run in parallel; T061 can run in parallel with implementation.
- In US3, T064 through T067 can run in parallel; T072 can run in parallel with implementation.
- In US4, T076 through T078 can run in parallel; T081 and T082 can run in parallel after T079 defines the conformance model.
- In US5, T086 and T087 can run in parallel; T091 can run in parallel with implementation.
- T094, T095, and T097 can run in parallel after all story behavior stabilizes.

---

## Parallel Example: User Story 1

```text
Task T033: CLI session grammar contract tests
Task T034: Lifecycle unit tests
Task T035: Codex projection contract tests
Task T036: Packaged tool acceptance tests
Task T037: Ten-workspace lifecycle acceptance tests
```

## Parallel Example: User Story 3

```text
Task T064: Diagnostic catalog contract tests
Task T065: Negative-result golden tests
Task T066: Disclosure tests
Task T067: Provider transport failure tests
```

## Parallel Example: User Story 4

```text
Task T076: Provider conformance contract tests
Task T077: Provider-neutrality architecture tests
Task T078: Determinism and permutation tests
```

---

## Implementation Strategy

### MVP first

1. Complete Setup and Foundational phases.
2. Complete US1 and its isolated packaged-tool proof.
3. Demonstrate explain/install/verify from a fresh consumer repository.
4. Stop and validate the public lifecycle before expanding session guidance or conformance.

### Incremental delivery

1. **US1** delivers the independently installable session lifecycle.
2. **US2** adds honest human-led AI workflow guidance and request-bound invocation.
3. **US3** makes every expected recovery path actionable and disclosure-safe.
4. **US4** proves the contract is provider-neutral without building a speculative second adapter.
5. **US5** closes the lifecycle with exact, non-destructive removal.
6. Cross-cutting deterministic and human evidence determines whether the feature is ready beyond development use.

### Scope guardrails

- Do not add MCP bindings, plugins, global provider configuration, `AGENTS.md` mutation, Spec Kit orchestration, native planning, runtime AI dependencies, migration machinery, dynamic provider discovery, or a second provider.
- Do not make the Program Kit source repository consume its own session integration.
- Do not treat live provider execution as a deterministic CI dependency; only the explicitly authorized `eng/Invoke-CodexSessionReview.ps1` review harness may launch Codex, and no product assembly may launch an AI provider.
- Do not translate unknown domain implementation intent into a false deterministic claim.
- Do not let provider-local syntax, paths, payloads, or types become canonical source truth.

---

## Requirement Coverage Index

| Requirement group | Primary task coverage |
|---|---|
| FR-001 through FR-006: distribution and isolation | T006-T008, T014, T036, T056, T094, T097, T104 |
| FR-007 through FR-014: canonical session integration | T010, T014-T22, T026-T030, T035, T044-T046, T077 |
| FR-015 through FR-023: explicit lifecycle | T019-T024, T033-T043, T047-T052 |
| FR-024 through FR-032: human-led AI behavior | T053-T063, T101-T102 |
| FR-033 through FR-038: provider neutrality | T014, T026-T028, T044-T046, T067, T076-T085 |
| FR-039 through FR-043: diagnostics, disclosure, and local-first operation | T011, T014, T022, T029-T031, T036, T046, T064-T075, T094, T103 |
| FR-044 through FR-046: exact removal | T020, T043, T086-T093 |
| SC-001 through SC-010 | T036-T037, T052, T055-T056, T062, T065-T066, T073-T075, T084-T085, T087, T092-T105 |

## Notes

- `[P]` means different files and no unfinished dependency; it does not authorize concurrent edits to shared project or verification files.
- Keep generated and golden artifacts deterministic, UTF-8, and path-normalized.
- Commit after each coherent task or tightly coupled red/green pair with the requirement identifiers in the commit message.
- `verification.md` is append-only evidence during implementation; consolidate it only in T105 without removing raw command provenance.
- T101 and T102 require explicit live-provider availability and an independent human decision. A pending gate is truthful; invented success is not.

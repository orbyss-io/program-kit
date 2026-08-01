# Tasks: Claude Code Session Adapter

**Input**: Design documents from `specs/003-claude-code-adapter/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Contract, unit, acceptance, conformance, packaging, negative-path, deterministic-review, disclosure, and runtime-isolation tests are required. Add each listed test first, confirm that it fails for the intended reason, and then implement the corresponding behavior.

**Organization**: Tasks are grouped by user story so the adapter can be implemented and evaluated incrementally. Requirement identifiers in parentheses provide direct traceability.

**Upstream acceptance constraint**: Feature 002 is the immutable provider-neutral dependency for this feature, but its product acceptance is currently **rejected**. Feature 003 MUST NOT modify Feature 002 or claim the Claude adapter `supported`, pass live-product review, or accept release evidence while that dependency remains rejected. Deterministic adapter mechanics MAY be implemented and verified with the support claim fail-closed as `not-evaluated`; the blocked acceptance gates remain explicit below.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase because it changes different files and has no unfinished dependency
- **[Story]**: User story served by the task (`[US1]` through `[US5]`)
- Every task names the exact file or directory it changes or uses for evidence

## Phase 1: Setup (Shared Project Structure)

**Purpose**: Add the isolated Claude provider project and test references without changing provider-neutral contracts.

- [X] T001 Create the locked-restore Claude provider class-library project with a one-way reference to SessionIntegration in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/ProgramKit.SessionIntegration.Providers.ClaudeCode.csproj`
- [X] T002 Add `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/ProgramKit.SessionIntegration.Providers.ClaudeCode.csproj` to `ProgramKit.slnx`
- [X] T003 Add the Claude provider reference to `src/ProgramKit.Cli/ProgramKit.Cli.csproj`
- [X] T004 Add Claude provider references required by contract, unit, and acceptance coverage to `tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj`, `tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj`, and `tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj`
- [X] T005 [P] Create the planned provider source folders under `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/`, `Projection/`, `Invocation/`, `Diagnostics/`, `Conformance/`, and `Schemas/`
- [X] T006 Restore in locked mode and commit `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/packages.lock.json` plus updated test and CLI lock files

---

## Phase 2: Foundational Provider Contracts and Fail-Closed Support (Blocking)

**Purpose**: Establish exact Claude identities, provider-only schemas, diagnostic vocabulary, and an executable guard that prevents the rejected Feature 002 dependency from becoming a support claim.

**CRITICAL**: No user-story implementation starts until these tests and mechanics pass. This phase may inspect Feature 002 identities but MUST NOT alter Feature 002 artifacts or semantics.

### Tests first

- [X] T007 [P] Add architecture tests proving Claude paths, types, diagnostics, versions, and surface vocabulary occur only in the provider project, fixtures, review tooling, and provider documentation in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeProviderBoundaryContractTests.cs` (FR-003 through FR-005, FR-031)
- [X] T008 [P] Add manifest closure and canonical serialization tests for exact provider `2.1.220`, adapter, surface, definition, catalog, operation, projection, scope, and binding identities in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeProviderManifestContractTests.cs` (FR-001 through FR-004, FR-006, FR-007, FR-009, FR-022)
- [X] T009 [P] Add schema compilation, valid-record, malformed-record, and accepted-decision invariant tests for the isolated-machine review contract in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeMachineReviewSchemaContractTests.cs` (FR-024 through FR-026, FR-029)
- [X] T010 [P] Add uniqueness, stable metadata, trigger, safe-remediation, and generic-diagnostic reuse tests for `PKCLD0001` through `PKCLD0008` in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeDiagnosticCatalogContractTests.cs` (FR-027 through FR-029)
- [X] T011 Add fail-closed tests proving a rejected, missing, stale, or mismatched Feature 002 definition keeps the Claude support claim `not-evaluated` and blocks supported/admitted/release claims in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeSupportAdmissionContractTests.cs` (FR-001, FR-010, FR-022, FR-026)

### Provider foundations

- [X] T012 [P] Define the exact Claude provider, project-skill surface, adapter, catalog, conformance profile, and supported-version identities in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/ClaudeProviderIdentities.cs` (FR-002, FR-006, FR-007)
- [X] T013 [P] Embed the provider-owned machine-review schema at `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Schemas/isolated-machine-review.schema.json` and register its stable resource identity in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Schemas/ClaudeSchemaResources.cs` (FR-024, FR-025)
- [X] T014 [P] Implement the complete provider diagnostic catalog and safe typed entries in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Diagnostics/ClaudeDiagnosticCatalog.cs` (FR-027 through FR-029)
- [X] T015 Define the immutable exact provider manifest resource in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/claude-code-provider-manifest.json` with support defaulted to `not-evaluated` (FR-001 through FR-004, FR-006, FR-007, FR-009, FR-022)
- [X] T016 Implement manifest loading, schema validation, canonical identity binding, and exact dependency status evaluation in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/ClaudeProviderManifestLoader.cs` (FR-001, FR-002, FR-006, FR-007, FR-022)
- [X] T017 Implement a provider support admission evaluator that cannot upgrade the rejected Feature 002 dependency or incomplete live evidence in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Conformance/ClaudeSupportAdmissionEvaluator.cs` (FR-001, FR-022 through FR-026)
- [X] T018 Run the foundational Claude contract filters and record the commands, exact identities, and fail-closed upstream status in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: Claude-specific meaning is isolated, exact identities resolve once, schemas and diagnostics validate, and the rejected Feature 002 dependency makes support unavailable without changing upstream code.

---

## Phase 3: User Story 1 - Connect Claude Code to Program Kit (Priority: P1) - MVP

**Goal**: Explain, install, and verify one exact workspace-local Claude project skill through the existing neutral lifecycle, without touching settings, global state, provider installation, or any other provider.

**Independent Test**: In a clean isolated consumer workspace, use the packaged CLI to explain the exact Claude adapter, prove missing authority blocks changes, install after exact authority, and verify the byte-exact `.claude/skills/program-kit/SKILL.md` while support remains `not-evaluated` until upstream acceptance and live evidence exist.

### Tests first

- [ ] T019 [P] [US1] Add golden-byte, UTF-8/LF, YAML-front-matter, forbidden-field, ownership, and deterministic-permutation tests for `.claude/skills/program-kit/SKILL.md` in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeSkillProjectionContractTests.cs` (FR-009 through FR-014, FR-029, FR-030)
- [ ] T020 [P] [US1] Add provider adapter tests for exact manifest binding, projection descriptors, no global/provider mutation, collisions, and source-authoring refusal in `tests/ProgramKit.UnitTests/SessionIntegration/ClaudeCode/ClaudeSessionProviderAdapterTests.cs` (FR-002, FR-008 through FR-012, FR-034)
- [ ] T021 [P] [US1] Add CLI catalog/help/version tests proving explicit Claude registration without new lifecycle grammar or ambient selection in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeCliRegistrationContractTests.cs` (FR-002, FR-004, FR-006, FR-007)
- [ ] T022 [US1] Add packaged explain/install/verify acceptance tests for missing authority, exact authority, incompatible version, collision, idempotency, fresh-workspace repeatability, and exact record fields in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeInstallationAcceptanceTests.cs` (FR-006 through FR-013, FR-023, FR-030, FR-034, SC-001, SC-002, SC-007)

### Implementation

- [ ] T023 [US1] Implement deterministic canonical skill bytes from canonical guidance plus Claude-only syntax in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Projection/ClaudeSkillProjector.cs` (FR-009, FR-013 through FR-015, FR-017 through FR-019)
- [ ] T024 [US1] Implement the Claude `ISessionProviderAdapter` projection and provider observations without provider launching in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/ClaudeSessionProviderAdapter.cs` (FR-002, FR-003, FR-008 through FR-013, FR-023)
- [ ] T025 [US1] Register the adapter explicitly and expose its identities in help/version output in `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs` and `src/ProgramKit.Cli/Commands/HelpCommand.cs` (FR-002, FR-004, FR-006, FR-007)
- [ ] T026 [P] [US1] Add exact valid install/verify request and expected projection fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Valid/` (FR-006 through FR-010, FR-013)
- [ ] T027 [P] [US1] Add unsupported-version, mismatched-definition, missing-authority, source-authoring, collision, and stale-record fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Invalid/` and `tests/Fixtures/SessionIntegration/ClaudeCode/Colliding/` (FR-007, FR-010 through FR-012, FR-034)
- [ ] T028 [US1] Add deterministic ten-workspace packaged CLI proof with exact projection and record digest comparisons in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeInstallationRepeatabilityAcceptanceTests.cs` (SC-001, SC-002)
- [ ] T029 [US1] Run the US1 filters and record package identity, projection digest, ten installation identities, effect states, and the explicit `not-evaluated` support limitation in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: The exact Claude project skill can be installed and verified safely from a packaged CLI, but no live-provider or accepted-support claim is made.

---

## Phase 4: User Story 2 - Build Safely Through Claude Code (Priority: P2)

**Goal**: Project the canonical human-authority workflow and exact CLI binding so a Claude session can explain, construct, and evaluate without inventing meaning, authority, or success.

**Independent Test**: Evaluate the projected skill and normalized invocation against incomplete intent, missing/exact authority, construction results, read-only drift evaluation, and runtime-isolated generated software without starting Claude Code.

### Tests first

- [ ] T030 [P] [US2] Add guidance tests proving exact CLI resolution, version verification, explain-first behavior, bounded questions, no grant creation/reuse, read-only evaluation, separate remediation, stop cases, and typed-result authority in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeGuidanceContractTests.cs` (FR-013 through FR-019)
- [ ] T031 [P] [US2] Add Windows/Linux executable-plus-argument-array normalization tests with spaces, separators, working scope, request identity, operation, and JSON mode in `tests/ProgramKit.UnitTests/SessionIntegration/ClaudeCode/ClaudeInvocationBindingTests.cs` (FR-018, FR-020, FR-021)
- [ ] T032 [P] [US2] Add tests proving Claude process permission never becomes Program Kit effect authority and stale/mismatched/widened/reused grants remain blocked in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeAuthorityPreservationAcceptanceTests.cs` (FR-015 through FR-018, FR-021)
- [ ] T033 [US2] Add deterministic explain-to-construct-to-evaluate acceptance coverage preserving operation, input, scope, result, effect, diagnostics, evidence, receipts, and continuation in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeWorkflowAcceptanceTests.cs` (FR-014 through FR-019, FR-021, SC-004)
- [ ] T034 [P] [US2] Add runtime-isolation acceptance coverage for the generated reference application after all Program Kit, Spec Kit, Codex, Claude, adapter, skill, and authoring state is unavailable in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeRuntimeIsolationAcceptanceTests.cs` (FR-031, SC-008)

### Implementation

- [ ] T035 [US2] Implement safe exact executable and argument-array projection for factory and session operations in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Invocation/ClaudeInvocationBinding.cs` (FR-018, FR-020, FR-021)
- [ ] T036 [US2] Complete the canonical guidance projection in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Projection/ClaudeSkillProjector.cs` without scripts, permissions, dynamic commands, provider prose authority, or copied consumer semantics (FR-013 through FR-019, FR-029)
- [ ] T037 [P] [US2] Add valid workflow and incomplete-intent fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Valid/Guidance/` (FR-013 through FR-019)
- [ ] T038 [P] [US2] Add missing/stale/mismatched authority, drift-evaluation, transport, and unsupported-intent fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Invalid/Guidance/` (FR-015 through FR-019)
- [ ] T039 [US2] Run the US2 filters and record canonical request/result identities, authority outcomes, read-only workspace hashes, and runtime dependency closure in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: Deterministic evidence proves the Claude projection preserves the human-led workflow; actual Claude behavior remains an external observation.

---

## Phase 5: User Story 3 - Prove Cross-Provider Contract Portability (Priority: P3)

**Goal**: Evaluate direct CLI, neutral harness, Codex, and Claude fixtures against one canonical corpus without adding Claude meaning to neutral contracts.

**Independent Test**: Run every shared scenario through the four paths and compare canonical operation, scope, arguments, maximum/actual effect, outcome, disposition, diagnostics, artifacts, evidence, receipts, and continuation.

### Tests first

- [ ] T040 [P] [US3] Add conformance-profile contract tests for exact provider, adapter, definition, surface, corpus, invocation, result-preservation, provider-observation, and verdict fields in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeConformanceProfileContractTests.cs` (FR-020 through FR-023)
- [ ] T041 [P] [US3] Extend provider-neutrality assembly/schema inspection to prohibit Claude vocabulary in `ProgramKit.Contracts`, `ProgramKit.Kernel`, and `ProgramKit.SessionIntegration` in `tests/ProgramKit.ContractTests/ProviderNeutralityArchitectureTests.cs` (FR-003 through FR-005, FR-020)
- [ ] T042 [US3] Add direct-neutral-Codex-Claude semantic parity tests over the shared corpus, including provider-specific prerequisite diagnostics that cannot change the underlying result in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeProviderParityAcceptanceTests.cs` (FR-020 through FR-023, SC-004)
- [ ] T043 [P] [US3] Add semantic-loss, altered-argument, contaminated-output, contradictory-success, unavailable-version, and non-evaluated-live-review cases in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeConformanceNegativeAcceptanceTests.cs` (FR-021, FR-022, FR-026, SC-004, SC-005)

### Implementation

- [ ] T044 [US3] Define immutable provider observation, conformance case, live trial, summary, and review-record models in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Conformance/ClaudeConformanceModels.cs` (FR-020 through FR-026)
- [ ] T045 [US3] Implement the exact Claude conformance profile and neutral semantic comparison adapter in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Conformance/ClaudeConformanceProfile.cs` (FR-020 through FR-023)
- [ ] T046 [P] [US3] Add provider-specific invocation and observation fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Evidence/` (FR-020 through FR-026)
- [ ] T047 [P] [US3] Extend the shared conformance corpus only with provider-neutral cases required by the approved contract under `tests/Fixtures/SessionIntegration/Providers/Conformance/` (FR-020, FR-021)
- [ ] T048 [US3] Run all deterministic conformance modes and record corpus identity, parity results, provider-local differences, and explicit incompatible/not-evaluated cases in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: Provider-neutral meanings are preserved or fail with exact incompatibility; Claude-specific representations remain adapter-local.

---

## Phase 6: User Story 4 - Diagnose and Recover on the Isolated Machine (Priority: P4)

**Goal**: Return stable, safe Claude-specific diagnostics while keeping installation integrity, provider availability, provider permission, Program Kit authority, and live evidence separate.

**Independent Test**: Exercise every `PKCLD` trigger plus shared collision, drift, authority, publication, disclosure, and removal triggers and compare the complete structured result with safe golden evidence.

### Tests first

- [ ] T049 [P] [US4] Add golden operation-result tests for all eight `PKCLD` triggers and their interaction with generic diagnostics in `tests/ProgramKit.ContractTests/SessionIntegration/ClaudeCode/ClaudeDiagnosticGoldenContractTests.cs` (FR-027 through FR-030, SC-005)
- [ ] T050 [P] [US4] Add disclosure tests prohibiting credentials, provider output, transcripts, prompts, reasoning, physical protected paths, raw exceptions, and unsafe commands in `tests/ProgramKit.UnitTests/SessionIntegration/ClaudeCode/ClaudeDisclosureTests.cs` (FR-027, FR-029)
- [ ] T051 [US4] Add acceptance coverage distinguishing exact installation from `not-evaluated`, `reload-required`, `available`, and `unavailable` provider observations in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeAvailabilityAcceptanceTests.cs` (FR-013, FR-026 through FR-028)
- [ ] T052 [P] [US4] Add interrupted, partial, stale, contaminated-output, transport-change, contradictory-success, and isolated-boundary violation fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Invalid/Diagnostics/` (FR-022, FR-026 through FR-030)

### Implementation

- [ ] T053 [US4] Implement provider observation validation and exact mapping to `PKCLD0001` through `PKCLD0008` in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Diagnostics/ClaudeDiagnosticFactory.cs` (FR-027, FR-028)
- [ ] T054 [US4] Implement safe live-output classification boundaries that accept only bounded normalized fields and never persist raw provider output in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Conformance/ClaudeObservationClassifier.cs` (FR-025 through FR-029)
- [ ] T055 [US4] Run the US4 negative matrix and record diagnostic identities, actual effect states, disclosure audit, and bounded next-action classes in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: Expected provider failures are actionable without weakening generic diagnostics, disclosing unsafe data, or claiming readiness.

---

## Phase 7: User Story 5 - Remove Only the Claude Integration (Priority: P5)

**Goal**: Remove only exact admitted Claude-owned skill bytes through the existing neutral removal workflow while preserving parent directories and every independently managed artifact.

**Independent Test**: Install beside consumer-owned Claude material, alter and restore the owned skill across separate cases, remove with a fresh exact grant, and byte-compare all unrelated content and the independently installed CLI.

### Tests first

- [ ] T056 [P] [US5] Add exact, absent, drifted, adopted, missing, partial, and already-removed Claude lifecycle tests in `tests/ProgramKit.UnitTests/SessionIntegration/ClaudeCode/ClaudeRemovalTests.cs` (FR-032, FR-033)
- [ ] T057 [US5] Add packaged removal acceptance coverage proving only unchanged `.claude/skills/program-kit/SKILL.md` is removed and all parent directories, settings, other skills, CLI, provider, adapters, and lifecycle evidence are preserved in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeRemovalAcceptanceTests.cs` (FR-030, FR-032, FR-033, SC-006)

### Implementation and evidence

- [ ] T058 [P] [US5] Add exact, drifted, adopted, unrelated-state, absent, partial, and interrupted removal fixtures under `tests/Fixtures/SessionIntegration/ClaudeCode/Valid/Removal/`, `Drifted/Removal/`, and `Invalid/Removal/` (FR-032, FR-033)
- [ ] T059 [US5] Verify the Claude manifest and adapter declare only the exact skill file as generated-owned and delegate all journaling, grant, fingerprint, and preservation mechanics unchanged to the neutral lifecycle in `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/claude-code-provider-manifest.json` and `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/ClaudeSessionProviderAdapter.cs` (FR-030, FR-032, FR-033)
- [ ] T060 [US5] Run the US5 filters and record removed/preserved byte identities, lifecycle evidence, CLI availability, and drift outcomes in `specs/003-claude-code-adapter/verification.md`

**Checkpoint**: Removal is exact, reversible, and provider-local; it cannot delete consumer-owned containers or independently managed tools.

---

## Phase 8: Review Kit, Cross-Cutting Proof, and Honest Acceptance Gates

**Purpose**: Produce a sealed external-review path, finish deterministic repository proof, document the present limitation, and leave live/product acceptance blocked until its prerequisites are actually satisfied.

- [ ] T061 [P] Add deterministic sealed-kit export with exact file/package/schema/corpus/adapter/provider/catalog digests and no source, credentials, grants, transcripts, or provider output in `eng/Export-ClaudeCodeReviewKit.ps1` (FR-023 through FR-025, FR-029, SC-007)
- [ ] T062 [P] Add clean-boundary, kit-digest, runtime/OS, workspace, prior-state, CLI identity, and provider-version validation in `eng/ClaudeCodeReview/Initialize-ConsumerWorkspace.ps1` (FR-024, FR-025, FR-031, FR-034)
- [ ] T063 [P] Add ten-workspace installation, shared-corpus, negative-path, drift/removal, disclosure, and runtime-isolation execution using only the packaged CLI in `eng/ClaudeCodeReview/Invoke-DeterministicConsumerProof.ps1` (FR-023 through FR-025, FR-030 through FR-034, SC-001, SC-002, SC-004 through SC-008)
- [ ] T064 Add the sole opt-in Claude process launcher with exact `2.1.220` validation, normal `claude -p`, bounded JSON schema, ten fresh trials, independent Program Kit/effect evidence, and transient provider output in `eng/ClaudeCodeReview/Invoke-ClaudeCodeTrials.ps1` (FR-013, FR-024 through FR-029, SC-003, SC-009)
- [ ] T065 Add fail-closed human review completion that validates all mandatory evidence and cannot record `accepted` while Feature 002 is rejected, live trials are incomplete, or any mandatory verdict is not passed in `eng/ClaudeCodeReview/Complete-HumanReview.ps1` (FR-001, FR-024 through FR-026, SC-003, SC-009)
- [ ] T066 [P] Add unit/contract coverage for review-kit sealing, clean-boundary rejection, safe provider-output disposal, complete-trial cardinality, upstream rejection, and human-decision invariants in `tests/ProgramKit.AcceptanceTests/SessionIntegration/ClaudeCode/ClaudeReviewKitAcceptanceTests.cs` (FR-001, FR-024 through FR-029, SC-003, SC-007, SC-009)
- [ ] T067 Add Windows and Linux locked restore, build, test, pack, deterministic Claude conformance, review-kit export/validation, disclosure, and runtime-isolation jobs without launching Claude Code in `.github/workflows/vertical-slice.yml` (FR-005, FR-023, FR-026, FR-031)
- [ ] T068 [P] Update `README.md` with the implemented Claude adapter boundary, exact project-skill scope, independent CLI use, provider-neutral separation, runtime isolation, rejected Feature 002 dependency, and honest `not-evaluated` support status (FR-001 through FR-005, FR-026, FR-031)
- [ ] T069 [P] Add isolated-machine operator instructions, non-goals, external prerequisites, evidence safety, and blocked acceptance status to `eng/ClaudeCodeReview/README.md` and reconcile `specs/003-claude-code-adapter/quickstart.md` with the implemented commands (FR-005, FR-024 through FR-026, FR-029, SC-009)
- [ ] T070 Refresh and verify locked dependency closure in `src/ProgramKit.Cli/packages.lock.json`, `src/ProgramKit.SessionIntegration.Providers.ClaudeCode/packages.lock.json`, `tests/ProgramKit.UnitTests/packages.lock.json`, `tests/ProgramKit.ContractTests/packages.lock.json`, and `tests/ProgramKit.AcceptanceTests/packages.lock.json`
- [ ] T071 Run `dotnet restore --locked-mode`, `dotnet build --no-restore`, and `dotnet test --no-build`, then record complete deterministic commands, versions, counts, package/review-kit digests, limitations, and support status in `specs/003-claude-code-adapter/verification.md`
- [ ] T072 Run `eng/Export-ClaudeCodeReviewKit.ps1` twice from clean output roots and record byte-identical manifest/package/schema/corpus/script identities in `specs/003-claude-code-adapter/verification.md` (SC-007)
- [ ] T073 Confirm the generated reference application restores, builds, tests, and runs with all Program Kit, Spec Kit, Codex, Claude Code, adapter, session capability, source tree, and authoring state unavailable, then record the dependency/process proof in `specs/003-claude-code-adapter/verification.md` (FR-031, SC-008)
- [ ] T074 Record Feature 003 implementation status as deterministic adapter mechanics complete but provider support/product acceptance blocked by rejected Feature 002 and unexecuted live evidence in `specs/003-claude-code-adapter/verification.md` (FR-001, FR-026)
- [ ] T075 Obtain explicit human authority for external Claude execution and reviewer identity, transfer the sealed kit to a qualifying isolated machine, run exactly ten fresh Claude Code `2.1.220` trials, and import only schema-valid bounded evidence into `specs/003-claude-code-adapter/evidence/` (FR-024 through FR-026, FR-029, SC-003, SC-007, SC-009)
- [ ] T076 After Feature 002 has an accepted identity and T075 has complete passing evidence, obtain an independent human product decision and record the schema-valid review without inferring acceptance from tests in `specs/003-claude-code-adapter/evidence/isolated-machine-review.json` (FR-001, FR-024 through FR-026, SC-009)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational and supplies the adapter/projection used by later stories.
- **US2 (Phase 4)**: Depends on US1 projection and registration.
- **US3 (Phase 5)**: Depends on US1 and US2 so complete invocation/result meaning can be compared.
- **US4 (Phase 6)**: Depends on the manifest, conformance, and lifecycle paths from US1-US3.
- **US5 (Phase 7)**: Depends on US1 installation/ownership but is independently testable after that point.
- **Review/Proof (Phase 8)**: Deterministic tasks T061-T074 depend on the desired user stories; T075 additionally requires explicit live-provider authority and an isolated machine; T076 additionally requires accepted Feature 002 identity, complete T075 evidence, and an independent human decision.

### User Story Dependencies

- **US1** is the MVP and has no dependency on another Feature 003 story.
- **US2** consumes the US1 skill projection and invocation registration.
- **US3** compares the complete meanings established by US1 and US2.
- **US4** classifies failures across US1-US3 without changing their underlying results.
- **US5** reuses US1 ownership declarations and Feature 002's neutral removal mechanics.

### Parallel Opportunities

- Tasks marked `[P]` within a phase modify different files and can run concurrently after their phase prerequisites.
- Test tasks within one story can be written concurrently, but each must fail for the expected missing behavior before implementation.
- Fixture tasks can proceed beside implementation once their governing tests and contracts exist.
- US5 can proceed in parallel with US2-US4 after US1 is complete.
- Review-tool scripts T061-T063 can proceed in parallel after the deterministic product surface is stable; live T075-T076 cannot.

## Implementation Strategy

1. Establish the project and fail-closed dependency boundary.
2. Deliver US1 as the smallest deterministic adapter MVP.
3. Add the human-authority workflow, parity proof, diagnostics, and exact removal in priority order.
4. Complete deterministic review-kit and repository evidence without launching Claude Code.
5. Stop with support `not-evaluated` and acceptance blocked unless both the Feature 002 accepted dependency and explicit external live-review authority/evidence exist.

## Notes

- Feature 002 artifacts are immutable inputs to this feature; authority-closure remediation belongs to the later first-vertical-slice convergence feature.
- Green deterministic tests demonstrate adapter mechanics, not live Claude fitness or product acceptance.
- Provider installation, authentication, workspace trust, process permission, network, and external-machine state remain separately managed observations.
- No task may add settings, `CLAUDE.md`, plugins, MCP, hooks, global configuration, provider credentials, runtime coupling, provider-neutral Claude vocabulary, or speculative provider surfaces.

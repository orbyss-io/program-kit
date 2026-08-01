# Tasks: Status Component and API Vertical Slice

**Input**: Design documents from `specs/001-status-component-api/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, and `quickstart.md`

**Tests**: Tests are mandatory for this vertical slice because its product
promise depends on public-contract, negative-path, repeatability, publication,
and runtime-isolation evidence. Story tests are written before their
implementations and must initially fail for the intended reason.

**Organization**: Tasks are grouped by user story. Shared trust-boundary work is
limited to Setup and Foundational phases; consumer Status meaning remains under
`tests/Fixtures/Reference.Status/` or in generated consumer workspaces.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Safe to execute in parallel after its phase prerequisites because it
  changes different files and does not depend on another incomplete marked task.
- **[Story]**: Maps a task to one specification user story.
- Every task names the concrete file or directory it must create or change.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the exact, independently buildable .NET repository and
its four production and three proof boundaries.

- [X] T001 Pin SDK `10.0.302`, C# `14.0`, `net10.0`, nullable, deterministic compilation, warnings-as-errors, code style, and LF/UTF-8 policy in `global.json`, `Directory.Build.props`, and `.editorconfig`
- [X] T002 Define exact centrally managed package versions, locked-source policy, and deterministic governed dependency-mirror bootstrap/manifest in `Directory.Packages.props`, `NuGet.Config`, `eng/Bootstrap-DependencyMirror.ps1`, and `eng/dependency-mirror.manifest.json`
- [X] T003 Create the four production projects, three MSTest projects, fixed project-reference directions, and repository solution in `src/*/*.csproj`, `tests/ProgramKit.*Tests/*.csproj`, and `ProgramKit.slnx`
- [ ] T004 [P] Add repository build targets that reject floating package versions, forbidden production namespaces, and Program Kit/Spec Kit/AI references from generated consumers in `Directory.Build.targets`
- [ ] T005 [P] Add linked shared test sources for isolated workspaces, culture switching, deterministic environment setup, process capture, and exact-path cleanup without creating another project boundary in `tests/Shared/`
- [X] T006 Copy the accepted Draft 2020-12 contract schemas into embedded public resources without semantic edits in `src/ProgramKit.Contracts/Schemas/`
- [ ] T007 Create the reference fixture directory structure and ownership marker files in `tests/Fixtures/Reference.Status/Valid/`, `tests/Fixtures/Reference.Status/Invalid/`, and `tests/Fixtures/Reference.Status/Golden/`
- [X] T008 Restore every executable and test root, commit the resulting exact `packages.lock.json` files, and prove a second `dotnet restore ProgramKit.slnx --locked-mode` is clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the public types, exact byte/identity mechanics,
diagnostic result boundary, and thin CLI shell required by every story.

**CRITICAL**: No user-story implementation begins until this phase passes its
contract and architecture checks.

- [ ] T009 Implement immutable identity, digest, artifact, ownership, trace, safe-value, evidence, waiver, and gate primitives in `src/ProgramKit.Contracts/Identity/` and `src/ProgramKit.Contracts/Operations/CommonContracts.cs`
- [ ] T010 [P] Implement immutable command/operation request, inline result/explanation/continuation, change, diagnostic, inline-or-existing remediation, and catalog contracts with closed enums in `src/ProgramKit.Contracts/Operations/` and `src/ProgramKit.Contracts/Diagnostics/`
- [ ] T011 [P] Implement immutable provider manifest/SPI, exact selection, resolution lock, explanation, seam, and coverage contracts in `src/ProgramKit.Contracts/Providers/` and `src/ProgramKit.Contracts/Resolution/`
- [ ] T012 [P] Implement immutable candidate, publication journal, receipt, artifact-state, and workspace snapshot contracts in `src/ProgramKit.Contracts/Workspace/`
- [ ] T013 Implement the offline exact `$id`/digest schema registry and bounded `JsonSchema.Net` structural adapter in `src/ProgramKit.Kernel/Validation/SchemaRegistry.cs` and `src/ProgramKit.Kernel/Validation/StructuralSchemaValidator.cs`
- [X] T014 Implement strict duplicate-rejecting JSON parsing and `program-kit.canonical-json/v1` encoding, including unsigned UTF-16 key order, safe integers, string validation, and no BOM/whitespace/newline in `src/ProgramKit.Kernel/Canonicalization/`
- [ ] T015 [P] Implement SHA-256 qualified digests, typed collection identities, canonical logical-path normalization, and traversal/symlink/case/reserved-name collision checks in `src/ProgramKit.Kernel/Canonicalization/Digests.cs` and `src/ProgramKit.Kernel/Artifacts/LogicalPaths.cs`
- [ ] T016 Implement the exact kernel and .NET provider diagnostic catalogs, deterministic ordering/grouping/truncation, and disclosure classification in `src/ProgramKit.Contracts/Diagnostics/Catalogs/` and `src/ProgramKit.Kernel/Diagnostics/`
- [ ] T017 Implement the command-aware operation-result factory, command-specific inline payload invariants, optional bounded diagnostic artifact rules, outcome/effect/disposition invariants, canonical serialization, and dependency-minimal `PKINT0001` fallback serializer in `src/ProgramKit.Kernel/Operations/`
- [ ] T018 Implement the finite case-sensitive `explain|construct|evaluate|help|version` argument grammar and typed invocation model in `src/ProgramKit.Cli/Parsing/`
- [ ] T019 Implement JSON/text result renderers, stdout/stderr separation, outcome exit-code mapping, and `help`/`version` envelopes in `src/ProgramKit.Cli/Rendering/` and `src/ProgramKit.Cli/Commands/UtilityCommands.cs`
- [ ] T020 Implement the immutable exact first-party provider registry contracts and CLI composition root without assembly scanning in `src/ProgramKit.Kernel/Operations/ProviderRegistry.cs` and `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs`
- [ ] T021 [P] Add architecture tests for all allowed and forbidden project edges, absence of production `Reference.Status` semantics, three-role protocol closure, and generated-runtime forbidden references in `tests/ProgramKit.ContractTests/Architecture/ArchitectureBoundaryTests.cs`
- [ ] T022 [P] Add schema-profile, canonical JSON golden/adversarial, digest, logical-path, diagnostic catalog, ordering, truncation, redaction, and fallback tests in `tests/ProgramKit.ContractTests/Schemas/`, `tests/ProgramKit.ContractTests/Canonical/`, and `tests/ProgramKit.UnitTests/Kernel/`
- [ ] T023 Add black-box CLI grammar, JSON cleanliness, text fidelity, utility command, parse-failure, and exit-code tests against the public executable in `tests/ProgramKit.ContractTests/Cli/CliContractTests.cs`

**Checkpoint**: The repository builds independently and the public CLI returns
an honest structured refusal or utility result without invoking a provider.

---

## Phase 3: User Story 1 - Understand Integration Before Construction (Priority: P1) MVP

**Goal**: Resolve and explain the exact Status-component/API integration before
any live consumer write, while refusing missing, conflicting, ambiguous,
incompatible, or unavailable meaning.

**Independent Test**: Run the valid `explain` request twice and compare canonical
results, then run every explain-path invalid fixture. The valid result must
trace the complete intended integration with `effectState: none`; every invalid
result must be actionable and create no live artifacts.

### Tests and fixtures for User Story 1

- [ ] T024 [P] [US1] Author canonical valid component/API bundle, relationship, selection, request-bound approved evaluation context, authority, custom-source, and explain-request inputs in `tests/Fixtures/Reference.Status/Valid/`
- [ ] T025 [P] [US1] Author missing-selection, ambiguous-selection, conflicting-identity, incompatible-contract, unavailable-input, duplicate-key, and restricted-YAML rejection fixtures in `tests/Fixtures/Reference.Status/Invalid/`
- [ ] T026 [P] [US1] Add restricted-YAML/strict-JSON equivalence, rejection, resource-limit, typed-binding, semantic-completeness, and aggregate-needs-input tests in `tests/ProgramKit.UnitTests/Kernel/Intake/`
- [ ] T027 [P] [US1] Add exact provider-selection, authority, closure, relationship, seam, construction-identity, and no-implicit-fallback resolution tests in `tests/ProgramKit.UnitTests/Kernel/Resolution/`
- [ ] T028 [P] [US1] Add schema-valid golden Integration Resolution Explanation and trace-completeness tests in `tests/ProgramKit.ContractTests/Resolution/ExplanationContractTests.cs`
- [ ] T029 [US1] Add black-box valid/invalid `explain` acceptance tests proving repeatable bytes and zero live writes in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ExplainAcceptanceTests.cs`

### Implementation for User Story 1

- [ ] T030 [US1] Implement the bounded low-level `program-kit.restricted-yaml/v1` parser with explicit event rejection and safe source spans in `src/ProgramKit.Kernel/Intake/RestrictedYamlParser.cs`
- [ ] T031 [US1] Implement extension-selected YAML/JSON loading, neutral value projection, structural validation, and immutable typed binding in `src/ProgramKit.Kernel/Intake/IntakePipeline.cs` and `src/ProgramKit.Kernel/Validation/TypedContractBinder.cs`
- [ ] T032 [US1] Implement bundle/request semantic validators for identity integrity, traceability, completeness, ownership, selection, effect, continuation, and operation agreement in `src/ProgramKit.Kernel/Validation/SemanticValidator.cs`
- [ ] T033 [P] [US1] Implement the repository-record authority provider with exact request/lock/effect/freshness/revocation checks against the approved request-bound evaluation context and no ambient clock reads in `src/ProgramKit.Kernel/Authority/RepositoryAuthorityProvider.cs`
- [ ] T034 [P] [US1] Define exact intake, CShells component, ASP.NET assembler, and evaluation provider manifests plus distribution provenance in `src/ProgramKit.Providers.DotNet/Manifests/`
- [ ] T035 [US1] Implement fail-closed finite-closure resolution, provider/profile availability, relationship disposition, seam ownership, and deterministic resolution locks in `src/ProgramKit.Kernel/Resolution/ResolutionEngine.cs`
- [ ] T036 [US1] Implement the trace-complete Integration Resolution Explanation projector with bounded claims and planned ownership/claim classes in `src/ProgramKit.Kernel/Resolution/IntegrationExplanationBuilder.cs`
- [ ] T037 [US1] Implement the public explain operation pipeline and no-write effect guard in `src/ProgramKit.Kernel/Operations/ExplainOperation.cs`
- [ ] T038 [US1] Wire `explain` through the CLI composition root and write accepted canonical golden explanation/diagnostic fixtures in `src/ProgramKit.Cli/Commands/ExplainCommand.cs` and `tests/Fixtures/Reference.Status/Golden/explanation/`

**Checkpoint**: User Story 1 is a standalone usable MVP: an architect receives
one deterministic, authoritative integration decision before construction.

---

## Phase 4: User Story 2 - Construct an Independently Usable Component and API (Priority: P2)

**Goal**: Construct, evaluate, publish, and admit a packaged Status component
and separate API that integrates only through the exact local package and runs
as ordinary consumer-owned software.

**Independent Test**: Run the valid `construct` request in a clean workspace,
verify the complete admitted set and receipts, then relocate only generated
consumer outputs/declared feeds and prove locked restore, build, test, publish,
startup, and black-box Status behavior without this repository or Program Kit.

### Tests for User Story 2

- [ ] T039 [P] [US2] Add candidate lifecycle, immutable sealing, manifest ordering, ownership, mutation-after-seal, collision, and gate-closure tests in `tests/ProgramKit.UnitTests/Kernel/Artifacts/`
- [ ] T040 [P] [US2] Add endpoint contribution cardinality, duplicate-route, meaningful-order, exact-assembler, and order-independence tests in `tests/ProgramKit.UnitTests/Providers/HttpEndpoints/`
- [ ] T041 [P] [US2] Add exact CShells 0.0.28 generated-shape/ABI, explicit `WithAssemblies`, `MapShells`, and no-ambient-discovery conformance tests in `tests/ProgramKit.ContractTests/Providers/CShells028ConformanceTests.cs`
- [ ] T042 [P] [US2] Add local-feed/source-mapping, exact `[x.y.z]` binding, clean-cache locked restore, package/hash agreement, and external-output claim-class tests in `tests/ProgramKit.ContractTests/Providers/NuGetIntegrationContractTests.cs`
- [ ] T043 [US2] Add real-workspace happy-path construct acceptance tests for two bundles, package-only integration, complete artifacts/evidence, publication receipt-last admission, and black-box Status behavior in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ConstructAcceptanceTests.cs`

### Implementation for User Story 2

- [ ] T044 [P] [US2] Implement immutable endpoint contribution and one exact host assembler with explicit route identity, compatibility, cardinality, conflict, and ordering rules in `src/ProgramKit.Providers.DotNet/Composition/HttpEndpoints/`
- [ ] T045 [P] [US2] Implement deterministic whole-file project/source/config template rendering with seeded-handoff custom-source preservation in `src/ProgramKit.Providers.DotNet/Templates/` and `src/ProgramKit.Providers.DotNet/Construction/MsBuild/`
- [ ] T046 [US2] Implement the exact CShells 0.0.28 component feature and ASP.NET host activation projections, isolated from kernel meaning, in `src/ProgramKit.Providers.DotNet/Construction/CShells028/` and `src/ProgramKit.Providers.DotNet/Construction/AspNetCore/`
- [ ] T047 [P] [US2] Implement bounded external `dotnet` execution with explicit arguments, environment, timeouts, safe structured observations, and no raw-output disclosure in `src/ProgramKit.Providers.DotNet/Construction/DotNetToolRunner.cs`
- [ ] T048 [US2] Implement component generation/build/test/pack and record exact package SHA-256 plus NuGet content hash inside the isolated candidate in `src/ProgramKit.Providers.DotNet/Construction/NuGet/ComponentPackageBuilder.cs`
- [ ] T049 [US2] Implement the two-source local feed, package-source mapping, dependency mirror validation, clean relative cache, API sub-lock finalization, and exact package reference projection in `src/ProgramKit.Providers.DotNet/Construction/NuGet/LocalPackageIntegrator.cs`
- [ ] T050 [US2] Implement candidate draft creation, logical-path validation, complete ownership manifest, byte hashing, immutable sealing, rehash checks, and set digest in `src/ProgramKit.Kernel/Artifacts/CandidateArtifactSetBuilder.cs`
- [ ] T051 [US2] Implement mandatory candidate evaluation gates for contracts, build/test evidence, package agreement, ownership, support, provenance, canonical claim classes, and non-waivable admission closure in `src/ProgramKit.Kernel/Evaluation/CandidateEvaluator.cs`
- [ ] T052 [US2] Implement same-volume publication planning, cooperative workspace locking, durable journal transitions, canonically ordered writes/backups, and post-write byte verification in `src/ProgramKit.Kernel/Publication/RecoverablePublisher.cs`
- [ ] T053 [US2] Implement admission receipt-last semantics, exact receipt validation, and rejection of partial/interrupted/unverified candidates in `src/ProgramKit.Kernel/Publication/AdmissionService.cs`
- [ ] T054 [US2] Implement the construct operation orchestration through intake, resolution, explanation, providers, candidate evaluation, publication, verification, and admission in `src/ProgramKit.Kernel/Operations/ConstructOperation.cs`
- [ ] T055 [US2] Wire `construct` through the CLI and finalize valid construct/authority fixture digests plus package-mirror metadata in `src/ProgramKit.Cli/Commands/ConstructCommand.cs` and `tests/Fixtures/Reference.Status/Valid/`
- [ ] T056 [US2] Make the generated component/API fixture pass exact local restore, compile, tests, API startup, and status observation while containing no production Program Kit reference in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ConstructAcceptanceTests.cs`

**Checkpoint**: User Story 2 independently proves that Program Kit is a real
software factory and that its products do not carry the factory at runtime.

---

## Phase 5: User Story 3 - Recover Safely from Invalid Input and Drift (Priority: P3)

**Goal**: Return stable safe guidance for invalid, drifted, colliding,
interrupted, or internally faulted operations; evaluation never mutates and
repair is a separately authorized exact construction.

**Independent Test**: Exercise every invalid/drift/publication-fault fixture,
verify stable typed results and no unauthorized mutations, then apply the
generated exact repair request and prove only authorized generated-owned bytes
change.

### Tests and fixtures for User Story 3

- [ ] T057 [P] [US3] Complete duplicate-route, missing-assembler, ambiguous-order, unsafe-disclosure, generated-drift, live-collision, stale-precondition, interrupted-publication, and provider-failure fixtures in `tests/Fixtures/Reference.Status/Invalid/`
- [ ] T058 [P] [US3] Add catalog-trigger golden tests for all kernel and .NET provider diagnostic IDs, dispositions, typed remediations, continuation grouping, and safe expected/observed fields in `tests/ProgramKit.ContractTests/Diagnostics/DiagnosticBehaviorTests.cs`
- [ ] T059 [P] [US3] Add adversarial disclosure tests covering secrets, secret-derived digests, protected paths, unsafe commands, raw tool output, exceptions, stack traces, verbose text, progress, and fallback in `tests/ProgramKit.ContractTests/Diagnostics/DisclosureTests.cs`
- [ ] T060 [P] [US3] Add read-only exact/missing/modified/stale/colliding/interrupted/unsupported/unavailable evaluation tests in `tests/ProgramKit.UnitTests/Kernel/Evaluation/WorkspaceEvaluatorTests.cs`
- [ ] T061 [P] [US3] Add real-filesystem fault injection after each publication mutation boundary on Windows/Linux in `tests/ProgramKit.AcceptanceTests/Publication/PublicationRecoveryTests.cs`
- [ ] T062 [US3] Add drift/evaluate/no-mutation/repair/fresh-authority/consumer-preservation acceptance tests in `tests/ProgramKit.AcceptanceTests/VerticalSlice/RepairAcceptanceTests.cs`

### Implementation for User Story 3

- [ ] T063 [US3] Implement aggregate semantic/selection/authority diagnostics and stateless continuation artifacts with complete freshness revalidation in `src/ProgramKit.Kernel/Diagnostics/ContinuationBuilder.cs` and `src/ProgramKit.Kernel/Operations/OperationFailureBuilder.cs`
- [ ] T064 [US3] Implement read-only workspace evaluation against locks, receipts, evidence, ownership, support, and live bytes in `src/ProgramKit.Kernel/Evaluation/WorkspaceEvaluator.cs`
- [ ] T065 [US3] Implement typed bounded repair proposals and exact repair-request materialization without granting authority or mutating during evaluation in `src/ProgramKit.Kernel/Evaluation/RepairProposalBuilder.cs`
- [ ] T066 [US3] Implement complete/rollback publication recovery and repair precondition enforcement with no blind retry or consumer-owned overwrite in `src/ProgramKit.Kernel/Publication/PublicationRecovery.cs`
- [ ] T067 [US3] Implement provider-exception/external-output sanitization and route recoverable normal-pipeline failures through the independent fallback in `src/ProgramKit.Kernel/Diagnostics/DisclosureFilter.cs` and `src/ProgramKit.Cli/Program.cs`
- [ ] T068 [US3] Implement the public evaluate operation, wire `evaluate` and repair-mode `construct`, and ensure outcome exit codes remain result-derived in `src/ProgramKit.Kernel/Operations/EvaluateOperation.cs`, `src/ProgramKit.Cli/Commands/EvaluateCommand.cs`, and `src/ProgramKit.Cli/Commands/ConstructCommand.cs`

**Checkpoint**: User Story 3 proves that every recoverable path returns safe,
AI-usable guidance and that diagnosis never acquires repair authority.

---

## Phase 6: User Story 4 - Resume with a Trustworthy Workspace View (Priority: P4)

**Goal**: Give a new human contributor or AI session one deterministic scoped
view of the admitted construction, with traceable currentness and honest limits.

**Independent Test**: Construct a valid workspace and inspect only the snapshot
plus its references; then change identity/evidence/artifact state and verify the
view is detected as stale or drifted and directs custom-behavior debugging to
consumer-owned source.

### Tests for User Story 4

- [ ] T069 [P] [US4] Add snapshot schema/golden/trace-completeness, canonical ordering, and no-inferred-meaning contract tests in `tests/ProgramKit.ContractTests/Workspace/WorkspaceSnapshotContractTests.cs`
- [ ] T070 [P] [US4] Add current/stale/drifted/unsupported/unavailable/incomplete snapshot state tests in `tests/ProgramKit.UnitTests/Kernel/Evaluation/WorkspaceSnapshotFreshnessTests.cs`
- [ ] T071 [US4] Add fresh-session orientation acceptance tests using only the snapshot and referenced authority records in `tests/ProgramKit.AcceptanceTests/VerticalSlice/WorkspaceOrientationTests.cs`

### Implementation for User Story 4

- [ ] T072 [US4] Implement the canonical workspace snapshot projector from authoritative locks, manifests, evidence, gates, reviews, receipts, support, retention, and diagnostics in `src/ProgramKit.Kernel/Evidence/WorkspaceSnapshotBuilder.cs`
- [ ] T073 [US4] Publish `.program-kit/workspace.snapshot.json` before final admission receipt binding and expose it through construct results in `src/ProgramKit.Kernel/Operations/ConstructOperation.cs`
- [ ] T074 [US4] Recompute closure/evidence/live-state bindings during evaluation and report stale/drifted snapshot status without rewriting it in `src/ProgramKit.Kernel/Operations/EvaluateOperation.cs`
- [ ] T075 [US4] Write canonical snapshot golden fixtures and an offline source-navigation note for custom behavior in `tests/Fixtures/Reference.Status/Golden/snapshot/`

**Checkpoint**: All four stories are independently testable through public
contracts; the snapshot accelerates orientation without becoming source truth.

---

## Phase 7: Product Proof and Cross-Cutting Completion

**Purpose**: Close the constitutional evidence obligations that span stories,
prove fresh-consumer usability, and document only what is actually true.

- [ ] T076 [P] Add path/culture/input/provider/contribution/filesystem/scheduling-order repeatability matrices and canonical-byte comparisons in `tests/ProgramKit.AcceptanceTests/Repeatability/RepeatabilityTests.cs`
- [ ] T077 [P] Add external `.nupkg` verified-equivalence tests and upgrade its claim only if exact SDK `10.0.302` fixtures prove byte identity in `tests/ProgramKit.AcceptanceTests/Repeatability/PackageVerifierTests.cs`
- [ ] T078 Add relocated clean-cache locked restore/build/test/publish, assets/deps/PE allowlisting, process startup, and black-box Status runtime-isolation proof in `tests/ProgramKit.AcceptanceTests/RuntimeIsolation/RuntimeIsolationTests.cs`
- [ ] T079 [P] Add offline/local-source-only, no-telemetry/source-upload, secret scanning, no-self-host bootstrap, dependency/source/lock drift tests, and an explicit Windows/Linux proof matrix in `tests/ProgramKit.ContractTests/Security/LocalSafetyTests.cs` and `.github/workflows/vertical-slice.yml`
- [ ] T080 [P] Generate deterministic distribution manifest, dependency inventory/SBOM, source/package provenance, diagnostic catalog digests, and exact provider support metadata in `eng/Generate-DistributionEvidence.ps1` and `artifacts/evidence/`
- [ ] T081 Add performance assertions for the two-bundle finite closure and sub-two-second local `explain` path in `tests/ProgramKit.AcceptanceTests/VerticalSlice/PerformanceAcceptanceTests.cs`
- [ ] T082 Automate the documented valid/invalid/repeatability/drift/repair walkthrough without ambient setup in `eng/Invoke-VerticalSliceQuickstart.ps1` and reconcile `specs/001-status-component-api/quickstart.md` with the executable flow
- [X] T083 Prepare the fresh-contributor one-hour product-review record with automated timing evidence, the seven architecture questions, every honest limitation, and an explicit pending human-approval gate that must not be reported as passed without an independent reviewer in `specs/001-status-component-api/reviews/first-vertical-slice.md`
- [X] T084 Reconcile `README.md` with the accepted constitution, implemented CLI behavior, archived-history boundary, current branch/main state, known limitations, and exact contributor entry points
- [ ] T085 Run locked restore, release build, all tests, schema validation, generated-consumer runtime isolation, quickstart automation, formatting, and clean-worktree checks; record the exact verification commands and results in `specs/001-status-component-api/verification.md`

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)** has no dependencies.
- **Foundational (Phase 2)** depends on Setup and blocks all user stories.
- **US1 (Phase 3)** depends on Foundational and establishes accepted resolution,
  explanation, and valid reference identities used by construction.
- **US2 (Phase 4)** depends on US1 because construction must use the exact lock
  and explanation path rather than a second private resolution path.
- **US3 (Phase 5)** depends on US2 because drift, interruption, and repair need
  real admitted artifacts and publication state.
- **US4 (Phase 6)** depends on US2 for admitted records and on US3 for honest
  stale/drifted diagnostic state.
- **Product Proof (Phase 7)** depends on all selected stories.

### User-story dependency graph

```text
Setup -> Foundation -> US1 Explain -> US2 Construct -> US3 Diagnose/Repair
                                             |                 |
                                             +-------> US4 Workspace View
                                                               |
                                             Product Proof <---+
```

The stories remain independently testable at their checkpoints even though the
real factory state used by later stories is intentionally cumulative.

### Within each user story

- Author prerequisite fixtures, then write contract/unit/acceptance tests and
  confirm they fail for the intended missing behavior.
- Implement typed contracts/adapters before kernel orchestration.
- Keep provider construction behind exact public SPI boundaries.
- Complete public CLI wiring before declaring the story checkpoint complete.
- Never parallelize publication, admission, or repair across an unestablished
  ownership/precondition dependency.

## Parallel Opportunities

### User Story 1

After T023, T024-T028 may proceed in parallel. Once those failing proofs exist,
T033 and T034 may proceed in parallel before T035-T038 serialize resolution and
public CLI integration.

### User Story 2

After US1, T039-T042 may proceed in parallel. T044, T045, and T047 change
separate provider areas and may proceed together; T046 then binds the generated
shape, followed by the ordered package/candidate/publication chain T048-T056.

### User Story 3

T057-T061 may proceed in parallel after an admitted US2 workspace is available.
T063-T067 affect separate kernel concerns where marked, while T068 performs the
final public operation integration.

### User Story 4

T069 and T070 may proceed in parallel; T071 is written before T072-T075 and
remains the independent contributor-orientation proof.

## Implementation Strategy

### MVP first

1. Complete Setup and Foundational phases.
2. Complete US1 and demonstrate deterministic, no-write integration resolution.
3. Stop only if US1 reveals a material semantic, authority, contract, or
   determinism ambiguity; return that issue to the spec/plan instead of guessing.

### Incremental delivery

1. **US1** proves the central governed-integration promise.
2. **US2** proves tangible package-based software construction and runtime
   independence.
3. **US3** proves safe long-lived maintenance behavior without implicit repair.
4. **US4** proves trustworthy cross-session orientation.
5. **Product Proof** closes repeatability, safety, provenance, documentation,
   performance, and human-review obligations.

## Completion Rules

- A checked task must have its named code/artifact and directly affected proof.
- A green test is evidence of execution, not approval of product meaning.
- No Program Kit integration/self-host check is required for this redesign; the
  independent standard .NET/Spec Kit bootstrap is authoritative.
- No task may introduce native planning, runtime Program Kit, migration,
  marketplace, dynamic third-party execution, multi-ecosystem generation, or a
  generalized semantic engine.
- If implementation exposes material ambiguity, changed authority, unsupported
  determinism, broadened effects, or a constitutional conflict, stop and return
  to specification/planning rather than silently widening this list.

---

## Phase 8: Convergence

**Purpose**: Reconcile the implemented reference slice with its original
contract, close constitutional trust gaps, and make the independent human
product decision possible without inferring acceptance from green automation.

- [ ] T086 CRITICAL Replace Boolean/window authority with an exact grant bound to request, operation closure, requested effect, evaluation context, freshness, review, and revocation state, with fail-closed adversarial tests, per FR-003, FR-004, FR-017, and Constitution I (partial)
- [ ] T087 CRITICAL Route public operations through the versioned factory-request contract, complete offline Draft 2020-12 structural and typed semantic validation, remove provider-specific intake ownership from the kernel, and aggregate independently known missing input per FR-001 through FR-003, FR-008, and Constitution III (partial)
- [ ] T088 CRITICAL Add callable intake-mapping, construction, and evaluation provider SPI surfaces plus exact role/support admission so a provider cannot advertise an unimplemented role, per FR-008, FR-030, the plan three-role decision, and Constitution VI (contradicts)
- [ ] T089 CRITICAL Complete candidate gate closure, exact support/provenance/evidence evaluation, live-precondition rechecks, publication fault recovery, and receipt-last admission so partial or interrupted state cannot be trusted, per FR-014, FR-015, FR-018, and Constitutions IV and V (partial)
- [ ] T090 Complete read-only exact, missing, modified, stale, colliding, interrupted, unsupported, and unavailable evaluation plus separately authorized ownership-safe repair and publication recovery, per FR-016, FR-017, and US3 (partial)
- [ ] T091 CRITICAL Make fallback effect reporting depend on the furthest proven lifecycle state and complete result, diagnostic-trigger, disclosure, truncation, continuation, and remediation contract tests, per FR-019 through FR-025 and Constitution VII (contradicts)
- [ ] T092 Project the workspace snapshot only from authoritative closure, identity, relationship, seam, artifact, provenance, gate, review, waiver, evidence, receipt, support, retention, and diagnostic records, and recompute freshness without mutation, per FR-026 through FR-028 and US4 (partial)
- [ ] T093 Complete the declared invalid, repair, publication-fault, path/culture/order, package-claim, provenance/SBOM, performance, hostile-filesystem, local-safety, no-self-host, and relocated-runtime proof matrix, per FR-018, FR-029, FR-031, FR-032, FR-034, and SC-004 through SC-010 (partial)
- [X] T094 Reconcile every original T001-T085 checkbox against its named artifact and direct proof, retain unchecked status wherever proof is absent, and update README plus verification with only current evidence, per the Spec Kit workflow and Constitution IX (partial)
- [ ] T095 CRITICAL After T086-T094 and all applicable deterministic gates pass, obtain an independent human product accept/reject decision and record its exact scope, reviewer identity, evidence binding, limitations, and date without deriving acceptance from automation, per Constitutions I and IX (missing)

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
- [ ] T004 [P] Add repository build targets that reject floating package versions, forbidden production namespaces, and Program Kit/Spec Kit/AI references from generated consumers in `Directory.Build.targets` (superseded: accepted outcome is proven through the consolidated boundary cited in the task-closure audit)
- [X] T005 [P] Add linked shared test sources for isolated workspaces, culture switching, deterministic environment setup, process capture, and exact-path cleanup without creating another project boundary in `tests/Shared/`
- [X] T006 Copy the accepted Draft 2020-12 contract schemas into embedded public resources without semantic edits in `src/ProgramKit.Contracts/Schemas/`
- [ ] T007 Create the reference fixture directory structure and ownership marker files in `tests/Fixtures/Reference.Status/Valid/`, `tests/Fixtures/Reference.Status/Invalid/`, and `tests/Fixtures/Reference.Status/Golden/` (superseded: accepted outcome is proven through the consolidated boundary cited in the task-closure audit)
- [X] T008 Restore every executable and test root, commit the resulting exact `packages.lock.json` files, and prove a second `dotnet restore ProgramKit.slnx --locked-mode` is clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the public types, exact byte/identity mechanics,
diagnostic result boundary, and thin CLI shell required by every story.

**CRITICAL**: No user-story implementation begins until this phase passes its
contract and architecture checks.

- [X] T009 Implement immutable identity, digest, artifact, ownership, trace, safe-value, evidence, waiver, and gate primitives in `src/ProgramKit.Contracts/Identity/` and `src/ProgramKit.Contracts/Operations/CommonContracts.cs`
- [X] T010 [P] Implement immutable command/operation request, inline result/explanation/continuation, change, diagnostic, inline-or-existing remediation, and catalog contracts with closed enums in `src/ProgramKit.Contracts/Operations/` and `src/ProgramKit.Contracts/Diagnostics/`
- [X] T011 [P] Implement immutable provider manifest/SPI, exact selection, resolution lock, explanation, seam, and coverage contracts in `src/ProgramKit.Contracts/Providers/` and `src/ProgramKit.Contracts/Resolution/`
- [X] T012 [P] Implement immutable candidate, publication journal, receipt, artifact-state, and workspace snapshot contracts in `src/ProgramKit.Contracts/Workspace/`
- [X] T013 Implement the offline exact `$id`/digest schema registry and bounded `JsonSchema.Net` structural adapter in `src/ProgramKit.Kernel/Validation/SchemaRegistry.cs` and `src/ProgramKit.Kernel/Validation/StructuralSchemaValidator.cs`
- [X] T014 Implement strict duplicate-rejecting JSON parsing and `program-kit.canonical-json/v1` encoding, including unsigned UTF-16 key order, safe integers, string validation, and no BOM/whitespace/newline in `src/ProgramKit.Kernel/Canonicalization/`
- [X] T015 [P] Implement SHA-256 qualified digests, typed collection identities, canonical logical-path normalization, and traversal/symlink/case/reserved-name collision checks in `src/ProgramKit.Kernel/Canonicalization/Digests.cs` and `src/ProgramKit.Kernel/Artifacts/LogicalPaths.cs`
- [X] T016 Implement the exact kernel and .NET provider diagnostic catalogs, deterministic ordering/grouping/truncation, and disclosure classification in `src/ProgramKit.Contracts/Diagnostics/Catalogs/` and `src/ProgramKit.Kernel/Diagnostics/`
- [X] T017 Implement the command-aware operation-result factory, command-specific inline payload invariants, optional bounded diagnostic artifact rules, outcome/effect/disposition invariants, canonical serialization, and dependency-minimal `PKINT0001` fallback serializer in `src/ProgramKit.Kernel/Operations/`
- [X] T018 Implement the finite case-sensitive `explain|construct|evaluate|help|version` argument grammar and typed invocation model in `src/ProgramKit.Cli/Parsing/`
- [X] T019 Implement JSON/text result renderers, stdout/stderr separation, outcome exit-code mapping, and `help`/`version` envelopes in `src/ProgramKit.Cli/Rendering/` and `src/ProgramKit.Cli/Commands/UtilityCommands.cs`
- [X] T020 Implement the immutable exact first-party provider registry contracts and CLI composition root without assembly scanning in `src/ProgramKit.Kernel/Operations/ProviderRegistry.cs` and `src/ProgramKit.Cli/Composition/ProgramKitComposition.cs`
- [X] T021 [P] Add architecture tests for all allowed and forbidden project edges, absence of production `Reference.Status` semantics, three-role protocol closure, and generated-runtime forbidden references in `tests/ProgramKit.ContractTests/Architecture/ArchitectureBoundaryTests.cs`
- [X] T022 [P] Add schema-profile, canonical JSON golden/adversarial, digest, logical-path, diagnostic catalog, ordering, truncation, redaction, and fallback tests in `tests/ProgramKit.ContractTests/Schemas/`, `tests/ProgramKit.ContractTests/Canonical/`, and `tests/ProgramKit.UnitTests/Kernel/`
- [X] T023 Add black-box CLI grammar, JSON cleanliness, text fidelity, utility command, parse-failure, and exit-code tests against the public executable in `tests/ProgramKit.ContractTests/Cli/CliContractTests.cs`

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

- [X] T024 [P] [US1] Author canonical valid component/API bundle, relationship, selection, request-bound approved evaluation context, authority, custom-source, and explain-request inputs in `tests/Fixtures/Reference.Status/Valid/`
- [X] T025 [P] [US1] Author missing-selection, ambiguous-selection, conflicting-identity, incompatible-contract, unavailable-input, duplicate-key, and restricted-YAML rejection fixtures in `tests/Fixtures/Reference.Status/Invalid/`
- [X] T026 [P] [US1] Add restricted-YAML/strict-JSON equivalence, rejection, resource-limit, typed-binding, semantic-completeness, and aggregate-needs-input tests in `tests/ProgramKit.UnitTests/Kernel/Intake/`
- [X] T027 [P] [US1] Add exact provider-selection, authority, closure, relationship, seam, construction-identity, and no-implicit-fallback resolution tests in `tests/ProgramKit.UnitTests/Kernel/Resolution/`
- [X] T028 [P] [US1] Add schema-valid golden Integration Resolution Explanation and trace-completeness tests in `tests/ProgramKit.ContractTests/Resolution/ExplanationContractTests.cs`
- [X] T029 [US1] Add black-box valid/invalid `explain` acceptance tests proving repeatable bytes and zero live writes in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ExplainAcceptanceTests.cs`

### Implementation for User Story 1

- [X] T030 [US1] Implement the bounded low-level `program-kit.restricted-yaml/v1` parser with explicit event rejection and safe source spans in `src/ProgramKit.Kernel/Intake/RestrictedYamlParser.cs`
- [X] T031 [US1] Implement extension-selected YAML/JSON loading, neutral value projection, structural validation, and immutable typed binding in `src/ProgramKit.Kernel/Intake/IntakePipeline.cs` and `src/ProgramKit.Kernel/Validation/TypedContractBinder.cs`
- [ ] T032 [US1] Implement bundle/request semantic validators for identity integrity, traceability, completeness, ownership, selection, effect, continuation, and operation agreement in `src/ProgramKit.Kernel/Validation/SemanticValidator.cs` (superseded: accepted outcome is proven through the consolidated boundary cited in the task-closure audit)
- [X] T033 [P] [US1] Implement the repository-record authority provider with exact request/lock/effect/freshness/revocation checks against the approved request-bound evaluation context and no ambient clock reads in `src/ProgramKit.Kernel/Authority/RepositoryAuthorityProvider.cs`
- [X] T034 [P] [US1] Define exact intake, CShells component, ASP.NET assembler, and evaluation provider manifests plus distribution provenance in `src/ProgramKit.Providers.DotNet/Manifests/`
- [X] T035 [US1] Implement fail-closed finite-closure resolution, provider/profile availability, relationship disposition, seam ownership, and deterministic resolution locks in `src/ProgramKit.Kernel/Resolution/ResolutionEngine.cs`
- [ ] T036 [US1] Implement the trace-complete Integration Resolution Explanation projector with bounded claims and planned ownership/claim classes in `src/ProgramKit.Kernel/Resolution/IntegrationExplanationBuilder.cs` (superseded: accepted outcome is proven through the consolidated boundary cited in the task-closure audit)
- [X] T037 [US1] Implement the public explain operation pipeline and no-write effect guard in `src/ProgramKit.Kernel/Operations/ExplainOperation.cs`
- [X] T038 [US1] Wire `explain` through the CLI composition root and write accepted canonical golden explanation/diagnostic fixtures in `src/ProgramKit.Cli/Commands/ExplainCommand.cs` and `tests/Fixtures/Reference.Status/Golden/explanation/`

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

- [X] T039 [P] [US2] Add candidate lifecycle, immutable sealing, manifest ordering, ownership, mutation-after-seal, collision, and gate-closure tests in `tests/ProgramKit.UnitTests/Kernel/Artifacts/`
- [X] T040 [P] [US2] Add endpoint contribution cardinality, duplicate-route, meaningful-order, exact-assembler, and order-independence tests in `tests/ProgramKit.UnitTests/Providers/HttpEndpoints/`
- [X] T041 [P] [US2] Add exact CShells 0.0.28 generated-shape/ABI, explicit `WithAssemblies`, `MapShells`, and no-ambient-discovery conformance tests in `tests/ProgramKit.ContractTests/Providers/CShells028ConformanceTests.cs`
- [X] T042 [P] [US2] Add local-feed/source-mapping, exact `[x.y.z]` binding, clean-cache locked restore, package/hash agreement, and external-output claim-class tests in `tests/ProgramKit.ContractTests/Providers/NuGetIntegrationContractTests.cs`
- [X] T043 [US2] Add real-workspace happy-path construct acceptance tests for two bundles, package-only integration, complete artifacts/evidence, publication receipt-last admission, and black-box Status behavior in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ConstructAcceptanceTests.cs`

### Implementation for User Story 2

- [X] T044 [P] [US2] Implement immutable endpoint contribution and one exact host assembler with explicit route identity, compatibility, cardinality, conflict, and ordering rules in `src/ProgramKit.Providers.DotNet/Composition/HttpEndpoints/`
- [X] T045 [P] [US2] Implement deterministic whole-file project/source/config template rendering with seeded-handoff custom-source preservation in `src/ProgramKit.Providers.DotNet/Templates/` and `src/ProgramKit.Providers.DotNet/Construction/MsBuild/`
- [ ] T046 [US2] Implement the exact CShells 0.0.28 component feature and ASP.NET host activation projections, isolated from kernel meaning, in `src/ProgramKit.Providers.DotNet/Construction/CShells028/` and `src/ProgramKit.Providers.DotNet/Construction/AspNetCore/` (superseded: accepted outcome is proven through the consolidated boundary cited in the task-closure audit)
- [X] T047 [P] [US2] Implement bounded external `dotnet` execution with explicit arguments, environment, timeouts, safe structured observations, and no raw-output disclosure in `src/ProgramKit.Providers.DotNet/Construction/DotNetToolRunner.cs`
- [X] T048 [US2] Implement component generation/build/test/pack and record exact package SHA-256 plus NuGet content hash inside the isolated candidate in `src/ProgramKit.Providers.DotNet/Construction/NuGet/ComponentPackageBuilder.cs`
- [X] T049 [US2] Implement the two-source local feed, package-source mapping, dependency mirror validation, clean relative cache, API sub-lock finalization, and exact package reference projection in `src/ProgramKit.Providers.DotNet/Construction/NuGet/LocalPackageIntegrator.cs`
- [X] T050 [US2] Implement candidate draft creation, logical-path validation, complete ownership manifest, byte hashing, immutable sealing, rehash checks, and set digest in `src/ProgramKit.Kernel/Artifacts/CandidateArtifactSetBuilder.cs`
- [X] T051 [US2] Implement mandatory candidate evaluation gates for contracts, build/test evidence, package agreement, ownership, support, provenance, canonical claim classes, and non-waivable admission closure in `src/ProgramKit.Kernel/Evaluation/CandidateEvaluator.cs`
- [X] T052 [US2] Implement same-volume publication planning, cooperative workspace locking, durable journal transitions, canonically ordered writes/backups, and post-write byte verification in `src/ProgramKit.Kernel/Publication/RecoverablePublisher.cs`
- [X] T053 [US2] Implement admission receipt-last semantics, exact receipt validation, and rejection of partial/interrupted/unverified candidates in `src/ProgramKit.Kernel/Publication/AdmissionService.cs`
- [X] T054 [US2] Implement the construct operation orchestration through intake, resolution, explanation, providers, candidate evaluation, publication, verification, and admission in `src/ProgramKit.Kernel/Operations/ConstructOperation.cs`
- [X] T055 [US2] Wire `construct` through the CLI and finalize valid construct/authority fixture digests plus package-mirror metadata in `src/ProgramKit.Cli/Commands/ConstructCommand.cs` and `tests/Fixtures/Reference.Status/Valid/`
- [X] T056 [US2] Make the generated component/API fixture pass exact local restore, compile, tests, API startup, and status observation while containing no production Program Kit reference in `tests/ProgramKit.AcceptanceTests/VerticalSlice/ConstructAcceptanceTests.cs`

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

- [X] T057 [P] [US3] Complete duplicate-route, missing-assembler, ambiguous-order, unsafe-disclosure, generated-drift, live-collision, stale-precondition, interrupted-publication, and provider-failure fixtures in `tests/Fixtures/Reference.Status/Invalid/`
- [X] T058 [P] [US3] Add catalog-trigger golden tests for all kernel and .NET provider diagnostic IDs, dispositions, typed remediations, continuation grouping, and safe expected/observed fields in `tests/ProgramKit.ContractTests/Diagnostics/DiagnosticBehaviorTests.cs`
- [X] T059 [P] [US3] Add adversarial disclosure tests covering secrets, secret-derived digests, protected paths, unsafe commands, raw tool output, exceptions, stack traces, verbose text, progress, and fallback in `tests/ProgramKit.ContractTests/Diagnostics/DisclosureTests.cs`
- [X] T060 [P] [US3] Add read-only exact/missing/modified/stale/colliding/interrupted/unsupported/unavailable evaluation tests in `tests/ProgramKit.UnitTests/Kernel/Evaluation/WorkspaceEvaluatorTests.cs`
- [X] T061 [P] [US3] Add real-filesystem fault injection after each publication mutation boundary on Windows/Linux in `tests/ProgramKit.AcceptanceTests/Publication/PublicationRecoveryTests.cs`
- [X] T062 [US3] Add drift/evaluate/no-mutation/repair/fresh-authority/consumer-preservation acceptance tests in `tests/ProgramKit.AcceptanceTests/VerticalSlice/RepairAcceptanceTests.cs`

### Implementation for User Story 3

- [X] T063 [US3] Implement aggregate semantic/selection/authority diagnostics and stateless continuation artifacts with complete freshness revalidation in `src/ProgramKit.Kernel/Diagnostics/ContinuationBuilder.cs` and `src/ProgramKit.Kernel/Operations/OperationFailureBuilder.cs`
- [X] T064 [US3] Implement read-only workspace evaluation against locks, receipts, evidence, ownership, support, and live bytes in `src/ProgramKit.Kernel/Evaluation/WorkspaceEvaluator.cs`
- [X] T065 [US3] Implement typed bounded repair proposals and exact repair-request materialization without granting authority or mutating during evaluation in `src/ProgramKit.Kernel/Evaluation/RepairProposalBuilder.cs`
- [X] T066 [US3] Implement complete/rollback publication recovery and repair precondition enforcement with no blind retry or consumer-owned overwrite in `src/ProgramKit.Kernel/Publication/PublicationRecovery.cs`
- [X] T067 [US3] Implement provider-exception/external-output sanitization and route recoverable normal-pipeline failures through the independent fallback in `src/ProgramKit.Kernel/Diagnostics/DisclosureFilter.cs` and `src/ProgramKit.Cli/Program.cs`
- [X] T068 [US3] Implement the public evaluate operation, wire `evaluate` and repair-mode `construct`, and ensure outcome exit codes remain result-derived in `src/ProgramKit.Kernel/Operations/EvaluateOperation.cs`, `src/ProgramKit.Cli/Commands/EvaluateCommand.cs`, and `src/ProgramKit.Cli/Commands/ConstructCommand.cs`

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

- [X] T069 [P] [US4] Add snapshot schema/golden/trace-completeness, canonical ordering, and no-inferred-meaning contract tests in `tests/ProgramKit.ContractTests/Workspace/WorkspaceSnapshotContractTests.cs`
- [X] T070 [P] [US4] Add current/stale/drifted/unsupported/unavailable/incomplete snapshot state tests in `tests/ProgramKit.UnitTests/Kernel/Evaluation/WorkspaceSnapshotFreshnessTests.cs`
- [X] T071 [US4] Add fresh-session orientation acceptance tests using only the snapshot and referenced authority records in `tests/ProgramKit.AcceptanceTests/VerticalSlice/WorkspaceOrientationTests.cs`

### Implementation for User Story 4

- [X] T072 [US4] Implement the canonical workspace snapshot projector from authoritative locks, manifests, evidence, gates, reviews, receipts, support, retention, and diagnostics in `src/ProgramKit.Kernel/Evidence/WorkspaceSnapshotBuilder.cs`
- [X] T073 [US4] Publish `.program-kit/workspace.snapshot.json` before final admission receipt binding and expose it through construct results in `src/ProgramKit.Kernel/Operations/ConstructOperation.cs`
- [X] T074 [US4] Recompute closure/evidence/live-state bindings during evaluation and report stale/drifted snapshot status without rewriting it in `src/ProgramKit.Kernel/Operations/EvaluateOperation.cs`
- [X] T075 [US4] Write canonical snapshot golden fixtures and an offline source-navigation note for custom behavior in `tests/Fixtures/Reference.Status/Golden/snapshot/`

**Checkpoint**: All four stories are independently testable through public
contracts; the snapshot accelerates orientation without becoming source truth.

---

## Phase 7: Product Proof and Cross-Cutting Completion

**Purpose**: Close the constitutional evidence obligations that span stories,
prove fresh-consumer usability, and document only what is actually true.

- [X] T076 [P] Add path/culture/input/provider/contribution/filesystem/scheduling-order repeatability matrices and canonical-byte comparisons in `tests/ProgramKit.AcceptanceTests/Repeatability/RepeatabilityTests.cs`
- [X] T077 [P] Add external `.nupkg` verified-equivalence tests and upgrade its claim only if exact SDK `10.0.302` fixtures prove byte identity in `tests/ProgramKit.AcceptanceTests/Repeatability/PackageVerifierTests.cs`
- [X] T078 Add relocated clean-cache locked restore/build/test/publish, assets/deps/PE allowlisting, process startup, and black-box Status runtime-isolation proof in `tests/ProgramKit.AcceptanceTests/RuntimeIsolation/RuntimeIsolationTests.cs`
- [X] T079 [P] Add offline/local-source-only, no-telemetry/source-upload, secret scanning, no-self-host bootstrap, dependency/source/lock drift tests, and an explicit Windows/Linux proof matrix in `tests/ProgramKit.ContractTests/Security/LocalSafetyTests.cs` and `.github/workflows/vertical-slice.yml`
- [X] T080 [P] Generate deterministic distribution manifest, dependency inventory/SBOM, source/package provenance, diagnostic catalog digests, and exact provider support metadata in `eng/Generate-DistributionEvidence.ps1` and `artifacts/evidence/`
- [X] T081 Add performance assertions for the two-bundle finite closure and sub-two-second local `explain` path in `tests/ProgramKit.AcceptanceTests/VerticalSlice/PerformanceAcceptanceTests.cs`
- [X] T082 Automate the documented valid/invalid/repeatability/drift/repair walkthrough without ambient setup in `eng/Invoke-VerticalSliceQuickstart.ps1` and reconcile `specs/001-status-component-api/quickstart.md` with the executable flow
- [X] T083 Prepare the fresh-contributor one-hour product-review record with automated timing evidence, the seven architecture questions, every honest limitation, and an explicit pending human-approval gate that must not be reported as passed without an independent reviewer in `specs/001-status-component-api/reviews/first-vertical-slice.md`
- [X] T084 Reconcile `README.md` with the accepted constitution, implemented CLI behavior, archived-history boundary, current branch/main state, known limitations, and exact contributor entry points
- [X] T085 Run locked restore, release build, all tests, schema validation, generated-consumer runtime isolation, quickstart automation, formatting, and clean-worktree checks; record the exact verification commands and results in `specs/001-status-component-api/verification.md`

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

- [X] T086 CRITICAL Replace Boolean/window authority with an exact grant bound to request, operation closure, requested effect, evaluation context, freshness, review, and revocation state, with fail-closed adversarial tests, per FR-003, FR-004, FR-017, and Constitution I (remediated)
- [X] T087 CRITICAL Route public operations through the versioned factory-request contract, complete offline Draft 2020-12 structural and typed semantic validation, remove provider-specific intake ownership from the kernel, and aggregate independently known missing input per FR-001 through FR-003, FR-008, and Constitution III (remediated)
- [X] T088 CRITICAL Add callable intake-mapping, construction, and evaluation provider SPI surfaces plus exact role/support admission so a provider cannot advertise an unimplemented role, per FR-008, FR-030, the plan three-role decision, and Constitution VI (remediated)
- [X] T089 CRITICAL Complete candidate gate closure, exact support/provenance/evidence evaluation, live-precondition rechecks, publication fault recovery, and receipt-last admission so partial or interrupted state cannot be trusted, per FR-014, FR-015, FR-018, and Constitutions IV and V (remediated)
- [X] T090 Complete read-only exact, missing, modified, stale, colliding, interrupted, unsupported, and unavailable evaluation plus separately authorized ownership-safe repair and publication recovery, per FR-016, FR-017, and US3 (remediated)
- [X] T091 CRITICAL Make fallback effect reporting depend on the furthest proven lifecycle state and complete result, diagnostic-trigger, disclosure, truncation, continuation, and remediation contract tests, per FR-019 through FR-025 and Constitution VII (reclosed: typed diagnostic truth, production triggers, disclosure, and fallback are directly proven)
- [X] T092 Project the workspace snapshot only from authoritative closure, identity, relationship, seam, artifact, provenance, gate, review, waiver, evidence, receipt, support, retention, and diagnostic records, and recompute freshness without mutation, per FR-026 through FR-028 and US4 (remediated)
- [X] T093 Complete the declared invalid, repair, publication-fault, path/culture/order, package-claim, provenance/SBOM, performance, hostile-filesystem, local-safety, no-self-host, and relocated-runtime proof matrix, per FR-018, FR-029, FR-031, FR-032, FR-034, and SC-004 through SC-010 (reclosed: the executable SC-005 diagnostic and invalid-input matrix is directly proven)
- [X] T094 Reconcile every original T001-T085 checkbox against its named artifact and direct proof, retain unchecked status wherever proof is absent, and update README plus verification with only current evidence, per the Spec Kit workflow and Constitution IX (complete: 80 satisfied, 5 superseded, 0 missing)
- [ ] T095 CRITICAL After T086-T094 and all applicable deterministic gates pass, obtain an independent human product accept/reject decision and record its exact scope, reviewer identity, evidence binding, limitations, and date without deriving acceptance from automation, per Constitutions I and IX (the 2026-08-01 ACCEPT decision remains valid only for commit `16c6c627dfc9cd2211993580019f43d084dc718d` and manifest digest `sha256:60b63f41a220c95df0fb87abcb7bbca94f17f97da8c361350d1115539110e557`; a fresh decision is requested for candidate `c84335ee9eea4666fc69af5c2e49cbce821b8fbb` and manifest digest `sha256:25fd0146dcca3fe8b8d359a9a208e51504718eb978b95fde60570a33cd8ecebd`)

---

## Phase 9: Evidence-Ledger Closure

**Purpose**: Close only the requirements that remain genuinely unproven after
the consolidated implementation, then make the original task ledger and fresh
human decision depend on exact current evidence rather than historical paths.

- [X] T096 CRITICAL Classify every original T001-T085 row as satisfied, superseded, or missing with exact current artifact/proof citations; explain every supersession and correct the premature T094 status in `specs/001-status-component-api/reviews/task-closure-audit.md` and `specs/001-status-component-api/tasks.md` (complete)
- [X] T097 CRITICAL Complete the API-neutral typed contract surface for safe diagnostic values, finite waivers, candidate preconditions/gates/source trace, admission receipts, artifact state, and workspace snapshots; preserve safe restricted-YAML source spans for diagnostics and prove the public model in `src/ProgramKit.Contracts/Operations/CommonContracts.cs`, `src/ProgramKit.Contracts/Workspace/WorkspaceContracts.cs`, `src/ProgramKit.Kernel/Intake/RestrictedYamlParser.cs`, and `tests/ProgramKit.ContractTests/ContractModelClosureTests.cs`
- [X] T098 CRITICAL Record and verify both exact package SHA-256 and NuGet content hash, validate every dependency-mirror package against the governed lock before use, fail closed on tampering, and prove both paths in `src/ProgramKit.Providers.DotNet/DotNetFactoryProvider.cs`, `tests/ProgramKit.ContractTests/NuGetIntegrityTests.cs`, and `tests/ProgramKit.AcceptanceTests/VerticalSliceAcceptanceTests.cs`
- [X] T099 Complete the missing black-box CLI grammar/result/exit-code matrix, executable invalid-intake fixture matrix, every-diagnostic trigger contract, and adversarial disclosure/fallback cases in `tests/ProgramKit.ContractTests/CliAndDiagnosticClosureTests.cs`, `tests/ProgramKit.AcceptanceTests/InvalidInputAcceptanceTests.cs`, and `tests/Fixtures/Reference.Status/Invalid/` (complete after bounded production-trigger, catalog, SC-005, and adversarial-disclosure repair)
- [X] T100 Complete canonical snapshot schema/golden/trace/no-inference coverage, every freshness state, and fresh-session orientation using only the snapshot plus referenced authority in `tests/ProgramKit.ContractTests/WorkspaceSnapshotClosureTests.cs`, `tests/ProgramKit.AcceptanceTests/WorkspaceOrientationAcceptanceTests.cs`, and `tests/Fixtures/Reference.Status/Golden/snapshot/`
- [X] T101 Complete the accepted repeatability and independent-runtime proof matrix, including supported path/culture/input/order variants, external-package claim verification, clean-cache relocation, and assets/deps/PE dependency allowlisting in `tests/ProgramKit.AcceptanceTests/ProductProofAcceptanceTests.cs` and `tests/ProgramKit.AcceptanceTests/RuntimeAndDriftAcceptanceTests.cs`
- [X] T102 CRITICAL Run locked restore, release build, all contract/unit/acceptance tests, schema and generated-consumer checks, quickstart, distribution-evidence regeneration/check, formatting, diff, and clean-worktree gates; then reconcile T001-T094 plus README/review/verification claims only to the evidence actually recorded in `specs/001-status-component-api/tasks.md`, `specs/001-status-component-api/reviews/task-closure-audit.md`, `specs/001-status-component-api/reviews/first-vertical-slice.md`, `specs/001-status-component-api/verification.md`, and `README.md` (complete: final 91-test gate passed and the exact candidate binding is reconciled in verification.md)

**Checkpoint**: T095 remained pending until T096-T102 were complete and a fresh
independent reviewer evaluated the exact pushed commit and bound evidence. Those
conditions were met before the separate named-human ACCEPT decision.

---

## Phase 10: Diagnostic Contract Readiness Convergence

**Purpose**: Close only the four existing-MUST diagnostic findings from the
independent pre-T095 audit. These findings reopen the T058, T091, T094, and
T102 readiness claims until all four tasks, the complete T102 gate, and the
evidence ledger reconciliation pass again. T095 was held pending until then.

- [X] T103 CRITICAL Require every normal and independent-fallback diagnostic to carry at least one exact evidence reference and at least one typed bounded remediation with an existing request artifact or complete inline request/argument-array/digested-patch payload; reject empty or kind-only projections in the public schema and direct contract tests, per FR-021, FR-022, and Constitution VII (complete: non-empty catalog evidence and executable request payloads are schema-enforced for normal and fallback diagnostics)
- [X] T104 CRITICAL Replace public-by-default heuristic diagnostic string classification with explicit schema-classified safe values that fail closed for unclassified subject/cause/consequence inputs; pass secret-derived fingerprints through the real classifier/factory and prove ordinary, provider, rendering, verbose/progress, and fallback paths cannot disclose them, per FR-024 and Constitution VII (complete: raw command, positional, and option tokens are excluded from bounded parse prose and black-box opaque-token disclosure proof passes)
- [X] T105 CRITICAL Bind each diagnostic catalog identity to its canonical catalog bytes, add exact diagnostic-catalog and conformance-evidence identities to `ProviderManifest`, carry those bindings through the first-party manifest/runtime registry and generated distribution evidence, and prove identity/artifact digest agreement plus exact provider resolution, per Constitutions III and VI, the accepted `ProviderManifest` data model, T011, and T034 (complete: canonical catalog bytes, provider manifest, registry, and distribution evidence share exact digest bindings)
- [X] T106 CRITICAL Add direct production-boundary trigger-and-ID assertions for `MissingInput`, `ConflictingInput`, `IncompleteMeaning`, `GateFailed`, `CShellsConformance`, and `PackageMismatch`, while retaining the all-ID schema/catalog projection test only as catalog coverage, per T058, T091, SC-005, and Constitution IX (complete: all six IDs are asserted at their callable production boundaries)

**Checkpoint**: T103-T106 and the complete repository-owned T102 gate passed;
the original-task ledger and review documents were reconciled to the new
evidence; a clean exact candidate was committed and pushed; and the final
independent read-only readiness verdict returned READY before the named-human
T095 ACCEPT decision.

---

## Phase 11: Cross-Platform Provenance Merge Closure

**Purpose**: Close the T080/SC-006 deterministic provenance defect discovered
by fresh Windows and Ubuntu pull-request checkouts without weakening merge
protection or silently extending the prior exact T095 acceptance binding.

- [X] T107 CRITICAL Reject BOM, invalid UTF-8, and CR bytes before source-provenance hashing; prove every recorded source digest against canonical UTF-8/LF bytes; regenerate the exact source provenance and distribution manifest; and rerun the complete local T102 gate, per T001, T080, SC-006, and Constitutions III and IX (complete in `4d1c519fd5e788c36252437de03cb8c1ccb13c33`; 91 tests passed)
- [X] T108 CRITICAL Push the corrected exact candidate, require both Windows and Ubuntu vertical-slice checks to reproduce its evidence, reconcile the final reviewed commit and manifest binding, and only then request a fresh named-human T095 decision before merge, per Constitutions III and IX (complete: protected PR run `30720316337` passed Ubuntu and Windows against `c84335ee9eea4666fc69af5c2e49cbce821b8fbb`; the exact manifest binding is reconciled below)

**Checkpoint**: The exact pushed review candidate is
`c84335ee9eea4666fc69af5c2e49cbce821b8fbb`, bound to corrected manifest digest
`sha256:25fd0146dcca3fe8b8d359a9a208e51504718eb978b95fde60570a33cd8ecebd`.
Protected PR run `30720316337` passed on Ubuntu (3m26s) and Windows (4m41s).
Only the fresh named-human T095 product decision remains before merge.

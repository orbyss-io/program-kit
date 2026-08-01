# Verification: Provider-Neutral AI Session Integration Proof

This record contains repository-local execution evidence. It is not semantic approval, publication authority, or a substitute for the independent human/live-session gates listed in `tasks.md`.

## Foundation — 2026-08-01

- Red-state contract filter: failed to compile because the four session schemas, session result fields, lifecycle command identities, and disclosure contracts did not yet exist.
- Red-state unit filter: failed to compile because request-bound authority and namespaced publication contracts did not yet exist.
- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj -c Release --no-restore --filter "FullyQualifiedName~SessionIntegrationSchemaContractTests|FullyQualifiedName~SessionOperationResultContractTests|FullyQualifiedName~SessionIntegrationBoundaryTests"`
  - Passed: 6; failed: 0.
- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj -c Release --no-restore --filter "FullyQualifiedName~SessionAuthorityGrantTests|FullyQualifiedName~NamespacedArtifactSetPublisherTests"`
  - Passed: 4; failed: 0.
- `dotnet test ProgramKit.slnx -c Release --no-restore`
  - Contract: 10 passed.
  - Unit: 19 passed.
  - Acceptance: 4 passed.

Foundation observations:

- session contracts are embedded in the offline registry with stable schema identifiers;
- session results reuse `program-kit.operation-result/v1`;
- read-only operations reject supplied authority, while effects require an exact unexpired, unrevoked, unconsumed grant bound to request, operation, workspace, provider, and scope;
- namespaced publication preserves candidate bytes, rejects collisions and stale staging, and rolls back an injected partial publication;
- source-authoring workspaces fail closed;
- canonical and provider-neutral assemblies contain no provider-local projection symbols; and
- runtime projects do not acquire development-session dependencies.

## US1 — workspace-local CLI and Codex projection — 2026-08-01

- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj -c Release --no-build --filter "FullyQualifiedName~SessionCliContractTests|FullyQualifiedName~CodexProjectionContractTests"`
  - Passed: 6; failed: 0.
- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj -c Release --no-build --filter "FullyQualifiedName~SessionLifecycleTests"`
  - Passed: 2; failed: 0.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj -c Release --no-build --filter "FullyQualifiedName~PackagedToolAcceptanceTests|FullyQualifiedName~SessionInstallationAcceptanceTests"`
  - Passed: 3; failed: 0.
  - The package was produced without rebuilding, installed through an isolated local-only NuGet configuration, and invoked only through the workspace-local `program-kit` app host while network proxies were denied.
  - Ten fresh workspaces completed explain/install/verify with equal generated skill fingerprints.
  - Each installation classified the live projection as `exact`, while provider-session availability remained separately `reload-required`.
- `eng/Pack-ProgramKitTool.ps1 -OutputRoot C:\tmp\program-kit-us1-pack`
  - Package: `Orbyss.ProgramKit.Cli.1.0.0-alpha.1.nupkg`.
  - SHA-256: `2B1D70BF84A738D248B4E7C85158ED2EA3105BD773CB2E83AA9FEAF6D5B23D8B`.

US1 observations:

- explain returned no effect and the exact provider, adapter, definition, release, candidate-set, projection, expected-state, and authority-request bindings;
- install consumed a separately stored grant bound to the exact request core, workspace, provider, scope, operation, and committed effect;
- projection publication and its journal were namespaced under `.program-kit/session-integrations/codex/`, with the admission record written last;
- verify compared admitted record and live bytes without mutation;
- source-authoring workspaces were rejected before lifecycle inspection or projection;
- the installed projection consisted only of `.agents/skills/program-kit/SKILL.md`; and
- no source checkout, global registration, provider process, network client, telemetry client, or runtime dependency was introduced.

## US2 — human-led intent and exact construction authority — 2026-08-01

- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj -c Release --no-build --filter "FullyQualifiedName~SessionGuidanceContractTests"`
  - Passed: 1; failed: 0.
- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj -c Release --no-build --filter "FullyQualifiedName~ConstructAuthorityBindingTests"`
  - Passed: 1; failed: 0.
  - Changes to canonical input, operation, workspace target, or provider selection invalidated the original binding.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj -c Release --no-build --filter "FullyQualifiedName~HumanLedSessionWorkflowAcceptanceTests|FullyQualifiedName~SessionRuntimeIsolationAcceptanceTests"`
  - Passed: 2; failed: 0.
  - Declined/missing authority produced `blocked / none / request-approval`; the exact separately granted request installed successfully; verify preserved the complete workspace digest.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj -c Release --no-build --filter "FullyQualifiedName~Construct_then_evaluate_proves_admission"`
  - Passed: 1; failed: 0 after migrating Feature 001's reference request from ambient approval to an exact repository grant.
- `dotnet test ProgramKit.slnx -c Release --no-build`
  - Contract: 17 passed.
  - Unit: 22 passed.
  - Acceptance: 9 passed.

US2 observations:

- the canonical workflow distinguishes known, incomplete-known, and unknown intent without inventing consumer semantics;
- clarified input, target paths, provider resolution, operation, and grant identity participate in the invocation binding;
- factory construction now loads and consumes a request-bound repository grant instead of trusting an ambient Boolean;
- the existing public construct/evaluate slice remained compatible under the stricter authority mechanism;
- the ten-workspace deterministic lifecycle suite retained equal projection fingerprints, exact request bindings, committed install outcomes, and read-only verification outcomes.

## US3 — stable diagnostics and corrective guidance — 2026-08-01

- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter "SessionDiagnosticCatalogContractTests|SessionNegativeResultGoldenTests|InvocationTransportGuidanceContractTests"`
  - Passed: 4; failed: 0.
  - Aggregate canonical negative-result SHA-256: `sha256:6c72c60b19a44e2ef7ef2279eac0a269576c5ff9f38f349d25142189a4dc5947`.
- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter SessionDisclosureTests`
  - Passed: 6; failed: 0.
  - Secrets, credentials, authorization headers, conversation identifiers, raw tool output, rooted paths, controls, stack traces, and oversized values were withheld or bounded.
- `dotnet build src/ProgramKit.Cli/ProgramKit.Cli.csproj --no-restore` followed by `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --no-build --filter SessionDiagnosticsAcceptanceTests`
  - Passed: 3; failed: 0.
  - CLI mismatch stopped with `PKSES0001`; admitted drift proposed a separate repair with `PKSES0004`; source-authoring use stopped with `PKSES0006`; every case proved `effectState: none` or byte-for-byte preservation.

US3 observations:

- reserved neutral IDs `PKSES0001` through `PKSES0009` and provider IDs `PKCDX0001` through `PKCDX0003` have stable versioned catalog entries;
- transport failures before a valid envelope remain integration-layer failures and never fabricate a Program Kit result or launch a provider;
- unexpected internal exceptions return the existing safe `PKINT0001` fallback rather than being mislabeled as a session-availability warning;
- remediation projection is typed, bounded, non-executable guidance; and
- disclosure filtering returns stable withheld/truncated values without raw paths, provider output, credentials, prompts, transcripts, or exception details.

## US4 — provider-neutral conformance — 2026-08-01

- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter "SessionProviderConformanceContractTests|ProviderNeutralityArchitectureTests"`
  - Passed: 3; failed: 0.
- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter SessionProjectionDeterminismTests`
  - Passed: 1; failed: 0.
  - Repeated and semantically irrelevant projection variants produced observation SHA-256 `sha256:26822f5b3c1d3f55bd25981f12605131bea313105d56a457e533e0fd00b0dd00`.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter "CodexProviderConformanceAcceptanceTests|SessionProviderParityAcceptanceTests"`
  - Passed: 3; failed: 0.
  - Valid, stale-definition, incompatible-support, and corrupted-content cases were classified exactly; direct CLI, neutral harness, and reference-provider observations preserved normalized outcome, effect, and disposition meaning.
- Provider-neutral golden corpus aggregate SHA-256: `sha256:255f26e0db6e737dd016041525b05e828763fe2144e8af6652cf46d71a3eb562`.

US4 observations:

- conformance evaluates only the public adapter contract and canonical definition;
- required operations, workspace scope, generated ownership, diagnostic/profile identities, structured-result expectations, authority, disclosure, and fresh-session classification are explicit profile fields;
- repeated projection is byte-stable and provider-local paths are normalized out of semantic comparison;
- canonical source and corpus inspection found no reference-provider paths, payloads, command names, or types; and
- semantic weakening produces ordered exact failures instead of silently lowering the canonical boundary.

## US5 — exact record-driven removal — 2026-08-01

- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter RemoveSessionIntegrationTests`
  - Passed: 5; failed: 0.
  - Absent, exact, partial, drifted, interrupted, and already-removed transitions were exercised; interrupted removal rolled back the admitted bytes and returned `PKSES0005` with an `indeterminate` effect.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter SessionRemovalAcceptanceTests`
  - Passed: 2; failed: 0.
  - Exact removal preserved unrelated workspace files and independent provider state byte for byte; drifted owned content was retained and blocked with `PKSES0004`.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter PackagedToolRemovalAcceptanceTests`
  - Passed: 1; failed: 0.
  - The locally packed and workspace-installed CLI remained callable and returned release `1.0.0-alpha.1` after its Codex session projection was removed.
- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter Session`
  - Passed: 17; failed: 0.
- Exact-removal fixture corpus aggregate SHA-256: `sha256:b0a12389080e615f801f0b16930e6361ad4fbcdb928f9ccac7174f48eccd8aa6`.
- Preserved fixture-byte SHA-256 values:
  - unrelated consumer skill: `sha256:2410afe65935fd59b394ea566129afb3ffffe694ba20f9c063e29c783dab44ca`;
  - unrelated consumer source: `sha256:5039bcb2e17e52f8e551c6c4daa72326bde093956e72297a09796ff1bb284738`; and
  - independent provider/global state: `sha256:43486b14488497e183fda442c5b82dac7b70e59d097fea192ba4231b1906c31a`.

US5 observations:

- removal requires an exact unconsumed grant bound to the removal request, workspace, provider, scope, operation, and committed effect;
- every recorded projection is revalidated under the workspace lock before any deletion;
- only exact paths from the admitted record are backed up and removed, with no broad consumer-directory deletion;
- interruption produces a durable rollback/incomplete journal, restores any removed exact bytes when possible, and never reports a committed outcome;
- a committed receipt distinguishes an explicitly removed integration from one never installed, while verification reports no provider-session availability claim;
- missing, partial, corrupt-record, and drifted installations fail closed without mutation; and
- authority grants, unrelated `.agents` content, application files, provider/global state, and the independently installed workspace-local CLI remain outside removal ownership.

## Cross-cutting completion evidence — 2026-08-01

Environment and dependency closure:

- .NET SDK: `10.0.302`.
- `dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config`, with isolated `APPDATA`, `XDG_CONFIG_HOME`, `DOTNET_CLI_HOME`, and the repository-ignored package cache:
  - succeeded; all projects were already current;
  - no `packages.lock.json` changed.
- A restore without the explicit repository `NuGet.Config` was rejected by the workspace sandbox because the .NET SDK attempted to read the inaccessible user-level NuGet configuration. No result from that rejected invocation is counted as restore evidence.
- `dotnet format ProgramKit.slnx --no-restore --verify-no-changes`: passed.
- `dotnet build ProgramKit.slnx -c Release --no-restore`: passed with 0 warnings and 0 errors.
- Final full Release suites:
  - contract: 24 passed, 0 failed;
  - unit: 34 passed, 0 failed;
  - acceptance: 19 passed, 0 failed.

Package and isolated-workspace proof:

- `eng/Invoke-SessionIntegrationQuickstart.ps1 -SkipBootstrap` completed on Windows in ten isolated workspaces outside the source repository.
- Bounded evidence: `reviews/deterministic-session-review.json` using schema `program-kit.deterministic-session-review/v1`.
- Evidence SHA-256: `sha256:bc8ffe0d1ae8cdd51bc2a03202cd019a7c82f07b7385d4573bbd9e47efa73846`.
- Acquired package identity: `Orbyss.ProgramKit.Cli` `1.0.0-alpha.1`; observed package SHA-256: `sha256:d9fd462a847045b4fd4887e1fd14967bdac5cc67893bbbd5b3fa03b0be2c7907`.
- Trials: 10 passed, 0 failed. Workspace-local tool installation took 316 ms minimum, 323.5 ms median, and 335 ms maximum.
- The ten workspace-bound installation records and removal receipts each had ten distinct exact digests; every generated skill had the same projection SHA-256 `sha256:8ddcb2a195a09bc56c060a97398491607b2191e053c951b88f84519e80a4b4fb`.
- Every trial proved missing-authority `program-kit.kernel/PKPOL0001`, drift `program-kit.session/PKSES0004`, exact removal, preserved consumer bytes, and a still-callable independently installed CLI.
- The evidence asserts denied network after package acquisition, disabled telemetry, no source upload, and no provider-global registration.
- A separate final pack inspection produced `Orbyss.ProgramKit.Cli.1.0.0-alpha.1.nupkg`, SHA-256 `sha256:0643fee471958f0acdba4aec31664f724d8deb392e8bf112c22d9c61b4bbc6cc`, 908,816 bytes, with 31 expected entries and no external NuGet dependencies in its manifest. NuGet archive hashes are recorded per acquisition and are not claimed to be equal across separate pack invocations.

Focused conformance, disclosure, and runtime evidence:

- `dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj -c Release --no-build --no-restore --filter SessionDisclosureTests`: 6 passed.
- `dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj -c Release --no-build --no-restore --filter "SessionProviderConformanceContractTests|ProviderNeutralityArchitectureTests"`: 3 passed.
- `dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj -c Release --no-build --no-restore --filter "CodexProviderConformanceAcceptanceTests|SessionProviderParityAcceptanceTests|RuntimeAndDriftAcceptanceTests|SessionRuntimeIsolationAcceptanceTests"`: 6 passed.
- The runtime test now installs and removes the session projection before restoring, building, starting, and calling the generated reference application's accepted `/status` behavior. Its dependency closure contains no Program Kit, Spec Kit, session-integration, or Codex provider assembly.
- Static scans of product session/CLI sources found zero network clients, telemetry mechanisms, provider launches, source-upload mechanisms, credential literals, or user-global registration mechanisms.
- Static scans of bounded review evidence found zero source-root paths, temporary consumer roots, prompts, responses, transcripts, or credential-like values.
- Inspection of every extracted package entry found zero source-root paths, temporary consumer roots, or credential-like values. The intentional synthetic disclosure-test fixture `password=withheld` is test data and is not a product or evidence finding.

## Requirement reconciliation and pending gates — 2026-08-01

| Requirement area | Disposition |
|---|---|
| FR-001, FR-003 through FR-006 | Passing Windows automated package/isolation, direct-CLI, source-separation, and runtime evidence. Linux execution remains pending the shared matrix run. |
| FR-002, FR-020, SC-007 | Partial: the selected exact release/version and admitted identities are recorded and observed, but a cryptographic binding from the acquired package through the callable executable is not yet enforced. This is a recorded first-vertical-slice convergence gap, not a Feature 002 success claim. |
| FR-007 through FR-014 | Canonical session contracts and provider-neutral projections pass their contract tests. Provider-role admission and vocabulary/support-envelope fail-closed enforcement remain recorded follow-up gaps. |
| FR-015 through FR-023 | Automated explain, preflight, exact authority, staged publication, verification, failure, and structured-result behavior passes, subject to the exact artifact-binding gap above. |
| FR-024 through FR-032, SC-003, SC-005 | Guidance and deterministic workflow mechanics pass automated tests. Fresh live Codex behavior and the two-turn human interaction outcome remain pending T101 and T102. |
| FR-033 through FR-038, SC-006 | The public session adapter conformance and parity suites pass. The separate factory SPI/public factory-request seam is not remediated by this feature. |
| FR-039 through FR-046, SC-004, SC-008 through SC-010 | Passing diagnostics, disclosure, local-first, exact-removal, preservation, and post-removal runtime evidence. |
| SC-001, SC-002 | Ten Windows workspaces pass. Linux and the documented fresh-provider-session portion remain pending shared CI/live review. |

Final disposition: the Feature 002 implementation and deterministic Windows evidence are ready for review, but the feature is not semantically approved, release-ready, or fully converged. T100 remains open for Linux execution, T101 remains open because no live Codex launch was authorized, T102 remains open for an independent human product decision, and T105 remains open because the known artifact-binding and factory/VSL enforcement gaps are engineering gaps rather than human gates.

The separate read-only review identified these out-of-scope follow-ups; none were implemented in Feature 002:

1. `ProviderRole` declares construction, evaluation, and projection roles while `IFactoryProvider` exposes only construction, and role admission is not enforced.
2. Runtime intake uses the provider-specific .NET intake instead of the public factory-request seam.
3. Exact digest equality and observed CLI/package/executable binding need convergence wherever Feature 002 claims exactness.
4. Vocabulary and support-envelope behavior is not yet fully fail-closed.

Agreed follow-up order: close and converge Feature 002 with the pending evidence visible; reconcile and implement the existing pushed Feature 003 Claude adapter; reconcile and implement the existing pushed Feature 004 engineering-quality/constitution gates; then create Feature 005 for first-vertical-slice convergence. No later feature branch was created or executed during this work.
## Phase 9 convergence evidence — 2026-08-01

The following evidence supersedes the earlier partial dispositions for the canonical definition, provider manifest, CLI artifact binding, production provider admission, and installation-record trust chain. It does not change the pending Linux, live Codex, or independent-human gates.

- `dotnet format ProgramKit.slnx --no-restore --verify-no-changes`: passed.
- `dotnet build ProgramKit.slnx -c Release --no-restore`: passed with 0 warnings and 0 errors.
- Full Release suites after convergence:
  - contract: 28 passed, 0 failed;
  - unit: 34 passed, 0 failed;
  - acceptance: 27 passed, 0 failed.
- The acceptance suite includes the ten fresh packaged/offline Windows workspaces and the packaged negative matrix.

T106 — canonical session definition:

- one embedded `session-integration-definition.json` is now the runtime source for the full authority, effect, result, guidance, projection, diagnostic, factory-operation, and lifecycle contract;
- its identity digest is recomputed from normalized canonical content, the guidance reference is verified against the embedded Markdown bytes, and placeholder or drifted identities are rejected;
- round-trip, definition-drift, guidance-drift, and definition/provider-binding tests pass.

T107 — Codex manifest:

- the embedded `codex-provider-manifest.json` is now the only runtime source for provider, adapter, definition, conformance, provider-surface, tested-version, diagnostic, support, operation, scope, and projection declarations;
- provider and adapter identities bind the normalized manifest content, the diagnostic identity binds the executable Codex diagnostic catalog, and the manifest must bind the exact executable definition and conformance profile;
- placeholder and divergent manifest identities fail closed.

T108 — selected CLI release:

- candidate admission resolves the declared workspace-local executable, hashes its current bytes, resolves the exact installed `.store` NuGet package, hashes its current bytes, and compares schema, canonical profile, package ID/version/digest evidence, command, executable path/digest, reported version, runtime profile, package-source evidence identity, and claim class;
- the mismatch table covers every governed CLI field plus missing executable and missing installed-package evidence, always returning `PKSES0001` with `effectState: none`.

T109 — production provider admission:

- exact provider, adapter, definition, and conformance-profile content identities are resolved before projection;
- the declared conformance evaluator now runs in production before effects and rejects support, scope, operation, binding, ownership, definition, diagnostic, deterministic projection, structured-result, authority, disclosure, normalization, and fresh-session-classification loss;
- ambient provider selection is rejected as typed ambiguity `PKRES0002`; unavailable exact selection remains `PKSES0002`; incompatible admitted behavior remains `PKSES0003`.

T110 — installation trust and verification:

- the installation-record schema now matches the emitted exact record, including canonical profile, workspace root binding, provider/adapter/definition/conformance identities, full CLI release, projection set, publication evidence, admission receipt, and record digest;
- inspection recomputes the record digest, installation identity, projection-set live-state digest, journal digest, admission receipt, installed package/executable evidence, and current workspace/provider/CLI/projection bindings without mutation;
- tests prove exact idempotence, reload-required/fresh-session separation, corrupt and missing-journal `partial`, current CLI `stale`, provider-profile `incompatible`, and projection `drifted` states.

T111 — packaged negative matrix:

- the locally packed and workspace-installed CLI proves malformed input `PKREQ0002`, ambient ambiguity `PKRES0002`, incomplete/unsupported exact selection `PKRES0001` or `PKSES0002`, unavailable executable/package `PKSES0001`, collision `PKWSP0002`, interrupted prior publication `PKWSP0003`, stale/drifted binding `PKSES0004`, and missing authority `PKPOL0001`; the production-admission corpus separately injects incompatible providers and proves `PKSES0003`;
- every case asserts the primary disposition and effect state; collision, interruption, drift, missing authority, and all request failures preserve consumer-owned or pre-existing bytes.

Convergence disposition:

- the earlier FR-002/FR-020/SC-007 cryptographic package-to-callable-executable gap is closed for the tested workspace-local .NET tool layout;
- the earlier FR-007 through FR-014 placeholder-definition/manifest and test-only session-provider admission gaps are closed;
- the factory SPI/public factory-request/vocabulary findings remain deliberately deferred to Feature 005 and were not implemented here;
- T100 remains pending for Linux execution, T101 remains pending because no live Codex launch was authorized, T102 remains pending for an independent human product decision, and T105 remains pending until those authorized final gates can be truthfully consolidated.

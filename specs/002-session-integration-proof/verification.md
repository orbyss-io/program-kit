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

## Supported-platform deterministic review — 2026-08-01

T100 is satisfied by the bounded Windows/Linux matrix evidence in
`reviews/deterministic-session-review.json`:

- Draft PR `#7`, workflow run `30699217250`, head
  `d19626a288d5b2de143b9709b2a3e15b48dd01af` passed both supported jobs:
  Ubuntu job `91367117663` and Windows job `91367117669`.
- Aggregate evidence schema:
  `program-kit.deterministic-session-review-index/v1`; SHA-256
  `sha256:c253d0b4cbf1eed212b57777244713debe7f8560412495b154da5bbcecfc0171`.
- Ubuntu raw evidence SHA-256:
  `sha256:e5bceb579558f271749810647d083d25052137f058bd3f34e92454207192ceee`;
  Windows raw evidence SHA-256:
  `sha256:2cc5c3583a115a991c29a73ca7890ba6817aa10b98473448c604cda6eddfdc9b`.
- Both platforms used SDK `10.0.302` and package identity
  `Orbyss.ProgramKit.Cli@1.0.0-alpha.1`. Observed package bytes are honestly
  `verified-equivalent`, not claimed cross-platform canonical-byte: Ubuntu
  `sha256:8414bfc5c919d048f4b4d378fdcbf476c1db727e1ce41177276d19e8f6152884`;
  Windows `sha256:500c5d24250da816c2f4d338829d9cb7a93cac3102a78a23ca94f35cc82d42ce`.
- Ten fresh workspaces passed per platform, twenty total, with zero failures.
  Tool installation took 314–344 ms on Ubuntu and 518–2150 ms on Windows.
- Each platform produced ten distinct installation-record digests and ten
  distinct removal-receipt digests. Every trial proved missing-authority
  `program-kit.kernel/PKPOL0001`, drift `program-kit.session/PKSES0004`, exact
  removal, preserved consumer bytes, and a callable CLI after removal.
- Platform-specific projections were deterministic within their declared
  profiles: Ubuntu `sha256:f6b58f754bd93c6d8bd40259933eabba7200bf53db14ee54103e7c5271d18f10`;
  Windows `sha256:1e27eb2a631c2a4de27cb08fccfe0cac00837b112c0de3c44154643143e00a21`.
- Bounded evidence scans found zero source-root paths, temporary consumer roots,
  prompts, responses, transcripts, credential-like values, or raw provider
  output. T100 is complete.

## Live Codex session review — 2026-08-01

T101 was executed with explicit authorization and recorded as bounded evidence
in `reviews/codex-session-review.json`:

- provider `codex`, exact CLI version `0.137.0`, observed version output
  `codex-cli 0.137.0`, and explicitly pinned bundled model `gpt-5.5`;
- reviewer identity `joey-orbyss`, 10 fresh isolated trials, 8 complete passing
  attestations, and final status `findings-present`;
- trial 3 did not ask for missing input within two interaction turns; trial 9
  neither completed evaluation nor asked for missing input within two turns;
- normalized-LF evidence SHA-256
  `sha256:e7d6b00c53b0473e9e2a0de98bf8a2c783a50d21447d66f96ef5f5e72ea6f91d`;
- the bounded record contains no prompt, response, transcript, conversation,
  credential, raw-output, source-root, consumer-root, or workspace-path field;
  absolute-path and credential-pattern scans returned zero findings.

The human-observed bounded finding was that the construct authority grant
declared consumer-owned `requests/revocations.json` and
`requests/review.json` artifacts that were absent, while construction was
still admitted. The repository authority loader currently does not close those
declared revocation and provenance references. This is an upstream Feature 001
first-vertical-slice authority-closure finding and was deliberately not
remediated inside Feature 002.

T101 execution is complete, but SC-003 and SC-005 are not passed by this run.
T102 remains pending for an independent human approval or rejection decision;
T105 remains pending until that decision is recorded without self-approval.

## Final T105 requirement reconciliation — 2026-08-01

This section supersedes the earlier pending-gate dispositions while preserving
their raw provenance. It records the final Feature 002 state after T100, T101,
and the independent T102 decision.

| Requirement | Final evidence disposition |
|---|---|
| FR-001 through FR-006 | **Automated pass.** Exact packaged acquisition, isolated consumer use, direct CLI operation, source-workspace separation, and generated-runtime independence pass supported-platform and runtime evidence. |
| FR-007 through FR-014 | **Automated pass within Feature 002 scope.** Canonical session definition, provider-neutral projection, manifest/definition binding, production adapter admission, and fail-closed projection validation pass. The separately recorded factory SPI/public-request/vocabulary work remains deferred to Feature 005 and is not claimed here. |
| FR-015 through FR-023 | **Automated pass.** Explicit selection, explain/preflight, staged publication, exact CLI/package/executable admission, verification state, and structured lifecycle results pass the convergence and negative matrices. |
| FR-024 through FR-032 | **Not product-accepted.** Automated guidance/authority/result mechanics pass, but live trial 9 did not complete evaluation and trials 3 and 9 failed timely missing-input handling. The missing revocation/provenance closure means the exercised factory authority path was not a valid happy path. |
| FR-033 through FR-038 | **Automated pass.** Codex remains one provider projection; neutral/direct/provider conformance and normalized semantic parity pass. |
| FR-039 through FR-043 | **Automated pass.** Stable diagnostics, bounded next actions, disclosure filtering, local-first behavior, and zero credential/path/transcript evidence findings pass. |
| FR-044 through FR-046 | **Automated pass.** Explicit authorized removal, unchanged-owned-byte deletion, consumer-byte preservation, and removed-state verification pass. |
| SC-001 | **Pass.** Supported-platform deterministic evidence proves documented isolated acquisition, installation, and verification well within ten minutes. |
| SC-002 | **Pass.** 20/20 supported-platform fresh-workspace trials admitted complete exact state or failed safely, with zero trusted partial-success reports. |
| SC-003 | **Fail.** The authorized live review passed only 8/10 attestations; trial 9 did not complete evaluation. Independent reviewer `joey-orbyss` rejected product acceptance. |
| SC-004 | **Pass.** The packaged negative and production-admission matrices return the expected typed next-action/effect classes without unauthorized mutation. |
| SC-005 | **Fail.** Trials 3 and 9 did not ask for missing input within two interaction turns. |
| SC-006 | **Pass.** Direct, neutral, and Codex adapter conformance preserve normalized outcome, effect, and disposition meaning. |
| SC-007 | **Pass.** Exact CLI release, provider/adapter/definition/conformance identities, workspace binding, projection set, and verification state are recorded and revalidated. |
| SC-008 | **Pass.** Exact removal preserves unrelated/consumer-owned bytes and refuses drifted or unproven targets. |
| SC-009 | **Pass.** Source, package, projection, and bounded-evidence scans found zero secrets, protected paths, transcripts, source uploads, telemetry, or undeclared provider launching. |
| SC-010 | **Pass.** The generated reference application restores, builds, starts, serves `/status`, and remains runtime-independent after session integration and Program Kit removal. |

Independent review disposition: **REJECTED — NOT APPROVED**. The exact decision
is recorded in `reviews/product-review.md` under reviewer identity
`joey-orbyss` at `2026-08-01T13:28:07.307Z`.

Feature 002 implementation evidence is complete enough to hand off, but the
feature MUST NOT claim product acceptance, release readiness, or semantic
approval. Reconsideration requires first-vertical-slice authority-closure
remediation, correction of the resulting session-guidance failures, a new full
ten-consecutive-fresh-session evidence set, and a new independent human
decision. T105 is complete as a truthful reconciliation, not as an approval.

## Approved remediation candidate — 2026-08-02

This section supersedes only the implementation-readiness conclusion above. It
does not reinterpret the rejected 8/10 review or claim new product acceptance.

- T112 passed focused diagnostic proof: 12 contract tests, including schema
  validation of every retained `PKSES` and `PKCDX` result. The negative aggregate
  identity is `sha256:f57590685ce39389c0d5d5440bdfbd78a19442627629b4cac1637c966a4ad3da`.
  The session and Codex catalog identities are respectively
  `sha256:006042a0eaee83f410f96405db492c33ccd66514f19886a54ea88913335b22e5`
  and `sha256:e96a4a56a2c9e6b007a745e1e31713ebdc630592c6fb4616e8d733ec02f0b2c5`.
- T113 passed the exact-seed helper and contract matrix for the current Feature
  001 factory request, grant, review, revocation, definition, implementation,
  explain, construct, and evaluate closure. The seed identity is
  `sha256:cd2207f623d9705a1768c9a242a6f76acc8feb78f15d24557602c76b20de45f6`.
- T114 passed one focused projection test and two human-led workflow acceptance
  tests covering typed missing input, exact continuation, non-authorizing
  conversation, selected grant authority, construction, and evaluation. The
  current definition and provider-manifest identities are respectively
  `sha256:238ed8e709e0bc85204cc802556e364f51002d370145e7ce6cec7f7832c5994f`
  and `sha256:2f8ca6b14475f0c06e56746916fd4f7156442c9247279a6cd8f78a63db4f1d9f`.
- T115 passed feature-owned schema and contract proof for exact candidate
  bindings, ten bounded reviewer attestations, typed final results, fail-closed
  invalid evidence, and absence of raw prompts, responses, transcripts, output,
  credentials, and paths. The schema identity is
  `sha256:963b74d9721993dfd2bd9f3adeb4c9ac5316d1042a33d5e9e465cbc7f6c43ad3`.
  The rejected historical evidence remains byte-exact at
  `sha256:e7d6b00c53b0473e9e2a0de98bf8a2c783a50d21447d66f96ef5f5e72ea6f91d`.
- T116 regenerated eight deterministic distribution artifacts twice without
  drift. The manifest identity is
  `sha256:439355b70d8319ab1c26c8e2fda692d96e678618705d255f5d9553d25184ef4b`.
  `eng/Invoke-Verification.ps1 -Mode PrePr` then passed isolated builds with
  zero warnings/errors, 46 unit tests, 64 contract tests, changed-file format,
  SpecKit integrity, canonical text, and diff hygiene. The unchanged dependency
  mirror was reused; the local full acceptance/conformance/platform matrix was
  intentionally not duplicated.

T117 is pending authoritative protected Windows/Linux CI. T118 remains an
explicitly human-operated ten-fresh-session review, T119 remains a new
independent human decision, and T120 remains final reconciliation. Therefore
Feature 002 is remediated for CI handoff but is not yet accepted.

### First protected remediation run — 2026-08-02

Protected run `30742625953` exercised exact head
`bab4d453099973198a29f372ce44c9d619c4bb4c`. Preflight, locked restore,
Release build, and deterministic evidence passed on Windows and Ubuntu. Both
platform jobs then found the same existing-requirement blocker in
`Packaged_cli_negative_matrix_is_typed_fail_closed_and_byte_preserving`: the
ambiguous session-provider path requested `needs-input` without the mandatory
typed continuation, so result aggregation safely replaced it with fallback
`PKINT0001`. T114 and T116 were reopened; T117 remains pending. This failed run
is retained as repair provenance and is not acceptance evidence.

The approved focused repair now emits `needs-input` with exact diagnostic
`PKRES0002`, a request-bound continuation, and missing-input identity
`providerselection.provider.selected`. The single previously failing packaged
acceptance test passed in 6 seconds. Distribution evidence regenerated twice
without drift; the repaired manifest identity is
`sha256:ef753696a915123aa38b09600b37e154d4757799c00b586da785132fddc11a95`.
The fast pre-PR gate then passed zero-warning/error builds, 46 unit tests, 64
contract tests, formatting, SpecKit integrity, canonical text, and diff hygiene
while reusing both the dependency mirror and locked restore. T114 and T116 are
reclosed; T117 still requires a new protected run for the repaired exact head.

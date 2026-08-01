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

# Verification: Claude Code Session Adapter

**Feature**: `003-claude-code-adapter`
**Evidence status**: deterministic implementation evidence in progress
**Product acceptance**: blocked

## Governing limitation

Feature 002 is the exact provider-neutral dependency and its human product
decision is `rejected`. The Feature 003 manifest therefore declares
`supportClaim: not-evaluated`; the executable admission evaluator returns
`canonical-dependency-not-accepted` for rejected, missing, stale, or mismatched
dependency state. No deterministic result in this file upgrades that status.

## Foundational provider-contract evidence

Command:

```text
dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeProviderBoundaryContractTests|FullyQualifiedName~ClaudeProviderManifestContractTests|FullyQualifiedName~ClaudeMachineReviewSchemaContractTests|FullyQualifiedName~ClaudeDiagnosticCatalogContractTests|FullyQualifiedName~ClaudeSupportAdmissionContractTests"
```

Result: 9 passed, 0 failed on .NET SDK `10.0.302`.

Exact bounded identities established by the tests:

- provider: `anthropic:session-provider:claude-code@2.1.220`;
- adapter: `orbyss.program-kit:session-provider-adapter:claude-code-project-skill@1.0.0`;
- manifest digest: `sha256:24d4eb1b3e5703235109efabcb71a7b4dfdca2322245fa7b9bc1b8d905e42c5b`;
- diagnostic catalog digest: `sha256:01c390a82039bed04a5f6c38bb606eccfd2d623f84c5dd7c309a7cc5f0c7a6aa`;
- provider surface: exact project skill at `.claude/skills/program-kit/SKILL.md`;
- support claim: `not-evaluated`.

The provider-boundary test also proves Claude names, paths, and diagnostic
identities are absent from Contracts, Kernel, and the neutral SessionIntegration
project.

## US1 deterministic project-skill evidence

Commands:

```text
dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeSkillProjectionContractTests|FullyQualifiedName~ClaudeCliRegistrationContractTests"
dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeSessionProviderAdapterTests"
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeInstallation"
```

Result: 7 passed, 0 failed. Ten fresh adapter evaluations produced one exact
skill digest,
`sha256:37b044db0db48140ec9946d7dff085e75e0f7a121a9abe90e058288da794260a`,
and one exact manifest identity. Every lifecycle resolution remained blocked
with `effectState: none` and `program-kit.session/PKSES0003` because the upstream
dependency is not accepted. Therefore no installation record exists and none is
claimed; the repeatability proof covers the adapter candidate bytes and honest
fail-closed result only.

## US2 authority and invocation evidence

Commands:

```text
dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter FullyQualifiedName~ClaudeGuidanceContractTests
dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter FullyQualifiedName~ClaudeInvocationBindingTests
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeAuthorityPreservationAcceptanceTests|FullyQualifiedName~ClaudeWorkflowAcceptanceTests|FullyQualifiedName~ClaudeRuntimeIsolationAcceptanceTests"
```

Result: 6 passed, 0 failed. The projection preserves canonical workflow order,
requires explain-first handling and current human effect authority, and renders
an executable plus argument array rather than shell text. The tests also prove
that Claude process permission is not Program Kit effect authority and that
runtime templates contain no Claude/session-provider dependency. They do not
claim a successful installed lifecycle while the upstream definition is
rejected.

## US3 conformance evidence

Commands:

```text
dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter FullyQualifiedName~ClaudeConformanceProfileContractTests
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter "FullyQualifiedName~ClaudeProviderParityAcceptanceTests|FullyQualifiedName~ClaudeConformanceNegativeAcceptanceTests"
```

Result: 4 passed, 0 failed. Direct, neutral-harness, Codex, and Claude channel
observations preserve the same canonical result fields in the bounded model.
Altered outcome meaning and a `not-evaluated` support claim fail conformance.
This is deterministic adapter-model evidence, not live Claude behavior.

## US4 diagnostics and disclosure evidence

Commands:

```text
dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --no-restore --filter FullyQualifiedName~ClaudeDiagnosticGoldenContractTests
dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter FullyQualifiedName~ClaudeDisclosureTests
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter FullyQualifiedName~ClaudeAvailabilityAcceptanceTests
```

Result: 3 passed, 0 failed. All eight provider-local triggers map to stable
`PKCLD` entries, observations expose bounded safe fields only, and availability
remains distinct from installation and support. No raw prompt, transcript,
credential, reasoning, protected physical path, or provider output is retained.

## US5 removal-boundary evidence

Commands:

```text
dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --no-restore --filter FullyQualifiedName~ClaudeRemovalTests
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --no-restore --filter FullyQualifiedName~ClaudeRemovalAcceptanceTests
```

Result: 3 passed, 0 failed. The manifest declares only
`.claude/skills/program-kit/SKILL.md` as generated-owned with
`exact-admitted-digest-only`; parent directories, settings, other skills, and
the independently installed CLI remain outside adapter ownership. Because the
rejected upstream definition prevents installation, the executable removal
proof is presently a fail-closed no-effect/preservation proof. Exact admitted
installation-and-removal remains pending and is not claimed.

## Sealed review-kit reproducibility

Two exports from distinct clean output roots produced:

- review-kit digest: `sha256:7d1d47c0908ea4bc799465fff31915404679d5ee2694ede220a64b9e1b40fffc`;
- package digest: `sha256:24881aa60942e950f977ee64aebb4d26c798221558da20b01c2812668db11ad7`;
- file count: 45 in each export;
- byte/hash differences: 0.

The sealed kit was then initialized in a fresh external consumer root. Ten
package-only CLI installations all reported CLI `1.0.0-alpha.1`, Claude support
`not-evaluated`, `effectState: none`, and an absent Claude project skill. The
bounded proof recorded 10 passed and 0 failed. No Claude process was launched.

## Complete deterministic repository gate

Commands:

```text
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx --configuration Release --no-restore
dotnet test ProgramKit.slnx --configuration Release --no-build --no-restore
dotnet format ProgramKit.slnx --no-restore --verify-no-changes
```

Environment and results:

- .NET SDK: `10.0.302`;
- restore: succeeded with the locked graph;
- build: succeeded with 0 warnings and 0 errors;
- contract tests: 42 passed;
- unit tests: 43 passed;
- acceptance tests: 38 passed;
- total: 123 passed, 0 failed, 0 skipped;
- formatting: no changes required.

## Honest completion boundary

Deterministic Claude adapter mechanics, provider-local projection, invocation
binding, diagnostics, bounded conformance models, documentation, and sealed
no-effect review tooling are implemented. Product support and acceptance remain
blocked. In particular, this feature does not claim:

- successful Claude lifecycle installation or an installation record;
- exact removal following an admitted installation;
- the complete package-only lifecycle/corpus/removal/runtime proof described by
  the future accepted-support procedure;
- ten live Claude `2.1.220` trials; or
- an independent human `accepted` decision.

Those claims require an accepted Feature 002 identity, a newly sealed
`supported` adapter manifest, explicit authority for Claude execution, ten
qualifying isolated-machine trials, and a separate human product decision.

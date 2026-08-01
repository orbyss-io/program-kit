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

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

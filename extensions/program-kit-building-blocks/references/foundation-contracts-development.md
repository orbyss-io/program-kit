# Foundation contracts development candidate

The named recipe [foundation-contracts-development-v4.json](foundation-contracts-development-v4.json)
selects `0.3.0-contracts.20261006.6` explicitly. The prior v1, v2 and v3 recipes remain preserved for historical evidence.
Qualification requires the private runtime package/Host path
through actual F6 managed-host, Nuplane, two-shell and PostgreSQL tests. The public dependency registry,
its selected default and historical qualification receipts remain authoritative for public adoption.

The Host supplies native ASP.NET status handling and shares only its two CShells contracts.
Each shell selects its Foundation or custom problem mechanisms. Foundation authentication and typed
JSON retain their shared bounded failures; an unowned root route uses the native platform status response.
Configure `WebRouting.Path` explicitly, including an empty path for a root shell, when native routing
failures must use that shell's representation. Foundation runtime archives stay in the actual loader
feed; their assemblies are not forced into the Host.

Prepare only after F6 writes a successful `result.json` alongside its matching `inputs.json`:

```powershell
python scripts/prepare_foundation_contracts_development_profile.py prepare `
  --profile foundation-contracts-0.3.0-contracts.20261006.6-development `
  --version 0.3.0-contracts.20261006.6 `
  --f6-result <F6-run>/result.json `
  --packages <F6-run>/feed `
  --host <exact-private-host>/Orbyss.Foundation.Host.dll `
  --output artifacts/foundation-contracts-development-profile
```

The helper verifies the complete live feed against F6 hashes, reads actual nuspec identities/versions,
and checks the Host plus its adjacent native loader assemblies, dependency/runtime configuration and
all root JSON settings, optional web-profile configuration and native runtime assets. Swapping those dependencies behind an unchanged Host DLL invalidates the
evidence. It generates `profile.json` and `catalog.json` through the maintained
dependency profile overlay adapters, preserving composition choices. `runtime-packages.props` uses the
maintained central-pin renderer and admits each generated pin only when its exact package exists in the
qualified private feed. New Authentication/Collections/Execution/ProblemDetails Core contracts and the
Execution/PostgreSQL mechanisms are separately listed in `supplemental-packages.json`; this supplements
package references without inventing new catalog compositions or activations.

Exporter, analyzer and OCI pins retain the stable public baseline through explicit `toolVersions`.
Prerelease tooling and a public candidate Host image are outside this development qualification. The
private Host is represented by its assembly path/hash and runtime file inventory in `evidence.json`. The generated development
index has `default: null` and uses `development-qualified` status, which the public qualification guard
does not accept. Evidence explicitly records `publicAvailabilityEstablished: false`,
`publicHostAvailabilityEstablished: false` and `defaultPromotionPerformed: false`.

Consumers of this development evidence must select its exact profile identity and verify it before
restoring or qualifying their disposable scenario:

```powershell
python scripts/prepare_foundation_contracts_development_profile.py verify `
  --profile foundation-contracts-0.3.0-contracts.20261006.6-development `
  --directory artifacts/foundation-contracts-development-profile `
  --f6-result <F6-run>/result.json `
  --packages <F6-run>/feed `
  --host <exact-private-host>/Orbyss.Foundation.Host.dll
```

The Notes runner requires the same directory and explicit identity. Pass the original F6 feed to the
profile verifier; a later feed augmented with Notes packages has a different hash set. Altered F6
results, inputs, package bytes, Host bytes, generated pins, recipe or public baseline invalidate the
development evidence. Existing output is preserved; mismatched preparation requires a new directory.

The independent Notes specimen under `tests/fixtures/foundation-consumer-contracts/notes/v1` demonstrates
four compilation projects: Core owns semantic seams/values, Notes owns domain behavior, Notes.Api owns
operation endpoints/wire contracts, and Notes.PostgreSql owns EF entities, its context and provider configuration.
Its instance endpoints consume `IJsonRequestReader<T>`, `IJsonResponseFactory<T>`,
`IValidatedAccountIdentityReader` and `IProblemMapper<TFailure>` through DI. Registration declares typed
profiles/resolvers; configuration supplies byte/count/depth limits. Domain denial results map through
`FoundationProblemResults.Problem`, while native exceptional handlers retain precise failure types.

Provider code creates independent units using the native factory surface:

```csharp
await using var unit = await leases.BeginUnitAsync(callerCancellation, operationDeadline);
await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
await context.SaveChangesAsync(unit.Deadline.Token);
```

`leases` is `IPostgreSqlUnitLeaseFactory<TContext>` and the provider's context derives from
`FoundationPostgreSqlDbContext`. Mutation and receipt reconciliation use separate units while retaining
the existing outer deadline. The tracked shell lease retains datasource ownership through cleanup;
plain root/DI scopes cannot admit factory contexts. SQLSTATE/constraint classification and uncertain
commit policy remain provider/application-owned. No generic repository or application entities enter Core.

The specimen demonstrates exact replay, expected revisions and bounded independently read pages. Its
canonical algorithm remains application-owned, using Foundation's incremental UTF-8/hash mechanics.
The named recipe preserves existing validated claim URNs, authentication codes and canonical-v1
identities. Shell-bound BFF ticket keys require reauthentication of older unbound sessions; they do not
change account or persisted result identity.

This preparation starts no coding agent, publishes no package, promotes no default and supplies no
Program Kit Release or paid-trial authority. Public adoption requires PK2B immutable availability,
restore, published Host/activation closure and the separate release gates. De Zaaglijst migration
follows publication through its separately authorized real consumer specification.

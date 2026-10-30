# Synthetic asynchronous batch processing

This optional example compiles SDK-free `BatchProcessing.Core` separately from recording providers
and a console conformance runner. It supplies no application host, SDK adapter, durable persistence,
Docker engine access or cloud infrastructure. Existing applications retain the published Orbyss
host, CShells/Nuplane and managed exporter. The console runner is test tooling only.

Read the governance `references/asynchronous-workloads.md` source map first when selecting platforms.
The example demonstrates captured execution/exchange bindings, provider-private state, stable
submission identity, duplicate handling, authorized-attempt fencing, original deadlines, cancellation
versus observed stop, cleanup obligations and retaining older run bindings after a default changes.
It deliberately labels volatile in-memory admission/outbox behavior as a model, not durability.
The exchange models a resource-side authority check; it does not qualify storage tokens or a real
remote side effect. Production implementations must enforce these guarantees at their effect owners.

Run with the installed .NET 10 SDK:

```powershell
dotnet build AsyncWorkloadProof.csproj --configuration Release --nologo
dotnet bin/Release/net10.0/AsyncWorkloadProof.dll
```

## Explicit composition check

From the consumer root, use the installed .NET adapter:

```text
python .specify/extensions/program-kit-dotnet/scripts/provider_composition.py --input config/program-kit/batch-provider-composition.json
```

Copy `composition.example.json` to that path to try the synthetic Development example, then replace
its fictional metadata/observations with actual selected inputs. Changing its environment label
alone must fail: the example's recording packages are Development-only. Tests construct separately
labelled fictional non-Development providers; they do not relabel these as production-qualified.
The finite schema is exercised in `tests/validate_async_workloads.py` in the contributor repository.
Required top-level fields: `schemaVersion: 1`, `environment`, `scope`, `requirements`, `bindings`,
`packages`, `features`, `packageRoots`, `featureRoots`, `packaged`, `activated`, `fixtures`,
`privileges`, `compatiblePairs`. Every field is explicit; the check writes nothing or contacts services.

- `requirements`: exactly execution/exchange `{capability, contractVersion}` rows.
- `bindings`: `{capability, contractVersion, provider, version, scope, package, feature}` rows,
  exactly one per capability. Scope equals the selected environment/tenant security scope.
- `packages`: `{id, version, dependencies, developmentOnly, privileges}` rows. Versions are exact;
  dependency identities resolve within this selected metadata inventory.
- `features`: `{id, package, dependencies}` rows. Dependencies are transitive activation requirements,
  not every feature that a package happens to export.
- `packageRoots`, `featureRoots`: explicit selections. Package closure also includes active features'
  packages. No implicit provider or Docker fallback exists.
- `packaged`, `activated`: independently observed exact package and activation identities. Include
  base host/runtime dependencies in roots and metadata. Extra packages or activations fail as well
  as missing ones. Supply their complete resolved closure, not project reference guesses.
- `fixtures`: `{id, developmentOnly}` rows. `privileges` names engine/host privileges (socket mounts,
  engine endpoints, elevated container rights), not normal cloud IAM grants. All such privileges and
  Development-only packages/fixtures are forbidden in every environment other than Development.
- `compatiblePairs`: exact `["execution-provider@version", "exchange-provider@version"]` pairs
  whose interoperability the owner explicitly selected. This list is a declaration, not qualification.

Use separate environment inputs/closures. The existing typed materializer has global feature
selection; this checker does not retrofit environment-specific packaging into it. Select separate
graphs/bundles where necessary and compare actual emitted closures. Do not claim that changing only
resource settings removes a package or transitive activation. Native observation adapters for arbitrary
external providers are not supplied; this check validates supplied observations, not their provenance.

## Qualification limits

A qualified provider needs real deployment, identity, configuration, isolation, durable recovery,
ambiguous-submission reconciliation, duplicates, deadline/stop, external-effect fencing, erasure and
retirement tests for its exact version/scope. This example does not qualify Docker, WebJobs, Azure
Container Apps, Kubernetes or a queue transport. Adding a provider should preserve business rules;
it still requires platform engineering. Do not publish synthetic results as platform acceptance.

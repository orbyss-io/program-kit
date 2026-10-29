# Typed first operation

This revised recipe requires a qualified Foundation runtime **0.3.10 or later** in its actual API/runtime/provider
owners: `JsonContractFactory`, descriptive JSON contracts, scoped endpoint registration and problem-status metadata use that release's
APIs. The finite adapter rejects older or incompatible native pins before writes; it never upgrades a preserved
consumer lock. Qualify/adopt the dependency through its normal owner first. Consumers retaining older releases
may continue ordinary manual implementation with that release's supported APIs and the same engineering rules;
do not copy these newer helper calls into an incompatible project or treat manual editing as a version bypass.

Construct new consumer metadata with `JsonContractFactory.Request<T>()` and
`JsonContractFactory.Response<T>()` from `Orbyss.Foundation.Json.AspNetCore`. Keep the shared declaration on
its DTO or operation owner and reuse it for native registration and endpoint mapping. Use named overrides
for supported intervals instead of repeating positional numbers or standard profile strings. The defaults
are 1 byte through 16 MiB and nesting depth 1 through 64; retain intentional existing overrides such as
`minimumDepth: 2`. The optional typed `profile` selects a custom configured key, as in this example.
These capacities describe what the contract supports; the shell still owns active deployment budgets.

Export the exact installed optional sources into a new owned artifact directory:

```sh
python .specify/extensions/program-kit-governance/scripts/asset_sources.py --repository . --component program-kit-dotnet --subtree references/examples/typed-operation
```

Preserve the adapter's project-local layout:

```text
Core/Labels/{ILabelStore,ILabelOperations}.cs
Runtime/Labels/{LabelOperations,LabelServices,LabelExecutionOptions}.cs
PostgreSql/Labels/PostgreSqlLabelStore.cs
Api/Operations/ReadLabel/Endpoint.cs
Api/Operations/WriteLabel/{Endpoint,LabelRequest}.cs
Api/Representation/LabelResponse.cs
Api/Configuration/{LabelApiOptions,LabelApiOptionsValidator,LabelApiOptionsAdmission}.cs
Api/LabelEndpoints.cs
Tests/Labels/LabelOperationsTests.cs
```

Each endpoint owns its actual route, admission, handler binding and mapping. Place operation-only
request/response models and mapping helpers in that operation's folder; share representations
under an explicit shared owner only when their meaning is genuinely shared. There is no mandatory
Constants bag or extra model for a bodyless operation. Stable route/name constants may live on the
endpoint. Shared permission tokens belong to the feature's semantic public contract, so API and
Web consumers do not reference each other's endpoint implementations. Where permissions apply,
use `RequirePermission(FeaturePermissions.Read)` with the real canonical permission owner;
the helper preserves native authorization and does not grant permissions.

The read operation is
bodyless, so it needs no request DTO. Both operations deliberately share the same
public label representation; its explicit shared owner preserves the existing CLR
and wire identities. `LabelEndpoints` is thin composition. Tests mirror the runtime
capability's ownership. The application capability owns write-then-read orchestration.
That observation is not an atomic
write/read snapshot and supplies no general transaction or retry guarantee.
Declare the real
Core project references in the native projects and `eng/architecture.json`. Register
`ILabelStore` to `PostgreSqlLabelStore<YourContext>` beside the existing native
`AddFoundationPostgreSql` registration. The context derives from
`FoundationPostgreSqlDbContext`; each operation owns a bounded public unit lease.

The selected API feature calls `LabelEndpoints.Configure(services, settings)` and
`LabelEndpoints.Map(endpoints)`, and declares the selected Foundation JSON and
ProblemDetails features and direct package references. The public
`FoundationProblemEnvelope` is supplied by the new Foundation closure; consume its
released package rather than copying an internal writer shape. Endpoint metadata
declares actual admission, authentication/authorization and server errors alongside
the typed success contract. A prepared owned status array feeds `ProducesFoundationProblemStatuses`, which
describes the existing bounded envelope without inventing runtime failure definitions or handlers.
Strict request DTO metadata disallows unknown members.
Its shell configuration sets `Sample:Api:Prefix` explicitly and selects the example's
own bounded JSON profiles. Merge these values under that shell's `Configuration`:

```json
{
  "Sample": {
    "Api": { "Prefix": "configured-" },
    "Execution": { "Timeout": "00:00:30" }
  },
  "Foundation": {
    "Json": {
      "Profiles": {
        "sample-label-request": { "Preset": "strict-request", "MaxBytes": 1024 },
        "sample-label-response": { "Preset": "tolerant-response", "MaxBytes": 2048 }
      }
    }
  }
}
```

The owning runtime feature prepares `configuration = settings.GetConfigurationRoot()`
before calling `LabelServices.Configure(services, configuration)` and directly
references the selected `Orbyss.Foundation.Execution` package. It owns
one native outer deadline for the entire operation, preserving the original caller
cancellation separately from expiry. Both provider units receive the bounded outer
token; neither starts a fresh total budget. Completion freshness is checked after
each await, including a provider that returns after cancellation. Expiry does not
prove that work stopped, undo a write or authorize retry. This BCL-only store port
propagates the total cancellation cap, not `IExecutionDeadline` identity or native
provider deadline classification. The runtime's thirty-second default is an explicit
sample I/O safeguard, configurable at `Sample:Execution:Timeout`, never semantic Core
policy. Invalid durations fail before effects; product policy requires its actual owner.
API and runtime depend on Core rather than each other's implementation. Shell
configuration selects both features and the provider. Registration is authored
integration, never inferred from generated source presence.
`LabelRequest.Contract` and `LabelResponse.Contract` describe the actual JSON profiles and supported
capacity with named factories. Register that same definition with `AddJsonContract` and map it with
`WithJsonRequest`/`WithJsonResponse`: runtime admission and `x-foundation-json-contracts` retain one
source. Both operations register the shared response; identical registrations are idempotent,
while conflicting profile/requirements fail. The extension's intervals describe supported capacity,
not the current deployment's byte/depth budget. JSON Schema describes wire shapes; actual readers
and result factories still enforce parser/range, byte/depth and output admission. Preserve native
binding attributes on the mapped endpoint method, including optional headers and raw duplicate
header cardinality; co-locating a request DTO never authorizes unbounded native body binding.

The contract's supported maximum and configured budget must agree. Binding this
small contract to a larger default profile correctly fails shell activation.
No provider is created,
schema deployed or operation executed while registering or exporting metadata.
`AddJsonEndpoint` registers the scoped endpoint with deferred constructor activation. It resolves its real provider port only for an admitted
request. This preserves cold metadata export when runtime-only providers are
excluded; never register a fake provider to make export pass. Actual request and
durable-effect qualification must prove that the selected provider supplies the port.
Declare applicable native settings metadata using its maintained producer/inspection
contract. A typed options class alone supplies no independently verified settings
manifest. Preserve original source hashes and review actual generated changes.
Native `AddOptions/Bind` and the separate `IValidateOptions<LabelApiOptions>` validator precede immutable policy admission; copying a validated
work snapshot does not replace binding or require `IOptions` in Core. Required API options are
observed by the non-disposable scoped `LabelApiOptionsAdmission` at native CShells preparation (order -1000),
before request activation and later protected work. Its only dependency is `IOptions<LabelApiOptions>`;
it resolves no product/store provider. Effect owners must keep protected work after required admission.
Native lifecycle enumeration may construct initializer objects before ordered execution; their constructors
must perform no I/O. Cold metadata export does not run shell initializers. Root `ValidateOnStart` alone is
not shell activation proof. SDK IDE2001 and Foundation ORB1007–ORB1010 check different
parts of the source-layout contract; a passing invocation-chain check does not cover the category.
For new declarations, adapt `settings.source.template.json` for the API and
`runtime.settings.source.template.json` for the runtime to the actual package and
feature identities. After restore, run
`dotnet msbuild <api-project> -t:FoundationInspectSettingsSourceBindings -p:Configuration=Release`
for each owning project with the released Foundation Build producer. Review its separate
`obj/Release/<tfm>/orbyss-foundation/settings-source-bindings.json` report and merge
the complete current source inventory into `sourceSha256`. Set
`FoundationSettingsMetadataSource` to `settings.source.json` in the owning project.
The template's empty inventory intentionally cannot pass normal build. Build and
pack validate actual compiled provenance separately; inspection never authorizes
rewriting an established declaration or accepting a changed historical receipt.

Explicit fixture deployment creates `sample_labels(id integer PRIMARY KEY, value
text NOT NULL, revision integer NOT NULL DEFAULT 0)` and inserts `(1, 'ready', 0)`, granting only the runtime operations it
actually needs. Startup does not create this application table. The disposable
composition qualifier independently reads the actual committed value and restarts
the Host before observing it again. This small single-row example supplies no
general idempotency, multi-resource transaction or uncertain-write retry contract.

Initialize the actual shell's OpenAPI contract with `eng/openapi_init.py`, retaining
its isolated generator package and lock. Run the emitted lock command, then the
maintained Build/OpenAPI pipeline. It executes the actual native metadata producer,
exporter, comparison and TypeScript generator. Preserve established baselines;
initialization is appropriate only for a genuinely new contract.

Place `client.ts` under `web/policy-web/src/` in this example layout, adjusting its
generated-types import to the real initialized contract identity. It is a thin
application transport adapter importing the actual generated `paths`; it does not
replace generator output or hand-author wire schema. The application check/build
must include it under strict TypeScript. Obtain the native BFF antiforgery token
from the authenticated session, then invoke it once with the caller's bounded
AbortSignal for an explicit operation.
Cancel before dispatch performs no write. After dispatch failure, reconcile the
actual outcome before considering another request. No provider/model/coding agent
or human approval is invoked by this example.

For an F2-prepared task with a qualified F3 pattern bound to this recipe, use
`coding_scaffold.py preview/apply`; see the contributor `docs/coding-scaffolding.md`.
The finite adapter creates absent consumer source, shows exact diffs and preserves
existing content on conflicts. Application code is consumer-owned immediately and
never added to toolkit managed-file ownership. Use ordinary editing for later
refactors. Unsupported adapters retain the compatible manual recipe route and all
normal evaluation duties.

The editable C# sources follow the canonical `dotnet-engineering.md` Orbyss style
overlay: more than two parameters/arguments use one per line and an aligned closing
parenthesis on its own line; argument values are prepared before calls; fluent
chains start below the receiver and put each invocation on its own line. The named
endpoint registration still resolves dependencies only in the request scope. Named route
handlers retain their explicit service-binding attributes. Review these mandatory
conventions after ordinary edits too. The selected Foundation source-readability
analyzer mechanically checks its documented rules, including prepared deferred
arguments. The maintained fixture compiles actual emitted owners with that analyzer;
it does not certify state ownership, method abstraction, provider policy or arbitrary
file placement. Review those semantics and adverse behavior in the first operation.

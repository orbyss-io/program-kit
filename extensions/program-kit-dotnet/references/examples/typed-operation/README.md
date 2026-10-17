# Typed first operation

Export the exact installed optional sources into a new owned artifact directory:

```sh
python .specify/extensions/program-kit-governance/scripts/asset_sources.py --repository . --component program-kit-dotnet --subtree references/examples/typed-operation
```

Place `ILabelStore.cs` in the accepted Core project, `PostgreSqlLabelStore.cs` in its
selected PostgreSQL provider, and the `Label*.cs` files in its API. Each named type
has its own file. The small bodyless read returns the same stored resource
representation; the write owns strict request admission and its provider effect.
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
the typed success contract. Strict request DTO metadata disallows unknown members.
Its shell configuration sets `Sample:Api:Prefix` explicitly and selects the example's
own bounded JSON profiles. Merge these values under that shell's `Configuration`:

```json
{
  "Sample": { "Api": { "Prefix": "configured-" } },
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

The contract's supported maximum and the configured budget must agree. Binding this
small contract to a larger default profile correctly fails shell activation.
No provider is created,
schema deployed or operation executed while registering or exporting metadata.
The scoped endpoint factory resolves its real provider port only for an admitted
request. This preserves cold metadata export when runtime-only providers are
excluded; never register a fake provider to make export pass. Actual request and
durable-effect qualification must prove that the selected provider supplies the port.
Declare applicable native settings metadata using its maintained producer/inspection
contract. A typed options class alone supplies no independently verified settings
manifest. Preserve original source hashes and review actual generated changes.
For a new declaration, adapt `settings.source.template.json` to the actual package
and feature identities. After restore, run
`dotnet msbuild <api-project> -t:FoundationInspectSettingsSourceBindings -p:Configuration=Release`
with the released Foundation Build producer. Review its separate
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

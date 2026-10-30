# Typed executable Foundation composition

## Choose the active route before custom setup

An accepted Foundation Host/BFF/Keycloak/PostgreSQL decision selects this maintained
composition route. Before adding container topology, authentication presentation,
public asset serving or the first product endpoint, inspect the accepted exact
profile and `config/program-kit/foundation-composition.json`. A legacy `--web-profile bff-cookie`
scaffold supplies compatibility files; it does not create that active v2 graph.
Do not interpret its presence as completed composition adoption or a need to recreate
native middleware. Other explicitly selected hosts retain their own engineering route.

For a fresh consumer, adapt the v2 application template named below to the agreed
owners and inputs. For an existing consumer without an active graph, review
`composition_migrate.py --proposal <reviewed-v2.json>` before applying its exact
preview. Then preview `dotnet_sync.py --target . --composition-only --check --json`
with the selected profile/host/source arguments. This bounded scope reconciles
managed composition configuration through the normal transaction. It preserves
authored C# identities, architecture, shell policy, realm users/client identities,
frontend/branding and locks. Inspect actual conflicts and the transaction; this
does not certify that whole-baseline synchronization can overwrite local repairs.
Do not fabricate managed hashes or delete source to make a preview pass.

Preparation, native provider deployment, runtime activation and product acceptance
remain distinct. Provision the selected environment, deploy required native EF
migrations separately under deployment authority, grant the runtime's least
privileges, then exercise the native login and a permission/owner-isolated product
operation. Product secrets and schema readiness are actual runtime inputs. Generic
coding hooks supply read-only guidance and never start this sequence. On resume,
reuse the graph, setup and applicable evidence; repeat only affected checks when
relevant inputs change. Preserve agreed human story reviews.

## First engineering increment

Make initial composition adoption an explicit bounded increment around the first product operation,
before expanding product implementation. Prepare the graph/configuration before adding an endpoint.
Keep it in the current feature unless a reusable platform is itself an independently scoped outcome.
Its result is the active graph with exact pins and generated configuration. Include a realm and real
login check only when identity is selected, a product permission/owner check where that boundary
applies, and separate native schema deployment/read-only admission plus a small real provider fixture
when persistence is selected. Do not add identity or a database to an unrelated worker composition.
Do not expand setup into supplier-wide protocol requalification.
Use the [fast PostgreSQL fixture](examples/postgresql-lifecycle/README.md#fast-provider-test-composition)
for later provider work; it does not need the complete identity/browser topology.
Retain authored realm users/client identities and product overlays when adopting an existing consumer.
On resume, reuse applicable setup/evidence and correct stale operative tasks openly, preserving history.
This is an engineering result, not a new human approval gate or an instruction for generic hooks to
start services. The agreed story reviews and actual security/deployment prerequisites still apply.

Profile activation/exporter hashes establish their declared metadata/admission
scope. Retained Forms browser evidence establishes its Forms scope. The maintained
`validate_composition_start.py --execute` scenarios separately exercise actual
generated Host/Keycloak/browser composition; they do not qualify every consumer
authorization query or require a supplier-wide rerun before each business task.

New qualified profiles carrying `Orbyss.Foundation.Web.Presentation` enable the
native presentation feature for supported browser shells. Historical profiles keep
their exact original package/activation closure. The selected publisher metadata
supplies defaults; no local source checkout substitutes for published knowledge.
The shell resource may also set `"pathBase":"/products/orders"` (empty means root).
The model owns that canonical prefix. Native `WebRouting:Path`, identity callback
registrations, browser BFF endpoints, hosted page paths and the presentation
configuration URL derive from it together. A conflicting consumer overlay requires
reconciliation in the typed graph. Use literal segments without trailing slashes,
encoded aliases, traversal or an origin. The root-only typed operation example is
qualified separately from the nested native composition fixture.

Release qualification distinguishes these supported seams explicitly:

| Integration | Execution and evidence boundary |
| --- | --- |
| Typed managed BFF, native HostedPages, optional PostgreSQL | Root and configured nested shell paths require actual generated Host/browser qualification and installed migration evidence. |
| Typed managed BFF API shell without a frontend | Native authentication readiness and owned API behavior remain separate from UI acceptance. |
| SPA-PKCE source profile and client-owned session adapter | Exact types, redirect/popup headers and native SPA protocol are qualified at their own boundaries. The typed executable composition rejects `browser-spa` before writes; it does not dispatch a BFF substitute or promise turnkey SPA Host materialization. |
| External authority, HTTPS certificate, delegated/API-call or multiple-shell Host execution | Declarations retain their exact capability diagnostic until a matching executable adapter is qualified. |

Under the owning shell resource, configure its public option names explicitly:

```json
"presentation": {
  "enabled": true,
  "settings": {
    "ApplicationName": "Orders",
    "Locale": "en",
    "Theme": "green",
    "RoutePrefix": "/account",
    "ReturnPath": "/",
    "SignOutConfirmation": "when-unsaved"
  }
}
```

The native `LogoutLandingPath` follows that prefix's `signed-out` page. Native
activation validates paths, route collisions, copy and response policies. Set
`"presentation":{"enabled":false}` to omit this feature independently; reconcile
any explicitly selected activation first. A custom presentation keeps the native
public `IProblemPageRenderer` seam and normal application registration. Customize
through that seam or admitted options instead of copying Foundation browser modules.
Use `/account/configuration` to load its authoritative shared confirmation and
session modules; components register their own unsaved state and private roots.
No server page can infer a SPA client's in-memory session or provider revocation.

For the qualified native BFF composition, the generated app entrypoint binds to
Foundation's shared controls through `foundation-controls.ts`. The exact publisher
package owns the checked ESM declarations under `foundation-browser/`; runtime
modules remain served by the native feature. The app's frontend title, locale and
theme supply presentation defaults independently of identity-provider branding.
Private roots stay hidden until a fresh native session observation succeeds.
Cancellation acquires no antiforgery token or logout action. Expiry removes private
presentation and offers recovery without replaying an application operation.

Untouched authenticated generated entrypoints update normally. Customized
entrypoints receive their observed and proposed hashes plus concrete reconciliation
instructions. After reviewing the native binding and retaining owned editor/draft
logic, record the exact source hash under the shell's
`presentation.entrypoints` map, keyed by its bound frontend resource ID. A changed
file or foreign frontend rejects initial adoption. After the managed binding is
installed, routine app edits remain owned; that initial hash stays historical and
does not freeze the entrypoint or prove continued runtime usage. This records source review;
actual type/build, browser and protocol qualification remain required. It does not
grant approval of application behavior or turn an unqualified SPA adapter into an
executable BFF composition. Independently disable presentation when it is not selected.

The optional installed `references/examples/unsaved-editor.ts` supplies a runnable
custom state-source seam. Copy it beside the generated app and declarations, retain
the result of `bindFoundationPresentation(root)`, and pass that binding to
`attachExampleEditor`. Dispose it with the editable component. A pending or uncertain
save reports `unknown`; only the application's actual acknowledged save reports
`clean`. This example implements no persistence, automatic save, replay or domain
acceptance, and cancellation leaves its field value intact.

<!-- program-kit:knowledge-rule principle.private-provider-binding -->
Private-file provider authoring uses the exact typed binding projected into
`eng/foundation-composition.resolved.json`, the generated configuration reference and
scoped phase context. For a binding selecting `EvidenceFiles:Root`, read that key in
the provider and declare it in its native settings metadata. An invented
`PolicyEvidence:RootPath` key is not an alias. Current native source declarations are
compared before dependent materialization; absent declarations are reported as such,
and their presence cannot establish actual compiled registration or exhaustive
dynamic C# access coverage. Use configured native activation to establish that proof.
The maintained lifecycle fixture includes an actual emitted private binding and
missing/invented-key negatives, without changing the accepted private location.
<!-- /program-kit:knowledge-rule -->

The sole authoring input is schema version 2 of `config/program-kit/foundation-composition.json`.
Start from `templates/dotnet/compositions/application-foundation.json` or its
`application-foundation-postgresql.json` variant, then populate the consumer's Accepted
owners, feature paths, assigned endpoints/clients and database bindings. The retained
`foundation-bff-keycloak*.json` files are version 1 migration fixtures and are rejected
by normal generation/execution.

These v2 examples are minimal activation compositions, not complete application project designs.
Their HTTP feature does not acquire workflow ownership merely because its role is `implementation`.
Reconcile actual responsibilities with `principle.compilation-boundaries` in
`program-kit-governance/references/modularity-and-contracts.md`: when application workflows need
runtime coordination, add their owned feature with `responsibility: "runtime"` and its shell binding;
retain `responsibility: "http"` for HTTP adaptation. Pure calculations may remain in Core. No empty
Runtime/Calculations project or additional business context is required by the example.

Define stable typed resources (features, shells, hosts, database servers/databases,
identity authorities/clients/protected resources, frontends), explicit bindings and
environment placement. Link them to the consumer's Accepted architecture and
selection identities. Resource counts come from this graph: multiple contexts can
bind separate databases on a shared server, and multiple applications can use one
authority with separate registrations and audiences. This supplies no aggregate C#
project or consumer host. Feature and context sources are consumer-owned after scaffold.

An `implementation` project may own runtime services or HTTP; the role alone does not select
an endpoint seam. Feature resources use `responsibility: "runtime"` or `"http"` for explicit
new intent. Retained projects may obtain that distinction from their accepted architecture
responsibilities; conflicting or missing authority rejects before writes. Runtime gets a named
`IShellFeature`, while HTTP gets `IWebShellFeature`. Providers retain their persistence seam.
Changing the CLR name preserves the exact `featureIdentity`/ShellFeature string and package owner.

Use optional `capabilityPackages` only for selected Foundation package IDs actually consumed by
that feature. Accepted native per-project selections also contribute their packages. This field
selects no version and cannot admit an unselected dependency; it does not copy every shell web
package into each runtime project. An architecture package inventory containing obsolete scaffold
references is not evidence of capability use. Preserve native pins, meaningful selected activations
and consumer customizations. Untouched authenticated scaffold contributions reconcile through normal
sync; a customized obsolete ApiFeature that would duplicate the identity requires scoped source
correction before managed writes. Do not reset owned code or locks to force reconciliation.

Required product configuration can use an explicit environment projection:

```json
{"kind":"configurationEnvironment","featureRef":"notes-runtime","shellRef":"notes-shell",
 "setting":"Notes:HmacSecret","environmentRef":"EXAMPLE_NOTES_HMAC"}
```

The feature must belong to that shell and the exact product setting declaration must
match its available native metadata. Native authentication, database, routing and Host
settings keep their own bindings. The projection declares a name, never a secret value;
the caller supplies it through the process environment. Missing required input stops the
selected runtime action before processes start. Do not commit values, print them, or
store their hashes in readiness records. Provider code still owns typed binding,
validation, snapshot/reload and disposal semantics. A declaration cannot prove compiled
registration; actual selected activation remains necessary.
For an environment-only secret rotation, use an explicit
`python scripts/composition_run.py run --host <host-id>` with the new process input so
native Compose observes it. Source-only freshness deliberately stores no secret value
hash and cannot infer a rotation; a no-op source update is not rotation evidence.

Branding is consumer-owned authoring data. During migration, retain the existing
identity display name/accent in `identityAuthority.theme.branding` and each frontend's
localized title, purpose, loading, failure, no-script and logo alternative text in
`frontend.branding`. The version 1 importer preserves its explicit identity theme;
version 1 has no frontend resource. For a reviewed version 2 proposal, the consumer
must carry existing frontend branding into the proposal before preview/apply. The
importer preserves supplied values; it does not infer copy from generated realm,
theme or page files. New projects without supplied branding keep the generic defaults.

Declare additional repository-relative frontend/theme input files or directories in
that resource's `inputs` when they live outside its source directory. Their complete
closure participates in preparation freshness, including additions, changes and
removals. Preserve React entrypoints, SDK/API consumer assets, route permissions and
lockfiles; a generic scaffold is not a reconciliation strategy. The actual mounted
identity theme is also a runtime preparation input. A path/hash declaration alone
does not prove that a frontend build consumed the asset or that native admission passed.

The captured manifest producer validates its declared paths and hashes; it does not
certify every image's internal format. Native HostedPages owns content admission,
including PNG chunk restrictions. Discover that selected contract before preparing
branding. Retain the original asset separately. If a reviewed deployment derivative
removes an unsupported ancillary chunk, preserve the image-bearing chunks and their
CRCs and inspect the result through native admission. Do not automatically strip
unknown metadata, weaken admission or treat an unadmitted/failed build as a retained
successful revision. Explicit build input/output and native readiness remain separate.

Activation-test projects and their feature `ProjectReference` bindings are
consumer-owned. Program Kit does not generate or rebind them during composition
migration/synchronization. Tests that instantiate or inspect web feature types must
directly reference both `CShells.Abstractions` and `CShells.AspNetCore.Abstractions`,
using the matching central pins already imported from `config/program-kit/build/ProgramKit.Packages.props`:

```xml
<PackageReference Include="CShells.Abstractions" PrivateAssets="all" />
<PackageReference Include="CShells.AspNetCore.Abstractions" PrivateAssets="all" />
```

Feature projects keep these contracts private because the production host supplies
them. A test `ProjectReference` therefore cannot supply their compile/runtime closure.
After rebinding tests to migrated feature projects, restore through the supported
consumer tooling and build/execute the actual activation tests. Preserve unrelated
locks; do not remove `PrivateAssets="all"` from feature projects to make tests compile.
Native host readiness complements these consumer registration/preparation assertions.

Record each planned test responsibility's actual direct uses in `testSeams` in
`config/program-kit/architecture.json`: `shell-lifecycle` requires only CShells.Abstractions;
`api-feature` and shell `activation` require both contracts; `pure-core` adds neither.
This mapping is bounded to those public seams. Missing or unsupported selected test use
is unresolved, not permission to add blanket dependencies. Keep production PrivateAssets.
For a new declared test owner, `python scripts/test_project.py --project <csproj>` previews
the project and synchronized inventory, bound to the accepted central pins. Apply with
`--apply-digest <reviewed digest>`. It creates no behavioral assertions and cannot replace
an existing consumer project; actual restore, locked dependency review, build and tests
remain required. Existing tests receive only reviewed demonstrably needed direct references.

During task reconciliation, match planned test owners to actual projects. Reviewed unused
empty scaffolds can be archived with their locks and declared successor ownership in
`config/program-kit/verification.json`; do not create empty tests to make a broad gate green. Use named
Focused activation and architecture tests plus real browser/build checks as prerequisites,
then run Affected from the retained implementation baseline once descendant behavior tests
exist. Preserve task IDs, effort, historical failures and story human reviews.

After reviewed archival, preview `python scripts/repository_verification.py --reconcile-owners`.
Its explicit `testOwnershipReplacements` resolve stale owners in verification.json,
verification.setup.json and authored verification-inputs.json rules. Missing, active,
ambiguous or cyclic replacements fail. Apply only the reviewed plan with
`--reconcile-owners --apply-digest <digest>` through the installed native sync transaction.
Authored input/check rules, archive bytes, planned project identities and failed-run evidence
remain intact; fresh unfiltered successor regression must repay retained failure obligations.
Runtime selection also normalizes setup/testGroups through these same explicit successors.
Neither reconciliation nor a Focused prerequisite proves eventual broad acceptance.

Offline OpenAPI export composes metadata, not provider initialization. Effect-only provider
scaffolds emit `FoundationComposeForOpenApi=false`; apply the same reviewed metadata to
consumer effect-only runtime features. API features must retain complete dependencies/routes
and explicit `[FromServices]` endpoint dependencies so offline export does not infer services
as request bodies. Real host activation must resolve those services with actual bindings.
Do not fabricate connection configuration for export. Build stages every declared host using
its canonical `runtimeStage`/`rootPackages`; contracts select their unique shell's host stage,
closure evidence and effective shell configuration. Closure freshness remains mandatory.

<!-- program-kit:knowledge-rule principle.strict-profile-schema -->
Foundation 0.3.3's strict request parser rejects numeric strings, while ASP.NET's default
`JsonNumberHandling.AllowReadingFromString` can produce number|string schemas. Compare
real export output with each registered profile's `TypeInfo<T>()` before implementing the
wire contract. Profile metadata yields numeric-only schemas; explicit DTO property
`[JsonNumberHandling(JsonNumberHandling.Strict)]` is a scoped candidate when those DTOs
are exclusively strict contracts. Verify real producer output and actual numeric-string
rejection before adoption. A publisher profile-aware transformer must distinguish contract
direction/profile; do not strip strings from all schemas, broaden parsing, change all shell
serializer options, or reset a compatibility baseline. Contract changes still require review.
<!-- /program-kit:knowledge-rule -->

A frontend can bind several distinct page routes in the same shell while sharing one
compiled deployment root. Each `frontend` binding supplies its `routeId` and `path`,
with optional `pagePermission` and `bootstrapPermission`. Omitted `pageMode` and
`bootstrapMode` preserve authenticated, private admission. Explicit `Public` selects
anonymous admission with the default response policy; public entries must contain
only deployment-safe public content. A public admission cannot carry a permission,
and bootstrap cannot be public when its page is authenticated. Bootstrap permission
adds to page admission. These fields
preserve existing route restrictions during migration and never grant permissions to
users. Product role/permission assignments remain consumer-owned.

For request-specific initial HTML and metadata, a newly qualified Foundation 0.3.11
profile provides the optional `Orbyss.Foundation.Web.DynamicPages` package. Select it
with a shell resource's `dynamicPages` object using the publisher's native option names:

```json
"dynamicPages": {
  "Routes": [{ "Id": "stall", "Path": "/stalls/{slug}", "Resolver": "stalls", "Mode": "Public" }],
  "TimeoutSeconds": 5
}
```

The compiler selects the exact package/activation and emits `Foundation:DynamicPages`.
It requires the package in the consumer's selected qualified profile; upgrading the toolkit
alone does not advance a retained profile. The owning application feature references the
package (through its `capabilityPackages` selection) and registers its scoped
`IDynamicPageResolver` using `AddDynamicPageResolver<T>("stalls")`. Implement both fresh
resolution and post-render `VerifyAsync` against authoritative publication/resource
authorization state. Unknown state rejects disclosure. No resource projection belongs
in the composition, HostedPages revisions, immutable assets or retained bootstrap.
Native runtime activation owns full route, resolver, policy and configuration admission;
toolkit metadata checks do not replace that qualification.

Keep layout, map libraries, branding, localization and resource business rules with the
consumer. A trusted `IDynamicPageRenderer` can replace the complete document. Keep its
output encoded and bounded; it cannot bypass post-render eligibility verification or
native headers. Fresh GET/HEAD/conditional requests must recheck publication; applications
also revalidate resource eligibility before revealing restored browser content. APIs,
media, discovery, service workers and upstream caches require their own matching policy.
See the captured publisher's `docs/dynamic-page-and-recovery-adoption.md` and package README.

`scripts/composition_run.py prepare` verifies prerequisites, acquires exact dependencies
and browser executables, builds frontends, stages admitted assets/packages and provisions
owned databases and identity registrations. Existing identity users and registration IDs are
preserved; removed owned clients are disabled. `run` starts the generated Docker Compose and checks real activation,
provider connectivity, BFF authentication/theme and page runtime loading. `update --host
<resource-id>` rebuilds affected native compilation dependants and preserves unrelated
services; `stop` preserves owned database/identity volumes. These are explicitly
selected engineering operations; the native implementation prehook supplies only
read-only context. First acquisition is explicit.

Preparation validates the planned architecture and builds/packages the selected
foundation inputs; `run` owns Host activation and readiness. Accepted product bindings may still name interfaces
and implementations that have not been written. Keep those bindings in the plan;
the full evaluated/compiled product architecture check remains an implementation
verification obligation. Foundation readiness does not claim that check has passed.

Generated settings, realm imports and Compose files are outputs. Legacy finite
inputs require explicit `scripts/composition_migrate.py` preview/apply, followed by normal
managed reconciliation and fresh implementation entry. Preserve task IDs, valid owned
code, baseline, effort, original locks and Accepted decision history. Reconcile active
scoped decisions, affected plans and retired placements; no repeated bootstrap/intake.
For an existing consumer with no finite legacy input, supply `composition_migrate.py --proposal
<local-reviewed-v2.json>`; preview binds the Accepted authority, current plans/tasks and locks.
Apply its exact plan digest, then use the same managed synchronization and preparation route.
The proposal is an import document; the active definition remains the one canonical model.

The initial executable adapter qualifies PostgreSQL, managed Keycloak and BFF hosts.
External authority/database placement is represented separately from owned provisioning;
an unqualified provider/profile/handshake reports its missing capability before execution.
Application-only/delegated intent never silently chooses another protocol or grant.
Local insecure BFF applications require distinct browser hostnames because ports do
not isolate the pinned publisher's cookies. HTTP/TLS routing/certificate capabilities
must be qualified for the actual environment. Private imports/personas are synthetic
Development inputs, not production authority provisioning.

Retained private Development/Test filesystem storage uses a `privateFiles` resource
with its architecture `ownerRef`, an environment `directory` outside source, runtime,
package and public asset trees, and a binding with `filesRef`, `hostRef`, `shellRef`,
`featureRef` and `setting`. Optional `section` defaults to `EvidenceFiles` for retained
consumers. It supplies owner configuration through normal CShells configuration and
a writable `/private-evidence/<resource-id>` bind with `create_host_path: false`.
It creates no storage capability port or production/cloud policy; the selected owner
implements its accepted port and validates writable availability at activation.
Explicit `prepare` first provisions a dedicated directory and records its identity in
existing lifecycle state. Repeated preparation, updates and restarts retain it. A lost
or relocated previously bound directory stops setup; restore it or perform an explicit
owned data migration. Existing operator-provisioned permissions are preserved. On
POSIX, only a newly created empty directory is initialized for the selected immutable
Host's actual UID and the provisioning user's group; existing data is never recursively
chowned. Private bytes never enter package stages, public manifests or archives.

Run and update wait for only the selected hosts' managed database/identity services
without recreating their containers before host activation. External endpoints retain
their qualified readiness obligations. A source-only no-op `update` remains a no-op;
select `--host <id>` explicitly to recover a stopped host/dependency without source changes.
Prepared bundles recorded in `pendingActivationHosts` are separate activation work:
plain `update` activates them even when source and prepared closure already match. A selected
host update retains other pending entries. Readiness clears an entry only after actual HTTP
and browser checks pass; failed activation remains due for retry.

Provider placement alone does not select persistence. An explicit `responsibility: runtime`
provider registers its owner services through `IShellFeature`, using the retained `ProviderFeature`
CLR name and exact `ShellFeature` identity. Database bindings require a persistence owner and
select its context, packages and Prepare contribution. An ordinary file/decoder provider must
not acquire a database context, database Prepare work or HTTP/authentication packages. Historical
captures without an explicit provider responsibility retain their original persistence meaning.

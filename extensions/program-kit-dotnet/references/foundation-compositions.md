# Supported Foundation composition inputs

The finite inputs are `foundation-bff-keycloak` and
`foundation-bff-keycloak-postgresql`. Copy the matching file from
`templates/dotnet/compositions/` to the consumer's
`eng/foundation-composition.json`, then name its real application-owned API and,
where selected, provider projects. This records the accepted responsibilities;
it does not create a consumer host or aggregate dependency library.

Use the installed .NET sync with the accepted .NET, Foundation host and package
source selections. Preview first with `--check --json`, review its existing plan
digest, then apply with `--plan-digest <digest>` and the same selections.
Generation, platform readiness and product acceptance are separate outcomes.
The maintained executable setup adapter qualifies fresh disposable services with
loopback HTTP Development origins and an owned private Docker alias on port 8080.
It never provisions a production realm or deployment. Materialization also admits
validated TLS/deployment inputs; production TLS, trusted proxy routing and existing
identity/provider provisioning require targeted checks of that actual environment.
The generated `deploy/compose.identity.yml` is a synthetic local fixture projection.
For a local HTTP loopback identity origin it binds only that loopback interface and
selected public port, imports the selected `<realm>-realm.json`, and assigns the
independently declared administration/backchannel DNS aliases on container port
8080. Their immutable image and generated file hash are recorded in the settings
contract. Unsupported local private transport relationships fail before writes.
TLS/nonlocal identity inputs produce an inert Compose file with no services and an
`external-deployment-required` projection in the resolved view. They require actual
deployment qualification; the file supplies no production identity provisioning.
Reuse the maintained authentication/provider tests for those checks.
An unsupported profile or effective callback/origin conflict fails before any
managed transaction writes. Existing customized scaffolds are preserved and
managed-file drift remains a reviewed conflict.

Application source becomes consumer-owned after scaffolding. Deselecting a
Foundation feature retains a customized project group, including an untouched
project container beneath edited or newly added source, and releases its managed
contribution. Its accepted physical source role remains in `eng/architecture.json`;
runtime feature selection and `runtime.rootPackages` exclude it. An entirely
untouched scaffold can retire. Reconcile a consumer-owned solution when retiring
an untouched project. Managed, configuration and unrelated producer retirement
still require authenticated bytes or explicit conflict resolution.

The captured dependency profile owns exact package versions and host digest.
Publisher-exported typed options own defaults and constraints. Composition inputs
derive the exact client registrations, public issuer, callback and signed-out
callback, allowed origins and setup targets. The private administration address
and metadata backchannel address have independent fields; neither becomes the
public issuer. Secret values remain deployment inputs. For the default shell,
use `CShells__Shells__default__Configuration__Foundation__Web__ClientSecret` and,
for PostgreSQL,
`CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__application__ConnectionString`.

The supported maintained theme is `program-kit`. Admitted branding is plain-text
`displayName` and a six-digit CSS `accentColor`; sync renders those into the local
realm and actual maintained CSS. Custom templates, behavioral code and changed
theme bytes require their own qualification. The local realm/personas are
synthetic testing fixtures. Importing a realm is not an existing production-realm
update procedure. The identity owner must reconcile its exact client registrations,
TLS/proxy settings and least-purpose administration credentials through its
deployment process.

The generated `docs/architecture/foundation-configuration.md` reference and Mermaid
diagram derive from `eng/foundation-settings.contract.json`, whose hashes bind the
exact selected publisher metadata. Run
`python eng/foundation_composition.py --repository . --effective` for the redacted
configured source view. It explicitly distinguishes this projection from activated
options; the maintained readiness adapter observes actual bound settings through
the test-only inspector. Public browser exports allow only the application origin
and admitted display branding.
The selected host projects deployment inputs into a native shell memory provider.
The runtime view identifies that projection and owner bytes; pair it with the
configured-source view rather than inferring an original host provider chain.

Selected feature roots are explicit `runtime.rootPackages`. Runtime staging uses
the maintained sealed pack inventory and selected-root package closure, with
`runtime.directory` deriving `artifacts/release-bundle` for the root shape or
`artifacts/<directory>` for a nested shape. The stage command requires both
`--stage-packages` and `--pack-inventory`. It verifies package identity, graph
consistency and the freshness of source and toolchain inputs.

PostgreSQL provider features own Prepare connectivity admission with the native
owned unit/deadline mechanisms. The generated empty context owns no product schema
or synthetic test table. Product schema migrations are explicit deployment-owned
commands; startup can admit their completed schema version read-only. Consumers
continue to test their own ownership, transactions, conflicts, replay and recovery.

For development-only response-policy candidates, an explicit `developmentCandidate`
input names a hashed consumer-local profile. That profile retains `baseProfile`,
uses `status: development-candidate`, and independently names the version, local
archive path and SHA256 of each changed response-policy owner. The renderer reads
typed metadata from those verified packages and creates an explicit local NuGet
route. It preserves the public default and captured base profile. Public adoption
still requires approved Foundation publication, immutable availability and fresh
exact-composition qualification.

Existing-consumer adoption is explicit: preserve accepted architecture history,
dependency profiles, native locks, custom configuration and data; review the new
composition responsibilities against existing projects; preview sync and resolve
managed conflicts without replacing custom files. Upgrade only the accepted scope,
rebuild selected roots and run applicable maintained readiness plus product-specific
regressions. Provider removal must remove its selected root/feature contribution
while preserving application data and deployment migration history. Live Notes and
De Sportomgeving adoption remain separate consumer actions.

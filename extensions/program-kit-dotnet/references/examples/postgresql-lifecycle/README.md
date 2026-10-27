# Native EF migrations with a Foundation context

`NativeMigrationContext` is an ordinary provider-owned EF model derived from the selected
`FoundationPostgreSqlDbContext`. Its mappings remain in `IEntityTypeConfiguration<T>`. The design-time
factory supplies Npgsql options directly for EF tooling without starting a shell/application host.
It does not supply runtime contexts. `NativeMigrationFeature` retains Foundation registration; its
read-only `NativeMigrationAdmission` initializer must succeed before activation. `NativeMigrationProbe`
then uses the actual shell, tracked unit lease and independently disposed context for an ordinary EF write.

The example's executable is a test host, not a migration runner to add to an application. Application
providers normally remain libraries. EF owns generated migrations, the snapshot, migration history
and deployment execution. Keep tooling's deployment credential outside runtime processes. The fixed
`ef_example` schema belongs only to this synthetic example; choose the real data owner's schema in
an application. Design-time and runtime must resolve the same mapping, schema and history location.

The existing `FixtureDeployment` and `FixtureContext` separately exercise synthetic ownership and
parallel lifecycle behavior. Their handwritten fixed SQL/journal must not be copied as an EF
application migration system. Native migrations do not use that journal or deployment code.

## Fast provider-test composition

Use `Program.cs` and `NativeMigrationProbe.cs` for focused actual-provider tests, not a bare
`ServiceCollection` resolving a native unit factory. That factory depends on the activated shell's
`IShell` lifecycle. The fixture registers `AddCShells`, activates the selected feature/configuration
through `IShellRegistry.GetOrActivateAsync`, and resolves the native lease factory from that shell.
For scoped application services, enter tracked `IShell.BeginScope()` and dispose the scope before
disposing the shell provider. Await/dispose each native unit and independently created context.
The root provider owns the shell registry; do not create a replacement shell or unit factory.

Deploy the isolated test schema with native EF under a separate deployment identity, then activate
the real read-only admission with the runtime identity. One provider operation and a denied owner
or schema case can establish the first small integration. This fixture needs PostgreSQL, not the
full application Host, Keycloak or a browser. Use those only for affected HTTP/login journeys.
Read the selected CShells APIs before choosing configuration dictionaries or scope methods; compile
this first small fixture before expanding a test collection. Reuse passing fixture evidence while
its relevant inputs/environment are unchanged. Pure domain tests remain in-process tests.

For selected CShells 0.0.31 disposable generation resources, use the
[verified non-owning admission workaround](../cshells-initializer-ownership/README.md).
`NativeMigrationAdmission` already separates admission from its native resource owner;
retain its read-only schema/privilege checks and actual native scope/lease lifetimes.

## Author and deploy with EF

Use the exact selected SDK, Foundation/CShells packages and EF Design version. Pin local `dotnet-ef`
to that Design version. The maintained qualifier supplies the project properties and existing tool
runtime; do not install a device SDK.
Pass MSBuild properties to `dotnet build`; `dotnet ef -p` means `--project`, not an MSBuild property.
Build with the required project properties first, then use `dotnet ef ... --no-build` where applicable.
From this example project, the standard operation sequence is:

```text
dotnet ef migrations add Initial --context NativeMigrationContext
dotnet build
dotnet ef migrations has-pending-model-changes --context NativeMigrationContext --no-build
dotnet ef migrations script --context NativeMigrationContext --idempotent --no-build --output migration.sql
```

Use the separately versioned analyzer's supported native EF declaration layout when selected.
Do not add a generated header, exclude the migrations directory or rewrite native operations merely
to satisfy layout. Authored helpers and arbitrary computations still need the selected source rules;
the main migration remains editable/reviewable. Keep migration identity, designer and snapshot intact.

Review the generated migration and SQL. Deployment sets `PK_FIXTURE_EF_DEPLOYMENT` from its secret
provider to the isolated target and uses the native EF deployment command, or produces a bundle:

```text
dotnet ef database update --context NativeMigrationContext --no-build
dotnet ef migrations bundle --context NativeMigrationContext --no-build --output efbundle
```

Select the supported artifact for the deployment environment; the qualifier exercises generated SQL
and native EF update, not every bundle platform. An EF bundle already is an executable deployment
artifact. A reviewed application migration may contain SQL or use a justified separate EF migrations
assembly; neither implies a second migration engine. SQL Server and SQLite need their own provider
qualification; SQLite cannot generate an idempotent migration script.

## Runtime admission and verification

Grant the runtime identity schema usage, only the owned table/sequence operations and read access to
EF history. It cannot create schema objects or write history. Startup admission reads required EF
migrations/model compatibility; it never calls `Migrate` or `EnsureCreated`. Keep compatibility policy
with the data owner; this example requires its exact current model, not a rolling-upgrade policy.

Run the existing focused validator from the Program Kit checkout:

```text
python scripts/run_validation.py --check validate_postgresql_lifecycle --reason "native EF/Foundation migration workflow and credential separation"
```

It generates migrations/snapshot in an isolated copy, builds them, checks model drift, emits reviewed
idempotent SQL, uses native EF deployment, repeats deployment without another history entry, and runs
the real Foundation context under least privileges. Denied deployment and missing history prevent
runtime effects. Existing journal/concurrency/ownership tests remain separate. All use one uniquely
owned pinned PostgreSQL container, with independently observed cleanup. No arbitrary coding agent,
production migration, cloud provider or consumer application acceptance is established.

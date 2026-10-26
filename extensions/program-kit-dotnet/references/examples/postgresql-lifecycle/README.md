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

## Author and deploy with EF

Use the exact selected SDK, Foundation/CShells packages and EF Design version. Pin local `dotnet-ef`
to that Design version. The maintained qualifier supplies the project properties and existing tool
runtime; do not install a device SDK. From this example project, the standard operation sequence is:

```text
dotnet ef migrations add Initial --context NativeMigrationContext
dotnet build
dotnet ef migrations has-pending-model-changes --context NativeMigrationContext --no-build
dotnet ef migrations script --context NativeMigrationContext --idempotent --no-build --output migration.sql
```

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

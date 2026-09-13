# Independent acceptance interface

These are implementation-phase test requirements, not bootstrap scaffolding.
The fixed HTTP and browser contracts are adjacent JSON files. The supervisor runs
the unchanged published Foundation image and owns container stop/restart, isolated PostgreSQL and
one persistent file-data path. `services.json` pins the real database used by this fictional trial.

When `ASPNETCORE_ENVIRONMENT=ProgramKitAcceptanceFixture`, use `ASPNETCORE_URLS` for
the loopback listener, `LENDING_FIXTURE_DATA` for isolated file artifacts,
and `LENDING_FIXTURE_WEB` for the compiled browser assets (`web/dist`). Implement the
documented `/__acceptance` controls only in this test environment. Normal deployment
must not expose reset/fault-injection controls. Honor the same durable path across a
real process restart; substituting a mock restart cannot pass the oracle.

Use the server-relational persistence default through normal per-owner admission. The supervisor
provides `LENDING_FIXTURE_DATABASE_PROVIDER=postgresql` and `LENDING_FIXTURE_CONNECTION_STRING`
for an isolated database; read the latter from the environment, never persist or log it. Workers
can test real EF/provider behavior without starting Docker. Host containers use the same service
through its private network. Process restart retains the database. Database restart is a separate
infrastructure check; it must not be substituted for process restart. HTTP and browser acceptance
each receive a fresh isolated database. `/__acceptance` reset is scoped to that fixture database.
Apply the reviewed migration artifact as explicit fixture deployment/setup; normal host startup
only checks schema compatibility. If the service environment is absent, report the missing fixture
setup instead of replacing PostgreSQL with an in-memory/file store or changing product architecture.
Record `testProvisioning: supervisor` in the feature's persistence admission. Provide explicit EF
design-time context creation from the fixture connection environment. Independent acceptance uses
the managed `dotnet-ef` pin to preserve an idempotent migration script and apply the migrations to
that fresh database before starting the unchanged Foundation host. Context identity may be declared
as `dbContext`; this never requires a consumer host project or image.

Keep the solution at `Lending.slnx` and expose `npm run verify` in `web/package.json`.
Produce artifacts/application-bundle.zip containing shells.json, hostsettings.json, nuplane.settings.json and optional NuGet feeds/packages for independent acceptance on the unchanged published Foundation host image. Do not create a host project, host DLL or consumer Dockerfile/image. Internal names and
implementation details remain feature decisions within the reviewed target placement.
The independent browser tools live outside the consumer; do not add Playwright/axe
to production dependencies just to satisfy the supervisor.

# Independent acceptance interface

These are implementation-phase test requirements, not bootstrap scaffolding.
The fixed HTTP and browser contracts are adjacent JSON files. The supervisor runs
the actual compiled host and owns process stop/restart and one persistent data path.

When `ASPNETCORE_ENVIRONMENT=ProgramKitAcceptanceFixture`, use `ASPNETCORE_URLS` for
the loopback listener, `LENDING_FIXTURE_DATA` for the isolated durable fixture state,
and `LENDING_FIXTURE_WEB` for the compiled browser assets (`web/dist`). Implement the
documented `/__acceptance` controls only in this test environment. Normal deployment
must not expose reset/fault-injection controls. Honor the same durable path across a
real process restart; substituting a mock restart cannot pass the oracle.

Keep the solution at `Lending.slnx` and expose `npm run verify` in `web/package.json`.
Record the produced API host DLL path for independent acceptance. Internal names and
implementation details remain feature decisions within the reviewed target placement.
The independent browser tools live outside the consumer; do not add Playwright/axe
to production dependencies just to satisfy the supervisor.

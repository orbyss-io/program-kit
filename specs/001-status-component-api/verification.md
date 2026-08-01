# Verification Record

Date: 2026-08-01

## Passing local evidence

```powershell
dotnet clean ProgramKit.slnx --configuration Debug
dotnet clean ProgramKit.slnx --configuration Release
./eng/Invoke-VerticalSliceQuickstart.ps1
```

The quickstart bootstraps the exact dependency mirror, performs a locked
restore, builds and tests in `Release`, and verifies formatting. Debug outputs
were cleaned first so acceptance tests could not pass against stale binaries.

The test run passed 23 tests: 15 unit, 4 contract, and 4 acceptance tests.
Acceptance coverage includes generated component/package/API construction,
admission, exact evaluation, drift/no-mutation, a relocated-style clean local
restore/build, runtime dependency inspection, host startup, and `/status`.

The exact dependency mirror is governed by
`eng/dependency-mirror.manifest.json` and
`eng/dependency-mirror.lock.json`; its downloaded package bytes remain ignored
local test input under `artifacts/dependency-mirror/`.

## Deliberately not claimed

The disabled historical `Program Kit integration` self-host check was not run
or awaited. No independent human product review has passed. The independent
`Vertical slice` Windows and Ubuntu pull-request jobs are required to pass
before merge; they do not replace the pending human product review.

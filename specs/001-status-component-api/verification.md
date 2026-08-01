# Verification Record

Date: 2026-08-01

## Passing local evidence

```powershell
dotnet restore ProgramKit.slnx --use-lock-file --configfile NuGet.Config
dotnet build ProgramKit.slnx --no-restore
dotnet test ProgramKit.slnx --no-build --no-restore --configuration Debug --verbosity minimal
dotnet format ProgramKit.slnx --no-restore --verify-no-changes
```

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
or awaited. No independent human product review has passed. Cross-platform CI
is configured but is not represented here as executed evidence until GitHub
reports it.

# Releasing Program Kit 0.8.6

This patch release closes the OpenAPI producer gap found during the first consumer implementation
flow. Components are `0.8.6`; runtime packages, the shallow host image, and the managed exporter tool
are `0.8.6-preview.1`.

The external `ProgramKit.Host` remains feature-free. The new exporter instead composes the consumer's
validated staged feature packages in a no-listener process, invokes feature service and endpoint
registration, suppresses hosted services and shell initializers, and asks ASP.NET Core for the raw
OpenAPI document. The managed pipeline then runs normalization/compatibility, the isolated client
generator lockfile, and the application TypeScript compile. Projects with an empty
`.program-kit/openapi-contracts.json` registry do not restore or run the exporter or npm stages.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet test ProgramKit.slnx -c Release --no-build --no-restore
python tests/validate_dotnet_consumer_restore.py
python tests/validate_dotnet_feature_host.py
python tests/validate_openapi_exporter.py
```

Existing consumers must update the workflow before the bundle, without running governance commands
between those updates:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

Replace `codex` with the repository's installed integration. Consumers using the accepted .NET
runtime profile then rerun their existing `dotnet_sync.py` command with the same accepted profile,
host-runtime, preview-source, persistence, and web-profile flags. The sync adds the managed exporter,
pipeline, schema, tool manifest, build integration, and an empty scaffold registry without changing
feature-owned source.

For an interrupted OpenAPI slice, remediate the existing plan/tasks before resuming implementation:

1. Register the consumer contract path in `.program-kit/openapi-contracts.json`.
2. Make that contract name the exact exporter `0.8.6-preview.1`, selected shell, every API-contributing
   feature, `artifacts/runnable-host/packages`, raw/artifact/baseline paths, pinned oasdiff approval,
   the isolated generator package/lock/script/output, and the application package/lock/typecheck/tsconfig.
3. Refresh `speckit.analyze`, the architecture check, and lifecycle readiness evidence because
   `PKA014` intentionally invalidates the prior incomplete readiness decision.
4. Initialize a reviewed first baseline once with
   `./eng/program-kit/Build.ps1 -LockedMode -InitializeOpenApiBaseline`; subsequent builds use
   `./eng/program-kit/Build.ps1 -LockedMode` and require explicit `-UpdateOpenApiArtifact` for a
   reviewed generated-contract update.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.6
git push origin main v0.8.6
```

The public catalog checks run after the release workflow publishes immutable assets:

```powershell
python tests/validate_public_install.py
python tests/validate_public_upgrade.py
```

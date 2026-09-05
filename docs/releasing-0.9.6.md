# Releasing Program Kit 0.9.6

This consumer-upgrade release corrects repository-isolated restore, Windows Git ownership handling,
OpenAPI toolchain discovery/evidence, and Program Kit versus application version authority.
Components are `0.9.6`; runtime packages and the host image are `0.9.6-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --force-evaluate --configfile NuGet.config
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build -p:PackageOutputPath="$PWD/artifacts/nuget"
python tests/validate_openapi_exporter.py
python tests/validate_keycloak_realm_import.py
```

The restricted-profile restore test must reproduce the direct ambient-config failure and pass through
`Restore.ps1`. The runnable-host commit test must exercise the command-scoped Git path without an
inherited `GITHUB_SHA`. The OpenAPI fixture must use an application `VERSION` different from Program
Kit and retain valid toolchain evidence when a discovery attempt fails.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.9.6
git push origin main v0.9.6
```

NuGet and host-image publication remain downstream reusable jobs of the complete Release validation
job. Do not announce or install 0.9.6 until the entire ordered workflow succeeds.

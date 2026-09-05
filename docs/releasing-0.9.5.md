# Releasing Program Kit 0.9.5

This corrective release carries the complete 0.9.4 feature set while repairing the two release-gate
defects exposed by its immutable tag. Components are `0.9.5`; runtime packages and the host image are
`0.9.5-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
python tests/validate_openapi_exporter.py
python tests/validate_keycloak_realm_import.py
```

The Git commit-resolution regression must additionally pass with an inherited `GITHUB_SHA`. The
resolved SDK must be exactly `10.0.202`, even on a runner that also contains a newer 10.0 patch.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.5
git push origin main v0.9.5
```

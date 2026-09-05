# Releasing Program Kit 0.9.8

This maintenance release prevents protected integration or profile destinations from causing a late,
partially applied upgrade. Components are `0.9.8`; runtime packages and the host image remain
`0.9.7-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --force-evaluate --configfile NuGet.config
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build -p:PackageOutputPath="$PWD/artifacts/nuget"
python tests/validate_local_upgrade.py
python tests/validate_web_security_assurance.py
python tests/validate_keycloak_realm_import.py
```

The local-upgrade regression must prove both zero-component-mutation `PKU115` handling and
idempotent convergence from a deliberate two-step partial installation. The release archive must
retain the updater and every component at `0.9.8`; runtime artifacts must remain exactly
`0.9.7-preview.1`. The topology fixture must reject both a disconnected desired model and stale
running attachments. Each clean Keycloak import must emit no missing-scope warning and reach the
real login form through its managed PAR request.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.9.8
git push origin main v0.9.8
```

NuGet and host-image jobs will rebuild, attest, skip already published identical runtime package
versions, and verify their public availability. If the release pipeline fails before a stable
release exists, repair the candidate and replace the failed tag with the fixed, explicitly approved
commit; do not create a drift version. Do not announce or install 0.9.8 until the entire ordered
workflow succeeds.

# Releasing Program Kit 0.9.7

This maintenance release corrects Windows sandbox upgrades, exact CShells feature identity,
managed persona-fixture loading, and the local Keycloak container backchannel. Components are
`0.9.7`; runtime packages and the host image are `0.9.7-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --force-evaluate --configfile NuGet.config
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build -p:PackageOutputPath="$PWD/artifacts/nuget"
python tests/validate_analyzer.py
python tests/validate_dotnet_feature_host.py
python tests/validate_openapi_exporter.py
python tests/validate_keycloak_realm_import.py
```

The Windows updater fixture must prove the release bridge performs every read-only Specify probe
without mutating the consumer. The dotted feature fixture must fail with `PK1006`, and both host and
exporter must reject absent or divergent runtime identities. The Keycloak smoke test must retain the
public issuer, authorization, and logout endpoints while exposing token, user-info, and JWKS through
the private backchannel.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.9.7
git push origin main v0.9.7
```

NuGet and host-image publication remain downstream reusable jobs of the complete Release validation
job. If that pipeline fails before a stable release exists, repair the candidate and replace the
failed tag with the fixed, explicitly approved commit; do not create a drift version. Do not announce
or install 0.9.7 until the entire ordered workflow succeeds.

# Releasing Program Kit 0.9.4

This release completes the packaged web-feature boundary and hardens the generated build, OpenAPI,
runtime-staging, identity-fixture, upgrade, and publication paths. Components are `0.9.4`; runtime
packages and the host image are `0.9.4-preview.1`, producing one coherent immutable artifact set.

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

The candidate must prove that profile-owned and consumer-owned shell inputs produce one effective
feature graph; that OpenAPI export fails closed when toolchain or runtime-closure evidence is stale;
that managed .NET/NuGet operations cannot consume ambient caches or user configuration; that both
generated Keycloak realms import into the exact pinned image; and that upgrade preflights cause no
mutation when Specify is unavailable or runtime lock renewal remains outstanding.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.4
git push origin main v0.9.4
```

The NuGet workflow verifies every package through the public NuGet flat-container endpoint. The host
workflow records its digest-pinned image reference in a release asset. Publication is complete only
when both artifacts are independently usable and their evidence is attached to the GitHub release.

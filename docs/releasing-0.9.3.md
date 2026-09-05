# Releasing Program Kit 0.9.3

This corrective release makes managed producer-pin upgrades explicit, atomic, and lifecycle-safe.
Components are `0.9.3`; runtime packages and the host image are `0.9.3-preview.1` so the tag
publishes one coherent immutable artifact set.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

The candidate must additionally exercise the full upgrade/pre-implementation chain: seed a consuming
repository with a registered OpenAPI contract and implementation-ready lifecycle on the prior
exporter pin; prove the default upgrade stops before mutation with the exact affected-file list;
explicitly reconcile contract, plan, tasks, and research atomically; prove managed sync and complete
artifact ownership are clean; prove the combined implementation preflight blocks the invalidated
lifecycle; renew after-tasks analysis; and prove that same full preflight then succeeds.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.3
git push origin main v0.9.3
```

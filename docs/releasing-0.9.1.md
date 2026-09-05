# Releasing Program Kit 0.9.1

This patch aligns the selected-profile source model, BFF identity contract, consumer-owned state,
runnable-host schema, and managed workflow extension points. Components are `0.9.1`; changed runtime
packages and the host image are `0.9.1-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

The candidate must additionally prove exact Keycloak client sets on clean BFF/SPA installs and both
transition directions; authenticated legacy-hostsettings retirement plus customized-value conflict;
clean `--check` results after valid consumer extension-point edits; descriptor/schema validation;
verification-hook absence, presence, failure, preservation, and path safety; and direct compilation
and execution of the BFF session adapter tests.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.1
git push origin main v0.9.1
```

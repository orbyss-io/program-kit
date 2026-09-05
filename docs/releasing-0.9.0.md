# Releasing Program Kit 0.9.0

This release moves all Program Kit web policy out of `ProgramKit.Host` and into separately packaged
CShells features. Components are `0.9.0`; runtime packages and the host image are
`0.9.0-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

The candidate must also prove fresh BFF-cookie and SPA-PKCE synchronization, all six directed
profile transitions, legacy SPA-residue migration, zero-mutation conflict handling, injected
rollback, packaged CShell feature activation, CORS, correlation/security headers, and the default
Problem Details response.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.0
git push origin main v0.9.0
```

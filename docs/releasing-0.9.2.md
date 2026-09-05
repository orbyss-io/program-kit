# Releasing Program Kit 0.9.2

This corrective release makes after-tasks severity evidence structural and retry-safe. Components
are `0.9.2`; runtime packages and the host image are `0.9.2-preview.1` so the tag publishes one
coherent immutable artifact set.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

The candidate must additionally prove that the canonical PriceCalculator clean report parses with
zero findings; severity labels in headings, legends, prose, and zero-valued metrics are ignored;
MEDIUM/LOW rows are recorded without blocking; HIGH/CRITICAL rows block; malformed and duplicate
tables fail explicitly; malformed evidence retains the active run; and corrected evidence can retry
completion without restarting analysis.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.9.2
git push origin main v0.9.2
```

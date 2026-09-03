# Releasing Program Kit 0.8.11

This corrective release makes constitution ratification byte-preserving. Components are `0.8.11`;
runtime packages and the host image are `0.8.11-preview.1` so the tag publishes immutable artifacts.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

## Recovery from the 0.8.10 ratification mutation

Upgrade with the verified full 0.8.11 release from a normal user-owned terminal. Then run the
installed governance script's `begin` command. It opens Draft state and embeds the existing faulty
ratification record as `previous_ratification`; do not edit that JSON.

Restore the constitution itself to the exact reviewed Draft: change only the status back to Draft and
reinsert `## Core Principles` at its reviewed location. Validate and regenerate the packet:

```powershell
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-constitution-draft
python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage constitution
```

For the reported PriceCalculator case, require the regenerated review-basis SHA-256 to equal
`32f631012c877843e748e73e085b8af57ef9192981d6cf1db2d8f50792a03f7f`. Any mismatch means the reviewed
draft was not restored exactly and ratification must remain paused. After an exact match, show the
packet and obtain a new dedicated `ratify` verdict. Only then may architecture work resume.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.11
git push origin main v0.8.11
```

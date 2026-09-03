# Releasing Program Kit 0.8.10

This corrective release makes upgrades fail closed across the Program Kit bundle, workflow, two
extensions, governance preset, and existing managed .NET baseline. Components are `0.8.10`; runtime
packages and the host image are `0.8.10-preview.1` so the tag publishes immutable artifacts.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

## Existing consumer upgrade

Download `program-kit-0.8.10.zip` and `SHA256SUMS` from the release, verify the archive, and extract it.
From a normal user-owned terminal in the consumer repository, run:

```powershell
python C:\path\to\program-kit-0.8.10\scripts\upgrade_program_kit.py --release-root C:\path\to\program-kit-0.8.10 --target . --integration codex
```

The command is offline after extraction. It replaces the old remote workflow/bundle update sequence,
runs all component mutations sequentially, synchronizes an existing managed .NET baseline from its
recorded profiles, validates complete version coherence, and records Accepted upgrade authority
without modifying hash-bound bootstrap decisions before returning zero.

For a constitution draft already opened under an older Program Kit release, finish the upgraded
gate with the installed governance script:

```powershell
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-constitution-draft
python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage constitution
```

Review `docs/architecture/reviews/constitution-review.md`, then provide the dedicated `ratify`
verdict through the normal constitution ratification command. Future `speckit.constitution` runs
perform the validation and review regeneration through the mandatory post-hook.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.10
git push origin main v0.8.10
```

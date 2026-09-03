# Releasing Program Kit 0.8.5

This patch release corrects .NET Package Source Mapping after the first consumer implementation
flow exposed that Program Kit's exhaustive public package-ID list blocked legitimate direct and
transitive dependencies. Components are `0.8.5`; runtime packages and the shallow host image are
`0.8.5-preview.1`.

The generated `NuGet.config` now uses nuget.org as the default public-package route while retaining
more-specific protected mappings for the approved CShells and Nuplane preview feeds. An unchanged
Program Kit-managed configuration receives this correction once and then transfers to consumer
ownership. Consumers may add private feeds with namespace-specific mappings; sync accepts valid
extensions and rejects unsafe catch-all or protected-namespace reassignment.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
python tests/validate_dotnet_consumer_restore.py
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet test ProgramKit.slnx -c Release --no-build --no-restore
python tests/validate_dotnet_feature_host.py
```

Existing consumers must update the workflow before the bundle, without running governance commands
between those updates:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

Replace `codex` with the repository's installed integration. Consumers using the accepted .NET
runtime profile must then run the same `dotnet_sync.py` command and profile flags used for their
current baseline. An unchanged 0.8.4 `NuGet.config` is migrated automatically. If it was modified,
merge the new nuget.org `*` route with the protected CShells/Nuplane routes explicitly; no
consumer-selected public package IDs or transitive dependencies should be enumerated.

After synchronization, rerun the interrupted `dotnet restore --force-evaluate`. This release does
not require changes to the feature specification, plan, or tasks because it changes source routing
rather than feature architecture. If the upgrade reports lifecycle evidence drift, refresh the
existing pre-implementation verification before continuing the paused implementation task.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.5
git push origin main v0.8.5
```

The public catalog checks require both the immutable tag and its GitHub release assets, so run them
after the release workflow publishes those assets; they are also the workflow's final verification
steps:

```powershell
python tests/validate_public_install.py
python tests/validate_public_upgrade.py
```

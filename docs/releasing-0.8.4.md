# Releasing Program Kit 0.8.4

This patch release hardens the first real specification and implementation lifecycle following a
live bootstrap. Components are `0.8.4`; runtime packages and the shallow host image are
`0.8.4-preview.1`.

It makes selected Program Kit package and SDK pins authoritative, rejects consumer-owned host
projects when the external `ProgramKit.Host` profile is selected, validates npm peer compatibility
before implementation readiness, and improves per-user Node remediation on Windows. It also adds
the separately authorized live first-slice continuation and corrects the Windows Git and validation
false positives it exposed.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
python tests/validate_dotnet_feature_host.py
```

The paid live suite is entirely user-invoked and is not a publication prerequisite. Do not ask to
run it or report it as skipped. Its bootstrap plus first-slice continuation was explicitly approved
and exercised while preparing this release; the retained consumer passed corrected deterministic
revalidation after the harness findings were repaired.

Existing consumers must update the workflow before the bundle, without running governance commands
between those updates:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

Replace `codex` with the repository's installed integration. Consumers using the accepted .NET
runtime profile must then synchronize managed files with the already accepted profile selections.
For an external host, SPA PKCE, and PostgreSQL consumer:

```powershell
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py `
  --target . `
  --profile-selected `
  --host-runtime-accepted `
  --preview-sources-approved `
  --web-profile spa-pkce `
  --persistence-profile ef-postgresql
```

Review any reported consumer-owned conflicts instead of overwriting them. After synchronization,
rerun the feature's architecture analysis and `verify-before-implement` so stale readiness evidence
cannot survive the stronger host and dependency-graph contracts.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.4
git push origin main v0.8.4
```

The public catalog checks require both the immutable tag and its GitHub release assets, so run them
after the release workflow publishes those assets; they are also the workflow's final verification
steps:

```powershell
python tests/validate_public_install.py
python tests/validate_public_upgrade.py
```

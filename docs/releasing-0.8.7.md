# Releasing Program Kit 0.8.7

This patch hardens the first real consumer implementation flow. Components are `0.8.7`; unchanged
runtime packages, shallow host image, and managed OpenAPI exporter remain `0.8.6-preview.1`.

The release carries exact Node/npm command evidence into every managed npm subprocess, uses
repository-owned npm and NuGet caches, preserves strict TLS with system/organization CA support,
binds restores to the repository `NuGet.config`, selects Microsoft Testing Platform, seeds activated
built-in runtime packages, and makes implementation checkbox progress lifecycle-safe.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
```

Existing consumers update the workflow before the bundle, without running governance commands
between those updates:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

Replace `codex` with the installed integration, then rerun the existing .NET profile sync command.
The sync adds `.npm-version`, `js_toolchain.py`, repository cache ownership, MTP selection, and the
corrected managed build/runtime staging files. Run `eng/program-kit/toolchain.py` once before resuming
an npm or OpenAPI stage; its evidence records the exact commands and trust/cache policy.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.7
git push origin main v0.8.7
```

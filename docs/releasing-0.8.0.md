# Releasing Program Kit 0.8.0

> Withdrawn: do not publish these artifacts. Use the corrective 0.8.1
> [release runbook](releasing-0.8.1.md).

This minor release adds executable lifecycle, API-contract, feature-activation, SPA-security,
preflight/readiness, toolchain, persistence-profile, ownership, and UTF-8 capabilities. The Program
Kit components are `0.8.0`; changed runtime packages and host image are `0.8.0-preview.1`.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify `VERSION` is `0.8.0`, `RUNTIME_VERSION` is `0.8.0-preview.1`, component manifests and
catalogs agree, and `artifacts/SHA256SUMS` covers:

- `program-kit-0.8.0.zip`
- `program-kit-governance-0.8.0.zip`
- `program-kit-dotnet-0.8.0.zip`
- `program-kit-governance-preset-0.8.0.zip`
- `program-kit-bootstrap-0.8.0.zip`
- `Initialize-ProgramKit-0.8.0.cmd`
- `Initialize-ProgramKit-0.8.0.sh`

Existing consumers upgrade in this order so Spec Kit 1.0.1 cannot leave a mixed workflow/bundle:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --host-runtime-accepted --preview-sources-approved
```

Replace `codex` with the repository's integration. Add an explicit `--web-profile` or
`--persistence-profile` only when existing Accepted evidence selects it. Review scaffold-once
consumer files and any newly required root MSBuild/Vite imports; synchronization never overwrites
them or evidence files. Use `docs/compatibility-0.8.0.md` as the migration checklist.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.0
git push origin main
git push origin v0.8.0
```

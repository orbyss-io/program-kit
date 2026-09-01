# Releasing Program Kit 0.6.11

This patch corrects final-review ADR totals and adds an explicit, audited recovery path for a
hard-terminated bootstrap run that remains persisted as `running`. It prevents concurrent bootstrap
runs from mutating the same governed artifacts and preserves abandoned run history.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.11`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.11.zip`
- `program-kit-governance-0.6.11.zip`
- `program-kit-dotnet-0.6.11.zip`
- `program-kit-governance-preset-0.6.11.zip`
- `program-kit-bootstrap-0.6.11.zip`
- `Initialize-ProgramKit-0.6.11.cmd`
- `Initialize-ProgramKit-0.6.11.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes governance
review reporting, bootstrap run recovery, tests, guidance, and distribution metadata only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.11
git push origin main
git push origin v0.6.11
```

After publication, verify the release workflow, public catalogs, provenance attestations, SHA-256
digests, downloadable initializers, and the public install/upgrade regressions.

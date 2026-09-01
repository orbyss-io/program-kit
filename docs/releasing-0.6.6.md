# Releasing Program Kit 0.6.6

This patch makes the consumer integration explicit, validates the full Python resolver dependency
chain during setup, provides a precise PyYAML repair path, and prevents a failed preflight from
dispatching a nonexistent diagnostic integration.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.6`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.6.zip`
- `program-kit-governance-0.6.6.zip`
- `program-kit-dotnet-0.6.6.zip`
- `program-kit-governance-preset-0.6.6.zip`
- `program-kit-bootstrap-0.6.6.zip`
- `Initialize-ProgramKit-0.6.6.cmd`
- `Initialize-ProgramKit-0.6.6.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
distribution, dependency setup, preflight behavior, and guidance only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.6
git push origin main
git push origin v0.6.6
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests, and
both downloadable initializers before marking the release usable.

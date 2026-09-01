# Releasing Program Kit 0.6.10

This patch fixes upgrades from releases whose initializers registered immutable release-tag
catalog URLs. Initialization still resolves its advertised release from immutable catalogs, then
hands the four registrations to the trusted `main` update channel after installation succeeds.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.10`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.10.zip`
- `program-kit-governance-0.6.10.zip`
- `program-kit-dotnet-0.6.10.zip`
- `program-kit-governance-preset-0.6.10.zip`
- `program-kit-bootstrap-0.6.10.zip`
- `Initialize-ProgramKit-0.6.10.cmd`
- `Initialize-ProgramKit-0.6.10.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes catalog
registration, upgrade tests, recovery guidance, and distribution metadata only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.10
git push origin main
git push origin v0.6.10
```

After publication, verify the release workflow, live pinned-catalog upgrade, public catalogs,
provenance attestations, SHA-256 digests, and downloadable initializers.

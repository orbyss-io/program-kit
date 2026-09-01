# Releasing Program Kit 0.6.9

This patch makes the specification roadmap authoritative for roadmap-entry status, synchronizes
derived architecture and traceability views, validates cross-artifact consistency before final
review and approval, exposes completion stderr, and adds clean-consumer completion coverage.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.9`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.9.zip`
- `program-kit-governance-0.6.9.zip`
- `program-kit-dotnet-0.6.9.zip`
- `program-kit-governance-preset-0.6.9.zip`
- `program-kit-bootstrap-0.6.9.zip`
- `Initialize-ProgramKit-0.6.9.cmd`
- `Initialize-ProgramKit-0.6.9.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
governance, workflow orchestration, validation, tests, and guidance only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.9
git push origin main
git push origin v0.6.9
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests,
public catalogs, and downloadable initializers before marking the release usable.

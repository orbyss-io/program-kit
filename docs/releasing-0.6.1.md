# Releasing Program Kit 0.6.1

This patch makes native Windows bootstrap compatible with enforced PowerShell script signing by
standardizing Codex consumers on Spec Kit's Python resolver.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.1`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.1.zip`
- `program-kit-governance-0.6.1.zip`
- `program-kit-dotnet-0.6.1.zip`
- `program-kit-governance-preset-0.6.1.zip`
- `program-kit-bootstrap-0.6.1.zip`
- `Initialize-ProgramKit-0.6.1.cmd`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
and distribution behavior only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.1
git push origin main
git push origin v0.6.1
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests, and
the downloadable initializer before marking the release usable.

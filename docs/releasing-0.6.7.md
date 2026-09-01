# Releasing Program Kit 0.6.7

This patch establishes the Git work tree required by coding-agent workflows during consumer
initialization and rejects an unusable Codex repository trust boundary before intake.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.7`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.7.zip`
- `program-kit-governance-0.6.7.zip`
- `program-kit-dotnet-0.6.7.zip`
- `program-kit-governance-preset-0.6.7.zip`
- `program-kit-bootstrap-0.6.7.zip`
- `Initialize-ProgramKit-0.6.7.cmd`
- `Initialize-ProgramKit-0.6.7.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
distribution, Git initialization, preflight behavior, and guidance only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.7
git push origin main
git push origin v0.6.7
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests, and
both downloadable initializers before marking the release usable.

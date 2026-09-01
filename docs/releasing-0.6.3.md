# Releasing Program Kit 0.6.3

This patch adds a Bash consumer initializer for Linux, macOS, and WSL while retaining the command
launcher for Windows environments that enforce PowerShell `AllSigned`.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.3`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.3.zip`
- `program-kit-governance-0.6.3.zip`
- `program-kit-dotnet-0.6.3.zip`
- `program-kit-governance-preset-0.6.3.zip`
- `program-kit-bootstrap-0.6.3.zip`
- `Initialize-ProgramKit-0.6.3.cmd`
- `Initialize-ProgramKit-0.6.3.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
distribution and regression behavior only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.3
git push origin main
git push origin v0.6.3
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests, and
both downloadable initializers before marking the release usable.

# Releasing Program Kit 0.6.8

This patch makes Git initialization an explicit user action. Both consumer launchers fail before
package installation or repository setup and print immediate recovery commands when the directory
is not already inside a Git work tree.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.8`, `RUNTIME_VERSION` remains `0.6.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.8.zip`
- `program-kit-governance-0.6.8.zip`
- `program-kit-dotnet-0.6.8.zip`
- `program-kit-governance-preset-0.6.8.zip`
- `program-kit-bootstrap-0.6.8.zip`
- `Initialize-ProgramKit-0.6.8.cmd`
- `Initialize-ProgramKit-0.6.8.sh`

The runtime NuGet packages and host image remain at `0.6.0-preview.1`; this patch changes bootstrap
distribution, Git preflight behavior, tests, and guidance only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.8
git push origin main
git push origin v0.6.8
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests, and
both downloadable initializers before marking the release usable.

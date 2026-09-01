# Releasing Program Kit 0.7.2

This patch removes the remaining whitespace sensitivity from constitution metadata validation. The
validator parses the three unique fields independently inside Governance, preserves their required
order, and retains semantic-version, date, Draft, and human-ratification checks.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.7.2`, `RUNTIME_VERSION` remains `0.7.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.7.2.zip`
- `program-kit-governance-0.7.2.zip`
- `program-kit-dotnet-0.7.2.zip`
- `program-kit-governance-preset-0.7.2.zip`
- `program-kit-bootstrap-0.7.2.zip`
- `Initialize-ProgramKit-0.7.2.cmd`
- `Initialize-ProgramKit-0.7.2.sh`

The runtime NuGet packages and host image remain at `0.7.0-preview.1`; this patch changes governance
validation, regression coverage, guidance, and distribution metadata only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.7.2
git push origin main
git push origin v0.7.2
```

After publication, verify the release workflow, public catalogs, provenance attestations, SHA-256
digests, downloadable initializers, and the public install/upgrade regressions.

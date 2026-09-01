# Releasing Program Kit 0.7.1

This patch makes constitution metadata parsing agree with valid Markdown produced by the Codex
constitution step. The governance validator now accepts both the canonical pipe-separated metadata
row and three adjacent metadata lines without weakening field order, semantic-version, date, Draft,
or human-ratification checks.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.7.1`, `RUNTIME_VERSION` remains `0.7.0-preview.1`, all component
manifests and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.7.1.zip`
- `program-kit-governance-0.7.1.zip`
- `program-kit-dotnet-0.7.1.zip`
- `program-kit-governance-preset-0.7.1.zip`
- `program-kit-bootstrap-0.7.1.zip`
- `Initialize-ProgramKit-0.7.1.cmd`
- `Initialize-ProgramKit-0.7.1.sh`

The runtime NuGet packages and host image remain at `0.7.0-preview.1`; this patch changes governance
validation, regression coverage, guidance, and distribution metadata only.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.7.1
git push origin main
git push origin v0.7.1
```

After publication, verify the release workflow, public catalogs, provenance attestations, SHA-256
digests, downloadable initializers, and the public install/upgrade regressions.

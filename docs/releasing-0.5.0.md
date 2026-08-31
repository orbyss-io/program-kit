# Releasing Program Kit 0.5.0

This release establishes the permanent component boundary:

- `program-kit` is the umbrella bundle only.
- `program-kit-governance` contains technology-neutral governance behavior.
- `program-kit-dotnet` contains the opt-in .NET capability.
- `program-kit-governance-preset` augments core templates through `append` composition.
- `program-kit-bootstrap` remains the orchestrating workflow.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION`, `RUNTIME_VERSION`, component manifests, catalogs, and the generated checksum file
all agree. The release must contain these five ZIP assets plus `SHA256SUMS`:

- `program-kit-0.5.0.zip`
- `program-kit-governance-0.5.0.zip`
- `program-kit-dotnet-0.5.0.zip`
- `program-kit-governance-preset-0.5.0.zip`
- `program-kit-bootstrap-0.5.0.zip`

Then create the matching immutable tag:

```powershell
git tag v0.5.0
git push origin v0.5.0
```

After publication, verify the GitHub provenance attestation and the recorded SHA-256 digest before
marking the catalog release as usable.

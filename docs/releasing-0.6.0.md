# Releasing Program Kit 0.6.0

This release makes bootstrap opinionated by default and fail-closed at every human boundary:

- concise review packets replace noisy raw-artifact prompts;
- explicit intake choices and versioned Program Kit defaults become one approved baseline;
- `ProgramKit.Host` is the automatic .NET default unless intake records a justified opt-out;
- rejection pauses for revision and requires packet regeneration before approval;
- constitution ratification consumes the actual gate result and deterministically finalizes status
  and the initial ratification date; and
- stale, missing, malformed, or post-approval artifacts prevent downstream completion.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.6.0`, `RUNTIME_VERSION` is `0.6.0-preview.1`, all component manifests
and catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.6.0.zip`
- `program-kit-governance-0.6.0.zip`
- `program-kit-dotnet-0.6.0.zip`
- `program-kit-governance-preset-0.6.0.zip`
- `program-kit-bootstrap-0.6.0.zip`

The same tag starts publication of immutable `0.6.0-preview.1` NuGet packages and the
`ghcr.io/orbyss-io/program-kit-host:0.6.0-preview.1` image through their protected environments.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.6.0
git push origin main
git push origin v0.6.0
```

After publication, verify the GitHub release checks, provenance attestations, SHA-256 digests,
NuGet packages, and GHCR image before marking the release usable.

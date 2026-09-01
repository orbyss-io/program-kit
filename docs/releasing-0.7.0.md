# Releasing Program Kit 0.7.0

This feature release makes authenticated browser boundaries executable bootstrap profiles. It adds
the secure-default BFF/cookie runtime, the explicit direct SPA PKCE alternative, validated settings,
Keycloak fixtures, role personas, local developer commands, safe HTTP/health/telemetry defaults, and
mandatory Playwright contract evidence.

The release also ships the versioned browser threat model and machine-readable security evidence
register. Release validation must prove complete threat/control/source/default/verification/review
traceability, honest normative-status labels, exact assurance IDs in both profiles, and managed
assurance snapshots in clean consumers.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION` is `0.7.0`, `RUNTIME_VERSION` is `0.7.0-preview.1`, all component manifests and
catalogs agree, and `artifacts/SHA256SUMS` covers these release assets:

- `program-kit-0.7.0.zip`
- `program-kit-governance-0.7.0.zip`
- `program-kit-dotnet-0.7.0.zip`
- `program-kit-governance-preset-0.7.0.zip`
- `program-kit-bootstrap-0.7.0.zip`
- `Initialize-ProgramKit-0.7.0.cmd`
- `Initialize-ProgramKit-0.7.0.sh`

The runtime publication produces the `0.7.0-preview.1` NuGet packages and digest-addressable
`ProgramKit.Host` image. Verify the Keycloak image digest in the generated Compose fixture and the
locked ASP.NET Core 10.0.11 packages again immediately before tagging.

Review `web-security-evidence.json` immediately before tagging. Confirm that primary-source links
and statuses remain current, especially the non-final IETF browser-app draft, and update
`lastReviewed` only after that review. A material change to a threat, control, assumption, residual
risk, or profile behavior requires compatibility analysis and potentially a new profile version.

Create and push the matching immutable tag only from the validated release commit:

```powershell
git tag v0.7.0
git push origin main
git push origin v0.7.0
```

After publication, verify the release workflow, public catalogs, provenance attestations, SHA-256
digests, downloadable initializers, host image, and the public install/upgrade regressions.

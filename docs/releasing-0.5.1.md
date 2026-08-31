# Releasing Program Kit 0.5.1

This patch release closes the approval boundary around the optional .NET repository baseline:

- write-mode sync requires an Accepted Program Kit host/runtime ADR;
- adding preview packages and NuGet sources requires explicit human approval;
- drift checks remain local and read-only without those write approvals;
- networked restore and build verification require separate authorization; and
- technology-neutral governance and proposed quality gates do not depend on the optional runtime sync.

Before tagging, run from a normal user-owned PowerShell or WSL terminal:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Verify that `VERSION`, `RUNTIME_VERSION`, component manifests, catalogs, and the generated checksum file
all agree. The release must contain these five ZIP assets plus `SHA256SUMS`:

- `program-kit-0.5.1.zip`
- `program-kit-governance-0.5.1.zip`
- `program-kit-dotnet-0.5.1.zip`
- `program-kit-governance-preset-0.5.1.zip`
- `program-kit-bootstrap-0.5.1.zip`

The same tag publishes immutable `0.5.1-preview.1` NuGet packages and the
`ghcr.io/orbyss-io/program-kit-host:0.5.1-preview.1` image through their protected environments.

Then create the matching immutable tag:

```powershell
git tag v0.5.1
git push origin v0.5.1
```

After publication, verify the GitHub provenance attestation and the recorded SHA-256 digest before
marking the catalog release as usable. Verify the NuGet package attestations and GHCR image provenance before
approving their use in consuming repositories.

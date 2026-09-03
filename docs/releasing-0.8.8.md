# Releasing Program Kit 0.8.8

This release establishes the semantic Core and named runtime-implementation architecture discovered
through the first real consumer flow. Components are `0.8.8`; changed runtime packages, the
application-neutral host image, and the managed OpenAPI exporter are `0.8.8-preview.1`.

The release replaces generic horizontal layer and `.Feature` project topology with domain-specific
`.Core`, implementation, `.Api`, provider, bridge, helper, and composition packages. `PKA015`
enforces exact role/reference graphs, activated capability implementations, provider-independent
endpoints, Core package boundaries, and explicit decision/test evidence for every direct Core-to-Core
edge.

It also publishes lightweight `ProgramKit.DomainEvents.Abstractions` and the default awaited,
scoped, sequential, bounded, non-durable `ProgramKit.DomainEvents` runtime feature. Durable
Integration Events remain deliberately separate and require the tracked outbox architecture before
first use. `ProgramKit.Host` now owns the selected secure web profile and maps provider roles/scopes
to canonical application permissions, while consumer `.Api` packages own routes and permission
metadata.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
```

The paid live bootstrap and first-slice continuation remain entirely user-invoked. Publication does
not prompt for them or record them as skipped.

Existing consumers update the workflow before the bundle, without running governance commands
between those updates:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

This release intentionally changes the planning ownership schema. Existing in-progress feature
plans require architecture remediation before implementation; a fresh consumer receives the new
model during bootstrap.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.8
git push origin main v0.8.8
```

The tag publishes the Program Kit component archives, the `0.8.8-preview.1` NuGet packages,
including both DomainEvents packages, and the multi-architecture
`ghcr.io/orbyss-io/program-kit-host:0.8.8-preview.1` image. Verify all three workflows and their
attestations before announcing the release as usable.

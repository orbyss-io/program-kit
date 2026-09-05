# Releasing Program Kit 0.9.5

This corrective release carries the complete 0.9.4 feature set while repairing the two release-gate
defects exposed by its immutable tag. Components are `0.9.5`; runtime packages and the host image are
`0.9.5-preview.1`.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
python tests/validate_openapi_exporter.py
python tests/validate_keycloak_realm_import.py
```

The Git commit-resolution regression must additionally pass with an inherited `GITHUB_SHA`. The
resolved SDK must be exactly `10.0.202`, even on a runner that also contains a newer 10.0 patch.

Create and push the stable tag only from the validated release commit:

```powershell
git tag v0.9.5
git push origin main v0.9.5
```

## Publication ordering

Stable publication is ordered so that reversible validation completes before registry writes:

1. The `Release` job restores and builds with the pinned SDK and lock files.
2. It packs the built-in feature packages needed by the OpenAPI consumer integration test.
3. It runs all deterministic release, consumer, component, and public upgrade validation.
4. Only after that job succeeds does it call the NuGet and host-image publication workflows.

The NuGet and host-image workflows use `workflow_call`; they do not react independently to a pushed
stable tag. This makes a failed candidate tag recoverable: fix and validate the release, obtain
approval for the corrected commit, delete and recreate the same tag at that commit, and rerun the
full ordered pipeline. A failed candidate is not a reason to create the next stable version.

If an older workflow published an immutable artifact before this ordering was introduced, record and
disclose that partial publication during recovery. Do not announce the release to consumers until the
recreated tag's complete Release workflow succeeds.

## Failed-candidate incident record

The first `v0.9.5` candidate at commit
`906d696f62400911922f7e7eaa8631d827117c25` failed before creating the GitHub release because the
Release workflow had not packed the built-in features required by its OpenAPI integration test.
Independent publication workflows had already pushed all twelve `0.9.5-preview.1` NuGet packages and
the multi-architecture host image. The canceled host job published
`ghcr.io/orbyss-io/program-kit-host:0.9.5-preview.1` at
`sha256:fb79b7c34027ed6cc8a03bb5b8737f442255c091303101a7cdac753333af02fb`, but did not create or attest
the host-image release evidence file.

The corrected candidate changes release orchestration, validation, contributor guidance, and this
release record only; it does not change the runtime package or host-image source. The recreated tag's
ordered pipeline must rebuild, validate, and publish the missing release evidence before `v0.9.5` is
announced to consumers.

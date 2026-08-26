# Program Kit .NET runtime and application bundles

Program Kit's .NET profile uses a standard host and independently packaged CShells features. Selecting the
.NET profile is an explicit architecture decision. Installing Program Kit alone never creates .NET files.

## Repository baseline

Run the installed `speckit.program-kit-governance.dotnet-sync` extension command only after the repository has
accepted the .NET profile. Root `Directory.*`, `VERSION`, `shells.json`, and `hostsettings.json` files are
scaffolded once and become consumer-owned. Program Kit hash-manages `global.json`, `NuGet.config`, the root
`.editorconfig`, generated workflows, and distinct `ProgramKit.*` implementation files under `eng/program-kit`.
All managed paths are tracked in `.program-kit/managed.json`; a consumer edit causes a reported conflict rather
than an overwrite.

Updating the Program Kit bundle updates the extension and templates. It does not rewrite the repository.
Run the sync command separately, review its report, and resolve conflicts explicitly.

The first local `eng/program-kit/Build.ps1 -SkipBundle` restore creates `packages.lock.json` files. Commit those
files. Generated CI and release workflows pass `-LockedMode`, so dependency changes must be reviewed and
regenerated deliberately.

## Application deployment bundle

`eng/program-kit/Build.ps1` restores, builds, tests, packs, resolves the runtime NuGet closure, and creates
`artifacts/application-bundle.zip`. The ZIP contains a manifest, digests, shell and host configuration,
deployment instructions, and every required `.nupkg`. It contains no secrets and is not a self-contained host.

ProgramKit.Host verifies and safely extracts the ZIP before constructing configuration. Configuration order is
host defaults, environment-specific defaults, bundle host settings, bundle shell structure, environment
variables, then command-line arguments. Environment variables therefore override bundled structure.

## Runtime administration

The preview host exposes read-only `/health/live`, `/health/ready`, and `/_program-kit/bundle` endpoints. It deliberately does not
expose an unauthenticated package or shell refresh mutation. A bundle digest is immutable for one process;
updating an application means publishing and deploying a new layered image. A future refresh endpoint requires
an accepted authentication, authorization, quiescence, rollback, and audit contract.

## Containers

The first deployment format is a layered container image. Set the consuming repository's
`PROGRAMKIT_HOST_IMAGE` GitHub Actions variable to a digest-pinned host image such as
`ghcr.io/orbyss-io/program-kit-host@sha256:<digest>`. The generated release workflow publishes the ZIP and,
when that variable is configured, builds and pushes an application image containing only the ZIP layer.

Docker, Kubernetes, and Azure Web App for Containers run the same application image. Runtime package feeds,
directory watching, and automatic reconciliation are disabled by default.

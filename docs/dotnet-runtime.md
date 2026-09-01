# Program Kit .NET runtime and application bundles

Program Kit's .NET profile uses a standard host and independently packaged CShells features. Selecting the
.NET profile automatically adopts `ProgramKit.Host` unless intake explicitly opts out and records why.
Installing Program Kit alone never creates .NET files.

## Repository baseline

Run the installed `speckit.program-kit-dotnet.sync` extension command in write mode only after the repository
has an approved bootstrap baseline (or later Accepted override) selecting the .NET profile and
`ProgramKit.Host`, and the human-reviewed baseline acknowledges the pinned preview packages plus the
`CShells Preview` and `Nuplane Preview` NuGet sources. A read-only `--check` remains safe before those write
approvals. Root `Directory.*`, `VERSION`, `shells.json`, and `hostsettings.json` files are
scaffolded once and become consumer-owned. Program Kit hash-manages `global.json`, `NuGet.config`, the root
`.editorconfig`, generated workflows, and distinct `ProgramKit.*` implementation files under `eng/program-kit`.
All managed paths are tracked in `.program-kit/managed.json`; a consumer edit causes a reported conflict rather
than an overwrite.

Updating the Program Kit bundle updates the extension and templates. It does not rewrite the repository.
Run the sync command separately, review its report, and resolve conflicts explicitly. The sync performs only
local, path-contained file operations. Subsequent restore, build, CI, release, and bundle creation can contact
the configured NuGet sources and require their own execution authorization. The runtime sync is optional and
is not a prerequisite for the technology-neutral governance workflow or its proposed quality gates.

The first local `eng/program-kit/Build.ps1 -SkipBundle` restore creates `packages.lock.json` files. Commit those
files. Generated CI and release workflows pass `-LockedMode`, so dependency changes must be reviewed and
regenerated deliberately.

## Secure web profiles

Pass `--web-profile auto` (the default) to repository sync. Reviewed bootstrap evidence selecting a
browser UI adopts `bff-cookie-v1`: the browser receives only an opaque `HttpOnly` session cookie while
OIDC access and refresh tokens remain in the host's server-side ticket store. `spa-pkce-v1` remains an
explicit option for a separately hosted static browser client that must call the API directly. A UI
described as an SPA does not by itself select browser-held tokens.

The selected profile scaffolds validated `ProgramKit:Web` configuration, a digest-pinned Keycloak
realm and deterministic personas, local startup commands, a web contract, and Playwright tests. The
host owns authentication/authorization middleware, role normalization, antiforgery or exact CORS,
Problem Details, correlation and security headers, localization defaults, identity readiness, and
OpenAPI. Features declare named policies such as `role:admin`; they do not configure schemes or parse
provider claims. See the extension's `references/secure-web-profiles.md` for the complete contract.

Authenticated profiles also copy the managed `program-kit-web-threat-model-v1` and
`program-kit-web-security-evidence-v1` snapshots into the consumer. The latter is a machine-readable
map of threats, controls, classified primary evidence, risk-based configurable defaults, residual
risks, assurance levels, and review triggers. The architecture inherits these IDs and records only
project-specific additions or Accepted deviations; Playwright evidence demonstrates behavior but is
not a security certification.

## Application deployment bundle

`eng/program-kit/Build.ps1` restores, builds, tests, packs, resolves the runtime NuGet closure, and creates
`artifacts/application-bundle.zip`. The ZIP contains a manifest, digests, shell and host configuration,
deployment instructions, and every required `.nupkg`. It contains no secrets and is not a self-contained host.

ProgramKit.Host verifies and safely extracts the ZIP before constructing configuration. Configuration order is
host defaults, environment-specific defaults, bundle host settings, bundle shell structure, environment
variables, then command-line arguments. Environment variables therefore override bundled structure.

## Runtime administration

The preview host exposes anonymous `/health/live` and `/health/ready` endpoints. Bundle inspection and
the generated `/_program-kit/openapi/v1.json` contract inherit the authenticated fallback policy when
a secure web profile is selected. Readiness reports fixed check names only and does not disclose
identity-provider configuration. The host deliberately does not
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

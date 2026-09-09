# Deterministic building-block selection

Program Kit owns the selection contract, executable catalog, resolver, and materializers. The
consumer owns the architecture decision and every generated repository in which dependencies are
placed. Orbyss Foundation, Forms, and Localization remain independent sibling products owned and
released by the Orbyss software factory and AI consultancy; this mechanism does not revisit that
repository split or transfer consumer business semantics into those packages.

## Invariants

- `docs/architecture/building-block-selection.json` is architecture evidence, not generated state.
  Its lifecycle is `Draft` to `Accepted` to `Superseded`. Program Kit may draft suggestions but never
  silently accepts a composition, option, scope, package placement, provider, or environment.
- An Accepted selection is usable only when `architecture-map.json` registers its exact canonical
  hash and every cited architecture decision is already `Accepted`. Editing it invalidates that
  authority.
- The executable catalog is schema `1.0`. This is the first consumer contract, not a second catalog
  format. `resolutionRevision` and `resolutionSha256` separate behavior-affecting changes from prose.
- Resolution is pure and offline. Identical accepted inputs produce byte-identical lock and managed
  projections. Registry access happens only in the separate availability command.
- NuGet and npm solve transitive dependencies in their native locks. Program Kit resolves only
  catalog-declared direct companion closure and never publishes a giant meta-package.
- Functional dependencies remain directly visible in their exact `.csproj` or `package.json`.
  `Orbyss.Foundation.Analyzers` is the sole repository-wide exception.
- Secrets and configuration values never enter the selection, catalog lock, plan arguments, or
  logs. The catalog and generated requirements describe required and optional keys, defaults,
  sensitivity, ownership, and validation phase.

## Selection contract

The selection names architecture scopes, concrete targets, and named composition instances. A
target is not inferred from a solution, directory name, or package role. Every used target slot is
bound explicitly. Options are arrays even for choose-one groups, so empty, one, and many have one
unambiguous representation and catalog cardinality can reject invalid choices.

```json
{
  "$schema": ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
  "schemaVersion": "1.0",
  "selectionId": "building-block-selection",
  "revision": 1,
  "status": "Accepted",
  "catalog": {
    "id": "orbyss-building-blocks",
    "schemaVersion": "1.0",
    "resolutionRevision": 1,
    "resolutionSha256": "8017cec0be489e5a76c0a6a75a383f5785cdcfabaf358a322d18d20e3116539d",
    "familyReleases": {
      "forms": "0.1.1",
      "foundation": "0.1.0",
      "localization": "0.1.1"
    }
  },
  "authority": {
    "architectureMap": "docs/architecture/architecture-map.json",
    "decisionIds": ["application-runtime"],
    "rationale": "Use the governed Foundation API baseline and external runnable host."
  },
  "scopes": [
    {"id": "repository", "kind": "repository", "environment": "production"},
    {"id": "application", "kind": "application", "parent": "repository", "environment": "production"}
  ],
  "targets": [
    {"id": "repository-policy", "kind": "repository", "path": "Directory.Build.props", "role": "repository", "scope": "repository"},
    {"id": "api", "kind": "dotnet-project", "path": "src/Product.Api/Product.Api.csproj", "role": "api", "scope": "application"},
    {"id": "shell", "kind": "cshell-shell", "path": "shells.json", "role": "composition", "scope": "application", "shell": "default"},
    {"id": "runtime-host", "kind": "host-image", "path": "Dockerfile", "role": "runtime-host", "scope": "application"}
  ],
  "instances": [
    {
      "id": "api-baseline",
      "composition": "api_baseline",
      "scope": "application",
      "targetBindings": {
        "repository": "repository-policy",
        "dotnet": "api",
        "shell": "shell",
        "host": "runtime-host"
      },
      "options": {"host": ["foundation-host"]}
    }
  ]
}
```

`required` catalog requirements always enter the closure. Optional behavior exists only through an
explicit option group. `minimum: 1, maximum: 1` means choose exactly one; `minimum: 0` makes the
group optional; a larger maximum permits an explicit compatible set. Package `requires` entries add
mandatory companions in the declared slot or same target. Composition conflicts are evaluated in
their named ancestor scope, and environment constraints reject development-only adapters in
production. Capabilities only suggest compositions for a Draft; they never make these decisions.

## Commands and lifecycle

Run the installed `building_blocks.py` through
`speckit.program-kit-building-blocks.sync`:

```text
building_blocks.py draft --capability dotnet-host-runtime
building_blocks.py accept --decision-id application-runtime --rationale "..."
building_blocks.py plan
building_blocks.py apply --plan-digest <reviewed-sha256>
building_blocks.py check
building_blocks.py recover
restore_dependencies.py renew --approved
restore_dependencies.py locked --approved
```

Automation supervisors that must keep registry credentials outside an agent process can emit the
exact read-only requests without performing network access:

```text
restore_dependencies.py request-renew
restore_dependencies.py request-locked
```

Each request binds the plan digest, lock hash, subjects, working directories, and native commands.
The supervisor must recompute and validate it before executing an approved restore; a request is not
authorization by itself.

`draft` refuses to overwrite consumer architecture and records only catalog suggestions. Complete
its scopes, targets, instances, and options, then use `accept`; acceptance updates the architecture
documentation registration only when the cited decisions already exist as Accepted. `plan` emits
the complete deterministic lock without writes. `apply` recomputes the plan and requires the exact
reviewed digest. `check` fails on input, lock, managed-region, ownership, or placement drift.

Apply uses a durable transaction under `.program-kit/building-block-transactions/`, writes the lock
last, and rolls back an ordinary failure. A process interruption leaves a journal; the next apply
fails closed until `recover` restores authenticated originals. Recovery preserves a path that was
externally changed after interruption and reports it for manual resolution.

## Lock and materialized state

`.program-kit/building-blocks.lock.json` is generated and committed. It binds the canonical
selection hash, resolution-affecting and raw catalog hashes, accepted decision projection, Program
Kit/resolver versions, named instances, exact target assignments, direct companion closure,
activations, registries, configuration requirements, managed-output semantic hashes, and the plan
digest. It deliberately excludes timestamps, credentials, configuration values, native lock hashes,
and live registry results.

Materialization owns the smallest possible entries:

- `.program-kit/eng/ProgramKit.BuildingBlocks.props` contains selected project-package pins only;
- labeled `ProgramKit.BuildingBlocks` regions contain direct `PackageReference` entries in the exact
  selected projects;
- actual exact `dependencies` or `devDependencies` keys are reconciled in each selected
  `package.json`, while unrelated keys and fields remain consumer-owned;
- marked `.npmrc` regions route catalog scopes to their registry and reference an environment
  variable such as `${PROGRAM_KIT_NPM_TOKEN}`;
- real .NET CLI packages are reconciled into their selected tool manifest; packages whose names end
  in `.Tool` but provide MCP tool classes remain normal project references;
- `<shell-directory>/.program-kit/building-blocks.shells.json` is the generated activation overlay
  beside each exact selected `shells.json`; shell composition consumes it while `shells.json` remains
  consumer-owned. A package may contribute more than one activation identity (the Keycloak
  administration adapter does), and every identity is explicit;
- `.program-kit/building-blocks.hosts.json` records selected version-tagged host inputs; public
  verification resolves the immutable digest used by release staging;
- `.program-kit/building-blocks.configuration.json` publishes required and optional configuration
  knowledge without values.

An edit inside an owned region or key is drift and blocks apply. An unregistered catalog package
reference is also rejected rather than silently adopted. Consumer content outside those entries is
preserved. To change a selected dependency, change and re-accept architecture, then review a new
plan. To stop Program Kit ownership, first remove or supersede the selection through the governed
transition path; do not delete the lock or markers by hand.

## Restore and public availability

Materialization is local and does not restore packages. After apply, explicitly run the approved
`renew` mode for native lock files, then the approved `locked` mode (`dotnet restore --locked-mode`
and `npm ci`) using the generated
registry routing. Restore failure does not roll back valid source manifests; it leaves availability
evidence absent or stale and therefore blocks verification and release.

For a consumer, verify only the lock closure. For Program Kit release acceptance, verify every
catalog artifact:

```text
public_availability.py --target . --catalog <catalog-path>
public_availability.py --target . --catalog <catalog-path> --all
```

The gate requires NuGet versions to be both listed and restorable, npm metadata to name the exact
version and a tarball, and the host tag to resolve to an OCI manifest digest. GitHub npm credentials
come only from the catalog-named environment variable. Evidence is separate from the deterministic
lock so live state cannot change resolution.

## Introduction, upgrades, and migration

There are no existing consumers, so this release introduces the executable `1.0` contract directly.
It does not infer selection from the former descriptive catalog or from pre-existing references.
Repositories without a selection continue to use the normal Program Kit baseline; selection checks
become applicable when the artifact is created.

On later Program Kit upgrades, prose-only or unselected catalog changes may be rebound automatically
only when the complete effective selected resolution is identical. A selected version, companion,
target, activation, registry, configuration, compatibility, or cardinality change requires a Draft
transition and renewed architecture acceptance. Unknown schema changes, removed options without an
explicit replacement, cross-major transitions, ambiguous renames, and ownership-kind changes stop
as unsupported rather than guessing. Native lock renewal and public verification remain explicit
after a compatible source transition.

## Delivery boundary

The smallest complete implementation covers the current 16 compositions, 50 NuGet packages, 12 npm
packages, Foundation host input, exact project placement, lock generation, NuGet/npm/tool/registry/
CShell/configuration materialization, drift checks, rollback, and availability gates. Safe follow-up
work includes pnpm/yarn adapters, third-party catalogs, automated rename or cross-major migrations,
and a generalized repository-level transaction that composes the existing .NET baseline, web,
persistence, building-block, and future ecosystem reconcilers under one digest. Until that final
orchestrator lands, each existing reconciler retains its own reviewed digest and transaction; no
command may imply cross-reconciler atomicity.

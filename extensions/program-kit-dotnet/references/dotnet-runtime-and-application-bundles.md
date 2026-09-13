# .NET runtime and application-bundle release profile

Apply this reference when .NET is selected unless intake explicitly opts out of the Orbyss Foundation building blocks.

## Host boundary

- `Orbyss.Foundation.Host` is application-neutral plumbing: Nuplane package loading, the
  Nuplane-to-CShells assembly provider, CShells configuration/routing, CShells-only eager activation,
  and the versioned Program Kit secure-web profile selected from host configuration.
- It has no application-bundle parser, package/feature policy, database client, business endpoint,
  application permission identity, or feature-health aggregation.
- Actual business behavior arrives as runtime packages. Standard authenticated web plumbing is
  configured by the host's accepted Program Kit web profile; persistence, business endpoints,
  tasks, and health implementations remain explicit capabilities.
- Until a feature-health contribution interface exists, do not invent a host dependency-readiness model.

## Feature creation and activation closure

The authoritative activation shape is `CShells:Shells:<shell-name>:Features:<feature-identity>` in the real
consumer-owned `shells.json`. Add a reviewed selection deterministically with:

```text
python .program-kit/eng/feature_metadata.py activate --shells shells.json --shell <name> --feature <identity>
```

An activatable implementation/provider/bridge/composition project is packable, belongs to the solution, sets `FoundationFeatureIdentity`, declares an exact matching `[ShellFeature("<FoundationFeatureIdentity>")]`, and sets
`AssemblyName` equal to `PackageId`. It references host-supplied CShells/framework abstractions with
`PrivateAssets=all`; it does not reference the host, Nuplane runtime, or peer runtime implementations.
Optional dependency, route, and dormant metadata is embedded during pack.

Tasks cover the project, solution inclusion, explicit identity, `shells.json` activation, release-bundle
inclusion, and missing/duplicate/dependency/route/dormancy tests. `.program-kit/eng/release_bundle.py stage`
enforces those constraints while assembling image inputs. The host does not know or repeat this policy.

Activated built-in features obtain their exact package versions from the repository-root
`Directory.Packages.props` and its imported props files. This includes both managed imports and
consumer-owned central pins. A managed file that is not imported is not package authority.
The staging reader supports unconditional literal `PackageVersion Include` items with a literal
`Version` attribute or child, repository-contained literal imports relative to their containing
file, and the root-level `Exists` condition matching the imported path (including the optional
`ProgramKit.BuildingBlocks.props` import). Package identity comparison is case-insensitive.

`PKR019` stops staging for missing or duplicate/conflicting pins, ranges/floating versions,
property expressions, conditional package items/groups, `Update`/`Remove`, and other unsupported
MSBuild evaluation. Do not copy pins into managed files to bypass the central import graph.
Packed packages, restored runtime dependencies and the final closure must agree with every
activated built-in pin; a higher transitive dependency cannot silently change it. A failed stage
leaves runtime-closure evidence unsatisfied and retains any previous output until validation passes.

## Application release bundle

One application release produces an application-bundle.zip, not a consumer Docker image.
Run the unchanged, digest-pinned `ghcr.io/orbyss-io/foundation-host` published by Foundation.
Only the Foundation publisher builds that image. Consumers build packable features, not a host
project, host DLL, Dockerfile, derived image or image-publication pipeline.

The bundle contains consumer-owned `shells.json`, `hostsettings.json`, `nuplane.settings.json`,
optional local NuGet package feeds under `packages/`, and a source/version/hash-bound
`application-bundle.json`. Secrets remain in deployment configuration. Nuplane settings are
runtime feed/loading configuration, distinct from build-time NuGet.config source mapping.
`nuplane.settings.json` has one top-level `Nuplane` object. The packager projects it into staged
hostsettings.json because the published Foundation host reads that file; the host does not parse
the bundle or separately load nuplane.settings.json. Conflicting duplicate Nuplane settings fail.
Upgrade copies existing hostsettings.Nuplane into the new consumer-owned file without overwriting
the original. Reconcile legacy duplicates before changing runtime configuration.

`release_bundle.py stage` composes configuration and verifies available package/activation closure;
`describe` binds the published Foundation image digest and emits the descriptor, ZIP and checksum.
Package-free configuration bundles are allowed; active features must still have verified resolution.
Runtime feeds, watching, reconciliation and reload are explicit deployment choices; configuring a
feed does not establish successful feature loading. Application identity/version and bundle hashes
are separate from the independently released Foundation image identity/digest.

Local execution and delivery acceptance mount the bundle's individual settings and package directory
into the published image, preserving /app and its host binaries. Never mount the entire bundle over
/app. Prove actual feature activation, application behavior and stop/restart with retained data using
that image. The release workflow attests and publishes the bundle without building or pushing images.

Architecture binds the external image to a `host-image` target whose path is hostsettings.json and
plans bundle ownership. Feature planning/tasks cover configuration, package inclusion, activation and
actual published-host checks. Delivery requires current executed bundle/runtime evidence; bootstrap
drafts and package availability alone are not runtime acceptance. Setup and upgrade use the same
repository-sync mechanism; retire untouched managed image files and report conflicts for consumer edits.

## Boundaries retained from the wider .NET profile

- Central package management, locked restore, deterministic pack, and package-source mapping are mandatory.
- `shells.json`, `hostsettings.json` and `nuplane.settings.json` remain scaffold-once consumer-owned inputs.
- Managed OpenAPI production runs after package-closure staging through
  `.program-kit/eng/openapi_pipeline.py`. Consumers register complete producer, compatibility,
  isolated client-generation, and application-compile contracts in
  `.program-kit/openapi-contracts.json`; the external host remains application-neutral.
- Core and persistence guidance remains context-owned. No provider-private model, shared `DbContext`,
  generic repository/store/unit-of-work contract, provider, or readiness probe belongs in the host.

# .NET runtime and application-bundle profile

Apply this reference automatically when .NET is selected, unless intake explicitly opts out of the
Program Kit host/runtime default.

- Generate features and contracts, not application hosts. `ProgramKit.Host` is the standard runtime appliance.
- Feature projects reference CShells abstraction packages. Only the host owns CShells and Nuplane runtimes.
- Shell-owned work uses `ProgramKit.Tasks`; direct `AddHostedService` in an `IShellFeature` is invalid.
- Application projects share one release version when they ship as one application bundle.
- Central package management, locked restore, deterministic pack, and package-source mapping are mandatory.
- The application bundle contains the full runtime NuGet closure, `shells.json`, `hostsettings.json`, manifest,
  checksums, and deployment instructions. Secrets are external. The release pipeline attests the ZIP; the host
  image publication adds SBOM and provenance evidence.
- Production composition is immutable. Runtime feed access, directory watching, automatic reconciliation, and
  live shell reload require an Accepted ADR.
- Configuration precedence is host defaults, environment-specific defaults, bundle host settings, bundle shell structure, environment variables, then command line.
- Container deployments pin `ProgramKit.Host` by digest and add the application ZIP as a single image layer.

## Feature creation and activation closure

The one authoritative activation shape is the CShells configuration already consumed by the host:
`CShells:Shells:<shell-name>:Features:<feature-identity>`. `shells.json` remains consumer-owned and
no package is activated merely because it exists. Add an explicit selection deterministically with:

```text
python eng/program-kit/feature_metadata.py activate --shells shells.json --shell <name> --feature <identity>
```

A feature project is packable, is included in the solution, sets `ProgramKitFeatureIdentity`, and
sets `AssemblyName` equal to `PackageId` so Nuplane resolves its main assembly deterministically. It
references only `CShells.Abstractions` or `CShells.AspNetCore.Abstractions` plus owned contracts.
Host-supplied abstraction references set `PrivateAssets=all`; carrying those packages into the
application graph would create a second load-context type identity instead of using the host contract.
It must not reference the runtime, host, Nuplane, or peer feature implementations. Optional
`ProgramKitFeatureDependencies`, `ProgramKitRuntimeDependencies`, and `ProgramKitFeatureRoutes`
are semicolon-separated deterministic metadata; an intentionally packaged but inactive feature sets
`ProgramKitFeatureDormant=true`. The managed pack target embeds this metadata.

Every plan that creates a feature must generate tasks for the packable project, solution inclusion,
explicit identity, consumer-owned `shells.json` activation, bundle inclusion, and tests for missing
features, duplicate identity/version, dependency closure, route collisions, and eager activation in
`ProgramKit.Host`. The bundle build fails with shell, feature, and package identities when closure is
invalid. Do not edit `eng/program-kit/Build.ps1`; use these project properties and root consumer-owned
MSBuild imports.

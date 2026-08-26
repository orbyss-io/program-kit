# .NET runtime and application-bundle profile

Apply this reference only when .NET is selected by accepted project architecture evidence.

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

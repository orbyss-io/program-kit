# Test-toolchain selection and compatibility approval

New Program Kit consumer proofs use TUnit `1.60.0` as an exact centrally pinned
test framework. TUnit supplies native `net10.0` assets for its framework,
assertions, core, and engine packages and runs as a normal .NET 10 executable.
It was selected for new proofs because the executable Microsoft Testing
Platform model, source-generated discovery, asynchronous tests, lifecycle
support, and parameterized tests cover the Program Kit acceptance needs without
a custom test harness. Existing MSTest unit and conformance projects remain
legacy projects; they are not the template for subsequent test projects. A
future framework change requires a separately reviewed selection.

Known accepted issue: the selected TUnit closure currently resolves five
Microsoft Testing Platform support assemblies from lower target folders:

- `Microsoft.Testing.Extensions.CodeCoverage` `18.9.0` from `net8.0`;
- `Microsoft.Testing.Extensions.MSBuild` `2.3.2` from `net9.0`;
- `Microsoft.Testing.Extensions.Telemetry` `2.3.2` from `net9.0`;
- `Microsoft.Testing.Extensions.TrxReport` `2.3.2` from `net9.0`; and
- `Microsoft.Testing.Platform` `2.3.2` from `net9.0`.

This is not a general permission to consume .NET 8 or .NET 9 application
assemblies. The human-approved CS1701 exception is limited to
`ObservatoryScheduling.Tests`, binds fourteen compatibility-sensitive package
hashes, the four native TUnit `net10.0` assets, the five exact lower-target
assembly identities, the .NET 10 `System.Runtime` identity, and the absence of
matching `net10.0` support assets. The complete resolved project graph remains
locked in `packages.lock.json`. Any approved-toolchain hash, identity, or
asset-availability change invalidates the approval and fails the build.

The canonical approval is recorded in
`program-kit/governance/approved-warning-suppressions.tsv`. Conformance tests
actively mutate the runtime identity, support-assembly identity, and TUnit
framework asset selection to prove the quarantine fails closed.

Release acceptance executes each test module directly with a minimum discovery
count, so zero-test discovery cannot pass:

```powershell
ObservatoryScheduling.Tests.exe --minimum-expected-tests 14 --maximum-parallel-tests 1 --progress off
```

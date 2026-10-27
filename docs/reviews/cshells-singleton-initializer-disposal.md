# CShells 0.0.31 initializer disposal assessment

## Disposition

Confirmed native CShells registration/disposal-ownership defect. This is independent of
Foundation, PostgreSQL, authentication, filesystem storage and product code. The consumer's
reported failure is not evidence of an application lifetime mistake: the documented helper
explicitly preserves an existing concrete singleton lifetime. No consumer was read or changed.

Public CShells and CShells.Abstractions 0.0.31 restore with repository commit
`b7611aadb49789d3b282749df18ffe68d0eacec5`. The bounded public check on 2026-10-27 found
0.0.31 remains the newest public version and the upstream default source is that same commit.

## Source-confirmed mechanism

- [ServiceCollectionLifecycleExtensions.cs, lines 133–135](https://github.com/valence-works/cshells/blob/b7611aadb49789d3b282749df18ffe68d0eacec5/src/CShells.Abstractions/Lifecycle/ServiceCollectionLifecycleExtensions.cs#L133)
  preserves the concrete registration with `TryAddTransient<TInitializer>()`, but always adds
  a transient `IShellInitializer` factory returning that concrete instance.
- [ShellRegistry.RunInitializersAsync, lines 870–892](https://github.com/valence-works/cshells/blob/b7611aadb49789d3b282749df18ffe68d0eacec5/src/CShells/Lifecycle/ShellRegistry.cs#L870)
  resolves those aliases inside a temporary async scope. Microsoft DI captures a disposable
  factory result for that scope, including an instance already owned by another descriptor.
  Ending activation disposes the singleton through this alias; its concrete registration
  still owns it for generation teardown. Matching both descriptor lifetimes does not make
  them a single disposal owner.
- [Upstream PR 131](https://github.com/valence-works/cshells/pull/131) fixed the earlier lifetime
  replacement issue. Its commit is already an ancestor of 0.0.31; it does not repair this
  remaining alias defect. The same source file uses the alias pattern for terminators;
  that adjacent owner needs upstream inspection, not an unexecuted runtime-failure claim.

## Independent synthetic reproduction

Retained under `C:/Users/tech_/Code/program-kit/artifacts/t/cshells-owner-b761/`:
`Probe.csproj`, three tiny C# files, isolated NuGet/build configuration, native lock,
`restore.log`, `observation-with-drain.log` and `observation-with-drain.json`.
Only the exact public CShells 0.0.31 package is directly referenced. The fixture uses actual
`AddCShells`, `GetOrActivateAsync`, `ReloadAsync`, `DrainAsync` and awaited native generation
disposal. It installs no toolchain, starts no service/container and uses no private material.

| Case | Disposal calls after settled activation | After generation teardown |
| --- | ---: | ---: |
| Explicit singleton plus helper, IAsyncDisposable | 1, incorrectly early | 2 |
| Explicit singleton plus helper, IDisposable | 1, incorrectly early | 2 |
| Non-disposable admission adapter, async owner | 0 | 1 per generation |
| Non-disposable admission adapter, sync owner | 0 | 1 per generation |
| Scoped concrete plus helper, async | 2 | 2 |
| Transient concrete plus helper, async | 2 | 2 |
| Failing initialization, singleton plus helper | 2 during rollback | 2 |
| Failing initialization, non-disposable adapter | 1 during rollback | 1 |
| Diagnostic singleton interface alias matching concrete lifetime | 0 | 2 |
| Direct transient interface registration control | 1 | 1 |

Successful cases reload into a second generation and await both generations' native drain/
Disposed state. The adapter keeps the new generation live while the old one disposes once,
then disposes the new owner once at its own teardown. Initialization failures remain failures,
leave no active candidate and do not require a replacement lifecycle. The initial observation
files remain retained; their `afterTeardown` label only measured outer root-provider disposal,
which is not registry-owned generation teardown. The later explicit-drain observation is the
authoritative teardown measurement.

Reproduce from this synthetic fixture directory, using its isolated declared cache:

```powershell
$env:NUGET_PACKAGES = "$PWD/cache"
$env:DOTNET_CLI_HOME = "$PWD/dotnet-home"
dotnet restore Probe.csproj --configfile NuGet.config --locked-mode
dotnet run --project Probe.csproj -c Release --no-restore
```

These are observations of the defect and a bounded workaround, not passing native lifetime
contract tests or a fixed upstream package. Full cancellation, drain-deadline/race, terminator,
mixed initializer-ordering and multiple-container behavior remain upstream regression work.

## Recommended remedy

CShells should preserve one DI disposal owner for each concrete initializer, while lifecycle
references remain non-owning. Preserve explicit/default lifetimes, ordering, same-instance
semantics, legacy registrations and compatibility. A simple lifetime-matching factory alias is
insufficient: the independent control still disposes the singleton twice. Broadly bypassing
scope disposal would leak legitimate scoped/transient initializers and is not a repair.

An upstream patch should exercise IDisposable and IAsyncDisposable; assert liveness after
settled activation; cover initializer failure and later activation rollback, reload with active
tracked scopes, drain and repeated teardown; verify exactly-once generation disposal and
legitimate scoped/transient cleanup. Inspect the terminator helper's parallel registration seam.
The helper/planner integration owns the repair; no replacement shell, runner or consumer lifetime
manager is justified.

Until a repaired release is qualified, Program Kit's existing PostgreSQL lifecycle guidance
documents a separate non-disposable admission adapter using typed constructor injection. The
resource remains an ordinary generation singleton. No consumer rewrites, dependency upgrades,
upstream issue/PR, publication or runtime patch were performed by the initial assessment.

Guidance validation: Integrity passed in 7.493s
(`artifacts/validation-runs/20261027T101158Z-fa9572bd/results.json`); five focused discovery/
native-phase/installed-mechanism checks passed in 16.852s
(`artifacts/validation-runs/20261027T101309Z-e6b5d945/results.json`). Both runs retained stable
source during execution. The README-only affected PostgreSQL runtime selection was deliberately
not rerun: no provider fixture implementation changed, and the independent CShells probe owns
this defect reproduction. `git diff --check` passed. Those initial edits were uncommitted;
that assessment supplied no new exact-source package CI or release acceptance.

## Maintained workaround and upstream report

The owner subsequently authorized a maintained, discoverable workaround and an upstream issue.
[CShells issue 216](https://github.com/valence-works/cshells/issues/216) now contains a verified,
self-contained public reproduction, observed counts and native repair/regression boundaries.
The GitHub connector denied repository write access; authenticated GitHub CLI created the issue.
No upstream runtime patch, package upgrade or publication was performed.

The maintained example is under
`extensions/program-kit-dotnet/references/examples/cshells-initializer-ownership/`.
Its actual feature and typed admission are the reusable pattern; its memory resource and counters
are explicitly synthetic instrumentation. General .NET `principle.disposal-ownership`, the
installed implementation command and the existing PostgreSQL fixture link this example. The
existing lifetime guidance owns discovery; there is no new phase requirement or automatic test gate.
Its version-specific safety contract retains original admission/failure/cancellation, normal DI
lifetimes, read-only schema/privilege admission, native tracked scopes/drain and human story review.

`validate_cshells_initializer_ownership.py` is an explicitly selected native check, with a 120s
budget and 240s timeout. It compiles the actual five shipped source files against the exact public
CShells 0.0.31 packages, authenticates repository/source metadata, and starts no external service.
Final native execution passed 11 cases in 5.698s, with stable source hashes, process/stream cleanup
and owned scratch cleanup:
`artifacts/cshells-initializer-ownership/b0c8ebf53974/results.json`.

The stronger maintained assertions include:

- The shipped resource is usable after settled activation, with zero disposal calls, then closes
  after actual native generation teardown with exactly one disposal call.
- Asynchronous rejection after resource acquisition preserves the original exception, cleans up
  once and publishes no active or partial generation. Cancellation starts only after initializer
  entry, preserves the actual token, cleans up once and does not publish the candidate.
- Reload creates a distinct owner/generation while the old tracked scope remains open. Old and
  new owners stay usable, with zero disposal calls; the old drain remains incomplete. Releasing
  the scope lets the old generation close once while the new owner remains live.
- Failed and canceled replacements preserve the old active identity and its usable owner while
  cleaning the rejected candidate once.
- Sync owner disposal and legitimate scoped/transient admission-only cleanup occur exactly once.
  Native bad-alias controls retain their observed premature/double-disposal behavior.

A separate build of those exact example sources with public Foundation.Analyzers 0.3.8 and
`FoundationSourceReadability=true` passed with zero warnings/errors. The initial build exposed
missing private-field documentation and an inline buffer construction; their repaired positive
is retained alongside the original failure under `artifacts/cshells-admission-style-*.log`.
No suppression or analyzer exclusion was introduced. The native fixture's own diagnostic controls
are compiled separately and do not claim selected product source-policy acceptance.

This establishes the bounded ownership adaptation, not arbitrary provider security, concurrent
business-operation safety, emergency forced-drain semantics, full activation-participant rollback
or a fixed upstream package. Preserve the real owner's existing contracts and test only affected
adaptations. Remove or reconsider the version-specific workaround only after upstream qualification.

## Contributor validation and package representation

- Integrity passed in 7.343s:
  `artifacts/validation-runs/20261027T103555Z-f0a9eeca/results.json`.
- The affected batch executed 24 steps in 45.865s: 22 passed, including the final native ownership
  check (5.089s); two installed-phase fixtures failed because a new .NET source-fidelity assertion
  was incorrectly placed in the standalone-governance test. Preserve this failed run:
  `artifacts/validation-runs/20261027T103631Z-9b3d5529/results.json`.
- The assertion now belongs to the existing full-bundle package smoke, which actually installs the
  .NET component. Standalone governance still verifies the conditional recipe link without adding
  a .NET prerequisite. Both failed checks passed their focused rerun in 10.184s:
  `artifacts/validation-runs/20261027T103848Z-e3e30915/results.json`.
- Actual archive construction and full native bundle installation passed in 13.521s (build 3.181s,
  install/entrypoint smoke 9.915s):
  `artifacts/validation-runs/20261027T104128Z-bfbc5b01/results.json`.
  All five executable example sources and its README match maintained bytes in both the original
  component archive and the installed component. Focused selected .NET lifetime lookup exposes
  the workaround and remains read-only; an unrelated Rust selection excludes that requirement.

All bound runs retained stable source while executing. Unknown coverage, budget overruns and
unsupported platform claims were not converted to success. No broad database/browser matrix was
rerun for this metadata/guidance/example change. Existing consumer installation refresh remains
separate from application changes and dependency/profile upgrades.

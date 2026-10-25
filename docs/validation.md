# Development validation

Run `./scripts/Test-ProgramKit.ps1` for the fast Integrity baseline. It uses the selected
Python; it does not preflight unrelated SDKs, npm, browsers or device tools. For tests
that import PyYAML/Spec Kit, select the existing prepared interpreter explicitly:
`./scripts/Test-ProgramKit.ps1 -Python <prepared-python> -Suite Baseline`.
Validation installs no device tools. Missing prerequisites are printed per check.

`python scripts/run_validation.py --suite Affected --changed-from <base>` includes
committed changes since the merge base, staged/unstaged modifications and untracked
files. Without a base it considers the current working changes. Unknown history or
paths become coverage gaps; supported independent checks still execute. Report and
resolve gaps through maintainer review; the runner never silently passes them or
falls back to the complete inventory.

## One definition

`tests/validation-inventory.json` contains capabilities, their input patterns and
`dependsOn` edges, check commands, prerequisites, budgets and baseline membership.
A changed producer selects its dependent capabilities transitively. Check-specific
inputs select the owning check. `--list` explains selection without preparing tools.

To add coverage, identify the changed contract and add a small capability or a narrow
input/edge to an existing one. Add its check and real prerequisites; specify what
failure it detects. Verify that a changed producer selects its consumers and an
unrelated change does not. Prefer a capability-level approximation over a speculative
dynamic import graph. Do not add a second map to CI or documentation. Inputs outside
the declared map intentionally remain unresolved until reviewed.

Broad integration scenarios are `manualOnly`: they run only by explicit ID with a
concrete reason, for example `--check validate_postgresql_lifecycle --reason
"changed PostgreSQL lifecycle login/grant handling"`. Narrow automatic checks still
need mapped affected mechanisms. Shared SDK/profile changes select representative
mechanisms; they do not justify the entire browser/database/Host scenario inventory.

## Representative mechanical baseline

Establish `--suite Baseline` once when adopting this process. Later development selects
affected families. The baseline includes shared archive preparation once, then:

| Family | Concrete operational claim | Important omissions |
| --- | --- | --- |
| Installation | Native bundle installation of actual archives in a clean space-path workspace; all component ownership/registrations, installed governance coherence and representative helpers work on Windows/Linux | Other installation routes, restricted permissions, unusual filesystems |
| Phases | Real task/phase rules reject invalid prerequisites/graphs; interrupted drafting resumes and preserves completed work | Specification quality, agent obedience, every optional phase branch |
| Knowledge | API and frontend scopes select correct owners; unrelated decisions stay excluded; missing required binding is rejected | Correctness of upstream guidance, all dependency combinations/runtime compatibility |
| Founding | Native installed intake skill validates fictional synthesis, constitution ratification and named decision acceptance, rejects stale authority and begins feature intake directly | Conversational quality, actual human approval, runtime compatibility and provider behavior |
| Upgrade | Actual supported historical source installation advances through the candidate packaged updater; authored files/coherence survive, managed conflicts reject and interrupted profile transactions roll back/retry | Every historical layout, migration combination and filesystem failure |
| Scaffolding | Real generator emits coherent relationships and runs lightweight drift validation; invalid selection preserves authored files | Native compilation/startup, services, browsers and deployment |

These are narrow journeys, not a substitute for meaningful cheap regression tests.
Case counts, historical report hashes and retired-command messages are not acceptance
criteria. Supported consumer case-inventory behavior retains its focused unit tests.

## Selecting expensive mechanisms

PostgreSQL lifecycle/provisioning, connection and role changes select real lifecycle
coverage, including allowed and denied operations against the shipped example.
Exporter/baseline changes select offline export/comparison. Client/wire changes select
real generation/compilation and a small transport contract. Durable operation/restart
changes select database-backed operation tests. Browser session changes select the
relevant browser scenario. Toolchain and Foundation updates select representative
affected mechanisms, with explicit limitations. Source/hash parity establishes
packaging fidelity; it does not establish correct execution.

## Runtime budgets and results

Initial targets are Integrity <=60s, each mechanical family <=120s, initial Baseline
<=600s including shared preparation, narrow integration normally <=300s, and package CI
300-600s elapsed including provisioning/transfers/security. Each command also has a
bounded hard timeout. A budget overrun is visible and returns a needs-attention result;
inspect cost, split unnecessary work or revise an unjustified budget in normal review.
Do not call a timeout, failure, unsupported environment or overrun success.
Explicit `--check` selections retain each command's budget; aggregate Integrity and
Baseline targets apply when those suites are selected, not to an arbitrary manual batch.

Ignored `artifacts/validation-runs/<unique>/results.json` records actual content hashes
(including dirty/untracked files and deletions), interpreter/platform, preparation,
individual execution and total elapsed time, commands, outcomes, logs and gaps. Changes
during execution invalidate the run's complete-input claim. Records are local
diagnostics, not signed evidence, merge gates or automatic cache entries. Full logs
remain local; CI retains only its own normal logs/artifacts. A concise PR summary states
what ran, total/cold/warm cost where measured, outcomes and omissions. The maintainer
accepts the developer's execution claims; CI independently checks package mechanics.

Automatic cross-run caching is deferred. Measure rebuilt scenarios first. Add reuse
only if measured benefit justifies sound invalidation across relevant source, check,
dependency and environment inputs. No agent participates in deterministic validation.

## Retained, replaced and removed checks

The old Development/Release labels did not describe actual cost. Installation,
restore/build/pack, Node builds and service execution now have separate entrypoints or
explicit integration registrations. The default fast suite contains syntax/configuration
integrity and small admission/selection/publication-safety regressions. Capability
selection also retains meaningful focused phase, knowledge, wire/schema, composition,
managed-file and task/closure tests. An old test count is not an acceptance target.

| Previous pattern | Maintained treatment |
| --- | --- |
| Historical campaign/report hashes, lineage counts, retired-command diagnostics | Removed with obsolete reports and entrypoints; supported consumer case-inventory behavior keeps ordinary fixture-generated unit tests |
| Shared obligations invoking a separately registered repository matrix | Useful matrix retained once; duplicate wrapper removed |
| Mixed runner/closure/frontend checks | Cheap default separated from explicit native restore/build/pack or Vite mode |
| Broad typed-operation scenario as the only exporter check | Independent actual official export and generated TypeScript compilation; full browser/database operation remains an explicit investigation |
| Generic embedded SQL grants test | Allowed/denied assertions consolidated into the shipped PostgreSQL lifecycle example |
| Large install test with repeated reinstalls and wording inventories | Small actual-package install/entrypoint smoke; detailed packaging fidelity scenarios remain on demand |
| Bootstrap/task/recovery fixtures | Small real operational journeys with fictional authoring; broader lifecycle, host and provider combinations remain selectable for concrete risks |
| Native/runtime integrations | Retained where they detect a distinct failure: PostgreSQL, API/client, authentication/session, host activation, standalone handoff, public compatibility and dependency qualification |

The representative upgrade installs immutable sources for the immediate predecessor
declared in release history through native bundle installation, then runs the updater
extracted from the candidate archive for Copilot. It checks copied native outputs,
customization/alias refusal, every component/bundle version, preserved authored
feature/note bytes and native installation coherence/migration completion. Local Git must contain that supported
historical fixture tag; its resolved commit is recorded. Additional focused cases cover
profile transitions, managed conflicts and rollback/retry. Other historical layouts and
owner-fault combinations remain separate investigations.

Retained investigations have no entitlement to run by their historical suite label.
Their useful assertions remain callable, and the fixture owns deeper pinned-runtime
checks; the central definition supplies minimum early prerequisites without duplicating
those policies. A changed check can identify an explicit maintainer coverage decision.
Removing a broad default gate does not establish the behavior it formerly attempted
to cover. Review the stated omissions and choose the smallest applicable real check.

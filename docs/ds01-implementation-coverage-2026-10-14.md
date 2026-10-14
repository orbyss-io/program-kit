# DS01 approved implementation coverage

This is the execution record for the accepted [repair plan](ds01-upstream-repair-plan-2026-10-13.md).
Items1–15 and their historical evidence remain unchanged in `diagnostics-repair-batch.json`.
Items16–28 retain the source investigation in the linked research addenda. The accepted Q5 scope
is upstream implementation, with real-consumer correction separate. Q6–Q8 add server-owned validation
export, raw-control rejection before trimming and preserved UTF-16 counting. No consumer product
files, pins, migrations or native locks were changed by this upstream batch.

| Item | Cause/owner | Implemented reusable repair | Focused coverage and remaining boundary |
| --- | --- | --- | --- |
|16 Runtime scaffolded as API | Confirmed Program Kit generator defect | Explicit runtime/HTTP responsibility and capability consumption; IShellFeature runtime; identity-preserving reconciliation; activated package closure | Composition model30, package closure23, mixed native shell activation and reconciliation. Customized seams remain reviewable. |
|17 Commit forwarding wrapper | Consumer design mistake; Foundation0.3.3 interceptor admission gap | Native transaction/public-port guidance; Foundation owns additive native EF contributions | Foundation real postcommit/durability/isolation/drain regression reported passed. Consumer receipt discovery and one-effect replay still require separate consumer regression. |
|18 Outcomes and invalid results | Consumer contract design/guidance | Restricted result construction, established-fact uncertainty and explicit ownership guidance | Semantic source review and operation-specific consumer compatibility/invariant tests required; no generic Foundation outcome introduced. |
|19 Storage/policy literals | Consumer consistency/guidance | Current owner metadata, provider identifier quoting, immutable migrations and independent consistency checks | Current consumer mapping/deployment/admission checks remain consumer-owned; historical migrations unchanged. |
|20 Clock/deadline/lock expiry | Consumer implementation/guidance; existing Foundation mechanisms sufficient | Effect-owner fresh clock after lock; preserve DI replacement and outer native deadline | Consumer real lock-wait crossing, exact precision/boundary and cancellation/deadline tests remain required. No unfounded claim that the original risk was reproduced. |
|21 Friend access | Consumer test boundary mistake | PKA021 rejects evaluated SDK and actual compiled friend declarations; public registration guidance | Architecture validator23 includes actual compiled SDK and aliased C# friend declarations. Consumer PostgreSQL tests must migrate through public ports without public entities/DbSets. |
|22 Catalog page maximum/default | Consumer operational configuration mistake and missed review | Trace typed effective owner options through omitted API defaults, admission, query and settings; no hidden constant | Non-default activated consumer settings and query-bounds regressions required during consumer correction. No pagination business policy moved to Foundation. |
|23 Human login timeout | Publisher default and generator policy defect | Omitted900-second generator/template policy, separate network budgets; Foundation default repair | Typed model/template checks; maintained fresh-login human delay; Foundation actual expiry/restart reported passed. Published profile adoption remains pending. |
|24 Browser authentication errors | Consumer presentation omission; initial provider-failure writer gap | Maintained application-owned writer/page example; Foundation narrow initial provider failure integration | Compiled public writer seam and browser rendering evidence; Foundation native availability/cancellation/session-preservation tests reported passed. Real consumer branding acceptance separate. |
|25 Signed-out JSON landing | Consumer journey omission; publisher destination gap | Public application landing guidance/example and additive Foundation destination repair | JSON protocol retained; Foundation root/non-root success/fallback tests reported passed. New published option must be selected before use. |
|26 Tests accepted wrong journey | Program Kit test-scope defect and consumer acceptance gap | Separately named protocol checks, human delay, actual shipped helper and accessible synthetic owner UI journeys |11 cases per engine,22 total, passed against actual prepared Foundation0.3.3/BFF/Keycloak on Chromium/WebKit. Fixture proves reusable adapter behavior, not consumer story acceptance. |
|27 Unbounded logout observations | Confirmed Program Kit adapter defect | One elapsed budget for fetch/body/poll; signal; dispatched/unknown acknowledgement result; independent recovery |13 focused helper cases and strict TS compile passed; actual native lost-observation/recovery journey passed on Chromium/WebKit. No private UI restored after dispatch. |
|28 Truncation/validation parity | Consumer input-loss defect, missing supported generation path and form guidance | Pure owner exporter → closed normalized descriptor → generated immutable browser rules; source/client checks |16 invalid-descriptor cases, duplicate-property rejection,85 compiled Core/JS/digest vectors,75 native HTTP invalid requests, Chromium real paste and WebKit native insertion. HTTP effect counter is synthetic, not PostgreSQL durability proof. |

The shipped [implementation boundary guidance](../extensions/program-kit-dotnet/references/implementation-boundaries.md)
provides concrete corrections and regression requirements for every item. Existing implementation
and architecture commands and the implementation-quality obligation route semantic review through
ordinary tasks/source review. There is no additional approval mechanism. Maintained source and
runtime checks enforce their declared properties; application semantic decisions still need review.

Focused Program Kit evidence includes:

- `artifacts/tests/ds01-generator-impact/` and reconciliation `artifacts/foundation-composition/413047f898dc45ca81f88704bb90130d`.
- Mixed activation `artifacts/tests/composition-activation/a6552f2e37b24fcd8332372613851de3`.
- Validation parity final `artifacts/tests/validation-parity/65488016/status.json`, including seven runtime rule-key refusals, explicitly owned constructor admission and placeholder-bearing identity/hash preservation.
- Public presentation baseline `artifacts/tests/authentication-presentation/207a0728/result.json`; final `artifacts/tests/authentication-presentation/39d92362/result.json` proves25 compiled seam cases,14 Chromium/WebKit rendered observations and a real failed credential assertion whose failure remains nonzero without private output or automatic context artifacts. Original machine codes and native code admission remain intact.
- Actual prepared authentication/helper journey `artifacts/tests/reusable-foundations/functional-76658736ce914dde/`, with22 passing native browser cases bound to the final maintained source. Original11-second fixture source and52 staged inputs were restored exactly; the901-second test payload/logs remain separately preserved.
- Root architecture, phase and development logs in `artifacts/tests/ds01-repair/`.

The first bounded Development run retained its failed journal at
`artifacts/validation-runs/20261013T215117Z-bf4da869/journal.json`. Sandbox socket denial, temporary
directory restrictions and source/index changes during that run must be separated from actual code
failures and resolved by fresh checks; that run is not a success receipt. A second run preserved at
`artifacts/validation-runs/20261013T222716Z-a6b33ee3/journal.json` exposed missing knowledge routes and
dependency declaration order, which are repaired. Repository-local TEMP also made simulated shared
tools appear repository-owned and caused temporary-file failures. All eight failed checks passed
focused reruns with normal user TEMP and external process access. The complete stabilized Development
suite passed with normal user TEMP; its preserved journal is
`artifacts/validation-runs/20261013T225324Z-c6fb8a24/journal.json`. The later presentation-only correction
has the final native proof above. These are Development/focused checks, not a Release receipt.
Publisher/profile qualification remains open. Unchanged Forms/Localization local403 is the sole
user-approved local exception; it does not waive dependency lookup or CI failures.

Foundation's unreleased repair source `0cf5da54df52b6e1a0fdbb52967392d67a347813` is in
[PR11](https://github.com/orbyss-io/dotnet-foundation/pull/11). Complete
[Windows/Linux CI](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38477136638) passed;
the merge test commit has the same source tree. Preserved Linux browser results confirm Chromium,
Firefox and WebKit native fifteen-second provider dwell, actual short-window expiry/restart, valid
session preservation and independently observed local logout. These are synthetic publisher
fixtures, not real consumer or provider-wide logout acceptance.

The required [Foundation dependency update](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38477135373)
failed because official metadata selects SDK10.0.402 while its matching Microsoft container image
returns not found. The local refresh independently reproduced the failure and rolled back pins.
At that failed attempt Foundation had not selected/tagged/published a new immutable version.
Its retained native qualification used SDK10.0.401, EF10.0.12 and Npgsql/provider10.0.3;
published0.3.3 remains the adoption baseline until its successor is fully verified.

Subsequent progress on October14: the SDK image became available. Foundation refreshed its
active pins and native locks, qualified source `805383ad55e2f50716196faf2ba764073aa5f42c`
for0.3.4, passed full Windows/Linux CI and dependency qualification, and scanned both candidate
image platforms with zero High/Critical findings. PR11 merged and the exact source was tagged;
the [protected Release](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38506924214)
is running. Adoption still waits for completed publication and verified public artifacts. The
earlier failed evidence and published0.3.3 profile remain unchanged.

Program Kit [PR CI](https://github.com/orbyss-io/program-kit/actions/runs/38483789818) and the
required [dependency update](https://github.com/orbyss-io/program-kit/actions/runs/38483858372)
failed on the Linux composition activation probe and the Firefox owner-landing/provider-failure
authentication journeys. Windows CI passed. Original logs and artifacts are preserved under
`artifacts/tests/ds01-repair/remote-failures/`; investigation and repairs are underway. These
failures block qualification and are separate from the known local Firefox launch limitation.

Foundation publication, the required Program Kit dependency workflow, exact new profile/knowledge adoption and fresh
Program Kit Release qualification remain open. Program Kit patch publication is authorized after
these gates. The Windows Release command must run in the user-owned terminal unless the user
explicitly overrides the restriction. No paid live phase, real-consumer acceptance or release success
is claimed by this record.

Published Program Kit v0.13.1 is tag source `5e462b73b2fd34604701573161f9fd071e09427f`.
The existing repair PR41 remains unpublished and includes the original fifteen repairs plus this
extension. During patch preparation, carry its unreleased diagnostics migration addition into the
new patch guide and restore the published0.13.1 guide bytes; do not describe that addition as already
delivered in0.13.1. Preserve original diagnostic records and immutable native source witnesses.

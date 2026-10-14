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
passed qualification and image scans but failed during NuGet publication on an HTTP500 followed
by a300-second timeout. Foundation preserved the failed attempt, verified the21 visible payloads
against the exact candidate knowledge, and is retrying the same protected workflow without changing
source/version/tag. Nine package publications and final Host/knowledge verification remain pending.
Adoption still waits for complete success and verified public artifacts. The earlier failed evidence
and published0.3.3 profile remain unchanged.

Program Kit [PR CI](https://github.com/orbyss-io/program-kit/actions/runs/38483789818) and the
required [dependency update](https://github.com/orbyss-io/program-kit/actions/runs/38483858372)
failed on the Linux composition activation probe and the Firefox owner-landing/provider-failure
authentication journeys. Windows CI passed. Original logs and artifacts are preserved under
`artifacts/tests/ds01-repair/remote-failures/`. The activation validator now requests native xUnit XML
and checks exact named tests and counts. Focused proof at
`artifacts/tests/composition-activation/dafab161c89c4b2ab330328f404bd5af/` retains compile-negative,
locked restore, mixed shell and lifetime checks. Eight malformed report probes were rejected; a real
ANSI-formatted execution reproduces the old console-parser failure while its native report passes.
The exact remote formatting cause remains inferred because the inner execution log was not uploaded.

The [targeted browser reproduction](https://github.com/orbyss-io/program-kit/actions/runs/38507694729)
observed all33 cases and isolated both Firefox failures to `ended-heading-focused`. Finite checkpoint
properties export no private content and reject unexpected, conflicting or stale input. The corrected
journey brings the application tab forward after the provider popup, then retains the original heading
focus assertion without focusing the element itself. Native Chromium/WebKit verification passed22/22
at `artifacts/tests/reusable-foundations/functional-cfbe58d78b7343b0/`, bound to source
`28f2b72485d8ba448432d0105e625b697a2f36550f7a82dd686dd0c384074811`. The original fixture and52
staged inputs were restored exactly. An earlier21/22 run failed in WebKit's uncertain-recovery branch;
the narrowed rerun passed without changing those assertions, so that failure's precise cause remains
unestablished and its evidence is retained. Final Firefox acceptance still requires fresh Linux CI.

A fresh bounded Development run retained a numeric client-generation failure despite successful
installation. The same installed generator succeeds with the existing child-only Windows PATH
preparation, reducing the23299-character inherited PATH to1830 without installing or substituting
tools. The validator now uses maintained exact toolchain/npm/TLS/cache selection and that existing
Windows preparation. Focused numeric parity passed at
`artifacts/tests/numeric-schema/0f3505edd0954991b3f4e72adeaac34b/`, retaining parser, writer,
official producer, actual generated client and nullable-numeric refusal checks. This is a test-harness
environment repair, not a schema change or token403 waiver. Fresh bounded Development and remote
qualification of the stable source remain due.

The full follow-up Development attempt is preserved at
`artifacts/validation-runs/20261014T034553Z-52f9240b/journal.json`: numeric generation, standalone
engineering and native frontend builds failed. Normal user TEMP, the independently verified shared
device Python and the existing Windows invocation PATH preparation resolved the remaining environment
failures in focused reruns. Validation-runner11, standalone restore/build/behavior/architecture/pack
with negative behavior, and native-start26 checks passed; logs are
`artifacts/tests/ds01-repair/prepared-*-20261014.log`. The failed full attempt remains failed.

The stable follow-up commit `548611c4422871487c8d49c575a7e6cc3562ecb6` passed all101 bounded
Development checks with the verified invocation environment. Its journal is
`artifacts/validation-runs/20261014T040543Z-a5704e8b/journal.json`. Latest full
[CI38509608053](https://github.com/orbyss-io/program-kit/actions/runs/38509608053) passed activation
and all other checks but retained both Firefox heading-focus failures. The foreground attempt is
therefore insufficient for Firefox acceptance. Additional finite owner-document/heading/popup focus
observations are being collected through targeted CI; no assertion or production helper was weakened.

Foundation0.3.4 is now fully public and independently verified. Protected Release38506924214
succeeded on attempt2 at the same immutable source. Program Kit independently downloaded its public
knowledge and verified SHA-256 `4d644f1fa5ca08f6c522fd64e20f373500fed4bd8dae82af2de582a62f593493`,
source `805383ad55e2f50716196faf2ba764073aa5f42c`, version0.3.4 and30 packages. The publisher verified
every public package payload and Host digest
`sha256:5c13acaf838cae83ab60e187fcef4720e67f85bc84201df4e3fb1ed2d6f938d9` on both platforms.
This resolves publisher availability; exact Program Kit profile adoption remains due.

Required [adoption workflow38510590025](https://github.com/orbyss-io/program-kit/actions/runs/38510590025)
stopped before qualification because its old0.3.0 blueprint would discard retained HostedPages
composition metadata. PKB610 correctly rejected that proposal. The updater now derives targets from
the verified current qualified default and checks preservation from both current and maintained base
before writes. Four preparation regressions retain historical bytes and reject corrupted history or
conflicting candidates. Dependency workflow17 and profile catalog34 focused checks pass at
`artifacts/tests/ds01-repair/updater-current-target/`; native adoption must still pass its complete
workflow. No local profiles, pins, knowledge or consumer locks changed during these repairs.

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

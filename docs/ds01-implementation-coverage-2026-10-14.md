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

The next [Firefox reproduction38511790143](https://github.com/orbyss-io/program-kit/actions/runs/38511790143)
observed all33 cases and isolated the provider-failure recovery to an active owner document with
an unselected heading and a still-open provider popup. The one-shot owner focus behavior therefore
needed an implementation repair. The maintained recovery module now waits for actual document
activation, preserves a user-selected control and disposes pending work on navigation or view
replacement. The compiled HTML example serves that same external module under its captured shell
prefix; guidance requires an actually served owner asset. Browser tests retain their original focus
assertions and never focus the heading themselves.

Final local verification passed22/22 Chromium/WebKit maintained authentication cases at
`artifacts/tests/reusable-foundations/functional-18477b4855e4496a/`. Presentation evidence at
`artifacts/tests/authentication-presentation/259c917e/` includes five module lifecycle cases,
25 compiled contract cases and20 browser observations covering activation, chosen controls,
self-only CSP and no-script presentation. Failure privacy, strict TypeScript and fast unit checks
also passed. Historical staged inputs were restored. Firefox still requires fresh Linux CI;
the failed foreground-only attempts remain failed.

The committed focus repair `a198f380ef1e35c9a1a1b1d757dc706b1d4bc159` passed all101
bounded Development checks at `artifacts/validation-runs/20261014T050339Z-084fefa4/journal.json`.
However, targeted CI38514486891 and full CI38514476241 still failed Firefox recovery-heading
selection with an active owner document. Local success therefore does not establish Firefox repair.
Further investigation retains the native assertion and adds only finite synthetic owner observations.

Required dependency update38514490015 successfully qualified/promoted its candidate profile and
public0.3.4 knowledge, then failed deterministic validation. Three failures were obsolete tests that
selected the evolving default while asserting literal0.3.3 identities; historical coverage must be
retained when correcting those assertions. The numeric official exporter failed with a real public
assembly mismatch. Independent local reproduction at
`artifacts/tests/ds01-repair/numeric-public-0.3.4-5b6f9b41/official-export.log` reports PKO200:
selected OpenApi.Exporter0.2.5 cannot inspect the0.3.4 closure's Microsoft.AspNetCore.OpenApi10.0.13
and Microsoft.OpenApi2.12.2 assemblies. The existing Foundation task received this exact integration
failure for supported repair and independent tool publication; no source-tool substitution is accepted.
The failed workflow also retained a PostgreSQL fixture failure whose inner log was omitted from
upload. A local exact-image role regression passed at
`artifacts/tests/schema-role-grants/771f02b29dc64c49b55b13b0231bcfff/`; its remote cause remains
unestablished. Narrow numeric and already-redacted role logs are added to future CI/update evidence.
Security scanning and opening the update PR did not run after these failures. No candidate profile,
pins or knowledge have been adopted locally, and no Program Kit patch has been selected or published.

The obsolete-default assertions are repaired with independent selected-context provenance checks;
explicit historical0.3.2/0.3.3 coverage remains. Composition30, wire11 and knowledge17 checks pass
under the unchanged admitted default. Public0.3.4 wire/guidance projection checks pass at
`artifacts/tests/ds01-repair/adoption-fixture-compatibility/`; these disposable projections do not
reconstruct missing qualification authority. Future update evidence preserves the actual candidate
registry and maintained catalog alongside qualification logs so their original hashes can be checked.
The native focus trace passes22 local browser cases at
`artifacts/tests/reusable-foundations/functional-075d587c8e8c45b2/`, and strict finite projection
contracts pass at `artifacts/tests/reusable-foundations/contracts-6e9c0868895e4439/`.
Presentation/lifecycle/privacy verification passes at
`artifacts/tests/authentication-presentation/32009c7c/`. The diagnostic change forwards native calls
only on exact fictional owner pages and exports eight booleans plus a closed active-element category;
it reads no private text, value, provider DOM or raw exception. This establishes observability, not
another claimed Firefox repair. Fresh targeted Linux reproduction is required.

Targeted diagnostic CI38520948303 failed both Firefox owner recovery cases and established that
the active document called native heading focus, which never selected the heading. The active element
remained the body; no activation, visibility or rendering-frame callback occurred. This narrows the
failure to the initial refused call rather than a later lost selection. The next candidate schedules
initial focus through the same existing coalesced rendering-frame boundary. It retains neutral-focus
guards, cleanup and the native assertion. Local22/22 journeys pass at
`artifacts/tests/reusable-foundations/functional-90d1bb2cca534815/`, now observing actual frame
execution and heading selection. Lifecycle,25 compiled presentation cases,20 browser observations
and credential-failure privacy pass at `artifacts/tests/authentication-presentation/9140cf7c/`.
Historical source and52 staged inputs were restored. Fresh Firefox acceptance remains required.

Full diagnostic CI38520934866 retained the refused initial focus and also reproduced the PostgreSQL
fixture failure. Its newly preserved inner logs show socket readiness followed by a missing socket
on the first SQL command. The exact immutable18.6 image entrypoint confirms a temporary socket-only
initialization server (`listen_addresses=''`) that stops before the final server starts. Readiness now
requires127.0.0.1 TCP, matching the actual application transport and excluding that temporary server.
Real role grants, denial, idempotent deployment and application-login checks pass at
`artifacts/tests/schema-role-grants/51dc3dfb43ef4159a9fc56f4f3b0b9c5/`. This repairs fixture readiness;
the historical failed runs remain failed and consumer schema ownership remains unchanged.

The Foundation task reports an exporter repair in PR12 at
`ef5d1e7f22e425bb05ca93398d7bea9f80534ffb`: tool-private OpenAPI assemblies shadowed the staged
runtime closure. The independent0.2.6 candidate removes that private dependency and obtains the native
document provider from the validated staged assembly. Installed diagnostic-package acceptance against
public0.3.3/0.3.4 and frozen older/Assurance closures is reported passed. This is candidate evidence;
full qualification and protected public publication remain pending, so Program Kit does not adopt it.

Exporter0.2.6 is now public. Protected independent publication38524116102 completed successfully
after Windows/Linux CI38522658333 and mandatory qualification38522657477. Program Kit independently
downloaded and verified its exact source `ef5d1e7f22e425bb05ca93398d7bea9f80534ffb`, all16 payload
files and the absence of private OpenAPI libraries. Public package SHA-256 is
`222126f6be411b3e45287a14fe5449fd7a8a450048e6c7f8c5aba18a597e7cbd`; independent tool knowledge
SHA-256 is `acc51cb1788d15ed6eb716cdbcfc85f585054f3736459ba41ce30e59a22cb43c`.
Evidence is `artifacts/tests/ds01-repair/exporter-0.2.6-public/verification.json`.
The previously failing real public0.3.4 exporter fixture now succeeds with0.2.6 at
`artifacts/tests/ds01-repair/numeric-public-0.3.4-exporter-0.2.6-f1efcfc2/`, retaining exact producer,
business-effect exclusion, controlled negative registration and unsupported nullable refusal.
This is isolated tool compatibility proof, not complete candidate profile adoption.

Targeted CI38523570537 passed cold qualification but failed one Firefox landing case on the prepared
consumer; fullCI38523575187 failed both cold Firefox recovery cases. The frame did execute in an
active document, but native focus remained refused. The TCP role fixture passed in that full run.
Pinned [Playwright1.64 source](https://raw.githubusercontent.com/microsoft/playwright/v1.64.0/packages/injected/src/injectedScript.ts)
and its actual installed bundle independently document two native focus calls for Firefox scenarios.
The next candidate therefore permits one guarded second native call within the same rendering frame
only after refusal, while connection, visibility, non-hidden/non-inert state, neutral user focus and
binding lifetime still permit it. There is no delay loop, platform sniff or test-side forced focus.
Local22/22 journeys pass at `artifacts/tests/reusable-foundations/functional-6e5005829b4f46fc/`;
seven lifecycle regressions,25 compiled cases,20 actual browser observations and privacy proof pass
at `artifacts/tests/authentication-presentation/bff63d2d/`. Exact primary/source evidence is
`artifacts/tests/ds01-repair/focus-native-fallback-ab05254a.json`. Fresh repeated Firefox qualification
and the complete required dependency/security workflow remain mandatory before adoption/publication.

The required Program Kit dependency workflow, exact new profile/knowledge adoption and fresh
Program Kit Release qualification remain open. Program Kit patch publication is authorized after
these gates. The Windows Release command must run in the user-owned terminal unless the user
explicitly overrides the restriction. No paid live phase, real-consumer acceptance or release success
is claimed by this record.

Published Program Kit v0.13.1 is tag source `5e462b73b2fd34604701573161f9fd071e09427f`.
The existing repair PR41 remains unpublished and includes the original fifteen repairs plus this
extension. During patch preparation, carry its unreleased diagnostics migration addition into the
new patch guide and restore the published0.13.1 guide bytes; do not describe that addition as already
delivered in0.13.1. Preserve original diagnostic records and immutable native source witnesses.

## Additional approved batch, items29–33

The user confirmed implementation after the additional grilling. See
[the classification, repair matrix and separate PDF/OCR handoff](ds01-additional-repairs-2026-10-14.md).
Private storage and selected dependency readiness are Program Kit defects. npm child PATH
reuses the existing safe preparation algorithm, managed into standalone engineering helpers.
Review scoping uses versioned supported projections inside the current checkpoint lifecycle,
preserving human decisions while separately blocking stale engineering. PDF/OCR remains
consumer-owned with generic parser qualification added to existing semantic guidance.

Current focused evidence: `artifacts/tests/ds01-repair/second-batch-toolchain-native.log`
passes15 cases including actual npm child execution with oversized inherited PATH and unchanged
parent environment. `second-batch-review-final.log` passes32 cases including scoped freshness,
shared authentication/storage impact, preserved decisions, unknown/deleted inputs and failed
checks. Final native-start evidence passes37 cases, with two Windows filesystem limitations
covered by Linux CI (POSIX ownership and directory symlinks). The complete new disposable Host
qualification passes at `artifacts/tests/composition-start/ad55635a5d294803b1d448699cacac1b`:
actual non-root Host writes retain65,536 bytes across restart, authenticated public requests
cannot retrieve them, missing retained storage is rejected and recovery succeeds, cold update
starts selected prerequisites and stopped database recovery preserves its container identity.
Existing identity reconciliation, browser privacy, immutable frontend revision and incomplete
product-architecture refusal checks still pass. Source helper hashes, immutable image identities,
Compose hash and retained-byte hash were independently verified in
`artifacts/tests/ds01-repair/second-batch-native-verification.json` against repair source
`d36d8177acdd8e1e8218e588975d7b9945b8ae1c`. These are focused
checks, not a Release receipt or real-consumer acceptance.

Both failed native attempts remain preserved. The first proved the new guarantees but stopped
the Host during the deliberate missing-volume case and omitted restart before an existing later
browser check; the fixture now explicitly proves volume recovery. The second failed because
Docker had exhausted its network address pool, before host activation. Disposal removes only
this fixture's hash-verified Compose containers/network, retaining named volumes, private data
and all evidence; no global Docker pruning was performed. Final PostgreSQL readiness uses TCP
to exclude the image's temporary socket-only initialization server.

Current exact-source full CI38536210895 and mandatory dependency qualification38536205978 are
running for `d36d817`. Bounded Development is running with preserved log
`artifacts/tests/ds01-repair/development-d36d817.log` and journal
`artifacts/validation-runs/20261014T083448Z-f3c982c0/journal.json`. No complete Release was started
from this task, and no release tag was created.

The bounded run exposed a Windows source-test loader omission: it loaded `js_toolchain`
without its managed shared PATH module. Installed consumer helper hashes were already verified.
The test loader now loads the same canonical module, and all28 setup cases pass in
`artifacts/tests/ds01-repair/second-batch-foundation-setup.log`. Preserve the original failed
bounded journal; fresh passing Development evidence is required. Final source review also
rejects `__` in private configuration target literals, preventing environment-key nesting into
framework settings. All12 focused private cases pass (the same two platform skips). The native
proof above remains exact for its original source; the added refusal requires current-source
CI and eventual complete Release qualification, with no altered receipt or false reuse claim.

Prior-source targeted three-engine CI38526047800 and full CI38526053067 passed. Mandatory
dependency update38526051812 failed the hardcoded exporter0.2.5 expectation after selecting
public0.2.6; consumer-provider validation was dependency-blocked rather than executed. Logs
and artifacts remain under `artifacts/tests/ds01-repair/remote-failures/dependency-38526051812`.
The repaired test compares selected catalog to independent active tool-manifest authority and
retains frozen historical expectations. No failed update is adopted and publication remains
conditional on this batch plus complete required qualification.

## Final-source qualification and native logout ordering

Source `38db205dab87518b1a4224cfd073e82b1ed61d40` passed all101 bounded Development checks
in `artifacts/validation-runs/20261014T085526Z-e99350ec`; its successful log and journal
remain unchanged. Full CI38537958578 and required dependency update38537955991 both failed
only `qualify_reusable_foundations`, at WebKit's lost-observation independent session check.
Both exercised all33 authentication cases without skips; Firefox focus was not the reported
failure. Their exact logs/artifacts remain under `artifacts/tests/ds01-repair/remote-failures`.
The required update did not reach Host scanning or a tested update PR and was not adopted.
Its real mixed-host, three-engine composition qualification passed all new storage/readiness
guarantees on the candidate profile; that intermediate proof does not satisfy adoption gates.

The old test made one immediate session request after browser observation failed. The production
adapter correctly returns unconfirmed after dispatch without promising that the separate popup's
POST has completed. The redacted old logs do not establish the exact response or exception.
The strengthened test holds the actual native POST, observes authenticated state independently
while pending, releases native dispatch, then requires absent session within a bounded independent
observation and exactly one POST. Private content stays cleared and explicit recovery remains
required. It fabricates neither a successful response nor cookie removal; production adapter
behavior and all timeout/cancellation assertions remain unchanged.

Both controlled cases passed in the first local native run; that overall run failed the human-paced
login with a deliberately tight17-second fixture window after16 seconds of human delay. That
evidence remains preserved. With an explicit bounded30-second fixture window, all22 native
Chromium/WebKit journeys pass in `artifacts/tests/reusable-foundations/functional-eb8809ac4d0c4c82`.
Original source/settings/bundle bytes were restored; the production900-second default and existing
consumer overrides were not changed. Bounded classification/privacy contracts also pass.
The added fixed `uncertain-session-before-dispatch` checkpoint exposes ordering without retaining
page/provider data. Fresh CI and complete required qualification are still mandatory; no claim of
new-source Firefox acceptance or patch publication is made here.

## Approved DS02 follow-on batch; publication held

The owner's later instruction pauses publication and authorizes the remaining DS02 repairs.
The separate execution matrix is `ds02-program-kit-repair-batch-2026-10-14.json` (items34–41).
Earlier DS01 findings, approvals and original evidence above remain intact; the real consumer
checkout is read-only. No dependency selection, lock, migration or baseline changes in this batch.

| Item | Root cause and disposition | Reusable repair and focused evidence |
| --- | --- | --- |
|34 Review capacity | Confirmed checkpoint persistence defect; must fix | Intern verified distinct bases inside existing retained state; 8-KiB current summary and 1-MiB retained state; atomic legacy migration. Sixty decisions over121 files retain every original basis, with overflow/tamper/expansion refusal. |
|35 Scoped continuation | Confirmed workflow transition defect; must fix | Preserve existing owner's named permits independently of engineering freshness. Changed operation meaning revokes affected permits; technical failures, enabling prerequisites, stale acceptance and closure remain guarded. No new approval ledger. |
|36 Active effort | Confirmed clock transition defect; must fix | A permitted active operation keeps accruing; actual human waiting and suspension stop it. Scope revocation stops future accrual while preserving accumulated effort and original corrections. Synthetic-time regressions cover multiple checkpoints and exact-once accrual. |
|37 Ordinary providers | Confirmed model/scaffold defect; must fix | Explicit runtime providers use IShellFeature/retained ProviderFeature identity; database bindings select persistence, packages and Prepare. Historical implicit persistence captures keep their meaning. Model34 and real CShells activation pass; published-Host qualification is separately retained. |
|38 Prepared activation | Confirmed runner defect; must fix | Pending activation is separate from source freshness. Plain update activates fresh prepared bundles; selected update retains others; clear only after real readiness. Newly rebuilt bundles retain pending intent across readiness failure. Eight focused transitions include failed-boundary retries. |
|39 Runtime PdfPig loading | Verified Nuplane.Loading defect; external handoff, excluded from Program Kit repair | [Nuplane issue132](https://github.com/valence-works/nuplane/issues/132) includes exact package/assembly/version/source evidence. Ordinary runtime dependencies need not be isolated. No parser replacement, worker runtime or package/pin workaround is introduced. |
|40 Build-only dependencies | Confirmed architecture/freshness defect plus missing qualified output guidance; must fix | Distinct buildProjectReferences participate in source/affected closure without permitting CLR edges. A closed owned-output recipe uses SDK Publish before content enumeration, exact nested copy/pack paths and current PE metadata. Real executable clean/incremental/rename-removal/copy/pack checks pass; unknown tasks remain refused. |
|41 EF test seam | Consumer test integration mistake; guidance and separate handoff | Replacing admitted options is intentionally rejected. Select the published0.3.4 additive interceptor seam only through qualified adoption, or independently qualify an exact-version fixture-owned completion diagnostic. Require postcommit fault propagation, isolated subscription disposal, independent receipt discovery before replay and one durable effect. No production wrapper or friend-access addition. |

The output-recipe qualification caught two real recipe errors before acceptance: copying after
Build missed cold transitive content enumeration, and a directory-only PackagePath duplicated
nested resource paths. Both failed attempts remain under `artifacts/tests/ds01-repair`; neither
was treated as success. The final executable proof also checks runtime configuration, notices,
actual execution and the absence of a CLR reference to the build-only producer.

Current focused logs include `ds02-review-final-scope-effort.log` (44 cases),
`ds02-provider-source-scope-final.log` (34), `ds02-native-start-retry-qualified.log` (46,
two known Windows platform skips), `ds02-scoped-verification-final.log` (50) and
`ds02-build-output-executable-final.log` (28). Logs and fixtures are ignored local evidence,
not consumer acceptance or a Release receipt. Preserve the sandbox-TEMP permission failure,
the mistaken native test invocation and the first full-prepare/isolation assertion failure
separately. The latter conflated full prepared-host activation with selective-update isolation;
the corrected integration exercises and asserts both behaviors independently.

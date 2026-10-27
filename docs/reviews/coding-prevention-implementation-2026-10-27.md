# Coding prevention implementation and review

## API contracts, configuration and method layout follow-through

This later increment uses Program Kit base `40220694` and the isolated Foundation implementation branch;
earlier results below retain their original scope. The trial consumer's US4 remains halted and untouched.

Review these concrete Program Kit owners:

- `extensions/program-kit-dotnet/references/examples/typed-operation/Operations/{ReadLabel,WriteLabel}/Endpoint.cs`
  own route/name, native handler binding and prepared failure-status metadata. Composition registers/maps only.
  The two operations intentionally register the same shared `LabelResponse.Contract`; matching declarations
  are idempotent. Request/response declarations name supported capacity and actual configured profile keys.
  `AddJsonEndpoint` preserves deferred scoped activation for cold metadata export; no fake provider is added.
- `Configuration/LabelApiOptionsValidator.cs` implements native `IValidateOptions<T>`, including null/empty/long
  rejection. The real typed-operation renderer includes it. The contract namespaces, schema identities,
  `/api/sample-label` path, operation names and response status sets remain unchanged.
- Canonical `dotnet-engineering.md`, `secure-web-profiles.md` and programming guardrails cover operation-owned
  contracts/mappings, shared semantic permission keys, inferred locals, whitespace phases, provider query
  factories and meaningful reusable construction. They prohibit neither simple loops nor legitimate target
  typing. Method extraction and semantic ownership remain review duties, not automatic analyzer claims.
- The emitted `.editorconfig` enables the standard SDK var preferences and IDE0007 error. Maintained native
  source-category controls compile the positive inferred local plus typed expression factory/IQueryable path,
  then reject an explicit eligible local alongside the existing layout/prepared-value/chain negatives.
  The native fixture now reads active package/ABI pins and a declared public feed rather than fixed old pins.

Foundation adds descriptive registration and numeric schema repair in the existing Json/Json.AspNetCore,
Authentication and Web.ProblemDetails owners. Its committed review is
`docs/validation-api-contract-ergonomics-2026-10-27.md` at source `5101abcb38e5c1f7dedc44ae574771784eb46761`.
That note indexes the strict/loose nullable-number reproduction, actual-profile/native producer controls,
custom converter limits, supported versus deployment budgets, permissions and the original application JSON
capacity initializer's purpose. This is a bounded numeric correction, not universal serializer/schema parity.

Retained local verification:

- Final Program Kit Integrity: passed 7.410s, `artifacts/validation-runs/20261027T221430Z-f5f62fe4/results.json`.
  Final knowledge/guidance regressions: passed 27.438s,
  `artifacts/validation-runs/20261027T221430Z-ac9880fd/results.json`.
- Native source-category controls passed all 16 mutations, including SDK IDE0007, after a successful positive
  and restored positive. `artifacts/api-ergonomics-native-var.log` and `artifacts/t/typed-native-a43bddf7/style-*`
  retain the output. This focused reuse used its existing SDK 10.0.402/analyzer 0.3.7 fixture; released-profile
  qualification must rerun the maintained full fixture with the final adopted pins.
- Existing syntax oracle: 49 actual new Foundation/emitted C# files, 14 adverse controls, zero violations;
  `artifacts/readability-problem-statuses-final2.log`. Foundation's actual HTTP JSON/admission and problem-status
  metadata controls passed; its independent parent validation/release remains separately owned.
- Original independent Affected report `20261027T220652Z-0e013c9d` remains needs-attention: expanded guidance
  exceeded the established brief limit, and sandbox privileges prevented an owned test junction. Guidance was
  condensed without raising limits; all 25 knowledge tests passed. The focused junction case passed outside
  the sandbox (`artifacts/api-ergonomics-junction-external.log`), 1 test/0.015s. The original composition-model
  run also exceeded its budget; a focused case does not turn that run into a pass.

The coordinator still owns public Foundation 0.3.8 publication/availability, every affected Program Kit profile
and lock/knowledge refresh, actual released-package cold OpenAPI export/generated-client qualification,
`validate_coding_scaffolding` and final full Affected selection against `40220694`. New API source alone cannot
qualify old public pins. No consumer toolkit refresh, app restart or refactor was performed in this increment.

Parent review subsequently found a compatibility omission: the revised finite recipe emitted APIs introduced
in Foundation 0.3.8 while `coding_scaffold.native_contracts` still admitted 0.3.6. The existing native preflight
now requires a stable qualified runtime at least 0.3.8 and retains its same-release/actual-owner checks.
An old API declaration is rejected before rendering a usable preview or writing business files; no pin or
consumer lock is rewritten. The README states this prerequisite and retains ordinary manual implementation
against an older release's supported APIs, without presenting the newer helper calls as compatible.

Focused compatibility proof: five existing/new scaffold tests passed (10.322s), including actual native MSBuild
preview inputs, 0.3.7 rejection with a byte-for-byte unchanged source/lock snapshot, same-owner requirements,
stable 0.3.8+ positives and older/malformed/prerelease negatives. These tests use fictional project declarations
to test preflight; they do not claim public package availability or compile the emitted new-runtime sources.
Output is retained at `artifacts/api-ergonomics-recipe-version-guard.log`. The full emitted native fixture and
released-package export remain the coordinator's post-publication adoption checks.

Parent semantic review also found that the earlier API-options activation claim had no observation owner:
binding plus `IValidateOptions<T>` alone deferred validation until an endpoint first read `Value`. The actual
example now registers non-disposable scoped `LabelApiOptionsAdmission : IShellInitializer` in native preparation
(order -1000). Its sole dependency is `IOptions<LabelApiOptions>`; it performs no provider construction or I/O.
The renderer includes the admission file under API Configuration. Later protected effects must follow required
admission; native initializer object enumeration/construction is distinct from ordered work execution.

The maintained scaffold test now compiles the actual binder/validator/admission sources with a real selected
CShells registry. Missing/null/empty/oversized configuration rejects with the API owner's actual native
`OptionsValidationException`, publishes no failed generation and executes no later Start-phase observation.
Valid nondefault configuration remains unchanged and the later phase executes once. This does not claim that
arbitrary provider constructors are never created or that a real database was qualified. Cold exporter
qualification still belongs to the coordinator's actual released-package route, which must keep initializers
unexecuted. The focused native activation, emitted-source layout and renderer inclusion tests passed (3 tests,
`artifacts/api-ergonomics-options-final.log`). Original setup and sandbox DNS failures remain in preceding
options-activation logs; the approved external-process run restored declared public dependencies and passed.

The user authorized the research plan's Program Kit prevention changes in a fresh implementation agent, with parent coordination and independent review. They explicitly retained trial-consumer refactoring for a later joint plan. The consumer remains read-only evidence.

Working checkout: `C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis`, branch `codex/bootstrap-intake-analysis`, baseline `88477de14db70837f342f87854d375c4e0ce1f69`. The untracked [audit](trial-consumer-coding-system-audit-2026-10-27.md) and ignored evidence are preserved. The main checkout and unrelated work are untouched.

The implementation proceeds through three connected existing owners:

1. Scoped discovery and canonical phase guidance: identify actual recurring/background execution without confusing startup/ordinary async work; surface concise source-attributed operation constraints within the existing bounded phase route.
2. Native planning/task/implementation/review guidance: establish semantic state/policy/configuration/lifetime ownership and useful file placement before the first pattern is replicated. No new gate, ledger, blanket string rule or automated semantic certification.
3. Maintained typed-operation example and adapter: emit meaningful project-local ownership, preserve existing HTTP identities and recipe behavior, and exercise real generated placement plus browser admission and configured operation boundaries with focused regressions.

The selected Foundation analyzers retain their qualified mechanical scope. No new analyzer version or semantic engine is invented. Deterministic checks establish only their exercised mechanisms; consumer correctness, arbitrary agent obedience, provider acceptance and human product acceptance remain separate.

## Delivered owners and inspectable changes

- `feature_context.py` discovers bounded selected native background/recurring implementations and registrations in planning, task review and implementation. Trial-shaped queued-processing prose selects the same existing async-workload guidance. Startup-only tasks, ordinary async HTTP, imports/package-only Core, comments/string lookalikes and excluded future work remain negative controls.
- Canonical `programming-guardrails.md` and `modularity-and-contracts.md` now own first-operation semantic review and project-local placement. The ordinary phase renderer carries essentials with canonical attribution before detailed optional context. Plan/tasks/implementation and architecture review require actual code, state/policy/configuration ownership, method coherence, total budgets, effects and negative behavior before replication. Named arguments retain recommendation wording.
- The typed-operation adapter emits separate `Operations/ReadLabel` and `Operations/WriteLabel` owners, shared `Representation`, `Configuration`, and meaningful Core/runtime/provider `Labels` groups. Public label wire types, route and operation names remain stable. A bounded old-root conflict check preserves partial authored adoption and refuses duplicate types, including a file appearing after preview; refactoring remains ordinary authored work.
- The browser adapter executes strict request/token and bounded UTF-8 response admission, preserves empty string contract variants and tolerant response fields, and cancels/releases its reader. Caps derive from the native example's 1024/2048 byte profiles.
- Runtime `LabelOperations` uses the existing native Execution owner for one configured complete-operation deadline. It forwards a bounded BCL token into both units, checks original caller cancellation and monotonic completion freshness, and distinguishes expiry. This token-only port does not propagate native deadline object identity/provider classification. Expiry supplies neither hard stop nor rollback/retry authority. The runtime's documented configurable default is an I/O safeguard; Core contains no policy default.
- `typed_operation_native_check.py` builds actual emitted projects and split, documented test support with the selected 0.3.7 analyzer enabled. It exercises cumulative budget exhaustion, non-cooperating late write/read, delayed timer callback, original caller cancellation, omitted/default and nondefault configuration, exact supported timer maximum and over-limit rejection before effects, and clock ownership. An actual inline-array ORB1008 negative guards native enforcement. Test support is placed under mirrored `Labels` ownership. Independent missing-effect negatives retain exact mutation seams and behavioral markers.

## Parent review and retained evidence

Parent review found and corrected planning/task source discovery, an inaccurate canonical link, partial legacy-root preservation, restarted operation budgets, inline deferred validation, inline SQL collection arguments and completion freshness. These are substantive independent review findings; deterministic passing fixtures did not reveal every defect on their own.

Inspect ignored `artifacts/consumer-audit-2026-10-27/parent-discovery-review.json`, `parent-real-scope-review.json`, `parent-final-guidance-review.json` and `parent-client-review.json`. The final read-only trial scope selects async work in all six phases; its first CLI page includes all four concise essentials (15,550 total assembled bytes). The parent observed 14 actual emitted browser controls. Native initial failure is retained at `artifacts/t/prevention-parent-73a3d778/`; corrected emitted/native deadline and ORB1008-negative evidence is at `artifacts/t/typed-native-3dcbac20/`. The later `artifacts/t/typed-native-87f72fb3/` additionally compiles actual base and multi-context composition-provider sources. Earlier implementation fixture failures remain alongside them; no failure evidence was overwritten.

## Validation and explicit limits

Initial focused discovery, guidance and scaffold preservation/browser controls passed. Integrity passed in 6.77 seconds: `artifacts/validation-runs/20261027T144647Z-4bc4ceb0/results.json`. Reproduce fixed-source validation with `./scripts/Test-ProgramKit.ps1`, then `python scripts/run_validation.py --suite Affected --changed-from 88477de14db70837f342f87854d375c4e0ce1f69`. The parent coordinates final source-bound review results and focused installed/generated-route evidence.

The first Affected run is retained at `artifacts/validation-runs/20261027T144751Z-e6c40938/results.json` (430.04 seconds, needs-attention). New scaffold/browser/native checks passed; canonical parent coverage registration failed and was repaired through existing `coveredBy`/requirement routing. Three checks lacked `specify_cli` in global Python; the existing prepared interpreter is `C:/Users/tech_/AppData/Roaming/uv/tools/specify-cli/Scripts/python.exe`, with no installation. Composition's single link/junction control and one Bash parse control hit sandbox privilege failures; composition's 132.15 seconds also exceeded its 120-second budget. A focused external link control passed, preserving that broad failure/overrun. Numeric export reached actual native output, then npm DNS failed under sandbox. Its retained actual document passed the unchanged maintained generated-client owner externally (`artifacts/tests/numeric-client-retry/91de2511/results.json`), without a broad export rerun.

The first explicit F4 installed-layout review failed on the absent retired `task_draft` engine (`artifacts/validation-runs/20261027T144859Z-a45a02f7/results.json`). Investigation found the whole historical fixture still assumed retired prepare/finish/reconcile/pattern-ledger protocols. Its maintained scenario now uses current native `typed-label` preview/apply and real independently built application tests; no retired engine was restored. It preserves root/late-file conflicts, original tasks and managed state, manual customization, and a successful native build before the intended omitted-write behavioral failure. Earlier retained review directories remain intact.

The repaired focused knowledge/phases/native-scaffold/F4 cohort passed in 111.04 seconds (`artifacts/validation-runs/20261027T145849Z-afcdf790/results.json`). Parent review then caught an installed-consumer setup preservation defect: F4 now captures actual original state before authoring and refuses changes to all differing pre-existing assets. Its source-copy journey establishes a nonempty fictional managed sentinel before setup. The strengthened F4 passes in 37.46 seconds (`artifacts/validation-runs/20261027T150213Z-f840e683/results.json`). The single unchanged Bash parse control also passes outside the sandbox; no Linux acceptance is implied.

Actual typed-operation qualification retained two further failures: prepared Python was incorrectly selected as the shared device interpreter, then real native compilation found four ORB1007/1008 diagnostics in inherited inline PostgreSQL context factories. Explicitly selecting the verified existing shared `C:/Python315/python.exe` addresses the first without installation/PATH masking. Named factories and vertical arguments now repair both existing `foundation_composition.py` and `composition_render.py` owners; the focused native check compiles both actual generated shapes. The selected integration fixture's inherited private-options/probe route source was also inspected and brought under the same rules before retry. The manual typed-operation input map now includes its real example/adapter/producers, preserving `manualOnly`. These failures are retained at `20261027T145923Z-86fab76f` and `20261027T150225Z-836b8966` under ignored validation runs; full runtime qualification remains a distinct actual result, not inferred from these repairs.

The latest full runtime attempt (`20261027T150856Z-532e5401`, 98.95 seconds) compiles the repaired source, then fails before label integration at `release_bundle.py:941`: PostgreSQL's restored `Microsoft.EntityFrameworkCore.Relational/10.0.13` nuspec requires Configuration.Abstractions >=10.0.13, pruned from that ASP.NET-framework project's assets; non-web runtime/ordinary-provider roots restore Configuration.Abstractions10.0.0. The merged staging closure selects10.0.0 and correctly fails PKR014 consistency. Exact initial generated project assets/nuspecs remain under `artifacts/t/cs-de85a311/c`; `implementation-closure-diagnosis.json` indexes dependencies. This is a separate mixed-root/framework-pruning staging defect in the existing release-bundle owner. Its resolution requires explicit closure/native-framework ownership investigation, not pin/lock changes or weakening the guard as part of prevention. Full Host/provider/effect/restart/browser integration remains blocked and is not claimed.

To complete the changed contract proof independently, existing `validate_typed_operation.py --export-client-only` now compiles/packages the actual moved API/Core sources with a thin fictional native wrapper, invokes the selected native feature/settings producers and official exporter, asserts unchanged actual route/operation identities, then uses the shared maintained generator/compiler to compile the emitted client against real generated label paths. It adds no runtime/provider fake, hand-authored schema/types or staging bypass. The manual `validate_typed_operation_contract` check passes in17.94 seconds (`20261027T151942Z-250376fe`). Initial cold-wrapper setup failures are retained separately. Shared numeric behavior remains intact: the same retained native numeric document passes the extracted generator plus unchanged numeric assertions in7.26 seconds (`artifacts/tests/numeric-client-retry/d2507818/results.json`). Cold output records explicit false runtime/provider/HTTP/Host-staging flags and actual API/Core/document/adapter identities.

Final supported provider/native/scaffold and inventory checks passed in45.59 seconds (`20261027T150844Z-26a8154d`); later Integrity passed in6.75 seconds (`20261027T151729Z-2848e86f`). Remaining broad owner-operation, composition-start/layout, emitted-CI and nested-composition scenarios were not expanded into a matrix: changed factory shapes have focused actual native compilation; no authentication, provisioning, nested-shell or external provider semantics were changed. This disposition does not repair or green the separately observed full-runtime staging failure. The final code and review handoff remain uncommitted.

Final code verification: Integrity passed in6.81 seconds (`20261027T152238Z-fcd69fc7`), followed by the final native/scaffold/browser/CLI-mode controls, inventory and canonical knowledge cohort in55.48 seconds (`20261027T152244Z-95058a4c`). Both records report unchanged working inputs during execution. This paragraph is a subsequent report-only update; it changes no tested implementation contract. The parent independently reviewed source, actual output and limits. No live coding agent or consumer acceptance was exercised.

Focused reproduction uses the existing prepared interpreter with `scripts/run_validation.py --check validate_coding_scaffolding --check validate_validation_runner --check validate_knowledge_inventory --check validate_knowledge_sources --reason "prevention source and canonical coverage"`. The cold actual label route is `--check validate_typed_operation_contract --reason "actual moved label producer/generated client"`; it needs the existing shared device Python and project-local dependency network access. The full runtime route remains `--check validate_typed_operation --reason "actual native label/provider/browser integration" --engines=chromium,webkit`, selecting `PROGRAMKIT_DEVICE_PYTHON=C:/Python315/python.exe` independently of the prepared Spec Kit interpreter. Its recorded PKR014 failure is the unresolved disposition, not a passing reproduction.

The new native fixture uses cached selected packages with no restore sources; a missing package remains a failed prerequisite, never permission to install toolchains. Actual generated-client export/compilation retains its existing owner. Broad unrelated Host/composition scenarios are not implied by helper edits. Firefox is unavailable on this Windows host; affected browser CI remains authoritative for Firefox. Linux and consumer acceptance are not established locally.

The selected analyzer mechanically enforces its released scope. There is no automatic detector here for arbitrary string states, semantic Core provider policy, mixed abstraction, all SOLID violations or useful arbitrary file placement. Those remain explicit source/adverse-behavior review duties. A future mechanical rule outside the selected released contract requires a concrete external Foundation analyzer contribution and qualification; no fabricated enforcement claim is made. Deterministic fixtures establish exercised mechanisms, not agent obedience or human acceptance.

No commit, push, PR, consumer repair, publication, paid worker or provider operation is authorized by this work. This work leaves the consumer untouched for the later jointly defined refactoring plan.

## Follow-up: category enforcement and refactor feedback

The human subsequently authorized Program Kit repairs and commit/push on
`codex/bootstrap-intake-analysis`. This follow-up does not repair or refresh the active consumer.

The active implementation owner is the chat **Implement US4 refactor plan**, not the earlier
**Implement current feature tasks** chat initially consulted. Its retained history records the human
flagging `inspection_unavailable`, the implementation owner's acknowledgement of repeated shared
failure-code literals as an omission, and their replacement with owner-scoped constants. The later
coordinator inspected repaired source. A public Core state-to-storage/wire mapping switch was a
different observation, and does not refute the earlier failure-code omission. The public placement of
that representation map and remaining provider transition ownership still require their own review.
This is observed human-triggered correction, not evidence that a scheduled review caught the issue.

Canonical first-operation, planning, tasks, implementation and architecture guidance now require
shared failure/retry key ownership in actual decisions/private helpers and honest completion evidence.
The selected .NET guidance explicitly requires Microsoft Options binding/validation at actual shell
activation before immutable domain/work admission. Preserve existing keys/defaults/conversion semantics;
Core need not depend on IOptions, and retries retain original admitted snapshots. No blanket string,
static-method or switch ban, general constants sink or automatic semantic detector is introduced.

The whole source-readability category is in scope, not only method chains:

| Rule | Mechanical owner and exercised proof |
| --- | --- |
| Next-line control-flow bodies; simple unbraced bodies allowed | SDK IDE2001 with EnforceCodeStyleInBuild; native positive and same-line negative |
| Parameter/constructor/call layout | Released ORB1007; native malformed declaration and call controls |
| Prepared method/constructed/awaited/deferred arguments | Released ORB1008; independent native controls plus the retained inline-array negative |
| Receiver and every chained invocation on separate lines | Released ORB1009; first-call-beside-receiver and combined-call negatives |
| Fields first, private helpers last, one type, XML presence | Released ORB1010/ORB1004/ORB1003/ORB1005 native controls |
| Private fields camelCase without underscore | SDK IDE1006; explicit build-level severity added after its negative initially compiled successfully |
| Method coherence, purposeful XML, policy/key/configuration ownership, SOLID and native reuse | Mandatory actual source review; no automatic semantic certification claimed |

SDK naming-rule severity alone was insufficient build enforcement. The template now sets IDE1006
error severity and enables SDK code-style analysis. Native build and task preflight reject disabled
code-style analysis. The emitted-source fixture uses actual maintained props/targets/EditorConfig and
the pinned SDK, requires successful positive compilation before intended diagnostic failures, rejects
incidental compiler/analyzer crashes, and restores a passing positive afterward. Existing editable
label examples and runtime support use next-line bodies/statements. No external/generated/historical
source was mass-reformatted. ORB1002 named arguments remain a recommendation.

Complete selected .NET time/options and layout rules are now emitted with canonical provenance in
ordinary phase context, after existing framework/EF essentials. Scoped Rust work excludes those .NET
sections. Pagination is preserved; the representative assembled context is about 20 KB, measured
against a 22 KB regression bound rather than truncating its rules. Installed native-phase review and
the full native source category have focused regression coverage in the existing inventory.

Retained initial diagnostics include `artifacts/t/native-phases-first.log`,
`artifacts/t/native-style-second.log`, and the per-control directories under `artifacts/t/typed-native-*`.
The first exposed rules pushed EF essentials past page one; ordering was corrected. The second
exposed missing naming build severity. A sandboxed optional formatter also failed connecting to its
MSBuild named pipe; the source fixes and actual compiler checks do not depend on that formatter.
Validation outcomes for the final source are reported in the coordinating chat and existing
`artifacts/validation-runs/` records. These remain local proof, not publication/agent-obedience claims.

The deferred `validate_typed_operation_contract` is cold actual label metadata/client proof, not a
Host/provider/browser scenario. No schema, route or client shape changed here: the label source changes
only line layout. Native emitted-label owner compilation/runtime controls and the selected actual
OpenAPI export/client check cover the changed mechanisms; the extra cold label producer run is not
claimed. The separate full runtime scenario's earlier PKR014 disposition remains unchanged.

The first follow-up Affected run (`20261027T182237Z-bef7b46e`, 147.564 seconds) retained four failures:
the expanded source brief exceeded its existing 10 KB budget; the new native negative expected a
compiler-style code prefix for an MSBuild error that actually rejected correctly; a reused scope
test expected complete canonical text from the intentionally brief view; and new .NET sections
displaced host essentials from page one. Repair shortens duplicated enforcement prose without
dropping duties, recognizes the actual PKQ003 MSBuild error, checks full text through the detailed
route, and puts existing host/EF essentials before the added .NET source sections. Other checks,
including the real OpenAPI export/client, passed without timeouts or overruns in that run.

The development-candidate analyzer qualification script gains the same disabled-style flag in its
existing matrix; its broad candidate/suppression qualification is not needed to establish this
released-package flag repair. The maintained emitted-source regression exercises the actual updated
props/targets and rejection using selected released 0.3.7 bytes; no new candidate/profile is promoted.

SDK configuration references checked for this follow-up:
[IDE2001](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/ide2001) and
[build-level naming severity](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/naming-rules).

Final source verification: Integrity passed in 6.915 seconds
(`20261027T182856Z-1c1f95a5`). All 31 executed Affected checks passed in 173.574 seconds
(`20261027T182911Z-a7f67330`), with no coverage gaps, overruns, timeouts or source changes during
execution. The runner correctly retains `needs-attention` for the two explicitly deferred manual
scenarios discussed above; it is not an unqualified green Affected-suite result. The focused native
source-category controls also passed independently, including next-line unbraced and standalone-call
positives, every category mutation, disabled-style rejection and restored positive. The original
failing runs remain retained. These are Windows local results, not Linux, publication or consumer
acceptance evidence.

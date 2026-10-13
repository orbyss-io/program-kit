# DS01 implementation diagnostics and proposed repairs

These findings extend items1–15 in [the scaffold and contract diagnostics](diagnostics-repair-batch.json) as items16–28. They separate generator/default defects, consumer mistakes, implementation-review gaps and verified Foundation integration gaps. The latter concern native interceptor admission, a browser logout destination covering both success and failure, and initial provider-failure routing through the existing authentication writer; application outcomes and schema policy remain consumer-owned.

This document retains the initial source investigation. Q5–Q8 subsequently settled its upstream repair scope; the [implementation coverage record](ds01-implementation-coverage-2026-10-14.md) carries current execution and qualification status. Real-consumer correction remains separate. Consumer source was inspected at `C:/Users/tech_/Code/Orbyss/temp-tests/claim_evaluator`; Program Kit source was inspected at commit `4b776437033327d3090e3420a5a5b739fa7abd1b`.

## Contract baseline and preservation

The consumer's retained accepted profile selects Foundation **0.3.3**, Foundation Build **0.3.1**, and its existing exact dependency locks. The inspected Foundation capture binds source commit `0739892610a12f36673941dbe9718f45a38ae6cb`. Its knowledge directory is:

`.specify/extensions/program-kit-building-blocks/references/dependency-profiles/candidates/foundation-0.3.3-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2/knowledge/`

The complete `source.pack` hash and the inspected segments were checked against `index.json`. PostgreSQL owns native provider classification, tracked context units and bounded provider work; its contract explicitly excludes application schema, transaction contents, retry policy and domain outcome mapping. Execution supplies replaceable time, monotonic deadlines, caller cancellation and bounded stages. It does not infer rollback or commit certainty.

All repairs must preserve exact pins, package and ShellFeature identities, capability owners, Accepted history, migration bytes, task identities, compatibility baselines and meaningful tests. Existing consumer files require scoped reconciliation; a changed template alone cannot repair them. Changes to public contracts require the existing compatibility process, without resetting baselines to conceal changes.

## 16 Runtime projects generated as HTTP features

**Classification and root cause.** Confirmed Program Kit generator defect. `foundation_composition.py:398–430` interprets every `implementation` as HTTP, emits `ApiFeature : IWebShellFeature`, adds authentication/WebDefaults dependencies and the ASP.NET framework, and distributes selected shell web packages to that implementation. `composition_model.py:178,438` retains role but loses the runtime versus HTTP distinction; `composition_render.py:393–433` repeats the assumption and invents an HTTP responsibility.

The accepted consumer architecture already distinguishes PolicyPortfolio's `runtime` responsibility (`eng/architecture.json:54`) from PolicyPortfolio.Api's `http` responsibility (`:155`). Both legitimately have role `implementation`. PolicyPortfolio's generated `ApiFeature.cs` registers lifecycle capabilities and maps no endpoints. ClaimAssessment has the same erroneous seam. The consumer retained a generated design mistake; it did not supply evidence that runtime requires HTTP.

**Proposed generator repair.** Project accepted responsibilities and consumed capabilities into scaffolding. Keep the existing `implementation` role; do not infer HTTP from role or a filename suffix. Generate an appropriately named runtime `IShellFeature` and HTTP `IWebShellFeature` in their respective owners. Diagnose conflicting or absent responsibility authority before writes. Preserve the existing ShellFeature strings, package identity, owner, shell membership and capability bindings when changing CLR names. Select packages, framework references and activation dependencies from actual consumed capabilities, preserving native selected Tasks and other legitimate activations. Reconcile only demonstrably obsolete scaffold contributions in existing projects.

**Focused regressions.** Generate mixed runtime, HTTP and provider owners; verify descriptors, unchanged identities, actual shell activation, capability resolution and lifetimes, HTTP endpoint mapping and appropriate OpenAPI participation. Prove runtime receives no incidental web/authentication contribution, while legitimate selected runtime dependencies remain. Cover ambiguous responsibility rejection and preservation of customized source, native pins and locks. Current `SelectedFeatureTests.cs:17–19` asserts both feature interfaces and therefore endorses the defect; `validate_composition_activation.py:56–71` covers only an API fixture.

**Foundation gap.** None. The selected CShells contracts already distinguish `IShellFeature` and `IWebShellFeature`.

## 17 Production commit forwarding seam used for test faults

**Classification and root cause.** Consumer implementation mistake plus missing test-integration guidance; no demonstrated generator cause. `PolicyTransactionCommit` only forwards native `CommitAsync`. Its virtual method exists for a test subclass that commits and then throws. The regression addresses a real application invariant, but the production type adds no transaction policy, lifecycle or application responsibility.

**Verified native contracts.** Installed EF Core Relational **10.0.12** documents `TransactionCommittedAsync` after native `DbTransaction.CommitAsync`. However, Foundation 0.3.3's `OwnedPostgreSqlDbContextFactory.cs:22–28` creates the options and installs its own interceptors; `FoundationPostgreSqlDbContext.cs:27,33` requires the exact admitted options object and seals `OnConfiguring`. Its public registration has no interceptor/options customization argument. Adding an interceptor in a reconstructed context-options object would violate the captured Foundation contract.

A possible test-only alternative uses EF's public DiagnosticListener subscription. In the pinned EF source, `RelationalTransaction.CommitAsync` awaits native commit, emits the committed event, and rethrows a diagnostic observer fault. `RelationalLoggerExtensions.TransactionCommittedAsync` dispatches `TransactionEndEventData`; runtime `DiagnosticListener.Write` invokes observers synchronously. The public diagnostic subscription is documented, but throwing from an observer is an implementation-dependent fault-injection technique, not a documented interception contract. A real PostgreSQL proof must establish suitability before replacing the regression. [Microsoft's interceptor documentation](https://learn.microsoft.com/en-us/ef/core/logging-events-diagnostics/interceptors) distinguishes interception from observation; [diagnostic listeners](https://learn.microsoft.com/en-us/ef/core/logging-events-diagnostics/diagnostic-listeners) observe contexts across the process.

**Proposed consumer and guidance repair.** Call native transaction commit directly after qualifying its replacement regression. Following the requester's direction, prefer an additive Foundation contribution of context-specific native interceptors, preserving existing factory guarantees. Keep fault injection entirely in tests. The diagnostic route is an investigated fallback that would require an isolated process, narrowly matched transaction, one-shot fault and disposed subscriptions before replay. Do not create another production commit facade or rebuild Foundation options behind its back.

**Focused regressions.** Observe actual commit, throw once afterward, require the public operation to return uncertainty, and independently query PostgreSQL through a different connection for the durable effect and receipt. Discover the receipt through the production capability, replay the same input, and prove one effect. Preserve changed-input conflict, precommit rollback/cancellation, concurrent replay and postdispatch uncertainty. A postcommit interceptor simulates loss of acknowledgement to application code; it does not by itself prove a network-level failure. A mocked successful commit is inadequate.

**Foundation gap.** Native per-context interceptor admission is a verified integration capability gap selected for upstream repair. No missing business transaction capability is established.

**Updated requester direction.** The requester prefers repairing native interceptor admission in Foundation. The proposed preferred path is now an additive context-specific contribution of native EF interceptors, preserving the factory's provider/options/mandatory-interceptor/lease guarantees. The diagnostic observer remains a researched alternative, not the proposed default. This is a Foundation integration capability gap, not a reason to move consumer transaction policy upstream. The concrete [Foundation handoff](ds01-foundation-repair-handoff-2026-10-13.md) is being investigated in the existing Foundation task; implementation and a new release remain pending the combined design discussion.

## 18 Application outcome ownership and result invariants

**Classification and root cause.** Consumer contract design weakness and insufficient semantic review; no confirmed generator defect. Reusable status names alone do not make `PolicyOutcome` wrongly owned. Its comments describe application decisions, including bound-input conflict, admission expiry and postdispatch uncertainty. Foundation intentionally leaves those decisions to the consumer.

The confirmed defect is unrestricted `PolicyResult<T>` construction: completed results may lack a value, failures may carry arbitrary values, and replay/field flags may accompany irrelevant outcomes. The public positional record also permits invalid `with` changes. HTTP handlers rely on `Value!`. More subtly, the accepted-admission/no-receipt branch in `PolicyRecords.cs:59` returns a newly generated candidate receipt, although its random policy ID and completion time are not a discovered durable receipt.

**Proposed consumer and guidance repair.** Define the operation decision table before selecting types. Identify which operations require a completed payload, which failures carry field identity, and which metadata is known during uncertainty. Use restricted construction with validated factories where a cohesive common shape holds. Use distinct cases where unresolved operation metadata differs from a durable receipt. Preserve stable operation/admission identity without asserting an unobserved effect or completion time. Retain application ownership; use `PostgreSqlFailureInfo` only for provider facts relevant to an owned decision and Execution for actual expiry/cancellation facts. Do not introduce a Foundation PolicyOutcome enum or classify every exception unnecessarily.

**Focused regressions.** Prevent publicly constructible invalid combinations, including record mutation; require payloads on successful operations; preserve failure rather than returning successful empty data. Test stable unresolved-operation identity, receipt discovery, one-effect replay and the missing-receipt latch. Verify safe constraint classification without provider messages. Distinguish expiry and caller cancellation before dispatch; neither proves rollback after dispatch.

**Foundation gap.** None. Generic domain outcome mapping would cross the documented ownership boundary.

## 19 Repeated storage identities and policy literals

**Classification and root cause.** Consumer ownership/consistency problem plus guidance gap; no demonstrated generator defect. The schema name, current revision and policy durations are repeated across mapping, raw SQL, startup admission, deployment and tests. Repetition is not automatically a defect: historical migration identities must remain frozen, and independent deployment assertions must not simply copy the implementation's answer.

**Proposed consumer and guidance repair.** Group current schema/table/revision identifiers under cohesive persistence-owner metadata, or derive current table/schema identifiers from supported EF mapping metadata. Use provider-supported identifier delimiting for raw locking SQL and parameterize all data values, including revision predicates. Define admission/replay/retention limits with their application owner, then apply them consistently at boundaries. Keep protocol constraints fixed and make only genuinely operational choices configurable. Preserve original migration and deployment history bytes; a historical migration must never consult today's mutable constants. A deployment artifact may embed a frozen literal, with a consistency test against current runtime admission.

Concrete classifications include the schema and required `20261013_ds01_metadata` revision as persistence identities; 120-character normalized labels, lowercase SHA-256 representation and `CreatePolicy:v1` digest framing as application/protocol constraints; 24-hour admission and 30-day replay retention as application semantics unless the accepted contract allows configuration; and native connection/command/lock budgets as typed operational policy. Tests already copy the production deployment SQL rather than maintaining a separate deployment script. Preserve that useful arrangement and the existing `Migrations/**/*.cs` project exclusion pending its own product review.

The current feature plan (`specs/002-policy-backed-veterinary/plan.md:123`) explicitly specifies 24-hour action admission and thirty-day completed non-content receipts. These are settled consumer semantics for this repair, not newly configurable settings. It also specifies accepted-action reconciliation ahead of expired unaccepted-admission rejection; the lock-boundary repair must preserve that distinction.

The specification's FR-018 (`spec.md:206`) and plan (`plan.md:37`) also cap the complete metadata operation at ten seconds. Operational provider/stage configuration may enforce tighter limits within that cap; moving a literal into settings must not silently permit a longer end-to-end budget.

**Focused regressions.** Compare actual EF mappings, current deployment SQL, migration history and startup revision admission. Exercise exact revision success and missing/wrong revision rejection, role grants and real locking SQL. Verify correctly quoted identifiers and parameterized data. Cover validation/storage bounds and expiry/retention boundaries. Independent database assertions must still detect an incorrect mapping or deployment; do not make every test reuse the same constants.

**Foundation gap.** None. Application storage identities and schema history are explicitly consumer-owned; EF/provider metadata supplies the required native mechanisms.

## 20 Clock ownership and stale expiry after database waits

**Classification and root cause.** Confirmed consumer integration mistakes and missing guidance. The stale decision ordering is source-confirmed; expiry crossed during a lock wait has not yet been demonstrated by a failing regression.

Runtime `ApiFeature.cs:17` registers `TimeProvider.System` unconditionally, allowing an earlier supplied clock to lose ordinary single-service resolution. `PolicyLifecycle` reads time before entering persistence. `PolicyRecords.cs:47–60` awaits `FOR UPDATE` and receipt lookup, then evaluates expiry with that old snapshot. It also uses stale time for replay retention and durable timestamps. `PolicyEndpoints.cs:28–38` uses direct UTC time and a native timeout; POST handlers add duplicate linked timeouts. Those nested timeouts do not extend the outer budget, but duplicate ownership and bypass Foundation's clock/deadline factory. Provider units create fresh deadlines because callers pass only a token, while unit-local expiry can be mapped to Unavailable.

**Existing Foundation mechanisms.** Execution registers defaults with `TryAddSingleton`, uses injected TimeProvider timestamps/timers, exposes `IsExpired` independently of caller cancellation, and provides capped stages. PostgreSQL's `BeginUnitAsync` accepts an existing outer execution deadline. No new clock interface is needed.

**Proposed consumer and guidance repair.** Consume the selected replaceable clock. Inject it into the persistence owner making decisions after waits; retain explicit instants only for meaningful pure policy inputs or caller-selected time. Preserve owned admission/digest/receipt/accepted-latch ordering, then read fresh time immediately before admission-expiry validation. An expired admission must not invalidate an already accepted legitimate replay. Freshen retention decisions at their actual boundary. Preserve UTC millisecond normalization for durable timestamps and response/replay equality.

Create one Foundation deadline for the complete operation and pass it into provider stages; do not restart the budget at each layer. Choose the smallest appropriate existing capability signature/context change through normal compatibility review. Keep wall-clock deadline metadata distinct from monotonic enforcement. Specify caller-cancellation/expiry race precedence; postdispatch failures remain uncertain regardless of cancellation source.

**Focused regressions.** Register a controlled clock before actual production feature activation and resolve the public capability. Hold the admission lock with an independent PostgreSQL transaction, prove creation is waiting, advance UTC across expiry, release, and assert no acceptance/effect/receipt. Cover before/exact/after expiry, previously accepted replay, retention crossed while waiting and timestamp precision. Use a controlled clock with timestamps and timers to test outer-budget propagation, capped stages, UTC adjustments, caller cancellation, expiry and postdispatch uncertainty. Existing tests manually construct lifecycle/records and their MutablePolicyClock changes only UTC; they cannot prove actual DI replacement or deterministic monotonic deadlines.

**Foundation gap.** None.

## 21 Friend assemblies and tests of implementation internals

**Classification and root cause.** Consumer violation of existing guidance, plus missing enforcement and semantic review coverage. `extensions/program-kit-dotnet/references/technology-profiles/dotnet.md:110–114` already prohibits friend access. `PolicyPortfolio.Persistence/AssemblyInfo.cs` nevertheless grants it to PortfolioAssessment.Tests and ClaimEvaluator.ActivationTests. Tests construct internal records/commit types and inspect internal storage. This bypasses registration and contributed to missing the clock override and unnecessary forwarding seam.

**Proposed consumer and guidance repair.** Resolve production capability ports through actual feature registration and appropriate shell lifecycle. Keep implementation classes, EF entities and DbSets internal. Use independent Npgsql assertions for owned database state and isolation. Keep native fault injection in test code, subject to item 17's integration qualification. Remove friend declarations only after replacing their meaningful coverage. Do not compensate with public implementation types, a new test facade, reflective internal construction or interfaces with no production consumer.

**Focused regressions.** Preserve provider activation/admission, owner isolation, concurrent replay, rollback, bounded cancellation, uncertainty, independent receipt discovery and one effect. Test source-level absence of the unwanted friend access and public entity leakage alongside real behavior. Include registration/lifetime assertions, schema deployment/admission and the controlled clock. Maintain independent database assertions; testing only mocks of capability ports would lose the relevant guarantees.

The inspected test files contain eight creation Facts, four metadata Facts and two selected-feature Facts. These are 14 source cases to preserve or replace with equivalent coverage, not new executed results. A maintained architecture check can enforce the existing friend-access rule against source declarations, SDK project items and compiled friend attributes; checking only `AssemblyInfo.cs` would miss alternate declaration routes.

**Foundation gap.** No business capability gap. The interceptor registration limitation described in item 17 affects one preferred testing technique and must not justify exposing consumer internals.

## 22 Catalog page limits hardcoded instead of configured

**Classification and root cause.** Confirmed consumer implementation mismatch with existing configuration guidance, plus missed semantic review. `PolicyLifecycle.cs:36`, `PolicyRecords.cs:87` and `PolicyMetadataQuery.cs:12` each impose `1..50`; `PolicyEndpoints.cs:108` supplies omitted default `20`. There is no typed catalog-options owner. The specification promises paged opaque cursors without selecting those values. The actual catalog OpenAPI exposes the parameter but omits minimum/maximum/default. The shared wire schema's `maxItems:50` applies to different service collections, not catalog pages.

The applicable rule already exists in `modularity-and-contracts.md:251–254`: deployment limits belong to typed validated options. `dotnet-engineering.md:109–110` requires validation at actual activation, with defined snapshot/reload semantics. The failing implementation repeated an operational limit as policy in several owners instead of tracing a configured value through admission and query construction. The source establishes that mismatch; it does not reveal the implementation agent's private reasoning.

**Proposed consumer and guidance repair.** Keep page size positive as the algorithm's valid-input requirement. Make catalog default/maximum consumer-owned typed configuration, initially retaining `20` and `50` as defaults. Validate positivity, default no greater than maximum, and safe lookahead arithmetic at actual shell activation. Use one coherent policy for omitted API input, application admission and bounded provider queries, with a stable snapshot during each operation. Do not invent a fixed hard ceiling of fifty without an accepted resource/protocol constraint. Keep request-overmaximum behavior explicit rather than silently truncating. Surface configuration in source-backed settings/handoff and document effective bounds through the existing contract process. Foundation needs no catalog-settings abstraction.

**Focused regressions.** Activate real production registration with a non-default maximum/default, such as maximum 100/default 25, and prove all affected paths use them. Cover omitted size, one, exact maximum, maximum plus one, zero/negative input, invalid options at activation, bounded lookahead, stable opaque-cursor traversal and owner isolation. Review generated query metadata without silently resetting compatibility baselines. Independent catalog tests must not all read the same implementation constant.

**Foundation gap.** None. This is consumer operational configuration supported by existing options mechanisms.

## 23 Interactive login timeout consumes human entry time

**Classification and root cause.** Confirmed Foundation and Program Kit default/semantic guidance defect. Captured `FoundationWebOptions.cs:64` defaults remote authentication to ten seconds; `FoundationBffCookieFeature.cs:188` maps it to ASP.NET's complete `RemoteAuthenticationTimeout`. Backchannel timeout is separately mapped from discovery's three seconds (`:189`). [ASP.NET documents the complete-flow timeout and its fifteen-minute default](https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.authentication.remoteauthenticationoptions.remoteauthenticationtimeout?view=aspnetcore-10.0); pinned v10.0.12 source also sets correlation-cookie expiry from it. Human credential entry, MFA and consent consume this window.

Program Kit's `web-security-evidence.json` WEB-D03 incorrectly describes the ten seconds as bounding only server-controlled work. Raw profile settings contain ten; typed generation consumes captured publisher defaults unless overridden, so changing only a legacy JSON template cannot fix the active generated path.

The requester supplied a prepared-host reproduction: fresh immediate login reached `/policies` with an authenticated session; fresh login after a fifteen-second pause reached callback-invalid with an anonymous session. This reproduction was not rerun here. Its behavior matches the timeout semantics, but exact correlation-expiry causation requires callback/cookie evidence rather than URL inference.

**Proposed reusable and consumer repair.** Select a finite human-facing login window separately from discovery/backchannel limits. Fifteen minutes is a concrete framework baseline for the grilling. Fix Foundation's default/metadata and Program Kit's policy rationale, typed generation and applicable legacy profiles together. Preserve intentional consumer choices; reconcile accidental inherited defaults through normal ownership-aware adoption. The consumer can select an appropriate value through existing configuration before a new Foundation release. Keep state, nonce, correlation, PKCE, cookie safeguards and session lifetimes intact.

**Focused regressions.** Fresh login succeeds after a real pause exceeding fifteen seconds but within the configured window. Test actual expired-flow rejection and explicit fresh retry, MFA/consent where selected, actual named-options/correlation-cookie expiry and a network outage still bounded by its separate budget. Automated immediate submission cannot substitute for human-paced evidence. Preserve forged/replayed/missing state and correlation rejection.

**Foundation gap.** No missing timeout mechanism. The existing default and its description need correction upstream.

## 24 Browser authentication errors receive machine JSON

**Classification and root cause.** Consumer presentation mistake and reusable guidance/scaffold gap; no missing Foundation mechanism. `DefaultAuthenticationErrorWriter` writes bounded problem JSON, but the public `IAuthenticationErrorWriter` already permits consumer representation and its default is registered with `TryAddSingleton`. BFF normalizes failure codes before using the writer on access-denied; API challenges can use the same writer. Keycloak theme changes cannot render a response generated by the application host.

**Proposed consumer and guidance repair.** Register a small application-owned writer for actual interactive browser routes, rendering accessible branded HTML and a safe explicit restart-sign-in action. Preserve status codes and machine/API problem bodies. Select representation using route purpose and appropriate request signals; a generic Accept wildcard must not turn API problems into HTML. Use allowlisted failure codes and fixed safe copy, HTML encoding and a validated local retry target. Retain final security/no-store/no-index headers in the shell pipeline. Do not show raw provider messages, state, tokens or private identity details.

A callback-invalid page means a particular login attempt failed; it does not prove that every existing session is absent or expired. Correlate `/bff/user`, actual protected access and challenge timing in the same browser context. A subsequent successful `/policies` load may involve an existing session or another login attempt. Wording and available actions must match the observed state, preserving any independently valid session.

**Focused regressions.** Safe, branded keyboard-accessible failure page; explicit successful retry; anonymous and already-authenticated callback-failure contexts; distinct provider-unavailable/authorization-denied wording; API problem compatibility; malicious code/return target rejection; no secret reflection; correct privacy/security headers. Test actual navigation, not only direct HTTP status.

**Foundation gap.** None identified. Reuse `IAuthenticationErrorWriter`; do not invent a second general error interface.

**Foundation follow-up qualification.** The upstream proposal found a narrower coverage gap before callbacks: `/bff/login` issues a native Challenge, and initial provider metadata retrieval can throw before callback `OnRemoteFailure`. The selected generic exception writer may then return 500 JSON without using `IAuthenticationErrorWriter`. The callback/access-denied seam remains sufficient; initial challenge failure needs separate narrow upstream handling of expected provider unavailability through that same seam. The requester accepted including this repair, a usable browser explanation/retry and safe machine availability response. Preserve request cancellation and unexpected programming-error handling; broadly catching InvalidOperationException would conceal other defects.

## 25 Browser logout lands on the signed-out JSON protocol route

**Classification and root cause.** Consumer journey mistake, reusable defaults/guidance gap and a narrow verified Foundation destination gap. Foundation intentionally maps `/bff/signed-out` to `BffSignedOutResponse` JSON (`FoundationBffCookieFeature.cs:108–109`). The product's `app.ts:100–103` submits logout in its own top-level window, following the provider back to that JSON route. It does not use the installed Program Kit logout helper or provide a public signed-out landing.

Foundation passes `/bff/signed-out` explicitly as logout RedirectUri (`:273`) and hardcodes the same path for initiation failure (`:280`), after clearing the local session. Native `SignedOutRedirectUri` alone cannot override the nonempty explicit property. Supported OIDC events can change the successful destination, but metadata retrieval can fail before those events, leaving the hardcoded fallback. Both literals omit shell PathBase, unlike login-failure routing. That is a source-confirmed non-root-shell risk requiring a regression.

Program Kit's browser helper already accepts a local `signedOutPath`, so a consumer-owned application-window landing is supported today. That does not provide one server-owned setting covering successful callback and failed initiation. These are distinct customization scopes.

**Proposed Foundation repair.** Add a validated local browser landing destination used consistently in success and fallback, retaining the old JSON destination by default for compatibility. Preserve shell PathBase, reject external/ambiguous/conflicting paths and keep local session termination before provider work. Leave page branding/content with the application owner. Keep `/bff/signed-out` machine-readable; do not shadow the route or globally replace its JSON.

**Proposed consumer and Program Kit repair.** Provide an accessible public application landing with a sign-in action and truthful provider-completion status. Use the supported native antiforgery/logout adapter and explicit application landing. Clear private state and cancel late work. Remote provider failure must not displace the application page or restore local access. Public landing content must not depend on authenticated private bootstrap.

**Focused regressions.** Click the actual product logout button, follow normal and failed provider flows, and assert a useful branded landing/focus/sign-in action. Independently confirm local session absence and protected access denial, retain JSON machine contract checks, test non-root shell success/fallback and invalid targets, and preserve antiforgery rejection, separate tabs, back navigation and late-response privacy coverage. State local success separately from unconfirmed provider sign-out.

**Foundation gap.** A unified validated browser destination covering both successful logout and initiation failure is absent. Existing OIDC events and the client helper cover portions of the journey, so logout is not wholly uncustomizable. A small option is preferable to another broad interface.

## 26 Browser tests accept protocol acknowledgement as the complete journey

**Classification and root cause.** Reusable test-scope defect and consumer acceptance gap. Consumer `eng/web/tests/authentication.spec.ts:99–100,248–249` and the maintained common browser template expect signed-out JSON. Those assertions match the captured Foundation machine contract and should remain as protocol checks. The defect is treating that terminal JSON response as successful browser experience.

The common test manually navigates to an acknowledgement URL after checking logout. It uses a handwritten form rather than the shipped logout adapter. Product `ds01-entry.spec.ts:108–122` posts logout via the request client, checks a redirect and eventual anonymous state, but never follows the real button/provider/browser landing. Immediate credential entry also hides the interactive timeout defect.

**Proposed reusable and consumer repair.** Keep wire/security tests separately named and add complete browser-journey acceptance. Exercise the actual adapter and product controls, not a manually constructed substitute that omits navigation. Carry readable text, branding, keyboard/focus behavior, explicit recovery and privacy through login errors, expiry, sign-out and provider failure. A passing protocol test must report its scope without claiming complete UX.

**Focused regressions.** Human-paced fresh login; expired-login recovery; branded error/sign-out pages; keyboard and pointer logout; focus and visible recovery; local logout surviving provider failure; no restored private DOM; machine status compatibility. Use local Chromium/WebKit and retain Firefox in CI under the known host limitation. These browser cases were not rerun during this source investigation.

**Foundation gap.** None beyond item 25. This is a test/acceptance problem.

## 27 Logout helper does not bound each fetch or distinguish acknowledgement uncertainty

**Classification and root cause.** Additional confirmed reusable Program Kit adapter defect discovered while researching the requested logout cases. The BFF helper's nominal five-second local-termination deadline is checked only between session fetches. Its session fetch (`bff-session.ts:30`) and antiforgery fetch (`:56–59`) have no abort bound; a hanging fetch can exceed the claimed bound. After form submission, its catch closes the provider window and rethrows just as it does for pre-submit failure, although local deletion may already have succeeded.

The existing unit assertion that failed logout must not navigate covers malformed antiforgery before dispatch. That is valid for its case, but cannot establish what happened after a dispatched logout. The common browser test bypasses the helper, so it misses these branches.

**Proposed reusable repair.** Bound application-controlled fetches within one remaining operation budget, using monotonic browser elapsed time and cancellation. Distinguish rejection before dispatch from unknown acknowledgement afterward. Keep private content cleared after dispatch; do not restore authenticated UI merely because session polling failed. Offer a public status/recovery view when termination cannot yet be confirmed, and render the signed-out claim only after actual evidence. Keep provider navigation and local-session evidence separate.

**Focused regressions.** Hanging antiforgery fetch, hanging/malformed session response, cancellation/timeout after submission, actual local deletion with lost observation, unaffected normal logout, popup refusal and provider navigation failure. Exercise the shipped helper in a real browser, plus focused unit tests for dispatch/acknowledgement sequencing and bounded fetch cancellation.

**Foundation gap.** None for bounding client requests or truthful uncertainty; this adapter belongs to Program Kit. Foundation's complete browser-destination gap remains item 25.

## 28 Name validation loses input and diverges across runtimes

The [validation-parity investigation](ds01-validation-parity-research-2026-10-13.md) separates the reported maxlength UI data-loss defect, current code state and the missing normalization-aware export/generation path. Current consumer inputs no longer set maxlength, but Core, API/schema and browser constraints are not supplied by one executable rule path. No particular Program Kit scaffold is shown to generate the original mistake.

Fresh synthetic real-clipboard evidence reproduced truncation of a valid space +120-letter+space input to119 normalized letters under maxlength120. .NET and JS trim sets differ, affecting admission and digest content. Ordinary schema length counts code points, while current Core/browser count UTF-16 units. Existing Forms schema validation cannot silently substitute those semantics.

The accepted narrow capability exports a consumer-owned rule descriptor from actual Core and generates matching browser normalization, validation and field metadata. Preserve raw correction input, keep server admission authoritative, and require executable parity/staleness checks plus direct invalid-API no-effect and real-paste zero-request regressions. Q6–Q8 settled Core authority, rejection of raw controls before trimming, and preserved UTF-16 counting. The supported generator and disposable compiled/browser parity fixtures are implemented; real-consumer correction remains separate. See the implementation coverage record for current evidence and limits.

## Semantic implementation review proposal

Existing guidance already requires source review and explicitly separates graph success from semantic acceptance. The `implementation-quality` rule in `phase-obligations.json` has behavior-and-review enforcement, with routing coverage but no application semantic tests. Strengthen that existing projection, `programming-guardrails.md`, `dotnet-engineering.md`, `modularity-and-contracts.md`, applicable phase guidance and the existing implementation/architecture commands with concrete, conditional evidence requests:

1. For each changed production abstraction, identify its application invariant, policy, lifecycle or actual replacement responsibility. A test substitution alone does not justify it.
2. Compare generated feature contracts and dependencies with actual responsibilities and consumed capabilities.
3. Identify the owner of each operation decision and prove required payload/replay invariants.
4. Locate the final time read after asynchronous waits and the complete deadline's creation, propagation and disposal.
5. Distinguish known precommit failure from postdispatch uncertainty and show independent database evidence for recovery.
6. Classify repeated literals by current owner identity, immutable history, protocol constraint or operational setting; verify consistency without making tests tautological.
7. Exercise production registration through public capabilities and explain supported test injection without friend access.
8. Trace operational limits through actual activated options, omitted request defaults, admission, query execution and exported settings/contracts. A repeated constant is not evidence of configuration ownership.
9. Separate human interaction windows, app-controlled network deadlines and session lifetimes; prove browser recovery and actual session state independently of URLs or machine acknowledgement bodies.

Record source locations, dispositions and relevant tests in existing tasks and normal delivery review. Add maintained focused fixtures for reusable mechanisms, while application outcomes and consumer database regressions remain in the consumer. Do not add a separate approval ledger, a universal result framework, blanket lint rules or full acceptance runs to ordinary edit loops.

## Grilling status and next decisions

The first questions were too abstract for the requester to assess. They did not establish agreement on result shape, deadline semantics or review enforcement. The requester has since selected the direction of repairing native interceptor admission in Foundation and identified catalog maximum/default sizes as configuration. Those preferences remain settled inputs; exact API and compatibility design must follow source-backed review rather than requiring the requester to choose C# mechanisms.

The requester answered yes to all three subsequent browser decisions: a configurable fifteen-minute interaction window with separately short network budgets; preserving an independently valid session and offering Continue plus fresh sign-in after a failed new attempt; and truthful application-versus-provider sign-out wording with an explicit sign-in action. Those choices are now settled.

The parallel Foundation proposal confirmed additive scoped native interceptor admission and a validated shell-relative logout destination can preserve existing contracts. The requester also accepted handling expected initial provider discovery failure through the existing authentication writer, completing the browser error-recovery scope. Q5 authorized the combined [shared understanding](ds01-upstream-repair-plan-2026-10-13.md) and parallel upstream implementation. Subsequent instructions authorized Program Kit patch publication after Foundation publication and the required gates.

Initial research verification consisted of source/capture inspection and pinned EF contract/source review. Item28 subsequently added separately preserved synthetic browser/framework/schema evidence. Foundation owns publisher postcommit instrumentation qualification; real-consumer receipt/replay and lock-wait regressions remain required during separate consumer correction. Q5-approved upstream implementation is in progress, with Q6–Q8 accepted. Real-consumer source, selected pins, migration bytes and historical evidence remain unchanged.

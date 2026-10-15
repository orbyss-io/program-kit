# DS01 upstream repair plan and shared understanding

## Purpose and authority

Repair the reusable causes of the DS01 findings, make implementation review concrete, and give the consumer a separate correction path. The [research addendum](ds01-implementation-diagnostics-research-2026-10-13.md) contains source evidence, classifications and regression requirements for items16–28 alongside the original fifteen diagnostics. The requester confirmed Q5 and authorized the agreed Foundation and Program Kit upstream implementation in parallel. Later diagnostic28 joined that scope through the accepted Q6–Q8 decisions.

The requester has accepted native interceptor admission in Foundation, configurable catalog default/maximum sizes, a configurable fifteen-minute login window, preservation of independently valid sessions on a failed login attempt, truthful application-versus-provider sign-out messages, and recovery for expected provider failure when sign-in first starts.

No real-consumer product edits are authorized. The requester subsequently explicitly requested a new Program Kit patch publication after the qualified Foundation release and implementation of the agreed fixes. Source compatibility, qualification and exact profile/knowledge adoption retain their existing processes. Do not add an approval ledger, runtime abstraction framework or another startup route.

## Foundation work

The existing Foundation task owns runtime changes and publisher qualification; it must remain independent of Program Kit. Its verified baseline is released 0.3.3 at `0739892610a12f36673941dbe9718f45a38ae6cb`, with EF Core 10.0.12 and Npgsql/provider 10.0.3. The [Foundation handoff](ds01-foundation-repair-handoff-2026-10-13.md) specifies the narrow repair boundaries.

1. Add context-specific native EF interceptor contributions. Preserve existing registration signatures and exact options admission; resolve contributions in the tracked unit scope. Retain provider selection, mandatory interceptors, redaction, bounded work, datasource holds and drain. Use native EF types and explicit DI lifetime/disposal ownership. Do not expose arbitrary options/provider replacement or invent a commit service.
2. Change the omitted interactive-login default to 900 seconds and correct its description and settings metadata. Keep discovery/backchannel work separately short and bounded; preserve intentional overrides, state, nonce, correlation, PKCE, cookie safeguards and session lifetimes.
3. Add one validated shell-relative logout landing destination for both normal completion and provider-initiation failure. Preserve the existing JSON route by default and its machine contract. Expand shell PathBase correctly. Reject unsafe/conflicting destinations; local cookie/ticket deletion precedes provider navigation.
4. Route expected initial sign-in provider-unavailability failures through the existing authentication writer. Retain request cancellation and unexpected-error behavior. Classify demonstrated native failure provenance instead of broadly catching InvalidOperationException. Reuse the public error-writer seam; application branding remains application-owned.

Foundation evidence must include a real postcommit native interceptor fault, independently observed durable state, correct scoped contribution lifetime/isolation and actual drain; delayed fresh login, expiry/restart and separately bounded network failure; root/non-root custom logout success/fallback; and expected initial provider failure with machine/browser writer behavior. Preserve current contract/security/cancellation tests. These changes must not claim consumer receipt/replay acceptance from publisher tests alone.

## Program Kit work

1. Carry accepted runtime versus HTTP responsibilities and actual capability consumption through the composition model, renderer and scaffold. Generate IShellFeature for ordinary runtime and IWebShellFeature for HTTP owners. Preserve ShellFeature/package/owner identities and legitimate selected dependencies. Diagnose missing/conflicting responsibility authority and reconcile existing customized projects without destructive template replacement.
2. Correct interactive-timeout generation and policy evidence for both typed and applicable legacy paths. Do not fix only a raw JSON template while the active generator still imports a ten-second publisher default. Preserve purposeful consumer overrides and keep network budgets distinct.
3. Provide maintained browser-presentation guidance and a small reusable example using IAuthenticationErrorWriter. Render browser failures and public signed-out/recovery views through application-owned presentation; preserve API problem and BFF JSON status contracts. Carry existing consumer branding and public/private content admission. Avoid application UI in Foundation.Host and route shadowing.
4. Repair the BFF logout adapter so every app-controlled fetch respects a single remaining elapsed-time budget. Separate failure before dispatch from unknown acknowledgement afterward; keep private state cleared after dispatch. Do not infer local or provider session state from the landing URL, remote query hints or static JSON acknowledgement.
5. Separate protocol tests from complete browser-journey tests. Exercise the actual shipped adapter and real product controls, human-paced login, readable branded recovery, keyboard/focus behavior and provider failure. Retain wire assertions, antiforgery, no restored private DOM, separate-tab and late-response coverage.
6. Strengthen existing phase guidance, implementation/source review and targeted architecture checks. Trace each production abstraction to a real responsibility, verify result invariants, final clock reads after waits, deadline propagation, uncertainty, literal/configuration ownership and public test boundaries. Enforce the existing friend-access rule against source/project/compiled declarations where supported. Record source locations and dispositions in existing tasks/review output.

Maintain focused mixed-project activation, ownership/reconciliation, options-routing, browser adapter and guidance fixtures. Do not present fixture success or a compiled graph as consumer semantic acceptance.

## Consumer corrections remain separate

The consumer correction instructions must cover the following without applying them to the real consumer during upstream work:

- Reconcile runtime/API CLR names and dependencies while retaining existing feature/package identities and accepted ownership.
- Replace the commit forwarding class with native transaction commit after the selected Foundation interceptor regression is available. Use public production registration and independent PostgreSQL assertions; preserve concurrency, rollback, cancellation, uncertainty, receipt discovery and one-effect replay.
- Make completed results carry their required value. Make uncertain operations carry only established operation metadata rather than a fabricated durable receipt. Use the smallest restricted result shape appropriate to each operation, keep decisions consumer-owned and preserve wire semantics through reviewed mapping. Do not add a generic Foundation outcome enum.
- Inject the selected TimeProvider into the effect owner. Read expiry/retention time after database waits at the actual decision boundary. Preserve accepted replay before unaccepted expiry rejection and UTC millisecond timestamp precision. Propagate the selected Foundation outer deadline into bounded provider stages. Caller cancellation before dispatch and uncertainty after dispatch remain distinct.
- Consolidate current persistence identifiers and application constraints by owner, with correctly quoted identifiers and parameterized SQL values. Preserve historical migration bytes and existing deployment/history decisions. Keep the accepted 24-hour admission, 30-day completed receipt retention and ten-second metadata maximum.
- Configure catalog default/maximum through typed owner options, initially 20/50, validated at actual shell activation and consistently consumed by API defaults, admission and bounded query construction. Positive page size is an input invariant. Do not invent a hard ceiling of fifty or change unrelated wire-array constraints.
- Replace friend-access tests with real registration/public capability tests and independent synthetic database setup/assertions. Keep entities, DbSets and implementation types internal; preserve the fourteen inspected cases' meaningful coverage.
- Implement branded public recovery/landing pages through supported mechanisms and the reviewed new logout setting, with current session checks and existing ownership/permission enforcement.

## Agreed browser behavior

People have a configurable fifteen-minute window to complete sign-in, including credentials, MFA and consent. Expired attempts fail safely and require a fresh explicit attempt. Short server network waits remain separately bounded.

A failed new login attempt does not delete an independently valid session. When the application verifies that session, offer Continue to the application and Try signing in again; otherwise offer fresh sign-in. Current permissions still govern access. Provider unavailability while starting sign-in receives a safe explanation and explicit retry, with a bounded availability response for machine callers.

When application sign-out is confirmed but provider sign-out cannot be confirmed, explain that distinction and offer explicit sign-in; a remaining provider session may be reused. When even local acknowledgement is unknown, state that application sign-out is not yet confirmed and offer bounded status/recovery. Never restore private content merely because a response was lost. Branding, accessible text, keyboard/focus behavior and usable recovery are part of journey acceptance.

## Execution and acceptance boundaries

The requester authorizes Program Kit patch publication once Foundation's new version is qualified/published and these fixes pass their required checks. A narrow local exception covers token-access HTTP403 failures for unchanged Forms/Localization versions; preserve and identify those original failed tests rather than calling them passes. Verify unchanged pins and let complete CI cover those tests. The exception covers no other local failure and does not weaken tagged CI or publication gates. The Windows local Release terminal restriction remains unless the requester explicitly overrides it for this task.

Diagnostic28 adds a separate [normalization-aware validation investigation](ds01-validation-parity-research-2026-10-13.md). Q6–Q8 are accepted: export from the server-owned pure rule, generate browser validation, reject raw controls before trimming and preserve UTF-16 counting. Implement the narrow supported path, source-backed metadata/staleness checks and native/browser parity fixtures. Preserve full correction input; keep normalization-aware bounds distinct from transport/schema length. This accepted addition joins the complete implementation scope rather than replacing the Q5 work above.

After shared-understanding confirmation, Foundation and Program Kit may implement their independent repairs in parallel. Program Kit can first repair generator/guidance/adapter defects against the retained baseline. New publisher contract usage must wait for an explicitly selected qualified Foundation release; local archives must not masquerade as public availability.

Use focused regressions and the bounded Development suite during ordinary work. Preserve failed evidence and repair actual defects. Full publication qualification is a later release boundary governed by repository instructions, including the dependency workflow, user-owned local Release restriction unless explicitly overridden, and Firefox acceptance in CI. No paid worker or interactive intake run is included.

Preserve original diagnostic records, selected consumer pins/native locks, feature/package identities, accepted ownership, tasks/delivery history, migration bytes, compatibility baselines and security coverage. Later publisher/profile adoption must update exact package/host/knowledge inputs together through supported reconciliation and rerun affected compatibility/consumer tests. Consumer correction remains separate. Program Kit publication is authorized subject to the release prerequisites stated above.

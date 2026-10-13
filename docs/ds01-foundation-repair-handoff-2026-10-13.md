# Foundation repair scope for DS01

## Current authority

The requester prefers repairing Foundation's native interceptor admission rather than relying on a diagnostic-observer workaround and has confirmed Q5's combined shared understanding. This handoff now authorizes the agreed Foundation implementation and focused qualification in parallel with Program Kit work; it does not authorize a new release or consumer upgrade. Prior publication authority for 0.3.3 must not be reused as approval for these new changes.

Baseline: captured Foundation 0.3.3, source commit `0739892610a12f36673941dbe9718f45a38ae6cb`, selected EF Core 10.0.12. Verify current publisher source and release state before implementing. Preserve existing public contracts and tests, dependency pins and historical evidence. Foundation remains independent of Program Kit and consumer business semantics.

## Native transaction interceptor admission

`AddFoundationPostgreSql` currently accepts a context construction delegate but no interceptor contribution. `OwnedPostgreSqlDbContextFactory` builds the native options and adds its own connection/command interceptors. `FoundationPostgreSqlDbContext` requires the exact admitted options instance and seals `OnConfiguring`.

Propose an additive, backward-compatible way for an owned context registration to contribute native EF interceptors. Prefer existing native types over a new Foundation interception abstraction. Keep Foundation in control of provider selection, exact options admission, mandatory interceptors, redaction, timeouts, tracked leases, datasource holds and drain. Do not expose unrestricted replacement of the options/provider or introduce a transaction commit wrapper. Specify contribution construction, lifetime, ordering, disposal and context/shell isolation; do not promise arbitrary EF interception can never alter behavior.

Qualification must use a real PostgreSQL transaction and a test-only `DbTransactionInterceptor.TransactionCommittedAsync` that throws once after native commit. Independently read durable state through another connection; prove fault propagation, one-shot isolation, normal transactions afterward, context/unit disposal and datasource drain. Preserve deadline/cancellation and failure-redaction tests. Consumer admission, outcome mapping, receipts and replay remain consumer-owned, and their acceptance follows separately through actual production registration.

## Interactive authentication timeout

`FoundationWebOptions.RemoteAuthenticationTimeoutSeconds` defaults to ten seconds and maps to ASP.NET's complete remote authentication flow, including human time at the provider. Discovery/backchannel already have a separate three-second budget. User-supplied consumer reproduction: immediate submission authenticates; waiting fifteen seconds yields callback-invalid and no authenticated session.

The requester accepted a configurable fifteen-minute default, ASP.NET's standard complete-flow window, with a safe explanation and fresh restart action after expiry. Correct settings metadata/docs. Keep discovery/backchannel budgets separately bounded and all state, nonce, correlation, PKCE and return-target validation. Preserve explicit consumer overrides through subsequent adoption. Include actual human-paced fresh login, expired-flow rejection and restart, plus bounded backchannel failure and actual option binding.

## Configurable browser logout landing

Foundation intentionally provides JSON at `/bff/signed-out`. Preserve that typed machine response. Logout currently passes literal `/bff/signed-out` as `AuthenticationProperties.RedirectUri`; its initiation-failure catch redirects to `/bff/signed-out?remote=unavailable`. Setting native `SignedOutRedirectUri` alone cannot replace the explicit property. Native events can change the successful flow, but do not cover metadata failure before the event and the hardcoded fallback.

Propose one validated application-local browser landing destination used consistently for success and initiation failure, preserving the existing destination by default for compatibility. Resolve shell PathBase correctly; reject external, protocol-relative, ambiguous or conflicting targets. Retain local session clearing before provider navigation, antiforgery enforcement and safe failure handling. Keep landing content/branding in the application owner rather than Foundation.Host. Do not shadow Foundation routes or change machine JSON into HTML globally.

Qualification: default compatibility; custom success and failed-provider destinations; non-root shell; invalid target rejection; cleared local session and denied private routes/API after provider failure. Distinguish reaching a landing from actually observing session state. Provider completion and local completion are separate facts.

The requester accepted truthful landing wording when local completion is confirmed but provider completion is unknown: "You're signed out of this application. Sign-out from your identity provider could not be confirmed." Offer explicit sign-in and explain that a remaining provider session may be reused. Unknown local acknowledgement must instead show that application sign-out is not yet confirmed.

## Existing browser error extension

`IAuthenticationErrorWriter` is already public and replaceable. Browser callback/access-denied pages should use it in an application-owned presentation feature, while machine/API requests retain bounded problem responses. No new Foundation browser-error interface is currently justified. Verify the seam against actual named authentication registration and headers; report any concrete limitation rather than assuming one.

The requester accepted preserving an independently valid session after a failed new login attempt. The application may offer Continue to the application and Try signing in again, while enforcing current permissions. An anonymous context offers fresh sign-in without claiming authentication.

## Reviewed Foundation proposal

The existing Foundation task confirmed current remote main `8085d4f` has the same source tree as released `0739892` (0.3.3), with EF Core 10.0.12 and Npgsql/provider 10.0.3. Its proposal preserves both existing PostgreSQL registration signatures and adds overloads accepting an ordered native interceptor contribution callback resolved from the tracked unit's scoped provider. Snapshot contributions, retain mandatory interceptors and exact options, and keep DI disposal with the unit scope. Scoped/transient contributions must not be captured by singleton registration; native singleton interceptors require stable thread-safe instances.

For logout it proposes a validated `LogoutLandingPath`, defaulting to the existing protocol route, expanded with shell PathBase for both successful and failed initiation. Browser branding remains application-owned. Implementation API names remain subject to normal source review.

The proposal identified an additional writer-coverage gap: initial `/bff/login` discovery failure occurs during Challenge before callback `OnRemoteFailure`, so the existing authentication writer is bypassed. With ProblemDetails selected this can become generic 500 JSON. The requester accepted including narrowly handled expected provider-unavailability failures through the existing writer, with usable browser retry and a safe availability response for machine callers. Preserve caller cancellation and unexpected-exception behavior; do not add another writer interface. Classification must use demonstrated native failure provenance, not a blanket InvalidOperationException catch.

## Deliverable

Implement the agreed source-backed scope and return focused qualification results, compatibility implications and any further verified gap in the Foundation task. The coordination task will inspect that result. New immutable release publication and Program Kit profile/knowledge adoption are separate later actions; current consumer pins remain unchanged.

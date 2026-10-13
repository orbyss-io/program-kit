# Correcting application implementation boundaries

Use this guidance when reviewing generated application code against the selected captured Foundation
contracts. Generation, a passing architecture graph and green behavior tests each prove a limited
scope. Review the actual operation and its effect owner. Put repairs and regressions in existing
feature tasks; preserve dependency locks, identities, accepted ownership, migration history and
compatibility evidence. This is not another approval stage.

## Runtime and HTTP ownership

Select a composition resource's responsibility from actual behavior. An ordinary runtime registers
application services through `IShellFeature`; its HTTP adapter uses `IWebShellFeature` in the API
owner. Select packages and prerequisites from consumed capabilities. An implementation role alone
does not imply HTTP, authentication or endpoint mapping. Correct CLR/file names while preserving the
existing `ShellFeature` identity. Reconcile untouched generated seams through maintained sync;
review customized seams explicitly rather than replacing them or registering both identities.

Verify mixed runtime/API generation and actual shell activation through the public capabilities,
including lifetime and duplicate-identity rejection. Compare dependencies with actual consumption.

## Transactions, outcomes and public tests

Commit the native transaction directly unless an application responsibility requires another type.
A class that only forwards `CommitAsync` to enable a throwing test subclass does not provide one.
Use the selected publisher's supported native EF interceptor contribution when available. Foundation
0.3.3 does not admit that contribution; do not assume a newer contract without selecting its qualified
capture. Keep test instrumentation in the tests and use native `TransactionCommittedAsync` for a
fault after the actual database commit.

Resolve the operation's production port through actual feature registration. With a real PostgreSQL
transaction, commit once and throw once from the postcommit hook. An independent connection must
observe durable data and discover the receipt. Replay the same operation and prove one effect and
the original receipt. Retain rollback, conflict, concurrency, ownership and cancellation cases.
Never substitute a mocked successful commit for this uncertainty regression. Keep implementation
classes, entities and DbSets private; remove friend declarations instead of exposing them for tests.

Keep admission, replay, expiry and result decisions application-owned. Foundation provider failure
classification and execution deadlines supply mechanisms, not a generic domain outcome or proof of
rollback. Review each operation's permitted results: a completed value-returning operation requires
its value, an uncertain operation carries only facts already known, and a durable receipt exists
only when observed. Prefer restricted construction of the smallest useful result shape. Preserve
public response meaning through explicit mapping and compatibility tests.

## Time, deadlines and admission

Use the replaceable selected `TimeProvider` in the implementing effect owner. Default registration
must preserve an already supplied provider. Passing an instant is appropriate for a pure policy or
a caller-specified instant; it does not replace a fresh read at an effectful decision boundary.
After database work and `FOR UPDATE`, read time again before testing persisted admission expiry.
Specify equality explicitly, retain the established persisted timestamp precision, and test the
actual lock-wait crossing with independently coordinated transactions. A test merely supplying a
later instant does not reproduce the wait.

Create the complete operation deadline through the selected `IExecutionDeadlineFactory` and carry
that outer `IExecutionDeadline` into PostgreSQL units and stages as well as its bounded token into
effect calls. Preserve caller cancellation separately from `IsExpired`. Avoid creating a new full
budget in each layer. Test
actual DI clock replacement, immediately before/at/after expiry, caller cancellation and deadline
expiry separately. A cancelled wait or elapsed deadline does not establish commit certainty.

## Identities and operational settings

Keep current schema identity and revision metadata with the persistence owner. EF mapping metadata
may supply current table/schema identifiers for raw SQL. Parameterize values; correctly quote
identifiers through the selected provider mechanism. Do not interpolate an untrusted identifier.
Use cohesive owner metadata for current deployment and admission checks, while preserving historical
migration bytes and their original literals. Prove current mappings, deployment and startup admission
agree through independent checks; a test reusing the same erroneous constant proves little.

Classify each repeated literal before consolidating it. An immutable migration identity, protocol
constraint and approved business rule differs from an operational limit. Catalog default and maximum
page sizes belong in owner options when the product expects configuration. Validate positive default
and maximum with default at most maximum; route the effective default for omitted requests and the
effective maximum through API admission and query execution. Export them through the selected settings
mechanism. Test a non-default configuration through actual activation, omitted/default requests,
below-one/above-effective-maximum rejection and query bounds. Avoid a hidden hardcoded maximum in
the endpoint, Core validator, UI or query after adding options.

## Browser journeys and validation

Use the [secure web profile](secure-web-profiles.md) and maintained application-owned
`IAuthenticationErrorWriter` example. Keep machine/API problem and signed-out JSON contracts.
Application callback failures need readable branded recovery independent of provider theming.
Verify session state through the native cookie/session capability: a failed new attempt can leave
an independently valid session. Offer Continue only after observing that session; always offer a
fresh sign-in action. Exercise a human-paced fresh login and actual expired-state recovery while
preserving nonce, state, correlation and PKCE validation. The configurable 900-second interaction
default includes credentials/MFA/consent; network work retains separate bounded budgets.

Serve the signed-out page from the application's public presentation owner using the selected
publisher's supported destination option. Foundation 0.3.3 hardcodes its machine destination on
both success and initiation failure; do not shadow that route to simulate support. Preserve PathBase,
antiforgery and local deletion before provider navigation. Inspect the shipped helper's result:
confirmed local sign-out with unconfirmed provider completion differs from unknown local
acknowledgement. Clear private state after dispatch and offer bounded independent session recovery.
Never restore private content merely because the response was lost.

Protocol assertions are necessary and separately named. Complete browser acceptance clicks the actual
product controls and shipped adapter, checks branding, readable text, keyboard/focus and explicit
recovery, and independently observes session absence even when provider navigation fails. Include
late responses, separate tabs and back-navigation privacy. A synthetic owner UI fixture demonstrates
the reusable helper; it does not accept the real product journey.

For normalized labels use the [owner-backed validation path](label-validation.md): export from the
actual pure server rule, then generate matching browser validation and metadata. Check both source
export and client staleness. Preserve the full raw correction input, reject raw controls before
trimming, and use the accepted UTF-16 count. Do not apply HTML maxlength or raw schema code-point
bounds as substitutes. Real paste must retain an overlong value, show an accessible field error and
make no admission/mutation request. Verify 120/121 boundaries, whitespace, controls and normalized
digest parity; direct invalid API calls must fail without durable effects. The number120 is an
application rule in the diagnostic, not a universal Program Kit constant.

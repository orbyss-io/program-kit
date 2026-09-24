# Foundation 0.2.2 adoption and completed proxy bootstrap

The published Foundation 0.2.2 combination passes the previously blocked real
host and BFF/Keycloak proofs. The existing same-session proxy bootstrap completed
through native `complete-bootstrap`, with READY, four readiness checks and zero
blockers. All consumer answers and review decisions remain simulated; the proxy
result explicitly has `authority: none` and `independentLiveWorker: false`.

This follows the [original provider-handoff audit](provider-handoff-audit-2026-09-16.md).
That audit and its failed-run archive remain historical evidence, not a current
claim that 0.2.2 is blocked.

## Verified publisher release

Foundation v0.2.2 resolves to source commit
`8d60cdd55e7fb9056c83d614786667c04ef78bdf`. The complete
[publisher Release workflow](https://github.com/orbyss-io/dotnet-foundation/actions/runs/35110254848)
succeeded. Registry inspection and pull resolved `foundation-host:v0.2.2` to
`sha256:622353f8c3888ae173819abad493ecde786307e72f661cdfa3bf3afa84cf6cde`.
The exact tagged source/license and publisher scope-binding/callback-routing
validation reports were inspected before adoption.

The 0.2.1 repair makes explicitly configured OIDC scopes replace initialized
fallback scopes while preserving defaults when configuration is absent. Version
0.2.2 also registers shell callback routes so OIDC middleware receives sign-in,
signed-out and remote-sign-out callbacks. Program Kit verifies the published
combination rather than adding the unwanted scope to its Keycloak realm.

## Program Kit changes

The managed Foundation catalog family, analyzer, OpenAPI exporter, maintained
compatibility fixtures and component probes now select 0.2.2. Forms remains
0.2.0; Localization remains 0.1.1. Runtime recovery fixtures bind the observed
0.2.2 image digest. The consumer still produces a settings/package bundle and
runs the external published host; no consumer host or image is built.

New versioned paid-trial fixtures are Internal Forms Workspace v3 and Knowledge
Application v2. Their catalog resolution hash is
`0ca415b7627d5d335c53582a3694dc98c6ece6a205c7dbf8425b3897b912ec81`.
Their predecessors remain unchanged and are explicitly rejected against this
candidate. Existing paid authorizations and checkpoints are not migrated.
Product acceptance contracts and released-reference identity remain unchanged.
The original released-reference admission continues to use its historical v1
descriptor; this is separate from selecting the current candidate fixture.

## Executed evidence

Disposable consumer: `C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-3s7t1p38`.
Native run: `proxy-a779efce3aad`. The original failed consumer is untouched.

Changed design/pins correctly invalidated previous closure evidence. The version
change was recorded in Proposed decisions; current prerequisites were reopened,
their previous values preserved, and new native receipts generated. The simulated
assessment was reviewed again because the tooling evidence changed. Final review
then accepted only the first journey's declared scope. No native workflow state or
old proof receipt was manually rewritten.

| Proof | Result | Receipt SHA-256 |
| --- | --- | --- |
| Host activation, extraction, compiled boundary, replacement, HTTP/OpenAPI and restart | 5 named cases passed | `6f94935d4fbe2f0a52dd50da97fb25521077b8bdc59b1b4010f109fa934a1ed7` |
| Pinned Keycloak discovery, published BFF activation, real code flow, permissions, antiforgery and local logout | 3 named cases passed | `1ba7808c11355115e8ad5286ceb2b96a26838393a9ff3c13329e5dccb2b9d450` |

Keycloak remains pinned to
`26.7.3@sha256:ff4257d0d64efbe99ed1ddfaf07765cc3c36dc7518bf8324d41961327f441c54`.
Shared dependency execution performed renew and locked verification. Both receipts
bind executed recipe inputs, toolchain, named JUnit cases and preserved streams.
The evidence archive retains exact executed sources. Final probe source edits after
execution only update module docstrings; AST comparison excluding those docstrings
confirms unchanged executable logic. No exact final-source receipt is fabricated.
No probe containers remained after completion.

RM-01, remember and share a need, is Ready. Buying, correction, repeat and history
remain four separate Candidate slices. Feature policy/provider admission is due at
feature planning, actual durable/member/device/accessibility checks before delivery,
and hosting/cost/secrets/recovery decisions before production. These are retained
obligations, not claimed completed application work.

Local archive: `artifacts/foundation-022-rehearsal-2026-09-16/evidence.zip`, 217 files.
SHA-256: `69e7cf5d7b3b51713647ffb306e520269b508eca49ab1c2bc0bceffcdd363201`.
The adjacent inventory binds each file. The earlier archive is preserved unchanged.
Ignored local evidence archives are not included in Git.

## Regression validation and limits

Targeted provider/pin tests: 8 passed. Intake-handoff tests: 6 passed. Versioned
fixture admission, historical-pin rejection, and live authorization/checkpoint/
supervision contracts passed without starting coding agents.

The bounded Development suite passed; log:
`artifacts/foundation-022-development-final.log`. Its first attempt correctly
rejected stale fixture catalog bindings; separately versioned fixtures repaired
that mismatch. The full suite then passed. No validation gate was relaxed.

This is a repaired investigative rehearsal, not a fresh consumer acceptance run or
a completed feature/upgrade trial. The identity probe uses local HTTP and does not
establish production cookie transport, every WEB control or provider-wide SSO logout.
Browser coverage here is Chromium; Firefox remains the existing local-host limitation
and CI obligation. No isolated token/cost savings are claimed. A fresh human intake
and bootstrap remains the useful next check of interview quality and avoidable work.
No real consumer approval, feature implementation or release publication is implied.

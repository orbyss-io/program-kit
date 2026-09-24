# Phase obligations and evidence

The installed `scripts/phase_obligations.py` owns projections and execution receipts.
Consumer semantic design and attributed reviews remain authored artifacts. Paths below
are relative to the repository, not to the feature folder.

1. Before plan/task generation, `project --feature-dir specs/<feature> --phase planning`
   creates `phase-obligations.json` and `phase-context.md`. Do not hand-edit the projection.
2. `obligation-design.json` contains `schemaVersion: 1` and a `requirements` array.
   Every projected ID occurs exactly once with `id`, `owner`, `applicability` (`applicable`,
   `not-applicable`, `exception`), a substantive `rationale`, existing `designRefs`, and
   `checkIds`. Applicable behavior requirements need actual executable check identities.
3. `semantic-contract.json` defines `schemaVersion: 1`, `scope`, and explicit `subjects`,
   `policies`, `effects`, `admissions`, `outcomes` arrays. Empty arrays mean no such mechanism
   is needed, subject to semantic review; at least one outcome is always required.
   Each record has an `id`. Policies/effects/admissions/outcomes have `checkIds`.
   Stateful subjects need identity, states, initial and terminalStates, invariants,
   transitions (id, from, to, intent, guard, outcome, checkIds), and illegalTransitionCheckIds.
   A stateless subject instead records `stateful: false` and rationale. A module's release
   cadence is not its domain subject lifecycle. No state-machine framework is mandatory.
   Policies name inputs, decisionType, decisions, sideEffectFree and beforeEffects.
   Effects name owner, kind and failureOutcome. Outcomes name owner and kind (success,
   rejection, failure, cancellation, durable-acceptance); durable acceptance additionally
   needs operationIdentity and durableOwner. Admissions name requirement (required/optional),
   owner, consistency, acknowledgement, idempotency, retry, ordering, timeout and failureOutcome;
   required admissions set successAfterAcknowledgement to true. Tests must verify these claims.
4. `verification-plan.json` has `schemaVersion: 1` and `suites`. Each suite declares an argv
   `command`, bounded `timeoutSeconds`, `result` under `artifacts/`, `format` (`trx`/`junit`),
   and `checks` mapping each required check ID to exact actual test-case names. JUnit names
   are `classname.name`; TRX uses testName. A check needs passing executed cases; disabled,
   skipped, absent and stale results cannot pass. Do not substitute `echo`/aggregate success.
5. Run `review-basis --feature-dir ...`; use its exact `basis` in `obligation-review.json`
   with stage `design` or `delivery`, verdict `accepted`, reviewer, source, findings array
   (severity low/medium/high/critical) and `requirements` mapping every ID to a substantive
   review conclusion. High/critical findings block. The review must actually assess the
   referenced design/code/tests and applicability; merely copying a hash is not review.
6. `verify --feature-dir ...` executes the approved suites, removes stale output before
   each run, captures named results and source freshness, and owns verification-results.json.
   `check --phase delivery` requires both current executed proof and delivery review.
   Changing relevant evidence or implementation requires renewed verification/review.

Owner-approved exceptions are recorded separately in `obligation-exceptions.json`, bound
to the current basis, with `approvals` keyed by requirement ID. Each contains verdict approved,
owner, confirmationSource, confirmationText, scope, rationale, compensatingEvidence and
reviewTrigger. This record must come from an actual owner decision; the agent cannot self-waive
an accepted requirement. Normal nonapplicability follows supported rules and attributed review.

For .NET, the maintained `scripts/architecture_verify.py --manifest <ownership> --output
artifacts/architecture.xml` recipe evaluates MSBuild project/package items and inspects built
assembly metadata. Register its JUnit cases `ProgramKit.Architecture.evaluated-and-compiled-graph`
and `ProgramKit.Architecture.compiled-capability-bindings` in the verification plan. Build the
current configuration first. Capability, implementation and registration names are fully qualified
compiled names. The helper uses the selected .NET 10 SDK and no third-party packages.
This recipe is complemented by consumer tests that invoke actual activated feature registration,
resolve the capability in its intended shell, and exercise replacement/extension semantics.
Where a supported equivalent suite covers these rules, use its actual cases instead. Unsupported
metadata shapes (for example unresolved generic type specifications) need equivalent compiled
tests and an explicit reviewed applicability decision; do not claim the simple metadata adapter
proves every CLR shape. Core exception paths must exist and be mapped to executed cases.

Planning declarations are not completion proof. A package pin proves selection; restored
artifacts prove materialization; configuration/registration proves activation; actual public
API use and behavior tests prove exercise of the selected mechanism. Keep these claims separate.

The .NET engineering obligations route to exact sections in the existing engineering reference.
Disposition applicability against accepted intent and affected source; do not invent use of Lazy,
pooling, queries or another conditional mechanism just to create evidence. Compiler diagnostics,
runtime cases and attributed semantic review establish different properties. Report suppressed
diagnostics with their actual scope/rationale, and review generic design conclusions against code.

For HTTP operations, declare `apiOperations` in ownership and create `api-proof.json` from its
schema. Reuse the registered OpenAPI contract paths. Bind baseline and generated artifact hashes,
typed DTO/parser/schema and old-client/snapshot checks, version decisions and per-operation source
roles. Build/export first, finalize those hashes, then execute the mapped verification plan and
review the current source. `small-operation` is a supported proportional layout with a rationale;
the normal operation-folder layout keeps composition outside the operation. Placement checks do
not prove that a composition method is thin: review the actual responsibility boundary.

For persistence, ownership names `persistenceOwners` from the canonical bootstrap decisions.
Resolve `persistence.schema.json` admission before tasks, materialize coherent central pins/project
references before coding, and bind real-provider checks in the persistence-adoption obligation.
Use existing architecture/runtime proof for actual shell resolution. Do not claim that a props
import establishes transactions, tenancy, recovery or correct provider activation.


`architecture-proof.json` uses `schemaVersion: 1`; `graph` has `method` (`evaluated-compiled`
or reviewed `equivalent`), `rationale`, and `checkIds` (an equivalent also names a `designRef`).
`bindings` covers every ownership binding exactly once with ID `<capability>@<implementationProject>`,
actual `shell` and `registration`, `resolutionCheckIds`, `extensionCheckIds`, and the observable
extension `contract`. `coreReferences` maps each `<fromProject>-><toProject>` exception to
`checkIds`. Every ID belongs to the .NET boundary obligation and an actual verification suite.
An implementation method merely existing cannot establish resolution or extension behavior.
No bindings or Core exceptions means empty collections, not invented architectural layers.

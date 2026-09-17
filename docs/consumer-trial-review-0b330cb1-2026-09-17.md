# Consumer trial review: 0b330cb1

Candidate: `05f8eb4ba15bf5f914eb3aab3b93f5cc10ea5db7` (clean source).
Preserved intake record: `artifacts/intake-sessions/9329768657894ffc9c90fa577ccb9a2e/`.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-3awzh8u3`.
Scope: saved interview, eight captured session rollouts, native workflow events,
review/approval records, architecture, roadmap, prerequisite ledger and proof receipts.
No consumer artifacts were corrected and no agents or probes were rerun for this review.

## Outcome

Bootstrap completed. The installed `workflow_lifecycle.py validate-completion`
returned `{"status":"completed","engine_verified":true}` during this review.
The event log contains 62 step starts, 62 step completions and one workflow finish.
There was no native failed step or recovery run. Internal producer retries still
occurred, documented below; successful orchestration does not mean zero trial/error.

The baseline is INITIALIZED. RM-01 is specification eligible. Feature implementation
has not happened, and this run is not evidence of product quality or delivery readiness.

Three compatibility receipts have exit code zero and close their exact obligations:

- Foundation activation: five named cases for compiled boundaries, pinned-image
  activation, registration/replacement, HTTP/OpenAPI and bundle restart.
- BFF/Keycloak: three named cases for pinned-provider discovery, published BFF
  activation, real code-flow login/permission negatives/logout.
- EF/PostgreSQL: five named cases for exact server, write/read, atomic expected-revision
  conflict, transaction rollback and retained state after restart.

The final receipt checks remain bound to the accepted baseline. They are generic
compatibility evidence, not proof of the future shopping application's behavior.

## Findings

### High: delivery execution obligations are assigned to planning and typed as decisions

`docs/architecture/bootstrap-prerequisites.json:218` assigns `actual-runtime-delivery`
to `feature-plan`, while its task says to plan AND execute application activation,
restart and security checks before delivery. At line 235, `device-proof` likewise
requires planning AND performing checks of the delivered loop at `feature-plan`.
Both have no explicit verification type, so feature obligations default to decision.

The generated readiness report already lists both as planning blockers. The native
gate in `bootstrap_lifecycle.py:212` evaluates that trigger at planning, and permits
confirmed specification answers to satisfy feature decision obligations. Thus the
current representation conflates planning evidence with executed evidence: it can
block too early, or allow an answer to satisfy what the prose describes as execution.
No actual bypass is claimed; no feature intake or implementation has run.

Split test-design/admission decisions due by planning from actual execution evidence
due at delivery. Require execution evidence for the latter, rather than a confirmed
answer. Review `provider-admission` similarly: defining the cases is legitimate
planning work, executing the actual application is a later obligation.

### Medium: consumer security case IDs have conflicting definitions

`quality-attributes.md:31` defines WEB-Q04 as private/noindex routes, public-export
privacy and headers/assets. `quality-system.md:24` uses WEB-Q04 for headers,
readiness, correlation, Problem Details, locale fallback, leaks and invalid config.
`quality-attributes.md:33` additionally defines WEB-Q05 for actual-device/accessibility
verification; the quality-system mapping stops at Q04. General accessibility prose
is present, but it does not resolve the inconsistent case identity.

Use one consumer case mapping and reference it from both artifacts. Review must
check case meaning and coverage, not only the presence of managed WEB-C identifiers.
This passed structural validation and should not be mistaken for semantic agreement.

### Medium: avoidable generation/validation churn persists

Architecture's captured tool results show four hard-budget failures:
quality-attributes.md at 6,750, 6,240 and 6,146 bytes against 6,144, then
bootstrap-baseline.md at 6,382 against 6,144. The last quality-attributes retry
was for two bytes. Architecture occupied approximately 11m29s of bootstrap.

Roadmap tool results show a size failure (6,641 against 6,144), then an unrecognized
roadmap structure and two exact affected-slice mapping failures. It initially marked
RM-01 Blocked for before-implementation compatibility; closure corrected it to Ready
for specification. This is evidence of a remaining producer-contract/application gap.

Prefer compact templates and a deterministic size/shape check before the terminal
batch, with headroom for generated sections. Preserve semantic completeness; do not
solve this simply by raising every limit or weakening validators. Measure whether
the first producer output is valid and count rereads/truncation separately.

### Lower: duplicated current-status prose is stale

`specification-roadmap.md:13` says all three compatibility dependencies remain open;
the ledger and receipts close all three. `quality-system.md:3` says the founding ADRs
remain Proposed, while its generated lifecycle section and canonical map say Accepted.
The toolchain-remediation task also retains worker-local Docker-access observations
although the supervisor successfully provisioned and executed the proofs. That does
not prove every future consumer toolchain requirement is satisfied, but these scopes
need to be distinguished.

The mechanical workflow correctly follows structured authority rather than failing
on this narrative history. Remove duplicated live status or label it dated history;
link to current receipts/ledger. No successor ADR is needed merely to restate proof
completion or acceptance.

## Intake, slicing and architecture

The interviewer proposed the complete add/bought/remaining loop, equal adult access,
one ongoing private list and a connected phone browser. The user accepted those
recommendations, explicitly deferred offline access and added future child requests.
The interviewer clarified the conditional connectivity answer and obtained explicit
confirmation before handoff. It disclosed .NET/Foundation, Keycloak and PostgreSQL
as revisable defaults instead of inventing consumer technology preferences.

Seven journeys map to five roadmap entries: shared loop; repeat items; history;
child requests; offline use. RM-01 combines three supporting journeys but does not
include those four later outcomes. On this run, that grouping follows the accepted
interview; it is not evidence that a fixture forced the entire envisioned app into
one specification. Future entries preserve uncertainty instead of inventing rules.

Architecture records one bounded context, owned list/access/UI contracts, explicit
assembly and runtime-feature dependency directions, and future architecture tests.
It explicitly selects the unchanged published Foundation image and a settings/package
release bundle, with no consumer Dockerfile or host binary requirement. UI privacy,
domain persistence, transaction/retry policy and future integration-event decisions
are represented. These are design commitments; actual enforcement needs first-code
evidence. A `.Core` suffix is deliberately not required for this small layout.

## Measured efficiency

Summed the final cumulative token usage event once per each of the eight saved
sessions; reasoning tokens are a subset of output and were not added again.

| Measurement | Observed |
| --- | ---: |
| Uncached input tokens | 619,283 |
| Output tokens | 77,632 |
| Uncached input + output | 696,915 |
| Cached input tokens, separately | 5,448,960 |
| Total input including cache + output | 6,145,875 |
| Native bootstrap elapsed time | 35m39s |
| Launcher elapsed, including intake/human waits | 1h07m37s |
| Real compatibility executor elapsed | about 87s |

Bootstrap's seven producer sessions account for 504,713 uncached-input-plus-output
tokens; the intake accounts for 192,202. Cached input is real processed usage, but
has a different cost basis; these numbers are not a billing quote. Time includes
human review waits, so it is not all agent execution. There is no controlled,
same-input comparison establishing a percentage improvement over earlier trials.

All eight rollouts contain at least one truncated tool response. This is a useful
efficiency warning, not proof that every truncated read was wasteful. The concrete
budget and structure retries above are stronger evidence of preventable work.

## Recommended next step

Keep this as a successful bootstrap baseline and a valid learning run. Correct the
phase/evidence classification and consumer case mapping before judging the subsequent
planning/implementation flow. Preserve this consumer as evidence; make any corrections
through reviewed consumer changes rather than silently rewriting accepted artifacts.
No further full intake is necessary merely to prove that this bootstrap completed.

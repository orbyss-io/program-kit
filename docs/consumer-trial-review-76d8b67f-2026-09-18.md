# Critical review: completed bootstrap 76d8b67f

Candidate: `d7e52f4a6fc3fa89d7d71ec88d90528a82cac77c`, clean source.
Preserved record: `artifacts/intake-sessions/a1825d9ecdeb47329bae517329a80604`.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-4l_9e6cl`.

## Verdict

The baseline has credible integrity and coherent design, but bootstrap completion
does not mean all managed work was successfully resolved. One confirmed Program Kit
projection defect unnecessarily deferred BFF/Keycloak verification. A separate size
contract inconsistency continues to cause avoidable authoring work. Neither finding
justifies discarding the accepted architecture or claiming the consumer is ready
for implementation.

This was a read-only consumer review. It inspected the captured interview and eight
rollouts, workflow events, approved artifacts, architecture/ADRs, roadmap, ledger,
quality mapping and proof receipts. It did not rerun agents/probes, change consumer
files or implement repairs. It did not independently re-research every external
claim in the research report or certify the eventual application.

## Integrity verified

- Installed `workflow_lifecycle.py validate-completion` returned
  `{"status":"completed","engine_verified":true}`. Native events contain 62 starts,
  62 completions and one workflow finish, with no failed native step/recovery.
- All seven assessment-approved artifact hashes still match. The previous failure
  from modifying approved research did not recur. Later verification decomposition
  lives in the Accepted `closure-verification` ADR, not rewritten approved research.
- Canonical architecture, roadmap and derived traceability/navigation validate.
  The quality-system view preserves the source WEB-Q definitions.
- Three compatibility receipts contain 11 executed JUnit cases, all successful
  with no failed/error/skipped cases: Foundation activation 5, PostgreSQL 5,
  managed browser runtime 1. These are bounded synthetic mechanism proofs.
- BFF/Keycloak compatibility is explicitly open, with no fabricated receipt.
  INITIALIZED and specification eligibility are accurately separated from planning,
  implementation, delivery and production eligibility.

The launcher's `downstream-review-required` does not invalidate this result: original
intake artifact hashes are no longer sufficient to review downstream architecture.
Current workflow completion and approval authority were independently validated.

## Finding 1: managed provider identity is case-sensitive across incompatible contracts

**Priority: high; Program Kit defect, not a missing consumer decision.**

`docs/architecture/bootstrap-decisions.json:37` contains provider `Keycloak`, scope
`local-evaluation`, source `program-kit-default`. The decision schema accepts a text
provider. Installed `bootstrap_provider_context.py:73` projects the managed runtime
only when provider equals lowercase `keycloak` exactly. Consequently the closure
brief contains `provider_inputs.identity_runtime: null`.

Read-only reproduction called the existing projection twice with copies of the
approved register. The actual value returned null. Changing only the in-memory
provider spelling to `keycloak` returned the already installed image:
`quay.io/keycloak/keycloak:26.7.3@sha256:ff4257d0d64efbe99ed1ddfaf07765cc3c36dc7518bf8324d41961327f441c54`.
The approved file was not changed.

Closure correctly avoided guessing and created `local-keycloak-proof-input` and
`bff-keycloak-compatibility`, both before implementation. However, the required kit
metadata already existed; no research or consumer choice was actually needed.
This is avoidable incomplete work. The artifact truthfulness is a success; the
managed capability handoff is not.

Recommended repair: give managed provider identities a consistent canonical contract
across default resolution, schema validation and projection. Handle known spelling
variants at the interpretation boundary without modifying approved bytes; preserve
distinct consumer-owned providers. Add a contract test that every accepted managed
identity choice supplies its required runtime/proof inputs. Do not solve this by
removing the implementation gate or treating Foundation activation as BFF proof.

## Finding 2: size budgets mix authored content with generated views

**Priority: medium; efficiency and contract clarity.**

Architecture initially exceeded 10,240 bytes at 10,339. Roadmap authoring tried
6,764, 6,293 and 6,200 bytes against 6,144, and encountered additional assertion
and architecture-size failures. Roadmap synchronization brought architecture to
10,459 bytes and triggered more trimming. These are internal producer retries,
not native workflow failures.

Later deterministic views grew the final architecture to 11,598 bytes, of which
2,072 are generated lifecycle/navigation; its authored remainder is 9,526 bytes.
Final traceability is 6,665 bytes (authored remainder 4,593); quality-system is
7,838 bytes (6,355 excluding lifecycle, still including generated quality cases).
Completion validates although these exceed earlier whole-file stage budgets.

The inconsistent unit of accounting means the agent can spend time deleting prose
to satisfy a limit that a later generated view exceeds anyway. Do not simply remove
limits or increase them arbitrarily. Define authored-content targets separately
from deterministic generated sections, reserve/measure generated content consistently,
and check the same contract at the relevant handoff. Preserve every required case
and source, rather than reward short artifacts with weaker evidence.

## Architecture and product quality

The first slice reflects the actual confirmed answers: one private continuous list,
equal partner rights, duplicate choice, bought/undo/clear, automatic online updates
and honest save/conflict feedback. Unlike a previous trial, this user accepted
duplicate detection; its presence is not unrequested scope. The confirmed synthesis
also disclosed that clearing v1 entries does not guarantee future historical recovery.

Five roadmap entries distinguish the initial shopping loop, regular-item reuse,
history, offline use and child requests. The initial loop spans four supporting
journeys and is reasonably cohesive for the accepted outcome. It is not the whole
future application. Child request handling is deliberately unselected; no approval
workflow was invented. Future journey scopes remain Candidate and owned.

One shopping context and two semantic modules are explained with alternatives.
The design distinguishes contracts/rules, provider implementation, endpoint adapters,
runtime features, shell composition and C4 containers. It names allowed dependency
directions, architecture-test placement and a deliberate same-context transaction
boundary. Those are useful implementation constraints, not evidence that dependency
tests or feature extension points have already been implemented correctly.

The consistency ADR supplies a concrete design: household revision, serialized
membership/effects, atomic idempotency, visible conflicts, bounded polling/backoff
and stale-response rejection. It acknowledges false conflicts and simultaneous
physical purchases. The five-second target has a bounded test envelope and remains
an acceptance target, not a measured result. Actual membership races, lock behavior,
idempotency retention and domain invariants remain consumer planning/delivery work;
the generic PostgreSQL fixture does not prove them.

Runtime delivery correctly uses the published Foundation host plus shells.json,
hostsettings.json, nuplane.settings.json, optional packages and a bound bundle
descriptor. No consumer host DLL, Dockerfile or derived image is required.
The browser design separates managed authentication from household authorization,
keeps private content out of discovery/export and retains the 13 web-security cases.

The three grouped planning obligations cover product policy, persistence admission
and delivery-test design. Grouping is more concise than the previous ten-item list,
but success depends on the next phase resolving their component decisions rather
than accepting a vague blanket answer. The implementation trial must still prove
application of domain semantics, .NET engineering guidance, architecture tests,
API contract discipline and safe persistence; bootstrap documents alone cannot.

## Efficiency measurements

Last cumulative token count once per each of eight unique captured sessions:

| Metric | Previous completed c0a74a71 | Current 76d8b67f |
| --- | ---: | ---: |
| Input including cached | 7,248,506 | 7,294,430 |
| Cached input | 6,734,336 | 6,823,680 |
| Uncached input | 514,170 | 470,750 |
| Output | 71,220 | 88,012 |
| Uncached input + output | 585,390 | 558,762 |
| Intake uncached input + output | 81,975 | 91,941 |
| Bootstrap uncached input + output | 503,415 | 466,821 |
| Total including cached input | 7,319,726 | 7,382,442 |

Bootstrap uncached input plus output fell about 7.3%; overall fell about 4.5%.
Total including cache grew about 0.9%. Output grew, and the current run omitted
the BFF proof, so these are observations rather than controlled causal savings.
Truncated-output occurrences fell from 19 to 12, but they remain in six sessions.
Intake had two corrected authoring mistakes: missing constraint decision_refs and
default attribution to undeclared coverage. Paging and improved diagnostics do not
yet eliminate agent authoring errors.

Native elapsed time was 49m06s, with 5m18s in review steps, leaving 43m48s outside
review versus approximately 36m42s in the prior completed run. Architecture took
14m32s; roadmap 6m54s; compatibility execution 55s. This is not evidence of a wall-time
improvement. Neither non-review elapsed time nor cached token counts equal pure
model compute or billed cost.

## Recommended next step

Keep this valid accepted baseline. Repair the managed identity contract at kit level
and validate its projection before another expensive run. Address generated-view
budget accounting as a separate bounded efficiency improvement. Specification can
start now; implementation must still wait for the accurately reported identity
obligations. The next decisive quality test is the first slice's specification,
planning and implementation gates, not another claim that bootstrap completion
proves the application or all Program Kit knowledge enforcement.

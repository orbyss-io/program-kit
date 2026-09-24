# Bootstrap initialization and phase readiness

## Problem and approved behavior

A valid project baseline was coupled to a Ready first slice. An unresolved provider,
late question or historical status assertion could prevent bootstrap completion even
when the repository was usable. The approved behavior is to initialize a reviewed
baseline, preserve uncertainty and gate only the affected slice at its actual due phase.

The stopped human trial `14d89da8` (candidate c8aed8f) retained both a servicing-risk
question and conflicting WEB-Q identifiers. These are different: the servicing decision
can retain an appropriate due activity; contradictory definitions must be corrected
before accepting them together. Original consumer files and trial evidence were not edited.

## Implementation

- Native completion renders INITIALIZED from validated baseline authority. No Ready
  entry or complete first-slice proof coverage is required. The report lists phase eligibility.
- The existing prerequisite ledger remains the authority for open obligations. No parallel
  decision registry or blanket approval bypass was introduced. Optional verification kind
  distinguishes decision evidence from compatibility evidence; existing architecture entries
  retain their compatibility requirement by default.
- Ready authorizes specification intake. Before-implementation obligations gate implementation;
  feature-plan obligations gate planning; delivery and production retain their due phases.
  Legacy before-bootstrap-completion obligations conservatively gate specification.
- An explicitly incomplete canonical journey can retain Proposed status, discovery IDs and
  empty steps/view. Its roadmap entry cannot be Ready or Active. No interaction is fabricated.
- Stage intent/design questions travel through bounded contexts. Before review, unresolved
  questions must be carried into the source-bound ledger with their exact fingerprint, owner,
  affected slices, due phase and rationale. Changed questions invalidate old carry-forward.
- Artifact conflicts and explicitly required-now questions pause for resolution. Normalized
  pauses require a matching structured handoff and current diagnostic; generic crashes remain
  failures. Native resume retains the existing owner routing and approval boundaries.
- Explicit unfamiliar stacks remain explicit. Missing managed integration becomes a consumer-owned
  design/verification obligation instead of silently adopting a conflicting managed backend.
  Applicable defaults continue to resolve absent selections.
- Proof plans may be partial or empty. Existing recipe validation still runs before execution.
  Executed negative named-test results and provisioning gaps retain open obligations and receipts;
  they do not claim compatibility. Broken probes, missing/malformed results and timeouts still fail.
- Confirmed feature-owned answers can satisfy their carried planning decisions without rewriting
  bootstrap history. Unconfirmed/stale answers and interview claims cannot replace compatibility proof.
- Fresh and recovery completion use the same initialization rule. Existing assessment/constitution/
  architecture review and scope/hash validation remain required.

## Resolution in an initialized consumer

Inspect a selected slice:

```text
python .specify/extensions/program-kit-governance/scripts/bootstrap_handoff.py eligibility --entry <ID> --phase implementation
```

Resolve ordinary feature questions in specification intake. Resolve material design changes through
existing research/architecture and ADR review; a stopped or completed primary workflow can be
reopened with `workflow_lifecycle.py reopen --run-id <ID> --stage architecture` (or research when
assessment selections must change), then resumed. Consumer-specific compatibility uses the existing
custom recipe contract and executor. These routes require no Program Kit release merely to admit
new consumer knowledge. They do not bypass actual source, approval or evidence requirements.

## Validation and limits

The new phase-readiness tests execute actual validators, a bounded negative Python compatibility
fixture and the shipped native terminal workflow. Cases cover open provider proof; no Ready entry;
ambiguous journey discovery; unanswered consumer intent; stale question carry-forward; artifact
conflicts; partial/empty proofs; confirmed feature decisions; technical failure and changed authority.
Additional existing suites cover source-bound receipts, redaction, native resumption, feature intake,
component contracts and compact context budgets. Test outcomes and commands are recorded in local
`artifacts/phase-*.log` files. The Development suite includes the new phase-readiness regression file.

These are deterministic fixtures, not a new independent live-agent intake/bootstrap run. A green
terminal replay is not evidence that all independently authored artifacts will succeed, nor a token
or elapsed-time improvement measurement. No paid worker, interactive intake, release or publication
was started by this change. The next human trial must use a fresh disposable consumer.


Verified results:

- Bounded Development suite: passed (`artifacts/phase-development-verified.log`), including
  all 13 phase-readiness cases, 22 handoff cases, 14 proof-plan cases and native resumption.
- Feature-intake confirmation/carryover: 14 cases passed, including confirmed feature answers
  satisfying their planning obligations and stale confirmation rejection.
- Context generation/staleness: passed; largest tested stage brief 32,513 bytes, below 32 KiB.
- Fresh setup-only installation: all eight components installed; 12 selected installed source
  files match the candidate byte-for-byte. Evidence record:
  `artifacts/intake-sessions/0e62bef12dc54f1a93a33ef3f99ded99/REVIEW.md`.
  This preparation did not start an intake or bootstrap session.
- `git diff --check`: passed.

The optional unfamiliar-stack path is exercised by default-resolution/handoff tests. It is not
an empirical certification of every consumer technology, and no such certification is claimed.

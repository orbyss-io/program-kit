# Repairs following successful bootstrap trial 0b330cb1

The reviewed consumer and its approvals remain unchanged. This candidate changes
Program Kit's producers and gates for a new disposable intake/bootstrap trial.

## Phase and evidence ownership

The existing prerequisite ledger still owns conditions, scope and due phase. It
now defaults delivery obligations to executed compatibility evidence rather than
an interview decision. Planning is for policy and test design; an execution-type
condition cannot be assigned to feature-plan. Explicit consumer decisions may
still be deferred to delivery when that is their actual deadline.

Specification intake projects verification kind and preserves the original due
phase. It cannot mark an open execution obligation answered/default. Closed
obligations are no longer re-interviewed. The old reference instruction that put
every inherited obligation at planning was corrected in place.

Later delivery can use the existing native proof runner with consumer-specific,
source-bound test inputs. Phase eligibility validates the latest retained attempt
with the same named-test/input/stream/design rules as ledger-attached proof.
Failed, interrupted, missing or stale attempts do not resurrect an older success.
This satisfies the relevant gate without rewriting the approved bootstrap ledger
or reconfirming a feature interview simply to record that a test passed. Normal
feature verification gates still apply. Device tests require actual device/human
evidence where applicable; a script cannot manufacture it.

## Quality-case authority

Consumer WEB-Q definitions remain in quality-attributes.md. The tooling stage
receives those definitions and generates a marked exact view in quality-system.md.
It does not independently redefine or renumber them. Duplicate definitions,
changed generated meanings and omitted cases are diagnosed. Closure and bootstrap
validation check that the view agrees with its source. Non-web projects do not
acquire a web-case requirement.

## Producer efficiency and status

The roadmap brief supplies exact Markdown record syntax and current prerequisite
scope. It omits duplicate diagram-layout data while retaining canonical journey,
ownership and relationship information. Producers name/link prerequisite IDs and
ADR metadata instead of repeating live approval or proof status in narrative text.
The existing generated lifecycle and readiness views remain responsible for status.
Historical prose is not promoted into a new blocking authority.

Output-size validation reports all oversized/missing files together, with the
terminal batch also reporting final sizes. Tooling's authored-text target reserves
space for the generated quality-case view. No hard byte limit was raised. Actual
reductions in agent retries, rereads and tokens must be measured in the next trial;
deterministic checks alone do not establish those improvements.

## Verification evidence

- `tests/validate_phase_readiness.py`: 17 cases, including planning with pending
  delivery, rejection of an answer as execution evidence, an explicit late consumer
  choice, a real bounded native receipt, preserved approval bytes, stale inputs and
  a later failed attempt.
- `tests/validate_bootstrap_handoff_quality.py`: six cases covering canonical case
  propagation, conflicting definitions, stale/missing cases, non-web behavior and
  combined size diagnostics.
- `tests/validate_specification_intake.py`: existing 14-case intake suite.
- `tests/validate_bootstrap_lifecycle.py`: proof and approval/recovery regressions.
- `tests/validate_bootstrap_context.py`: all stage projections remain within the
  synthetic fixture's 32 KiB bound; roadmap projection 31,195 bytes.
- Bounded Development suite log: `artifacts/consumer-handoff-development-final.log`.

An earlier Development attempt detected a source-file edit made while its
hash-bound proof fixture was running. The final run uses stable source; the
original failed log remains at `artifacts/consumer-handoff-development.log`.
No agent sessions, human trial, or Release suite are represented by these checks.

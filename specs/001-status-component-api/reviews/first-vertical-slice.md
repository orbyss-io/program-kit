# First Vertical Slice Review

## Candidate presented for fresh review

Feature 001 remains a narrow .NET 10 + CShells 0.0.28 vertical slice of the
public `explain`, `construct`, and `evaluate` factory operations. It is not a
general-purpose release. The prior 2026-08-01 decision rejected the earlier
prototype and remains valid for that exact evidence binding.

The current implementation/evidence candidate is pushed commit
`a5b9f04018a4e5a6ef7b046efc45fb902bfc638f`. Its distribution manifest byte
digest is
`sha256:b602af45b29e809ced96c89345bea6dcd725abc309372d4c5b00582e3a0b2345`.
The repository-owned quickstart passed 76 tests: 25 unit, 23 contract, and 28
acceptance. Exact commands, results, and proof scope are in
[`../verification.md`](../verification.md).

Material changes since the rejected candidate include:

- exact authority bound to request, closure, effect, live state, evaluation
  instant, review, and revocation state;
- a public factory-request seam, strict offline structural/typed validation,
  bounded safe values/waivers, and safe restricted-YAML source spans;
- executable intake, construction, and evaluation provider roles with exact
  role/support admission;
- mandatory candidate gates, recoverable journaled publication, exact live
  preconditions, and receipt-last admission;
- read-only evaluation, fresh-authority repair, publication recovery, honest
  lifecycle fallback, actionable bounded diagnostics, and authoritative
  workspace snapshots;
- complete black-box CLI/invalid-input/golden explanation and adversarial
  diagnostic proof;
- governed mirror tamper refusal, exact package SHA-256/NuGet content-hash
  verification, and honest verified-equivalent package claims; and
- path/culture/JSON-YAML/order canonical-byte repeatability plus clean relocated
  restore/build/test/publish, assets/deps/PE allowlisting, runtime startup, and
  `/status` without Program Kit.

## Task-ledger checkpoint before T095

T096 recorded a historical `53 satisfied, 5 superseded, 27 missing` snapshot.
T097-T100 are locally proven, T101 is complete, and the T102 deterministic gate
passes. Converting the historical 27 rows into a final proposed
`80 satisfied, 5 superseded, 0 missing` classification remains an explicit
human semantic reconciliation; automation must not silently make that claim.
T095 starts only after that ledger decision is recorded.

## Reviewer independence

T095 requires a named human making a current decision independently of
automation and the AI sessions that implemented or audited the feature. The
repository product owner may review it if their requirements authorship is
disclosed; a later independent release review may still be required.

## Review questions

1. Does the public operation/result boundary make human authority visible?
2. Is deterministic plumbing clearly separated from custom behavior?
3. Can a contributor locate and preserve consumer-owned implementation?
4. Are provider/profile selection and unsupported cases fail-closed?
5. Are diagnostics safe and actionable for a human-led AI session?
6. Do generated projects remain ordinary independently usable software?
7. Is this slice bounded enough to extend without turning Program Kit into a
   planner, runtime, or domain-semantics owner?

## Honest limitations

- Only the exact first-party .NET 10/CShells 0.0.28 profile is implemented.
- Authoring remains fixture-bounded; it is not the final user experience.
- External NuGet output is correctly `verified-equivalent`, not falsely claimed
  as canonical bytes across environments.
- The snapshot golden binds stable structure and verifies exact per-run
  references; it does not normalize dynamic external digests into a false
  timeless whole-snapshot claim.
- Recovery covers this bounded publication model; migration remains deferred.
- The local Windows gate passed; the workflow's Windows/Ubuntu result remains
  execution evidence required before merge, not semantic approval.

## Human approval gate

**PENDING TASK-LEDGER CONFIRMATION AND FRESH T095 HUMAN REVIEW.**

Do not derive acceptance from the 76 passing tests, generated evidence, CI, or
this document. After the task ledger is explicitly reconciled, record the T095
decision only after reviewing the exact candidate, with reviewer identity,
scope/evidence binding, limitations, date, and an explicit accept or reject
statement.

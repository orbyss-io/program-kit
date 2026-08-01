# First Vertical Slice Review

## Candidate presented for fresh review

Feature 001 remains a narrow .NET 10 + CShells 0.0.28 vertical slice of the
public `explain`, `construct`, and `evaluate` factory operations. It is not a
general-purpose release. The prior 2026-08-01 decision rejected the earlier
prototype and remains valid for that exact evidence binding.

The exact implementation/evidence candidate is pushed commit
`00ab520f692273e5d84329fe21034725431bafe5`. Its distribution-manifest byte
digest is
`sha256:7905022b5a8e600ad96829fd9480d3e5655e1e95005f5e0b2dfc02c497b9c2ba`.
The repository-owned quickstart passed 90 tests: 25 unit, 34 contract, and 31
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
- all 26 public diagnostics bound to typed disposition, expected/observed,
  non-empty evidence, executable remediation payloads, production triggers, and
  adversarial disclosure proof;
- content-bound diagnostic catalogs and exact provider-manifest conformance
  evidence carried into runtime admission and distribution evidence;
- nine executable SC-005 negative fixtures, including missing assembler,
  ambiguous order, determinism drift, live collision, stale precondition,
  interruption, and provider failure;
- governed mirror tamper refusal, exact package SHA-256/NuGet content-hash
  verification, and honest verified-equivalent package claims; and
- path/culture/JSON-YAML/order canonical-byte repeatability plus clean relocated
  restore/build/test/publish, assets/deps/PE allowlisting, runtime startup, and
  `/status` without Program Kit.

## Task-ledger checkpoint before T095

T096 recorded the historical `53 satisfied, 5 superseded, 27 missing` snapshot.
After T097-T106, the human explicitly authorized the current `80 satisfied, 5 superseded, 0 missing` classification.
T004, T007, T032, T036, and T046 remain unchecked and visibly superseded because
their accepted outcomes are proven through consolidated boundaries rather than
their originally named file split. T094 and T102 are complete. This ledger
decision is evidence accounting only and is not product acceptance.

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

**PENDING FRESH T095 HUMAN REVIEW.**

Do not derive acceptance from the 89 passing tests, generated evidence, CI,
ledger reconciliation, or this document. Record the T095 decision only after
reviewing the exact candidate, with reviewer identity, scope/evidence binding,
limitations, date, and an explicit accept or reject statement.

# First Vertical Slice Review

## Candidate presented for fresh review

Feature 001 remains a narrow .NET 10 + CShells 0.0.28 vertical slice of the
public `explain`, `construct`, and `evaluate` factory operations. It is not a
general-purpose release. The prior 2026-08-01 decision rejected the earlier
prototype and remains valid for that exact evidence binding.

The bounded remediation has now passed the repository-owned quickstart with
57 tests: 25 unit, 13 contract, and 19 acceptance. The exact results and proof
scope are in [`../verification.md`](../verification.md). Material changes since
the rejected candidate include:

- exact authority bound to request, closure, effect, live state, evaluation
  instant, review, and revocation state;
- a public factory-request seam and strict offline structural/typed validation;
- executable intake, construction, and evaluation provider roles with exact
  role/support admission;
- mandatory candidate gates, recoverable journaled publication, exact live
  preconditions, and receipt-last admission;
- read-only evaluation, fresh-authority repair, publication recovery, honest
  lifecycle fallback, actionable bounded diagnostics, and authoritative
  workspace snapshots;
- deterministic distribution/SBOM/provenance/catalog/support evidence, local
  safety checks, repeatability proof, and relocated ordinary runtime proof.

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
- The public schema and catalog suites are strong but not exhaustive for every
  future provider or diagnostic trigger.
- Recovery covers this bounded publication model; migration remains deferred.
- External NuGet output is correctly `verified-equivalent`, not falsely claimed
  as canonical bytes across environments.

## Human approval gate

**PENDING FRESH HUMAN REVIEW — T095 IS NOT COMPLETE.**

Do not derive acceptance from the 57 passing tests, generated evidence, CI, or
this document. Record the new decision only after reviewing the post-remediation
candidate, with reviewer identity, exact scope/evidence binding, limitations,
date, and an explicit accept or reject statement.

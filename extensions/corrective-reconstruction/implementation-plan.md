# ProgramKit corrective reconstruction implementation plan

Human-readable projection of
`pkid:plan:program-kit:corrective-reconstruction@1.0.0`.

Canonical plan SHA-256:
`df8ed9a67c41aac7f46e53e8f9a23507fee573b5527d05d644acc2e0aee1b5ae`.
Canonical design:
`pkid:design:program-kit:corrective-reconstruction@1.0.0#sha256:df36e241b7d8e9c58f1ed71d0d4d72153bcb4df789ee8548deab23d74d0d01d3`.
The canonical JSON plan is authoritative.

## Dependency order

1. `PKCR-W010` — accepted-source and reconstruction-receipt contracts,
   schemas, serialization, validation, compatibility, and migrations.
2. `PKCR-W020` — ownership/source gate and analyzer/build-policy participation
   in the existing version topology and reverse closure.
3. `PKCR-W030` — human corrective decision composed from the current migration
   assessment; add only semantically missing action values.
4. `PKCR-W040` — human-started empty-workspace, package-only reconstruction and
   atomic partitioned evidence.
5. `PKCR-W050` — repeatable clean-room structural identity, seam confinement,
   no drift, and complete acceptance evidence.
6. `PKCR-W060` — isolated cross-model conformance, honest review surface,
   canonical documentation, and bounded closure.

All work units are serial. No contract, analyzer/policy, migration, command,
runtime, or fixture implementation may begin under design authority. After exact
approval, use the registered `implement-software-plan` provider one work unit at
a time. Material architectural deviation stops for human review.

## Requirement coverage

| Requirements | Work units | Acceptance focus |
|---|---|---|
| `PKCR-R001`–`R002` | W010, W020, W040, W050 | Exact ownership and finite accepted source set |
| `PKCR-R003`–`R005` | W020–W040 | Existing topology, action reuse, complete human decision |
| `PKCR-R006`–`R009` | W040, W050 | Empty workspace, package-only reconstruction, receipt partitions, determinism |
| `PKCR-R010`–`R011` | W030, W060 | Honest cross-model and causal review-surface evidence |
| `PKCR-R012` | W010, W040–W060 | Preserved history and explicit operational/authority exclusions |

## Required verification

W010 proves schema/model round trips and rejects path overlap, invalid ownership,
forbidden accepted inputs, and conflated evidence. W020 proves source-gate
enforcement and analyzer/policy reverse closure. W030 proves complete explicit
human dispositions/actions and blocked refusal. W040/W050 run package-only
empty-workspace positive and negative reconstructions twice. W060 runs isolated
model fixtures and the full locked solution tests.

The fixture catalog in `acceptance-fixtures.json` is required. Closure evidence
must bind exact accepted/package/topology/decision/generator/structure/human/
logic/final/build/analyzer/test/ownership digests and state claim limitations.

## Stop boundary

Approval does not authorize production/operational reconstruction, secrets,
infrastructure, deployment, release, feed publication, provider integration,
Development Tool integration, capabilities, automatic rollback, history
rewriting, autonomous behavior, general behavioral-equivalence claims, or a
material deviation from the exact design or plan.

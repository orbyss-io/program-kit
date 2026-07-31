# ProgramKit bounded corrective reconstruction

Human-readable projection of
`pkid:design:program-kit:corrective-reconstruction@1.0.0`.

Canonical design SHA-256:
`df36e241b7d8e9c58f1ed71d0d4d72153bcb4df789ee8548deab23d74d0d01d3`.
If this projection differs from `architecture-design.json`, the JSON is
authoritative.

## Decision

Compose ProgramKit's current architecture/design/plan/approval, artifact,
generation-receipt, source-gate, local-package, version-map, reverse-closure,
migration, and evidence contracts. Add only:

- an accepted-source manifest with exact per-file ownership/mode;
- partitioned reconstruction receipt/review-surface evidence;
- two migration actions only if implementation-time semantic inspection proves
  no existing equivalent.

No parallel ownership graph, dependency graph, migration workflow, or rollback
system is introduced. This review is independent from Development Tools.

## Ownership model

| Class | Mode | Mechanical meaning |
|---|---|---|
| `human-semantic` | `protected` | Reviewed human semantics are copied byte-for-byte; generator/model edits fail. |
| `program-kit-generated` | `regenerated` | Exact declared generator owns structure/plumbing; generated header/path/source gate and generation receipt must match. |
| `declared-logic-seam` | `editable` | Human/model logic is allowed only at exact paths and under exact seam contracts/tests; structural edits fail. |

Paths are normalized, exact, non-overlapping, and finite. Every materialized
source file must be declared. Ownership comments are insufficient by themselves.

The accepted source set includes exact approved designs/plans/approvals, human
semantics, generation inputs and selections, accepted declared logic, local
package/version/lock inputs, version map and migration decision, quality/build
policy, and non-secret configuration templates. It excludes generated/build
outputs, history as executable input, ambient machine state, ProgramKit source
coupling, production/operational state, and secret values.

## Version topology and corrective choice

The analyzer/gate implementation and build policy become nodes in the existing
version map. Consumers depend on the policy through existing dependency
semantics, and the policy depends on the analyzer/gate, so reverse fixed-point
closure includes affected consumers.

The existing migration assessment remains authoritative:

- `UnaffectedWithProof` = unchanged with proof.
- `CompatibleAfterActions` plus existing actions = regenerate, recompile,
  repack/relock, retest, adapter, artifact/config migration.
- `Redesign`, `ManualReview`, and `Blocked` retain their existing meaning.
- `RepairImplementation` and `ReimplementDeclaredLogic` are added only if no
  existing action is semantically exact.

Every impacted node needs one human-reviewed disposition and exact actions.
ProgramKit may recommend and validate; it never silently chooses or executes a
repair, regeneration, reimplementation, adapter, migration, rollback, or
history rewrite.

## Clean-room reconstruction

The human starts reconstruction in a newly created, empty, contained application
workspace. ProgramKit validates exact accepted inputs and a complete unblocked
decision; prepares local packages and controlled `NuGet.Config`; materializes
protected semantics; regenerates structure; materializes accepted logic only
inside seams; restores/builds locked; runs ownership/source/analyzer/test gates;
atomically commits outputs; and emits a receipt only after success.

Consumer project references to ProgramKit, source/file includes, assembly hint
paths, build-output coupling, and uncontrolled first-party sources fail.

Receipts separately bind accepted-source set, package closure/source map,
version closure/decision, generator inputs/generator/receipts, structural tree,
human semantic tree, logic tree, final source tree, build/analyzers/tests,
ownership conformance, tool revisions, and empty-workspace proof.

## Determinism and cross-model honesty

Two identical reconstructions must have byte-identical protected/generated
structure and structural-tree digest. Authored logic is separately digested.

Two isolated model sessions receive identical accepted inputs, seams, packages,
policies, contracts, property tests, and negative tests. Both must preserve
structure and ownership and pass the same exact bounded tests. Their logic source
may differ. Passing those tests proves only covered behavior; it does not prove
general behavioral equivalence.

Review surfaces report exact artifact identities, ownership, causal paths,
human decisions/actions, contracts, logic seams, package/config migration,
tests/evidence, and risks. Line counts are not correctness, complexity, risk, or
equivalence evidence.

## Open decision, exclusions, and deferrals

Before PKCR-W030 changes migration actions, semantic inspection must decide
whether existing actions already express implementation repair or declared-logic
reimplementation. An existing exact meaning must be reused; a material plan
change returns to review.

Production data, infrastructure, secrets, operational history, deployment,
release, package-feed publication, provider integration, capabilities, automatic
rollback, destructive history rewriting, and autonomous behavior are excluded.
Any Development Tool integration or stronger equivalence claim needs another
review.

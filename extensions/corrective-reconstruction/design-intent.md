# ProgramKit corrective reconstruction design intent

## Human-started outcome

Design bounded implementation ownership and a human-reviewed corrective
reconstruction workflow that composes ProgramKit's existing architecture,
planning, approval, artifact, generation, version-map, migration, quality, local
package, and receipt contracts. Do not create redundant ownership or migration
systems when those contracts already carry the required meaning.

## Ownership and accepted source set

Add one versioned accepted-source manifest,
`pkid:schema:program-kit:accepted-source-manifest@1.0.0`, whose entries use
exact repository-relative paths (no globs after normalization), artifact
identity/version/digest, and one of three ownership classes:

1. `human-semantic`: reviewed human-owned semantics copied byte-for-byte and
   protected from generated or model edits.
2. `program-kit-generated`: deterministic structure/plumbing regenerated only
   by the exact declared generator and checked by current ProgramKit generated
   header/path, source-gate, generation-receipt, and output-digest rules.
3. `declared-logic-seam`: explicitly editable human/model-authored logic within
   exact paths and declared contract/test boundaries; structural edits outside
   the seam fail.

Each entry declares `protected`, `regenerated`, or `editable` mode, an owner,
the applicable architecture requirement or logic-seam contract, and exact
quality/build policy identities. Overlap, undeclared files, generated-header
misuse, edits to protected input, generated output outside generated paths, and
logic changes outside editable seams fail closed.

The clean-room accepted source set consists only of exact approved architecture
designs, implementation plans and approvals; human-semantic entries; generation
inputs and generator selections; declared logic-seam contracts and accepted
logic source; package manifest/version selection/locks; version map and migration
assessment; quality/build policy; and required non-secret configuration
templates. Generated outputs, `bin`/`obj`, ProgramKit project references,
ProgramKit source/file includes, assembly hint paths, build outputs, repository
history, production state, and ambient machine configuration are not accepted
inputs.

History remains preserved in normal version control and may inform human review,
but reconstruction neither requires it as executable input nor rewrites it.
Automatic rollback and destructive history rewriting are prohibited.

## Version topology and assessment

Analyzer and build-policy revisions become explicit nodes in the existing
component/version map. A project or generated-artifact boundary depends on the
build-policy artifact through the existing `configured-by` relation; that policy
depends on the exact analyzer/gate implementation. Existing reverse fixed-point
closure therefore includes affected consumers when either revision changes.
No parallel dependency graph is introduced.

The existing migration assessment remains the decision carrier:

- `UnaffectedWithProof` represents unchanged-with-proof.
- `CompatibleAfterActions` plus actions represents incremental repair,
  regeneration, recompilation, repackaging/relocking, retesting, logic
  reimplementation, adapter introduction, and artifact/configuration migration.
- `Redesign`, `ManualReview`, and `Blocked` preserve their existing meanings.

Only two action values are added if semantic validation confirms no existing
equivalent: `RepairImplementation` and `ReimplementDeclaredLogic`. Existing
`Regenerate`, `Recompile`, `RepackageOrRelock`, `Retest`, `AddAdapter`,
`MigrateArtifact`, and `MigrateConfiguration` are reused. Every impacted node
must receive one human-reviewed disposition and exact actions before execution.
The workflow recommends; it does not select, repair, regenerate, reimplement,
adapt, migrate, or roll back without that decision.

## Reconstruction workflow and evidence

The operation validates and digest-binds the accepted source manifest, emptiness
of a newly created application workspace, architecture/plan/approval bindings,
package closure, generator versions, version topology, migration assessment, and
quality policy. It then prepares exact local ProgramKit packages, emits a
source-mapped `NuGet.Config`, materializes protected human inputs, generates
deterministic structure, materializes only the accepted declared-logic source,
restores/builds under locked package-only consumption, runs ownership/source
gates and selected tests, and emits a reconstruction receipt only after all
outputs are committed.

The receipt separately records:

- accepted-source-set digest;
- ProgramKit package-closure and NuGet source-map digests;
- version-map, reverse-closure, assessment, and human-decision digests;
- generator-input, generator, generated structural-tree, and generation-receipt
  digests;
- human-semantic and declared-logic-seam tree digests;
- final source-tree, build, analyzer, test, and ownership-conformance evidence;
- tool/runtime revisions and the empty-workspace precondition.

Two repetitions with identical accepted inputs must produce byte-identical
generated/protected structural output and identical structural-tree digest.
Logic source identity is assessed separately.

## Cross-model conformance and review surface

Two isolated model sessions receive the same exact accepted source set and are
limited to the same declared logic seams. Both must leave protected/generated
structure byte-identical, produce no undeclared files, and pass the same
contract, property, negative, build, and analyzer tests. Their logic source may
differ; the evidence records each logic-tree digest and semantic seam outcomes.

Passing a shared test set proves only the behaviors covered by those exact
contracts and tests. It does not prove general behavioral equivalence. Identical
generated output is not presented as identical authored logic.

The review surface reports affected artifact identities, ownership class,
version-causality paths, chosen human disposition/actions, changed contracts,
logic seams, configuration/package migrations, test/evidence links, and
unresolved risks. Added/deleted line counts may be supplemental diagnostics but
must not be used as complexity, correctness, risk, or equivalence claims.

## Package boundary, exclusions, and independence

Reconstructed consumers use ProgramKit only through exact locally prepared
packages and controlled NuGet source mapping. Project references, source/file
includes, assembly hint paths, and build-output coupling fail conformance.

This review explicitly excludes automatic reconstruction of production data,
infrastructure, secrets, operational history, deployment, release, package-feed
publication, and autonomous behavior. It also excludes implementation and any
provider adapter, binding, MCP server, or capability. A future integration with
ProgramKit Development Tools would require its own approved review; neither
current review set approves or depends on the other.

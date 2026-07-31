# Program Kit alpha version transition

Canonical source: `architecture-design.json` (`sha256:2b8027d505dfcef7f1b28bc3aecf3333b575e59928dabb7121d24f28be2811ba`), governed by Architecture Design `2.0.0`.

> Transitional artifact: implementation requires later explicit approval of the exact canonical design and plan digests.

## Intent

Establish explicit version intents, replace pre-stable Program Kit-owned contract revisions with alpha ordinals, and coordinate every packaged first-party deliverable at 0.1.0-alpha.2 without rewriting external selections or immutable history.

## Scope

- A closed repository inventory that classifies product release versions, owned artifact revisions, external selections, historical evidence revisions, and fixture revisions.
- A replaceable alpha progression policy that validates explicit human-selected next versions without choosing release authority.
- Alpha replacement revisions and deterministic migrations for every active Program Kit-owned schema, contract, policy, capability, plan, design, and comparable governed identity.
- Architecture Design 0.1.0-alpha.2, Implementation Plan 0.1.0-alpha.3, and StaticConformanceDisposition 0.1.0-alpha.1 as the first transitioned design-flow contracts.
- One exact 0.1.0-alpha.2 product release identity across NuGet packages, CLI metadata, capability bundle content, and generated first-party package references.
- An independent capability-bundle manifest-format revision, byte-exact bundle regeneration, thin provider-wrapper verification, and isolated initialization proof.
- A second-stage review set under the transitioned contracts for refresh, contributor setup, Console reachability, public analyzers, and the eventual JTest migration prompt.

## Non-goals

- Defining or enforcing stable patch, minor, or major compatibility progression before Release Kit is designed.
- Publishing, promoting, deploying, or releasing 0.1.0-alpha.2 to a package feed.
- Rewriting immutable historical approvals, closure evidence, receipts, third-party versions, SDK versions, target frameworks, or intentional fixtures.
- Implementing capability refresh behavior, the .contributors maintainer setup, Console generation reachability, or public analyzer behavior in this transition.
- Mutating JTest or any other consumer repository.
- Activating Program Kit source capabilities in the Program Kit authoring workspace.
- Creating hooks, watchers, autonomous agents, provider-global configuration, or runtime application architecture.

## Assumptions

- The existing exact version-map and migration-assessment mechanisms remain suitable foundations once version intent and alpha progression are explicit.
- Legacy stable-looking contract revisions remain readable and immutable while active selectors move through registered migrations.
- The current private Program Kit C# gate remains compatible with Program Kit-owned transition implementation.
- Release Kit will own the later stable progression strategy and the explicit transition to 1.0.0.
- The Program Kit repository can prove capability initialization in an isolated consumer workspace without activating those capabilities at its authoring root.

## Version semantic models

| Identity | Meaning | Invariants |
|---|---|---|
| `pkid:model:program-kit:version-intent-classification` | A closed classification of every active version-bearing repository value before any automated progression or rewrite. | Every active value has exactly one intent; product and owned-artifact clocks are never conflated; external, evidence, and fixture values cannot become product or public-contract releases through defaulting. |
| `pkid:model:program-kit:alpha-owned-artifact-progression` | A stable governed identity with immutable revisions whose pre-stable versions progress as 0.1.0-alpha.N. | New identities begin at alpha.1; changed canonical bytes advance exactly one ordinal; identity plus version plus digest is immutable; compatibility and migration disposition are explicit; no stable SemVer significance is inferred. |
| `pkid:model:program-kit:coordinated-product-release` | One human-selected Program Kit release value projected into every first-party packaged surface. | The central selected value is 0.1.0-alpha.2 for this transition; package artifacts and current generated references agree exactly; bundle format remains an independent owned contract; publication remains separately authorized. |
| `pkid:model:program-kit:legacy-to-alpha-migration` | An explicit mapping from each active stable-looking legacy revision to one immutable alpha replacement revision. | Legacy bytes and evidence are not rewritten; replacement identities remain stable; selectors move only through registered migrations; reverse dependency closure and incompatible or undecided edges fail closed. |

## Components

### `pkid:component:program-kit:version-intent-inventory`

Enumerate every active version-bearing source with one exact intent, identity, current version, digest, owner, consumers, and transition disposition.

- Owner: `pkid:domain:program-kit:version-governance`
- Kind: `evaluated-artifact`
- Activatable: `false`
- Compatibility boundary: Inventory schema, closed intent vocabulary, exact source path and digest, active-versus-historical status, and completeness proof.

### `pkid:component:program-kit:alpha-progression-validator`

Validate an explicit proposed owned-artifact revision against immutable identity history and the selected alpha policy.

- Owner: `pkid:domain:program-kit:version-governance`
- Kind: `domain-core`
- Activatable: `false`
- Compatibility boundary: Policy identity, history input, canonical digest equality, next-ordinal result, diagnostics, and replacement-policy selection.

### `pkid:component:program-kit:owned-artifact-migration-registry`

Register exact legacy-to-alpha replacements, compatibility classifications, migration definitions, and selector closure.

- Owner: `pkid:domain:program-kit:version-governance`
- Kind: `evaluated-artifact`
- Activatable: `false`
- Compatibility boundary: Stable identities, exact source and target revisions, typed dependencies, compatibility decisions, migration order, and fail-closed unresolved edges.

### `pkid:component:program-kit:product-release-coordinator`

Project one explicit product release version into package metadata, bundle content metadata, generated current references, and verification expectations.

- Owner: `pkid:domain:program-kit:distribution-version`
- Kind: `focused-helper`
- Activatable: `false`
- Compatibility boundary: Explicit input version, finite projection targets, exact equality, deterministic diagnostics, and no publication or autonomous bump.

### `pkid:component:program-kit:capability-contract-transition`

Move design and gate-design procedures to the new alpha contracts, regenerate exact bundle bytes, and prove isolated provider-wrapper initialization.

- Owner: `pkid:domain:program-kit:capability-distribution`
- Kind: `design-time-source`
- Activatable: `false`
- Compatibility boundary: Canonical capability identity and authority, exact contract references, thin wrappers, bundle manifest format, content release, ownership locks, refresh migration, and authoring-root denial.

## Reference rules

- **forbidden** `pkid:reference-rule:program-kit:owned-version-independent-of-product` — Program Kit-owned schema, contract, policy, capability, plan, design, disposition, and comparable governed artifact revisions → The coordinated Program Kit product release value as an inferred owned-artifact revision. Product release and owned-artifact revision are independent clocks; a coincidental number never establishes compatibility.
- **allowed** `pkid:reference-rule:program-kit:single-product-release` — First-party Program Kit package metadata, CLI release metadata, capability bundle content metadata, and generated current first-party package references → One explicit central product release selection. One finite source eliminates release drift and permits exact package and generated-output verification.
- **forbidden** `pkid:reference-rule:program-kit:no-history-or-external-renumber` — Alpha version transition rewrites and active-selector migration → External selections, immutable historical approval or closure evidence, receipts, and explicit fixture identities as values to renumber. Those values carry upstream, evidentiary, or synthetic meaning and are not current Program Kit product or owned-contract releases.

## Boundaries

### security

Version processing reads only explicit repository inputs and performs no feed, provider, secret, or network discovery.

Guarantees:

- Exact paths, versions, and digests are validated before migration or projection.
- Generated and initialized outputs remain subject to path-containment and ownership checks.

Exclusions:

- Package-feed credentials, signing, promotion, deployment, and provider trust are outside this transition.

### authority

Humans select product releases, approve exact designs and plans, decide compatibility, and authorize migration; tooling only validates and projects explicit selections.

Guarantees:

- No version is bumped, package published, capability activated, or consumer migrated autonomously.
- The current review stops before implementation and the follow-on review stops again before its implementation.

Exclusions:

- Approval of recommendations is not treated as approval of later canonical design or plan bytes.

### secrets

No transition contract, migration, package build, bundle check, or isolated initialization needs a secret.

Guarantees:

- Verification is local and operates on repository or generated fixture bytes.

Exclusions:

- Feed authentication, signing keys, provider credentials, and consumer secrets are not read or recorded.

### persistence

Canonical revisions, migration definitions, registries, and review artifacts are immutable digest-bound repository files; projections are regenerated.

Guarantees:

- Legacy revisions and historical evidence remain byte-unchanged.
- New alpha revisions use new exact paths or registrations and atomic generated-output publication where applicable.

Exclusions:

- No database, remote registry, package feed, user-global state, or consumer repository is an authority.

### failure

Ambiguous intent, duplicate identity-version pairs, digest drift, skipped alpha ordinals, unresolved migrations, version disagreement, or unsafe output fails closed with deterministic diagnostics.

Guarantees:

- Validation reports every classified path and every incompatible or undecided dependency edge.
- Partial package, schema, bundle, or capability transitions cannot be accepted as closure.

Exclusions:

- Tooling never guesses intent, compatibility, migration authority, or the stable version strategy.

### concurrency

Inventory, generation, and validation may parallelize only over immutable inputs; final registry, package, and bundle promotion is serialized.

Guarantees:

- Concurrent validation cannot change selections or canonical bytes.
- One final exact inventory and release selection governs closure.

Exclusions:

- No watcher or autonomous refresh loop is introduced.

### cancellation

Cancellation stops before promotion or leaves the previous complete canonical or generated state intact.

Guarantees:

- Temporary outputs are outside authoritative roots until verification succeeds.
- Cancellation never implies approval, rollback of committed history, or silent retry.

Exclusions:

- External package publication and consumer migration are not started.

### observability

Deterministic reports expose classification, old and new exact revisions, digests, migration decisions, package agreement, bundle verification, initialization isolation, tests, and changed paths.

Guarantees:

- Review and closure evidence distinguishes implemented, scaffolded, deferred, historical, and external claims.
- Every artifact in the review set is digest-bound.

Exclusions:

- Telemetry, remote evidence transport, and consumer data capture are not introduced.

### compatibility

Version intents evolve independently; active contract replacement requires explicit compatibility and migration disposition even though stable patch/minor/major enforcement is deferred.

Guarantees:

- Identity plus version plus digest denotes one immutable revision.
- Legacy-to-alpha mappings are explicit and reverse dependency closure is assessed.
- First-party packaged outputs agree exactly on 0.1.0-alpha.2.

Exclusions:

- Matching numbers do not imply compatibility and external selections are never renumbered.

## Scenarios

### `pkid:scenario:program-kit:classify-version-inventory`

**Actor:** Program Kit maintainer

**Intent:** Classify every active version-bearing repository source before changing any version.

Steps:

1. Enumerate finite version-bearing sources and their exact paths and digests.
2. Assign exactly one version intent, owner, active status, and transition disposition to each source.
3. Reject duplicates, missing classifications, and inferred category changes.
4. Review the complete inventory before any rewrite or selector migration.

Outcomes:

- Every active value is explicitly classified.
- External selections, immutable history, and fixtures are protected from product or contract renumbering.

Failure outcomes:

- An unclassified or ambiguously classified value blocks the transition.

### `pkid:scenario:program-kit:migrate-owned-contracts-to-alpha`

**Actor:** Program Kit maintainer

**Intent:** Replace active stable-looking Program Kit-owned revisions with immutable alpha ordinal revisions.

Steps:

1. Materialize new alpha schema, contract, policy, capability, plan, design, and disposition revisions without changing legacy bytes.
2. Register exact old-to-new migration definitions and update internal exact references.
3. Run schema, semantic, version-map, migration-assessment, and historical-immutability conformance.
4. Move active selectors only after the dependency closure is fully decided.

Outcomes:

- Architecture Design selects 0.1.0-alpha.2, Implementation Plan selects 0.1.0-alpha.3, and StaticConformanceDisposition selects 0.1.0-alpha.1.
- All other active owned identities use the correct independent alpha ordinal.
- Legacy revisions remain available as immutable migration sources.

Failure outcomes:

- Skipped ordinals, changed legacy bytes, duplicate exact keys, stale references, or unresolved migration edges prevent selector movement.

### `pkid:scenario:program-kit:coordinate-alpha-two-packages`

**Actor:** Program Kit maintainer

**Intent:** Prepare every first-party packaged Program Kit deliverable at 0.1.0-alpha.2.

Steps:

1. Project the exact release into central package metadata, CLI metadata, bundle content metadata, and current generated first-party package references.
2. Assign the capability-bundle manifest format its independent alpha contract revision.
3. Build and inspect all packages and the exact capability bundle without publishing.
4. Generate representative hosts and verify that every current first-party package reference is 0.1.0-alpha.2.

Outcomes:

- No packaged first-party component has version drift.
- Bundle content release and bundle manifest format are distinguishable.
- Local package and generated-host conformance passes.

Failure outcomes:

- Any missing target, conflicting literal, stale bundle digest, or package mismatch blocks closure.

### `pkid:scenario:program-kit:transition-design-capability`

**Actor:** Program Kit maintainer

**Intent:** Move design procedures to alpha contracts without activating Program Kit source capabilities.

Steps:

1. Update canonical design and gate-design procedures to the exact alpha contract versions.
2. Keep provider adapters thin and regenerate the capability bundle with exact source and output digests.
3. Initialize an isolated consumer fixture from the explicit Program Kit root and verify ownership-lock refresh.
4. Reject initialization when the selected workspace is the Program Kit authoring root.

Outcomes:

- A future design session can produce Architecture Design alpha.2, Implementation Plan alpha.3, and StaticConformanceDisposition alpha.1 artifacts.
- The source capabilities remain inert in the authoring workspace.

Failure outcomes:

- Copied semantics in a wrapper, stale bundle bytes, unsafe overwrite, manual-fix dependency, or authoring-root activation blocks closure.

### `pkid:scenario:program-kit:produce-follow-on-health-review`

**Actor:** Program Kit architecture contributor

**Intent:** Produce the remaining health design under the transitioned alpha contracts.

Steps:

1. Design deterministic installed-bundle refresh and re-initialization.
2. Design the .contributors maintainer-workspace setup at the parent of the checkout.
3. Design Console CLI and refresh reachability with exact compilation inputs.
4. Design opt-in public analyzers without exposing private PKCS policy.
5. Produce and validate the separate alpha-contract review set and stop for exact human approval.

Outcomes:

- All deferred health concerns are represented by bounded dependency-ordered work units.
- The eventual JTest migration prompt is derived only after Program Kit implementation and verification complete.

Failure outcomes:

- The follow-on design cannot begin under legacy design-flow contracts or silently implement behavior.

## Static conformance

Disposition: `pkid:static-conformance-disposition:program-kit:alpha-version-transition@1.0.0` (`sha256:62536fba1fd42a652ab042398849a72c8c3a88f80f5d83e6eaa023839a16061d`).

The selected disposition is `reuse-existing` for the private Program Kit C# gate. Repository-wide version, package, migration, bundle, and initialization invariants remain executable or architecture conformance obligations.

## Approval boundary

This design is `scaffolded`. It is not approved and authorizes no implementation, publication, capability activation, consumer mutation, or JTest change.

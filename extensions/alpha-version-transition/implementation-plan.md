# Program Kit alpha version transition implementation plan

Canonical source: `implementation-plan.json` (`sha256:66e37776c11cda3ee17747b6dd3165286e4a2901e17dca41464a243f1f2e750f`), governed by Implementation Plan `3.0.0`.

Design binding: `pkid:design:program-kit:alpha-version-transition@0.1.0-alpha.1` (`sha256:2b8027d505dfcef7f1b28bc3aecf3333b575e59928dabb7121d24f28be2811ba`).

State: `ready-for-human-decision`.

## Requirements

| ID | Observable outcome | Work units |
|---|---|---|
| `PKAV-R001` | Every active version-bearing repository value is inventoried and has exactly one reviewed version intent. | `PKAV-W010, PKAV-W030, PKAV-W070` |
| `PKAV-R002` | The replaceable alpha policy validates explicit 0.1.0-alpha.N progression without selecting release authority or enforcing stable SemVer significance. | `PKAV-W010, PKAV-W070` |
| `PKAV-R003` | Identity plus version plus digest remains immutable and changed canonical bytes require the next alpha ordinal. | `PKAV-W010, PKAV-W020, PKAV-W030, PKAV-W070` |
| `PKAV-R004` | Every active Program Kit-owned governed identity has an exact legacy-to-alpha mapping, compatibility disposition, migration definition, and closed dependency assessment. | `PKAV-W020, PKAV-W030, PKAV-W070` |
| `PKAV-R005` | Architecture Design, Implementation Plan, and StaticConformanceDisposition move to alpha.2, alpha.3, and alpha.1 respectively before follow-on design. | `PKAV-W020, PKAV-W050, PKAV-W060, PKAV-W070` |
| `PKAV-R006` | All first-party NuGet packages, CLI release metadata, capability bundle content, and current generated first-party package references use exactly 0.1.0-alpha.2. | `PKAV-W040, PKAV-W070` |
| `PKAV-R007` | The capability-bundle manifest format has an independent owned alpha contract revision and cannot be confused with bundle content release. | `PKAV-W040, PKAV-W070` |
| `PKAV-R008` | External selections, immutable historical evidence, receipts, and explicit fixtures remain unchanged and explicitly classified. | `PKAV-W010, PKAV-W030, PKAV-W070` |
| `PKAV-R009` | Version maps, schema registries, semantic validators, migration assessment, and exact selectors accept and preserve prerelease SemVer identities. | `PKAV-W010, PKAV-W020, PKAV-W030, PKAV-W070` |
| `PKAV-R010` | Canonical capability procedures use the new alpha contracts, provider wrappers remain thin, and the regenerated bundle is byte-exact. | `PKAV-W050, PKAV-W070` |
| `PKAV-R011` | Isolated capability initialization and refresh succeeds without manual fixes while Program Kit authoring-root activation remains rejected. | `PKAV-W050, PKAV-W070` |
| `PKAV-R012` | Local package builds and representative generated hosts prove exact alpha.2 first-party reference agreement without publication. | `PKAV-W040, PKAV-W070` |
| `PKAV-R013` | A separate follow-on health design and plan are produced under the new alpha contracts and stop for exact human approval. | `PKAV-W060, PKAV-W070` |
| `PKAV-R014` | Closure evidence proves inventory completeness, migration closure, historical immutability, package agreement, bundle integrity, capability isolation, and unchanged deferred scope. | `PKAV-W070` |

## Work units

### `PKAV-W010`

Establish the closed version-intent inventory plus replaceable alpha progression policy schema, model, validator, fixtures, and diagnostics without granting version-selection authority.

- Sequence: `10`
- Kind: `product`
- Depends on: `none`
- Planned output: `pkid:plan-output:program-kit:pkav-w010@0.1.0-alpha.1`

Allowed edits:

- schemas/versioning and exact schema registration
- src/Orbyss.ProgramKit.Artifacts version-intent and progression contracts
- src/Orbyss.ProgramKit.Workbench bounded validation operations
- focused unit and conformance fixtures, tests, and versioning documentation

Compatibility:

- `pkid:policy:program-kit:alpha-version-progression` accepts `0.1.0-alpha.1`: First pre-stable policy revision; Release Kit may replace the selected policy through an explicit compatible strategy contract.

Stop condition: Stop if intent must be inferred from a numeric shape, the inventory is open-ended or incomplete, or the validator chooses a version or release.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — The closed inventory, alpha ordinal fixtures, duplicate/digest/skip failures, and no-authority behavior pass.

### `PKAV-W020`

Materialize and register Architecture Design 0.1.0-alpha.2, Implementation Plan 0.1.0-alpha.3, and StaticConformanceDisposition 0.1.0-alpha.1 with exact legacy migrations and updated semantic validation.

- Sequence: `20`
- Kind: `product`
- Depends on: `PKAV-W010`
- Planned output: `pkid:plan-output:program-kit:pkav-w020@0.1.0-alpha.1`

Allowed edits:

- schemas/architecture and src/Orbyss.ProgramKit.Architecture schema modules, models, validators, and migrations
- schemas/planning and src/Orbyss.ProgramKit.Planning schema modules, models, validators, admission, and migrations
- Workbench schema selection and exact migration registration
- design/planning/static fixtures, tests, renderers, and documentation

Compatibility:

- `pkid:schema:program-kit:architecture-design` accepts `0.1.0-alpha.2`: Replaces legacy 2.0.0 through an explicit deterministic migration; legacy bytes remain immutable.
- `pkid:schema:program-kit:implementation-plan` accepts `0.1.0-alpha.3`: Replaces legacy 3.0.0 and requires StaticConformanceDisposition 0.1.0-alpha.1.
- `pkid:schema:program-kit:static-conformance-disposition` accepts `0.1.0-alpha.1`: Replaces legacy 1.0.0 without changing the five explicit human decision states.

Stop condition: Stop if legacy schemas are edited, migrations lose information, plan admission weakens the static-conformance preflight, or alpha schema identities do not resolve exactly.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — Old and new schema validation, deterministic migrations, renderers, exact references, semantic validators, and admission fixtures pass.

### `PKAV-W030`

Migrate the remainder of the complete active Program Kit-owned governed inventory to independent alpha ordinals and close every exact reference and dependency edge.

- Sequence: `30`
- Kind: `product`
- Depends on: `PKAV-W020`
- Planned output: `pkid:plan-output:program-kit:pkav-w030@0.1.0-alpha.1`

Allowed edits:

- Only active owned-artifact paths and registries enumerated by the approved version-intent inventory
- Exact migration definitions, compatibility records, schema modules, source models, fixtures, and focused tests
- Canonical capability and policy revision metadata without activating capabilities
- Version maps, selection documents, assessment fixtures, and versioning documentation

Compatibility:

- `pkid:map:program-kit:active-owned-alpha-transition` accepts `0.1.0-alpha.1`: Every exact active legacy revision has one reviewed alpha target or an explicit protected non-owned disposition.

Stop condition: Stop on an unclassified active value, ambiguous revision ordinal, changed legacy byte, duplicate exact key, unresolved dependency, or a proposed renumber of external, evidence, receipt, or fixture values.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — Inventory completeness, old-byte immutability, exact registrations, version-map closure, reverse migration closure, and protected-category fixtures pass.

### `PKAV-W040`

Project the one explicit 0.1.0-alpha.2 product release across every first-party package, CLI surface, capability bundle content identity, current generated package reference, and exact local-package verification path.

- Sequence: `40`
- Kind: `product`
- Depends on: `PKAV-W030`
- Planned output: `pkid:plan-output:program-kit:pkav-w040@0.1.0-alpha.1`

Allowed edits:

- Directory.Build.props and bounded central package-version validation
- First-party project/package metadata, package locks, and exact package manifests
- CLI and generation renderers containing current first-party release metadata
- Capability-bundle manifest-format schema and bundle content metadata
- Local package, generated-host, bundle, and version-drift conformance tests

Compatibility:

- `pkid:release:program-kit:product` accepts `0.1.0-alpha.2`: All first-party packaged deliverables and embedded current first-party references agree exactly; no publication is performed.
- `pkid:schema:program-kit:capability-bundle-manifest` accepts `0.1.0-alpha.1`: The new format separates manifest contract revision from the alpha.2 bundle content release.

Stop condition: Stop if any first-party packaged component retains another version, a third-party version is rewritten, bundle content and format are conflated, generated references drift, or verification needs a package feed publication.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — All packages build locally at alpha.2, package archives and bundle bytes inspect exactly, representative generated hosts reference alpha.2, and the drift detector reports no active product-release mismatch.

### `PKAV-W050`

Move canonical design capabilities to the alpha design-flow contracts, regenerate exact provider wrappers and bundle entries, and prove clean isolated initialization plus refresh without authoring-root activation or manual repair.

- Sequence: `50`
- Kind: `product`
- Depends on: `PKAV-W040`
- Planned output: `pkid:plan-output:program-kit:pkav-w050@0.1.0-alpha.1`

Allowed edits:

- .agent-capabilities canonical design-software and design-csharp-build-gate definitions
- .agent-capabilities thin Codex and Claude provider-adapter templates, index, supporting resources, and bundle manifest
- bounded capability catalog, bundle, initialization, ownership-lock, refresh migration, and authoring-deny code
- isolated capability fixtures, tests, and contributor-facing contract-version guidance

Compatibility:

- `pkid:capability:program-kit:design-software` accepts `0.1.0-alpha.2`: Procedure authority is preserved while exact design, plan, and disposition contract references move to alpha revisions.
- `pkid:capability-bundle:program-kit:capabilities` accepts `0.1.0-alpha.2`: Content release matches every packaged Program Kit component; existing exact owned installations migrate only through explicit initialization.

Stop condition: Stop if capability authority changes, wrapper semantics are copied, the bundle is stale, refresh overwrites unowned or drifted files, manual fixes are required, or the Program Kit authoring workspace can activate source capabilities.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — Catalog and bundle digests, thin-wrapper drift checks, absent/existing/current/drifted installation fixtures, ownership-lock migration, no-global-writes, and authoring-root denial pass.

### `PKAV-W060`

Produce and validate a separate Architecture Design 0.1.0-alpha.2, Implementation Plan 0.1.0-alpha.3, and StaticConformanceDisposition 0.1.0-alpha.1 review set for the deferred Program Kit health concerns, then stop for exact human approval.

- Sequence: `60`
- Kind: `product`
- Depends on: `PKAV-W050`
- Planned output: `pkid:plan-output:program-kit:pkav-w060@0.1.0-alpha.1`

Allowed edits:

- One new bounded extensions review directory for installed-bundle refresh, .contributors setup, Console reachability, public analyzers, and JTest handoff planning
- Read-only inspection of implemented transition source and existing approved designs
- Canonical alpha design, plan, disposition, deterministic Markdown projections, validation report, and exact review manifest

Compatibility:

- `pkid:review-set:program-kit:program-kit-health` accepts `0.1.0-alpha.1`: Uses only the newly active alpha design-flow contracts and grants no implementation authority before exact approval.

Stop condition: Stop if the follow-on review uses legacy design-flow contracts, omits any approved health concern, mutates JTest, implements behavior, or lacks exact human-decision boundaries.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — The alpha review set validates, binds exact digests, covers every deferred concern, and is presented for a separate human approval without implementation.

### `PKAV-W070`

Close the transition with exact inventory, migration, package, bundle, capability-isolation, test, diff, and follow-on review evidence while leaving publication and consumer migration unperformed.

- Sequence: `70`
- Kind: `closure`
- Depends on: `PKAV-W060`
- Planned output: `pkid:plan-output:program-kit:pkav-w070@0.1.0-alpha.1`

Allowed edits:

- Version-transition conformance fixtures and expected bytes
- Local package and generated-host inspection evidence
- Capability bundle and isolated initialization evidence
- Transition implementation closure evidence and bounded documentation corrections

Compatibility:

- `pkid:evidence:program-kit:alpha-version-transition-closure` accepts `0.1.0-alpha.1`: Binds the exact implemented transition, complete verification results, and explicitly deferred publication and consumer work.

Stop condition: Stop on any failing gate or test, incomplete inventory or migration, changed protected history, version drift, stale digest, source capability activation, missing follow-on review, publication attempt, JTest mutation, or material design deviation.

Verification: `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` — Locked restore, private gate, full solution build and tests, migration and schema suites, package and generated-host inspection, bundle verification, isolated initialization, changed-file review, and closure evidence all pass.

## Static conformance

- State: `reuse-existing`
- Disposition: `pkid:static-conformance-disposition:program-kit:alpha-version-transition@1.0.0`
- Gate: `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`
- Selection lock: `pkid:selection-lock:program-kit:alpha-version-transition-private-gate@0.1.0-alpha.1`
- Activation evidence: `pkid:evidence:program-kit:reusable-csharp-build-gates-closure@1.0.0`

Every work unit binds the exact private Program Kit activation matrix and exhaustive verification profile. No gate-establishment unit is needed.

## Approval boundary

This plan is ready for one exact human decision. Approval of recommendations does not approve these later-produced bytes. Implementation must stop on material deviation and the follow-on health review must stop again for approval.

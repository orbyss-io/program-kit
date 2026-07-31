# Program Kit reusable consumer-owned C# build gates implementation plan

- Plan identity:
  `pkid:plan:program-kit:reusable-csharp-build-gates@1.0.0`
- Design:
  `pkid:design:program-kit:reusable-csharp-build-gates@1.0.0`
- State: ready for human decision after validation
- Authority: implementation remains blocked pending exact human approval
- Candidate static-conformance disposition: `reuse-existing`
- Selected implementation gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`

## 1. Execution contract

This is a design-time plan, not implementation authority. After exact human
approval, `implement-software-plan` executes one bounded work unit at a time,
under the current Program Kit-private gate, and stops on any material
architecture deviation.

For this Program Kit extension, the existing private gate is already active, so
the plan does not need a bootstrap gate-establishment unit before W010. The
extension being implemented must make future consumer plans obey the following
rule:

- `reuse-existing` requires a compatible exact selection lock at preflight;
- `create-new` and `extend-existing` permit only their approved
  `gate-establishment` units until the new or changed gate is proven, bound, and
  activated;
- every dependent `product` unit follows successful gate establishment;
- `not-justified` requires the exact human-accepted empty disposition; and
- `blocked-unavailable` stops.

A future consumer gate-establishment fragment may contain one or several
bounded units. They are the earliest units allowed to mutate that consumer's C#
implementation and all precede affected product work.

## 2. Requirements

| ID | Required observable outcome |
| --- | --- |
| `PKCG-R001` | `Orbyss.ProgramKit.CSharpGate`, `PKCS...` diagnostics, private profiles, allow lists, warning ledger, and exceptions remain Program Kit-repository policy and never execute on consumer-owned source. |
| `PKCG-R002` | A consumer-owned gate composes only exact selected components of kind `compiler-baseline`, `program-kit-public-contract`, or `consumer-owned`, with the consumer owning selection and activation. |
| `PKCG-R003` | Public Program Kit contract-conformance rules retain their Program Kit source-contract owner, stable `PKCC...` diagnostic meaning, compatibility, and fixtures; consumers cannot copy or redefine those diagnostics. |
| `PKCG-R004` | Consumer-specific rules, diagnostics, analyzer source, profiles, compatibility, and lifecycle remain consumer-owned and use collision-free consumer diagnostic identities. |
| `PKCG-R005` | Every Architecture v2 formal design carries exactly one exact `StaticConformanceDisposition`; missing, `null`, defaulted, and implicit-empty values are invalid. |
| `PKCG-R006` | `not-justified` is valid only with an exact empty selection, rationale, residual risks, non-static claims, and explicit human acceptance; `blocked-unavailable` blocks implementation. |
| `PKCG-R007` | `design-software` enumerates static invariants, proposes a disposition, asks the human when no selection/accepted empty exists, and starts `design-csharp-build-gate` only after an explicit create/extend instruction. |
| `PKCG-R008` | Gate definitions bind semantic owner, source contract, analyzer kind, analyzer assets, rules, diagnostics, profiles, generated inputs, suppressions, compatibility, fixtures, budgets, and evidence. |
| `PKCG-R009` | Every selected analyzer component has a finite digest-bound activation matrix over exact projects, inputs, commands, implementation boundaries, and verification profiles. |
| `PKCG-R010` | Temporary activation exceptions are typed, finite, exact-scope, human-authorized, risk/evidence/expiry bound, fail closed, and emit one non-execution receipt per affected compilation. |
| `PKCG-R011` | Suppression ledgers preserve rule-owner suppressibility policy and consumer-owned project/source approval; malformed, stale, widened, expired, duplicate, unknown, and unconsumed entries fail. |
| `PKCG-R012` | Physical, consumer-generated, Program Kit-generated, SDK/compiler-generated, third-party-generated, additional-file, and analyzer-configuration inputs have exact non-forgeable ownership and inventory semantics. |
| `PKCG-R013` | Selection locks bind all contracts, rules, analyzers, packages, assemblies, toolchains, matrices, exceptions, suppressions, inputs, operations, and expected receipt identities by exact revision and digest. |
| `PKCG-R014` | Every applicable analyzer assembly emits its own same-assembly nonce/project/profile-bound participation receipt; mechanics reconcile validated and executed compiler inputs before and after compilation. |
| `PKCG-R015` | Bootstrap builds locally owned analyzers twice from controlled source without trusting stale/self-produced bytes, validates packaged public analyzers against owner evidence, runs the combined corpus, self-validates, and proves automatic invocation before product work. |
| `PKCG-R016` | Gate updates keep the old accepted gate active until replacement compatibility, migration, deterministic build, fixtures, receipts, selection lock, rollback boundary, and activation evidence pass. |
| `PKCG-R017` | Five finite deterministic operations exist: `validate-definition`, `render-definition`, `scaffold`, `bind`, and `verify`; none scans, downloads, discovers plugins, executes arbitrary assemblies, or becomes a general process runner. |
| `PKCG-R018` | Public analyzer packages are narrow owner-contract companions, analyzer-only, direct opt-in, private-assets selections with no `lib/`, `ref/`, runtime, or `buildTransitive` activation. |
| `PKCG-R019` | Program Kit authoring helpers and recipes contain no analyzer/generator registrations; recipes transfer selected bindings to consumer ownership, while public contract analyzers retain Program Kit semantic ownership. |
| `PKCG-R020` | Every existing `PKCS` rule is classified as private policy, public-contract candidate, optional recipe, standard baseline/mechanics, or non-Roslyn claim before reuse; extraction uses a new public contract and diagnostic identity. |
| `PKCG-R021` | Compiler-backed proof composes at least one narrow `PKCC...` public contract analyzer and one fictional consumer-owned analyzer in the same consumer gate and rejects private analyzer leakage, unrelated activation, copied ownership, and diagnostic collisions. |
| `PKCG-R022` | Planning v3 binds the exact disposition, gate definition/design/lock, work-unit kind, activation matrix, and verification profile and validates establishment-before-product dependency ordering. |
| `PKCG-R023` | `implement-software-plan` permits only approved gate-establishment units while a create/extend lock is absent, then runs applicable gates for preflight, each product unit, generated output, and final closure. |
| `PKCG-R024` | Gate defect, ambiguous public or consumer rule, incompatible lock, changed activation, invalid exception, unapproved suppression, unavailable mechanics, or architecture conflict stops implementation instead of becoming a source fix or bypass. |
| `PKCG-R025` | `design-csharp-build-gate@1.0.0` remains unavailable until all backing contracts, operations, packages, fixtures, migrations, and proof pass; no separate implementation capability is created. |
| `PKCG-R026` | Capability integration updates canonical `design-software` and `implement-software-plan`, exact Codex/Claude adapter templates, initializer ownership, index/catalog, and CapabilityBundle `2.1.0` only through `author-and-maintain-skills`. |
| `PKCG-R027` | Architecture v1 and Planning v2 remain readable through deterministic explicit migrations to Architecture v2 and Planning v3; independent clocks and all dependency edges appear in the Version Map. |
| `PKCG-R028` | Fixtures cover positive, negative, generated-input, suppression, exception, tamper, package, runtime-closure, isolated-consumer, repeatability, cancellation, teardown, performance, migration, and clean-checkout behavior. |
| `PKCG-R029` | The Domain Semantic Engine-like proof uses a non-packable consumer-owned analyzer, may select exact public Program Kit contract analyzers, and never imports the private Program Kit analyzer or gains a general code generator. |
| `PKCG-R030` | Existing exhaustive private-gate proof remains unchanged; migrating the private gate onto reusable mechanics remains blocked pending a separate equivalence design and approval. |
| `PKCG-R031` | Durable evidence is deterministic, redacted, exact-input bound, phase/layer classified, and cannot become approval or claim semantic/runtime correctness beyond observed fixtures. |
| `PKCG-R032` | All new gate, analyzer, build, testing, capability, and provider-adapter assets remain isolated from Program Kit and consumer runtime/package dependency closures. |

## 3. Work units

### `PKCG-W010` — Architecture v2 and static-conformance disposition

**Kind:** product

**Depends on:** none

**Allowed edits:** `src/Orbyss.ProgramKit.Architecture/`,
`schemas/architecture/`, architecture unit/conformance tests, exact migration
fixtures, package documentation, and the Version Map entries owned by this
unit.

**Required outcomes:** add
`StaticConformanceDisposition@1.0.0`, exact selected-gate/linked-gate-design
references, invariant/layer allocation, residual-risk and non-static-claim
contracts, and Architecture Design `2.0.0`. Validate every disposition
cardinality and state combination. `not-justified` requires the exact
human-accepted empty form; `blocked-unavailable` cannot masquerade as empty.
Provide deterministic v1-to-v2 migration that requires a supplied human
decision rather than inventing a disposition.

**Verification:** focused Architecture tests; schema/model conformance;
valid reuse/create/extend/explicit-empty fixtures; invalid missing, `null`,
implicit-empty, unaccepted-empty, and blocked-as-empty fixtures; deterministic
normalization/digest; migration repeatability; current Program Kit private gate
passes.

**Stop conditions:** any migration defaults a human decision, approval is
stored as a Boolean/future digest, v1 bytes are rewritten in place, or the
architecture package acquires Roslyn/MSBuild/runtime-host dependencies.

### `PKCG-W020` — Planning v3 and establishment-first ordering

**Kind:** product

**Depends on:** `PKCG-W010`

**Allowed edits:** `src/Orbyss.ProgramKit.Planning/`, `schemas/planning/`,
planning tests and migrations, the host-tooling plan materializer only if a
v3 migration fixture requires it, and Version Map entries owned by this unit.

**Required outcomes:** add Implementation Plan `3.0.0` fields for exact static
disposition, gate design/definition/selection lock, work-unit kind
`gate-establishment|product|closure`, activation-matrix/profile references, and
dependency validation. Create/extend plans may run only their exact
gate-establishment units until compatible activation evidence exists. Reuse
requires a compatible lock at preflight; explicit empty requires its exact
accepted disposition; blocked stops.

**Verification:** focused Planning tests; v2-to-v3 deterministic migration;
single and multi-unit gate establishment; invalid product-before-gate,
closure-before-product, missing profile, stale lock, blocked, and implicit-empty
fixtures; exact trace coverage; current private gate passes.

**Stop conditions:** the model infers ordering from file names or sequence
alone, permits product mutation before establishment, introduces a second plan
execution authority, or fabricates an accepted disposition.

### `PKCG-W030` — C# build-gate contracts and schemas

**Kind:** product

**Depends on:** `PKCG-W010`, `PKCG-W020`

**Allowed edits:** new
`src/Orbyss.ProgramKit.CSharpBuildGates.Contracts/`, its schemas,
tests/fixtures, solution/central package registration, documentation, and
Version Map entries owned by this unit.

**Required outcomes:** implement versioned gate definition, analyzer-component,
semantic-owner, rule catalog, diagnostic catalog, project/input/generated
profiles, activation matrix, temporary activation exception, suppression
ledger, selection lock, participation receipt, evidence, compatibility,
migration, threat, fixture, and performance contracts. Register only finite
typed values and deterministic validators. Reserve `PKCS`, `PKCC`, and `PKCG`
according to the design and reject collisions or copied semantic ownership.

**Verification:** schema/model round trips; stable ordering; exact-path and
digest validation; ownership/cardinality matrices; exception fail-closed
fixtures; suppression reconciliation; generated-source forgery cases;
serialization limits; deterministic normalization/digest; package dependency
and runtime-closure checks.

**Stop conditions:** arbitrary conditions/scripts, globs as authority,
environment discovery, assembly scanning/loading, mutable registries, runtime
dependencies, universal Program Kit policy, or consumer reassignment of public
diagnostic meaning.

### `PKCG-W040` — Existing-rule classification and narrow public analyzers

**Kind:** product

**Depends on:** `PKCG-W030`

**Allowed edits:** a machine-readable `PKCS` classification ledger; exact new
public strict-C#/generated-source contract documents and schemas; narrowly
named `Orbyss.ProgramKit.<Contract>.Analyzers` projects justified by those
contracts; analyzer fixtures; private-gate tests required to prove no
regression; package registration and Version Map entries owned by this unit.

**Required outcomes:** classify every current `PKCS` rule with rationale and
owner. Keep private repository/project/layout/behavior/warning-exception
semantics private. Create only the minimum public `PKCC...` rules backed by an
exact public Program Kit contract and compilation-observable claim. Give each
public analyzer an analyzer-only package, stable diagnostics, exact
compatibility, same-assembly receipt generator, positive/negative/suppression/
performance fixtures, and direct-selection documentation. Do not delete or
weaken the private rule during this work unit.

**Verification:** classification completeness; private/public ownership tests;
semantic equivalence where research is extracted; independent public package
inspection; unrelated-profile negative controls; private analyzer regression;
diagnostic collision tests; no runtime/buildTransitive assets; current private
gate passes.

**Stop conditions:** a private `PKCS` diagnostic is published, a new public rule
lacks an owning contract, unrelated rules are aggregated, private enforcement
is weakened, or Roslyn is used for a claim it cannot establish.

### `PKCG-W050` — Authoring primitives, recipes, and consumer scaffolding

**Kind:** product

**Depends on:** `PKCG-W030`, `PKCG-W040`

**Allowed edits:** new
`src/Orbyss.ProgramKit.CSharpBuildGates.Authoring/`, inert recipe catalogs and
templates, scaffolding models/tests, package registration, and Version Map
entries owned by this unit.

**Required outcomes:** provide deterministic non-analyzer Roslyn helpers,
optional versioned recipes, receipt-generator source template, fictional
consumer analyzer/test templates, and explicit public-analyzer selection
projections. Recipe adoption requires consumer rule/diagnostic/parameter/
profile/fixture/compatibility/suppression bindings. Scaffolding is
transactional and never invents consumer semantics or copies `PKCC`
diagnostics.

**Verification:** package type inspection proves no `DiagnosticAnalyzer`,
source-generator, or incremental-generator registrations; golden scaffold
bytes; collision/path/traversal/existing-file failures; cancellation and
rollback; recipe ownership tests; clean consumer compilation.

**Stop conditions:** authoring assets auto-run as policy, templates embed
private `PKCS` rules, public diagnostics transfer to consumer ownership,
scaffolding overwrites unowned files, or Roslyn leaks into runtime closure.

### `PKCG-W060` — Direct build integration, activation, and receipts

**Kind:** product

**Depends on:** `PKCG-W030`, `PKCG-W040`, `PKCG-W050`

**Allowed edits:** new `Orbyss.ProgramKit.CSharpBuildGates.Build` package,
direct props/targets/tasks, build contracts/tests/fixtures, package
registration, and Version Map entries owned by this unit.

**Required outcomes:** attach exact selected public and consumer-owned analyzer
assemblies as analyzer-only inputs; validate exact project/input inventories;
control compiler/analyzer execution; evaluate finite activation matrices and
typed temporary exceptions; require one same-assembly nonce/project/profile
receipt per applicable analyzer; reconcile compiler inputs before/after
compilation; emit exception-use receipts; enforce build/test/pack/publish/
generated-project and implementation-boundary profiles.

**Verification:** automatic-invocation proof for every command; analyzer
removal/duplication/substitution/disable/demotion/stale-byte cases; source,
generated, additional-file, config, reference, ruleset, lock, matrix, receipt,
condition, suppression, and post-validation mutation; valid/invalid exception
matrix; package inspection; isolated consumer; current private gate passes.

**Stop conditions:** `buildTransitive`, runtime assets, ambient discovery,
warning-only failure, missing receipt accepted as success, one analyzer receipt
standing in for another, arbitrary skip input, or explicit verification
substituting for normal build invocation.

### `PKCG-W070` — Operations and compiler-backed testing

**Kind:** product

**Depends on:** `PKCG-W030`, `PKCG-W050`, `PKCG-W060`

**Allowed edits:** new
`src/Orbyss.ProgramKit.CSharpBuildGates.Testing/`; registered Workbench
operation implementations; finite CommandLine grammar/adapters; operation,
compiler, fixture, cancellation, teardown, and evidence tests; package and
Version Map entries owned by this unit.

**Required outcomes:** back `validate-definition`, `render-definition`,
`scaffold`, `bind`, and `verify`. Validation loads no analyzer code. Binding
uses exact local/package assets without restore/network/discovery. Verification
uses only pinned finite `dotnet`/compiler/MSBuild templates and emits typed
layered evidence. Compiler harness compares deterministic diagnostics,
receipts, exception uses, package closure, cancellation, performance, and
teardown.

**Verification:** operation golden files; schema/semantic/render freshness;
offline/no-network proof; I/O and commit-boundary failures; cancellation races;
process teardown; deterministic cross-path outputs; unknown command/profile
failures; serialization/redaction limits; no arbitrary executable/argument
surface.

**Stop conditions:** a general process runner, package/feed lookup, assembly
execution during validation/binding, scanner/plugin architecture, nondeterministic
render/evidence, or CLI-owned semantics.

### `PKCG-W080` — Composed fictional consumer and adversarial proof

**Kind:** product

**Depends on:** `PKCG-W040`, `PKCG-W050`, `PKCG-W060`, `PKCG-W070`

**Allowed edits:** exact fictional consumer fixtures under conformance-test
ownership, generated temporary workspaces, fixture manifests/locks, and
redacted expected evidence. No production consumer or sibling repository.

**Required outcomes:** establish one consumer-owned gate containing an exact
public `PKCC...` analyzer and a separate fictional consumer-owned analyzer.
Prove distinct semantic ownership, deterministic combined diagnostics,
collision rejection, exact applicability, per-analyzer receipts, suppressions,
temporary exceptions, bootstrap/self-validation, update/rollback, automatic
commands, explicit implementation boundaries, and zero runtime/package leakage.

**Verification:** clean package-only and local-project consumers; positive and
one negative fixture per rule/mechanic; private analyzer attachment; unrelated
public analyzer; missing owner contract; copied `PKCC`; diagnostic collision;
analyzer/order changes; all tamper and exception cases; repeat clean/incremental
and cross-path runs; cancellation/teardown; focused/final performance budgets.

**Stop conditions:** the fictional consumer imports private Program Kit policy,
public semantics are duplicated, one component can conceal another, evidence
contains source/secrets/absolute paths, or a green direct verifier hides failed
automatic build activation.

### `PKCG-W090` — Canonical capability integration

**Kind:** product

**Depends on:** `PKCG-W010` through `PKCG-W080`

**Allowed edits:** only through the explicitly invoked
`author-and-maintain-skills` flow: canonical `design-software`,
`design-csharp-build-gate`, and `implement-software-plan`; capability index,
catalog, bundle manifest/content; existing registered Codex and Claude adapter
templates; initializer fixtures/locks; capability conformance tests and docs.

**Required outcomes:** make the disposition question mandatory in
`design-software`; add human-started `design-csharp-build-gate@1.0.0` with an
exact gate-establishment plan fragment; update `implement-software-plan` for
v3 establishment-first execution and applicable gate runs. Keep
`design-csharp-build-gate` unavailable until the same work unit proves all
backing and atomically registers CapabilityBundle `2.1.0`. Add no separate
implementation capability.

**Verification:** canonical capability validation; wrapper thinness/exact
pointers; missing-wrapper blocker; index/catalog/bundle parity and digests;
initializer ownership and tamper cases; explicit human-start tests; no silent
subflow, implementation, activation, empty acceptance, exception renewal, or
approval; runtime/dependency isolation.

**Stop conditions:** capability semantics are authored outside the backed flow,
availability precedes evidence, a wrapper becomes source truth, provider
semantics diverge, installation grants authority, or a second implementation
authority is introduced.

### `PKCG-W100` — Versioning, migration, and Engine-like consumer proof

**Kind:** product

**Depends on:** `PKCG-W080`, `PKCG-W090`

**Allowed edits:** Version Map and migration manifests/fixtures; extension
documentation; a repository-local fictional Engine-like generated consumer
fixture; package manifests/locks; no Domain Semantic Engine repository edits.

**Required outcomes:** complete independent clocks and compatibility edges for
Architecture v2, Planning v3, disposition, gate contracts, public analyzers,
consumer analyzers, recipes, build mechanics, operations, capabilities, bundle,
toolchain, locks, and evidence. Prove an Engine-like non-packable
consumer-owned analyzer can adopt a recipe and select a public Program Kit
contract analyzer without private policy, runtime leakage, or a general code
generator.

**Verification:** migration matrices; mixed/partial/stale/floating selection
failures; exact package locks; clean-checkout offline proof; generated consumer
build/test/pack/publish and final verification; runtime/package closure;
terminology scan permits only `consumer-owned analyzer` for consumer-specific
policy; current private gate passes.

**Stop conditions:** sibling-repository edits, inferred Engine semantics,
floating versions, partial bundle/migration, private analyzer use, or general
source-generation authority.

### `PKCG-W110` — Exhaustive closure and review evidence

**Kind:** closure

**Depends on:** `PKCG-W010` through `PKCG-W100`

**Allowed edits:** focused defects within already approved work-unit scopes;
closure manifests, redacted verification evidence, documentation freshness,
and exact review/implementation evidence indexes. No architectural expansion.

**Required outcomes:** run all unit, conformance, package, operation, migration,
capability, composition, generated-consumer, deterministic, cancellation,
tamper, performance, clean-checkout, and runtime-closure profiles. Run the
unchanged exhaustive private C# gate plan. Confirm the private gate has not
been migrated and every capability/package is backed and exact.

**Verification:** clean restore/build/test/pack/publish; exhaustive private gate
test plan; two clean-path executions with equal canonical outputs/evidence;
all negative fixtures fail at their declared layer; no sensitive/absolute-path
evidence; package/runtime closure; capability bundle verification; design/plan/
manifest digest reconciliation; repository status contains only approved
implementation outputs.

**Stop conditions:** any failed/skipped/stale fixture, performance regression,
private-gate regression, public/consumer diagnostic ambiguity, residual
process/temp state, runtime leakage, unbacked capability, changed architecture,
or incomplete trace/evidence.

## 4. Requirement trace

| Work unit | Requirements |
| --- | --- |
| `PKCG-W010` | R005, R006, R027, R031 |
| `PKCG-W020` | R005, R006, R022, R023, R024, R027 |
| `PKCG-W030` | R002–R004, R008–R014, R016, R027, R031, R032 |
| `PKCG-W040` | R001–R004, R014, R018, R020, R030, R032 |
| `PKCG-W050` | R004, R008, R014, R019, R032 |
| `PKCG-W060` | R001–R004, R009–R014, R016, R018, R024, R028, R031, R032 |
| `PKCG-W070` | R008–R019, R024, R027, R028, R031, R032 |
| `PKCG-W080` | R001–R004, R009–R016, R018–R021, R024, R028, R031, R032 |
| `PKCG-W090` | R005–R007, R022–R027, R032 |
| `PKCG-W100` | R001–R004, R018–R021, R027–R032 |
| `PKCG-W110` | R001–R032 |

Every requirement is implemented before closure and independently rechecked by
W110. A work unit may split into smaller commits but may not merge with another
unit if that would weaken its verification or stop boundary.

## 5. Deliberately deferred

- Migration of `Orbyss.ProgramKit.CSharpGate` onto the new mechanics.
- Public analyzers for Program Kit contracts without an exact
  compilation-observable invariant and owner.
- A general Program Kit metadata/annotation/compiler abstraction.
- A language-neutral gate framework.
- Live package-feed lookup or automatic analyzer acquisition.
- Any Domain Semantic Engine implementation.

Each requires a separate human-started design if later justified.

## 6. Approval boundary

Approval must bind the exact final digests of:

- `design-intent.md`;
- `architecture-design.json`;
- `architecture-design.md`;
- `static-conformance-disposition.md`;
- `implementation-plan.json`;
- `implementation-plan.md`;
- `prior-draft-assessment.md`;
- `validation-report.md`; and
- `review-manifest.json`.

Approval authorizes only W010–W110 under their dependencies, allowed edits,
verification, and stop conditions. It does not approve a consumer gate, an
empty consumer selection, a temporary exception, private-gate migration, or
Domain Semantic Engine implementation.

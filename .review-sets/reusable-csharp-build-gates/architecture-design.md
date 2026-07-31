# Program Kit reusable consumer-owned C# build gates

- Design identity:
  `pkid:design:program-kit:reusable-csharp-build-gates@1.0.0`
- Review state: ready for human decision after validation
- Implementation state: not started
- Authority: design only
- Initial toolchain scope: C# 14, .NET 10 SDK, Roslyn, and MSBuild

## 1. Outcome

Program Kit will provide reusable mechanics for designing, implementing,
attaching, invoking, verifying, and maintaining consumer-owned C# build gates.
It will not provide a universal Program Kit policy analyzer for consumer code.

Four owners remain distinct:

1. Program Kit owns generic C#/.NET gate contracts, deterministic operations,
   build assurance, scaffolding, authoring primitives, optional rule recipes,
   test mechanics, and evidence.
2. `design-software`, `design-csharp-build-gate`, and
   `implement-software-plan` own their human-led procedures and authority
   boundaries.
3. Each consumer owns its composed gate, exact analyzer selections,
   project/source profiles, exceptions, suppressions, compatibility, and
   activation matrix. It also owns its consumer-specific analyzer assemblies,
   rule meanings, and diagnostic identities.
4. Each public Program Kit contract owner owns the invariant and diagnostic
   meaning of its narrow contract-conformance analyzer rules.
5. `Orbyss.ProgramKit.CSharpGate`, its `PKCS...` diagnostics, source profiles,
   allow lists, and warning ledger remain Program Kit-private policy.

Only explicitly selected analyzer components run on consumer-owned source:
standard compiler/analyzer baselines, narrow Program Kit public
contract-conformance analyzers for exact selected contracts or profiles, and
consumer-owned analyzers for consumer-specific policy. Program Kit build
mechanics execute around compilation to prove attachment, inventory,
participation, applicability, tamper resistance, and evidence. Those mechanics
are not a second policy analyzer.

## 2. Current source-truth finding

The implemented Program Kit gate demonstrates useful mechanics:

- mandatory analyzer attachment;
- physical `Compile` inventory comparison;
- Program Kit-owned generated-source classification;
- warnings, nullable, analysis, language, framework, and compiler-control
  validation;
- exact source, analyzer, reference, additional-file, and analyzer-config
  reconciliation before and after compilation;
- a same-assembly compiler participation receipt;
- a typed, source-local suppression ledger;
- bootstrap/self-validation and exhaustive mutation fixtures;
- stable diagnostics;
- clean/incremental and generated-project coverage; and
- build/test/pack/publish enforcement.

Its policy is not reusable as-is. The following remain private:

- `PKCS...` diagnostic meanings;
- Program Kit namespace, folder, project, test-mirroring, behavioral,
  construction, dependency, and source-layout rules;
- Program Kit warning quarantines;
- `ProgramKitGenerated` ownership conventions;
- exact FastEndpoints and Program Kit project exceptions;
- Program Kit target-profile and work-unit properties; and
- Program Kit's repository paths and allow lists.

The current analyzer is a monolith that combines private policy, potentially
reusable public-contract checks, optional conventions, baseline enforcement,
and generic mechanics. Implementation must classify every existing `PKCS`
rule before extracting anything:

1. repository-private policy remains in `Orbyss.ProgramKit.CSharpGate`;
2. an already justified public Program Kit invariant moves only into a narrow
   public contract-conformance rule with a new public diagnostic identity,
   compatibility contract, and equivalent fixtures;
3. an optional convention becomes an inert recipe only;
4. compiler/build baseline enforcement belongs to the selected standard
   profile or generic mechanics; and
5. a claim Roslyn cannot establish remains in schema validation, architecture
   tests, compiler fixtures, or executable conformance tests.

Implementation of this extension creates new generic mechanics, proves
composition with both a public Program Kit contract-conformance analyzer and a
consumer-owned analyzer, and preserves exhaustive regression evidence for the
private analyzer. It does not package or import the private analyzer into
consumer builds.

## 3. Static-conformance disposition contract

### Required architecture field

`pkid:schema:program-kit:architecture-design` advances from `1.0.0` to
`2.0.0`. Every v2 design requires an exact reference named
`staticConformanceDisposition` to
`pkid:schema:program-kit:static-conformance-disposition@1.0.0`.

The disposition artifact is independently versioned because it has a richer
lifecycle than one enum and must be presented before the complete design review
set is finalized. Its exact reference carries identity, version, and SHA-256.
The architecture design does not contain an approval flag or a future approval
digest.

The disposition contains:

- exact software-design identity and revision;
- enumerated statically decidable invariants;
- allocation across language/type-system, project/package, Roslyn/compiler,
  MSBuild, architecture-test, executable-test, and human-review layers;
- exactly one disposition:
  `reuse-existing`, `extend-existing`, `create-new`, `not-justified`, or
  `blocked-unavailable`;
- an ordered `gateSelections` set;
- exact activation-matrix references for every selection;
- residual risks;
- claims that cannot be statically proven;
- the human-supplied disposition decision source; and
- optional exact linked C# gate-design references.

The decision source records the human instruction that selected the candidate
for incorporation; it does not claim architecture approval. The later normal
design/plan approval binds the final architecture and plan bytes.

### Empty selection

- `not-justified` requires `gateSelections: []`, a non-empty rationale,
  residual risks, and explicit human acceptance of the empty selection.
- `reuse-existing`, `extend-existing`, and `create-new` require at least one
  exact selected gate or exact linked gate design.
- `blocked-unavailable` requires non-empty blockers and prevents
  implementation.
- missing, `null`, defaulted, or implicitly empty values are invalid.

### Program Kit extension's own disposition

This review set proposes `reuse-existing` for implementation of the Program Kit
extension itself: the existing Program Kit-owned gate policy
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0` continues to run on
Program Kit-owned source through the repository-owned
`Orbyss.ProgramKit.CSharpGate` project and current exact build spine.

This selection does not migrate the private gate onto the new mechanics and
does not make it available to consumers. Residual risks include the current
single-repository MSBuild trust boundary, the monolithic policy/mechanics
implementation, and claims beyond compilation observability.

## 4. `design-software` integration

Before finalizing any Program Kit-backed software review set,
`design-software` must:

1. enumerate static invariants;
2. allocate each invariant to the narrowest reliable enforcement layer;
3. inspect exact accepted gate selections and their availability;
4. create exactly one candidate disposition;
5. state residual risks and non-static claims;
6. present the candidate to the human;
7. stop when no accepted selection and no accepted empty selection exists; and
8. incorporate the exact human-selected disposition reference into the final
   design.

When no suitable gate exists, the prompt is semantically:

> This design has no accepted layered build gate and no accepted empty
> selection. Should this design reuse, extend, create, or explicitly proceed
> without a consumer-owned gate?

An explicit `create-new` or `extend-existing` response starts
`design-csharp-build-gate` in the same human-led design session. Silence,
timeout, installation, copied files, or capability availability never starts
it.

## 5. `design-csharp-build-gate`

The new provider-neutral capability owns detailed C#/.NET/Roslyn/MSBuild gate
design after the human starts it. It produces:

- a versioned consumer-owned gate definition;
- rule and diagnostic catalogs;
- project, physical-source, additional-file, analyzer-configuration, and
  generated-source profiles;
- a finite activation matrix;
- suppression and authority rules;
- bootstrap, update, self-validation, and threat models;
- positive, negative, generated-source, tamper, packaging,
  isolated-consumer, repeatability, cancellation, and performance fixtures;
- compatibility and migration requirements; and
- a linked gate-establishment implementation-plan fragment.

It does not implement, approve, activate, or weaken a gate. It does not assign
consumer semantics, start itself silently, or claim static success proves
semantic correctness.

There is no separate gate-implementation capability.

## 6. Consumer-owned gate definition

`pkid:schema:program-kit:csharp-build-gate-definition@1.0.0` defines:

### Identity and ownership

- consumer gate identity, semantic version, revision digest, and owner;
- consumer policy identity and compatibility policy;
- exact analyzer components, each consumer-owned;
- exact supported SDK, compiler/Roslyn, C# language, target framework, and
  Program Kit mechanics ranges; and
- local non-packable project or exact analyzer-package selection.

The Domain Semantic Engine candidate uses a repository-local non-packable
project. A packaged analyzer is optional for other consumers.

### Rule catalog

Every rule declares:

- rule kind: `program-kit-public-contract` or `consumer-owned`;
- semantic owner, source contract, rule identity, and stable diagnostic ID;
- title, category, default severity, rationale, and remediation;
- exact compilation-observable claim;
- layer allocation and claims deliberately outside the rule;
- applicable project/source profiles;
- suppression disposition;
- positive and negative fixture identities;
- compatibility, migration, deprecation, retirement, and supersession; and
- deterministic location/message and performance budgets.

A diagnostic ID never changes meaning. Program Kit reserves `PKCS` for its
private gate, `PKCC` for public Program Kit contract-conformance diagnostics,
and `PKCG` for Program Kit mechanics/operation failures. Consumer policy
diagnostics use consumer-owned collision-free prefixes.

### Public Program Kit contract-conformance analyzers

A public Program Kit rule is selected only when:

- its exact owning public contract/profile and analyzer revision are selected;
- the consumer's exact project/input/command/boundary/profile matrix applies;
- its compilation-observable claim is still owned by that public contract;
- its exact package or local assembly, catalog, and fixtures are locked; and
- no valid typed temporary activation exception applies.

Using Program Kit tooling or one unrelated Program Kit package never activates
all public Program Kit rules. Public contract analyzers use analyzer-only
packages, have no `lib/` or `ref/` runtime assets, are referenced explicitly
with private assets, and never use `buildTransitive`.

The initial implementation classifies every `PKCS` rule. It establishes a
small public strict-C#/generated-source contract-conformance proof only for
invariants that receive an explicit public contract and equivalent positive,
negative, compatibility, suppression, receipt, and performance fixtures.
Private Program Kit layout, behavioral, project, allow-list, warning-ledger,
and exception semantics do not cross that boundary.

### Optional Program Kit recipes

Program Kit may publish a versioned C# rule-recipe catalog and source templates
for commonly selected maintenance patterns. Recipes contain no consumer
diagnostic identity, project allow list, activation, or authority.

A consumer adopts a recipe only through an explicit binding that supplies
consumer rule identity, diagnostic identity, parameters, profiles, fixtures,
compatibility, and suppression policy. Scaffolding renders consumer-owned
analyzer source or uses non-analyzer authoring primitives. Program Kit recipe
assemblies contain no `DiagnosticAnalyzer`, source-generator, or incremental
generator registrations that could run as policy on consumer source.

Recipes differ from public contract-conformance analyzers: a recipe transfers
the selected rule binding and diagnostic ownership to the consumer; a public
contract analyzer retains Program Kit ownership of the invariant and
diagnostic.

### Project and input profiles

Profiles use finite repository-relative paths and exact identities. They define:

- projects and target frameworks;
- physical C# roots and exact exclusions;
- complete `Compile` inventory rules;
- consumer-owned generated sources;
- compiler/SDK/third-party generated-source classifications;
- additional files and analyzer configurations;
- per-rule applicability; and
- project/package dependency constraints.

No glob is an authority boundary. A validated finite expansion may be recorded
in the selection lock, but the lock contains the exact resolved paths and
digests.

### Generated source

Consumer-owned generated C# is distinguished by:

- exact generator identity, version, assembly digest, and owner;
- exact ownership marker and logical hint-path profile;
- generated-source manifest and content inventory; and
- consumer-approved rule applicability.

Program Kit-generated source becomes consumer-owned only when the generation
contract explicitly transfers ownership to that consumer. Compiler, SDK, and
third-party implementation details remain separately classified and cannot be
relabelled by a handwritten header. Physical source cannot escape analysis by
claiming to be generated.

### Suppression model

A suppression ledger binds:

- diagnostic semantic owner, diagnostic, rule revision, project, source,
  symbol or line target;
- exact suppression mechanism and scope;
- human authority reference, rationale, approval date, expiry/review condition;
- source, rule-catalog, and configuration digests; and
- migration/supersession condition.

Program Kit validates generic ledger structure and reconciliation mechanics.
The rule owner declares whether its diagnostic is suppressible; the consumer
owns every project/source-specific suppression approval within that declared
policy. Missing, stale, duplicate, widened, deactivated, expired, overbroad,
unknown, or unconsumed records fail at the suppression layer.

## 7. Activation matrix

One consumer-owned gate definition contains one or more selected analyzer
components. Each component declares `compiler-baseline`,
`program-kit-public-contract`, or `consumer-owned`, its semantic owner, exact
artifacts, and exact typed activation predicates:

| Dimension | Allowed values |
| --- | --- |
| Project | exact project identity and repository-relative path |
| Source | exact physical, consumer-generated, additional-file, and analyzer-config profile |
| Command | `build`, `test`, `pack`, `publish`, `generated-project-verify` |
| Implementation boundary | `gate-establishment`, `preflight`, `work-unit`, `generated-output`, `final-closure` |
| Verification profile | `bootstrap`, `focused`, `work-unit`, `generated-output`, `tamper`, `performance`, `final-closure` |

The matrix is conjunctive, finite, stable ordered, and digest-bound. It contains
no arbitrary expression, script, environment lookup, registration order,
folder guess, ambient discovery, or fallback. An applicable command always
runs the selected analyzer automatically. Explicit verification is additional,
not a substitute for normal build invocation.

### Temporary activation exceptions

A consumer may define a temporary exception only through a typed,
digest-bound record. This is useful when a predictable, observable condition
makes a selected gate temporarily inapplicable; it is not a general bypass.
Every exception requires:

- exact affected gate, rule, project, source, command, boundary, and
  verification-profile scope;
- one finite Program Kit-defined condition kind and typed parameters;
- a consumer owner and human authority reference;
- rationale, residual risk, compensating verification, and evidence
  requirements;
- an activation time plus an expiry time or deterministic removal trigger;
- maximum permitted uses when the condition is occurrence-bound; and
- the work unit or decision that must remove, renew, or supersede it.

Initial condition kinds are deliberately narrow: exact toolchain
incompatibility, exact target-framework incompatibility, unavailable
generated input with a separately verified producer state, and an exact
gate-establishment boundary. Condition evaluation uses already controlled,
digest-bound inputs. Unknown kinds, missing inputs, ambiguous evaluation,
expired records, widened scope, exhausted uses, changed parameters, or
unapproved renewal fail closed.

The verifier emits an exception-use receipt for every non-execution. That
receipt records the evaluated condition inputs, decision, affected
compilation, compensating verification, remaining lifetime/use count, and
exception digest. No environment-variable switch, command-line skip flag,
configuration default, warning demotion, analyzer removal, or arbitrary
Boolean expression can disable a selected gate.

Temporary exceptions are distinct from:

- `not-justified`, which is an explicit design-level acceptance of no selected
  gate;
- rule suppressions, which keep the analyzer executing and govern specific
  diagnostics; and
- gate failure or unavailability, which stops affected product work.

## 8. Selection lock and compiler participation

`pkid:schema:program-kit:csharp-build-gate-selection-lock@1.0.0` binds:

- disposition, gate definition, analyzer components, rule catalogs, recipes,
  activation matrix, suppression ledger, and operation revisions;
- local project/source or exact package/archive/assembly identities and
  SHA-256 values;
- exact SDK/compiler/Roslyn/language/framework selections;
- project, physical-source, consumer-generated-source, reference,
  additional-file, and analyzer-configuration inventories;
- expected same-assembly participation receipt identities; and
- deterministic input/output digests.

Compiler participation receipts are mandatory for every selected analyzer in
every covered compilation. A consumer-owned analyzer contains its scaffolded
receipt generator. A Program Kit public contract-conformance analyzer contains
the equivalent Program Kit-owned receipt generator. Program Kit build mechanics
clear the receipt root, generate a per-compilation nonce, compare validated and
executed compiler inputs, require one nonce/profile/project/analyzer-bound
receipt per applicable selected analyzer assembly, and recheck controlled
content after compilation.

A Program Kit helper library may support consumer-owned analyzers, but it
contains no policy analyzer registrations. Every policy analyzer identity in a
consumer compilation is an exact selected component; private Program Kit
analyzer identities are forbidden.

## 9. Bootstrap and updates

### Initial establishment

The bootstrap operation does not trust a stale analyzer, previous output, or
the candidate's self-produced evidence:

1. validate exact source, public-contract, package, toolchain, recipe, and
   dependency locks;
2. compile each locally built analyzer candidate twice in isolated clean roots
   with the pinned SDK/compiler and no candidate gate trusted as an input;
3. require deterministic assembly/content identity or a documented
   deterministic normalization boundary;
4. inspect that only declared analyzer and receipt-generator types exist;
5. run the full positive, negative, generated-source, suppression, cancellation,
   and tamper corpus against both builds;
6. require equal diagnostics and evidence;
7. run each locally owned candidate against its own source under the approved
   bootstrap profile and validate packaged public analyzers against their exact
   owner-provided conformance evidence;
8. prove the combined public-contract and consumer-owned analyzer diagnostic
   set is deterministic and collision-free;
9. bind all accepted component bytes in a selection lock; and
10. prove automatic invocation before any dependent product work.

### Updates

The current accepted gate remains active while a replacement is built. A rule
meaning change receives a new rule/diagnostic revision. The replacement passes
old/new compatibility, migration, self-validation, deterministic-build,
negative-control, and rollback-boundary evidence before the selection lock
changes. A gate defect, ambiguous rule, policy change, unapproved suppression,
or architecture conflict stops implementation.

## 10. Program Kit operations

Five deterministic operations are required:

1. `csharp-gate validate-definition` validates the exact definition, catalogs,
   profiles, matrices, suppressions, fixtures, compatibility, and layer
   allocations without loading analyzer code.
2. `csharp-gate render-definition` creates a deterministic human-readable
   projection from validated canonical bytes.
3. `csharp-gate scaffold` transactionally emits a consumer-owned analyzer
   project, selected recipe source, receipt generator, test projects, explicit
   public-contract analyzer selections, build integration, configuration, and
   ownership manifest. It never emits consumer rule meaning that the approved
   definition did not supply or copies Program Kit-owned public diagnostics
   into consumer ownership.
4. `csharp-gate bind` inspects exact local or package assets and produces the
   selection lock without restore, feed lookup, network, scanning, or arbitrary
   assembly execution.
5. `csharp-gate verify` runs an exact verification profile, bounded compiler
   and MSBuild commands, and fixtures, then emits typed evidence.

The CLI is a transport over these registered operations. The verifier accepts
only the pinned `dotnet` SDK and finite command templates; it is not a general
process runner.

## 11. Failure and diagnostic semantics

Every result identifies one failing layer:

| Layer | Examples |
| --- | --- |
| Definition | invalid consumer policy, diagnostic collision, unsupported rule or profile |
| Mechanics | missing/incompatible Program Kit build mechanics |
| Analyzer build | compilation, package, dependency, or deterministic-byte failure |
| Attachment | analyzer absent, duplicated, disabled, demoted, substituted, or not executed |
| Inventory | physical/generated/additional/config source missing, extra, or misclassified |
| Source policy | consumer rule violation |
| Suppression | malformed, stale, widened, missing, unapproved, or unconsumed record |
| Configuration/tamper | lock, matrix, compiler input, severity, ruleset, or receipt mutation |
| Evidence | stale, incomplete, mismatched, nondeterministic, or redaction failure |
| Performance | focused or full budget exceeded |
| Package/runtime | analyzer/build asset leaked into runtime or package closure |
| Toolchain | unsupported SDK, compiler/Roslyn, language, framework, or MSBuild |
| Internal regression | Program Kit's private gate no longer passes unchanged |

`PKCG...` mechanics diagnostics never masquerade as `PKCC...` public-contract
or consumer-owned rule diagnostics. Transport, tooling, public-contract,
consumer policy, source, evidence, and semantic-design failures are never
collapsed into one Boolean.

## 12. Package and project ownership

### Selected candidates

1. `Orbyss.ProgramKit.Architecture` owns the v2 architecture contract,
   `StaticConformanceDisposition`, validation, and v1-to-v2 migration.
2. `Orbyss.ProgramKit.Planning` owns the v3 implementation-plan binding,
   gate-establishment work-unit kind, static-conformance reference, and
   v2-to-v3 migration.
3. `Orbyss.ProgramKit.CSharpBuildGates.Contracts` owns C# gate definitions,
   catalogs, profiles, activation matrices, selection locks, suppression
   ledgers, evidence contracts, validators, and schemas. It depends only on
   Artifacts, Architecture, and Quality.
4. `Orbyss.ProgramKit.CSharpBuildGates.Authoring` owns non-analyzer Roslyn
   helpers, optional recipe catalog/source templates, and scaffold primitives.
   It depends on Contracts and exact Roslyn packages.
5. Narrow `Orbyss.ProgramKit.<Contract>.Analyzers` packages own only exact
   public Program Kit contract-conformance analyzers and `PKCC...` diagnostics
   for their source contracts. They are analyzer-only, separately versioned,
   directly selected, and never aggregate unrelated Program Kit policy.
6. `Orbyss.ProgramKit.CSharpBuildGates.Build` owns direct, opt-in MSBuild
   props/targets/tasks for attachment, inventories, compiler-input
   reconciliation, receipts, and automatic command integration. Its package
   has no `lib/` or `ref/` runtime assets and no `buildTransitive/` assets.
7. `Orbyss.ProgramKit.CSharpBuildGates.Testing` owns the compiler-backed
   conformance runner, fixture harness, deterministic diagnostic comparison,
   cancellation, performance, package inspection, and tamper profiles.
8. `Orbyss.ProgramKit.Workbench` owns the five deterministic operation
   implementations over those contracts.
9. `Orbyss.ProgramKit.CommandLine` owns only the finite CLI transport.

A concrete public analyzer package is added only after its owning public
contract and static claim are exact. The initial proof includes one narrow
public contract analyzer plus one separately owned fictional consumer analyzer;
it does not create an analyzer for every Program Kit package.

### Why not `Orbyss.ProgramKit.DotNet`

`Orbyss.ProgramKit.DotNet` owns host design-time generation and has a broad
runtime-facing package graph. Making it own Roslyn/MSBuild gate contracts would
couple host generation to build enforcement and increase runtime-leak risk.
The narrow packages keep all gate dependencies development/build-only.

### Allowed graph

```text
Artifacts <- Architecture <- CSharpBuildGates.Contracts
Artifacts <- Quality ------^
CSharpBuildGates.Contracts <- CSharpBuildGates.Authoring
CSharpBuildGates.Contracts <- CSharpBuildGates.Build
public Program Kit contract + CSharpBuildGates.Authoring
  <- exact Orbyss.ProgramKit.<Contract>.Analyzers
CSharpBuildGates.Contracts + Authoring + Quality
  <- CSharpBuildGates.Testing
Architecture + Planning + CSharpBuildGates.* <- Workbench <- CommandLine

consumer analyzer project
  -> CSharpBuildGates.Authoring (build-time only)
consumer product project
  -> direct CSharpBuildGates.Build import (PrivateAssets=all)
  -> exact selected public Program Kit contract analyzers as Analyzer only
  -> exact consumer-owned analyzer project/assembly as Analyzer only
consumer runtime/package closure
  -> no Program Kit gate, authoring, testing, build, capability, or analyzer asset
```

### Forbidden graph

- consumer runtime/product code to any gate/build/testing/authoring package;
- Program Kit runtime packages to consumer analyzers;
- `Orbyss.ProgramKit.CSharpGate` to any consumer project;
- public Program Kit contract analyzer without its exact selected owning
  contract/profile and activation matrix;
- one universal Program Kit analyzer aggregating unrelated public and private
  policy;
- Program Kit rule recipes to automatic analyzer activation;
- `buildTransitive` gate activation;
- public or consumer-owned analyzer to Program Kit-private policy or
  `PKCS...` catalog;
- capability definitions or provider adapters to runtime code; and
- arbitrary assembly loading, scanning, plugin discovery, service location,
  mutable global registries, or unbounded process execution.

## 13. Public Roslyn decision

The bootstrap deferred a public metadata package, consumer annotations,
compiler-symbol adapter, and Roslyn dependency until repeated concrete
generator use cases justified an ownership design.

This extension supplies a concrete repeated build-tooling case: Program Kit's
internal gate mechanics, a mandatory fictional external consumer proof, and
the Domain Semantic Engine candidate. The deferral is therefore reopened only
for the narrow C# build-gate packages above.

It does not authorize:

- `Orbyss.ProgramKit.DotNet.Metadata`;
- consumer source annotations;
- a language-neutral compiler model;
- assembly or attribute discovery;
- output-folder scanning;
- a general Roslyn workspace service; or
- Program Kit ownership of consumer rules.

## 14. Implementation-flow integration

`pkid:schema:program-kit:implementation-plan` advances from `2.0.0` to
`3.0.0`. A v3 plan requires:

- exact `staticConformanceDisposition`;
- exact selected gate design/definition/lock and operation revisions when
  runnable gates are selected;
- work-unit kind `gate-establishment`, `product`, or `closure`;
- exact gate profile and activation matrix per work unit; and
- dependency validation proving every affected product unit follows successful
  gate establishment.

At preflight:

- `reuse-existing` requires the exact compatible lock before any mutation;
- `extend-existing` and `create-new` allow only their exact approved
  gate-establishment units while the new lock is absent;
- no dependent product mutation is allowed until establishment evidence passes;
- `not-justified` requires the exact accepted empty disposition;
- `blocked-unavailable` stops; and
- stale, incompatible, disabled, absent, substituted, or unbound gates stop the
  affected product work.

An ordinary source violation may be corrected within an approved product work
unit. A gate defect, ambiguous rule, architecture conflict, policy change,
unapproved suppression, unavailable mechanics, or activation-matrix change
stops for design or human disposition.

## 15. Fixtures and acceptance evidence

The extension requires:

- one valid narrow Program Kit public contract-conformance analyzer with
  `PKCC...` diagnostics and one separately owned fictional consumer analyzer
  with consumer diagnostics, composed in the same consumer-owned gate;
- invalid public-analyzer selection without its owning contract/profile,
  unrelated public analyzer activation, diagnostic collision, copied public
  diagnostic ownership, and private `PKCS...` analyzer attachment;
- an explicitly accepted empty-selection disposition fixture;
- invalid missing, `null`, implicit-empty, and blocked-as-empty dispositions;
- one exact negative fixture per reusable mechanic and fictional rule;
- analyzer removal, duplication, substitution, disablement, severity demotion,
  ruleset, compiler/analyzer skip, and stale-byte fixtures;
- physical-source omission, generated-source evasion, wrong owner, forged
  marker, additional-file omission, and analyzer-config mutation;
- malformed, duplicate, stale, missing, widened, expired, overbroad, and
  unconsumed suppressions;
- valid typed temporary exceptions plus unknown, ambiguous, expired, widened,
  exhausted, unapproved-renewal, missing-evidence, and forged-condition
  failures;
- bootstrap stale-output, nondeterministic build, self-validation, and
  negative-control failures;
- configuration, lock, receipt, source, package, and post-validation mutations;
- build, test, pack, publish, and generated-project automatic-invocation proof;
- preflight, work-unit, generated-output, and final explicit-verification proof;
- clean package-only isolated consumers with no runtime gate assets;
- clean-checkout and cross-path repeatability;
- deterministic diagnostics and evidence;
- cancellation and teardown;
- focused and final-closure performance budgets; and
- unchanged exhaustive proof for Program Kit's private gate.

Before any later migration of the private Program Kit gate, a separate design
must prove rule, diagnostic, suppression, source-inventory, receipt, bootstrap,
fixture, and performance equivalence with no enforcement gap.

## 16. Version Map

Independent clocks are explicit:

| Surface | Initial/revised clock |
| --- | --- |
| Architecture design schema/model | `2.0.0` |
| Static conformance disposition | `1.0.0` |
| Planning implementation-plan schema/model | `3.0.0` |
| C# gate definition and catalogs | `1.0.0` |
| Selection lock | `1.0.0` |
| Suppression ledger | `1.0.0` |
| Evidence contracts | `1.0.0` |
| Build mechanics | independent package/contract revision |
| Authoring recipes and scaffolder | independent catalog/generator revisions |
| Operations | independent `1.0.0` contracts |
| Consumer gate/policy/analyzers | consumer-owned independent revisions |
| Capability definition | `design-csharp-build-gate@1.0.0` |
| Capability bundle inventory | `2.1.0` candidate |
| Program Kit private gate policy | remains `1.10.0` unless separately changed |

The Version Map records every dependency edge and exact selection. Architecture
v1 and Planning v2 remain readable through explicit migrations; writers emit
only the selected current revision after migration. A mixed v1/v2 architecture,
v2/v3 plan, partial bundle, or stale selection lock fails.

## 17. Capability index, adapters, and bundle

`design-csharp-build-gate` remains `unavailable` until contracts, schemas,
operations, packages, build integration, fictional proof, fixtures,
documentation, and migrations pass.

Only then, under the explicitly invoked `author-and-maintain-skills`
capability, implementation may:

- author the canonical capability;
- update `design-software` and `implement-software-plan`;
- add thin adapter templates for the already registered Codex and Claude Code
  providers;
- update the capability index and catalog;
- update initializer ownership and fixtures; and
- add the new design capability to exact CapabilityBundle inventory `2.1.0`.

No `implement-csharp-build-gate` capability is added. Bundle installation and
provider initialization remain inert and grant no authority.

## 18. Domain Semantic Engine implication

The Engine's eventual formal design must carry an exact accepted
`StaticConformanceDisposition`. If it selects `create-new`, the gate-design
subflow produces the exact Engine-owned definition for a non-packable:

```text
tools/Orbyss.Semantics.CSharpGate/
```

That gate owns Engine diagnostic identities, rule meanings, profiles,
exceptions, suppressions, compatibility, and activation. It may explicitly
adopt Program Kit rule recipes under Engine-owned bindings and select narrow
Program Kit public contract-conformance analyzers for exact Program Kit
contracts/profiles it consumes. It never imports the private Program Kit
analyzer or `PKCS...` policy.

The Engine implementation plan places gate establishment before its first
dependent product work unit. The Engine's existing bounded synthetic source
generation remains its only current C# generation authority; this design adds
no general Engine code generator.

## 19. Static evidence boundary

Passing a layered gate is structural evidence. It is not proof of:

- correct domain ownership or semantics;
- deterministic runtime behavior;
- privacy or security;
- concurrency safety;
- truthful reconstruction;
- persistence correctness;
- provider substitution;
- migration correctness beyond observed fixtures; or
- human architectural quality.

Those claims remain with type design, architecture tests, executable tests,
integration evidence, and human review.

## 20. Human decisions requested

Approval of this review set accepts:

- the private Program Kit gate boundary;
- the consumer-owned gate composition of standard baselines, selected public
  Program Kit contract-conformance analyzers, and consumer-owned analyzers;
- Program Kit ownership of public contract diagnostic semantics and consumer
  ownership of consumer-specific diagnostic semantics;
- the required disposition and explicit-empty rule;
- the finite activation matrix;
- typed fail-closed temporary activation exceptions;
- the five-operation surface;
- the selected package/project graph;
- mandatory same-assembly participation receipts;
- the bootstrap/update model;
- Architecture v2 and Planning v3 migrations;
- the capability and bundle disposition;
- deferred private-gate migration; and
- the exact implementation plan.

Approval does not authorize implementation beyond the exact approved plan.

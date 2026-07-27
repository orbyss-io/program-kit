# Reusable consumer-owned C# build gate intent

Status: human intent record for design only

## Outcome

Design a separately approved Program Kit extension that provides reusable
C#/.NET/Roslyn/MSBuild mechanics for serious consumer-owned layered build
gates, plus a backed human-session capability for designing those gates.

Program Kit owns generic contracts, deterministic operations, scaffolding,
build assurance, fixtures, and evidence. Each consumer owns its gate identity,
consumer-specific analyzer assemblies, consumer rule meanings and diagnostic
identities, project/source profiles, exceptions, suppressions, compatibility,
and activation selection.

The consumer owns the composed gate and every analyzer selection. Analyzer
policy ownership remains with the semantic owner: Program Kit owns diagnostics
for its public contract-conformance rules, while the consumer owns diagnostics
for its consumer-specific rules.

## Mandatory design integration

Every Program Kit-backed software design must carry exactly one
`StaticConformanceDisposition`. Omission, `null`, or an unaccepted empty
selection is invalid.

The disposition is one of:

- `reuse-existing`;
- `extend-existing`;
- `create-new`;
- `not-justified`; or
- `blocked-unavailable`.

`not-justified` is the only valid empty runnable selection. It requires an
explicitly human-accepted empty analyzer set, rationale, residual risks, and
claims that remain outside static proof. `blocked-unavailable` blocks
implementation and is not an empty-selection approval.

When no accepted gate selection and no accepted `not-justified` disposition
exists, `design-software` must stop before finalizing the review set and ask the
human whether to reuse, extend, create, or explicitly proceed without a gate.
An explicit `create-new` or `extend-existing` answer starts
`design-csharp-build-gate`; it is not silently self-started.

## Consumer-owned execution

Only explicitly selected analyzer components run on consumer-owned source.
Those components may include:

- standard compiler and C# analyzer baselines;
- narrow Program Kit-owned contract-conformance analyzers for exact public
  Program Kit contracts or profiles the consumer selected; and
- consumer-owned analyzers for consumer-specific policy.

Program Kit public contract-conformance diagnostics remain single-sourced,
versioned, and owned by the Program Kit contract owner. They run only where the
exact contract/profile and activation matrix apply; consuming any Program Kit
package does not silently activate every Program Kit rule.

Program Kit's private `Orbyss.ProgramKit.CSharpGate`, `PKCS...` diagnostics,
repository project allow lists, private source profiles, private
generated-source conventions, and private suppression policy remain private to
Program Kit and never execute as consumer policy.

Program Kit build mechanics may execute around compilation to prove exact
attachment, input inventory, consumer-analyzer participation, tamper resistance,
and evidence. Those mechanics are not a second source-policy analyzer.

Program Kit may offer optional source-rule recipes and analyzer-authoring
primitives. A consumer adopts a recipe only by assigning consumer-owned rule
meaning, diagnostic identity, scope, compatibility, and fixtures in its own
gate definition. No recipe is activated merely because Program Kit is
installed.

Public contract-conformance analyzers are not recipes: the Program Kit contract
owner retains their invariant and diagnostic meaning. A contract may instead
require schema validation, architecture tests, compiler fixtures, or executable
conformance tests when Roslyn cannot establish the claim.

## Activation conditions

Each selected analyzer component has a finite typed activation matrix over
exact:

- project identities and paths;
- source profiles;
- handwritten, consumer-owned generated, additional-file, and configuration
  inputs;
- build, test, pack, publish, and generated-project commands;
- implementation preflight, work-unit, generated-output, and final-closure
  boundaries; and
- focused, full, bootstrap, tamper, and performance verification profiles.

No arbitrary expression, script, glob, environment condition, registration
order, folder guess, ambient discovery, `latest`, first-compatible selection,
or silent fallback is permitted. Applicability conditions cannot disable a
selected analyzer for a command or boundary that the approved matrix covers.

A predictable edge case may use a temporary activation exception only when the
exception has a finite typed condition, exact affected scope, consumer owner,
human authority, rationale, residual risk, compensating verification, evidence,
expiry or deterministic removal trigger, and bounded renewal semantics. The
condition is evaluated from controlled digest-bound inputs and every valid
non-execution emits a receipt. Unknown, missing, ambiguous, changed, expired,
widened, exhausted, forged, or unapproved-renewal state fails closed.

A temporary activation exception is not an approved empty disposition, a rule
suppression, a gate failure, an environment-variable bypass, a warning
demotion, or permission to remove the analyzer.

## Implementation ordering

For `create-new` or `extend-existing`, the approved implementation plan places
gate establishment before every dependent product work unit. An absent gate
blocks product mutation but does not block the exact approved gate-establishment
work unit.

Gate establishment scaffolds or updates any consumer-owned analyzer, resolves
exact Program Kit public contract-conformance analyzer assets, builds locally
owned candidates without trusting stale or self-produced bytes, runs
self-validation and positive/negative/tamper fixtures for every selected
component, emits an exact selection lock, activates the approved build
integration, and proves automatic and explicit invocation. Only then may
dependent .NET projects be created or changed.

`implement-software-plan` remains the sole implementation authority. No
separate gate-implementation capability is created.

## Domain Semantic Engine implication

The Domain Semantic Engine is the first concrete external candidate. Its
prospective non-packable `Orbyss.Semantics.CSharpGate` is consumer-owned. It
may adopt selected Program Kit rule recipes under new Engine-owned diagnostic
identities and may select narrow Program Kit public contract-conformance
analyzers for exact Program Kit contracts it consumes. It does not run Program
Kit's private analyzer and does not gain a general C# code generator.

## Authority boundary

This intent authorizes design and implementation planning only. It does not
authorize analyzer, generator, package, operation, schema, capability,
provider-adapter, runtime, Engine, or Program Kit implementation.

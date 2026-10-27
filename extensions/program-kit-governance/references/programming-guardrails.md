# Generic programming guardrails

## Default coding constraints

<!-- program-kit:knowledge-rule principle.guardrail-defaults -->
These defaults apply unless a narrower rule is justified and documented:

- Prefer simple, cohesive designs that satisfy SOLID principles and make invalid states difficult to represent.
- Keep domain intent independent of UI, transport, persistence, serialization, and vendor SDK concerns.
- Make public contracts, dependencies, side effects, errors, timeouts, cancellation, concurrency, and ownership explicit.
- Validate at trust boundaries; preserve typed information inside them.
- Use deterministic, hermetic tests where possible. Test behavior, contracts, architecture rules, failure modes, and migrations in proportion to risk.
- Treat warnings as build failures in CI after a deliberate baseline. Do not suppress diagnostics without a reason and scope.
- Use structured logs without secrets, stable correlation identities, meaningful metrics, and trace propagation across asynchronous boundaries.
- Pin tool and dependency versions according to ecosystem practice; automate update discovery but require verification before promotion.
- Generate SBOM/provenance and perform dependency, secret, static security, and license checks when artifacts are distributed or deployed.
- Do not use invisible fire-and-forget work. Durable asynchronous work has identity, ownership, observability, retry semantics, and a terminal state.
- Avoid framework-shaped domain models and generic repository/store/unit-of-work abstractions that
  erase domain language. Model the smallest cohesive semantic capability; group naturally related
  methods and split only at real consumer, consistency, security, lifecycle, or replacement boundaries.
- Organize meaningful changes as complete vertical slices and avoid technical-layer delivery phases.
- Keep peer runtime implementations independent; collaborate through Core-owned semantic
  capabilities, consumer-owned bridges, immutable events, or accepted published-language Core edges
  rather than implementation references or shared persistence.
- Treat in-process domain events as awaited and non-durable. Durable asynchronous delivery requires
  an explicitly accepted integration-event/outbox design; fire-and-forget is not a bridge.
- Treat concrete inheritance across feature boundaries as stronger coupling, not an automatic exception. Require an Accepted ADR and an architecture-test allowlist for a genuine feature-family extension.
- Keep dependency injection and service location at composition boundaries. Business behavior declares explicit constructor dependencies and does not resolve arbitrary services from a container.
- Reuse the selected authentication feature's canonical permission policy. Consumer features do not
  parse provider roles/token shapes or reparse canonical permission claims; add a resource-specific
  authorization handler only for a real resource, state, tenancy, or protected-effect decision.

Apply rules proportionally. Pure transformations and trivial adapters should remain small; they do not need ceremony that adds no invariant, policy, or lifecycle value.
<!-- /program-kit:knowledge-rule -->

## Typed boundaries and design evidence

<!-- program-kit:knowledge-rule principle.first-operation-source-review -->
Before replicating a non-trivial operation, review its first coherent source and adverse case:

- Name the semantic owner and legal state transitions. Use owned typed states/keys internally and
  explicit unchanged wire/storage mappings; scattered state strings are not a lifecycle model.
  Shared failure/retry codes are owned semantic keys too: declare them once in a cohesive owner and
  use those names in policy, provider and adapter decisions. A typed facade over remaining raw-string
  decisions does not complete that refactor. Boundary maps may contain exact literal spellings;
  review their placement, and retain independent literal compatibility assertions in tests.
- Keep pure policy in its semantic owner. Core accepts admitted policy, not implementation-specific parser/browser/platform
  restrictions or optional defaults that silently replace configured snapshots. Providers retain
  their atomic effects and implementation constraints.
- Keep each method at one abstraction level. Extract meaningful policy, parsing, mapping and lifetime
  boundaries; a partial file, green analyzer or shorter method does not establish responsibility.
- Trace effective configuration from its single default source through activation and every consumer.
  Preserve original work snapshots; distinguish adjustable policy, fixed contracts and safeguards.
  Use the selected stack's native binding/validation mechanism before snapshot admission; a typed
  settings class or immutable snapshot does not prove native binding. Justify any specific replacement.
- Carry one complete execution deadline through bounded stages. Own cancellation, fresh scopes,
  retained state, disposal/drain and safe failure observations; cancellation is not actual stop.
- Admit external values at runtime and test a relevant malformed/denied/fault case. Generated types,
  casts, dependency graphs and generic SOLID claims do not establish semantic correctness.

Apply only relevant duties; preserve native mechanisms and agreed review points. This source review
adds no approval gate, factory per class or mandatory interface for private pure helpers.
Before completion, review changed decisions/helpers against the whole applicable source/layout
category; retain findings and pending reviews in task notes. A later review cannot justify known
omissions in completed work. Human-triggered repairs do not prove earlier detection. For concurrent
work, identify the active owner and distinguish before, repaired-after and unverified observations.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.framework-native-mechanisms -->
Use the selected framework's native mechanisms and supported extension points before adding equivalent
infrastructure. During planning and semantic review, challenge every proposed project, wrapper, runner
and lifecycle owner: what requirement does it meet that the selected mechanism cannot? Inspect exact
selected-version contracts first. Record a concrete unmet requirement, alternatives and justification
in the existing plan or ADR before replacing a framework responsibility. An assistant-authored task,
accepted dependency graph or passing behavioral test is not that justification. Keep legitimate local
choices and small application-owned policy; no new approval, receipt or fixed decision table is needed.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:decision-rule typed-admission -->
<!-- program-kit:knowledge-rule principle.typed-admission -->
Known request/response/configuration envelopes use typed contracts after admission. Prove
parser/schema/runtime parity, including valid variants and rejected inputs. Bounded
dynamic schemas and lexical/canonical JSON processing remain legitimate exceptions when encapsulated
and tested. A DTO alone does not establish validation, authorization or deep immutability.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->

<!-- program-kit:knowledge-rule principle.normalized-label-contract -->
For .NET labels shared with browser forms, consult the supported
[owner-backed normalized label path](../../program-kit-dotnet/references/label-validation.md).
Export actual pure Core rules through an owner build tool and generate matching client validation;
keep the server authoritative and verify raw-input preservation, character sets, length units,
normalization order and digest parity. This applies to relevant label contracts, not every model or
implementation phase, and adds no approval or automatic model-enforcement step.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.solid-design-evidence -->
Evaluate SOLID against changed responsibilities and actual consumers:

- SRP: separate unrelated reasons to change, especially policy from transport/configuration/I/O.
- OCP: use existing owned extension points; do not duplicate selected mechanisms or invent unused ones.
- LSP: preserve promised preconditions, outcomes and invariants across substitutable implementations.
- ISP: expose cohesive capabilities needed by real clients, without an interface-per-method rule.
- DIP: depend on owned semantic capabilities and replaceable time/environment/I/O. Keep private seams
  private; Core owns genuine feature contracts, not every implementation helper.

Implementation-only helpers default internal. Pure deterministic static transformations are valid.
Use framework constants or cohesive owner-scoped values without changing wire/version meaning.
An attributed review cites affected source and behavior for each relevant principle; a generic
"SOLID passed" statement or a file-count threshold is not evidence. Static analysis proves only its
specified properties; use substitution, boundary and architecture tests where the contract needs them.
Review the responsibilities changed by the diff, with source and behavioral evidence. Do not repeat
an entire SOLID inventory for each trivial edit, invent interfaces for private pure helpers, or add
new review approvals. Keep one named type per file and purposeful XML documentation as explicit
Orbyss source policy; these choices do not replace runtime correctness or architectural ownership.
<!-- /program-kit:knowledge-rule -->

## Review of effects and test boundaries

<!-- program-kit:knowledge-rule principle.effects-source-review -->
Review the changed operation with concrete source locations and its relevant regressions. Record findings
in existing tasks and delivery output; a passing graph or generic SOLID statement cannot close them.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.production-abstraction-responsibility -->
- A production interface, virtual method or forwarding type needs an actual capability, policy,
  invariant, lifecycle or replacement responsibility. A test-only substitution does not supply that
  responsibility. Prefer supported native test instrumentation without publishing implementation state.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.completed-result-integrity -->
- Require the payload promised by a completed result. Unresolved effects carry established operation
  metadata, not a fabricated durable receipt. Restrict construction and mutation of invalid result
  combinations. Provider classification and cancellation mechanisms inform consumer-owned decisions;
  they do not decide domain outcomes or commit certainty.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.decision-time-budget -->
- Read time where the effect owner makes its decision after asynchronous waits. Propagate the owned
  complete deadline into bounded stages; a new timeout per layer must not restart the budget. Verify
  actual DI clock replacement, exact boundaries and cancellation before/after effect dispatch.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.operational-setting-lifecycle -->
Before coding, inventory each affected behavioral/resource limit in the existing plan Operation
implementation map and carry its checks into ordinary tasks. Include counts, lengths and their units,
size/page/batch ceilings, quotas/rates, retries, deadlines and retention across literals, constants,
attributes, schemas, defaults and client/server copies. Establish each limit's meaning, units, semantic
owner, authoritative source, value/default, justification, enforcement and validation. Classify it as
configurable business/operational policy, a fixed contract constraint or an engineering safeguard.
A constant or a class named Rules supplies no policy authority. Existing hard-coded behavior is an
observation, not an approved business limit or default; do not auto-fill policy decisions from legacy
literals. Do not silently invent business policy.

For configurable policy name the setting, default basis (or required input without a default), activation/
reload lifecycle and every consuming boundary. Validate actual settings at the owning effect/composition
boundary; pass admitted typed policy values/snapshots to pure Core rather than adding configuration I/O
there. Trace omitted input, nondefault settings and consistent admission/execution/client behavior.
Keep adjustable policy separate from fixed wire/storage/protocol ceilings and validate compatibility.
For a fixed contract cite its actual contract basis; for a safeguard justify the engineering risk and
owner's chosen bound locally. Missing consequential business policy blocks affected implementation:
inspect accessible facts first, then clarify only missing consequential intent and update existing
spec/ADR/plan and dependent tasks. Routine justified engineering caps need no extra human approval.

Before completion reconcile every implemented/changed limit and consumer against those decisions in the
existing source inspection, including an explicit no-limit assessment for ordinary unbounded/pure work.
Reject invented/omitted limits, dead settings, hard-coded bypasses, inconsistent consumers and unvalidated
defaults; repair source/plan/tasks before claiming compliance. Exercise actual nondefault and exact-boundary
behavior, invalid configuration and omitted/default paths through the maintained check owner. A source
reference, structurally complete row or authored compliant assessment cannot establish its own truth;
semantic completeness and authoritative policy meaning remain source-review responsibilities.
Ordinary numeric indexes/discriminants, protocol identities, authorization and citation identity/hash/
exact-quote invariants are not adjustable policy. Preserve frozen migration bytes and independent
consistency assertions; this is no numeric-literal ban or universal semantic detector.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.production-composition-tests -->
- Tests resolve production capabilities through actual feature registration and lifecycle. Observe
  durable effects independently when certainty, rollback or replay matters. Keep implementation
  types/ORM state private and enforce the existing prohibition on friend access; do not introduce
  a public facade solely to rescue privileged tests.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.actual-browser-acceptance -->
- Browser acceptance exercises the actual controls and client adapter through readable, accessible
  recovery. Protocol JSON/status assertions remain protocol evidence. Independently observe session
  state, distinguish local from provider logout, and test human interaction windows separately from
  bounded application-controlled network work.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule context.effects-review-proportionality -->
Apply these checks only to relevant changed responsibilities. They introduce no additional approval
stage, proof dossier or full-acceptance run during ordinary implementation.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.untrusted-input-qualification -->
Before external processing of untrusted input, define what successful local inspection establishes.
Inspect the selected dependency's failure, fallback and deferred-execution semantics. A strict option,
successful return or top-level traversal can leave corrupt, unsupported or lazy work unvalidated.
Complete the application admission contract through supported native seams, reject inconclusive
results before dispatch, and preserve the identity of admitted bytes through submission.
Qualify the actual packaged runtime and dependency closure with malformed, truncated, expansion,
timeout and cancellation cases. Distinguish enforced resource bounds from monitored limits;
account for concurrent work and cleanup. Rejection must produce no downstream processing effect.
Keep failure observations bounded and free of input contents, sensitive paths and raw parser messages.
Record remaining uncertainty in ordinary tasks; happy-path checks prove only exercised guarantees.
<!-- /program-kit:knowledge-rule -->

## Maintained application handoff

<!-- program-kit:knowledge-rule principle.maintained-application-handoff -->
During planning identify affected delivered guides, public contracts, source-backed settings and
runtime/data requirements. Add their implementation and meaningful review scenarios to ordinary
feature tasks. During implementation maintain these consumer-owned inputs alongside behavior and
normal tests. Delivery uses retained eng/application_handoff.py after actual bundle description and
contract/settings export; it must reject required missing/stale coverage. Specifications and AI logs
are not evidence of delivered behavior. Link the existing engineering README and docs/application/
inputs; do not add an approval ledger. Infrastructure and documentation receivers own downstream
workflows. Missing publisher settings metadata remains an explicit upstream dependency.
<!-- /program-kit:knowledge-rule -->

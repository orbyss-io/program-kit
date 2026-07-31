---
artifact-kind: program-kit-design-category
category: feature-model
status: paused
last-updated: 2026-07-31
active-batch: FTR-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Feature Model

## 1. Category objective

Define the thinnest enforceable .NET feature model needed for Program Kit to
generate, identify, inspect, and integrate C# features built with CShells.

This category does not define a universal feature ontology or prescribe a
domain-driven architecture. Consumer-owned rules determine whether inheritance,
direct feature references, sibling-domain dependencies, messaging, registries,
bridges, or other composition forms are permitted.

Unified means that a small app and a complex domain system use the same
mechanics for identity, generation, artifacts, evidence, diagnostics, impact,
and evolution. It does not mean they share the same semantic or architectural
rules.

The current boundary is:

- Program Kit v1 is a .NET programming kit.
- CShells is the mechanism used for generated .NET features.
- A feature carries an implementation identity and purpose.
- An interface is the governed semantic boundary between a feature and a
  consumer.
- Program Kit records and evaluates declared boundaries and consumer-supplied
  rules; it does not invent domain composition rules.
- React or other targets may later reuse this philosophy through specialized
  target support, but they do not make the current model universal.

Discovery is paused at this boundary while Product Identity batch `PID-B05`
defines the portable unit, model-neutral development protocol, and future target
adapter promise. `DEC-013` remains a candidate and is not implicitly accepted.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `FTR-B01` | `FTR-001`, `FTR-003`, `FTR-004`, `FTR-015`–`FTR-017` | `active` | Define the thin .NET/CShells feature identity, interface boundary, and policy-ownership model. |
| `FTR-B02` | `FTR-002`, `FTR-005`–`FTR-007` | `queued` | Resolve CShells support, exposed surfaces, and minimal terminology. |
| `FTR-B03` | `FTR-008`–`FTR-012` | `queued` | Resolve identity scope, versioning, relationships, and implementation selection without imposing architecture. |
| `FTR-B04` | `FTR-013`–`FTR-014` | `queued` | Define the minimum record and how consumer-defined contracts and rules are referenced. |

## 3. Active batch: Thin feature boundary

### FTR-001 — Exact role of `CShells.IFeature`

- **Status:** `follow-up`
- **Previous state:** `DEC-012` treated CShells as prior art behind an optional
  projection adapter. The human reopened that decision because CShells is the
  intended .NET feature mechanism, not merely one optional modeling target.
- **Known intent:** Program Kit generates .NET features using CShells. A
  deterministic generator must know the exact syntax, conventions, version,
  validation rules, and diagnostics of the CShells target.
- **Questions:** Must every Program Kit-generated .NET feature implement
  `CShells.IFeature`? Is CShells a direct dependency of generated projects, a
  dependency of the generator, or both? Which package and version boundaries
  must be pinned and included in generation identity?
- **Recommendation:** For v1, make `CShells.IFeature` the required runtime marker
  for generated .NET features and make a version-specific CShells generator the
  required .NET projection. Keep Program Kit's generation manifest and feature
  identity metadata under Program Kit ownership. Pin the generator, CShells
  package, SDK, and rules as exact inputs. Do not generalize this into a
  cross-language abstraction yet.
- **Decision needed:** Confirm or refine this direct .NET/CShells role.

### FTR-003 — Minimum meaning of feature

- **Status:** `follow-up`
- **Human correction:** The previous candidate introduced feature contracts,
  feature implementations, components, and dependency restrictions as if they
  were universal architecture. That was too broad. A feature is an actual
  implementation and a way to express stable identity internally or externally.
- **Question:** Is the minimum core definition simply a concrete .NET feature
  implementation with stable identity, purpose, target, and declared interfaces
  or relationships, while all additional validity rules are consumer-owned?
- **Recommendation:** Yes. Program Kit should know that a feature exists, how it
  is identified, where its artifacts are, which interfaces it declares, and
  which relationships or policies the consumer attached. It should not decide
  that feature inheritance, feature references, cycles, nesting, or composition
  are invalid unless an active consumer rule says so.
- **Consequences:** Methods and helpers are not features unless explicitly
  declared or generated as features. Different consumers may impose different
  feature granularity and composition policies.
- **Decision needed:** Confirm or refine this minimum feature definition.

### FTR-004 — Minimum meaning of interface

- **Status:** `follow-up`
- **Accepted axiom:** An interface is the governed semantic boundary between a
  feature and a consumer; it is not necessarily a CLR interface.
- **Human correction:** Program Kit must not prescribe internal interface roles,
  public-surface categories, mediator patterns, messaging, eventing, registries,
  bridges, or transport choices. Consumers define and control those rules.
- **Question:** What is the minimum information Program Kit itself must know
  about an interface to identify it, connect it to a feature and consumer, run
  consumer-supplied rules, calculate impact, and return meaningful diagnostics?
- **Recommendation:** The core should require only stable interface identity,
  version, owning feature, consumer or audience reference, exposure direction,
  and references to consumer-owned contract artifacts and validation policies.
  Role names, schemas, transports, configuration semantics, compatibility rules,
  and bindings remain opaque or extensible consumer data unless a selected
  extension understands them.
- **Decision needed:** Confirm this minimal descriptor or remove fields that are
  still too prescriptive.

### FTR-015 — Feature identity versus interface identity

- **Status:** `follow-up`
- **Previous candidate rejected:** The earlier model required one primary feature
  contract per implementation and imposed component cardinality. Program Kit has
  no authority to impose that architecture.
- **Question:** Should a concrete feature have its own stable identity while each
  exposed or consumed interface has a separate identity that may be shared by
  multiple implementations?
- **Recommendation:** Yes. Feature identity identifies the concrete implemented
  unit. Interface identity identifies a consumer boundary or contract. Permit
  many-to-many declarations: a feature may expose or consume multiple
  interfaces, and multiple features may expose the same interface. Consumer
  policies determine whether a particular cardinality is valid.
- **Decision needed:** Confirm or refine this identity separation.

### FTR-016 — Ownership of composition rules

- **Status:** `follow-up`
- **Previous candidate rejected:** Program Kit must not impose bridge-only
  sibling-domain interaction, prohibit direct feature references, or choose a
  DDD dependency style for every consumer.
- **Question:** Which rules, if any, are intrinsic structural integrity rules of
  Program Kit, and which are always supplied by consumer policy?
- **Human input:** Program Kit's goal is one unified way to write components for
  both complex domain systems and simple applications. Consumers own their rules
  provided those rules do not interfere with Program Kit's imperative,
  immutable internal mechanics. Program Kit may offer defaults, but defaults
  must not restrict a consumer implicitly.
- **Recommendation:** The core should enforce only mechanics required to keep its
  own evidence honest: identifiers are valid and unambiguous; declared
  references resolve or remain explicitly unknown; exact tool, extension, and
  policy versions are recorded; required artifacts exist; and diagnostics never
  claim validation that did not run. Inheritance, feature references, cycles,
  bridges, domain sibling rules, transports, and composition constraints are
  consumer policies. Without a selected rule, a combination is not prohibited;
  without an applicable validator, Program Kit must not claim semantic
  compatibility.
  Default policy profiles are advisory until the consumer explicitly adopts a
  named, version-pinned profile. Adoption makes those rules enforceable for that
  consumer. Consumers may replace or remove semantic profiles, but no policy may
  override the kernel invariants required for deterministic mechanics and
  truthful evidence.
- **Decision needed:** Confirm this structural-integrity versus consumer-policy
  boundary.

### FTR-017 — .NET now and React later

- **Status:** `follow-up`
- **Previous candidate rejected:** The earlier dimensional interface-facet model
  attempted to create a generic, cross-technology feature language.
- **Question:** How much, if any, current design must be shared with future React
  component generation?
- **Recommendation:** None beyond the accepted philosophy of stable feature
  identity and governed consumer interfaces. Design and enforce the current
  model for C#, .NET, and CShells. A future React specialization may reuse the
  ideas or map compatible metadata, but it must prove its own target rules and
  must not weaken or generalize the .NET implementation in advance.
- **Decision needed:** Confirm that React is a future specialization, not a v1
  feature-model constraint.

## 4. Category decisions

| Decision | Status | Summary |
|---|---|---|
| `DEC-012` | `superseded` | The optional-projection framing overgeneralized the feature model and understated CShells as the intended .NET mechanism. |
| `DEC-013` | `candidate-decision` | Program Kit v1 uses a thin .NET/CShells feature identity and interface-boundary model; consumers own composition and architecture rules. |

## 5. Revision record

- The human rejected the generic contract/implementation/component ontology,
  built-in cross-domain bridge policy, and built-in interface-role taxonomy.
- `FTR-015` through `FTR-017` were retained as stable IDs but rewritten around
  identity separation, policy ownership, and current target scope.
- Git history preserves the rejected candidates; they are not current design.

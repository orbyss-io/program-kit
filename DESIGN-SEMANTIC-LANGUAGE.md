---
artifact-kind: program-kit-design-category
category: semantic-language-and-bounded-contexts
status: active
last-updated: 2026-07-31
active-batch: SEM-B02
parent-ledger: DESIGN.md
---

# Program Kit Design — Semantic Language and Bounded Contexts

## 1. Category objective

Define how human-approved meaning is represented canonically, extended by
consumers, compiled into target-specific implementations, bounded by authority
and contract scope, and proven against actual artifacts without turning Program
Kit into a universal domain language or runtime framework.

The active work must preserve these accepted constraints:

- Program Kit v1 is a semantic development toolchain, not a new programming
  language (`DEC-009`).
- The portable unit is a software-definition bundle with a canonical root
  manifest and separately governed linked artifacts (`DEC-015`).
- Core owns contract mechanics while versioned packages own platform and
  consumer semantics (`DEC-017`).
- Capability mappings support canonical-first and provider-first intake without
  silent loss of meaning (`DEC-016`).
- Only human-approved meaning supported by applicable fresh evidence is admitted
  as semantically understood (`DEC-019`, `DEC-023`).
- The kernel is the trusted non-bypassable product core; the CLI is its primary
  public application layer. Neither is an implicit generated-runtime dependency.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `SEM-B00` | `SEM-013`–`SEM-014` | `completed` | Provider/canonical intake and semantic admissibility accepted by `DEC-016` and `DEC-019`. |
| `SEM-B01` | `SEM-001`–`SEM-004`, `SEM-007`–`SEM-008` | `completed` | Resolve the semantic model, authored projections, canonical representation, declarative boundary, and build/runtime presence. |
| `SEM-B02` | `SEM-005`–`SEM-006` | `active` | Define consumer-owned vocabulary extension without core changes. |
| `SEM-B03` | `SEM-009`–`SEM-012` | `queued` | Define graph federation, cross-authority ownership, disagreement resolution, and the bounded implementation context. |

## 3. Accepted prior decisions

### SEM-013 — Provider-native and canonical intake

**Status:** `accepted`

Provider-first and canonical-first intake are both supported through explicit,
versioned, support-bounded capability contracts. Normalization is traceable and
fails closed when meaning is incomplete or cannot be represented. Provider-first
selection remains bound until an explicit migration. Governed by `DEC-016`.

### SEM-014 — Semantic admissibility

**Status:** `accepted`

Program Kit claims understanding only for governance-relevant meaning that is
human-approved, traceable to declared contracts, and supported by applicable
fresh evidence. Unknown, inferred-only, omitted, stale, drifted, or unverified
behavior remains explicit and cannot be admitted as understood. Governed by
`DEC-019` and evaluated through `DEC-023`.

## 4. Accepted batch: Semantic model and execution boundary

`SEM-B01` resolved:

- `SEM-001`: whether the semantic layer has a formal grammar, type system,
  validator, or compiler without contradicting the accepted non-language claim;
- `SEM-002`: the primary authored form;
- `SEM-003`: the single canonical representation behind multiple projections;
- `SEM-004`: whether governed definitions must remain declarative and
  non-Turing-complete;
- `SEM-007`: whether the semantic layer exists at build time, runtime, or both;
  and
- `SEM-008`: whether generated artifacts must carry the semantic model or may
  compile meaning into code, contracts, metadata, and evidence.

The human accepted all six recommendations. They are governed together by
`DEC-024`.

## 5. Non-authoritative stress-test lessons

The previously authorized
`C:\Users\tech_\Code\semanticdomainengine-design-intake` was reviewed only as
a stress test. Its business/domain model and proposed Engine architecture are
not Program Kit source truth. The following domain-neutral lessons informed the
recommendations:

- exploration should progressively formalize into structured candidates and
  only then into exact canonical bytes;
- structural validity, canonical representation, human approval, compilation,
  activation, and runtime truth are distinct;
- canonical semantic definition must not absorb mutable runtime state,
  environment observations, secrets, process topology, or activation; and
- interpreted or generated runtime projections must bind exact semantic inputs
  and generator/evaluator revisions without becoming a second source of truth.

## 6. Accepted SEM-B01 decisions

These recommendations are accepted under `DEC-024`.

### Delivery-depth boundary

The semantic layer retains its broader product purpose: making admitted
software legible and governable through human-approved meaning. Acceptance of
this batch does not reduce that purpose to implementation convenience for the
kernel or CLI.

For the current design and first implementation, however, Program Kit defines
only the semantic mechanics required to deliver a tangible, end-to-end testable
CLI. Richer semantic capabilities remain possible, but are deferred until a
concrete product workflow proves they are needed. In particular, this batch
does not authorize a reconstruction engine, generalized authority or delegation
system, comprehensive state-machine or lifecycle framework, global knowledge
graph, inference engine, ontology platform, or general semantic runtime.

Minimal identity, approval, authority reference, state, and lifecycle facts may
still be introduced where an actual CLI workflow requires them. This is a
delivery-depth boundary, not a permanent semantic-purpose boundary.

### SEM-001 — Formal typed artifact model, not a programming language

**Recommendation:** The semantic layer is a formal, versioned, API-neutral typed
artifact model with schemas, contract-defined types and constraints, a
canonicalizer, validators, and a deterministic compiler pipeline. It is not a
general-purpose programming language and does not claim an independent language
grammar, executable semantics, or universal type system.

The pipeline is explicit:

1. parse an authored projection under its exact projection profile;
2. validate structure and reject ambiguous or unsupported representation;
3. normalize losslessly into the typed semantic model;
4. resolve exact contract, vocabulary, relation, and profile references;
5. validate semantic and compatibility constraints;
6. emit canonical model bytes and content identity; and
7. compile selected target or runtime projections through exact capabilities.

Every stage produces structured results and diagnostics. Successful parsing or
schema validation does not imply semantic validity, human approval, target
compatibility, evidence-backed admission, or authorization to implement.
Human approval binds an exact semantic revision and digest separately from its
canonical encoding.

### SEM-002 — API-neutral model with a strict human-authored projection

**Recommendation:** The primary semantic authoring contract is the API-neutral
typed model, not C#, JSON, YAML, Markdown, or natural language. Program Kit v1
ships these first-party projections:

- a restricted YAML 1.2 workspace projection optimized for human and AI review;
- structured JSON request/result projections for CLI automation; and
- generated or hand-maintained .NET SDK types as a convenience API, never an
  executable C# DSL or semantic authority.

Natural-language conversation remains intake from which an AI session may
propose a typed candidate; it is not canonical semantic input. The YAML profile
rejects duplicate keys, merge keys, custom tags, anchors/aliases, ambiguous
implicit typing, undeclared fields, and other constructs that lack one lossless
mapping. Comments and formatting remain non-semantic. Program Kit renders a
normalized review form and a semantic diff before human approval.

Additional authored projections are capabilities. Each must declare a total,
deterministic, lossless mapping into the typed model within its support envelope
and must fail closed outside that envelope.

### SEM-003 — One canonical typed JSON byte profile

**Recommendation:** The canonical semantic representation is one exact,
versioned Program Kit canonical JSON byte profile over the typed model. It is a
linked artifact in the software-definition bundle; the bundle and its root
manifest remain the portable product unit.

The profile fixes object-key order, collection semantics, Unicode and string
normalization, number representation and bounds, Boolean representation,
absence versus `null` versus defaults, identifiers, schema and contract
references, extension points, and duplicate or unknown-field handling. Unknown
fields and undeclared extensions fail rather than being ignored. Typed extension
contracts remain possible through explicit referenced schemas.

Semantically identical supported projections produce identical canonical bytes
and a kind-, profile-, algorithm-, length-, and digest-bound content reference.
Different bytes do not become equivalent through a heuristic equivalence hash.
Canonical bytes establish representation and content identity, not truth,
trust, approval, activation, or runtime applicability.

A future binary distribution format may wrap or project the canonical model,
but it is a separately identified artifact and cannot become a second semantic
authority without an explicit later decision.

### SEM-004 — Declarative and non-Turing-complete definitions

**Recommendation:** Authored and canonical semantic definitions remain strictly
declarative and non-Turing-complete in v1. They contain no arbitrary code,
loops, recursion, templates, macros, environment reads, filesystem access,
network access, clocks, randomness, reflection, or ambient package discovery.

Derived meaning may be produced only by an explicit versioned capability or
adapter with declared input and output contracts, exact implementation and
profile revisions, deterministic limits, provenance, and evidence. The
semantic definition references that transform; it does not embed its code.
Consumer validators, analyzers, generators, and policy evaluators may be
implemented in ordinary code outside the semantic data, but their results do
not silently mutate the approved canonical revision.

A bounded expression language would be a separately governed future contract
requiring formal semantics, termination and resource limits, canonicalization,
security analysis, diagnostics, and compatibility. V1 includes none by default.

### SEM-007 — Build-time authority with explicit optional runtime use

**Recommendation:** Program Kit's semantic authority is primarily a
development- and construction-time concern. The CLI invokes the kernel to
validate approved semantic revisions, resolve inputs, generate target-native
artifacts, evaluate evidence, and issue admission results. Generated products
do not require the Program Kit kernel, CLI, capabilities, workspace, or authored
semantic files at runtime.

A selected capability may explicitly generate a runtime-interpreted semantic
artifact when the product genuinely needs runtime policy, workflow, schema,
plugin, or other semantic interpretation. That runtime interpreter and artifact
are target/product dependencies with their own contracts and support envelope;
they are not the Program Kit kernel and do not enlarge Program Kit's runtime
scope.

### SEM-008 — Compile away meaning or package a purpose-bound projection

**Recommendation:** Runtime artifacts need not carry the complete canonical
semantic model. Meaning may be compiled entirely into source, binaries,
contracts, configuration, schemas, metadata, and detached provenance/evidence.
Every generated artifact still binds its exact source semantic revision,
generator/capability revision, target profile, and artifact digest so drift can
be detected without loading Program Kit at runtime.

When runtime interpretation is selected, the generator emits a separately
identified, immutable, purpose-bound semantic projection with complete closure
for its declared operations, compatibility, provenance, and validation
contract. It is derived from and linked to the canonical model; it does not
replace it. Ambient partial loading, runtime filtering of the full model, or an
unvalidated subset may not be claimed as a closed semantic context.

Runtime state, secrets, current authority, clocks, external observations,
health, deployment topology, and environment-resolved values remain outside
immutable semantic definition. Runtime contracts may consume explicit values
or references to them without recasting mutable facts as canonical semantics.

## 7. Active batch: Consumer-owned vocabulary extension

`SEM-B02` resolves:

- `SEM-005`: whether consumers may introduce their own semantic types and
  vocabulary; and
- `SEM-006`: how those vocabularies are versioned and interpreted without
  changing Program Kit core.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### SEM-005 — Versioned vocabulary packages over a small core protocol

**Recommendation:** Consumers may introduce semantic vocabulary through
separately versioned vocabulary packages. A vocabulary package owns its
domain- or platform-specific terms and constraints. The kernel owns only the
small package protocol and the immutable integrity mechanics needed to identify,
load, canonicalize, validate, diagnose, and pin those packages.

A v1 vocabulary package minimally declares:

- an authority-scoped identity, immutable revision, and content digest;
- the semantic-model and vocabulary-protocol versions it supports;
- named types, fields, relations, and constraint parameters composed from the
  closed declarative primitives supported by that protocol;
- the explicit extension locations at which those definitions may appear; and
- references to any required mappings, validators, evaluators, or migrations.

It cannot redefine kernel identities or invariants, add undeclared fields,
embed executable behavior, or claim semantics beyond its declared support
envelope. Program Kit's first-party platform-contract families use the same
package protocol as consumer and third-party vocabularies; first-party status
does not create a second semantic mechanism.

V1 will implement only the declarative primitives exercised by the first
vertical slice. It will not attempt a universal ontology or type system in
anticipation of unknown consumers.

### SEM-006 — Exact declarative loading; executable meaning stays in capabilities

**Recommendation:** A software-definition bundle references every vocabulary
package by exact identity, revision, protocol profile, and digest. Construction
records the exact resolution in its lock. The kernel performs no ambient
discovery, implicit upgrade, semantic-version guess, or best-match selection.

The kernel interprets package manifests and supported declarative constraints
generically. Any validation, mapping, evaluation, migration, or generation that
cannot be expressed by those primitives belongs to a separately identified and
pinned capability. Such a capability executes outside the semantic data,
declares its support envelope, and returns structured evidence and diagnostics.
It cannot mutate a human-approved canonical revision or bypass kernel gates.

Adding a vocabulary that stays within the supported protocol therefore requires
no kernel code change. Requiring a genuinely new semantic primitive does require
an explicit protocol/kernel revision, compatibility decision, and migration;
the old kernel reports `unsupported` rather than guessing. Cross-vocabulary and
cross-authority reconciliation remain for `SEM-B03`.

### SEM-B02 delivery boundary

This batch defines only vocabulary packaging, exact loading, and the
declarative-versus-capability boundary. It does not design an ontology registry,
query language, inference system, vocabulary marketplace, trust federation,
general authority service, reconstruction engine, or full vocabulary lifecycle.

The first vertical slice should prove this mechanism with the smallest useful
first-party vocabulary and one independently identified consumer vocabulary
fixture. That proof should exercise the same kernel path without pretending the
initial vocabulary surface is a complete semantic engine.

## 8. Revision record

- Created after Feature Model closed under `DEC-023`.
- Imported only accepted cross-category constraints; no queued Semantic Language
  answer was promoted silently.
- Accepted `SEM-B01` under `DEC-024` and recorded the human's distinction
  between broad semantic purpose and deliberately shallow first-CLI delivery
  depth.
- Activated `SEM-B02` with bounded recommendations for consumer vocabulary
  packages; no draft recommendation in that batch is yet accepted.

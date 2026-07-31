---
artifact-kind: program-kit-design-category
category: semantic-language-and-bounded-contexts
status: active
last-updated: 2026-07-31
active-batch: SEM-B01
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
| `SEM-B01` | `SEM-001`–`SEM-004`, `SEM-007`–`SEM-008` | `active` | Resolve the semantic model, authored projections, canonical representation, declarative boundary, and build/runtime presence. |
| `SEM-B02` | `SEM-005`–`SEM-006` | `queued` | Define consumer-owned vocabulary extension without core changes. |
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

## 4. Active batch: Semantic model and execution boundary

`SEM-B01` resolves:

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

No answer is implied merely by activating this batch. Recommendations will be
recorded separately and remain unaccepted until human confirmation.

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

## 6. Draft recommendations for human review

These recommendations remain **unaccepted** until the human confirms or revises
them.

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

## 7. Revision record

- Created after Feature Model closed under `DEC-023`.
- Imported only accepted cross-category constraints; no queued Semantic Language
  answer was promoted silently.

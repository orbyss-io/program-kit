---
artifact-kind: program-kit-design-category
category: extensions-and-composition
status: active
last-updated: 2026-07-31
active-batch: EXT-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Extensions and Composition

## 1. Category objective

Define how the software factory gains target, provider, validation, and
construction behavior without allowing extensions to bypass the kernel, silently
change meaning, introduce ambient selection, or create multiple incompatible
plugin mechanisms.

The category preserves these accepted boundaries:

- the kernel owns invariant enforcement, exact resolution, admission, and
  diagnostic truth; extensions cannot replace those mechanics;
- Program Kit operates within exact declared semantic and factory-operation support
  envelopes (`DEC-028`);
- consumer vocabulary uses separately versioned declarative packages
  (`DEC-025`);
- every extension input is explicit and pinned; generated products have no
  implicit Program Kit or extension runtime dependency;
- Spec Kit owns guided planning while Program Kit remains independently callable
  through public factory contracts (`DEC-029`); and
- the external Spec Kit adapter is not designed or implemented until those
  public CLI contracts are stable.

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `EXT-B00` | `EXT-012`–`EXT-013` | `completed` | No internal Spec Kit product dependency; later external adapter invokes stable public factory contracts. |
| `EXT-B01` | `EXT-001`–`EXT-003` | `completed` | Separate factory execution, session guidance, packaging, provider metadata, and vocabulary; define minimum operation roles. |
| `EXT-B02` | `EXT-004`–`EXT-007` | `active` | Define composition, output ownership, conflict resolution, ordering, and version selection. |
| `EXT-B03` | `EXT-008`–`EXT-011` | `queued` | Define trust, isolation, packaging, mandatory metadata, and conformance obligations. |

## 3. Accepted Spec Kit boundary

Program Kit v1 does not embed, wrap, or internally reuse Spec Kit as a product
dependency. Program Kit's own repository uses Spec Kit as its development
method. The selected guided consumer workflow later uses a separately installed,
separately versioned adapter that translates only between public Spec Kit and
Program Kit contracts. Governed by `DEC-029`.

## 4. Accepted batch: Minimum extension roles

`EXT-B01` resolves:

- `EXT-001`: which extension families are foundational;
- `EXT-002`: whether those families are closed and versioned; and
- `EXT-003`: whether extensions may add semantic vocabulary.

The human accepted the refined recommendations. They are governed by
`DEC-031`.

### EXT-001A — Factory execution and session guidance are different products

**Recommendation:** Never use bare `capability` as a normative artifact type.
Keep these concepts distinct:

- an **extension bundle** is a distributable, exact-versioned package that may
  contain operation providers, vocabulary packages, target assets, schemas,
  diagnostics metadata, conformance fixtures, and documentation;
- a **factory operation contract** is one public, versioned kernel invocation
  seam with a declared input, result, support envelope, determinism
  classification, evidence obligations, and diagnostics contract;
- an **operation provider** is exact executable code implementing one or more
  factory operation contracts;
- a **session capability** is provider-neutral guidance and workflow metadata
  that teaches a human-led AI session how to invoke public Program Kit
  operations; it is projected into provider-specific skills or equivalent
  surfaces and is never loaded by the kernel as an operation provider;
- a **vocabulary package** is declarative semantic meaning under `DEC-025`, not
  executable extension code; and
- a **provider profile** describes one selectable provider implementation and
  the exact operation providers, contracts, configuration, and support profiles
  it binds.

A distribution may reference both factory extensions and session capabilities,
but their identities, digests, installation, activation, trust, and authority
remain separate. Any helper executable used by a session capability is an
explicit external tool or operation provider; instructions do not gain kernel
trust.

The kernel composes factory operation contracts, not package layout, skill text,
or marketing labels. Installing an extension bundle or session capability makes
it discoverable; installation alone activates or authorizes nothing.

### EXT-001B — Three closed v1 factory operation roles

**Recommendation:** V1 has three foundational kernel-invokable operation roles:

1. **Intake mapping** — transforms a declared source-intent contract into a
   canonical candidate with complete trace, unknowns, defaults, and loss.
2. **Construction** — produces or coordinates bounded implementation artifacts
   from approved canonical input and declares whether each output is
   deterministically projected or custom-authored.
3. **Evaluation** — validates semantic definitions, graphs, source, binaries, or
   generated artifacts and returns structured evidence and diagnostics without
   mutating the subject.

Provider, adapter, generator, projector, validator, analyzer, gate, and host
projection are specializations or compositions of these roles, not separate
plugin mechanisms. Exact resolution and admission remain kernel responsibilities.
The external Spec Kit orchestration adapter is a client of the public factory
protocol, not an operation provider loaded into the kernel.

Migration is not a fourth primitive role or an active v1 workflow. V1 preserves
exact versions and admission artifacts, detects changed, drifted, or unsupported
contracts, and returns actionable diagnostics; it does not automate semantic,
implementation, deployment, or runtime-data migration. The entire migration
design is deferred until real use of an independently working CLI exposes a
concrete consumer version-change problem (`DEC-030`).

### EXT-002 — Role families are closed and protocol-versioned

**Recommendation:** The set of kernel-invokable factory operation roles is
closed for each factory-protocol version. A profile may specialize a role but
cannot invent a new invocation lifecycle or result shape. Adding a genuinely
new role requires an explicit protocol and kernel revision with compatibility
decisions. V1 does not require an automated migration path for that revision.

This does not freeze the ecosystem: new extension bundles, factory operation
contracts, operation providers, providers, targets, and profiles may be added
without changing the kernel when they fit an existing role. Unsupported roles
fail visibly rather than being invoked through reflection, naming convention,
or a generic arbitrary-code hook.

Session capabilities are not constrained to these three factory roles because
they may orchestrate several public operations and human decisions. They still
cannot create new kernel hooks, grant authority, or treat instructions as
factory evidence.

### EXT-003 — Extensions may carry vocabulary, never invent it during execution

**Recommendation:** An extension bundle may include or depend on exact versioned
vocabulary packages using the accepted semantic package protocol. That is how a
consumer, provider, or platform extension introduces new declarative terms
without a core change.

Operation providers may interpret, validate, map, construct, or evaluate only
vocabulary declared in their support envelope. Session capabilities may help a
human or AI propose vocabulary-backed intent but cannot approve it or make
undeclared meaning canonical. Neither kind may create undeclared semantic fields
at runtime, reinterpret unknown fields, mutate an approved vocabulary revision,
or treat implementation-specific metadata as canonical meaning unless an exact
vocabulary contract declares it.

### EXT-B01 delivery boundary

The first CLI does not need a marketplace, dynamic third-party loader, runtime
plugin host, Spec Kit adapter, or every historical extension family. It needs
only enough static registration to prove one exact construction operation
provider and one evaluation operation provider through the same public
contracts later extensions will implement.

The initial .NET/CShells path may use first-party in-process implementations.
That is an implementation profile, not permission to couple the kernel to their
concrete types or bypass factory operation contracts.

## 5. Active batch: Deterministic composition

`EXT-B02` resolves:

- `EXT-004`: whether one extension may modify another extension's output;
- `EXT-005`: who resolves conflicts at a shared target seam;
- `EXT-006`: when extension ordering is meaningful; and
- `EXT-007`: exact pins versus a compatibility solver.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### EXT-004 — Immutable contributions; one declared owner per final artifact

**Recommendation:** An operation provider cannot modify or delete an artifact
owned by another provider. Each invocation produces a declared immutable
candidate output set with identity, digest, provenance, and ownership.

When several extensions affect one final artifact, they do not take turns
editing the file. The target contract exposes a named contribution seam:

1. each contributor emits a canonical contribution record;
2. one exact assembler operation provider consumes the complete locked
   contribution set; and
3. that assembler alone owns the resulting file or artifact.

A downstream operation may consume an exact upstream artifact and create a new,
separately identified derivative only when its contract declares that
transformation. The upstream artifact and provenance remain unchanged.
Custom-authored consumer files are never adopted or overwritten merely because
they are inside a target directory.

### EXT-005 — The seam contract defines composition; the kernel enforces it

**Recommendation:** Every contribution seam declares its composition model,
cardinality, identity keys, compatibility rules, and final assembler contract.
Examples include one exclusive contribution, a uniquely keyed set, or
constraint-ordered contributions.

The seam's owning contract defines those rules. The kernel validates them and
refuses unresolved zero-match, multi-match, duplicate-key, incompatible, or
cyclic results. An extension may report a conflict but cannot resolve a conflict
in its own favor.

Resolution requires an explicit revised selection, compatible adapter, or
human-approved input. The accepted result is recorded in the resolution lock;
installation order and provider preference are never conflict-resolution rules.

### EXT-006 — Semantic order must be explicit and identity-forming

**Recommendation:** Ordering is meaningful only when the seam or factory
operation contract declares it. Meaningful order is represented through exact
phase, predecessor, successor, or dependency constraints and becomes part of
the canonical contribution set and resolution lock.

Filesystem enumeration, extension installation order, discovery order, service
registration order, and process scheduling have no semantic authority. If
declared constraints do not produce a permitted deterministic order, resolution
fails with an actionable ambiguity or cycle diagnostic.

Independent operations may execute in parallel. Their scheduling cannot affect
canonical bytes or final artifacts. A canonical tie-break may be used only when
the contract explicitly declares the tied contributions semantically
commutative; it cannot conceal meaningful ambiguity.

### EXT-007 — Exact v1 resolution; no compatibility solver

**Recommendation:** Every invoked extension bundle, factory operation contract,
operation provider, vocabulary, provider profile, target profile, and dependency
is exact in the accepted resolution lock.

Discovery may list installed candidates, declared compatibility, support
envelopes, and missing inputs. A human or explicitly approved selection policy
may choose a proposed candidate, but construction begins only after the complete
exact resolution is accepted and locked.

V1 includes no version-range solver, transitive best-match algorithm, or
automatic upgrade. A future deterministic solver would require a separately
accepted selection model, proof of a unique reproducible result, complete
explanation, and an explicit migration boundary. Until then, zero or multiple
acceptable candidates remain actionable resolution results rather than a reason
to guess.

### EXT-B02 delivery boundary

The initial CLI can prove these rules using statically registered first-party
operation providers, one named contribution seam, one assembler, and small
fixtures for duplicate, incompatible, cyclic, and ambiguously ordered
contributions. It does not require dynamic loading, a package marketplace, or a
version solver.

## 6. Revision record

- Created after Consumer Planning and Delivery closed under `DEC-029`.
- Recorded the Spec Kit adapter only as an accepted future external client; no
  adapter design was started.
- Reduced the archived extension taxonomy to candidate factory roles rather than
  assuming every historical label needs a separate plugin system.
- Separated session capabilities from executable factory operation providers;
  the bare term `capability` is no longer sufficient in normative contracts.
- Removed migration from the candidate primitive roles. Under `DEC-030`, its
  design is deferred until real consumer version evolution exposes a concrete
  problem after the CLI is independently usable.
- Accepted `EXT-B01` under `DEC-031` with separate normative identities for
  extension bundles, factory operation contracts, operation providers, session
  capabilities, vocabulary packages, and provider profiles.
- Accepted intake mapping, construction, and evaluation as the three initial
  factory operation roles; later roles may be added only through an explicit
  protocol revision.
- Activated `EXT-B02` for deterministic composition.

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

Define how the software factory gains target, provider, validation, construction,
and migration behavior without allowing extensions to bypass the kernel,
silently change meaning, introduce ambient selection, or create multiple
incompatible plugin mechanisms.

The category preserves these accepted boundaries:

- the kernel owns invariant enforcement, exact resolution, admission, and
  diagnostic truth; extensions cannot replace those mechanics;
- Program Kit operates within exact declared semantic and capability support
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
| `EXT-B01` | `EXT-001`–`EXT-003` | `active` | Define extension, capability, role-family, and vocabulary boundaries. |
| `EXT-B02` | `EXT-004`–`EXT-007` | `queued` | Define composition, output ownership, conflict resolution, ordering, and version selection. |
| `EXT-B03` | `EXT-008`–`EXT-011` | `queued` | Define trust, isolation, packaging, mandatory metadata, and conformance obligations. |

## 3. Accepted Spec Kit boundary

Program Kit v1 does not embed, wrap, or internally reuse Spec Kit as a product
dependency. Program Kit's own repository uses Spec Kit as its development
method. The selected guided consumer workflow later uses a separately installed,
separately versioned adapter that translates only between public Spec Kit and
Program Kit contracts. Governed by `DEC-029`.

## 4. Active batch: Minimum extension roles

`EXT-B01` resolves:

- `EXT-001`: which extension families are foundational;
- `EXT-002`: whether those families are closed and versioned; and
- `EXT-003`: whether extensions may add semantic vocabulary.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### EXT-001A — Extension is packaging; capability is behavior

**Recommendation:** Keep these concepts distinct:

- an **extension bundle** is a distributable, exact-versioned package that may
  contain capability implementations, vocabulary packages, target assets,
  schemas, diagnostics metadata, migrations, conformance fixtures, and
  documentation;
- a **capability contract** is one public, versioned factory behavior seam with
  a declared input, result, support envelope, determinism classification,
  evidence obligations, and diagnostics contract;
- a **capability implementation** is exact executable code satisfying one or
  more capability contracts;
- a **vocabulary package** is declarative semantic meaning under `DEC-025`, not
  executable extension code; and
- a **provider profile** describes one selectable provider implementation and
  the exact capability, contract, configuration, and support profiles it binds.

The kernel composes capability contracts, not package layout or marketing labels.
An extension bundle grants no authority merely because it is installed.

### EXT-001B — Four closed v1 factory capability roles

**Recommendation:** V1 has four foundational executable capability roles:

1. **Intake mapping** — transforms a declared source-intent contract into a
   canonical candidate with complete trace, unknowns, defaults, and loss.
2. **Construction** — produces or coordinates bounded implementation artifacts
   from approved canonical input and declares whether each output is
   deterministically projected or custom-authored.
3. **Evaluation** — validates semantic definitions, graphs, source, binaries, or
   generated artifacts and returns structured evidence and diagnostics without
   mutating the subject.
4. **Migration** — transforms an exact source revision toward an exact target
   contract through an explicit, inspectable migration result.

Provider, adapter, generator, projector, validator, analyzer, gate, and host
projection are specializations or compositions of these roles, not separate
plugin mechanisms. Exact resolution and admission remain kernel responsibilities.
The external Spec Kit orchestration adapter is a client of the public factory
protocol, not a capability loaded into the kernel.

### EXT-002 — Role families are closed and protocol-versioned

**Recommendation:** The set of kernel-invokable capability roles is closed for
each factory-protocol version. A profile may specialize a role but cannot invent
a new invocation lifecycle or result shape. Adding a genuinely new role requires
an explicit protocol and kernel revision with compatibility and migration
decisions.

This does not freeze the ecosystem: new extension bundles, capability contracts,
providers, targets, and profiles may be added without changing the kernel when
they fit an existing role. Unsupported roles fail visibly rather than being
invoked through reflection, naming convention, or a generic arbitrary-code hook.

### EXT-003 — Extensions may carry vocabulary, never invent it during execution

**Recommendation:** An extension bundle may include or depend on exact versioned
vocabulary packages using the accepted semantic package protocol. That is how a
consumer, provider, or platform extension introduces new declarative terms
without a core change.

Executable capabilities may interpret, validate, map, construct, evaluate, or
migrate only vocabulary declared in their support envelope. They cannot create
undeclared semantic fields at runtime, reinterpret unknown fields, mutate an
approved vocabulary revision, or treat implementation-specific metadata as
canonical meaning unless an exact vocabulary contract declares it.

### EXT-B01 delivery boundary

The first CLI does not need a marketplace, dynamic third-party loader, runtime
plugin host, Spec Kit adapter, or every historical extension family. It needs
only enough static registration to prove one exact construction capability and
one evaluation capability through the same public contracts later extensions
will implement.

The initial .NET/CShells path may use first-party in-process implementations.
That is an implementation profile, not permission to couple the kernel to their
concrete types or bypass capability contracts.

## 5. Revision record

- Created after Consumer Planning and Delivery closed under `DEC-029`.
- Recorded the Spec Kit adapter only as an accepted future external client; no
  adapter design was started.
- Reduced the archived extension taxonomy to candidate factory roles rather than
  assuming every historical label needs a separate plugin system.

---
artifact-kind: program-kit-design-category
category: determinism-and-generated-artifacts
status: active
last-updated: 2026-07-31
active-batch: DET-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Determinism and Generated Artifacts

## 1. Category objective

Define exactly what Program Kit means by deterministic construction, which
inputs form a construction identity, which outputs may carry which
reproducibility claims, and how generated artifacts are published, owned,
verified, and diagnosed without pretending that custom implementation or runtime
behavior was deterministically derived.

The category preserves these accepted boundaries:

- determinism applies only inside an exact supported semantic and operation
  envelope (`DEC-018`, `DEC-028`);
- custom implementation is bounded and evaluated but is not claimed to be
  deterministically derived;
- all executed providers and dependencies are exact in the accepted resolution
  lock (`DEC-032`);
- operation providers return immutable candidate outputs and one declared
  assembler owns each final generated artifact; and
- runtime behavior and automated migration are outside v1 (`DEC-030`).

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `DET-B00` | `DET-010` | `completed` | Bound deterministic construction separately from human judgment, custom implementation, conformance, and runtime behavior. |
| `DET-B01` | `DET-001`–`DET-003`, `DET-009` | `active` | Define reproducibility profiles, claim strengths, and the complete construction identity. |
| `DET-B02` | `DET-004`–`DET-007` | `queued` | Define atomic publication, generated-file ownership, editing, and drift handling. |
| `DET-B03` | `DET-008` | `queued` | Define retention and evidence sufficiency without prematurely designing archival policy. |

## 3. Accepted determinism boundary

Program Kit guarantees deterministic construction only after intent has been
accepted, every required input and selection is complete and exact, and the
requested operation is inside a declared support envelope. Semantic coverage,
construction method, and conformance are independent. This boundary is governed
by `DEC-018` and `DEC-028`.

## 4. Active batch: Reproducibility claims and construction identity

`DET-B01` resolves:

- `DET-001`: when equal inputs must produce byte-identical outputs across
  environments;
- `DET-002`: which output kinds require byte reproducibility;
- `DET-003`: which values form the exact construction identity; and
- `DET-009`: whether a weaker semantic-equivalence claim is permitted.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### DET-001 — Determinism is relative to a named reproducibility profile

**Recommendation:** Every deterministic construction claim names an exact
reproducibility profile. Equal construction identities under that profile must
produce byte-identical canonical outputs and identical output digests,
regardless of process scheduling or workspace location.

A profile may be portable across operating systems, architectures, and runtime
patches only when its conformance fixtures prove that portability. Otherwise
the relevant platform, architecture, runtime, SDK, and toolchain identities are
explicit parts of the construction identity. Program Kit must never imply
cross-platform reproducibility merely because two environments were described
as compatible.

Culture, timezone, current time, temporary paths, repository location,
filesystem enumeration order, machine identity, process identity, random
values, and undeclared environment variables have no ambient authority. A
provider must normalize them away, declare an exact value as an input when it
has real semantic meaning, or reject the operation as non-reproducible. Hidden
environmental influence is a provider defect, not acceptable variance.

### DET-002 and DET-009 — Claims have explicit strengths and cannot be blurred

**Recommendation:** An operation output declares one of three construction
classifications:

1. **canonical-byte reproducible** — the same construction identity must yield
   the same bytes and digest;
2. **verified-equivalent** — original bytes may differ, but a named exact
   verifier evaluates a declared equivalence relation and records both original
   digests and evidence; or
3. **custom-bounded** — Program Kit did not derive the implementation and makes
   no reproducibility claim, but preserves its digest and evaluates it against
   the applicable contracts.

Canonical Program Kit JSON, manifests, locks, contribution records, machine
results, generated source, project files, configuration, infrastructure
descriptions, and other Program Kit-owned text artifacts must be
canonical-byte reproducible. Human renderings are projections of machine
results and are not canonical truth.

External compiler, formatter, packager, or build outputs receive a byte-level
claim only when the selected provider profile proves it for the exact toolchain
and reproducibility profile. Otherwise they may receive a separately named
verified-equivalence claim or no determinism claim. "Semantically equivalent"
is never an unnamed escape hatch and never substitutes for the canonical source
or evidence artifact.

### DET-003 — Every output-affecting input belongs to construction identity

**Recommendation:** A construction identity is a canonical digest over the
complete resolved operation closure, including at least:

- the factory protocol, kernel, CLI distribution, operation contract, and
  canonicalization-profile revisions;
- the accepted operation request, root software-definition manifest, resolved
  semantic graph, resolution lock, and all referenced input bytes and digests;
- every extension bundle, operation provider, vocabulary, provider profile,
  target profile, template, formatter, tool, SDK, and dependency used;
- every selected construction option, declared default, feature switch,
  ordering constraint, approved exception, and policy input; and
- every platform or environment property that the selected reproducibility
  profile declares output-affecting.

Execution metadata such as duration, absolute workspace path, host process, and
observation timestamp may appear in a non-canonical execution receipt but
cannot affect generated bytes. Secret values and deployment-time configuration
are late-bound and must not enter generated output or construction identity;
their typed parameter contracts and non-secret identifiers may do so.

Any provider that needs network-fetched or externally observed content must
resolve it to exact retained bytes and a digest before construction. If an
output-affecting value cannot be declared and captured, Program Kit must not
issue a deterministic claim for the result.

### DET-B01 delivery boundary

The first CLI needs one versioned reproducibility profile, one canonical
construction-identity record, and fixtures proving that repeated execution from
different workspace paths and cultures yields identical generated bytes. It
also needs negative fixtures showing that an undeclared varying input fails the
claim and that an identity-forming change produces a different construction
identity.

It does not need to prove reproducible binaries for every .NET SDK, operating
system, or architecture. Those claims remain absent until a provider profile
supplies evidence.

## 5. Revision record

- Created after Extensions and Composition closed under `DEC-033`.
- Preserved the already accepted `DET-010` boundary from `DEC-018` and
  `DEC-028`.
- Activated `DET-B01` to prevent an unscoped or environment-dependent use of
  the word deterministic before generated-file ownership and drift are defined.

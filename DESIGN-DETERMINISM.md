---
artifact-kind: program-kit-design-category
category: determinism-and-generated-artifacts
status: closed
last-updated: 2026-08-01
active-batch: none
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
| `DET-B01` | `DET-001`–`DET-003`, `DET-009` | `completed` | Define reproducibility profiles, claim strengths, and the complete construction identity. |
| `DET-B02` | `DET-004`–`DET-007` | `completed` | Define atomic publication, generated-file ownership, editing, and drift handling. |
| `DET-B03` | `DET-008` | `completed` | Define retention and evidence sufficiency without prematurely designing archival policy. |

## 3. Accepted determinism boundary

Program Kit guarantees deterministic construction only after intent has been
accepted, every required input and selection is complete and exact, and the
requested operation is inside a declared support envelope. Semantic coverage,
construction method, and conformance are independent. This boundary is governed
by `DEC-018` and `DEC-028`.

## 4. Accepted batch: Reproducibility claims and construction identity

`DET-B01` resolves:

- `DET-001`: when equal inputs must produce byte-identical outputs across
  environments;
- `DET-002`: which output kinds require byte reproducibility;
- `DET-003`: which values form the exact construction identity; and
- `DET-009`: whether a weaker semantic-equivalence claim is permitted.

The human accepted all four recommendations. They are governed by
`DEC-034`.

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

## 5. Accepted batch: Atomic publication, ownership, and drift

`DET-B02` resolves:

- `DET-004`: whether generation yields one complete trusted artifact set or no
  trusted output;
- `DET-005`: whether consumers may edit generated files;
- `DET-006`: how generated and consumer ownership remain unambiguous; and
- `DET-007`: how Program Kit responds to generated-artifact drift.

The human accepted all four recommendations. They are governed by
`DEC-035`.

### DET-004 — Artifact sets are logically atomic and physically recoverable

**Recommendation:** Construction first writes an immutable candidate artifact
set into an isolated staging location. Its manifest declares every path,
digest, provenance record, construction classification, and owner. Program Kit
performs all mandatory candidate validation and a collision/precondition check
before modifying live consumer paths.

Trust is atomic at the artifact-set level: the complete set receives one
admission and publication receipt only after all mandatory checks and writes
succeed. A failed or interrupted operation produces no partially trusted new
state. The candidate and diagnostics may be retained outside live paths for
inspection, but they are not admitted outputs.

Program Kit must not claim that arbitrary multi-file writes are physically
atomic on every filesystem. It uses atomic replacement where supported and an
exact publish plan, pre-write fingerprints, and recoverable journal otherwise.
An interruption or failed rollback leaves an explicit incomplete-publication
state that the next operation detects and refuses to treat as trusted. The last
complete receipt remains the last trusted state.

### DET-005 and DET-006 — Ownership is per artifact, never mixed inside a file

**Recommendation:** Every materialized artifact has exactly one of three
ownership modes:

1. **Program Kit generated-owned** — canonically reproducible bytes that
   Program Kit may replace only when the observed current digest matches its
   recorded precondition or an explicit repair is authorized. Consumer edits
   are drift, not new canonical input.
2. **Seeded handoff** — Program Kit creates an initial artifact only when the
   target is absent. Successful publication transfers ownership to the
   consumer; subsequent content is `custom-bounded`, and Program Kit never
   regenerates or overwrites it implicitly.
3. **Consumer-owned** — created and maintained outside the operation. A
   provider may read it only as a declared input and may never modify it.

V1 permits no generated and editable regions inside the same file. Marker
blocks and heuristic merges obscure authority and make regeneration unsafe.
Composition instead uses separate partial-class files, sibling artifacts,
explicit contribution records, include/import seams, or another target-owned
structured boundary. A future structured merge profile would need an exact
parser, canonical ownership model, conflict semantics, and conformance proof.

The artifact-set manifest records the owner authority and ownership mode.
Creating a seed is deterministic; the consumer's later implementation is not.
This allows Program Kit to help start custom code without later claiming or
destroying it.

### DET-007 — Drift is diagnosed before any explicit repair

**Recommendation:** Evaluation is read-only and classifies each governed
artifact at least as exact, missing, modified under the same construction
identity, stale because its construction identity changed, blocked by a path
collision, or indeterminate after interrupted publication.

The default construction path fails closed rather than overwriting a modified,
missing, colliding, or indeterminate live artifact. Its machine result reports
the expected and observed identities, ownership, consequence, and permitted
next actions. Program Kit never silently adopts edited generated bytes,
reverse-engineers them into canonical intent, or repairs them as a side effect
of evaluation.

Repair is a separate, explicit construction request. Safe actions may include
previewing the candidate difference, restoring exact generated-owned bytes,
moving a colliding consumer artifact, or revising the authoritative definition
and ownership. Reclassifying generated-owned output as consumer-owned requires
a human-approved definition change; an `accept drift` shortcut cannot present
custom bytes as deterministically generated.

A changed construction identity is a new construction request, not an
automated migration. This batch does not reopen migration scope.

### DET-B02 delivery boundary

The first CLI needs an isolated candidate directory, artifact-set manifest,
preconditioned publish plan, completion receipt, and recoverable interrupted
publication marker. One generated-owned file and one seeded-handoff file are
enough to prove ownership. Fixtures must cover modification, deletion,
collision, stale identity, and interrupted publication.

V1 does not need a general merge engine, source-control integration, arbitrary
filesystem transactions, or automatic repair.

## 6. Accepted batch: Retention and evidence sufficiency

`DET-B03` resolves `DET-008`: whether canonical inputs must be retained forever
or whether a generation manifest alone can remain sufficient evidence.

The human accepted the recommendation. It is governed by
`DEC-036`.

### DET-008 — Reproducibility requires resolvable bytes, not eternal retention

**Recommendation:** A construction manifest, resolution lock, and receipt are
the authoritative index and historical record of what Program Kit used and
claimed. They are not by themselves sufficient to reproduce or currently
verify an output when the exact referenced content is unavailable. A signature
could authenticate a record but cannot recover missing bytes or prove their
present availability.

For as long as an admitted construction is presented as actively supported or
reproducible, every identity-forming canonical input, provider, template, tool
artifact, dependency, and applicable evidence must remain exactly resolvable
and digest-verifiable under a declared retention and support policy. Content
may live in the repository, selected Program Kit distribution, an immutable
package source, or a content-addressed store; location is not authority and
duplication inside every consumer repository is not required.

Program Kit does not impose eternal retention. When policy expires or exact
content becomes unavailable, the historical receipt still records the prior
operation, but Program Kit must report that current reproduction,
re-evaluation, or repair is unavailable or stale. It cannot continue making an
active reproducibility claim from hashes alone. Evidence freshness and support
policy determine whether admission remains current; history is not silently
rewritten.

Secret values are never retained as reproducibility inputs. Only their
non-secret parameter contracts and identifiers may be governed. Transient
staging bytes, caches, human renderings, and ordinary logs need not be retained
after their declared purpose, provided no manifest identifies them as canonical
input or required evidence.

V1 requires no signing infrastructure, archival service, garbage collector, or
content-addressed repository product. It needs complete digest references,
availability preflight for the selected operation, and a stable diagnostic when
a required exact input cannot be resolved. A fixture that removes one
referenced input is sufficient to prove the failure boundary.

### DET-B03 delivery boundary

The first CLI retains its root definition, resolution lock, construction
identity, artifact-set manifest, publication receipt, and applicable evidence.
It verifies every required referenced input before claiming reproduction. The
consumer or selected distribution may retain the bytes; Program Kit must know
their exact identities and refuse unavailable claims.

## 7. Revision record

- Created after Extensions and Composition closed under `DEC-033`.
- Preserved the already accepted `DET-010` boundary from `DEC-018` and
  `DEC-028`.
- Activated `DET-B01` to prevent an unscoped or environment-dependent use of
  the word deterministic before generated-file ownership and drift are defined.
- The human accepted `DET-B01` in full under `DEC-034`.
- Established named reproducibility profiles, explicit byte/equivalence/custom
  claim strengths, and a complete construction identity with no ambient
  output-affecting inputs.
- Completed `DET-B01` and activated `DET-B02` for logical atomicity, generated
  artifact ownership, consumer editing, and drift handling.
- The human accepted `DET-B02` in full under `DEC-035`.
- Established logical artifact-set atomicity with recoverable physical
  publication, explicit generated/seeded/consumer ownership, and no mixed file
  ownership in v1.
- Required read-only drift diagnosis and separately authorized repair.
- Completed `DET-B02` and activated final Determinism batch `DET-B03`.
- The human accepted `DET-B03` under `DEC-036`: active reproducibility requires
  exact referenced bytes to remain resolvable under a declared policy; records
  and signatures cannot substitute for unavailable content.
- Closed Determinism and Generated Artifacts and activated Diagnostics and AI
  Guidance.

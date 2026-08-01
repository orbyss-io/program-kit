---
artifact-kind: program-kit-design-category
category: first-vertical-slice
status: closed
last-updated: 2026-08-01
active-batch: none
parent-ledger: DESIGN.md
---

# Program Kit Design — First Vertical Slice

## 1. Category objective

Choose the smallest real end-to-end consumer proof that makes Program Kit
tangible without hiding missing foundations behind a large sample. The slice
must exercise public factory contracts, exact integration, generated .NET
artifacts, CShells participation, diagnostics, evidence, repeatability, and
drift handling while preserving independent bootstrap and all v1 scope limits.

The category preserves these accepted boundaries:

- Program Kit is a human-governed software factory, not a planning or runtime
  product (`DEC-028`–`DEC-030`);
- the first .NET profile uses .NET 10 and CShells with exact dependencies
  (`DEC-021`, `DEC-043`);
- factory roles are intake mapping, construction, and evaluation (`DEC-031`);
- generated artifacts, contributions, publication, diagnostics, authority, and
  gates follow their accepted contracts; and
- the Program Kit repository never requires this slice to build or repair the
  kernel (`DEC-041`).

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `VSL-B01` | `VSL-001`–`VSL-005` | `completed` | Select the reference consumer, proof flow, first host, and first composition seam. |
| `VSL-B02` | `VSL-006`–`VSL-008` | `completed` | Define product-failure criteria, architect-visible value, and the AI-readable system artifact. |

## 3. Accepted batch: Reference consumer and proof flow

`VSL-B01` resolves:

- `VSL-001`: the smallest real consumer system that proves the thesis;
- `VSL-002`: whether feature definition and diagnostics precede host generation;
- `VSL-003`: the exact first proof flow;
- `VSL-004`: the first generated host type; and
- `VSL-005`: the first extension seam to prove.

The human accepted all five recommendations. They are governed by
`DEC-044`.

### VSL-001 — Two bundles prove contract-governed integration

**Recommendation:** The first slice uses a deliberately small consumer-owned
reference capability named `Reference.Status`. The name and behavior are test
fixture semantics, not Program Kit kernel vocabulary.

The slice constructs two independently identified software-definition bundles:

1. **Status component bundle** — a .NET class-library/package with a
   consumer-owned `IStatusProvider` contract, one custom-bounded implementation,
   and a CShells `IFeature` that registers the implementation through the
   selected .NET/CShells profile.
2. **Status API bundle** — an ordinary ASP.NET Core application that consumes
   the exact component package and contract, activates the feature, and exposes
   one HTTP `GET /status` endpoint through a generated host projection.

The component is packed to an isolated local test feed and the host consumes an
exact package version and digest through its accepted resolution lock. This
proves Program Kit's central promise across two constructed products without
requiring external publication, authentication, persistence, deployment, or a
Program Kit runtime.

The custom status behavior remains seeded-handoff or consumer-owned code. The
projects, package references, CShells plumbing, contribution record, host
assembly, manifests, locks, and evidence are Program Kit-owned deterministic
artifacts. The slice therefore proves the boundary between custom meaning and
deterministic integration instead of disguising all code as generated.

### VSL-002 — Definition and diagnostics are proven before host generation

**Recommendation:** The slice first proves that Program Kit can understand and
refuse a bounded component definition before producing an application. An
invalid reference fixture must return the universal structured result with
stable diagnostic ID, subject, rule, cause, effect state, primary disposition,
and typed remediation. No live project files are written.

Only a valid, complete, authorized, and exactly resolved definition reaches
construction. Host generation is the final integration proof, not the first
place ambiguity or missing meaning is discovered.

### VSL-003 — One staged public flow exercises all three operation roles

**Recommendation:** The executable proof follows this public-contract sequence:

1. map one small declared consumer intake into a canonical candidate with trace,
   supplied/defaulted fields, and no silently lost meaning;
2. validate identity, references, schema, vocabulary, authority, and required
   inputs through structured diagnostics;
3. resolve exact contracts, providers, .NET/CShells profile, package inputs,
   target profile, catalog, and toolchain into an accepted lock;
4. construct immutable component and host candidate artifact sets in isolation;
5. evaluate source, projects, contribution seam, package, build, and applicable
   contracts before publication;
6. publish each complete artifact set under exact preconditions and issue
   receipts;
7. pack the component to an isolated local feed, restore/build the host, and run
   one black-box endpoint test as external-tool evidence;
8. repeat construction from another workspace path and culture and prove
   identical canonical generated bytes; and
9. modify one generated-owned file, detect drift without mutation, preview the
   exact repair, and restore it only through an authorized repair request.

The flow is directly callable through Program Kit's public CLI and machine JSON
results. Spec Kit may prepare the implementation specification for this
repository, but no Spec Kit adapter or Program Kit-native planning artifact is
part of the slice.

### VSL-004 — The first host is a minimal ASP.NET Core API

**Recommendation:** Use a generated ASP.NET Core minimal API host rather than a
console or worker host. ASP.NET Core ships with the selected .NET platform,
produces a visible ordinary application, exercises dependency injection and
CShells feature activation, and proves a real external interface without adding
a database, broker, UI framework, deployment system, or Program Kit runtime.

Program Kit owns only construction and development-time evaluation. The API
runs as normal generated software for its black-box test and has no dependency
on the Program Kit kernel or CLI after construction.

### VSL-005 — Prove one HTTP endpoint contribution seam, not OpenID Connect

**Recommendation:** The first composition extension is the exact first-party
.NET/ASP.NET host projection with one named HTTP endpoint contribution seam.
The Status component or its exact adapter emits a canonical endpoint
contribution record; one host assembler owns the final generated endpoint map
and application plumbing. Duplicate route identity, incompatible contract,
missing assembler, and ambiguous order fixtures fail with stable diagnostics.

OpenID Connect, Keycloak, Entra ID, persistence, OpenTelemetry, secrets
providers, deployment, and infrastructure are intentionally not the first seam.
They require broader provider contracts and would let product complexity hide
whether the kernel's identity, composition, ownership, diagnostics, and
determinism mechanics actually work.

The endpoint contract is platform vocabulary owned by the exact ASP.NET
provider package. `Reference.Status` remains consumer vocabulary. Neither is
hard-coded as universal kernel meaning.

### VSL-B01 delivery boundary

The first slice needs two definition bundles, one first-party .NET/CShells
construction provider, one ASP.NET host provider, one endpoint contribution and
assembler, one local package feed, invalid and conflict fixtures, deterministic
artifact manifests, and a black-box endpoint test.

It does not need an extension marketplace, external package publication,
database, authentication, telemetry, infrastructure generation, migration,
runtime control plane, Spec Kit adapter, or a second programming ecosystem.

## 4. Accepted batch: Product proof and system understanding

`VSL-B02` resolves:

- `VSL-006`: what makes the slice a product failure even when tests pass;
- `VSL-007`: the first architect-visible value beyond ordinary .NET tooling; and
- `VSL-008`: the exact artifact a new AI session reads before source code.

The human accepted all three recommendations. They are governed by
`DEC-045`.

### VSL-006 — Green tests cannot excuse a false product proof

**Recommendation:** The vertical slice is a product failure if any of these are
true, even when every automated test passes:

- `Reference.Status`, its contract, route, package, or project names are
  special-cased in the kernel instead of expressed through consumer vocabulary
  and exact provider contracts;
- a manual edit, ambient machine state, discovery order, unpinned dependency,
  implicit selection, or undocumented command is required between public CLI
  operations;
- the generated host needs Program Kit, its semantic model, or an AI session at
  runtime;
- custom-bounded implementation is presented as deterministically derived or a
  generated file can overwrite consumer-owned work;
- invalid, ambiguous, stale, drifted, unavailable, or faulted input lacks a
  stable machine result that tells an AI whether to provide input, request
  approval, repair, revise, retry, or stop;
- the component/host integration cannot be explained from exact contract,
  provider, lock, contribution, artifact, and evidence records without first
  reverse-engineering source;
- repeated construction cannot reproduce bytes, drift cannot be detected before
  mutation, or interrupted publication can be mistaken for trusted state;
- the sample bypasses the same public operation contracts, authority, gates,
  diagnostics, or provider manifests that real consumers must use; or
- Program Kit cannot be built and repaired independently when the entire slice
  and its generated outputs are removed.

The acceptance record includes an explicit human product review against these
criteria in addition to automated evidence. A fresh contributor must be able to
complete the documented valid, invalid, repeatability, and drift walkthrough in
at most one hour from the pinned prerequisites, without undocumented recovery
knowledge.

### VSL-007 — The first visible value is an integration resolution explanation

**Recommendation:** Before showing generated code, Program Kit presents an
**Integration Resolution Explanation** for the selected root bundle. Its human
view answers:

- what the component and host mean according to their approved declarations;
- which consumer owns each contract and which implementation was selected;
- why the exact host may consume the exact component;
- whether the relation is direct, adapted, or incompatible;
- which provider/profile, endpoint contribution, assembler, dependency, and
  target decisions produced the result;
- which artifacts are generated-owned, seeded-handoff, or consumer-owned;
- which meaning is covered, custom-bounded, unresolved, or unsupported; and
- which gates, evidence, waivers, warnings, and diagnostics support or block
  admission.

This is the first thing an architect sees that a solution file, project graph,
NuGet restore, or dependency-injection container cannot provide: a human-owned
semantic and authority explanation of why integration is valid. It does not
claim full impact analysis, migration planning, runtime health, or source-level
behavioral understanding.

The explanation is a deterministic human projection of the same structured
artifact used by automation; it is not AI-authored summary prose.

### VSL-008 — One canonical scoped workspace snapshot starts every AI session

**Recommendation:** Construction and evaluation produce a generated-owned
canonical artifact at `.program-kit/workspace.snapshot.json` with artifact type
`program-kit.workspace-snapshot/v1`.

The snapshot is scoped to one exact root software-definition bundle and finite
resolved operation closure. It contains or references:

- root, bundle, feature, component, interface, and contract identities and
  immutable revisions;
- approved purpose and semantic-definition references without duplicating their
  authority-owned meaning;
- semantic coverage and construction classification for each governed subject;
- exact contract bindings, implementation selections, provider/target profiles,
  resolution lock, and the reason each relation resolved;
- the component/dependency graph, contribution seams, assemblers, and exposed
  endpoint contract;
- artifact paths, ownership modes, digests, provenance, and construction
  identities;
- applicable gates, review records, waivers, evidence, receipts, support and
  retention status; and
- unresolved, unsupported, stale, drifted, unavailable, redacted, and diagnostic
  states with exact explanation references.

Every field traces to an authoritative artifact; copied meaning, inference, and
generated prose are prohibited. The snapshot records its root request, closure,
and evidence digests. Evaluation refuses to present it as current when any
input or governed artifact is stale or drifted.

A new AI session first invokes the public structured inspect/evaluate operation
and reads this snapshot plus only the referenced declarations needed for its
task. It reads implementation source when debugging or changing custom behavior,
but not merely to reconstruct already governed identity and integration. The
snapshot is a reproducible view, never a competing source of truth or a global
semantic graph.

### VSL-B02 delivery boundary

The slice needs the canonical workspace snapshot, its deterministic human
Integration Resolution Explanation, stale-snapshot diagnostics, a one-hour
walkthrough, and a human product-review record covering every failure criterion.

It does not need generalized impact analysis, migration, AI-generated semantic
summaries, a global graph database, or automatic source-code understanding.

## 5. Revision record

- Created after Governance, Enforcement, and Self-Hosting closed under
  `DEC-043`.
- Chose a two-bundle integration proof so the non-negotiable product promise is
  exercised before adding broad platform capabilities.
- Activated `VSL-B01` for the reference consumer, proof flow, host, and seam.
- The human accepted `VSL-B01` in full under `DEC-044`.
- Selected independently identified Status component and ASP.NET API bundles,
  exact local-package integration, diagnostics-first progression, the complete
  public factory flow, and one HTTP endpoint contribution seam.
- Kept custom behavior consumer-owned and every plumbing/integration claim
  inside the deterministic construction envelope.
- Completed `VSL-B01` and activated final design batch `VSL-B02` for failure
  criteria, architect-visible value, and the AI-readable workspace snapshot.
- The human accepted `VSL-B02` under `DEC-045`.
- Made hard-coding, ambient/manual steps, false determinism, runtime coupling,
  poor diagnostics, unexplained integration, unreproducibility, public-contract
  bypass, and bootstrap coupling semantic product failures even with green tests.
- Established one structured workspace snapshot and deterministic Integration
  Resolution Explanation for architects and AI sessions.
- Closed First Vertical Slice and completed design convergence.

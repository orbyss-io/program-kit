---
artifact-kind: program-kit-design-category
category: product-identity
status: active
last-updated: 2026-07-31
active-batch: PID-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Product Identity


### 7.1 Category objective

Converge on what Program Kit is, whom it serves, the promise that governs
tradeoffs, the authors and consumers of its semantic input, its initial
ecosystem boundary, its first-hour proof of value, and its deliberate non-goals.

### 7.2 Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `PID-B01` | `PID-001`, `PID-002`, `PID-008` | `active` | Establish governing identity, primary promise, and the boundary with Spec Kit. |
| `PID-B02` | `PID-003`–`PID-005` | `queued` | Establish authorship, ecosystem scope, and first-hour proof. |
| `PID-B03` | `PID-006`–`PID-007` | `queued` | Establish deliberate refusals and language/toolchain naming. |

### 7.3 Product identity questions and decision records

#### PID-001 — Governing product identity

- **Status:** `open`
- **Question:** Is Program Kit primarily a semantic compiler/toolchain, an
  SDK/framework, or both? If these identities conflict, which one governs the
  design tradeoff?
- **Why it matters:** This determines whether authored semantics and compiled
  evidence lead the architecture, or whether runtime APIs and framework
  ergonomics do.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-002 — Governing product promise

- **Status:** `open`
- **Question:** What is the single most important promise Program Kit must keep:
  reusable features, deterministic system construction, change and migration
  safety, reliable understanding for AI agents, or another promise? The other
  benefits can remain important, but which one wins when they compete?
- **Why it matters:** A product with several equal primary promises cannot make
  hard scope or architecture decisions consistently.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-003 — Authors of canonical semantic input

- **Status:** `open`
- **Question:** Who is expected to author the canonical semantic input:
  architects, developers, domain experts, AI agents, or a defined collaboration
  among them? Who has final authority when their inputs disagree?
- **Why it matters:** This governs language ergonomics, validation, approvals,
  provenance, diagnostics, and how much judgment automation may exercise.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-004 — Initial ecosystem boundary

- **Status:** `open`
- **Question:** Is the first product deliberately .NET-specific, or must its
  semantic core be ecosystem-independent from day one even if the first
  projections target .NET?
- **Why it matters:** Premature neutrality can weaken the first proof, while an
  accidental .NET worldview can prevent the intended semantic portability.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-005 — First-hour proof of value

- **Status:** `open`
- **Question:** What must a consumer accomplish in their first hour with Program
  Kit for the product to have proved that it is useful and meaningfully
  different from ordinary .NET tooling or a template generator?
- **Why it matters:** This defines the earliest honest vertical slice and keeps
  the redesign anchored in observable user value.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-006 — Deliberate first-major-version refusals

- **Status:** `open`
- **Question:** What must Program Kit explicitly refuse to do in its first major
  version, even if doing it would be attractive or impressive?
- **Why it matters:** Refusals protect the product boundary and prevent future
  ambitions from obscuring the foundational proof.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-007 — Programming language or language toolchain

- **Status:** `open`
- **Question:** Is Program Kit itself the programming language, or is it the
  compiler/toolchain for a separately named semantic language or model?
- **Why it matters:** This affects terminology, user expectations, artifact
  ownership, compatibility, and whether the CLI name and language name should
  remain distinct.
- **Human input:** Pending.
- **Agent synthesis:** Pending.
- **Consequences and tensions:** Pending.
- **Candidate decision:** Pending.

#### PID-008 — Responsibility boundary with Spec Kit

- **Status:** `follow-up`
- **Origin:** The human identified that the archived Program Kit took on work
  that is better performed by Spec Kit and requested an especially clear
  constitutional boundary.
- **Question:** Which lifecycle responsibilities belong to Spec Kit and must not
  be reimplemented by Program Kit, and what distinct responsibility begins at
  the Program Kit boundary?
- **Why it matters:** Without this seam, the redesign can reproduce the old
  scope confusion, create competing sources of truth, and potentially restore a
  circular dependency under a different shape.
- **Human input:** Program Kit may eventually export defined capabilities that
  use some Spec Kit techniques inside a governed flow and combine them with
  Program Kit CLI extensions. That possibility should be explored later, not
  assumed now. The immediate constitutional need is to say unambiguously what
  Program Kit is and is not.
- **Agent synthesis:** Treat Spec Kit's discovery/specification/planning workflow
  as an upstream or collaborating authority rather than Program Kit-owned
  functionality. Require every proposed Program Kit responsibility to justify
  the distinct semantic construction, projection, integrity, or evolution
  concern it serves. Do not port an archived capability until it passes that
  boundary test.
- **Consequences and tensions:** A future integration can still be valuable, but
  invoking a Spec Kit capability is not the same as owning or recreating that
  capability. The dependency direction, artifact handoff, authority, version
  pinning, failure semantics, and isolation would all need explicit contracts.
- **Candidate decision:** Pending answers to `PID-001`, `PID-002`, and the exact
  lifecycle split requested here.

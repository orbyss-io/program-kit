<!--
Sync Impact Report
- Version change: unversioned Spec Kit template -> 0.1.0 proposal
- Modified principles: all template placeholders replaced by thirteen Program Kit principles
- Added sections: Product Boundary and Core Terms; Development Workflow and Quality Gates
- Removed sections: none
- Follow-up TODOs: explicit human ratification and ratification date remain pending
-->

# Program Kit Constitution

> **Proposal status:** This document is an initial governance proposal. It has no
> ratified authority until a human explicitly accepts its exact contents.

## Core Principles

### I. Human Authority Over Meaning and Scope

Humans MUST own product meaning, architectural decisions, risk acceptance, and
the authority to begin or continue implementation. Agents and tools MAY extract,
challenge, relate, and propose; they MUST NOT approve their own interpretation,
broaden scope, or turn a successful operation into semantic authority. Material
changes to approved intent, architecture, compatibility, migration, or proof
obligations MUST return to explicit human review of exact artifacts.

### II. Consumer-Owned Semantics, Domain-Neutral Mechanics

Program Kit MUST provide reusable mechanics without inventing consumer domain
vocabulary, business rules, authorization meaning, deployment intent, or
production policy. Consumer-defined meaning MUST remain in explicitly owned
semantic contracts and layers. A capability belongs in Program Kit only when its
contract is demonstrably domain-neutral; recurring words or one consumer's reuse
desire are insufficient evidence. Program Kit MUST NOT become a universal domain
model, workflow engine, runtime orchestrator, or owner of consumer state.

### III. The Feature Is the Fundamental Governed Interface

Every modeled capability MUST be represented as a feature with one stable
identity, semantic owner, version, purpose, and explicit internal and/or external
contracts. A feature definition MUST declare its dependencies, artifacts,
invariants, observable outcomes, extension points, compatibility policy, and
migration obligations. Every component MUST declare which features it realizes
or composes. A feature is not implicitly a project, package, host, class, or
deployment unit, and physical containment MUST NOT substitute for semantic
ownership.

### IV. Semantic Layers and Bounded Implementation Contexts

Consumer logic MUST live inside an explicit semantic layer that identifies the
meaning and ownership of its features and relationships. Every change MUST be
performed within a bounded implementation context that binds the exact semantic
intent, selected features and components, dependency closure, allowed artifacts
and edits, canonical profiles and tool versions, required evidence, migration
scope, and stop conditions. Work outside that boundary MUST stop for a new human
decision rather than being absorbed as incidental implementation.

### V. Typed, Versioned, and Canonical Contracts

Identity-forming and decision-changing inputs MUST use explicit typed, versioned
contracts. Each contract MUST define validation, compatibility, canonicalization,
collection semantics, diagnostics, and evolution rules appropriate to its role.
References MUST bind enough identity and version information to reject ambiguity;
a name, path, package presence, or bare digest MUST NOT silently become complete
identity. Invalid, ambiguous, duplicate, conflicting, unsupported, or
non-canonical input MUST produce stable findings and no trusted partial result.

### VI. Deterministic Mechanics Belong to Code

Validation, canonicalization, dependency closure, transformation, generation,
hashing, rendering, version selection, and evidence production MUST be
implemented as code-owned operations where Program Kit claims repeatability.
Given the same complete canonical inputs, selected contracts, profiles,
extensions, and tool versions, an operation MUST produce the same declared
semantic result and selected output bytes, or fail explicitly. Agents MAY choose
and invoke supported operations; they MUST NOT improvise their non-negotiable
mechanics. Determinism claims MUST NOT extend to arbitrary AI-authored code,
external reality, or omitted observations.

### VII. Dependency Topology and Migration Integrity

Dependencies MUST be explicit, typed, directionally owned, and inspectable.
Allowed directions, edge meanings, cardinality, cycle policy, and selection rules
MUST be defined by contract rather than inferred from folders or build success.
A versioned change MUST identify known affected features, components, consumers,
owners, causal paths, compatibility findings, migration actions, safe order, and
terminal dispositions. Unknown or external impact MUST remain explicitly unknown.
Unchanged affected elements require evidence or an explicit disposition, not
silent omission.

### VIII. Explicit Extensions Without Ambient Discovery

Program Kit extensions MUST enter through named, typed, versioned extension
contracts with an explicit semantic owner, compatibility range or exact pin,
configuration, inputs, outputs, ordering, and failure behavior. Extension
selection MUST be explicit and identity-forming when it can change results.
Assembly scanning, directory scanning, registration order, `latest`, best-match,
first-compatible, silent fallback, and mutable global registries MUST NOT define
semantics. An extension MAY adapt or project an owned contract; it MUST NOT
silently redefine another owner's meaning or broaden authority.

### IX. Constitutional Rules Are Enforced at the Earliest Reliable Layer

Every non-negotiable architecture or source rule MUST be assigned to the
narrowest reliable enforcement layer: type system, schema validation, compiler,
Roslyn analyzer, MSBuild gate, architecture test, executable conformance test, or
explicit human review. Rules that can be enforced statically MUST NOT depend on
late narrative analysis for discovery. Gate identity, revision, configuration,
source coverage, suppressions, and participation MUST be verifiable. A failing
gate MUST be fixed or the governing decision amended; it MUST NOT be weakened,
bypassed, or reclassified merely to make work pass.

### X. Evidence Is Exact, Fresh, Multidimensional, and Fail-Closed

Evidence MUST bind its exact inputs, versions, operation, implementation,
outputs, scope, and applicable observations. Approval, validation, compatibility,
integrity, operational completion, output availability, and production readiness
MUST remain distinct claims. Missing, stale, changed, incompatible, conditional,
rejected, superseded, incomplete, or unauthorized evidence MUST stop at the
applicable gate. Summaries and receipts MUST remain traceable to underlying
artifacts and MUST NOT fabricate certainty after unknown or partial effects.

### XI. Diagnostics Are Actionable Public Contracts

Every admitted Program Kit operation MUST return a meaningful typed outcome;
silence, a generic failure, a raw exception, or an unqualified Boolean is not an
acceptable contract. A versioned diagnostic catalog MUST give each finding a
stable identity, severity, category, stage, affected subject and location,
violated contract or rule, cause, disposition, and safe corrective guidance.
Guidance MUST tell a human or AI session whether it can repair input, select a
compatible contract, retry under stated conditions, gather missing evidence, or
stop for human authority. Diagnostics MUST be deterministic in identity and
ordering for identical findings, machine-readable, redaction-safe, and explicit
when information is unknown, unavailable, withheld, truncated, or incomplete.
Diagnostic revisions and removals MUST follow compatibility and migration rules.

### XII. Consumer Ownership and Runtime Isolation

Generated projects, packages, source, configuration, documentation, analyzers,
and hosts MUST remain ordinary, inspectable, testable, consumer-owned artifacts.
Runtime libraries MUST NOT load development capabilities, prompts, transcripts,
agent-provider configuration, repository state, or ambient authoring-workspace
material. Contributor tooling and consumer distributions MUST remain separate,
and build-time tools MUST NOT become accidental runtime or transitive package
dependencies. Secrets and mutable external truth MUST remain explicit runtime
inputs owned by their proper systems.

### XIII. Minimal, Honest, Vertical Delivery

Program Kit MUST introduce the smallest boundary that proves a real consumer
need through an end-to-end vertical slice. New projects, packages, abstractions,
registries, adapters, providers, services, and extension mechanisms require a
specific ownership or independent-consumption reason and negative-path proof.
Documentation MUST distinguish implemented behavior, accepted design, proposal,
illustration, limitation, and future horizon. Development evidence MUST NOT be
presented as universal correctness or production qualification. Complexity that
does not strengthen semantic clarity, reuse, determinism, integrity, diagnostics,
or change safety MUST be rejected.

## Product Boundary and Core Terms

Program Kit is a human-led semantic software-construction toolchain for complex,
modular systems. It translates exact consumer-defined feature and component
semantics into validated and reproducible technology artifacts. Those artifacts
may include projects, packages, source, configuration, host composition,
documentation, schemas, diagnostic catalogs, analyzers, build gates, dependency
maps, compatibility evidence, and migration material.

The following distinctions are constitutional:

- A **feature** is the smallest governed unit of semantic capability and reuse.
- A **component** is an independently identifiable implementation, packaging, or
  composition boundary that realizes or combines declared features.
- A **semantic layer** is the consumer-owned, typed definition of feature
  meaning, relationships, invariants, and policies.
- A **bounded implementation context** is the exact change boundary within which
  approved semantic intent may be implemented and verified.
- A **projection** is a deterministic technology-specific representation of
  accepted semantic input; it does not become a second semantic source of truth.
- An **extension** is an explicitly selected implementation of a versioned seam;
  its availability never implies selection or authority.
- A **diagnostic** is a stable, typed explanation and correction contract, not a
  log message or incidental exception string.

Program Kit's initial implementation MAY be ecosystem-specific. Technology
support MUST be represented as explicit projections and profiles, and MUST NOT
be confused with consumer semantics or advertised as ecosystem-neutral without
evidence. Historical Program Kit code, packages, schemas, and feature
abstractions are prior art, not constitutional source truth; each reused concept
MUST be re-specified and accepted under this constitution.

## Development Workflow and Quality Gates

Every feature specification and plan MUST identify:

1. the human-owned intent, non-goals, semantic owner, and unresolved questions;
2. feature identities, contracts, components, artifacts, and extension seams;
3. dependency direction, known impact closure, compatibility, and migration;
4. canonical inputs, selected profiles, deterministic outputs, and limitations;
5. bounded work units with allowed edits, required proof, and stop conditions;
6. diagnostic identities, failure dispositions, and safe correction paths;
7. the static, dynamic, integration, security, and consumer evidence required;
8. explicit claims that remain human judgment or external-system responsibility.

Implementation MUST proceed in dependency-ordered vertical slices that leave a
usable, testable behavior or contract boundary. A slice MUST NOT be declared
complete from compilation alone. Its selected quality profile MUST include, as
applicable:

- schema, semantic, identity, and compatibility validation;
- compiler, Roslyn, MSBuild, architecture, and forbidden-reference gates;
- diagnostic-catalog, corrective-guidance, ordering, and redaction conformance;
- positive, negative, adversarial, malformed-input, and boundary fixtures;
- deterministic-output, permutation, repeatability, and clean-environment proof;
- package-only or otherwise isolated consumer proof;
- extension-selection, collision, ordering, and failure proof;
- dependency-impact, migration, rollback/correction, and closure evidence;
- authority, privacy, secret-safety, partial-effect, and recovery boundaries;
- exact evidence freshness and traceability to the approved scope.

If implementation exposes a material ambiguity, ownership conflict, hidden
dependency, unverifiable determinism claim, migration expansion, gate defect,
unsafe external effect, or diagnostic that cannot guide safe correction, the
affected work MUST stop. The plan MUST be revised and re-approved rather than
allowing implementation momentum to redefine intent.

## Governance

This constitution governs Program Kit product, architecture, specifications,
plans, code, generated artifacts, extensions, documentation, diagnostics, and
contributor workflows. Before ratification it is a review proposal only.

Ratification and amendment require an explicit human decision over the exact
constitution bytes. Each amendment MUST include a rationale, affected
principles, compatibility and migration impact, enforcement changes, and a
semantic version update:

- **MAJOR** for removal or incompatible redefinition of a principle or authority
  boundary;
- **MINOR** for a new principle or materially expanded obligation;
- **PATCH** for a non-semantic clarification that changes no obligation.

Every specification, plan, and pull request MUST include a constitution check.
Exceptions MUST be named, narrowly bounded, time- or version-limited where
possible, evidenced, and explicitly approved; an undocumented exception is a
violation. When instructions conflict, the narrower interpretation that
preserves human authority, consumer-owned meaning, exact contracts, fail-closed
evidence, actionable diagnostics, and runtime isolation takes precedence. If the
conflict remains material, work MUST stop for human resolution.

**Version**: 0.1.0 | **Ratified**: TODO(RATIFICATION_DATE): pending explicit human ratification | **Last Amended**: 2026-07-31

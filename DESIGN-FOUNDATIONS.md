---
artifact-kind: program-kit-design-foundations
status: active
last-updated: 2026-07-31
parent-ledger: DESIGN.md
---

# Program Kit Design Foundations


The following sources inform discovery but have different authority:

| Source | Role | Authority boundary |
|---|---|---|
| Human statements in the Program Kit rebuild conversation | Primary product intent | Authoritative when recorded and subsequently confirmed as a decision. |
| Attached recovered product story, `pasted-text.txt` | Historical problem narrative | Inspiration and evidence of recurring problems; not a specification. |
| `C:\Users\tech_\Code\semanticdomainengine-design-intake` | Advanced future-design stress test | Explicitly non-authoritative for Program Kit and not permission to import its business-domain semantics. |
| Archived Program Kit commit `0cc3950bb75f5704f7b0c58784ba691f942c8a81` | Prior implementation and prior art | Not source truth for the redesign. Preserved on branch and tag `archive/pre-rebuild-2026-07-31`. |
| `.specify/memory/constitution.md` | Initial constitutional synthesis | Proposal only until discovery and ratification converge. |

## 4. Recorded founding intent

These statements faithfully summarize the product intent supplied before this
ledger was created. They are inputs to discovery, not yet a complete accepted
design.

- Program Kit is intended as a real developer tool for architects and software
  developers building and maintaining large, complex, modular software systems.
- Its motivating problem is not merely code generation. Code has become cheap;
  confidence in the semantic correctness, compatibility, impact, and safe
  evolution of generated or changed systems has not.
- Every logical capability is conceived as a feature and therefore as an
  interface, internal, external, or both depending on the feature. The exact
  meaning of "feature" and "interface" still needs convergence.
- A semantic layer should wrap and position features or components
  deterministically, identify their artifacts and relations, and make their
  meaning understandable to other Program Kit-aware tools and AI sessions.
- Domain knowledge is defined by consumers. Consumer-defined logic belongs
  within a bounded implementation context; Program Kit must provide reusable,
  domain-neutral mechanics rather than invent consumer-domain meaning.
- Canonical semantic input should produce deterministic contracts, projects,
  hosts, analyzers, gates, document structures, and other governed artifacts.
- Extensions should hook into explicit deterministic seams. The same canonical
  input and pinned inputs should yield the same result. OpenID Connect provider
  adapters such as Keycloak and Auth0 are an illustrative future example, not
  yet a selected first implementation.
- Dependency maps, impact calculation, drift detection, integrity checks, and
  migration planning/execution are central because changes in large systems
  otherwise create unexpected repercussions.
- Governance must detect contradictions and drift at the earliest reliable
  point, including through compiler, Roslyn, MSBuild, schema, architectural, or
  other static gates where appropriate.
- Program Kit must always return meaningful feedback to an AI session using it.
  A stable diagnostics catalog and corrective guidance are core product
  behavior, not incidental error handling.
- The previous implementation contained valuable problem discovery but was
  shaky, overly restrictive in places, and sometimes masked the actual intent.
  It is prior art, not the redesign's source truth.
- Program Kit previously used itself and thereby created a circular dependency.
  The redesign starts from Spec Kit and must not casually restore self-hosting.
- The archived Program Kit also attempted discovery, specification, planning, or
  convergence work that may properly belong to Spec Kit. The redesign must not
  preserve those responsibilities merely because the old implementation had
  them. Program Kit's identity must state clearly what it is and what it is not.
- A possible future integration is for Program Kit to export explicitly defined
  capabilities that use selected Spec Kit techniques within a governed flow and
  combine them with Program Kit CLI extensions or other Program Kit mechanics.
  This is an exploration candidate, not an accepted responsibility or design.
- AI-assisted applications commonly keep their development instructions and
  foundational guidance inside each application. This creates duplicated prompt
  and instruction clutter, inconsistent development methods, and a steep
  contribution cost when developers move between applications.
- Program Kit is intended to provide a model-neutral and domain-neutral common
  development protocol so human developers and AI sessions can recognize how a
  Program Kit-built application is designed, changed, validated, diagnosed, and
  integrated without every repository reinventing that foundation.
- The desired ecosystem effect resembles package management at a broader
  feature level: complex products compose many applications, APIs, and
  technologies, while reusable target adapters encode integration knowledge
  once. A future WordPress adapter that projects supported Program Kit features
  into governed plugins is an illustrative stress test, not a v1 commitment.
- Program Kit's AI-provider-neutral workflow is a development-time concern.
  Generated products are ordinary software and need no AI agent, MCP surface, or
  Program Kit runtime unless explicitly selected.
- Target composition mechanics are capability-owned: CShells and DI
  participation for .NET are one mechanism; module loading or other native
  patterns apply to other targets.
- Canonical platform contracts are intended to normalize recurring technical
  concerns across implementations. Entra ID, Keycloak, and other providers
  should map to a versioned OpenID Connect contract so compatible UIs, APIs,
  middleware, and token flows share governed meaning.
- APIs, middleware, OpenTelemetry, secrets, and configuration are additional
  platform-contract candidates. Their exact contract families, ownership,
  conformance profiles, and guarantee envelopes remain unresolved.
- Provider capabilities may expose provider-native consumer intake contracts so
  users can express intent through familiar concepts. Required input is collected
  and validated before a traceable mapping into the canonical platform contract.
  Provider-first and canonical-first intent paths, lossless normalization,
  provider-specific extension facets, and migration behavior still need
  convergence.
- The preferred product expression is "AI builds it. Human intent governs it."
  Its supporting promise is that every admitted implementation is legible through
  human-approved semantic contracts, traceability, and verifiable evidence.
  "Admitted" is essential: the semantic layer does not claim complete knowledge
  of arbitrary, undeclared, unverified, inferred-only, stale, or drifted code.

## 5. Accepted foundations and provisional synthesis

Items 1 through 3 and 6 through 15 are accepted decisions governed by the
decision register in `DESIGN.md`. Items 4 and 5 remain provisional until their
respective categories converge.

1. Program Kit is a human-led, AI-assisted modular software-development tool
   that translates human intent into bounded, contract-evaluated software.
   Construction becomes deterministic after the required intent is accepted and
   all construction inputs are complete and pinned.
2. Its non-negotiable promise is governed integration resolution between
   Program Kit-built products: direct compatibility, an explicit adapter or
   migration, or a precise contract-backed incompatibility result.
3. Program Kit uses a thin target-specific feature model. A feature is an
   implemented unit distinct from the portable software-definition bundle.
   CShells supplies selected .NET host-participation mechanics without becoming
   a universal runtime abstraction. Interface, contract, intake, and binding are
   distinct; feature and interface relations may be many-to-many. The kernel
   owns identity, provenance, mapping, evidence, unknown-state, diagnostic, and
   admission integrity. Consumers own architecture and may impose stricter
   composition and cardinality policies.
   Program Kit v1 begins with one exact `.NET 10 + CShells 0.0.28` construction
   profile with role-specific feature and host dependencies, explicit
   activation, conformance evidence, structured diagnostics, and explicit
   migration. Features may expose multiple capability-owned interfaces.
   Components carry governed composition and delivery identity independently
   from their concrete package, project, assembly, container, or other artifacts.
4. Deterministic mechanisms should be executable code; consumer-owned semantics
   should be explicit, typed, versioned, and canonical.
5. Extension discovery and selection should be explicit and pinned rather than
   ambient, order-dependent, or based on an implicit "best match."
6. Unknown, incomplete, incompatible, and unavailable states should remain
   explicit. They should never be disguised as success or guessed into
   certainty.
7. Generated runtime outputs should remain independent of Program Kit's
   development-session capabilities.
8. Product capability ownership and development method are separate boundaries.
   Program Kit owns a cohesive consumer-facing design, planning, implementation,
   public artifact, diagnostics, and compatibility surface. It may internally
   reuse or extend pinned Spec Kit techniques while Program Kit's own repository
   uses Spec Kit directly and remains non-self-hosted. An optional external
   Spec Kit bridge may use only Program Kit's public contracts. Exact integration
   packaging remains an Extensions decision.
9. Applications retain a thin declarative source of truth for human intent,
   domain semantics, selections, profiles, policies, approvals, exceptions,
   migrations, and effective-capability provenance. Reusable mechanics and
   generic AI guidance remain in versioned Program Kit capabilities. Local
   guidance is governed and cannot override kernel invariants.
10. The portable unit is a versioned software-definition bundle with a canonical
    root manifest and separately governed linked design, implementation,
    deployment, and evidence artifacts. Source code is governed but is not the
    canonical portable semantic unit.
11. Capabilities expose explicit, versioned, support-bounded public contracts.
    Canonical-first and provider-first intake are both supported; provider-first
    selection binds until explicit migration. Every normalization is traceable
    and fails closed rather than silently losing meaning.
12. Program Kit core owns contract-system mechanics. Separately versioned
    packages own platform semantics. Program Kit ships a small first-party
    platform-contract catalog and permits governed third-party families.
    Canonical scope always names a contract family, version, and profile.
13. Complete, accepted, pinned inputs deterministically construct software and
    produce evidence-backed contract-conformant integration inside declared
    support profiles. Runtime availability, deterministic business behavior, and
    external systems are outside that guarantee.
14. An implementation is admitted only when its governance-relevant meaning is
    human-approved, traceable to artifacts, and supported by applicable
    evidence. Unknown, undeclared, inferred-only, unverified, stale, or drifted
    behavior may not be presented as understood.
15. Program Kit is AI-provider-neutral and produces ordinary software with no
    required AI or Program Kit runtime unless selected. Its accepted expression
    is **AI builds it. Human intent governs it.** Every admitted implementation
    is legible through human-approved semantic contracts, traceability, and
    verifiable evidence.

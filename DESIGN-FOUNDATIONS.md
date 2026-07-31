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

## 5. Provisional synthesis to test

The following is the current agent synthesis. Every statement remains
non-authoritative until resolved through identified questions and accepted as a
decision:

1. Program Kit may be best understood as a human-led semantic construction and
   evolution toolchain, with an SDK as one delivery surface rather than its
   governing identity.
2. Its differentiating promise may be trustworthy change: explicit semantics,
   deterministic construction, intelligible dependency impact, safe migration,
   and exact diagnostics for humans and agents.
3. A feature may need to mean a governed semantic contract that can project to
   several technical interfaces, rather than only a literal CLR interface.
4. Deterministic mechanisms should be executable code; consumer-owned semantics
   should be explicit, typed, versioned, and canonical.
5. Extension discovery and selection should be explicit and pinned rather than
   ambient, order-dependent, or based on an implicit "best match."
6. Unknown, incomplete, incompatible, and unavailable states should remain
   explicit. They should never be disguised as success or guessed into
   certainty.
7. Generated runtime outputs should remain independent of Program Kit's
   development-session capabilities.
8. Spec Kit likely owns feature discovery and specification workflow, while
   Program Kit must own a different concern: compiling and governing accepted
   semantic system definitions and their technical realization. The exact seam
   is unresolved and must be defined before the constitution is ratified.

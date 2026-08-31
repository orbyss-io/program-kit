---
description: Create or update the living architecture baseline and ADR system.
scripts:
  py: scripts/governance_state.py validate
---

## Input

`$ARGUMENTS` identifies the initial design and bootstrap assessment.

## Constitutional authority

Before reading or writing architecture, run:

```text
{SCRIPT}
```

Read the ratified `.specify/memory/constitution.md` in full. The constitution governs architecture,
ADRs, specifications, plans, tasks, implementation, and verification. Stop if the ratification
record is missing, Draft, invalid, or stale, or if the constitution contains a placeholder or TODO.

## Architecture bootstrap

Preserve existing accepted decisions and user content. Create missing artifacts under `docs/architecture/`:

- `README.md`: navigation, ownership, update rules, and status vocabulary.
- `architecture.md`: goals, constraints, context, building blocks, runtime views, deployment, cross-cutting concepts, risks, and quality scenarios.
- `quality-attributes.md`: measurable scenarios and verification methods.
- `technology-radar.md`: proposed, accepted, deprecated, and rejected technologies with ADR links.
- `traceability.md`: design -> decision -> specification -> plan -> implementation -> verification.
- `specification-roadmap.md`: created later by the roadmap command after tooling; architecture establishes the candidate slice and decision evidence it consumes.
- `decisions/README.md` and an ADR template.

Use C4/Structurizr DSL and arc42-style sections when they fit the repository, but record their adoption as Proposed until accepted. Diagrams are views of the architecture model, not the source of truth by themselves.

The architecture baseline must also define:

- the bounded-context map and ubiquitous language boundaries;
- module and feature ownership, public contracts, data ownership, and allowed dependency graph;
- a candidate slice catalog using the contract in `references/vertical-slicing.md`;
- the distinction between compile-time modules, runtime features, shells, and endpoints;
- shared-kernel and feature-family extension policies, including exact Accepted exceptions;
- how the first specification delivers an observable vertical slice rather than technical layers.

## Decision policy

ADR states are `Proposed`, `Accepted`, `Rejected`, `Deprecated`, and `Superseded`. Only a human may move a project-specific ADR to `Accepted`. Every accepted technology, cross-domain dependency, public contract, data ownership rule, consistency boundary, security boundary, and material exception must cite an Accepted ADR.

Every accepted cross-module implementation reference, feature-family inheritance edge, shared store,
or runtime feature dependency must also cite an Accepted ADR and an executable or reviewable
enforcement location.

Resolve the decision backlog through focused design tasks before implementation depends on those answers. A design task produces evidence, alternatives, consequences, a proposed ADR, updated views, and follow-on specification slices. It does not implement application behavior.

Architecture documents must clearly distinguish facts found in the initial design, derived constraints, proposals, accepted decisions, and unresolved questions.

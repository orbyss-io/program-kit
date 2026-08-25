---
description: Create or update the living architecture baseline and ADR system.
---

## Input

`$ARGUMENTS` identifies the initial design and bootstrap assessment.

## Architecture bootstrap

Preserve existing accepted decisions and user content. Create missing artifacts under `docs/architecture/`:

- `README.md`: navigation, ownership, update rules, and status vocabulary.
- `architecture.md`: goals, constraints, context, building blocks, runtime views, deployment, cross-cutting concepts, risks, and quality scenarios.
- `quality-attributes.md`: measurable scenarios and verification methods.
- `technology-radar.md`: proposed, accepted, deprecated, and rejected technologies with ADR links.
- `traceability.md`: design -> decision -> specification -> plan -> implementation -> verification.
- `decisions/README.md` and an ADR template.

Use C4/Structurizr DSL and arc42-style sections when they fit the repository, but record their adoption as Proposed until accepted. Diagrams are views of the architecture model, not the source of truth by themselves.

## Decision policy

ADR states are `Proposed`, `Accepted`, `Rejected`, `Deprecated`, and `Superseded`. Only a human may move a project-specific ADR to `Accepted`. Every accepted technology, cross-domain dependency, public contract, data ownership rule, consistency boundary, security boundary, and material exception must cite an Accepted ADR.

Resolve the decision backlog through focused design tasks before implementation depends on those answers. A design task produces evidence, alternatives, consequences, a proposed ADR, updated views, and follow-on specification slices. It does not implement application behavior.

Architecture documents must clearly distinguish facts found in the initial design, derived constraints, proposals, accepted decisions, and unresolved questions.


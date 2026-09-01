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

Also validate and read `.specify/governance/bootstrap-assessment-approval.json` and
`docs/architecture/bootstrap-decisions.json`. The hash-bound assessment gate is the human authority
for explicit intake choices, Program Kit defaults, derived defaults, disclosed acknowledgements,
and recorded overrides. Do not reopen those choices as Proposed.

## Architecture bootstrap

Preserve existing accepted decisions and user content. Honor the configured ADR and roadmap paths;
create the remaining missing artifacts under `docs/architecture/`:

- `README.md`: navigation, ownership, update rules, and status vocabulary.
- `architecture.md`: goals, constraints, context, building blocks, runtime views, deployment, cross-cutting concepts, risks, and quality scenarios.
- `quality-attributes.md`: measurable scenarios and verification methods.
- `technology-radar.md`: proposed, accepted, deprecated, and rejected technologies with ADR links.
- `traceability.md`: design -> decision -> specification -> plan -> implementation -> verification.
- `specification-roadmap.md`: created later by the roadmap command after tooling; architecture establishes
  slice identity and decision evidence, but never owns or copies roadmap-entry lifecycle status.
- `decisions/README.md` and an ADR template.

Create `decisions/bootstrap-baseline.md` as a consolidated Accepted decision recording the exact
approved decision-register hash, default-profile version, explicit choices, applied defaults,
overrides, material acknowledgements, and easy supersession path. Copy the decision-register
SHA-256 from `.specify/governance/bootstrap-assessment-approval.json`; include the stable ID of every
choice, override, and acknowledgement so validation can prove traceability. Ordinary reviewed
defaults do not need one ADR each. Project-specific choices outside that baseline remain Proposed
until their own human approval.

Do not rewrite `bootstrap-assessment.md`, `decision-backlog.md`, `tooling-evaluation.md`, or
`bootstrap-decisions.json` after their approval. If one is wrong, stop and direct the user back to
the assessment review so the artifacts can be corrected, the packet regenerated, and the exact
contents approved again.

Use C4/Structurizr DSL and arc42-style sections when they fit the repository, but record their adoption as Proposed until accepted. Diagrams are views of the architecture model, not the source of truth by themselves.

The architecture baseline must also define:

- the bounded-context map and ubiquitous language boundaries;
- module and feature ownership, public contracts, data ownership, and allowed dependency graph;
- a candidate slice catalog using the contract in `references/vertical-slicing.md`;
- the distinction between compile-time modules, runtime features, shells, and endpoints;
- shared-kernel and feature-family extension policies, including exact Accepted exceptions;
- how the first specification delivers an observable vertical slice rather than technical layers.

`docs/architecture/specification-roadmap.md` is the sole authority for `Candidate`, `Blocked`,
`Ready`, `Active`, `Delivered`, and `Superseded` roadmap-entry status. Before roadmap generation,
architecture and traceability may describe provisional slice identity, scope, dependencies, and
decision evidence, but must not assign a roadmap status or claim that a future roadmap record is an
authoritative current state. The deterministic post-roadmap synchronization step owns the marked
derived navigation view in both files.

## Decision policy

ADR states are `Proposed`, `Accepted`, `Rejected`, `Deprecated`, and `Superseded`. Only a human may move a project-specific ADR to `Accepted`. Every accepted technology, cross-domain dependency, public contract, data ownership rule, consistency boundary, security boundary, and material exception must cite an Accepted ADR.

Every accepted cross-module implementation reference, feature-family inheritance edge, shared store,
or runtime feature dependency must also cite an Accepted ADR and an executable or reviewable
enforcement location.

Resolve the decision backlog through focused design tasks before implementation depends on those answers. A design task produces evidence, alternatives, consequences, a proposed ADR, updated views, and follow-on specification slices. It does not implement application behavior.

Architecture documents must clearly distinguish facts found in the initial design, derived constraints, proposals, accepted decisions, and unresolved questions.

When .NET is selected without the recorded opt-out, the architecture, technology radar, and
bootstrap-baseline decision must adopt `ProgramKit.Host` and the application-bundle model as
Accepted. Do not scaffold or restore packages during this command.

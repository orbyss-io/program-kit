# ADR-0004: Ratify governance before architecture and feature specifications

- Status: Accepted
- Date: 2026-08-25
- Decision owners: User and Codex

## Context

A generated constitution file does not prove human ratification, and a feature specification cannot
govern the process that creates feature specifications without bootstrap recursion. The bootstrap
also lacked an explicit project-level portfolio connecting architecture decisions to sequenced
feature specifications.

## Decision

Treat the project constitution as the highest governance artifact, separate from feature
specifications. Draft it with Spec Kit's core constitution command only after intake, current
research, and the assessment gate. Revoke stale authority before drafting. A dedicated human gate
and deterministic validation then write a Ratified marker bound to the constitution version,
governance dates, and SHA-256.

Architecture and tooling run only after ratification. They feed a required
`docs/architecture/specification-roadmap.md`, which is a governed portfolio rather than application
work. Only roadmap entries whose required ADRs are Accepted and whose boundaries contain no hidden
architecture choices may become Ready. `speckit.specify` is blocked until at least one entry is
Ready.

Design tasks remain outside the feature implement lifecycle. They create evidence, Proposed ADRs,
updated architecture views, and roadmap transitions.

## Consequences

Any constitution amendment invalidates its prior hash and requires another human ratification.
Rejected or abandoned drafts cannot unlock architecture or specifications. Bootstrap gains a
constitution gate, ratification finalization, roadmap generation, and a pre-specification hook.

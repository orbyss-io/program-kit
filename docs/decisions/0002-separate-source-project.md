# ADR-0002: Maintain Program Kit Bootstrap in a separate source project

- Status: Accepted
- Date: 2026-08-25
- Decision owners: User and Codex

## Context

The bootstrap is reusable across repositories and has its own workflow, release, compatibility, and packaging lifecycle. Keeping its tests inside a consuming application would give that application an unrelated responsibility.

## Decision

Maintain the source at `C:\Code\Orbyss\_ProgramKitBootstrap`. Consuming projects install released components and the bundle; they do not own its source tests.

## Consequences

Changes can be versioned and tested independently. A consuming repository can pin a known bundle version. Cross-repository testing is performed as a release compatibility suite.


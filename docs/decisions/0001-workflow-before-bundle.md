# ADR-0001: Develop the workflow before packaging the bundle

- Status: Accepted
- Date: 2026-08-25
- Decision owners: User and Codex

## Context

A Spec Kit bundle composes and distributes extensions, presets, workflows, and steps. It does not provide runtime behavior. The bootstrap must be testable independently of packaging.

## Decision

The bootstrap workflow and governance extension are developed and validated first. The bundle manifest pins the tested versions afterward. Bundle installation, update, and removal are release tests, not the primary development loop.

## Consequences

The consuming application repository does not carry bundle development tests. Workflow defects can be isolated from catalog and packaging defects. Releasing requires both component tests and clean bundle lifecycle tests.


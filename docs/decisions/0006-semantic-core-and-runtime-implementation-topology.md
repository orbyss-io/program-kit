# ADR-0006: Use semantic Core and named runtime implementations

- Status: Accepted
- Date: 2026-09-03
- Decision owners: User and Codex

## Context

The original .NET profile combined conventional `Domain`, `Contracts`, `Application`,
`Infrastructure`, and `Feature.*` layer projects. A live consumer followed that guidance and produced
endpoint projects that referenced persistence providers so a runtime-composition validator could
find a composition path. The result conflicted with the intended external-host, modular DDD, and
runtime feature model.

## Decision

Use domain-specific `.Core` projects for stable semantics and extension points. Name activatable
implementations for the domain behavior, protocol, provider, consumer/provider bridge, helper, or
composition preset they contribute. Feature is a runtime identity and activation type, not a project
layer; project/package names do not contain `.Feature`.

Core declares cohesive semantic capabilities rather than repositories, stores, units of work, or
generic CRUD. A capability may contain multiple naturally related operations. Provider-specific
persistence models stay private; direct ORM mapping of a persistence-ignorant Core POCO remains
valid. Cross-context work defaults to consumer-owned bridges, events, or named orchestrators. Direct
Core-to-Core references require an accepted stable-language/subdomain/shared-kernel relationship and
an exact architecture-test allowlist.

The external host activates independent API, implementation, provider, bridge, and composition
features. Endpoint projects never reference persistence providers merely to compose them. The
selected Program Kit web runtime owns generic authentication and HTTP infrastructure; `.Api`
projects own their actual endpoints, wire contracts, mappings, permission identities, and policy
metadata.

## Consequences

Planning and validation use the roles `core`, `helper`, `implementation`, `provider`, `bridge`,
`composition`, and `test`. Existing consumer manifests using legacy roles and fields require an
explicit architecture remediation. Generated project graphs communicate domain language and runtime
selection directly, at the cost of rejecting familiar but ambiguous horizontal-layer templates.

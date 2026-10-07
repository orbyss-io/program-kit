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
persistence models stay private and are separate provider-owned entity types; Core models are never
directly mapped as ORM entities. Cross-context work defaults to consumer-owned bridges, events, or named orchestrators. Direct
Core-to-Core references require an accepted stable-language/subdomain/shared-kernel relationship and
an exact architecture-test allowlist.

The external host activates independent API, implementation, provider, bridge, and composition
features. Endpoint projects never reference persistence providers merely to compose them. The
selected Program Kit web runtime owns generic authentication and HTTP infrastructure; `.Api`
projects own their actual endpoints, wire contracts, mappings, permission identities, and policy
metadata.

## Clarification adopted 2026-10-06

Core, runtime implementation, API adaptation and persistence use separate compilation projects when
present. One bounded context, package release, feature bundle or deployment cannot waive those
boundaries. Composition selects behavior rather than owning the implementations it selects. Runtime
capability bindings require a Core owner and a distinct implementation/provider/bridge project;
composition is not an implementation role. Namespace waivers and role relabeling are rejected.

The ordinary `eng/architecture.json` graph is validated after-plan/after-tasks and before affected
implementation, without builds or another approval dossier. Compiled metadata checks omitted owned
capability bindings and provider leaks. Actual activation, registration, resolution and lifetime tests
remain necessary. Review BCL-only serializers and provider configuration against source ownership;
structural checks cannot prove every semantic responsibility. Empty greenfield graphs and pure Core
utilities remain legitimate. Upgrades diagnose incompatible retained graphs and preserve their ADRs
and configuration for explicit remediation.

## Consequences

Planning and validation use the roles `core`, `helper`, `implementation`, `provider`, `bridge`,
`composition`, and `test`. Existing consumer manifests using legacy roles and fields require an
explicit architecture remediation. Generated project graphs communicate domain language and runtime
selection directly, at the cost of rejecting familiar but ambiguous horizontal-layer templates.

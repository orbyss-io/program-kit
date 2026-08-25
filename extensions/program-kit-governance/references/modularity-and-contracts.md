# Modularity, DDD, and contracts

## Vocabulary

- **Bounded context**: a business-language and model-ownership boundary.
- **Module**: a compile-time ownership and dependency boundary implementing a bounded context or a
  cohesive part of one.
- **Feature**: a runtime-composable capability exposed to a host.
- **Vertical slice**: one actor, trigger, or intent carried to an observable outcome through a module.
- **Shell**: a runtime isolation and configuration context, such as a tenant, plan, environment, or
  plugin configuration.
- **Endpoint**: a transport adapter exposing one slice through a public protocol contract.

These concepts are related but not interchangeable. A shell is not a bounded context, a feature is
not necessarily one endpoint, and a module can contain multiple slices.

## Proportional domain-driven design

Use strategic DDD to discover bounded contexts, ownership, relationships, and ubiquitous language.
Use aggregates, entities, value objects, domain services, and repositories only where business
complexity and invariants justify them. Simple transformations and CRUD behavior may remain
transaction scripts inside a well-owned slice.

Domain behavior is independent of transport, persistence, serialization, dependency injection, and
vendor frameworks. Aggregates protect invariants and transaction boundaries. Domain entities are
never used directly as public transport or persistence contracts.

## Dependency and ownership rules

- Modules do not reference peer module implementations.
- Features do not reference peer feature implementations.
- Cross-boundary collaboration uses published contracts, consumer-owned ports, events, or explicitly
  owned query APIs.
- A module does not access another module's store, schema, ORM context, or internal model.
- A shared database transaction, direct implementation reference, or cross-domain orchestration path
  requires an Accepted ADR.
- Cross-domain process managers consume published contracts or events and own their lifecycle.
- The host is the composition root. Business behavior does not resolve dependencies through a
  container or service locator.

## Contract placement

Place contracts at the boundary whose stability they protect:

- a consumer-owned port lives with the policy that needs it;
- a provider's published capability lives in a small contracts package owned by that provider;
- public API, event, and schema contracts are versioned independently from domain entities;
- framework registration interfaces live in a dedicated abstractions package;
- a shared kernel contains only deliberately shared domain semantics with joint ownership.

Do not create a generic `Core`, `Common`, or `Shared` project as a default dependency sink. Every
shared abstraction names its semantics, owner, consumers, compatibility policy, and verification.
Prefer an interface only when it protects a real boundary or supports credible implementations.

## Feature-reference policy

Implementing a shared interface is not a feature-to-feature reference: both implementations depend
on the neutral contract. Concrete inheritance is not an automatic exception. It increases coupling
to implementation and lifecycle and must not be used merely for code reuse.

A feature-family extension may depend on an explicitly designed abstraction or base only when:

1. both projects belong to the same bounded context, owner, and release lifecycle;
2. the relationship represents genuine substitutability or a documented extension protocol;
3. the base was designed, documented, and tested for extension;
4. composition or delegation cannot satisfy the requirement as clearly;
5. the edge grants no access to another module's internal state or persistence; and
6. an Accepted ADR and an architecture-test allowlist record the exact dependency.

A direct dependency on another concrete feature, including typed dependency metadata, remains an
error without that exception. If the exception is routine, model the projects as internal parts of
one feature family rather than independent peer features.

## Runtime dependencies

Runtime activation or ordering metadata does not grant compile-time access to another feature.
Business features normally collaborate through contracts after composition. Dependencies on named
platform capabilities may be declared when their activation order is material, but the dependency,
failure behavior, optionality, and compatibility policy must be explicit.

## Enforcement evidence

Record a context map, module catalog, feature catalog, slice catalog, contract-ownership table, and
allowed dependency graph. Enforce machine-verifiable edges in CI using build-graph, assembly, or
architecture tests. Test contract implementations, composition, forbidden references, cycles,
public compatibility, and data-ownership rules in proportion to risk.

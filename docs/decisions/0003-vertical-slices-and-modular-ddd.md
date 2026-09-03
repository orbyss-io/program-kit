# ADR-0003: Use vertical slices within explicit modular and domain boundaries

- Status: Accepted
- Date: 2026-08-25
- Decision owners: User and Codex

## Context

Program Kit mentioned behavior slices but did not define their completeness, ownership, dependency,
or verification rules. Technical-layer plans and peer feature references could therefore pass the
governance hooks without delivering an end-to-end outcome.

## Decision

Use vertical slices as the default delivery decomposition. Each meaningful slice follows an actor,
trigger, or intent to an observable verified outcome. Strategic DDD defines bounded contexts and
language ownership proportionally; semantic Core packages own stable language and capabilities;
runtime features activate named implementations without direct peer implementation references.

ADR-0006 supersedes the earlier technology-profile interpretation that permitted generic
`Domain`/`Contracts`/`Application`/`Infrastructure`/`Feature.*` project layers. It preserves this
decision's vertical-slice and dependency principles while making the package model explicit.

Concrete inheritance is not an automatic feature-reference exception. A genuine feature-family
extension requires shared ownership and release lifecycle, an explicitly designed extension
contract, substitutability or extension evidence, an Accepted ADR, and an architecture-test
allowlist.

Technology profiles implement these generic rules without making a folder layout, CQRS, mediator,
or framework universally mandatory.

## Consequences

Specifications and plans are outcome-oriented, while horizontal enabling work must identify the
slices it unlocks. Consuming repositories need context, module, feature, slice, contract, data, and
dependency evidence. Architecture tests enforce machine-verifiable boundaries.

# Program Kit bootstrap review

This directory contains the human-authored bootstrap exception for the Program
Kit. The Kit cannot have generated its own initial design because its contracts
and tools do not exist yet.

The review set is stored as UTF-8/LF text by repository attributes so its raw
SHA-256 bindings remain stable across checkouts. It contains:

- [architecture-design.md](architecture-design.md) — proposed architecture,
  ownership map, dependency graph, contract shapes, and boundaries;
- [implementation-plan.md](implementation-plan.md) — proposed, traceable work
  plan and verification obligations;
- `review-manifest.json` — exact SHA-256 bindings for the two review artifacts.

## Gate state

`awaiting-human-approval`

No Program Kit source project, schema, generated artifact, fixture, capability,
or provider wrapper may be implemented from this review set until the human
explicitly approves the exact design and plan digests in the review manifest.
Reviewability is not approval.

After approval, the decision will first be captured as a bootstrap approval
record bound to those digests. Once the normal Program Kit contracts and tools
work, that record will be represented through the implemented approval contract
without rewriting the bootstrap history.

## Current implementation-claim truth

This table uses the architecture claim states, not capability registration
status. Current capability availability is owned only by
[`.agents/capabilities/INDEX.md`](../../.agents/capabilities/INDEX.md).

| Claim | Implementation claim state |
| --- | --- |
| Bootstrap architecture and plan are available for review | `scaffolded` |
| Universal contracts, deterministic tooling, .NET kit, CLI, fixture, tests, and packages | `aspirational` |
| `develop-software`, `design-software`, and `implement-software-plan` | `deferred` pending their backing contracts and tools |
| Release Cycle capabilities and behavior | `deferred` outside Program Kit scope |
| Domain Semantic Engine domains and features | `deferred`; `core/` and `features/` remain README-only |

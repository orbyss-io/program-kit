# Program Kit bootstrap review

This directory contains the human-authored bootstrap exception for the Program
Kit. The Kit cannot have generated its own initial design because its contracts
and tools do not exist yet.

The two review artifacts are stored as UTF-8/LF text by repository attributes
so their raw SHA-256 bindings remain stable across checkouts. This directory
contains:

- [architecture-design.md](architecture-design.md) — proposed architecture,
  ownership map, dependency graph, contract shapes, and boundaries;
- [implementation-plan.md](implementation-plan.md) — proposed, traceable work
  plan and verification obligations;
- `review-manifest.json` — exact SHA-256 bindings for the two review artifacts
  and the current gate-state projection; and
- `bootstrap-approval-record.json` — immutable human approval bound to the exact
  review-set version and artifact digests.

## Gate state

`approved`

The human approved review set `0.3.0` unconditionally on 2026-07-23. The
authority is `bootstrap-approval-record.json`, which binds the exact design and
plan SHA-256 values and preserves the accepted and excluded scope. This README
is navigation and a status projection; it is not approval authority.

The architecture and plan bytes remain unchanged, including their embedded
pre-decision `awaiting-human-approval` state. Rewriting either frozen artifact
would create new, unapproved bytes. Implementation may now proceed only within
the exact approved boundary; a material deviation requires a new review set and
human approval.

Once the normal Program Kit contracts and tools work, the bootstrap record will
be represented through the implemented approval contract without rewriting the
bootstrap history.

## Current implementation-claim truth

This table uses the architecture claim states, not capability registration
status. Current capability availability is owned only by
[`.agents/capabilities/INDEX.md`](../../.agents/capabilities/INDEX.md).

| Claim | Implementation claim state |
| --- | --- |
| Bootstrap architecture and plan are approved for bounded implementation | `scaffolded` |
| Universal contracts, domainless modularity, model-first System.Text.Json-only serialization with deny-by-default DOM use, tasks/schedules, version topology and migration, deterministic tooling, direct CShells composition, .NET 10 API/Console/Worker generation, health composition, local package preparation/application publish, CLI, fixture, tests, and packages | `aspirational` |
| `develop-software`, `design-software`, and `implement-software-plan` | `implemented`; canonical definitions, thin Codex wrappers, index/catalog projection, and exact-byte distribution bundle are backed by W070 |
| Repository-local `publish-dotnet-application-locally` capability | `implemented` over the backed W065 operation and deliberately excluded from the three-capability distribution bundle |
| Public `Orbyss.ProgramKit.DotNet.Metadata` package and Program Kit attributes | `deferred` until repeated concrete generator use cases justify an owned public surface |
| Release Cycle capabilities and behavior | `deferred` outside Program Kit scope |
| Domain Semantic Engine domains and features | `deferred`; `core/` and `features/` remain README-only |

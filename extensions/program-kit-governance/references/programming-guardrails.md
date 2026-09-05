# Generic programming guardrails

These defaults apply unless a narrower rule is justified and documented:

- Prefer simple, cohesive designs that satisfy SOLID principles and make invalid states difficult to represent.
- Keep domain intent independent of UI, transport, persistence, serialization, and vendor SDK concerns.
- Make public contracts, dependencies, side effects, errors, timeouts, cancellation, concurrency, and ownership explicit.
- Validate at trust boundaries; preserve typed information inside them.
- Use deterministic, hermetic tests where possible. Test behavior, contracts, architecture rules, failure modes, and migrations in proportion to risk.
- Treat warnings as build failures in CI after a deliberate baseline. Do not suppress diagnostics without a reason and scope.
- Use structured logs without secrets, stable correlation identities, meaningful metrics, and trace propagation across asynchronous boundaries.
- Pin tool and dependency versions according to ecosystem practice; automate update discovery but require verification before promotion.
- Generate SBOM/provenance and perform dependency, secret, static security, and license checks when artifacts are distributed or deployed.
- Do not use invisible fire-and-forget work. Durable asynchronous work has identity, ownership, observability, retry semantics, and a terminal state.
- Avoid framework-shaped domain models and generic repository/store/unit-of-work abstractions that
  erase domain language. Model the smallest cohesive semantic capability; group naturally related
  methods and split only at real consumer, consistency, security, lifecycle, or replacement boundaries.
- Organize meaningful changes as complete vertical slices and avoid technical-layer delivery phases.
- Keep peer runtime implementations independent; collaborate through Core-owned semantic
  capabilities, consumer-owned bridges, immutable events, or accepted published-language Core edges
  rather than implementation references or shared persistence.
- Treat in-process domain events as awaited and non-durable. Durable asynchronous delivery requires
  an explicitly accepted integration-event/outbox design; fire-and-forget is not a bridge.
- Treat concrete inheritance across feature boundaries as stronger coupling, not an automatic exception. Require an Accepted ADR and an architecture-test allowlist for a genuine feature-family extension.
- Keep dependency injection and service location at composition boundaries. Business behavior declares explicit constructor dependencies and does not resolve arbitrary services from a container.
- Reuse the selected authentication feature's canonical permission policy. Consumer features do not
  parse provider roles/token shapes or reparse canonical permission claims; add a resource-specific
  authorization handler only for a real resource, state, tenancy, or protected-effect decision.

Apply rules proportionally. Pure transformations and trivial adapters should remain small; they do not need ceremony that adds no invariant, policy, or lifecycle value.

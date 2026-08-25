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
- Avoid framework-shaped domain models and generic repository/unit-of-work abstractions that erase domain language.
- Organize meaningful changes as complete vertical slices and avoid technical-layer delivery phases.
- Keep peer modules and features independent; collaborate through owned contracts rather than implementation references or shared stores.
- Treat concrete inheritance across feature boundaries as stronger coupling, not an automatic exception. Require an Accepted ADR and an architecture-test allowlist for a genuine feature-family extension.
- Keep dependency injection and service location at composition boundaries. Business behavior declares explicit constructor dependencies and does not resolve arbitrary services from a container.

Apply rules proportionally. Pure transformations and trivial adapters should remain small; they do not need ceremony that adds no invariant, policy, or lifecycle value.

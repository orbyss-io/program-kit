# Program Kit host-tooling extension design intent

- Recorded: 2026-07-25
- State: human-started and scope-aligned; exact design and plan not yet approved
- Repository scope: `program-kit/`
- Design identity: `pkid:design:program-kit:host-tooling`
- Intended design version: `1.0.0`

## Human intent

The human requested a provider-neutral, deterministic Program Kit toolbox for
generated .NET hosts and explicitly aligned with the following direction:

1. converge Program Kit operation contracts before host projections multiply;
2. generate external API clients through a pinned Kiota adapter rather than a
   new general-purpose client generator;
3. generate ASP.NET Core authentication and authorization host profiles;
4. support distinct OIDC confidential interactive-client and OAuth resource-
   server JWT bearer profiles;
5. generate Aspire AppHost projects from explicit application composition
   input;
6. generate and validate Dev Container artifacts;
7. project the same owned operations through an optional FastEndpoints adapter;
8. prove Keycloak only as an optional Aspire-backed local-test provider;
9. defer comprehensive direct Docker Compose modeling, automatic container or
   Dev Container execution, production Keycloak provisioning, and consumer-
   domain identity or authorization semantics.

The human also explicitly aligned with adding typed configuration, Options,
validation, provider composition, and controlled reload generation before the
security, Aspire, Keycloak, and client-generation integrations that consume
those mechanics.

The requested configuration sequence is:

1. configuration-source composition contracts;
2. typed Options binding and startup validation;
3. reload capability declarations and snapshot/monitor selection;
4. built-in provider profiles and a custom-provider extension ABI;
5. optional Azure Key Vault and Azure App Configuration adapters;
6. fixtures for valid and invalid changes, provider outage, precedence, secret
   redaction, scoped consistency, and singleton monitoring.

The human's explicit alignment statements included:

> “yes we fully 100% agree and align!”

> “Let’s do this. We 100% align and agree!”

## Protocol understanding to preserve

Program Kit owns deterministic host mechanics and exact protocol-profile
selection. It does not own provider product behavior or consumer-domain
identity and authorization meaning.

- OAuth 2.0 is delegated authorization infrastructure, not an authentication
  protocol.
- OpenID Connect is an identity layer over OAuth 2.0.
- An interactive client validates an ID token for its client session.
- An API validates an access token; an ID token is not an API access token.
- Access tokens are not universally JWTs. The initial resource-server profile
  is deliberately limited to JWT access tokens; opaque-token introspection is a
  later optional profile.
- Middleware may construct an ASP.NET Core `ClaimsPrincipal`, but claims,
  groups, roles, scopes, and provider-specific names do not become consumer-
  domain Identity or Authorization conclusions.
- Keycloak, Entra ID, and other products are interchangeable only when they
  satisfy the exact selected standards profile, metadata, algorithms, issuer,
  audience, client registration, and claim-mapping requirements.

## Authority boundary

This record preserves current human intent for design. It does not approve the
forthcoming architecture design or implementation plan, does not authorize
runtime implementation, and does not authorize network, secret, deployment,
release, provider-provisioning, container-execution, or autonomous behavior.

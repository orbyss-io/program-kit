# Program Kit host-tooling extension design intent

- Recorded: 2026-07-25
- State: human-started and scope-aligned; exact design and plan not yet approved
- Repository scope: `program-kit/`
- Design identity: `pkid:design:program-kit:host-tooling`
- Intended design version: `1.2.0`

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
10. generate structured .NET logging, tracing, metrics, correlation, transport
    telemetry, exception observation, and controlled provider/exporter
    composition without owning application observability meaning or a
    telemetry backend.

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

The human subsequently and explicitly aligned with adding diagnostics and
observability as foundational host infrastructure before the security, client,
Aspire, and endpoint projections that consume it. The aligned boundary is:

- .NET libraries emit through `ILogger`, `ActivitySource`, and `Meter`;
- generated hosts select collection, instrumentation, sampling, processors,
  and exporters;
- OpenTelemetry is the preferred provider-neutral adapter, not the semantic
  owner;
- exact OpenTelemetry specification and semantic-convention revisions are
  pinned because convention groups have independent stability;
- transport telemetry uses framework instrumentation wherever possible and
  avoids duplicate request middleware;
- request and response bodies, authorization material, tokens, cookies,
  claims, configuration values, secrets, personal data, and unbounded metric
  attributes are excluded by default;
- diagnostic telemetry is never an authoritative audit, security, compliance,
  or business record.

The human's explicit alignment statements included:

> “yes we fully 100% agree and align!”

> “Let’s do this. We 100% align and agree!”

For the diagnostics and observability addition, the human further stated:

> “Amazing. Really amazing. I 100% align and agree with everything you
> envisioned and recommended here.”

The human then requested two material corrections before approval:

1. deterministic ASP.NET Core transport-failure handling must accompany
   exception observation, while remaining behaviorally separate from
   telemetry and from consumer-domain error meaning;
2. public browser clients and OAuth token exchange must be initial core
   protocol capabilities rather than deferred work. The aligned analysis also
   added the more foundational client-credentials profile, retained a
   confidential server-side/BFF profile as the preferred browser architecture,
   and kept device authorization, CIBA, FAPI, DPoP, and opaque-token
   introspection deferred.

The public-browser profile must be concrete without pretending that an
ASP.NET Core host alone is a browser client. It therefore includes a
provider-neutral protocol contract, a first .NET browser target projection,
and layered verification:

- deterministic protocol and adversarial conformance;
- automated Playwright for .NET testing against an isolated local
  Aspire/identity-provider fixture;
- optional operator-assisted headed-browser acceptance for real providers
  whose MFA, passkey, consent, conditional-access, or anti-automation
  interaction requires a human;
- a separate explicit human security decision for whether browser-held tokens
  are appropriate for the consuming application's threat model.

Operator assistance is a supported verification mode, not permission for
Program Kit to capture credentials, automate a human identity, provision a
provider, or turn nondeterministic real-provider acceptance into canonical
generation evidence.

The human explicitly aligned with the complete correction:

> “Once again. I agree with every thing you wrote. We are 100% aligned in our
> vision and design”

## Protocol understanding to preserve

Program Kit owns deterministic host mechanics and exact protocol-profile
selection. It does not own provider product behavior or consumer-domain
identity and authorization meaning.

- OAuth 2.0 is delegated authorization infrastructure, not an authentication
  protocol.
- OpenID Connect is an identity layer over OAuth 2.0.
- An interactive client validates an ID token for its client session.
- An API validates an access token; an ID token is not an API access token.
- A public browser client cannot protect a client secret. Its initial profile
  uses authorization code flow with PKCE, exact redirect/origin rules, and no
  implicit or resource-owner-password flow. A confidential server-side/BFF
  profile remains the preferred default for sensitive applications.
- A public-client refresh token is either absent or uses rotation in the
  initial profile while sender-constrained token support remains deferred.
- OAuth client credentials and RFC 8693 token exchange are distinct,
  explicitly selected service-client capabilities. Token exchange declares
  subject and optional actor tokens, impersonation versus delegation,
  resource/audience/scope, requested/issued token types, and client
  authentication; none of those fields imply consumer-domain authorization.
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

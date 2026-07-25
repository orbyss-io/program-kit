# Program Kit deterministic host-tooling extensions

- Canonical design: `architecture-design.json`
- Design identity: `pkid:design:program-kit:host-tooling`
- Design version: `1.0.0`
- State: awaiting exact human approval; nothing in this design is implemented

## Outcome

Program Kit will gain a deterministic, provider-neutral toolbox for generated
.NET hosts. The toolbox owns universal construction mechanics: operation
contracts, configuration composition, typed Options, standards-profiled
transport security, client and host projections, exact provider selection,
validation, and provenance. It does not own a consumer's identity,
authorization, environment, deployment, or other domain meaning.

The key security abstraction is an exact **protocol profile**, not an identity
provider product:

- OAuth 2.0 supplies authorization protocol roles and token use. It is not, by
  itself, end-user authentication.
- OpenID Connect adds authentication and an ID token for the client.
- A web client validates its ID token and maintains its own session.
- An API validates an access token. It must never accept an ID token as an API
  access token.
- The initial API profile supports JWT access tokens only. Opaque-token
  introspection remains a later, separately designed profile.
- Keycloak, Entra ID, or another provider may satisfy a profile only when its
  exact issuer, metadata, endpoints, algorithms, client registration, token
  shape, and claim mapping conform to that profile.

This gives generated apps a stable shape without pretending that provider
products are automatically interchangeable.

## Approved-for-review scope

The proposed extension contains ten bounded capability areas:

1. **Operations convergence** — introduce a compact
   `Orbyss.ProgramKit.Operations` contract package over Artifacts and migrate
   the current DotNet-owned operation binding so all projections share one
   semantic owner.
2. **.NET configuration and Options** — model ordered configuration sources,
   typed and named Options binding, startup validation, reload capability, and
   explicit `IOptions<T>`, `IOptionsSnapshot<T>`, or
   `IOptionsMonitor<T>` consumption.
3. **Provider composition** — support a reviewed built-in provider catalog and
   a closed, explicitly registered custom-provider generation ABI.
4. **Azure configuration adapters** — optionally project Azure Key Vault and
   Azure App Configuration registration, credential references, refresh
   behavior, and secret-safe evidence.
5. **ASP.NET Core security profiles** — generate authentication schemes,
   middleware order, confidential interactive OIDC clients, JWT bearer
   resource servers, named host-policy attachment, and transport results.
6. **Kiota client generation** — consume an exact local foreign OpenAPI
   document through a pinned external Kiota adapter and retain the lock and
   provenance.
7. **Aspire AppHost generation** — project explicit low-level application
   composition into a pinned AppHost project without inventing environment or
   deployment semantics.
8. **Dev Container generation** — generate and validate deterministic
   `.devcontainer` artifacts from explicit inputs, without starting a
   container.
9. **FastEndpoints projection** — optionally project the same operation and
   ASP.NET Core security contracts through a pinned FastEndpoints adapter.
10. **Keycloak local fixture** — generate a minimal secret-free realm import
    and an Aspire-backed disposable local proof that Keycloak can satisfy the
    base OIDC/JWT profiles.

## Configuration and Options semantics

The generated host starts from an explicit ordered source list. The order is
part of the canonical input because later .NET configuration providers win for
the same key. Each source declares startup behavior, reload support, secret
classification, failure disposition, package selection, and provider
specialization. Generation performs no ambient configuration, network, or
credential discovery.

Each Options binding names:

- the owned options type;
- configuration section and optional Options name;
- binding mode and generated binding support;
- validators and whether startup must fail via `ValidateOnStart`;
- whether the value is fixed for the host lifetime, scoped as a snapshot, or
  observable through a monitor;
- whether changing the value is supported live or requires restart.

`IOptions<T>` is the fixed/default choice. `IOptionsSnapshot<T>` is scoped and
provides one value per scope; generated singleton infrastructure may not depend
on it. `IOptionsMonitor<T>` is singleton-capable and supports current values
and change notifications, but only when the selected provider actually emits
change tokens or an explicit refresh path triggers them.

An Options notification does not mean arbitrary application reconfiguration is
safe. It does not reconstruct middleware, DI registrations, listeners,
database providers, serializer profiles, or other host topology. Generated
monitor subscribers must be disposable, keep callbacks bounded, redact values,
and enqueue non-trivial reactions into consumer-owned bounded services.

Required and security-sensitive Options validate at startup. Validation also
runs when monitored values are recreated. Fixtures must distinguish a valid
change, an invalid candidate, provider outage, precedence, scoped consistency,
monitor behavior, restart-required values, and secret redaction. No stronger
“last known good” guarantee is claimed unless a later runtime-controller design
owns and proves it.

## Security ownership boundary

ASP.NET Core authentication handlers may produce an `AuthenticationTicket` and
`ClaimsPrincipal`; authorization middleware may apply explicitly selected
named host policies. Those are transport-host results. Provider claims,
scopes, groups, roles, tenant identifiers, and claim names are not silently
translated into a consumer-domain identity or permission decision.

The initial interactive profile is a confidential server-side web client using
authorization code flow with PKCE. Its exact metadata, callback, cookie,
correlation, nonce, client authentication, token validation, and HTTPS
requirements are explicit. Public browser clients, device flow, CIBA, FAPI,
DPoP, token exchange, and client credentials are deferred.

The initial API profile accepts only JWT access tokens and validates issuer,
audience, signature, allowed algorithm, lifetime, metadata, and selected token
profile. Unknown issuer behavior, permissive algorithms, missing audience,
insecure production metadata, or provider-default claim reinterpretation fail
closed.

## Provider and projection rules

Provider-neutral contracts never reference a product package. Every
technology-specific dependency lives in a provider or projection adapter.
Every adapter selection binds:

- exact Program Kit contract/profile version;
- exact package, tool, SDK, image, or specification version;
- source, license, digest, and resolved dependency evidence where applicable;
- deterministic input and normalized output rules;
- failure, cancellation, secret, and compatibility behavior.

Generated runtime consumers may reference only the selected runtime packages
and generated source. They may not reference Workbench, DotNet generation
assemblies, the CLI, development capabilities, or design-time adapters.

## Explicit deferrals

This design does not authorize:

- consumer-domain identity, authorization, roles, grants, policies,
  entitlements, principals, environment, deployment, release, or workspace
  semantics;
- comprehensive Docker Compose modeling or a Program Kit container
  orchestrator;
- automatic Aspire, Compose, container, Dev Container, Keycloak, Azure,
  deployment, or infrastructure execution;
- production Keycloak provisioning, backup, migration, or administration;
- a custom general-purpose OpenAPI client generator;
- opaque-token introspection, dynamic client registration, provider discovery,
  or automatic issuer selection;
- generation of arbitrary provider code from an unconstrained type name or
  script;
- a guarantee that every configuration change can be applied without restart.

## Dependency direction

The intended package direction is:

```text
Operations -> Artifacts

DotNet -> Operations, existing Program Kit dependencies
Workbench -> Operations, existing Program Kit dependencies

optional provider/projection adapter
  -> its Program Kit base contract
  -> its exact external technology dependencies

generated host
  -> selected runtime packages and generated source only
```

The exact adapter package graph is deliberately not invented in this design.
The implementation work unit that selects each external technology must first
record exact source, license, package/image/tool, dependency-closure, and
compatibility evidence. A selection that changes these boundaries stops for a
design revision.

## Delivery order

The configuration and Operations foundations precede their consumers:

```text
Operations convergence
        |
configuration composition + Options + reload
        |
provider ABI and built-in provider profiles
        |
        +-- Azure Key Vault / Azure App Configuration
        +-- ASP.NET Core OIDC and JWT profiles
        +-- Kiota client adapter
        +-- Aspire AppHost projection
        +-- Dev Container projection
                 |
                 +-- FastEndpoints projection (after ASP.NET security)
                 +-- Keycloak local fixture (after ASP.NET security + Aspire)
        |
migration, isolated consumers, deterministic closure
```

## Evidence required before completion

Implementation is incomplete until all of the following are true:

- schemas/models/validators and JSON round trips agree;
- package/reference rules and generated consumer closure are proven;
- repeated generation produces byte-identical normalized output;
- all external selections are exact and lock-verified;
- Options startup, snapshot, monitor, refresh, invalid-change, outage,
  precedence, and redaction fixtures pass;
- OIDC and JWT positive and adversarial fixtures pass with protocol roles kept
  distinct;
- Keycloak proves provider substitution but is not required by the base
  security profiles;
- Kiota, Aspire, Dev Container, and FastEndpoints outputs build or validate in
  isolated consumers without design-time dependencies;
- migration removes parallel semantic owners and updates version/impact
  evidence;
- the existing Program Kit test plan and an independent review pass.

## Consulted external authorities

These sources informed the design boundary. They are not yet implementation
selections; implementation must bind exact applicable revisions and digests.

- OpenID Connect Core 1.0 incorporating Errata Set 2 and Discovery 1.0,
  OpenID Foundation:
  <https://openid.net/specs/openid-connect-core-1_0-errata2.html>
  and
  <https://openid.net/specs/openid-connect-discovery-1_0.html>
- OAuth 2.0 Security Best Current Practice, RFC 9700 / BCP 240:
  <https://www.rfc-editor.org/rfc/rfc9700>
- OAuth Authorization Server Metadata, RFC 8414; JWT Profile for OAuth 2.0
  Access Tokens, RFC 9068; Bearer Token Usage, RFC 6750; and PKCE, RFC 7636:
  <https://www.rfc-editor.org/rfc/rfc8414>,
  <https://www.rfc-editor.org/rfc/rfc9068>,
  <https://www.rfc-editor.org/rfc/rfc6750>, and
  <https://www.rfc-editor.org/rfc/rfc7636>
- .NET Options and ASP.NET Core Options guidance:
  <https://learn.microsoft.com/en-us/dotnet/core/extensions/options> and
  <https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/options?view=aspnetcore-10.0>
- ASP.NET Core OIDC and JWT bearer guidance:
  <https://learn.microsoft.com/en-us/aspnet/core/security/authentication/configure-oidc-web-authentication?view=aspnetcore-10.0>
  and
  <https://learn.microsoft.com/en-us/aspnet/core/security/authentication/configure-jwt-bearer-authentication?view=aspnetcore-10.0>
- Azure Key Vault and Azure App Configuration provider guidance:
  <https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration?view=aspnetcore-10.0>
  and
  <https://learn.microsoft.com/en-us/azure/azure-app-configuration/reference-dotnet-provider>
- Kiota generation and locking:
  <https://learn.microsoft.com/en-us/openapi/kiota/using>
- Aspire integrations and Keycloak integration:
  <https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/integrations-overview>
  and
  <https://learn.microsoft.com/en-us/dotnet/aspire/authentication/keycloak-integration>
- Development Container Specification:
  <https://containers.dev/implementors/spec/>
- FastEndpoints security:
  <https://fast-endpoints.com/docs/security>
- Keycloak realm import:
  <https://www.keycloak.org/server/importExport>

## Review decision

Only explicit human approval of the exact canonical design digest and exact
implementation-plan digest authorizes implementation. Approval does not
authorize any deferred capability or external execution.

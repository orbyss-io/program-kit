# Program Kit deterministic host-tooling extensions

- Canonical design: `architecture-design.json`
- Design identity: `pkid:design:program-kit:host-tooling`
- Design version: `1.2.0`
- State: awaiting exact human approval; nothing in this design is implemented

## Outcome

Program Kit will gain a deterministic, provider-neutral toolbox for generated
.NET hosts. The toolbox owns universal construction mechanics: operation
contracts, configuration composition, typed Options, structured diagnostics
and observability, standards-profiled transport security, client and host
projections, exact provider selection, validation, and provenance. It does not
own a consumer's identity, authorization, observability meaning, environment,
deployment, or other domain meaning.

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

The proposed extension contains fourteen bounded capability areas:

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
5. **Diagnostics and observability** — generate structured .NET logging,
   tracing, metrics, W3C correlation, transport instrumentation, exception
   observation, redaction/cardinality rules, and controlled collection/export
   through exact platform APIs and a pinned OpenTelemetry adapter.
6. **ASP.NET Core transport failures** — generate Problem Details, ordered
   exception handlers, middleware and diagnostic disposition while requiring
   explicit consumer-owned mappings for non-generic error meaning.
7. **ASP.NET Core security profiles** — generate authentication schemes,
   middleware order, confidential interactive OIDC clients, JWT bearer
   resource servers, named host-policy attachment, and transport results.
8. **Public browser security** — define an authorization-code-with-PKCE public
   OIDC profile, initially project it through a pinned Blazor WebAssembly
   adapter, and generate layered protocol/browser verification.
9. **OAuth service clients** — generate explicit client-credentials and RFC
   8693 token-exchange profiles without ambient token forwarding or inferred
   delegation, impersonation, scope, audience, or authorization.
10. **Kiota client generation** — consume an exact local foreign OpenAPI
   document through a pinned external Kiota adapter and retain the lock and
   provenance.
11. **Aspire AppHost generation** — project explicit low-level application
   composition into a pinned AppHost project without inventing environment or
   deployment semantics.
12. **Dev Container generation** — generate and validate deterministic
   `.devcontainer` artifacts from explicit inputs, without starting a
   container.
13. **FastEndpoints projection** — optionally project the same operation and
    ASP.NET Core security contracts through a pinned FastEndpoints adapter.
14. **Keycloak local fixture** — generate a minimal secret-free realm import
    and an Aspire-backed disposable local proof that Keycloak can satisfy the
    base OIDC/JWT and selected OAuth service-client profiles.

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

## Diagnostics and observability semantics

.NET libraries emit provider-neutral signals through the platform APIs:
`ILogger`, `ActivitySource`/`Activity`, and `Meter`. Generated application hosts
select collection, filtering, sampling, processing and export. OpenTelemetry is
the preferred initial adapter over those APIs; it is not the semantic owner.

The canonical telemetry composition declares:

- stable logger categories, structured templates and event IDs, preferring
  source-generated `LoggerMessage` methods;
- stable, versioned `ActivitySource` and `Meter` names;
- trace/span names and kinds, metric instrument types, units and bounded
  attributes;
- W3C Trace Context propagation, with baggage treated as untrusted metadata;
- resource identity, instrumentation, filters, sampling, processors, exporters,
  batching, failure, drop and bounded shutdown behavior;
- redaction/classification rules and explicit metric-cardinality limits;
- exact OpenTelemetry specification, semantic-convention, SDK,
  instrumentation, exporter and stability-opt-in revisions.

ASP.NET Core and `HttpClient` use framework/OpenTelemetry instrumentation where
it provides the selected behavior. Custom middleware adds only missing,
bounded Program Kit operation correlation and must not duplicate transport
spans or logs.

Exception handling remains behaviorally separate from telemetry. The generated
pipeline can observe and classify an exception, but it changes an HTTP response
only through an explicit transport failure contract. Consumer-domain error
meaning remains consumer-owned.

HTTP request/response logging is a separate restrictive diagnostic profile.
Bodies, authorization headers, tokens, cookies, claims, configuration values,
secrets, personal data, raw exceptions and unbounded attributes are excluded
by default. Diagnostic telemetry may be sampled, dropped or unavailable and is
never an authoritative business ledger, security audit, compliance record or
authorization conclusion.

Logging filters may use controlled configuration reload. The OpenTelemetry
provider/instrumentation/processor/exporter graph is initially startup-fixed
unless an exact selected revision proves safe reconfiguration. Export failure
must be observable and bounded without silently changing application success.

## ASP.NET Core transport-failure semantics

Exception observation does not define client-visible failure behavior. The
selected transport-failure profile separately composes:

- `AddProblemDetails`;
- ordered singleton `IExceptionHandler` registrations;
- `UseExceptionHandler` in an explicit middleware position;
- optional status-code pages and content negotiation;
- environment-specific detail disclosure;
- cancellation and client-disconnect classification;
- behavior when a response has already started;
- generated OpenAPI Problem Details responses where the owned operation
  contract declares them;
- the .NET 10 handled-exception diagnostic suppression choice.

The generic production fallback is stable and discloses no internal detail.
Every non-generic exception-to-status or exception-to-Problem-Details mapping
is explicit consumer input. Program Kit never infers HTTP meaning from an
exception type name, message, namespace, inheritance pattern, or provider
payload.

Exception handling and observability share a correlation identity but not
ownership. Fixtures prove that handled and unhandled exceptions, cancellation,
response-started cases and framework endpoint projections produce their exact
response and diagnostic disposition without double logging or double counting.

## Security ownership boundary

ASP.NET Core authentication handlers may produce an `AuthenticationTicket` and
`ClaimsPrincipal`; authorization middleware may apply explicitly selected
named host policies. Those are transport-host results. Provider claims,
scopes, groups, roles, tenant identifiers, and claim names are not silently
translated into a consumer-domain identity or permission decision.

The initial confidential interactive profile is a server-side web client/BFF
using authorization code flow with PKCE. Its exact metadata, callback, cookie,
correlation, nonce, client authentication, token validation, and HTTPS
requirements are explicit. It remains the preferred browser architecture for
sensitive and business applications.

The separate public-browser profile also uses authorization code flow with
PKCE, but carries no client secret. It explicitly declares redirect and
post-logout URIs, origins and CORS expectations, state, nonce, issuer, scopes,
API resource, token storage, refresh-token absence or rotation, and logout.
Implicit and resource-owner-password flows are forbidden. The initial target
is a pinned Blazor WebAssembly OIDC adapter behind a versioned browser-target
projection boundary; other browser languages require their own selected
adapter rather than generic JavaScript generation.

Public-browser verification is layered:

1. deterministic protocol and adversarial vectors;
2. automated Playwright for .NET tests against an isolated local
   Aspire/identity-provider fixture;
3. optional operator-assisted headed-browser acceptance for real providers
   whose MFA, passkey, consent, conditional-access, or anti-automation
   interaction requires a human;
4. an explicit human threat-model decision that browser-held tokens are
   acceptable for the consuming application.

Operator-assisted acceptance pauses without capturing provider credentials,
resumes after the callback, records only redacted non-authoritative evidence,
and never becomes deterministic generation proof. Playwright authentication
state, traces, cookies and tokens are ephemeral secrets and cannot enter source
control or durable Program Kit evidence.

The initial service-client profiles include OAuth client credentials and RFC
8693 token exchange. Client credentials declares exact token endpoint, client
authentication, resource, audience and scope. Token exchange additionally
declares subject-token provenance/type, optional actor token, delegation versus
impersonation, requested and issued token types, and cache/lifetime behavior.
Neither profile performs ambient token forwarding or infers permissions,
downscoping, delegation, impersonation, audience, resource, or domain
authorization.

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
- device authorization, CIBA, FAPI, DPoP, implicit, or
  resource-owner-password profiles;
- generation of arbitrary provider code from an unconstrained type name or
  script;
- a guarantee that every configuration change can be applied without restart;
- application/domain observability meaning, business event or audit catalogs,
  telemetry backends, collectors, dashboards, alerts, retention or incident
  policies;
- automatic telemetry emission by Program Kit generation, design, validation
  or development-session tooling;
- Serilog, NLog, Application Insights, Seq, Grafana, Prometheus or another
  vendor product as a base semantic dependency.

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
diagnostics + logging + tracing + metrics + OpenTelemetry adapter
        |
        +-- Azure Key Vault / Azure App Configuration
        +-- ASP.NET Core transport-failure profile
        +-- ASP.NET Core confidential OIDC and JWT profiles
        |       |
        |       +-- public-browser OIDC + Blazor WebAssembly adapter
        |       +-- client credentials + RFC 8693 token exchange
        +-- Kiota client adapter
        +-- Aspire AppHost projection
        +-- Dev Container projection
                 |
                 +-- FastEndpoints projection (after failure + security)
                 +-- Keycloak/Playwright local fixture
                     (after security + public browser + Aspire)
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
- logging, trace, metric, W3C correlation, sampling, exporter outage, bounded
  flush, sensitive-data, cardinality and duplicate-instrumentation fixtures
  pass;
- OIDC and JWT positive and adversarial fixtures pass with protocol roles kept
  distinct;
- Problem Details, ordered handler, middleware, content-negotiation,
  cancellation, response-started, disclosure, OpenAPI and exactly-once
  diagnostics fixtures pass;
- public-browser PKCE, redirect/origin, state/nonce, storage, refresh rotation
  or absence, API access and logout fixtures pass in automated local browser
  tests without any client secret;
- client-credentials and token-exchange positive and adversarial fixtures prove
  exact client authentication, resource/audience/scope, token types,
  subject/actor distinction, delegation/impersonation, caching and redaction;
- optional real-provider acceptance remains operator-assisted, secret-safe,
  separately identified and non-authoritative;
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
- .NET logging and library instrumentation guidance:
  <https://learn.microsoft.com/en-us/dotnet/core/extensions/logging/overview>,
  <https://learn.microsoft.com/en-us/dotnet/core/extensions/logging/source-generation>,
  and
  <https://learn.microsoft.com/en-us/dotnet/core/extensions/logging-library-authors>
- .NET diagnostics and OpenTelemetry guidance:
  <https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel>
  and
  <https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing-instrumentation-walkthroughs>
- ASP.NET Core HTTP logging:
  <https://learn.microsoft.com/en-us/aspnet/core/fundamentals/http-logging/?view=aspnetcore-10.0>
- OpenTelemetry specification and independently versioned semantic
  conventions:
  <https://opentelemetry.io/docs/specs/otel/>,
  <https://opentelemetry.io/docs/specs/semconv/>, and
  <https://opentelemetry.io/docs/specs/semconv/http/>
- ASP.NET Core OIDC and JWT bearer guidance:
  <https://learn.microsoft.com/en-us/aspnet/core/security/authentication/configure-oidc-web-authentication?view=aspnetcore-10.0>
  and
  <https://learn.microsoft.com/en-us/aspnet/core/security/authentication/configure-jwt-bearer-authentication?view=aspnetcore-10.0>
- ASP.NET Core error handling, Problem Details, `IExceptionHandler`, and .NET 10
  handled-exception diagnostics:
  <https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling?view=aspnetcore-10.0>,
  <https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0>,
  and
  <https://learn.microsoft.com/en-us/aspnet/core/breaking-changes/10/exception-handler-diagnostics-suppressed?view=aspnetcore-10.0>
- OAuth 2.0 Token Exchange, RFC 8693, and the client-credentials grant in OAuth
  2.0, RFC 6749:
  <https://www.rfc-editor.org/rfc/rfc8693.html>
  and
  <https://www.rfc-editor.org/rfc/rfc6749>
- Browser-based OAuth guidance and the .NET 10 Blazor WebAssembly OIDC
  projection. The reviewed browser guidance is an Internet-Draft and is design
  input rather than a floating normative compatibility contract:
  <https://datatracker.ietf.org/doc/draft-ietf-oauth-browser-based-apps/26/>
  and
  <https://learn.microsoft.com/en-us/aspnet/core/blazor/security/webassembly/standalone-with-authentication-library?view=aspnetcore-10.0>
- Playwright for .NET browser, authentication, network and trace guidance:
  <https://playwright.dev/dotnet/docs/intro>,
  <https://playwright.dev/dotnet/docs/auth>,
  <https://playwright.dev/dotnet/docs/network>, and
  <https://playwright.dev/dotnet/docs/trace-viewer>
- Aspire AppHost testing:
  <https://learn.microsoft.com/en-us/dotnet/aspire/testing/manage-app-host>
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

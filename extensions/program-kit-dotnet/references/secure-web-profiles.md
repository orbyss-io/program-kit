# Secure web boundary profiles

## Purpose

This is an implementation contract, not a menu of unanswered questions. Once a profile is selected,
features inherit its authentication, authorization, HTTP, configuration, operational, and test
behavior. A feature normally supplies only route ownership, wire contracts, a named policy or an
explicit anonymous declaration, and its business outcomes.

The profile contract version is recorded in `docs/architecture/bootstrap-decisions.json` and
`.program-kit/web-profile.json`. Program Kit upgrades may add capabilities compatibly; a breaking
behavior change requires a new profile version.

## Security assurance contract

Both authenticated profiles inherit:

- threat model `program-kit-web-threat-model-v1` from `web-security-threat-model.md`; and
- evidence profile `program-kit-web-security-evidence-v1` from
  `web-security-evidence.json`.

The evidence register is authoritative for source status, threat-to-control traceability,
configurable-default rationale, residual risks, verification levels, and mandatory review triggers.
It distinguishes final standards and specifications, government guidance, an active IETF draft,
peer-reviewed formal analyses, platform guidance, industry frameworks, and Program Kit policy. A
local policy or operational default is never presented as a normative standard or scientific
result.

A consuming project inherits this assurance baseline by exact ID. Its architecture records only
additional assets, threats or assumptions; configured-value overrides; accepted residual risks; and
stronger controls. Any security-sensitive override requires an Accepted ADR naming the owner,
evidence, review condition, and regression test. Feature specifications consume the resulting
boundary and do not reopen inherited protocol decisions.

## Selection

| Application shape | Selected profile | Rule |
| --- | --- | --- |
| Browser UI, no explicit override | `bff-cookie-v1` | Secure default |
| Same-origin or proxyable browser UI | `bff-cookie-v1` | Preferred |
| Independently hosted static SPA that must call APIs directly | `spa-pkce-v1` | Explicit choice and acknowledgement |
| No browser authentication boundary | `none-v1` | Explicit or derived non-web choice |

An unqualified request for “SPA authentication” does not select browser-held tokens. A SPA is a UI
architecture; it can and normally should use the BFF profile.

## Common contract

### Runtime configuration

Configuration binds to `ProgramKit:Web` and is validated at startup. Secret values come from the
environment or a secret provider and never from committed settings.

- `Profile`: `None`, `BffCookie`, or `SpaPkce`.
- `Authority`: HTTPS issuer URL; HTTP is permitted only by an explicit local-development setting.
- `ClientId`; `ClientSecret` is required only for BFF.
- `Audience`, `Scopes`, and `RoleClaim` (default `roles`).
- exact `AllowedOrigins`; wildcards and origin reflection are rejected.
- callback, signed-out callback, remote-signout, and access-denied paths.
- discovery/JWKS, remote-authentication, and back-channel time budgets.
- session idle and absolute lifetimes; the absolute lifetime bounds refresh-token use.
- cookie name, `Secure`, `HttpOnly`, and `SameSite` policy.

Invalid or incomplete selected-profile configuration prevents startup with a path-specific error.
Checked-in local settings contain identifiers and loopback URLs only; production secrets and origins
must be supplied by deployment.

The presence of a configurable value does not mean its default is universal. The evidence register
classifies every material default and states when it must be reviewed. In particular, identity time
budgets are service-objective choices, session durations depend on assurance level and product risk,
local identities and ports are development fixtures, locale selection is a product default, and CSP
must be tightened or minimally adapted to the actual frontend resource model.

### Authentication and claims

- Issuer, audience, signature, and token lifetime are validated.
- The stable application subject is the issuer plus `sub`; email and display name are not keys.
- provider roles are normalized into the configured role claim and then the platform role claim.
- policies use named requirements such as `role:admin`; features do not parse provider token shapes.
- endpoints require authenticated users by fallback policy unless they explicitly opt into anonymous
  access. Login initiation and protocol callback endpoints are the standard anonymous set; any health
  endpoint needs a separately owned contract.
- authentication failures use `401`; authenticated policy failures use `403`. API failures are
  `application/problem+json` with stable `code`, `traceId`, and no provider internals.

### HTTP and telemetry

- Every request has a validated or generated correlation ID, returned as `X-Correlation-ID` and
  included in problem responses and logging scopes.
- Security headers include no-sniff, frame denial, a restrictive referrer policy, permissions policy,
  and a profile-appropriate CSP. HSTS is enabled outside local development.
- CORS is disabled for the same-origin BFF. SPA PKCE permits only configured exact origins, headers,
  and methods; credentials are not combined with wildcard origins.
- `ProgramKit.Host` does not expose or aggregate application health. Until CShells defines a feature-health
  contribution interface, selected features own any liveness/readiness surface and its redaction contract.
- identity-provider navigation is outside app-controlled response budgets. Product SLOs for
  discovery, JWKS, callback, API, and session operations are feature/deployment decisions and are
  not inferred from Program Kit's separate five-second local preflight default.

### Identity provider fixture

The local profile supplies a pinned Keycloak container, imported realm, confidential BFF client,
public SPA-PKCE client, API audience/scope, redirect and post-logout URIs, and three non-production
personas: authorized user, administrator, and authenticated user without the requested role. Fixture
credentials are local-test data and are never reused in deployed environments.

## `bff-cookie-v1`

- The selected web-boundary feature is a confidential OIDC client using authorization code flow and PKCE.
- Access and refresh tokens remain in a server-side `ITicketStore`; the browser cookie contains only
  an opaque protected session key.
- Cookie defaults are `HttpOnly=true`, `Secure=Always`, `SameSite=Lax`, a `__Host-` name, no domain,
  and path `/`. Local HTTP is supported only by an explicit development override and uses visibly
  development-only cookie names because browsers reject `__Host-` cookies without `Secure`.
- `GET /bff/login?returnUrl=/safe/path` starts login. Return URLs must be local and relative.
- `GET /bff/user` returns a minimal session projection (authentication state, subject, display name,
  roles, and expiry) and never returns tokens or the raw claims principal.
- `GET /bff/antiforgery` issues an antiforgery request token for in-memory use by the UI.
- unsafe same-origin `/api` and `POST /bff/logout` requests require the token in
  `X-CSRF-TOKEN`. Cross-site navigation cannot perform logout.
- session renewal is server controlled and cannot extend beyond the configured absolute lifetime.
  Expired or unrecoverable sessions terminate locally and return `401` to API requests.
- logout deletes the local server ticket and cookie first, then attempts RP-initiated provider
  logout. A failed or unavailable provider logout cannot restore the local session. The v1 profile
  does not claim back-channel logout; that requires verified logout-token validation in a later
  compatible profile.
- cookie redirects are converted to `401`/`403` problem responses for `/api`; interactive BFF
  endpoints retain protocol redirects.

## `spa-pkce-v1`

- The browser is a public authorization-code client with PKCE S256 and no client secret.
- The API accepts bearer tokens only and validates issuer, audience, signature, and lifetime.
- access and refresh tokens are memory-only by default. Browser refresh terminates the local session
  unless the explicitly selected client library can re-establish it using provider state without
  durable token storage.
- silent renewal, if enabled, is bounded and failure transitions to a locally signed-out state.
- logout clears all local authentication state before RP-initiated provider logout.
- exact API origin, allowed browser origins, redirect URIs, logout URIs, scopes, and renewal timeouts
  are part of the selected profile configuration.
- `eng/program-kit/web/vite.security.mjs` owns browser-response headers for local Vite development
  and preview. Consumer-owned `vite.config` imports `programKitSpaSecurity` with exact API and
  identity origins. A production static server or edge must translate the checked
  `spa-security.json` contract; the production TLS terminator separately owns HTTPS and HSTS, so
  local HTTP never claims them.
- The production CSP permits self-hosted scripts/styles by default. Add an exact source, nonce, or
  hash only after resource review; do not add `unsafe-inline` or wildcard sources. Keycloak
  top-level navigation needs no CSP source, while browser discovery/token calls need its exact
  origin in `connect-src`. Another approved SPA server must implement the same header contract and
  pass WEB-V1 configuration and WEB-V3 browser assertions.

## Local preflight ownership

`eng/program-kit/preflight.py` runs before any host or Compose command. It checks the Docker CLI,
then calls the daemon directly with a bounded five-second Program Kit development default. The
timeout is configurable through `PROGRAMKIT_PREFLIGHT_TIMEOUT_SECONDS`; it is a tooling hang budget,
not a product SLO. `PKP001` through `PKP004` stop on the first invalid setting, missing CLI, timeout,
or stopped daemon without cascading commands or echoing daemon error details.

## Mandatory verification

Every selected web profile implements assurance levels `WEB-V1` through `WEB-V3` from the evidence
register. A production deployment additionally owns `WEB-V4`. Every control must retain at least one
prevention or detection mechanism and its mapped negative evidence; a passing happy-path login is
not security evidence by itself.

The shared contract suite plus profile-specific browser suite verifies:

1. Anonymous API call is `401`; wrong-role call is `403`; authorized role succeeds.
2. Roles are derived from the configured provider claim and unknown/missing claims grant nothing.
3. Login returns only to a validated local path.
4. Browser refresh follows the selected session contract without leaking tokens to persistent
   storage, URLs, logs, or rendered output.
5. Session expiry and failed renewal produce a deterministic locally signed-out UI.
6. Local logout remains complete when the provider is unavailable; remote logout success is tested
   separately from that provider-controlled failure.
7. BFF unsafe requests without or with an invalid antiforgery token fail; valid same-origin requests
   succeed. SPA preflight and disallowed-origin cases are tested instead.
8. Security headers, correlation IDs, and Problem Details are asserted. Feature-owned operational probes
   require their own degradation/recovery contract and tests when selected.
9. Playwright runs the real local Keycloak login for the authorized, administrator, and wrong-role
   personas. Authentication state files are generated under test artifacts, treated as secrets, and
   never committed.

Unit mocks may test feature policy logic, but they do not replace this browser/provider contract.

## Review and non-claims

The profile must be reviewed when its standards or platform guidance changes, when the browser-app
draft becomes final, when the runtime/provider/library/deployment model changes, after a relevant
incident or advisory, for a security-sensitive override, and at least every twelve months. Review
updates the evidence register's `lastReviewed` value and either preserves the profile contract or
introduces a versioned migration.

Program Kit does not claim that browser tests, security headers, BFF, PKCE, or OIDC alone make an
application secure. It does not cover compromised identity providers or hosts, business-policy
correctness, tenant isolation, abuse controls, privacy classification, production secret/key
management, or risk-specific step-up authentication. Those responsibilities remain visible in the
threat model and the consuming architecture.

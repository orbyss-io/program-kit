# Program Kit web security threat model v1

- Model ID: `program-kit-web-threat-model-v1`
- Evidence profile: `program-kit-web-security-evidence-v1`
- Applies to: `bff-cookie-v1` and `spa-pkce-v1`
- Review owner: Program Kit maintainers
- Last reviewed: 2026-09-01

## Assurance claim

This model defines the threats that the secure web profiles are designed to reduce. It does not
claim that using a profile makes an application secure. Its claims hold only while the assumptions,
configuration constraints, implementation controls, and verification obligations below remain
true.

The accompanying `web-security-evidence.json` is the authoritative machine-readable mapping from
threats to controls, evidence, configurable defaults, residual risks, and review triggers. Sources
are classified by authority. An IETF working-group draft or vendor document is never represented as
a final standard, and a local Program Kit policy is never represented as scientific proof.

## Protected assets

- OAuth authorization codes, access tokens, refresh tokens, client credentials, and logout tokens.
- Application session identifiers, server-side tickets, antiforgery tokens, and signing/data-
  protection keys.
- User identity, stable subject, normalized roles, authorization decisions, and protected data.
- Redirect, issuer, audience, origin, scope, callback, and logout configuration.
- Security-relevant logs, health responses, browser state, test authentication state, dependencies,
  and identity-provider fixtures.

## Trust boundaries

1. **Browser execution boundary** — application JavaScript, third-party scripts, extensions, storage,
   cookies, and navigation are less trusted than server-side code.
2. **Application/BFF boundary** — the browser presents an opaque session and antiforgery proof; the
   server owns OAuth tokens and authorization for `bff-cookie-v1`.
3. **API boundary** — every protected operation independently authenticates the caller and evaluates
   its named application policy. UI visibility is not an authorization boundary.
4. **Identity-provider boundary** — discovery, keys, protocol redirects, claims, and logout messages
   cross an external administrative and availability boundary.
5. **Session-store boundary** — server tickets and keys must remain confidential, integrity-
   protected, revocable, and unavailable to the browser.
6. **Deployment and supply-chain boundary** — configuration, secrets, packages, images, generated
   assets, and CI evidence cross from build systems into the running application.

## Attacker capabilities

The profiles consider:

- a cross-site attacker who can cause navigation and CORS-safelisted requests;
- malicious JavaScript executing in the application origin through XSS, a compromised dependency,
  or a hostile browser extension;
- interception, injection, replay, mix-up, and redirect manipulation at OAuth/OIDC endpoints, while
  assuming correctly configured TLS is not cryptographically broken;
- theft of a browser cookie, authorization code, bearer token, refresh token, or logged secret;
- an authenticated user with missing, malformed, unknown, or insufficient roles;
- identity-provider unavailability, slow discovery/JWKS responses, failed renewal, and failed remote
  logout;
- configuration mistakes involving issuer, audience, origin, callback, scope, claims, secrets, and
  HTTP development exceptions; and
- dependency, container-image, fixture, or generated-test-state leakage and drift.

## Threat catalogue

| ID | Threat | Principal controls | Residual exposure |
| --- | --- | --- | --- |
| `WEB-T01` | Browser token extraction | BFF default, server ticket store, opaque `HttpOnly` cookie | Same-origin malicious code can still act through the victim browser. |
| `WEB-T02` | Authorization-code interception or injection | Authorization Code, PKCE S256, state/nonce validation, exact redirect URIs | A compromised endpoint or identity provider remains powerful. |
| `WEB-T03` | CSRF and login/logout CSRF | Antiforgery on unsafe BFF operations, SameSite cookie, local return URLs, exact origins | Antiforgery does not stop same-origin XSS. |
| `WEB-T04` | Token or identity substitution | Exact issuer, audience, signature, lifetime, nonce and claim validation | Incorrectly trusted identity-provider keys or administration remain out of scope. |
| `WEB-T05` | Missing or confused authorization | Authenticated fallback policy, named server policies, normalized roles, `401`/`403` tests | Business-policy correctness remains owned by the feature. |
| `WEB-T06` | Session fixation, theft, or excessive persistence | Protected host cookie, server-side session, idle and absolute bounds, local invalidation | A stolen live session remains usable until detected, expired, or revoked. |
| `WEB-T07` | Incomplete or forged logout | Local-first termination; standards-compliant RP logout; no back-channel claim without logout-token validation | Provider and other relying-party sessions may remain active. |
| `WEB-T08` | Cross-origin data access | Same-origin BFF; otherwise exact CORS allowlist and no wildcard credentials | CORS is not authentication and does not stop non-browser clients. |
| `WEB-T09` | XSS, framing, or content injection amplification | CSP, no-sniff, frame denial, restrictive browser policies, token isolation | CSP is defense in depth; output encoding and dependency hygiene are still required. |
| `WEB-T10` | Information leakage | Stable Problem Details, redacted readiness, correlation without secrets, PII-safe logs | Application code can still introduce sensitive logging. |
| `WEB-T11` | Identity outage or latency propagation | Bounded app-controlled calls, cached safe readiness, deterministic local signed-out state | Navigation on the provider origin is outside application control. |
| `WEB-T12` | Dependency, fixture, or test-state compromise | Version/digest pinning, generated-state exclusion, dependency checks, real-provider tests | Pinning preserves identity, not trustworthiness; vulnerability review is still required. |
| `WEB-T13` | Unsafe configuration or profile drift | Startup validation, governed profile selection, managed hashes, evidence-linked regression suite | Deployment systems may bypass or replace managed configuration. |

## Profile-specific consequences

### `bff-cookie-v1`

OAuth tokens remain outside browser JavaScript, reducing token-exfiltration consequences. The BFF
does not prevent malicious same-origin code from sending authorized requests through the user's
browser. CSP, safe rendering, dependency hygiene, antiforgery, business authorization, session
limits, and monitoring therefore remain mandatory.

### `spa-pkce-v1`

The browser is a public client and cannot keep a client secret. PKCE protects the authorization code
but does not make bearer tokens safe from malicious same-origin JavaScript. This profile accepts a
larger token-exfiltration consequence and therefore requires an explicit deployment rationale,
memory-only token storage by default, exact CORS, bounded renewal, and corresponding negative tests.

## Assumptions and out-of-scope risks

- Production transport uses correctly configured HTTPS; development HTTP is limited to explicit
  loopback/container use and is not production evidence.
- The operating system, runtime, cryptography, data-protection keys, secret provider, DNS, reverse
  proxy, and trusted identity provider are securely administered.
- Compromise of the identity provider, host, signing keys, or deployment control plane is not
  prevented by these profiles.
- Feature owners still define correct business policies, data classification, tenancy isolation,
  abuse controls, privacy requirements, and step-up authentication needs.
- Availability budgets constrain failure propagation; they do not prove identity-provider
  availability or prevent denial of service.
- Playwright and contract tests demonstrate selected behavior. They do not prove absence of defects,
  replace dependency review, penetration testing, protocol conformance testing, or formal
  verification of the deployed system.

## Project adoption

A consuming architecture references this model and its evidence profile by exact ID. It records only
project-specific changes: additional assets or attackers, changed assumptions, configured-value
overrides, residual-risk acceptance, and stronger controls. Repeating the inherited OAuth/OIDC
plumbing as feature-specification questions is architecture drift.


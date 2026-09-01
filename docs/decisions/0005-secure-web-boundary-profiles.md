# ADR 0005: Versioned secure web boundary profiles

- Status: Accepted
- Date: 2026-09-01
- Decision owners: Program Kit maintainers

## Context

The first authenticated vertical slice in a consuming repository exposed that the bootstrap left
ordinary web-boundary decisions to feature specifications. Authority and client configuration,
claim normalization, authorization failures, browser session storage, refresh and logout behavior,
CSRF, CORS, CSP, health, and browser-test personas were all known implementation prerequisites but
were not supplied as one executable contract.

That defeats the purpose of a bootstrapped repository. A feature specification should name its
actor, policy, operation, and observable outcome. It should not redesign authentication plumbing or
invent runtime configuration before it can cross the first HTTP boundary.

## Decision

Program Kit defines versioned secure web boundary profiles. Selecting a browser UI selects
`bff-cookie-v1` unless explicit intake or an Accepted ADR selects another profile.

`bff-cookie-v1` uses a same-origin backend-for-frontend. The host is a confidential OAuth client,
uses authorization code flow with PKCE, retains access and refresh tokens in a server-side ticket
store, and gives the browser only an encrypted `Secure`, `HttpOnly` session cookie. Unsafe API and
logout requests require antiforgery validation. Browser code never reads bearer or refresh tokens.

`spa-pkce-v1` is an explicit alternative for a separately hosted browser client that must call an
API directly. It uses authorization code flow with PKCE and API bearer validation. Its browser
token exposure, renewal, storage, CORS, and logout consequences must be acknowledged in the
bootstrap baseline. Tokens are held in memory by default; durable browser token storage is not a
Program Kit default.

`none-v1` is available for applications without a web authentication boundary. It is never inferred
for a detected browser UI.

The complete executable contract is maintained in the .NET extension's
`references/secure-web-profiles.md`. The contract owns configuration names and validation, identity
provider fixtures, claims and role normalization, middleware ordering, response/error conventions,
safe health and telemetry, logout limitations, and the mandatory browser/contract test matrix.

Security claims are governed by `program-kit-web-threat-model-v1` and
`program-kit-web-security-evidence-v1`, maintained respectively in
`references/web-security-threat-model.md` and `references/web-security-evidence.json`. Consuming
architectures inherit those controls, assumptions, residual risks, evidence classifications,
configurable-default rationale, and review triggers by exact ID. Project-specific deviations require
an Accepted ADR with an owner, evidence, risk treatment, and regression coverage.

## Selection rules

1. Explicit intake wins when it names a profile or requires an incompatible deployment shape.
2. A browser UI with no explicit choice adopts `bff-cookie-v1`.
3. `spa-pkce-v1` is selected only when intake requires independent static hosting or direct browser
   API access, or an Accepted ADR records why browser-held tokens are justified.
4. A feature specification may request roles and policies but cannot silently change the selected
   profile.
5. Profile changes are architecture changes with migration and regression evidence, not feature
   implementation details.

## Consequences

Authenticated vertical slices can start with named policies and stable HTTP outcomes. The bootstrap
has more generated infrastructure and a mandatory identity-provider browser test, but that work is
implemented and maintained once by Program Kit instead of rediscovered by each feature.

Local cookie clearing is the terminal application-controlled logout outcome. RP-initiated logout at
the identity provider is best effort after navigation; no application can promise its own error page
while the browser is controlled by an unavailable external provider. Back-channel logout is not
claimed by the v1 profile; adding it requires verified application-side logout-token validation and
a compatible profile revision.

## Security basis and strength of claim

The protocol controls follow the final [OAuth 2.0 Security Best Current Practice (RFC
9700)](https://www.rfc-editor.org/rfc/rfc9700.html), final OpenID Connect Core and logout
specifications, and final NIST SP 800-63B-4/SP 800-63C-4 federation and session guidance. OAuth and
OpenID Connect have also received peer-reviewed formal analysis of authentication, authorization,
and session-integrity properties:

- [A Comprehensive Formal Security Analysis of OAuth
  2.0](https://publ.sec.uni-stuttgart.de/FettKuestersSchmitz-CCS-2016.pdf), ACM CCS 2016.
- [The Web SSO Standard OpenID Connect: In-Depth Formal Security Analysis and Security
  Guidelines](https://publ.sec.uni-stuttgart.de/fettkuestersschmitz-csf-2017.pdf), IEEE CSF 2017.

The BFF preference follows the active [IETF OAuth browser-based applications working-group
draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-browser-based-apps/), which gives BFF the
strongest token-theft properties and strongly recommends it for sensitive and business
applications, plus ASP.NET Core guidance favoring confidential authorization-code clients with PKCE.
The IETF browser document is explicitly a working-group draft, not a final RFC.

Not every value is a scientific or normative constant. Five-second outcome handling, three-second
discovery, ten-second remote authentication, 30-minute idle and eight-hour absolute sessions,
local ports, locales, personas, and the initial CSP are risk-based operational or scaffold defaults.
Their rationale, override triggers, and required evidence are explicit in the evidence register.

The assurance claim is therefore limited: the profile reduces enumerated threats under documented
assumptions and verification obligations. It does not certify a consuming application, prove the
absence of vulnerabilities, or replace application threat modelling, deployment review, dependency
review, conformance testing, penetration testing, or incident response.

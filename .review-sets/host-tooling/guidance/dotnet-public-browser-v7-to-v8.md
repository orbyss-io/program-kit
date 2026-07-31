# .NET shell public-browser security v7 to v8

This source-guidance migration extends the provider-neutral transport-security
composition with a distinct public-browser OIDC authorization-code-with-PKCE
profile. It does not turn the ASP.NET Core API host into a browser client and it
does not make browser-held tokens the preferred architecture.

For each v7 host:

1. Keep `security: null` unchanged when transport security is disabled.
2. Add `oidcPublicBrowser: null` to an enabled security composition unless a
   reviewed browser application and explicit human threat-model acceptance
   exist.
3. When enabled, select the exact registered Blazor WebAssembly OIDC adapter.
   Require authorization code with PKCE, state, nonce, HTTPS metadata and exact
   login/logout callback URIs. Never add a client secret.
4. Declare the browser origin, API resource, CORS policy, API scope, session-only
   token storage, logout, and the initial adapter's absence of refresh tokens.
   Keep `offline_access`, implicit flow, and resource-owner-password flow absent.
5. Keep the API's JWT resource-server profile distinct. A browser ID token never
   becomes an API access token.
6. Record explicit human acceptance that tokens are held by the browser and
   retain a confidential server-side/BFF architecture as the preference for
   sensitive applications.
7. Bind the exact Playwright for .NET verification profile for Chromium,
   Firefox, and WebKit. Automated local execution remains separately
   human-started; real-provider interaction remains opt-in and operator-assisted.
8. Persist no credentials, tokens, cookies, Playwright authentication state, or
   traces. Retained acceptance evidence is redacted, non-authoritative, and
   separate from deterministic generation evidence.

The migration does not provision an identity provider. The disposable
Aspire/Keycloak substitution fixture is introduced by its later approved work
unit. Device authorization, CIBA, FAPI, DPoP, generic JavaScript generation, and
automation that bypasses provider-controlled human interaction remain absent.

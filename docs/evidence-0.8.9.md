# Program Kit 0.8.9 correction evidence

The 0.8.8 `spa-pkce-v1` templates were compared with the accepted secure-web profile and the first
governed PriceCalculator feature-planning stop. The following root causes were confirmed:

- the common static Keycloak fixture predated the exact-redirect contract and retained `/*` entries;
- a common application Compose file injected the BFF development secret for both web profiles;
- host session options were reused in the SPA scaffold although only the BFF ticket store consumed
  them, while the browser/provider enforcement handoff remained prose;
- the common Playwright default retained failure traces despite authentication-artifact secrecy;
- tooling-stage instructions invited sequential tests to reuse canonical `WEB-Cxx` identifiers;
- the OpenAPI pipeline required a consumer comparator pin while the architecture process still
  described that comparator as a candidate and supplied no empty-registry initializer.

The correction introduces a validated scaffold-owned SPA input and derives managed provider, host,
and browser artifacts from it. The fixture uses exact redirects, a public secret-free client, and
synchronized Keycloak SSO/client-session idle and maximum bounds. The browser adapter evaluates
trusted `auth_time` and `exp`, retains the original absolute deadline across renewal, clears local
state before provider logout, and coordinates sign-out across tabs without sending credentials.

Deterministic checks cover default and customized generation, wildcard rejection before writes,
sync convergence, client-secret exclusion, evidence-capture defaults, profile/control registry
integrity, OpenAPI initialization, exact oasdiff resolution, and the producer-first pipeline. The
official oasdiff 1.30.0 release substantially changed compatibility severities shortly before this
release; Program Kit therefore retains the already reviewed 1.29.1 behavior as its managed pin and
will evaluate 1.30.0 as a separate compatibility change.

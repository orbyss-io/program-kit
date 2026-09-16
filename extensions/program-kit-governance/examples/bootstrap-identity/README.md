# Published BFF and local Keycloak compatibility fixture

The maintained `bff-keycloak` recipe binds this fixture, the shipped BFF settings,
realm, client, theme and browser dependencies to a bootstrap compatibility receipt.
The shared coordinator owns renew and locked restore. The fixture packs only a
synthetic feature and runs the published Foundation image and pinned local Keycloak
image; it never builds a host image or implements consumer behavior.

The three named cases require actual provider discovery, published BFF activation,
and Chromium code-flow/permission/antiforgery/local-logout assertions. Anonymous,
authorized and wrong-role requests have distinct expected outcomes. Browser storage
must remain empty. The local HTTP session must use the publisher's separate local
cookie name, HttpOnly and SameSite=Lax. This is explicitly not a production HTTPS,
full security-assurance, consumer membership or application-acceptance test.

The 2026-09-16 actual rehearsal exposed an upstream Foundation 0.2.0 blocker:
configuration binding appends configured scopes to the initialized `Scopes` array,
retaining `orbyss-foundation-api` even when the selected profile configures only
`program-kit-api`. Keycloak rejects that unregistered scope. Preserve this failure;
do not register an unwanted scope or change fixture expectations to manufacture a
passing receipt. A corrected publisher package and reviewed pin/fixture update are
required before this exact profile can claim successful interoperability.

Source authority: Foundation v0.2.0 at
`3a97b158bd020391a0954e2148acc001eb8f2a17`:
`FoundationBffCookieFeature` owns `/api` 401/403 behavior, local cookie semantics,
OIDC and logout; `AntiforgeryMiddleware` owns unsafe API/logout CSRF rejection;
`AssuranceOptionsValidator` requires an effective named policy. The synthetic
freshness policy establishes activation only. Shipped realm users are explicitly
non-production fixtures. Keycloak uses the exact image in the installed managed
identity template. Runtime receipts, not this README, establish executed evidence.

Resources use unique names and loopback listeners and are removed in `finally`.
The read-only feed has a pre-created extraction mountpoint for writable tmpfs.
Bounded failures reach the coordinator's preserved, sanitized streams before
scratch removal, including container diagnostics. Provision the exact images and
Chromium first; a missing runtime cannot be treated as a passing compatibility case.

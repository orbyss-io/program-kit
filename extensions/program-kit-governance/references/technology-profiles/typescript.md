# TypeScript and web profile

<!-- program-kit:knowledge-rule principle.frontend-profile-authority -->
Adopt the independent `ui-experience-v1` profile for browser UI: consumer-owned branding and optional
SVG logos, Lucide/custom icons, responsive archetypes, semantic tokens, safe initial-response
metadata, page-level discovery intent, and opt-in analytics. Read `../ui-experience-v1.md` and its
evidence register. Native CSS is the default adapter; accepted frontend/framework decisions remain
authoritative. The isolated UI acceptance graph must not change the application's own npm graph.
<!-- /program-kit:knowledge-rule -->

## Admission and verification

<!-- program-kit:knowledge-rule context.typescript-profile-applicability -->
When TypeScript or a browser UI is detected, evaluate and normally enforce:
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:decision-rule typescript-admission -->
<!-- program-kit:knowledge-rule principle.typescript-strictness -->
- strict TypeScript mode and no implicit unsafe boundary casts;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-tools -->
- linting and formatting with pinned, non-conflicting tools;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-runtime-admission -->
- explicit runtime validation for untrusted API, storage, URL, and message data;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-contracts -->
- generated or checked API/schema contracts rather than duplicated handwritten shapes;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-accessibility -->
- accessible UI semantics and automated checks supplemented by human testing;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-test-boundaries -->
- component tests for behavior, integration tests for boundaries, and a small number of high-value end-to-end journeys;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-supply-chain -->
- dependency, lockfile, license, secret, and supply-chain checks;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-budgets -->
- bundle-size and performance budgets appropriate to the product;
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.typescript-client-security -->
- safe rendering, CSP, CSRF/session/token treatment, and secret-free client configuration.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->

<!-- program-kit:knowledge-rule principle.typescript-selected-auth-contract -->
For an authenticated browser UI, adopt the versioned secure web profile selected by the bootstrap.
The default is a same-origin BFF even when the UI is a React or other single-page application. The
browser calls `/bff/user`, obtains an in-memory antiforgery token from `/bff/antiforgery`, and sends
same-origin requests; it does not implement OIDC or persist bearer tokens. Direct SPA PKCE/bearer
authentication is an explicit deployment-profile choice, not a frontend-framework default.

Adopt explicit intake choices and applicable versioned Program Kit defaults in the reviewed bootstrap
baseline. Choices not supplied by either source remain Proposed until accepted in the project context;
do not invent a framework merely to make the register look complete.
<!-- /program-kit:knowledge-rule -->

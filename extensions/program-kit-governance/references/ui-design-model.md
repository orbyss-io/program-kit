# UI design model

## Layers and choices

Start from the person's journey and context of use. Use this model to explain what the profile
knows, what a choice changes, and where to override it. It is a coverage lens, not a questionnaire.

| Layer | Meaning | Current owner / configuration |
| --- | --- | --- |
| Product experience | Actors, outcome, information, decisions and recovery | Confirmed intent and affected specification; consumer rules |
| Global layout | Header, navigation, account area and canvas across the app | Profile archetype/navigation; accepted frontend shell |
| Page layout | List/detail, form, workspace, overview or readable content | Optional content page layout, generated pattern fragments, consumer feature composition |
| Branding | Name, logo, typography, palette and visual character | Profile brand; consumer-owned assets and rights |
| Theme | Light/dark, surface hierarchy, density and semantic roles | Scheme/density, brand color overrides, generated tokens |
| Components | Controls, states, semantics and keyboard/focus behavior | Versioned presentation; consumer component adapter |
| Feedback and recovery | Field, operation and page state; useful next action | ui-feedback-and-recovery.md; domain/transport outcomes mapped by consumer adapter |
| Motion | Feedback, entrance, exit and occasional emphasis | Motion style, semantic duration/easing tokens, user preference |
| Icons | Family, weight, size, labels and directional behavior | Brand icons; sanitized used subset and notices |
| Implementation | Frontend, component library and CSS integration | Existing accepted frontend; native/tailwind/existing-system CSS adapter |
| Authentication experience | Login, errors, success, expiry and logout states | Shared brand/theme; provider or application screen owner |

Brand and theme are related but distinct: the same identity must work in light and dark themes.
Global navigation and a page's composition are distinct; a list/detail page need not create a new
global navigation destination. Density follows the work and input needs, not visual taste alone.
Patterns do not add features, fields, routes, providers or operations to the product.

Material Design is a design system. Tailwind supplies styling utilities/theme integration rather
than a complete product behavior library. Bootstrap supplies styling, layout and interactive
components. React/Vue/etc are frontend implementation choices. These options can constrain each
other; do not combine competing resets, component semantics or token owners blindly. Program Kit
ships a native reference, a tested Tailwind token bridge and an explicit existing-system mapping.
It does not ship qualified Material or Bootstrap adapters merely because their guidance is known.

## Modern product baseline

New profiles select `presentation: modern-product-v1`. Omitted presentation means `classic-v1`;
init never overwrites a consumer profile. Upgrade intentionally by editing the presentation input,
reviewing the changed generated appearance and adapter fit, and using normal build/check ownership.
The experience profile remains `ui-experience-v1`; presentation is a separate versioned choice.

Use coherent typography/spacing, layered surfaces, restrained decorative separators, distinct
action styles, useful information hierarchy and responsive compositions. Essential control/focus
indicators retain contrast independently of decorative dividers. Keep touch targets usable and
keyboard/focus meaning stable. Compact workspace density is legitimate when the actual work fits.
Choose navigation from destinations and page composition from the journey; a sidebar is a fallback
proposal, not evidence that every small application needs one.

Motion is enabled normally. Productive feedback, entry and exit have separate roles; expressive
moments need a purpose. Honor reduced-motion preferences with equivalent static feedback. Do not
make completion, focus restoration or the next action depend on an animation finishing. Prefer
transform/opacity for movement; measure other animated properties when consequential.

Generated list/detail and form fragments are composition starters. The consumer owns actual
selection, responsive back navigation, retained state, rules and operation adapters. A component
gallery is not a working product journey. Review a representative real composition with the human
at the existing review handoff; contrast/axe passing does not establish visual quality or usability.

## Authentication presentation

Accepted identity-screen styling describes the person's complete sign-in/recovery journey,
including provider-hosted screens when they are in that journey. Trace the requirement from
project intent/intake and bootstrap decisions into the affected spec, plan, tasks and acceptance.
Use the consumer UI profile as configured brand inputs; a starter default is not proof of human
intent. Do not narrow the agreed outcome because the spec omits the implementation name "custom
Keycloak theme". Resolve actual ambiguity against existing authority; preserve an explicit
provider-styling exclusion or assign an explicitly deferred requirement to its owning slice.

For selected Keycloak, realize scoped login, password-reset/account-recovery, errors and enabled
MFA/required-action styling through the consumer-owned login theme. Merge generated brand CSS/logo
into the existing theme, retain its observed parent and base styles, and verify the active realm
`loginTheme` plus any client override. Include theme packaging/mounting, the selected provider
version and actual provider browser/keyboard/recovery tests in the same affected plan/tasks.
The shipped `keycloak.v2` parent uses `css/styles.css`; the classic `keycloak` parent uses
`css/login.css`. Append brand CSS after the matching parent stylesheet. Generated integration
assets and a configured realm alone do not establish that the live screens use the chosen theme.
See [Keycloak theme customization](https://www.keycloak.org/ui-customization/themes).

Generated `integration/auth/` supplies branded layout templates for login, login-error,
login-success, session-expired, logout-confirmation, logout-progress, logout-success and logout-error.
They are inert presentation templates with explicit control slots, not deployed routes or claims
that authentication occurred. Bind localized copy, verified state and provider/application-owned
controls. Never add a mandatory login-success interstitial when the established flow continues
directly into the application; use the same branded completion treatment in that flow.

Preserve provider-owned credential forms, MFA, required actions and provider error/recovery flows.
The Keycloak login theme scaffold inherits the provider templates and appends generated brand CSS;
it does not replace forms or change redirects. Integrate its logo and realm display name from the
accepted brand. Existing themes/providers retain authority; validate their actual DOM/version.
Styling covers login/error/info and logout confirmation through shared provider layout selectors.

Application callback success/error and expired-session recovery belong to the accepted frontend.
Logout confirmation explains unsaved work and the selected sign-out scope. Local logout completes
before provider logout where the secure profile requires it. Provider failure must not restore a
local session. `logout-error` requires local session termination with provider termination
unconfirmed; other failures need their own honest state. `logout-success` requires proof of the
selected scope, not a received redirect alone. Preserve registered return targets, OIDC validation
and antiforgery-protected logout. Templates never handle credentials or tokens.

Run actual provider login success/error, required actions where selected, callback error, logout
confirmation/cancellation/success and unavailable-provider logout acceptance before declaring the
consumer flow complete. Screen fixtures prove presentation only. Do not start a provider during
intake or expand paid/live acceptance to verify these templates.

## Inspecting and changing

Run `ui_profile.py explain --target .` to inspect choices, input/override paths, adapter coverage
and phase obligations without writes. The view and generated design map derive from the current
profile/content. Matching a starter default does not establish user preference: actual provenance
remains in existing intent/bootstrap decisions. Do not create another decision registry.

Change sources or the consumer CSS layer, then build/check. Research only the selected design,
component or provider integration. UI work does not require reading public discovery, analytics or
every framework's documentation. Verified source categories and limits live in ui-evidence-v1.json.

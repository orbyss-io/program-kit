# Consumer UI prototyping

Turn the consumer's product understanding into an experience they can explore and shape. Build
pages, navigation, layouts, branding and suitable components with fictional data and local state.
Ordinary frontend authoring is sufficient; no backend, UI schema, generated journey engine or
additional intake ceremony is required. Use this for an explicitly requested prototype or design
exploration, including a workspace that has already completed intake.

## Understand and compose

Read the relevant intent, actors, journeys, roadmap, architecture and existing design assets.
Reuse settled answers and prior prototypes. Accept readable documents and local representations;
neither architecture JSON nor a feature specification is mandatory. Architecture explains meaning
and boundaries; it does not dictate one page per entity, service, endpoint or roadmap item.

Derive a useful page structure and navigation from the person's work: where they enter, what they
need to see, what they can do and where they go next. Cover the requested journeys across pages,
shared layouts, menus, dialogs and specialized workspaces. Several journeys may share a page.
For a broad product preview, show the known breadth with lightweight pages and deepen selected
interactions; identify unfinished or deferred areas rather than claiming exhaustive coverage.

Propose reasonable visual details and fictional examples to keep design moving. Label assumptions
and ask only when a consequential missing answer changes the requested experience. Previewing
does not require restarting intake, ratifying documents or settling future backend decisions.
Preserve actual product scope; do not silently turn an illustrative control into a new requirement.

## Choose tools and components

Use [component research](ui-component-research.md) when choosing or comparing a framework,
component provider or specialized control. Research is part of prototyping, not a separate mandatory
phase. Existing accepted choices and usable components are the starting point; investigate gaps
and requested alternatives. Match graphs, diagrams, calendars, editors, maps, tables and other
controls to the actual work rather than forcing every product into one starter gallery.

Use the relevant layers of [the UI design model](ui-design-model.md). Reuse existing brand assets,
tokens and `.program-kit/ui/profile.json` where present. Keep exploratory variants in the prototype;
do not overwrite accepted shared inputs until the user selects that change. A prototype may use
plain HTML/CSS/JavaScript or a suitable frontend framework. Disclose a different prototype stack
as an exploration choice, with any handoff implications, rather than silently adopting it for
production. No particular framework, component provider or fixed layout is universally required.

## Build and explore

Keep editable prototype source in an isolated consumer directory such as `prototypes/<name>/`,
following existing repository conventions. Preserve prior variants and user edits. Keep authored
source outside `web/generated/program-kit`; that generator's public projection deliberately omits
private application pages. Render private-app designs locally with fictional data rather than
reclassifying private pages as public to make them appear. Do not copy private datasets or secrets.

Build connected pages with representative content, coherent navigation and a responsive shared
visual language. Make visible controls useful: navigate, open, select, filter, edit sample data,
change local state or clearly explain an intentionally unfinished action. Include specialized
components in their actual page context. Support keyboard/focus and meaningful narrow-screen
layouts; use relevant feedback guidance for the interactions being explored. Simulate only the
states that help review this design, without prescribing server contracts or building services.

Identify the experience as a prototype with fictional data. Keep interactions local and independent
of real authentication, persistence, accounts, providers and business effects. A role switch or
sign-in screen can simulate the journey; it does not authenticate or enforce authorization. Use
local assets/dependencies where practical and make any essential network dependency explicit.

Use available project tools to build and open the preview locally. Verify the actual page links,
representative interactions, layout and browser console where supported. Preview on wide and
narrow viewports and inspect the result visually; a successful build alone proves no visual quality.
If browser tooling is unavailable, report that limit and provide useful launch instructions.
Use existing installed runtimes; ordinary project dependency restore is allowed, device/global
toolchain installation remains human-owned. Keep preview hosting local; sharing needs its own scope.

## Refine and retain

Work conversationally from the runnable preview. Apply requests about page structure, component
choice, custom layout, branding, theme, density and wording while preserving unrelated decisions.
Show alternatives when they resolve a real choice, and preserve a useful comparison when requested.
Do not demand approval for each page or turn design iteration into a lifecycle gate.

Keep the prototype, assets and a short readable design note together. Explain how to open it,
which journeys/pages are represented, component choices and research links, important assumptions,
what is simulated, and remaining gaps. Record actual user decisions and their scope; visual approval
does not establish implementation acceptance. The code may be disposable, but retain the chosen
design and customizations as references for later ordinary specifications and implementation.

When the user chooses a design, link the chosen prototype and design note from existing product
intent or the relevant feature document so another session can find them. Use the conversation to
explain what was agreed and why, what is illustrative and what remains exploratory. For example,
the split workspace, inline editing and branding may be chosen while sample records and a mobile
layout remain illustrative. Preserve the chosen version through ordinary source history or a
retained variant as appropriate; do not let a later experiment silently replace the reviewed design.
No per-control confirmation, approval receipt or new design registry is needed.

Specification and planning reuse the relevant design rather than starting UI design over. Consult
the actual pages/source and the note, keeping observable experience in the spec and production
component/framework choices in the plan. Reuse suitable assets, tokens and components; prototype
code still needs production engineering review. Visual agreement does not silently adopt mock
rules, dependencies or integrations. Missing detail can be designed consistently without reopening
settled choices; missing prototype files do not block independent work on known requirements.

Use the existing [engineering feedback method](engineering-feedback.md) when a later decision
affects the agreed experience. Raise the affected choice, explain its effect and show a focused
preview where useful; preserve unrelated design and record the actual decision in the owning
documents. At the existing runnable story review, compare the implemented journey, layout,
branding and interactions with the agreed reference. Automated checks support this review rather
than establishing human design acceptance. After delivery, the implemented UI and current accepted
decisions guide further work; retain prototypes for rationale and new exploration without maintaining
a second synchronized application. An older prototype does not override later accepted changes.

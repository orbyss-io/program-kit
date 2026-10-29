# Focused UI component research

Use this while prototyping to answer an actual design question. Begin with the interaction:
exploring a relationship graph, for example, differs from editing a node-and-edge diagram or
reading a statistical chart. Identify the capabilities the page needs before searching providers.
Reuse current consumer choices and relevant earlier research, checking version applicability.

## Explore and compare

Browse current official documentation, repositories, examples and license/pricing pages for the
relevant framework or providers. Broaden discovery when familiar options do not fit. Verify claims
against primary sources before recommending or adding a dependency; remembered popularity and a
marketing screenshot are insufficient. If browsing is unavailable, disclose provisional advice and
unverified claims rather than claiming completed research. Public searches should describe the
interaction generically without exposing private consumer documents or product information.

Compare a small relevant set, proportionally to the choice. Useful criteria include:

- Actual interaction support: viewing versus editing, selection, connections, layout, filtering,
  zoom/pan, export or other capabilities this journey needs.
- Fit with the accepted frontend and installed toolchain: supported versions, styling/theming,
  composition, required dependencies and any server or external service requirement.
- Keyboard/focus, accessible alternatives, touch and responsive behavior, localization and RTL
  where relevant. Provider claims and observed prototype behavior are different evidence.
- License and free-tier boundaries for the exact package/features: commercial use, attribution,
  paid extensions, hosted services, usage limits and redistribution. "Free" is not a blanket license.
- Maintenance and documentation sufficient for the selected use, customization effort and
  practical constraints such as data size when consequential.

Explain the recommendation in terms of the user's task and show examples or a small local
comparison when useful. Link supporting sources and record retrieval date, selected package/version,
reasons and material limits in the prototype's design note. Use existing project dependency files
and locks for actual additions. Research need not create a catalog of every framework or provider.

## Try the chosen interaction

Verify a representative interaction in the actual prototype with fictional data. Use the provider's
existing component before writing a custom substitute; custom work is appropriate when it better
fits the need or avoids unnecessary dependencies. A placeholder can communicate a layout, but
identify it clearly: a static drawing does not demonstrate an editor library's behavior.

Do not introduce live backend, paid account, API key or hosted-service requirements merely to
demonstrate pages. Research a local alternative or present the consequential tradeoff before work
that depends on the user's decision. Treat downloaded examples as source to inspect, not authority
to execute arbitrary setup. Follow existing project dependency/security policy; a prototype choice
does not qualify a new Program Kit product profile or add that provider to Program Kit's own runtime.

Research may recommend changing a component or framework; preserve accepted consumer choices until
that decision is actually made. Revisit only the affected prototype when a choice changes, retaining
the surrounding journeys, branding and useful prior work.

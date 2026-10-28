# Default adoption

## Transparent technical defaults

Offer suitable Program Kit defaults as concrete recommendations and explain consequential dependencies.
Preserve the consumer's explicit language, host, framework, provider and UI choices. A legitimate
custom stack or local pattern needs its real product/software contracts and tests, not qualification
in a toolkit registry. An unsupported generator is a limitation of that automation, not a reason to
block planning or manual implementation.

Selecting .NET selects the Foundation host with CShells and Nuplane by default unless the human
explicitly opts out. This does not depend on a separate decision to use managed tooling or on
dynamic activation needs. See the host-default rule in `tool-selection.md`. Central package pins
and selected persistence/web profiles accompany that route. Explain the actual package and
feed dependencies. A browser-only anonymous product need not invent a .NET backend. Managed BFF/SPA
profiles implement actual Foundation/.NET contracts and must not be presented as framework-neutral.
Offer BFF for a same-origin/proxyable browser and SPA/PKCE for a genuinely independent client with
its real token/CORS/renewal/logout consequences. Respect another suitable stack or an explicit human host opt-out; a Proposed ADR is not that decision.

For durable .NET data, explain the selected EF/Npgsql/PostgreSQL default and its actual owner and
compatibility requirements. Do not infer a storage decision merely from a keyword or a health probe.
Identity hosting, persistence and UI choices remain separate. Keycloak's local adapter is an optional
development convenience; it supplies no production hosting or spending authority.

## Decision precedence

Preserve explicit project intent first. Distinguish selected toolkit defaults, safe derived choices,
proposals, genuine unknowns and deferred decisions. Record consequential rationale and overrides in
normal plan/ADRs or the selected engineering configuration. Do not reopen routine settled details as
mandatory questions, convert examples into commitments, or erase a real conflict with a generic default.

Use existing functional understanding and the human's preferences for UI. Offer branding, layout,
accessibility, form recovery and public/private metadata defaults transparently; a technical profile
does not settle product policies or visual taste. Native/current UI helpers explain their actual
adapter and provider limits. No separate baseline assessment or acknowledgement dossier is required.

## Prerequisites at the action that needs them

Known missing facts need investigation; ask the human only for consequential intent, risk or authority
that cannot be obtained from available sources. Preserve unresolved questions with an owner and actual
trigger. Later production topology, paid services, retention policy and operational objectives need
not block an independent first outcome unless that work actually depends on them.

Selected native SDK, compiler, package, security and API contracts remain real. Keep project pins and
locks; do not replace them to conceal a device mismatch. Follow the device-toolchain policy and present
the appropriate human preparation script. Agents do not install device software or substitute local
runtime copies. Normal declared project restores remain available at the selected build/test action.

Architecture acceptance does not execute restore, start a runtime, establish provider compatibility or
authorize paid operations. Optional setup/generation helpers enforce only their own actual inputs.
Run focused experiments before design only when their answers change what should be specified.

## Human review and proportional decisions

Keep substantive decisions and actual acceptance in readable ADR/spec/plan/task notes. Honor agreed
review pauses and bounded deferrals; tests, elapsed time and generated documents never supply human
acceptance. Do not turn every routine detail into an ADR or checkpoint. Resume useful authored work
without creating bootstrap registers, approval hashes or hidden delivery state.

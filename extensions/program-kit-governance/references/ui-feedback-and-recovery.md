# UI feedback and recovery

## State and ownership

Treat feedback as an end-to-end contract: domain/transport outcome -> user meaning -> presentation
-> safe next action. Loading, empty content, invalid input and failed retrieval are separate states.
Do not show an empty collection while a request is pending or failed. Preserve useful content during
refresh where safe, indicating stale data or refresh failure honestly. Scope a failure to the
affected component/operation unless the entire page is unusable. Do not hide material errors in an
ephemeral toast or replace the entire application for one failed request.

| State | Presentation and recovery |
| --- | --- |
| Initial loading | Stable structure, relevant skeleton/progress, text describing the pending work |
| Background refresh | Retain usable content where safe; distinguish refresh, stale state and failure |
| Empty | Explain absent content and an actually available next action |
| Field invalid | Identify the field and correction; retain values and guidance |
| Submission rejected | Inline errors and a linked summary when useful; preserve passing and failing input |
| Conflict/business rejection | Explain the rule or changed state and permitted resolution |
| Service/network failure | Explain interrupted work; preserve recoverable draft and offer safe recovery |
| Outcome unknown | Do not assert failure/rollback; reconcile status or safely replay the same operation |
| Unexpected app failure | Usable fallback, safe reference for support, no raw internal diagnostics |
| Success | Confirm the established outcome and appropriate next action |

<!-- program-kit:decision-rule ui-outcome-ownership -->
Only applicable states belong in the affected feature. No separate state dossier or per-task gate
is required. Draft retention follows privacy/security and lifetime rules; do not automatically put
private drafts or tokens in persistent browser storage. Cancellation does not prove server rollback.
Unknown completion requires reconciliation or safe replay; failed retrieval is never an empty result.
Generated UI callbacks do not establish backend idempotency or actual provider login/logout behavior.
For sign-in or recovery journeys, carry accepted styling/accessibility intent across application
and provider-owned screens. When Keycloak owns a screen, implement that intent through its login
theme, inherited templates and active realm/client theme binding. An omitted implementation term
such as "custom Keycloak theme" does not exclude an already agreed user-visible outcome. Reconcile
existing intake, bootstrap decisions and UI inputs before narrowing scope; explicit exclusions
or deferrals need their established authority and a concrete owning slice. Keep application
callbacks/session recovery with the frontend and preserve provider credential/MFA/required-action flows.
<!-- /program-kit:decision-rule -->

## Complete fields and forms

A field component supports label, optional persistent hint, input, error slot and state styling.
Supply concise hints when format, restrictions or consequences need explaining before submission;
do not pad self-explanatory fields with redundant text. Placeholders do not replace labels/hints.
Associate hints/errors through aria-describedby, mark established invalid fields with aria-invalid,
and use text plus visible invalid styling rather than color alone. Preserve focus indication in
normal and invalid states. Do not remove the hint when adding an error that still needs it.

Default to submission validation initially and helpful correction after reported errors. Earlier
validation needs a reason (such as meaningful character-limit feedback); do not mark unfinished
answers wrong on every keystroke. Server admission remains authoritative. Client and server rules
must agree; do not duplicate independently invented business policies in a UI helper.
When managed Orbyss Forms is selected, retain its schema/compiler/runtime admission and accepted
frontend components. Apply these presentation states through that adapter; do not add a competing
validation engine merely to reproduce the native reference pattern.

Use concise, actionable messages tied to field labels. An error summary links to affected fields
and uses the same messages; focus the summary or the affected field according to composition.
Coordinate focus and announcements so each error is not repeatedly announced. Dynamic ordinary
status uses polite feedback; reserve assertive interruption for urgent context. Keep values when
submission fails. Permission/service problems are not automatically invalid field values.

Generated `integration/patterns/form.html` and interactions.mjs supply the field/error/status
presentation and `setFieldError`, `presentFormErrors`, `setOperationState`, `bindOperation` helpers.
The latter accepts localized pending/unknown messages and a consumer-owned callback returning success, validation (errors keyed by owned
field name), failure, conflict or unknown, with admitted localized message text. A thrown/malformed
outcome becomes unknown; the helper does not retry, clear input, infer HTTP semantics or persist
drafts. It prevents duplicate local submission while pending; backend idempotency remains required
where promised. On disposal it ignores late callbacks. Other frameworks can implement equivalent
behavior through their accepted component model; do not replace them to use the reference helpers.

## Progress, errors and recovery

Choose skeletons when structure is known, inline progress for local actions, and measurable progress
when actual measurements exist. Avoid fake percentages, forced waiting and indefinite spinners
after a terminal failure. Give long-running work a defined deadline/recovery route; cancellation
controls are offered only when supported. Equivalent static feedback remains with reduced motion.

Map stable problem types/codes to presentation and permitted recovery using the existing API
contract. Field paths and user messages need a defined mapping. Unknown errors use a safe fallback;
raw exception text, SQL/provider details, tokens or personal data never become public copy. Safe
trace references may support diagnosis. Problem Details does not by itself specify UI behavior.

After response loss, distinguish proven rejection from uncertain completion. A retry requires an
idempotent operation, a same-operation replay guarantee or proof that the operation was not applied.
Do not generate a new operation identity on every retry or claim a client-side disabled button proves
one backend effect. Concurrency rejection preserves the draft and offers the agreed review/merge/
reapply behavior; never silently overwrite newer state. Authentication/expiry/logout follow the
screen ownership and state rules in ui-design-model.md and the selected secure-web profile.

## Phase and acceptance

Intake resolves consequential user meaning, conflict and recovery needs. Feature planning records
applicable field rules, state/outcome mapping and recovery in existing artifacts. Implement complete
fields and states with the first working journey. Run focused changed behavior tests during TDD,
affected browser/client tests after related changes, and feature acceptance at closure or handoff.
Reuse the existing browser-experience obligation; add no hook, questionnaire or full suite checkpoint.

Exercise empty/pending/failure distinctions, rejected submissions, hint/error associations, visible
invalid styling, linked summary/focus, preserved passing and failing values, corrected success,
duplicate local submits, actual backend error mapping, conflict, uncertain completion and stale
callbacks where applicable. Use controlled adapter responses for UI transitions and existing real
operation tests for backend guarantees. Template fixtures and screenshots do not prove actual
provider/consumer outcomes. Human visual/assistive review stays in the existing acceptance handoff.

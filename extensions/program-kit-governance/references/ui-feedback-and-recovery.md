# UI feedback and recovery

## State and ownership

<!-- program-kit:knowledge-rule principle.ui-feedback-state-contract -->
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
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:decision-rule ui-outcome-ownership -->
<!-- program-kit:knowledge-rule principle.ui-state-recovery -->
Apply only relevant feature states in existing artifacts; no separate dossier or per-task gate.
Retain drafts under privacy/security and lifetime policy; never persist private drafts or tokens by
default. Cancellation proves no rollback. Reconcile unknown completion or safely replay; failed
retrieval is not empty. UI callbacks prove neither backend idempotency nor actual provider login/logout.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.provider-owned-journey -->
For sign-in or recovery journeys, carry accepted styling/accessibility intent across application
and provider-owned screens. When Keycloak owns a screen, implement that intent through its login
theme, inherited templates and active realm/client theme binding. An omitted implementation term
such as "custom Keycloak theme" does not exclude an already agreed user-visible outcome. Reconcile
existing intake, bootstrap decisions and UI inputs before narrowing scope; explicit exclusions
or deferrals need their established authority and a concrete owning slice. Keep application
callbacks/session recovery with the frontend and preserve provider credential/MFA/required-action flows.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->

<!-- program-kit:knowledge-rule principle.browser-autosave -->
When autosave is selected, follow the [native autosave recipe](../../program-kit-dotnet/references/examples/browser-autosave/README.md)
against the exact public profile. Share manual/automatic coordination, preserve parent order and
original attempts, and observe drain separately from save outcome. Adapters own authorization,
receipt admission and recovery. Autosave never implies session renewal or durable browser storage.
<!-- /program-kit:knowledge-rule -->

## Complete fields and forms

<!-- program-kit:knowledge-rule principle.complete-form-contract -->
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
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.form-adapter-contract -->
Generated `integration/patterns/form.html` and interactions.mjs supply the field/error/status
presentation and `setFieldError`, `presentFormErrors`, `setOperationState`, `bindOperation` helpers.
The latter accepts localized pending/unknown messages and a consumer-owned callback returning success, validation (errors keyed by owned
field name), failure, conflict or unknown, with admitted localized message text. A thrown/malformed
outcome becomes unknown; the helper does not retry, clear input, infer HTTP semantics or persist
drafts. It prevents duplicate local submission while pending; backend idempotency remains required
where promised. On disposal it ignores late callbacks. Other frameworks can implement equivalent
behavior through their accepted component model; do not replace them to use the reference helpers.
<!-- /program-kit:knowledge-rule -->

## Progress, errors and recovery

<!-- program-kit:knowledge-rule principle.progress-error-recovery -->
Use skeletons for known structure, inline progress for local actions, and percentages only from
actual measurements. Avoid fake percentages, forced waiting and spinners after terminal failure.
Bound long work with a deadline/recovery route; offer cancellation only when supported. Preserve
equivalent feedback with reduced motion.

Map existing stable problem types/codes to presentation, field paths/messages and permitted recovery.
Unknown errors need a safe fallback. Never expose raw exceptions, SQL/provider details, tokens or
personal data; safe trace references may aid diagnosis. Problem Details alone specifies no UI behavior.

After response loss, distinguish proven rejection from uncertain completion. Retry only when
idempotent, identically replayable or proven not applied; retain the original operation identity.
A disabled button proves no single backend effect. Conflict preserves the draft and agreed review,
merge or reapply choice; never silently overwrite newer state. Authentication, expiry and logout
follow ui-design-model.md and the selected secure-web profile.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.operation-recovery-outcomes -->
| Established outcome | Retained state | Permitted recovery |
| --- | --- | --- |
| Server confirms validation rejected without effect | Keep editable values/focus; clear only rejected action | Correct input; explicitly prepare new action |
| Server confirms admission expired before acceptance | Keep values; restore editing; hide this expired action's reconciliation | Explicitly prepare new action |
| Accepted action with lost response, timeout or uncertain commit | Keep original contract-bound identity and values | Reauthorize lookup or supported identical replay; no blind new dispatch |
| Receipt absent or status unknown | Keep identity and unknown completion | Reconcile by server contract; absence proves neither rejection nor rollback |
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.status-lookup-disclosure -->
Codes and documented acceptance semantics establish no effect; generic HTTP 400/409 alone
does not. Status lookup checks current owner/permission and performs no business effect.
Unknown/forbidden status and public errors disclose no private identities, provider data or
raw diagnostics. Selected Foundation closed problems carry safe standard fields; typed
operation responses and the UI own recovery choices.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule context.operation-recovery-focused-example -->
The maintained [operation recovery example](operation-recovery-example.mjs) illustrates these
semantic transitions. Its events require the consumer's reviewed server contract; it supplies
neither a competing wire schema nor authority to classify every HTTP 400/409 as no effect.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.ui-server-adverse-controls -->
Test correction editability for every affected field, retained values, focus, absence of
automatic preparation, and unknown completion identity retention. A simulated UI refusal
proves presentation only: separately exercise actual server invalid-input and owned fixture
expiry rejection, plus accepted-response loss and missing-receipt behavior. Mirror server
control-character rules including C0, DEL and C1 (`U+0000–001F`, `U+007F–009F`) when the
server uses that bounded rule; server validation remains authoritative.
<!-- /program-kit:knowledge-rule -->

## Phase and acceptance

<!-- program-kit:knowledge-rule principle.actual-ui-acceptance -->
Intake resolves consequential user meaning, conflict and recovery needs. Feature planning records
applicable field rules, state/outcome mapping and recovery in existing artifacts. Implement complete
fields and states with the first working journey. Run focused changed behavior tests selected by risk,
affected browser/client tests after related changes, and feature acceptance at closure or handoff.
Reuse the existing browser-experience obligation; add no hook, questionnaire or full suite checkpoint.

Exercise empty/pending/failure distinctions, rejected submissions, hint/error associations, visible
invalid styling, linked summary/focus, preserved passing and failing values, corrected success,
duplicate local submits, actual backend error mapping, conflict, uncertain completion and stale
callbacks where applicable. Use controlled adapter responses for UI transitions and existing real
operation tests for backend guarantees. Template fixtures and screenshots do not prove actual
provider/consumer outcomes. Present the actual runnable journey for human visual/assistive review at
its required story checkpoint after relevant technical checks. Earlier product checkpoints require
explicit agreement. Human review assesses usefulness, clarity and intended journey without repeating
the automated suite; required deferred reviews remain due at feature acceptance. See phase-evidence.md.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.server-draft-durability -->
When server draft durability is promised, use the generated acceptance/tests/durability.mjs
checkpoint in the real consumer browser journey. Confirm the exact server draft identity, version
and content before fixture-owned restart; a pending save or local input value is not acknowledgement.
After restart, establish authenticated server readiness before reading recovered data or inspecting
the UI. Distinguish readiness/HTTP timeouts from an exact recovered-data mismatch. Status diagnostics
contain only stage, attempt, HTTP status and outcome, never URLs, response bodies, drafts, accounts,
credentials or exception/source text. Keep server data and private configuration through restart.
Invoke the maintained browser entrypoint with `--cases=durability --durability-contract=<adapter.mjs>`;
selecting durability without its real-server contract fails rather than reporting fixture success.
The adapter exports `createContract({browser, engine})`, runs the actual authenticated save journey,
and returns the Playwright request context, `expectedDraft: {id, version, content}`, `draftPath`,
`authenticatedReadinessPath` (a real authenticated endpoint), fixture-owned `restart`,
`authenticate`, UI `inspect` and owned-fixture `close` functions. Optional `draftFromResponse` projects
the existing server response into that draft shape; it must retain exact identity/version/content.
Optional `isAuthenticatedResponse` tests the selected publisher's actual response shape; the default
checks `authenticated: true`. Both HTTP 200 and an affirmative authenticated response are required;
an unconditional predicate or a generic unauthenticated health endpoint cannot establish readiness.
Use the existing isolated consumer fixture and actual host lifecycle; the generated static gallery
and helper sequencing tests do not establish consumer durability or authentication acceptance.
<!-- /program-kit:knowledge-rule -->

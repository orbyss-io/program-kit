# Proposed N17: useful failure identity in private browser reports

Prepared 16 October 2026 for the consolidated collection queue. This is a distinct proposed diagnostics improvement, not an established Program Kit security defect. It does not change the active implementation ledger, approved plans or consumer source. The consumer continuation report records the issue as D45; D46 records the separate mistaken antiforgery-status assertion that the improved location exposed.

## Evidence and attribution

The consumer's private reporter intentionally suppressed error payloads, including their locations, so a failing connected case could not be located. Its local repair extracts a spec filename/line/column annotation before stripping error properties, then emits those annotations with authored case identity and outcome.

Read-only inspection confirms this code in the current consumer `web/tests/fixtures/session.ts` and `private-reporter.mjs`. The fixture searches an error stack for a spec-looking basename and numeric location; the reporter accepts annotations matching a corresponding filename/location regular expression. It emits JSON, case titles/statuses and an output-path console summary. The report attributes this to consumer diagnostics design, not a canonical Program Kit reporter. The current shipped Playwright configuration has no corresponding private reporter in the inspected template; trace the actual provenance before assigning an upstream generator defect.

The consumer reports that the location exposed a wrong test expectation: selected native missing-antiforgery handling returns 400, while the new assertion expected 403. It corrected that assertion and independently checked that the file remained AwaitingOriginal. This is a correct contract/guard disposition, not a request to change server status or weaken antiforgery. Actual native contract observation and passing cases are reported, not independently executed by this collection task.

## Critique and proposed shared handling

Preserving a bounded authored failure identity is appropriate. The current regex is a format check, not an independently authenticated inventory of authored files, and it searches text that can contain arbitrary exception data. A plausible-looking substring is not proof that the selected location points to a real stack frame in an allowed spec. Treat the local change as a useful bounded continuation remedy, not a complete reusable redaction contract.

Proposed Program Kit work is a private-test reporting recipe/example with explicit metadata ownership, plus focused central tests. Prefer an author-controlled case/spec identity and trusted runner location metadata, or validate any extracted frame against the actual allowed authored source inventory before output. Normalize to a permitted relative identity or opaque authored ID; retain only bounded positive integer locations and a bounded number of entries. Missing/unsupported location must stay explicit and must not fall back to emitting raw stack or error text.

Case titles, annotations and output paths also need a defined admission policy. A title dynamically derived from private input is not safe merely because test source authored its template. Do not retain arbitrary annotations, absolute machine paths, DOM, request/response payloads, credentials, screenshots or attachments under the label of safe failure location. Check the actual configured reporter/stdout/stderr/attachment boundary; editing one error object alone does not prove all output channels are clean.

The recipe should retain real failed/timed-out/skipped outcomes, actual case identity and count without changing test behavior. Domain-specific assertions and accepted privacy policy stay with the consumer. Avoid introducing a second test runner or a general private-data reporting system solely for this finding.

## Closure evidence

- A deliberately failing synthetic authored spec remains locatable by its admitted identity and bounded location while retaining its actual failure outcome.
- A malicious or coincidental spec-like substring in exception text cannot fabricate an authored frame; external/unknown paths, malformed/oversized/negative locations and arbitrary annotations are rejected or replaced with an explicit location-unavailable marker.
- Secret canaries placed in error messages/stacks, DOM, response bodies, dynamic titles and attachments do not enter any permitted output channel. Authored non-sensitive identities and genuine statuses survive.
- Retries, multiple errors, setup failures, timeout and errors with no stack remain honestly reported and bounded. Sanitization failure cannot turn a failing case green or silently drop it.
- A real installed central example demonstrates the configured output boundary without running paid services or duplicating the consumer's full domain suite.

Source attribution and these executable checks are required before declaring a shared fix. Consumer-reported mobile/reload/reselection passes are useful progress evidence, not completion of its pending browser matrix or fresh Program Kit release qualification.

## Collection disposition

Queue N17 with N16 for later consolidated review, and retain any new evidence for already adopted N13–N15 separately. No individual handoff is sent. If adopted after reconciliation, N17 increases the combined distinct inventory from 48 to 49; the active maintenance ledger currently observed here still has 47 and does not yet include N16/N17.

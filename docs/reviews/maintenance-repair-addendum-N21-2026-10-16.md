# Proposed N21: local file identity failures and stale confirmation state

Prepared 16 October 2026 for the consolidated queue. Consumer continuation D62 reports a reproduced browser recovery defect, distinct from N13's server-side PDF decoding and N17's test-report diagnostics. It is a consumer implementation gap with possible shared guidance/example prevention; no canonical Program Kit upload implementation causing it has been established. No product/consumer code or active implementation ledger was changed here.

## Evidence and limits

The user saw a generic file-identity error before declaration, and a refresh allowed a later upload. The exact transient exception was not retained and remains unknown. Do not retrospectively call it a PDF encoding error, a corrupt file, a hash mismatch or a browser-security failure.

The consumer reports a synthetic NotReadableError against its actual UI reproducing failed File selection retention and undifferentiated recovery. Current test source injects failure into both the earlier Blob.arrayBuffer path and current FileReader path, checks that the input is cleared and no allocation occurs, reselects a valid synthetic PDF, confirms explicitly and observes one allocation followed by Ready. The reported red artifact is `e5753100-3f93-4e20-bdf8-ea35772cf0ad`; this collection inspected source/report but did not execute that test or qualify the repaired runtime.

Current repair source introduces a shared consumer `file-identity.ts`, bounded exact-byte FileReader reads with abort handling, WebCrypto SHA-256, safe failure categories and exact length checks. Upload code has selection/date snapshots, revision tokens, abort controllers, failed reference/input clearing and navigation cleanup. Static checks reportedly pass; repaired real browser/runtime qualification remains due.

## Critically assess the remedy

This is a reasonable recovery/state direction, but a helper and one red/green case cannot prove the whole lifecycle:

- File reads can be actively aborted by the current FileReader path. The inspected digest call has no abort parameter; source checks cancellation before/after it. Do not promise that cancellation interrupts an in-progress cryptographic operation. Bound admitted input/work and suppress late results even when underlying work completes.
- Treat browser capability/unavailability, local file read failure, caller/navigation cancellation, internal timeout and content rejection distinctly enough for honest recovery. Do not infer the root cause of the user's original transient from a synthetic failure class. No private path, bytes, raw exception or credential should appear in diagnostics.
- Invalidate asynchronous results when files, dates, destination or navigation/session state changes. Bind confirmation to an exact immutable selection snapshot. Re-enable controls only for the current revision; an older completion must not clear a newer selection, publish a stale preview or dispatch anything.
- Clear failed in-memory File references and the relevant input so the same file can be reselected without reload, while preserving acknowledged server work and known operation identities. After dispatch/uncertain allocation, changed details require reconciliation of the known action rather than silently discarding it and issuing another declaration.
- Reuse the same invariant for waiting-original recovery. Match the exact owner/destination/length/digest contract before upload. A display name is not an identity, and refreshing the page is not the required repair for a local read failure.
- The preview currently uses a zero digest sentinel for selections outside the admissible PDF envelope rather than reading arbitrarily large/unsupported files. If that rejection-path convention remains, document and prove it cannot become a successful identity or admitted effect. It is not a fallback for hashing a supported file; never replace a failed real hash with a fabricated successful value.

## Shared handling and closure

**Owners:** Program Kit frontend integration knowledge/examples and any existing reusable file-selection seam with an attributable gap. Domain upload declarations, reviewed dates, quotas and business recovery remain consumer-owned. Do not copy the domain UI or mandate a new generic upload framework solely for this finding.

1. Trace relevant generated tasks/examples and selected browser APIs before assigning an upstream defect. Provide an explicit state/recovery recipe using real supported mechanisms, safe result categories and immutable confirmation inputs.
2. Centrally qualify a small representative example: known bytes yield the expected native SHA-256; unreadable/partial input clears only its failed selection; absence/failure of crypto does not fabricate identity; reselection works without page reload.
3. Delay old read/hash results and change file/date/destination/navigation state while they are pending. Prove stale results cannot alter the current preview, restore cleared private state or submit. Test cancellation and deadline behavior honestly, including late digest completion.
4. Count real allocation/declaration/upload effects: none before successful explicit confirmation; bounded single intended effect afterward; lost acknowledgement follows known-action reconciliation without blind duplicate allocation or resubmission. Waiting-original reselection preserves prior durable identity.
5. Qualify error/timeout paths and safe reports across supported installed browser compositions with synthetic fixtures. Confirm affected current frontend/native checks after source changes; earlier 72-case browser success does not qualify the changed UI.

The intended result is effective local correction with truthful uncertainty, not another generic catch, a reload requirement, relaxed validation or a presumed fix for an unidentified original exception. Preserve existing data, original decisions and all failure evidence. No paid calls, later story, human acceptance or publication authority is supplied by this collection.

## Queue status

N21 is proposed and held for consolidated delivery. Latest observed maintenance adoption is 47; proposed N16–N21 are six additional findings, giving a combined distinct inventory of 53 if adopted. Reconcile actual adoption before any final count. D61's image/JPEG qualification remains a refinement to N13 and is not counted again.

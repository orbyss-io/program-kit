# Reusable autosave and browser recovery investigation

Date: 30 October 2026. User direction: make autosave reusable for future consumers.
This investigation proposes the implementation boundary; it changes no consumer or runtime.

Reusable autosave is worthwhile. The strongest first capability is a shared browser save controller
with application adapters. Existing guidance already covers uncertain completion, original deadlines,
replay, ownership and cleanup. The remaining opportunity combines executable reuse, clearer examples
and earlier verification of the actual effect boundary. A universal recovery service would combine
responsibilities that these applications deliberately handle differently.

## Consumer evidence

| Consumer | Implemented mechanisms inspected | Application decisions that must remain explicit |
| --- | --- | --- |
| dezaaglijst | Target-local save state/coordinator; immutable pending payloads; atomic version/action receipts; owner-authorized status; encrypted IndexedDB recovery; generation-safe retirement and key lifetime | Independent frame/metadata versions; compare-and-swap conflicts; dependent room creation; seven-day recovery grants; background saves must not renew login |
| EetRadar | Explicit section saves; atomic mutation receipts; same-operation replay; independent-unit reconciliation; fresh session/private-root handling; bounded recovery in tab memory | One current stall; requester-selected overwrite semantics without stored revisions; explicit save; five-minute same-account draft recovery; no persistent private browser drafts |
| pk_trial_claim_2 | Owner-scoped command keys; durable upload/preparation operations; volatile browser drafts; server-history restoration; original attempt deadlines; source fencing, drain and verified cleanup | Document versions/readiness, current-source promotion, native versus OCR preparation, source custody, selective erasure and retained history |

dezaaglijst's **periodic server autosave is planned, not implemented** in the inspected source.
[T058–T060](C:/Users/tech_/Code/dezaaglijst/specs/001-voorzetwand-zaaglijst/tasks.md:125)
add it above the existing save/recovery foundation. Its current local recovery capture is a different
mechanism. Neither EetRadar nor the inspected claim workflow establishes a shared automatic-save policy.

The most useful source comparisons are:

- dezaaglijst's [TargetSaveState](C:/Users/tech_/Code/dezaaglijst/web/src/projects/save-state.ts:16),
  [SaveCoordinator](C:/Users/tech_/Code/dezaaglijst/web/src/projects/save-coordinator.ts:7) and
  [RecoveryGenerations](C:/Users/tech_/Code/dezaaglijst/web/src/recovery/generations.ts:27).
  A receipt for edit 7 leaves edit 8 dirty; unknown work retains its exact original action and payload.
- EetRadar's [dispatch and reconciliation](C:/Users/tech_/EetRadar/web/eetradar/src/owner/draft.ts:312),
  [OwnerRecovery](C:/Users/tech_/EetRadar/web/eetradar/src/owner/recovery.ts:16) and
  [OwnerDraftWriter](C:/Users/tech_/EetRadar/src/Kraamaanbod/Kraamaanbod.PostgreSql/Toelating/OwnerDraftWriter.cs:173).
  The provider writes data and receipt together, then uses a fresh unit to observe an uncertain outcome.
  The browser rereads current state after establishing completion rather than restoring old receipt content.
- The claim app's [DocumentDrafts](C:/Users/tech_/pk_trial_claim_2/web/src/features/documents/DocumentDrafts.tsx:63),
  [PreparationControl](C:/Users/tech_/pk_trial_claim_2/web/src/features/documents/PreparationControl.tsx:82) and
  [CompleteInspectionAsync](C:/Users/tech_/pk_trial_claim_2/src/Coverage.PolicyManagement.PostgreSql/Inspection/PolicyEvidenceLifecycle.Inspection.cs:11).
  Pending browser commands retain their key in the current owner generation. Reload restoration of
  server operations is distinct from persistence of unsubmitted fields or selected files.

## Existing guidance and Foundation capabilities

| Responsibility | Existing owner and coverage | Remaining boundary |
| --- | --- | --- |
| Unknown completion and replay | [UI feedback and recovery](../../extensions/program-kit-governance/references/ui-feedback-and-recovery.md:86) specifies no blind new dispatch, retained input/identity, current authorization and missing-receipt uncertainty | The small JavaScript example is illustrative; it supplies no transport, scheduler, persistence or backend transaction |
| Actual commit observation | [Implementation boundaries](../../extensions/program-kit-dotnet/references/implementation-boundaries.md:21) requires a real postcommit fault, independent durable observation and replay tests | Every selected application transaction still needs integration evidence |
| Deadlines and database lifetime | Foundation Execution/Core and PostgreSql provide original deadlines, stage caps, tracked units, context disposal and safe provider-failure facts | Foundation explicitly leaves transaction contents, retry policy and domain outcomes to the application |
| Browser session and unsaved work | Foundation Web.Presentation supplies checked browser modules, an unsaved-work registry, logout controls and fresh session/private-DOM lifecycle | These modules deliberately do not save, discard, persist drafts or replay domain requests |
| Background task lifecycle | Foundation Tasks starts and drains shell-generation tasks | It is not a durable job store, receipt ledger or document erasure coordinator |
| Durable work and cleanup | [Asynchronous workloads](../../extensions/program-kit-governance/references/asynchronous-workloads.md:100), its synthetic example and [physical-effect fencing](../../extensions/program-kit-dotnet/references/cross-resource-fencing.md) cover original bindings, attempts, stop uncertainty, retryable cleanup and resource fences | The examples do not supply a qualified general production workflow/storage implementation |
| Save through server restart | [Server draft durability](../../extensions/program-kit-governance/references/ui-feedback-and-recovery.md:154) supplies an acceptance adapter contract for acknowledged server data | This is a test facility, not browser draft storage or autosave runtime |

The maintained typed-operation recipe explicitly excludes general idempotency and uncertain-write
retry guarantees. Extending that simple write/read example informally into a production save protocol
would leave substantial work to every agent. A separate focused safe-mutation recipe would be useful.

All three consumers report Program Kit `1.0.0-preview.1`. Selected Foundation packages are 0.3.9 in
dezaaglijst and pk_trial_claim_2, and 0.3.11 in EetRadar. Their installed UI recovery and asynchronous
workload references match the inspected Program Kit main files byte for byte. EetRadar's implementation
boundary reference also matches main; the other two retain an earlier revision of that file. A new
Foundation feature would require normal package/profile adoption rather than appearing through a
guidance update or copying current Foundation source into an older consumer.

## Guidance at the delivery stages

Nine read-only projections of the **installed** phase helper were exercised: planning, tasks and
implementation for each consumer's first feature. All selected browser-effects, persistence and
relevant .NET responsibilities with no context diagnostics. dezaaglijst and the claim app also selected
async-workload. EetRadar's projection did not select that separate workload responsibility; ordinary
database save recovery already has browser/persistence routes.

These results establish present discoverability, not historical agent obedience. More specific evidence is:

- dezaaglijst's research records reading UI recovery and asynchronous-workload guidance before design.
  T014–T024 put commit loss, replay, first-operation review, edit generations and encrypted recovery
  into the first working story. Autosave is explicitly scheduled later, on that foundation.
- EetRadar's plan records a substantive after-plan review and receipt/recovery decisions. The chat
  **Implement single-stall backend model** shows the implementation hook being applied and provider
  checks at the actual commit boundary. Its overwrite policy follows the requester's explicit decision.
- The claim plan already requires original deadlines, attempt generations and cleanup obligations.
  The chat **Implement Story 1 through R1** nevertheless records a later review finding that Ready
  acceptance checked the longer lease without independently checking the shorter attempt deadline.
  The inspected source now checks that deadline, and a focused provider test challenges the distinction.

The evidence supports an **application and verification gap alongside a reuse gap**. It does not support
the conclusion that agents never received guidance, or that every occurrence of recovery reasoning is
wasted work. Future implementation should carry the selected adverse cases into the first real save
or worker operation, before repeating its structure. Existing plan/tasks and first-operation review
are sufficient places to do this; another approval ledger or general recovery questionnaire is unnecessary.

Two focused guidance improvements are justified:

1. The outcome table and recovery example currently describe a retained **server-issued** operation
   identity. These applications also legitimately use client-generated action/command UUIDs. Explain
   client idempotency keys, server operation IDs and receipts separately. Their association, scope and
   replay semantics come from the server contract; a preparation endpoint is not universally required.
2. State explicitly that permission to accept a useful result can expire while the obligation to
   drain and acknowledge cleanup remains. Add this distinction to the existing async example and
   conformance cases, including stale-attempt cleanup that must not clear a successor's obligation.

## Proposed reusable autosave capability

Build a framework-independent browser controller with checked TypeScript declarations and small
application adapters. A separate network service is unnecessary: the browser already owns input and
cadence, while the existing backend owns effects. React and plain DOM code should consume the same
controller. Automatic saving must be opt-in for each application; EetRadar's explicit-save decision
does not change merely because the shared capability exists.

The controller should own these mechanics:

- One scheduled loop per editor/account generation, with a caller-supplied bounded interval. Start
  after the first interval, skip clean state and prevent overlapping manual/automatic dispatch.
  Preserve dezaaglijst's periodic cadence without adding debounce modes before another consumer needs one.
- Capture an immutable attempt, including a local edit generation, target and the adapter's stable
  operation key. Manual save and autosave enter the same controller. A late confirmation acknowledges
  only its submitted generation and cannot make newer edits clean.
- Distinguish confirmed, proven rejection without effect, conflict and unknown. Retain the exact
  original attempt while unknown; permit only adapter-supported status observation or identical replay.
  Never derive rollback or safe retry from a generic HTTP status or a thrown exception.
- Expose stable pending/dirty/unknown/conflict observations for the application's UI and the existing
  Foundation unsaved-work registry. Keep product copy, markup and styling outside the controller.
- Stop timer admission and fence late callbacks on disposal/account change. On suspension/resume,
  require fresh session admission and reconcile retained uncertain work before another write; perform
  at most one due attempt rather than a catch-up burst. Background activity must not imply human activity.

The application adapter supplies the target, serializable immutable snapshot, edit-generation token,
operation-key creation, admitted transport outcomes, authorized status/replay operations and any
parent-save dependency. A local edit-generation token is internal browser bookkeeping; it does not
require stored backend version columns or change EetRadar's overwrite semantics.

Browser persistence is a separate optional adapter. Its contract must cover owner isolation, schema
admission, retention, unavailable/quota failures and conditional removal of the exact confirmed
generation. A memory-only adapter must not advertise reload recovery. dezaaglijst's encryption,
device grants and key lifecycle are useful evidence for a future durable adapter, but should not
become mandatory infrastructure for every form. Reloading an acknowledged server draft remains a
server-read journey.

Foundation is the proposed runtime owner. Its current Web.Presentation package already ships versioned
browser modules and declarations, so an independently imported module there is a plausible first
delivery route. Confirm that package fit in Foundation's own review; keep the controller free of DOM,
React, document types and Program Kit dependencies. Program Kit owns the selection guidance, recipe,
integration example and qualified profile capture. Consumer repositories own domain adapters and UI.

Start with dezaaglijst's not-yet-built periodic story as the real integration. Prove the controller can
also handle an overwrite save through a second independent adapter, without enabling autosave in
EetRadar or changing either application's product policy. Extraction succeeds when both use the same
controller without consumer-specific branches, and application code supplies domain decisions rather
than rebuilding scheduling and attempt-state machinery.

## Autosave acceptance cases

Use deterministic clocks and controlled adapter promises for the controller. Then run focused browser
and actual-provider integration for the selected consumer; a shared unit test cannot prove its database.

| Case | Required observation |
| --- | --- |
| Cadence and clean input | First attempt after one interval; typing does not reset the period; clean ticks dispatch nothing |
| Manual and automatic collision | One active attempt; manual saving still works with autosave disabled |
| Newer input during save | Edit 7 confirmation leaves edit 8 dirty and leaves other targets untouched |
| Missing response or receipt | Original key and payload retained; no new effect identity or false rollback |
| Genuine rejection or conflict | Values retained; contract-defined correction or explicit conflict resolution remains available |
| Late callback | Old editor/account/generation cannot publish into its successor |
| Suspend and resume | Fresh authorization, original-attempt reconciliation, no timer burst |
| Authentication expiry | Background saves do not prolong the native session; no protected dispatch after expiry |
| Reload with persistence selected | Runtime-admitted snapshot and retained uncertain attempt restore in the correct owner scope |
| Storage failure | Online-save and local-recovery results remain separate and honestly visible |
| Actual commit response loss | Independent database observation and identical replay establish one effect and the original receipt |

## Backend recovery and cleanup reuse

A safe-mutation **recipe and reusable fault fixtures** are justified now. Cover owner-scoped keys,
versioned request fingerprints, atomic effect/receipt writes, replay before current-state rejection,
fresh-unit observation, current authorization and retention. Keep receipts in the same transaction
as business data. Generic HTTP middleware with an independently committed receipt store cannot
establish that guarantee. Use native EF execution-strategy facilities where compatible, without
assuming they establish the whole application contract.

A production shared receipt API remains a second extraction candidate. First demonstrate the same
contract against two different operations, including dezaaglijst's version conflict and EetRadar's
overwrite. Avoid a generic repository, transaction forwarding wrapper or centrally imposed domain
result schema. Do not expire receipts in a way that turns a late duplicate into a fresh effect.

The claim cleanup example has a reusable rule: **result acceptance, execution stop and cleanup
completion are separate facts**. A late Ready result must be rejected. The same bound attempt may
still acknowledge verified drain/absence as non-ready through its authorized cleanup path. Expiry
does not create proof of cleanup; acknowledgement must match the attempt, resource, generation and
actual cleanup observation. Restart and uncertain acknowledgement retain the obligation. Cleanup
needs its own bounded attempt budget without extending the original result deadline.

That rule deserves an executable example now. A general production cleanup coordinator needs more
evidence: the inspected consumers do not demonstrate interchangeable PDF scratch cleanup, encrypted
draft-key retirement and database transaction disposal. A shared workflow engine would bring more
policy and operational ownership than this evidence currently justifies.

## Existing library boundaries

EF Core already documents uncertain commits and provides verification-oriented transaction helpers.
That supports reusing native mechanisms while retaining application receipt/authorization policy.
[EF Core connection resiliency](https://learn.microsoft.com/en-us/ef/core/miscellaneous/connection-resiliency#transaction-commit-failure-and-the-idempotency-issue)

HTTP resilience handlers supply retries, timeouts and breakers. Microsoft explicitly warns that
retrying writes can duplicate effects and exposes controls for disabling unsafe-method retries.
Adding a retry library alone would not replace this investigation's save protocol.
[.NET HTTP resilience](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience)

TanStack Query provides mutation lifecycle, optional retry, serialization scopes and persisted
mutation resumption. It is a credible adapter option for a React application that already uses it.
Its documented behavior does not establish the backend's idempotency or the consumer's privacy policy;
the shared contract should work with it without requiring it in EetRadar's plain DOM editor.
[TanStack mutation guidance](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)

Browser unload events cannot guarantee a final save, particularly on mobile. Browser storage is also
subject to quota and eviction behavior. Autosave and local recovery must expose their actual guarantees
rather than promise that all recent input always survives closing a browser.
[MDN beforeunload](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event),
[MDN browser storage](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)

## Recommended sequence and investigation limits

1. Design and implement the shared autosave controller in Foundation, with deterministic adverse cases
   and two distinct adapters. Adopt its released/profiled capability in dezaaglijst's existing story.
2. Improve the existing recovery guidance and safe-mutation recipe, with real postcommit fault fixtures.
   Carry the selected cases into normal planning/tasks and the first-operation source review.
3. Extend the async example with separate result-deadline and cleanup-acknowledgement transitions.
   Consider a production cleanup or receipt component only after a second independent use validates
   the common contract.

This investigation inspected source and authored project decisions. dezaaglijst used no chat evidence,
as requested. The other two included the named active chats. Their pass counts remain reported results;
their applications, databases and browsers were not restarted or tested by this investigation.
The existing Program Kit recovery example was independently executed: **12 semantic recovery cases
passed** with `python tests/validate_operation_recovery.py`. The nine installed guidance projections
were also executed. These are narrow checks, not consumer acceptance or a general correctness audit.

Program Kit started at `69ae5656862f328d65c2d400e056999ef1624101` with unrelated working changes.
Consumer HEADs observed were dezaaglijst `fff7118d804489c9aaba8a565e5798fc04395ad2` (clean),
pk_trial_claim_2 `f9d81297752beee06adda7b713db3a3d3da23c9a` (active working changes), and EetRadar
`34ddb389e582c590d11ea07eeded3eaf97b2f820` (active working changes). Source observations in the
latter two concern their inspected working files, not just those commits. Both were being edited
concurrently, so this is a bounded investigation snapshot, not an exact-source certification.

No consumer files, installed skills, runtime source, existing maintenance ledgers or other reviews
were changed. There is no measured time-saving claim yet. The proposed extraction should be judged
by reduced repeated implementation and shared adverse-case coverage in actual integrations.

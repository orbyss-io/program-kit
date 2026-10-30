# Reusable autosave Foundation design and implementation plan

Date: 30 October 2026. Status: F1 reviewed, both gaps fixed; Foundation 0.3.12 publicly released.
Program Kit qualified-default adoption: `p-3bec4dafa1f3` through [PR 66](https://github.com/orbyss-io/program-kit/pull/66).
Scope: Foundation browser autosave and Program Kit adoption. dezaaglijst remains a deferred proposal.
The [investigation](browser-recovery-and-autosave-investigation-2026-10-30.md) supplies the consumer comparison.

The requester reviewed the controller and two recording adapters, then authorized both repairs,
public Foundation publication and Program Kit profile adoption. The [F1 review](https://github.com/orbyss-io/dotnet-foundation/blob/v0.3.12/docs/autosave-controller-review.md)
retains the original observations. [Foundation 0.3.12](https://github.com/orbyss-io/dotnet-foundation/releases/tag/v0.3.12)
is public, including all 31 runtime NuGets, both Host platforms and release knowledge. Program Kit's
normal qualified-profile owner supplies the new default; native PR package CI governs its merge.
dezaaglijst adoption below is a future proposal only. No consumer update is authorized here.

Deliver an optional `autosave.mjs` module in `Orbyss.Foundation.Web.Presentation`, with checked
TypeScript declarations. It coordinates local edit generations, manual saves, periodic saves and
retained uncertain attempts. Application adapters own serialized requests, receipt admission,
authorization, conflicts and persistence. This is a browser library in the existing package;
the backend continues to own the actual transaction and effect.

## Ownership and first release scope

| Owner | Responsibility |
| --- | --- |
| Foundation autosave | One editor lifetime, target registry, cadence, immutable pending attempts, local edit acknowledgement, single active adapter operation, timeout/cancellation observations and stale-callback exclusion |
| Existing Foundation browser modules | Session observation, private DOM visibility, unsaved-work registration and authentication controls |
| Application adapter | Target identities, current account admission, payload construction, server response validation, receipt binding, server versions or overwrite policy, conflict choices and save dependencies |
| Application recovery | Existing encrypted or volatile snapshots, key grants, exact-generation retirement, retention and reload admission |
| Program Kit | Capability selection and profile projection, focused usage recipe, phase guidance, installed representation and proportional validation |

The first release supports periodic saving and explicit manual saving through the same coordinator.
It includes a required application-supplied interval and finite operation budget. Debounce modes,
offline dispatch queues, cross-tab leadership, a shared receipt database, new HTTP endpoints and
general worker cleanup are outside this increment. Autosave is opt-in at the application boundary;
loading the module performs no save, timer registration, authentication or browser storage access.

Use no React, DOM, HTTP, document-model or Program Kit dependency in the controller. Browser built-ins
provide monotonic time, timers, abort signals and UUID generation. Private scheduler/clock injection
supports deterministic tests; do not expose a second production scheduling framework.

## Foundation package and compatibility

Add these package-owned files:

```text
src/Orbyss.Foundation.Web.Presentation/browser/autosave.mjs
src/Orbyss.Foundation.Web.Presentation/browser/autosave.d.mts
tests/browser/autosave.test.mjs
tests/browser/autosave-types.mts
tests/browser/autosave-browser.cjs
```

Extend the existing package README and explicit asset route list in
[FoundationBrowserPresentationFeature.cs](C:/Users/tech_/Code/Orbyss/dotnet-foundation/src/Orbyss.Foundation.Web.Presentation/FoundationBrowserPresentationFeature.cs:120).
The project already embeds and packs `browser/*`; no new .NET project or feature is required.
Serve the two new files through the existing anonymous GET/HEAD asset routes and response policy.
Keep application data out of those assets. The module exports `AUTOSAVE_CONTRACT` with value
`foundation-browser-autosave/v1`.

**Preserve the current bootstrap JSON.** The
[configuration loader](C:/Users/tech_/Code/Orbyss/dotnet-foundation/src/Orbyss.Foundation.Web.Presentation/browser/configuration.mjs)
admits an exact field set; adding `autosaveModulePath` to that response would break old loaders.
The application derives the module URL from the already admitted `modulePath`, replacing the fixed
`presentation.mjs` suffix with `autosave.mjs`. This preserves custom route prefixes and shell paths.
The focused recipe verifies that the selected package/profile actually contains the capability.
An older package remains supported for its existing features but cannot satisfy an autosave opt-in.

Runtime modules remain served by the selected Foundation package. Program Kit projects exact
declarations for compilation and never vendors an alternate autosave implementation. A new Foundation
release and qualified profile are required for normal consumer adoption; a local source build or
copied declaration cannot establish public availability. Select the actual release version through
Foundation's existing release owner rather than inventing a version in this plan.

## Controller contract

Create one controller per mounted editor/account generation and register independent targets on it.
Opaque target strings contain stable IDs, not labels or private content. Duplicate registration in
one controller fails before mutation. Cross-window and cross-controller deduplication remain backend
responsibilities. A frame and project metadata have separate target state even when they share a timer.

The following declaration fixes the intended API shape. Names can receive ordinary source review,
but implementation must preserve these responsibilities and behaviors.

```typescript
export declare const AUTOSAVE_CONTRACT: 'foundation-browser-autosave/v1';

export type SavePhase = 'clean' | 'dirty' | 'pending' | 'unknown' | 'conflict' | 'rejected';
export type SaveTrigger = 'manual' | 'automatic' | 'status' | 'replay';
export type Attempt = Readonly<{
  target: string;
  operationKey: string;
  editRevision: number;
  generation: string;
  payload: string;
}>;
export type OperationContext = Readonly<{
  signal: AbortSignal;
  expiresAtMonotonic: number;
  trigger: SaveTrigger;
}>;
export type Confirmed<R> = Readonly<{ kind: 'confirmed'; receipt: R }>;
export type Unknown = Readonly<{ kind: 'unknown' }>;
export type SaveResult<R> = Confirmed<R> | Unknown
  | Readonly<{ kind: 'rejected-without-effect' }>
  | Readonly<{ kind: 'conflict' }>;
export type SaveState<R> = Readonly<{
  phase: SavePhase;
  editRevision: number;
  confirmedEditRevision: number;
  generation: string;
  pending: Attempt | null;
  lastConfirmation: Readonly<{ attempt: Attempt; receipt: R }> | null;
  fault: 'adapter' | null;
}>;
export type InitialSaveState = Readonly<{
  editRevision: number;
  confirmedEditRevision: number;
  generation: string;
  pending: Attempt | null;
}>;
export interface SaveAdapter<R> {
  admit(context: OperationContext): Promise<'ready' | 'blocked'>;
  capture(identity: Omit<Attempt, 'payload'>):
    | Readonly<{ kind: 'prepared'; payload: string }>
    | Readonly<{ kind: 'blocked' | 'invalid' }>;
  prepare?(attempt: Attempt, context: OperationContext):
    Promise<'stored' | 'unavailable'>;
  write(attempt: Attempt, context: OperationContext): Promise<SaveResult<R>>;
  lookup?(attempt: Attempt, context: OperationContext): Promise<Confirmed<R> | Unknown>;
  replay?(attempt: Attempt, context: OperationContext): Promise<SaveResult<R>>;
  confirmed(attempt: Attempt, receipt: R): undefined;
}
export type RequestResult = 'observed' | 'clean' | 'busy' | 'blocked' | 'disposed';
export interface SaveTarget<R> {
  readonly state: SaveState<R>;
  edited(): void;
  save(): Promise<RequestResult>;
  reconcile(mode: 'status' | 'replay'): Promise<RequestResult>;
  resumeAfterConflict(): void;
  unsaved(): 'clean' | 'dirty' | 'unknown';
  subscribe(listener: (state: SaveState<R>) => undefined): () => void;
  unregister(): Promise<void>;
}
export interface AutosaveController {
  register<R>(options: {
    target: string;
    maximumPayloadBytes: number;
    initial: InitialSaveState;
    adapter: SaveAdapter<R>;
  }): SaveTarget<R>;
  suspend(): void;
  resume(): void;
  dispose(): Promise<void>;
}
export declare function createAutosaveController(options: {
  enabled: boolean;
  intervalMilliseconds: number;
  operationTimeoutMilliseconds: number;
  signal?: AbortSignal;
}): AutosaveController;
```

`resume()` permits scheduling again; it is not authentication proof and performs no write itself.
Every operation still goes through `admit`. Disabled autosave creates no cadence timer and preserves
manual save/status/replay. Disposed controllers cannot resume. Options are immutable for the editor
lifetime; configuration changes apply at an explicit remount, preserving active attempts' snapshots.

`edited()` increments the safe-integer local revision and creates a new opaque local generation.
It does not clear an uncertain attempt or resolve a conflict. Safe-integer exhaustion rejects before
altering state. These revisions are browser bookkeeping and require no database version column.
Fresh clean data starts at revision zero/confirmed zero; a new unsaved target starts dirty. Restored
state comes from the application's admitted snapshot as described below.

`capture` runs synchronously after admission while the controller owns the active slot. The supplied
operation key is generated once; a contract that needs a server-created identity must acquire it in
application admission and retain the association within its adapter. The generic key is a correlation
key, not a server-issued authorization. `payload` is the complete serialized application request;
strings and the frozen attempt envelope prevent later input mutation from changing replay bytes.
Validate nonempty IDs, finite/safe revisions, generation relationships and UTF-8 payload capacity before
installing the attempt. Foundation does not parse or reinterpret the application's wire JSON.

Registration derives phase from initial state: a retained pending action starts unknown; otherwise
unequal local/confirmed revisions start dirty and equal revisions start clean. A restored pending
revision must not exceed the current edit revision and must match the registered target; its original
generation may differ from the newer restored draft generation. Never rewrite that retained identity.

Adapters validate raw responses and bind receipt identity, target, submitted revision and any server
version/schema before returning `confirmed`. Foundation validates the result discriminator and
required receipt presence, and accepts it only for the active attempt/lifetime. It cannot establish
business correctness from an arbitrary receipt. Receipts remain application-owned immutable values.
Malformed results and exceptions after entering `write` become unknown, with the original attempt retained.

`confirmed` is a synchronous application state update: advance server basis/receipt and confirmed
parent relationships before publishing the final Foundation observation. It must not start unobserved
work. If it throws, retain the already established confirmation, set `fault=adapter`, stop this target's
new dispatch and expose the observation. A callback fault never converts an observed commit into a
failed write or licenses retry. Repair/recreate that adapter from the retained confirmation. Subscriber
exceptions are isolated after state publication and cannot roll back acknowledgement or cause dispatch.
Asynchronous recovery retirement is separately owned, bounded and observed by the application.
The declaration rejects asynchronous confirmation/subscription callbacks; runtime admission also
rejects thenable callback results. Guard transition publication against reentrancy: nested save
requests see the reserved active slot, and a callback cannot unregister/rebind a target and then let
its old continuation publish into the replacement.

## Scheduling and state transitions

**One interval triggers a finite pass over the registered targets**, rather than saving just one
frame every twenty minutes. This makes the multi-target interpretation explicit for review.

The first pass begins no earlier than one interval after editor creation. Typing and manual saving
do not reset the cadence. A pass snapshots registration order once, checks each target at most once,
and awaits operations sequentially. Targets registered during it wait for the next pass. A target
removed or already confirmed before its turn is skipped. There is no dynamically growing work queue.
Each operation has a finite reported cutoff. An adapter that ignores cancellation can keep its actual
drain and the pass pending; the controller must not release the slot to claim bounded physical stop.
Rotate the starting target between passes to avoid permanently favoring one
target when interruptions prevent completing a pass.

Arm the next interval after the pass settles. This ensures at least one full interval between passes
and between repeated automatic attempts for the same target. A slow pass does not accumulate timer
callbacks. Clean passes create no requests or new confirmation labels. Each pass may save multiple
independent dirty targets; each target still receives at most one fresh attempt per pass.

One active adapter operation is allowed per editor, across automatic, manual, status and replay calls.
A concurrent request returns `busy`; it does not silently queue an old snapshot. UI disables the
affected action or presents busy state. A manual request that arrives between operations ends the
remaining automatic pass and takes the next slot. Manual save captures current input; it never
automatically follows a pending manual request with another write.

| Current condition or event | Required behavior |
| --- | --- |
| Clean target | Skip without capture, network effect or status-label change |
| Dirty and admitted | Capture one immutable attempt; publish pending; optional prepare; invoke write once |
| Admission blocked or dependency unavailable | Keep dirty; no pending business action or write; retry eligibility at a later pass/manual request |
| Invalid capture or authoritative no-effect rejection | Retain editable values; rejected state; automatic saving waits for an edit or manual correction attempt |
| Confirmed attempt | Acknowledge only its submitted local revision; newer input stays dirty; retain the receipt |
| Conflict | Retain draft and attempt; pause that target; application performs comparison and changes basis before `resumeAfterConflict` |
| Unknown completion | Retain exact attempt; skip automatic/new manual writes; expose explicit status or supported identical replay |
| Absent, forbidden, malformed or failed status | Remain unknown; no new operation key |
| Confirmed status/replay | Apply the same exact-attempt admission and acknowledgement as a normal response |
| Other target unknown/conflicted | Continue eligible independent targets once the shared active operation has settled |

`lookup` is read-only and returns only confirmed/unknown in this version. `replay` exists only when
the adapter's server contract supports an identical replay. A missing callback returns blocked before
I/O. The module does not infer either capability from HTTP verbs, status codes or a retry library.
Neither reconciliation route resets the business operation's identity or stored server deadline;
each later browser request has its own finite observation/transport budget.

## Cancellation and lifecycle

The operation budget begins before admission and covers admission, preparation and transport.
Carry the same abort signal and absolute monotonic expiry through all adapter stages. Existing
provider/server budgets stay independent; adapter stages may impose smaller caps but cannot extend
the outer browser budget. Use native timer chunks for durations above the signed timer range.
Invalid/nonrepresentable intervals and budgets fail before creating a timer or changing target state.

At expiry or suspension, abort current adapter work and fence new dispatch immediately. If `write`
has not been entered, no save invocation occurred; preserve dirty/rejected input without claiming an
uncertain commit. Once `write` was entered, conservatively retain unknown unless its admitted result
was already accepted. A returned promise must settle before the active slot is released. An adapter
that ignores abort cannot cause a second overlapping operation merely because a timeout fired.
Its late result is observed for drain but cannot overwrite state after the operation cutoff.

`suspend()` stops timer admission and aborts active work synchronously while preserving retained
attempts. The application calls it on hidden/private-session uncertainty. On visibility/session return,
`resume()` rearms at most one overdue pass, using fresh adapter admission. Pending uncertainty still
requires explicit reconciliation. No catch-up burst, unload flush, automatic login or user-activity
report is generated. On account change, dispose the old controller; never resume it for the new account.

`dispose()` and `unregister()` fence callbacks and release idle data synchronously. Their returned
promise observes actual settlement of owned adapter calls; it is not proof that the server stopped.
An uncooperative adapter can keep that drain pending. Session hiding and private-data clearing never
wait for that promise. Retained input needed for recovery is transferred through the existing
application recovery owner before its normal disposal, rather than being silently erased by autosave.

These browser limits are deliberate: [timers can run late](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout),
[monotonic clocks differ during sleep](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now),
and [abort requires cooperating asynchronous work](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal).
Cadence is a minimum spacing guarantee while execution is available, not a maximum data-loss window
or proof of server rollback. Resume recalculates monotonic due state; it does not invent missed saves.

## Recovery and dezaaglijst adaptation

Keep the encrypted recovery format and server protocol unchanged. Translate between Foundation's
attempt and the existing `SaveAttempt` at one application boundary:

| Foundation field or state | dezaaglijst mapping |
| --- | --- |
| `target` | Stable encoding of existing ProjectId/TargetKind/TargetId |
| `operationKey` | Existing `actionId` UUID |
| `editRevision` / `generation` | Existing submittedEditRevision / recoveryGeneration |
| `payload` | Existing complete serialized metadata/frame request, including expectedVersion/schema |
| `confirmed` | Admitted confirmed or unchanged outcome, after existing receipt/version/schema checks |
| `rejected-without-effect` | Only established no-effect application rejection; a transport status alone is insufficient |
| `conflict` | Existing target-version conflict and explicit compare/reapply route |
| `unknown` | Existing lost response, missing status or uncertain dispatch; payload mismatch stays blocked for reviewed resolution |

Refactor [TargetSaveState](C:/Users/tech_/Code/dezaaglijst/web/src/projects/save-state.ts)
to retain only application receipt/version/conflict data and its compatibility view for recovery/UI.
Foundation becomes the sole owner of phase, current/confirmed local revisions and pending attempts.
Replace [SaveCoordinator](C:/Users/tech_/Code/dezaaglijst/web/src/projects/save-coordinator.ts)
with a thin adapter around the Foundation target. Remove the old transition/network coordination
logic in the same increment; do not run both implementations or leave a consumer timer fallback.

Update `ProjectEditor` to register metadata before frames. Metadata confirmation updates confirmed
room relationships synchronously. A new frame whose room is unconfirmed returns blocked at capture;
it may save after metadata succeeds earlier in that pass. Failed metadata must not block unrelated
existing-frame saves. Frame receipts never change metadata or another frame's state.

Reconstruct the old `SaveAttempt.expectedVersion` and `schemaVersion` from the admitted original
payload/snapshot at that adapter boundary, never from the latest server basis. Foundation's retained
generic attempt omits these domain fields; replay and recovery still require their original values.

Add optional outer-signal parameters to existing `ProjectClient.save/status` and thread them into
`AccountRequests.run`. Keep its account/antiforgery/no-store/response-bound ownership. Native session
reobservation remains in the existing session owner and supplies the adapter's admission, with actual
server authorization on every effect. Do not introduce an autosave authentication client.

The existing `RecoveryGenerations.prepare` supplies the optional prepare hook; add an optional outer
signal and compose it with its existing bounded recovery lifetime. It persists the exact
pending action where possible; unavailable local recovery is separately reported and does not suppress
an online save while the operation is still admitted. Confirmation retires only the matching stored
generation through the existing recovery owner. A local preparation timeout cannot dispatch after
the shared budget has expired.

For reload, first run the existing `admitRecoverySnapshot`, owner/device/key/expiry checks and parent
lookup. Reconstitute the application basis, then supply structurally valid Foundation initial state.
An admitted retained pending action starts **unknown**, with its original payload/key, while the restored
draft remains a newer local edit. Restore itself performs no dispatch. Preserve version-1 snapshot
fields and unknown-member rejection; no new fields are added to ciphertext just to mirror the library.
This allows old admitted recovery drafts to remain usable without a storage migration.

Implement `AutoSaveOptions` and editor configuration as already planned: Enabled=true and
IntervalSeconds=1200 from one native Options/settings-metadata source. Foundation has no twenty-minute
default. Use the existing client save allowance (server SaveTimeoutSeconds plus five seconds) as its
operation cap, and the existing JSON request limit per target. Preserve the independent thirty-minute
idle timeout and seven-day recovery retention. Background save/status/config calls must not renew login.

Reconcile the existing T058–T066 tasks rather than creating a new consumer feature or bypassing
their prerequisites. T058 gains the admitted settings projection; T059 loads/binds the native module
instead of implementing a timer; T060 replaces duplicate coordinator state with the adapter and
ordering tests. T061–T064 retain conflict, interruption, session isolation and recovery duties.
T065 runs the actual story scenarios; T066 remains the agreed human review. Do not mark the earlier
US4 review or other prerequisites satisfied through this cross-repository plan.

## Program Kit changes

1. Extend `foundation_composition.browser_declarations` to discover the optional autosave declaration
   from the **selected** package/source capture. Verify both module and declaration against captured
   source and exact package `payloadFiles`. Both absent means unsupported; inconsistent presence/hash
   is a broken capture and fails. Retain the required baseline declarations for historical profiles.
2. Let the existing composition renderer project only the exact declaration when supported. Add a
   focused example under `references/examples/browser-autosave/` that imports native runtime bytes,
   shows periodic and manual use, and makes capability absence explicit before adoption. Use a small
   version-conflict adapter and an overwrite adapter; neither uses a real consumer's private data.
3. Extend `ui-feedback-and-recovery.md` through its existing knowledge markers: autosave versus local
   recovery, one coordinator, immutable attempts, identity issuer distinctions, explicit unknown
   reconciliation, and session/activity isolation. Correct server-issued-only wording in the existing
   outcome table/example. Keep the standalone semantic example's proof limits visible.
4. Route the new focused guidance through existing browser-experience/browser-effects obligations
   in `phase-obligations.json`. Intake clarifies meaningful user promises only; planning selects
   capability/policy and adverse cases; tasks name adapter/first integration; implementation reviews
   the first save; delivery exercises the real journey. Add no mandatory autosave feature, new hook,
   lifecycle ledger or full-matrix checkpoint.
5. Extend the package-owned README for versioned usage. The existing publisher source allowlist already
   captures `.mjs`, `.mts` and package README files; verify this representation before changing capture
   policy. Qualify/promote a new public dependency profile through normal maintenance, preserving frozen
   profiles and consumer locks. No change to EetRadar or the claim app is part of this adoption.

## Implementation sections and review boundaries

| Section | Concrete deliverable | Validation and exit |
| --- | --- | --- |
| F1 Controller and contract | New module/types, deterministic cadence/state/lifetime tests, version-conflict and overwrite recording adapters, README contract | Strict types; first coherent manual+automatic save; edit-7/edit-8; unknown identity retention; actual pending/drain behavior; technical source review before replicating adapters |
| F2 Package and browser integration | Native routes, real browser fixture, package-content and existing-bootstrap compatibility checks | New source and built-package assets/types agree; custom prefix/path base GET/HEAD; unchanged bootstrap; native unsaved registry consumes observations; Chromium/WebKit locally and retained Firefox scenario in CI |
| P1 Program Kit adoption support | Optional exact declaration projection, recipe, canonical guidance/routing and focused tests | Old profiles still work without autosave; opting in without capability fails before consumer edits; mixed/tampered capture rejects; installed recipe/types match package owners |
| D1 dezaaglijst integration | Existing settings/tasks amended; manual path moved to native coordinator; periodic binding; preserved recovery format | Existing manual-save/recovery regressions pass before enabling cadence; actual CAS/receipt-loss/account/session tests; exact-generation retirement and old-snapshot restore |
| D2 Consumer story review | Complete T061–T065 journey and retained evidence, then existing T066 review | Requester sees real autosave, newer-input preservation, conflict, expiry and double-storage-failure behavior; required prior review decisions remain explicit |

The requester reviewed F1, identified two gaps and authorized their repair followed by public
Foundation publication and Program Kit adoption. Stable registration order replaces rotation, and
read-only activity observation distinguishes cutoff from actual drain/slot release. There is no
additional toolkit review gate. Consumer adoption remains deferred for a later discussion.

Development may validate recording adapters and a clearly labeled disposable candidate consumer before
publication. Normal dezaaglijst adoption follows the public Foundation release and Program Kit profile
qualification. Do not substitute unpublished bytes into its selected profile or claim they are released.

## Validation plan

| Layer | Required cases |
| --- | --- |
| Controller | Initial interval/clean skip; active typing does not debounce; disabled/manual path; multiple targets once per finite pass; dependency order; manual collision and busy results; stable parent-first order; no catch-up burst |
| Attempt state | Edit-7 confirmation preserves edit-8; independent targets; exact payload/key replay; missing/forbidden status; rejected/corrected and conflict/reviewed transitions; malformed result; old callback; callback failure after an observed commit |
| Lifetime | Abort before write; unknown after write entry; expiry during prepare; uncooperative adapter prevents overlap; suspend/resume; unregister/dispose during I/O; old-account callback; no server-stop claim |
| Recovery | Old v1 snapshot and retained action import; tampered/oversize/foreign input rejected by correct owner; local-store failure plus online success; online unknown plus stored recovery; conditional retirement preserves a newer generation |
| Native package | Packed files, declarations, exports and served bytes; actual GET/HEAD under changed prefix/path base; old bootstrap loader against new server; unsupported old package behavior; native unsaved registry binding |
| Consumer | Real atomic CAS/receipt, replay after lost commit response, owner isolation, no auth renewal by background saves, true expiry during save, independent targets and partial success; actual browser UI/status/accessibility checks |

Foundation: extend `tests/browser/package.json`, strict type includes and the explicit focused CI/Release
browser commands to include the new cases. Use `node --test tests/browser/autosave.test.mjs`,
`npm run --prefix tests/browser test:types` and `node tests/browser/autosave-browser.cjs
--engines=chromium,webkit` locally after implementation. These commands/files are now implemented. Use actual package probes for serving/installed claims, then the owner's normal
locked restore/build/pack and applicable release process. Dependency maintenance belongs to candidate
selection, not every edit loop. Retain Firefox in the affected CI scenario and report the known local
Windows launch limitation without production workarounds.

Program Kit: run Integrity, then inventory-selected Affected checks against the implementation base.
Extend `validate_browser_presentation_profile`, `validate_knowledge_sources`, the standalone
`tests/validate_operation_recovery.py` example check and relevant native-phase selection tests.
The standalone recovery check currently has no direct inventory registration: add a narrow owning
registration for the changed example and its inputs, rather than assuming Affected already selects it.
Register any new narrow recipe check in that same inventory.
Choose archive installation once for the changed shipped recipe/declaration representation. Broad
composition/browser/Host investigations require their specific affected contract and reason; a shared
package change does not select the complete historical matrix.

dezaaglijst: use its maintained native/browser entrypoints and affected groups for each section,
including the existing save-state, actual-provider, recovery and session fixtures. Preserve original
failed evidence; fix supported failures through their focused owners. Run short test intervals plus
real default projection, without waiting twenty minutes per mechanical check. Retain the final story
review and required device walkthrough; technical checks do not supply human acceptance.

## Original planning basis and current next action

Foundation source observed: `main`, `bc66af8d7a707b4d2ae1f199dfdcdfd3a428f07a`, with an unrelated
untracked `.worktrees/` directory. dezaaglijst remains clean at
`fff7118d804489c9aaba8a565e5798fc04395ad2` on `codex/bootstrap-do-over`. Program Kit is at
`69ae5656862f328d65c2d400e056999ef1624101` with previously existing unrelated working changes.
The original planning pass changed only this design document and retained a type-only API exercise
under ignored `artifacts/autosave-design-2026-10-30/`. Those planning checks established declaration
consistency and local document references, not runtime behavior.

F1 and F2 are implemented in the isolated Foundation branch `codex/reusable-autosave` at
`artifacts/foundation-autosave/`. The two reviewed gaps are fixed: every pass preserves registration
order, and immutable controller activity notifies reservation, cutoff and actual slot release,
including disposed drain. Foundation retains the editor-wide slot until actual adapter settlement.

Required Foundation maintenance succeeded on `a12ea406144552a1b4bea2910e22ef482b8dcb06` in
[run 41036559918](https://github.com/orbyss-io/dotnet-foundation/actions/runs/41036559918), including
all deterministic validators, real three-engine browser scenarios and both image scans. The original
failed descriptor binding is retained in run 41035892852; both native source bindings were repaired
and focused local build/pack reproduced before retry. [PR 26](https://github.com/orbyss-io/dotnet-foundation/pull/26)
contains the qualified 0.3.12 candidate. Public publication is still pending at this checkpoint.

P1 provides optional exact declaration projection, the native autosave recipe and profile preflight,
conditional guidance through existing browser obligations, and safe original-identity wording.
Historical profiles remain usable without autosave; opting in rejects missing capability before
consumer edits. Partial/duplicate/tampered captures fail. No runtime is vendored into application code.

Local Program Kit Integrity passed in 9.4 seconds. The first Affected run retained restricted-host
failures (junction/process access, NuGet/npm DNS, wrong interpreter) and a timeout/overrun. Focused
normal-access reruns passed: composition tooling/model 74/157 seconds, PostgreSQL lifecycle 136
seconds, actual OpenAPI producer/client 26 seconds, installed native phases 5 seconds and shell
syntax 2 seconds. Existing prepared Spec Kit Python supplies the phase checks; no toolchain was
installed. Other selected knowledge, scaffold, profile and recovery checks passed. These are local
execution claims; native package CI and public-profile qualification remain required.

## Public release and qualified adoption

[Foundation Release 41041390021](https://github.com/orbyss-io/dotnet-foundation/actions/runs/41041390021)
succeeded at `dadf5fbe57ca903b16c2fe80f418b6da827a2bdd`; exact-main Windows/Linux CI also passed.
Actual public autosave module/declaration bytes match their tagged Git blobs exactly. Windows
checkout line endings are not the comparison authority.

[Program Kit maintenance 41044292564](https://github.com/orbyss-io/program-kit/actions/runs/41044292564)
qualified and promoted `p-3bec4dafa1f3` for Foundation 0.3.12. Native, browser, public Host,
producer/client, affected validation and both Host scans passed. [Support PR 65](https://github.com/orbyss-io/program-kit/pull/65)
is merged; [adoption PR 66](https://github.com/orbyss-io/program-kit/pull/66) carries the qualified default
and native package/installation CI. Its profile preflight confirms the exact public autosave capture.
All 17 earlier profile registrations remain intact. Only 31 Foundation runtime NuGet pins and Host
advance to 0.3.12; independent tools, Forms, Localization and tooling pins remain selected as before.

The existing maintenance workflow offers explicit profile-only dispatch, retaining tooling pins
and tooling locks while keeping all profile, producer/client, affected and security gates. Default
and scheduled full maintenance remain unchanged. Failed full-maintenance run 40849036855 remains
preserved; its unrelated Node/Spec Kit/type upgrades are not claimed qualified by this adoption.
The workflow's final affected checks passed in 56 seconds after its renamed-step fixture was updated
and its declared project-local schema dependencies were prepared.

dezaaglijst source, installed toolkit and selected dependencies remain untouched. D1/D2 require a
later requester discussion. This records Foundation publication and Program Kit main/profile adoption;
it claims neither a newly published Program Kit toolkit version nor actual consumer acceptance.

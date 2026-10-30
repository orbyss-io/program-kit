# Native browser autosave

Use this optional recipe when the application has selected autosave. Foundation owns the controller
and versioned module; the application owns save semantics and UI. Foundation 0.3.12 introduces
`foundation-browser-autosave/v1`. Check the exact qualified public profile rather than assuming that
installing Program Kit upgraded an existing consumer.

Export these installed example sources through the existing `asset_sources.py` owner, then run:

```powershell
python <exported-example>/check-profile.py --repository .
```

This read-only check verifies module and declaration hashes against the selected package/source
capture. Both absent means unsupported; partial or changed captures fail. It starts no application,
modifies no consumer and supplies no acceptance claim. Normal composition projection emits the exact
`foundation-browser/autosave.d.mts` only when the selected publisher contains the complete capability.
Runtime code remains served by the native feature, not copied into the application source tree.

After obtaining the selected native configuration, import its sibling module:

```typescript
import type * as Autosave from './foundation-browser/autosave.mjs';

// `selected` comes from loadBrowserPresentation at the application's configured native route.
const folder = selected.modulePath.slice(0, -'presentation.mjs'.length);
const native: unknown = await import(/* @vite-ignore */ folder + 'autosave.mjs');
if (typeof native !== 'object' || native === null
    || !('AUTOSAVE_CONTRACT' in native) || native.AUTOSAVE_CONTRACT !== 'foundation-browser-autosave/v1'
    || !('createAutosaveController' in native) || typeof native.createAutosaveController !== 'function') {
  throw new Error('The selected native autosave capability is unavailable.');
}
const create = native.createAutosaveController as typeof Autosave.createAutosaveController;
const saves = create({ enabled: editorSettings.autoSaveEnabled,
  intervalMilliseconds: editorSettings.autoSaveIntervalMilliseconds,
  operationTimeoutMilliseconds: editorSettings.saveTransportTimeoutMilliseconds,
  signal: editorLifetime.signal });
const stopActivity = saves.subscribeActivity(activity => {
  saveButton.disabled = activity.busy;
  renderActivity(activity); // Application-owned, localized busy/drain feedback.
  return undefined;
});
```

The runtime export check establishes the expected module interface; it does not establish server
authorization, receipt correctness or backend idempotency. Admit those at their actual owners.

Register one target per independently saved resource. Metadata precedes dependent children in
registration order. Adapter `admit` checks the current context; synchronous `capture` returns one
serialized immutable request; optional `prepare` uses the existing recovery owner. `write`, `lookup`
and optional identical `replay` use the shared signal and absolute monotonic expiry. Validate exact
request/receipt/target bindings before returning a confirmed result. A no-effect rejection requires
the reviewed server contract; generic 400/404/409 responses or missing receipts are insufficient.

Two useful application bindings are a version-conflict save, which includes the expected server
version and requires explicit comparison on conflict, and an overwrite save with no server-version
column. Both can use the same controller. The published Foundation source tests include independent
recording adapters for these policies; they are not production backend services or durable stores.

Use target `edited`, `save`, `reconcile` and `unsaved` instead of a second timer or pending-action state
machine. Register `unsaved` through the existing native unsaved-work registry. On visibility/session
uncertainty suspend the controller; fresh application admission still controls resumed operations.
On account change dispose it. Detach activity observation and observe disposal through the existing
component lifetime. Never wait for drain before hiding private content, and never describe drain as
proof of server termination. An unknown original attempt stays retained even after the slot is free.

Optional browser persistence remains application-owned. Restore only runtime-admitted, owner-bound
snapshots; a retained pending attempt starts unknown and restores without dispatch. Retire only the
confirmed generation. Keep input, tokens and receipt payloads out of logs/public diagnostics. Validate
real defaults and nondefault/invalid settings through their native activation owner.

First integration checks: manual/automatic collision; edit-7 confirmation preserving edit-8; same-key
replay after real commit response loss; missing status remaining unknown; deliberate conflict choices;
parent/child ordering; independent targets; cancellation versus actual drain; auth expiry without
background renewal; and existing recovery generation/retention behavior. Controller/model tests do
not substitute for the actual provider/browser journey or the agreed human review.

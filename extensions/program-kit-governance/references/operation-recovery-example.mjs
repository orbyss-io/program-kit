// Behavioral example, not an API schema or a generic HTTP status classifier.
// The consumer's reviewed operation contract must establish each named event.
// Server status lookup/replay still reauthorizes ownership and idempotency.
export function recovery(state, event) {
  if (event.kind === 'prepared') {
    if (state.operationId) throw new Error('Reconcile the retained operation before new preparation.');
    if (!event.operationId) throw new Error('The reviewed contract requires a stable original operation identity.');
    return { ...state, operationId: event.operationId, editable: false, reconcile: false, outcome: 'prepared' };
  }
  // Bind asynchronous outcomes to the exact retained request/operation. A stale
  // callback for an older action cannot clear or replace the active identity.
  if (event.operationId !== state.operationId || state.outcome === 'accepted') return state;
  if (event.kind === 'validation-rejected-without-effect' || event.kind === 'admission-expired-before-acceptance') {
    return { ...state, operationId: null, editable: true, reconcile: false, outcome: 'correction', focus: event.field ?? state.focus };
  }
  if (['response-lost', 'completion-unknown', 'receipt-unknown'].includes(event.kind)) {
    if (!state.operationId) throw new Error('Uncertain completion requires the retained operation identity.');
    return { ...state, editable: false, reconcile: true, outcome: 'unknown' };
  }
  if (event.kind === 'accepted-status') {
    return { ...state, editable: false, reconcile: false, outcome: 'accepted' };
  }
  // Unclassified HTTP 400/409/404 and missing receipts do not supply no-effect
  // authority. Keep retained identity; the caller uses safe fallback presentation.
  return state;
}

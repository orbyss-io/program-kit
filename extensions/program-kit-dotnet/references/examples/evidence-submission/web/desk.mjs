import {createFileSelection} from '/file-selection.mjs';
import {recovery} from '/operation-recovery.mjs';
import {presentFormErrors} from '/interactions.mjs';
import {createSignOutControl, unsavedWork} from '/native/presentation.mjs';
import {observeBffSession} from '/native/session.mjs';
import {prepareEvidence,acceptEvidence,findEvidence,readInputContract} from '/client.js';

const element = id => document.getElementById(id);
const form = document.querySelector('form');
let selection;
const registry = unsavedWork('/');
let dirty = false;
let confirmed;
let state = {operationId:null, outcome:'empty', editable:true};
let generation = 0;
let disposed = false;
const lifetime = new AbortController();
const unregister = registry.register({getState: () => state.operationId && state.outcome !== 'accepted' ? 'unknown' : dirty ? 'dirty' : 'clean'});
const signOut = createSignOutControl({surface:'/', mode:'when-unsaved', signOut:async () => {
  disposed = true; lifetime.abort();
  selection?.invalidate(); element('private-workspace').replaceChildren(); element('status')?.remove();
}});
const signOutButton = document.createElement('button');
signOutButton.textContent = 'Sign out'; signOutButton.type = 'button'; document.querySelector('header').append(signOutButton);
signOutButton.addEventListener('click', () => { void signOut.request({returnFocus:signOutButton}); });

function invalidate() {
  generation++; selection?.invalidate(); confirmed = undefined; dirty = true;
  if (element('confirm').open) element('confirm').close();
}
async function prepareFile() {
  if (!selection) return;
  invalidate();
  const current = generation;
  element('selection').textContent = 'Preparing file…';
  const file = element('file').files[0];
  const date = element('date').value;
  const result = await selection.select(file, date);
  if (disposed || current !== generation) return;
  element('selection').textContent = result.kind === 'ready' ? `${result.name} is ready for review.` : result.message ?? 'Choose a file and date.';
  if (result.kind === 'failed') element('file').value = '';
}
element('file').addEventListener('change', prepareFile);
element('date').addEventListener('change', prepareFile);
element('title').addEventListener('input', () => { dirty = true; confirmed = undefined; });
form.addEventListener('submit', event => {
  event.preventDefault();
  if (state.operationId) return;
  const errors = {};
  if (!element('title').value.trim()) errors.title = 'Enter an evidence title.';
  if (!element('date').value) errors.date = 'Choose an evidence date.';
  if (selection?.current().kind !== 'ready') errors.file = 'Choose a prepared text file.';
  presentFormErrors(form, errors);
  if (Object.keys(errors).length) return;
  const title = element('title').value;
  try { confirmed = selection.confirm(title); }
  catch {
    const errors = {title:'Check the title and current file before review.'};
    presentFormErrors(form, errors);
    return;
  }
  element('preview').textContent = `${confirmed.title} · ${confirmed.date} · ${selection.current().name}`;
  element('confirm').showModal();
});
element('cancel').addEventListener('click', () => { confirmed = undefined; element('confirm').close(); element('review').focus(); });
function accepted(receipt) {
  if (disposed || state.outcome === 'accepted') return;
  state = recovery(state, {kind:'accepted-status', operationId:receipt.id}); dirty = false;
  element('status').textContent = `${receipt.desk}: ${receipt.title} accepted for review.`;
  element('reconcile').hidden = true; element('new').hidden = false; element('empty').hidden = true;
  const item = document.createElement('li'); item.textContent = `${receipt.title} · ${receipt.date} · ${receipt.hash.slice(0,12)}`;
  element('receipts').append(item);
}
element('accept').addEventListener('click', async () => {
  if (!confirmed || state.operationId) return;
  const packet = confirmed; confirmed = undefined; element('confirm').close();
  element('review').disabled = true; element('status').textContent = 'Submitting confirmed evidence…';
  const deadline = AbortSignal.timeout(10000);
  const signal = AbortSignal.any([deadline,lifetime.signal]);
  try {
    const prepared = await prepareEvidence(packet, signal);
    if (disposed) return;
    state = recovery(state, {kind:'prepared', operationId:prepared.id});
    const result = await acceptEvidence(prepared.id, signal);
    accepted(result);
  } catch {
    if (disposed) return;
    if (state.operationId) {
      state = recovery(state, {kind:'response-lost', operationId:state.operationId});
      element('status').textContent = 'Completion is unknown. Check the retained submission before starting another.';
      element('reconcile').hidden = false;
    } else {
      element('status').textContent = 'Preparation was not observed. No acceptance request was sent. Keep your input and try again.';
      element('review').disabled = false;
    }
  }
});
element('reconcile').addEventListener('click', async () => {
  const identity = state.operationId;
  const deadline = AbortSignal.timeout(10000);
  const signal = AbortSignal.any([deadline,lifetime.signal]);
  try {
    const result = await findEvidence(identity, signal);
    if (disposed || state.operationId !== identity) return;
    if (result.accepted) accepted(result);
    else element('status').textContent = 'The retained submission is prepared. Acceptance is not established; no new submission was sent.';
  } catch { if (!disposed) element('status').textContent = 'Status is unavailable. The original submission is still retained.'; }
});
element('new').addEventListener('click', () => {
  state = {operationId:null, outcome:'empty', editable:true}; invalidate(); form.reset();
  element('review').disabled = false; element('new').hidden = true; element('title').focus();
});
const observer = observeBffSession({privateRoots:[element('private-workspace')], userPath:'/bff/user', onObservation(observation) {
  if (observation.state !== 'authenticated') {
    disposed = true; lifetime.abort();
    invalidate(); unregister(); element('private-workspace').replaceChildren();
    const message = document.createElement('p'); message.textContent = 'Session unavailable. Return through the workspace entry.';
    document.querySelector('main').append(message);
  }
}});
await observer.ready;
try {
  const signal = AbortSignal.any([AbortSignal.timeout(10000),lifetime.signal]);
  const contract = await readInputContract(signal);
  if (!disposed) {
    selection = createFileSelection({maximumBytes:contract.maximumContentBytes,maximumTitleLength:contract.maximumTitleLength});
    element('title').maxLength = contract.maximumTitleLength;
    element('input-contract').textContent = `Only fictional UTF-8 text, up to ${contract.maximumContentBytes} bytes. Confirmed content stays in this disposable fixture.`;
    if (element('file').files.length) void prepareFile();
  }
} catch { if (!disposed) element('status').textContent = 'Input limits are unavailable. Reload the workspace before submission.'; }
window.addEventListener('pagehide', () => { disposed = true; lifetime.abort(); generation++; selection?.dispose(); observer.dispose(); unregister(); signOut.dispose(); });

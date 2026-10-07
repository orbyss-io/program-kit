// Native dialog owns modal semantics and Escape; keep Tab at the content edges and restore focus.
export function wireDialogs(root = document) {
  const cleanups = [];
  for (const opener of root.querySelectorAll('[data-pk-dialog]')) {
    const dialog = root.getElementById(opener.dataset.pkDialog);
    if (!(dialog instanceof HTMLDialogElement)) throw new Error('Missing native dialog');
    const open = () => dialog.showModal();
    const close = () => opener.focus();
    const wrap = event => {
      if (event.key !== 'Tab') return;
      const targets = [...dialog.querySelectorAll('a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]')]
        .filter(el => !el.disabled && el.tabIndex >= 0 && el.getClientRects().length);
      const first = targets[0], last = targets.at(-1);
      if (!first) { event.preventDefault(); dialog.focus(); return; }
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    opener.addEventListener('click', open);
    dialog.addEventListener('close', close);
    dialog.addEventListener('keydown', wrap);
    cleanups.push(() => { opener.removeEventListener('click', open); dialog.removeEventListener('close', close); dialog.removeEventListener('keydown', wrap); });
  }
  return () => cleanups.forEach(cleanup => cleanup());
}
if (typeof document !== 'undefined') wireDialogs();

// Consumers supply admitted, localized messages. No backend rule or retry is inferred here.
export function setFieldError(input, message = '') {
  if (typeof message !== 'string') throw new Error('Field message must be admitted text');
  const error = input.ownerDocument.getElementById(`${input.id}-error`);
  if (!error) throw new Error('Field requires an associated error slot');
  const descriptions = new Set((input.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
  error.textContent = message; error.hidden = !message;
  if (message) { input.setAttribute('aria-invalid', 'true'); descriptions.add(error.id); }
  else { input.removeAttribute('aria-invalid'); descriptions.delete(error.id); }
  if (descriptions.size) input.setAttribute('aria-describedby', [...descriptions].join(' '));
  else input.removeAttribute('aria-describedby');
}

export function presentFormErrors(form, errors = {}) {
  const summary = form.querySelector('[data-pk-error-summary]');
  if (!summary) throw new Error('Form requires an error summary slot');
  const list = summary.querySelector('ul'); list.replaceChildren();
  for (const input of form.querySelectorAll('input[id],select[id],textarea[id]')) {
    if (input.ownerDocument.getElementById(`${input.id}-error`)) setFieldError(input);
  }
  for (const [identity, message] of Object.entries(errors)) {
    const input = form.elements.namedItem(identity);
    if (!input || !input.id || !form.contains(input)) throw new Error('Error must reference an owned field');
    setFieldError(input, message);
    const link = form.ownerDocument.createElement('a');
    link.href = `#${encodeURIComponent(input.id)}`; link.textContent = message;
    link.addEventListener('click', event => { event.preventDefault(); input.focus(); });
    const item = form.ownerDocument.createElement('li'); item.append(link); list.append(item);
  }
  summary.hidden = !list.children.length;
  // Focus owns the announcement; do not also create one assertive alert per field.
  if (!summary.hidden) summary.focus();
}

export function setOperationState(form, state, message = '') {
  if (typeof message !== 'string') throw new Error('Operation message must be admitted text');
  if (!['idle', 'pending', 'success', 'validation', 'failure', 'conflict', 'unknown'].includes(state)) throw new Error('Unknown operation state');
  const status = form.querySelector('[data-pk-operation-status]');
  if (!status) throw new Error('Operation requires a status slot');
  form.dataset.pkState = state; form.setAttribute('aria-busy', String(state === 'pending'));
  status.className = state === 'failure' ? 'pk-status pk-status-error' :
    ['conflict', 'unknown'].includes(state) ? 'pk-status pk-status-warning' : state === 'success' ? 'pk-status pk-status-success' : '';
  status.textContent = message;
}

const operationBindings = new WeakMap();
export function bindOperation(form, submit, messages = {}) {
  operationBindings.get(form)?.();
  let pending = false, disposed = false;
  let controls = [];
  const release = () => controls.forEach(([control, disabled]) => { control.disabled = disabled; });
  const run = async event => {
    event.preventDefault();
    if (pending || disposed) return;
    pending = true;
    controls = [...form.querySelectorAll('button[type="submit"],input[type="submit"]')].map(control => [control, control.disabled]);
    controls.forEach(([control]) => { control.disabled = true; });
    try {
      presentFormErrors(form);
      setOperationState(form, 'pending', messages.pending || 'Saving…');
      const result = await submit(new FormData(form));
      if (disposed) return;
      if (!result || !['success', 'validation', 'failure', 'conflict', 'unknown'].includes(result.state)) throw new Error('Adapter must establish an operation outcome');
      if (result.state === 'validation' && (!result.errors || Array.isArray(result.errors) || typeof result.errors !== 'object' ||
          !Object.keys(result.errors).length || Object.values(result.errors).some(message => typeof message !== 'string' || !message.trim()))) throw new Error('Validation requires admitted field messages');
      if (result.state === 'validation') presentFormErrors(form, result.errors);
      const fallback = { success: 'Completed.', validation: '', failure: 'The action could not be completed. Follow the available recovery steps.',
        conflict: 'The item changed. Review the latest version before continuing.',
        unknown: 'We couldn’t confirm whether the change was saved. Check its status before trying again.' };
      setOperationState(form, result.state, result.message || messages[result.state] || fallback[result.state]);
    } catch {
      if (!disposed) setOperationState(form, 'unknown', messages.unknown || 'We couldn’t confirm whether the change was saved. Check its status before trying again.');
    } finally {
      pending = false;
      if (!disposed) release();
    }
  };
  form.addEventListener('submit', run);
  const dispose = () => {
    disposed = true; form.removeEventListener('submit', run); release(); form.removeAttribute('aria-busy');
    if (operationBindings.get(form) === dispose) operationBindings.delete(form);
  };
  operationBindings.set(form, dispose);
  return dispose;
}

// Local gallery only. Real forms supply their own rule/transport adapter to bindOperation.
if (typeof document !== 'undefined') {
  for (const form of document.querySelectorAll('[data-pk-demo-form]')) {
    bindOperation(form, async data => {
      if (!String(data.get('example-name') || '').trim()) return { state: 'validation', errors: { 'example-name': 'Enter a name.' } };
      return { state: 'success', message: 'Example saved. This is simulated gallery feedback.' };
    });
  }
}

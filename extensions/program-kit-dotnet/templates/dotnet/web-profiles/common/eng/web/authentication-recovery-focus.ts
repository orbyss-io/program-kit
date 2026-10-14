/**
 * Select an application-owned recovery heading once its document is visible and active.
 * Existing user-selected controls retain focus. Dynamic owners must dispose this binding
 * before replacing the heading; pending static bindings also dispose on page departure.
 */
export function focusAuthenticationRecovery(heading: HTMLElement): () => void {
  const document = heading.ownerDocument;
  const window = document.defaultView;
  if (!window) return () => undefined;
  let disposed = false;
  let activationFrame: number | undefined;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    if (activationFrame !== undefined) window.cancelAnimationFrame(activationFrame);
    window.removeEventListener('focus', activated);
    window.removeEventListener('pagehide', dispose);
    document.removeEventListener('visibilitychange', activated);
    document.removeEventListener('focusin', selected);
  };
  const neutral = () => !document.activeElement || document.activeElement === document.body
    || document.activeElement === document.documentElement || document.activeElement === heading;
  const selected = () => { if (!neutral()) dispose(); };
  const attempt = () => {
    if (disposed) return;
    if (!heading.isConnected || !neutral()) { dispose(); return; }
    if (document.visibilityState !== 'visible' || !document.hasFocus()) return;
    if (document.activeElement !== heading) heading.focus({ preventScroll: true });
    if (document.activeElement === heading) dispose();
  };
  // One rendering frame lets native activation settle; events coalesce and disposal
  // cancels pending work. This is not an elapsed-time retry loop.
  const activated = () => {
    if (disposed || activationFrame !== undefined) return;
    activationFrame = window.requestAnimationFrame(() => { activationFrame = undefined; attempt(); });
  };
  window.addEventListener('focus', activated);
  window.addEventListener('pagehide', dispose);
  document.addEventListener('visibilitychange', activated);
  document.addEventListener('focusin', selected);
  // Newly rendered recovery content also needs its first rendering boundary. Firefox
  // can refuse synchronous focus even when the new document already reports active.
  activated();
  return dispose;
}

// The static application example loads this as its external owner-local module. Dynamic
// views call the same function after rendering and retain its disposal callback.
if (typeof document !== 'undefined') {
  const recoveryHeading = document.querySelector<HTMLElement>('h1[data-authentication-recovery-heading]');
  if (recoveryHeading) focusAuthenticationRecovery(recoveryHeading);
}

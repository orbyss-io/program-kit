export interface FoundationBffSession {
  authenticated: boolean;
}

export interface ProgramKitAntiforgeryToken {
  headerName: 'X-CSRF-TOKEN';
  formFieldName: '__RequestVerificationToken';
  requestToken: string;
}

export interface FoundationBffLogoutOptions {
  antiforgeryPath?: string;
  logoutPath?: string;
  sessionPath?: string;
  signedOutPath?: string;
  popupName?: string;
  localTerminationTimeoutMilliseconds?: number;
  signal?: AbortSignal;
  /** Clear private views and cancel their work once the logout form has been submitted. */
  onDispatched?: () => void;
}

export interface FoundationBffLogoutResult {
  /** An unconfirmed observation never establishes that the local session survived logout. */
  localTermination: 'confirmed' | 'unconfirmed';
}

function localPath(value: string, label: string): string {
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) {
    throw new Error(`${label} must be an application-local absolute path.`);
  }
  return value;
}

async function withinBudget<T>(operation: () => Promise<T>, deadline: number, signal: AbortSignal): Promise<T> {
  signal.throwIfAborted();
  if (performance.now() >= deadline) throw new DOMException('The logout observation budget expired.', 'TimeoutError');
  let interrupted: () => void = () => undefined;
  const cancellation = new Promise<never>((_, reject) => {
    interrupted = () => reject(signal.reason);
    signal.addEventListener('abort', interrupted, { once: true });
  });
  try {
    const result = await Promise.race([operation(), cancellation]);
    signal.throwIfAborted();
    if (performance.now() >= deadline) throw new DOMException('The logout observation budget expired.', 'TimeoutError');
    return result;
  } finally {
    signal.removeEventListener('abort', interrupted);
  }
}

async function waitForLocalTermination(path: string, deadline: number, signal: AbortSignal): Promise<void> {
  while (true) {
    const response = await withinBudget(() => fetch(path, {
      credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal,
    }), deadline, signal);
    if (!response.ok) throw new Error('The BFF session endpoint did not return a successful response.');
    const session: unknown = await withinBudget(() => response.json(), deadline, signal);
    if (typeof session !== 'object' || session === null || !('authenticated' in session)
      || typeof session.authenticated !== 'boolean') throw new Error('The BFF session response does not match the managed contract.');
    if (session.authenticated === false) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      await withinBudget(() => new Promise<void>(resolve => {
        timer = setTimeout(resolve, Math.min(50, Math.max(0, deadline - performance.now())));
      }), deadline, signal);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
    }
  }
}

/**
 * Invoke directly from a trusted user gesture. It opens provider logout in a separate top-level
 * context, then navigates only after observing local termination. After dispatch, an interrupted
 * observation returns unconfirmed: keep private content cleared and offer public recovery without
 * claiming sign-out. Provider navigation continues independently. Use an application-owned landing.
 */
export async function beginFoundationBffLogout(
  options: FoundationBffLogoutOptions = {},
): Promise<FoundationBffLogoutResult> {
  const antiforgeryPath = localPath(options.antiforgeryPath ?? '/bff/antiforgery', 'antiforgeryPath');
  const logoutPath = localPath(options.logoutPath ?? '/bff/logout', 'logoutPath');
  const sessionPath = localPath(options.sessionPath ?? '/bff/user', 'sessionPath');
  const signedOutPath = localPath(options.signedOutPath ?? '/bff/signed-out', 'signedOutPath');
  const popupName = options.popupName ?? 'program-kit-provider-logout';
  const timeout = options.localTerminationTimeoutMilliseconds ?? 5000;
  if (!Number.isFinite(timeout) || timeout <= 0 || timeout > 2_147_483_647) {
    throw new Error('The logout observation budget must be a finite positive timer duration.');
  }
  options.signal?.throwIfAborted();
  const deadline = performance.now() + timeout;
  const budget = new AbortController();
  const signal = options.signal ? AbortSignal.any([budget.signal, options.signal]) : budget.signal;
  const providerWindow = window.open('about:blank', popupName);
  if (!providerWindow) throw new Error('Provider logout requires a user-initiated top-level window.');
  const timer = setTimeout(() => budget.abort(new DOMException('The logout observation budget expired.', 'TimeoutError')),
    Math.max(0, deadline - performance.now()));
  let dispatched = false;

  try {
    const tokenResponse = await withinBudget(() => fetch(antiforgeryPath, {
      credentials: 'same-origin',
      cache: 'no-store',
      redirect: 'error',
      signal,
    }), deadline, signal);
    if (!tokenResponse.ok) throw new Error('The BFF antiforgery endpoint did not succeed.');
    const token: unknown = await withinBudget(() => tokenResponse.json(), deadline, signal);
    if (
      typeof token !== 'object' || token === null
      || !('headerName' in token) || !('formFieldName' in token) || !('requestToken' in token)
      || token.headerName !== 'X-CSRF-TOKEN'
      || token.formFieldName !== '__RequestVerificationToken'
      || typeof token.requestToken !== 'string' || !token.requestToken
    ) {
      throw new Error('The BFF antiforgery response does not match the managed contract.');
    }

    const form = document.createElement('form');
    form.method = 'post';
    form.action = logoutPath;
    form.target = popupName;
    form.hidden = true;
    const field = document.createElement('input');
    field.type = 'hidden';
    field.name = token.formFieldName;
    field.value = token.requestToken;
    form.append(field);
    document.body.append(form);
    try {
      signal.throwIfAborted();
      if (performance.now() >= deadline) throw new DOMException('The logout observation budget expired.', 'TimeoutError');
      form.submit();
      dispatched = true;
    } finally { form.remove(); }
    options.onDispatched?.();

    await waitForLocalTermination(sessionPath, deadline, signal);
    window.location.assign(`${signedOutPath}?remote=pending`);
    return { localTermination: 'confirmed' };
  } catch (error) {
    if (dispatched) return { localTermination: 'unconfirmed' };
    providerWindow.close();
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

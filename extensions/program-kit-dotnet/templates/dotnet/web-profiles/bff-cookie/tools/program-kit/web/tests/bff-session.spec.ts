import { expect, test } from '@playwright/test';
import { beginFoundationBffLogout } from '../bff-session.js';

const originalWindow = Object.getOwnPropertyDescriptor(globalThis, 'window');
const originalDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
const originalFetch = Object.getOwnPropertyDescriptor(globalThis, 'fetch');
const originalPerformance = Object.getOwnPropertyDescriptor(globalThis, 'performance');
const originalDateNow = Date.now;

function restore(name: 'window' | 'document' | 'fetch', descriptor: PropertyDescriptor | undefined) {
  if (descriptor) Object.defineProperty(globalThis, name, descriptor);
  else Reflect.deleteProperty(globalThis, name);
}

test.afterEach(() => {
  restore('window', originalWindow);
  restore('document', originalDocument);
  restore('fetch', originalFetch);
  if (originalPerformance) Object.defineProperty(globalThis, 'performance', originalPerformance);
  Date.now = originalDateNow;
});

test('rejects non-local contract paths before opening provider logout', async () => {
  await expect(beginFoundationBffLogout({ logoutPath: 'https://attacker.example/logout' }))
    .rejects.toThrow('logoutPath must be an application-local absolute path.');
});

test('submits the managed antiforgery form and waits for local termination', async () => {
  const requests: string[] = [];
  const assignments: string[] = [];
  const popup = { close: () => { throw new Error('successful logout must not close the provider window'); } };
  const field = { type: '', name: '', value: '' };
  let submitted = false;
  let removed = false;
  const form = {
    method: '',
    action: '',
    target: '',
    hidden: false,
    append: (value: unknown) => expect(value).toBe(field),
    submit: () => { submitted = true; },
    remove: () => { removed = true; },
  };
  const documentStub = {
    createElement: (name: string) => {
      if (name === 'form') return form;
      if (name === 'input') return field;
      throw new Error(`unexpected element ${name}`);
    },
    body: { append: (value: unknown) => expect(value).toBe(form) },
  };
  const windowStub = {
    open: (url: string, name: string) => {
      expect(url).toBe('about:blank');
      expect(name).toBe('program-kit-provider-logout');
      return popup;
    },
    location: { assign: (value: string) => assignments.push(value) },
  };
  const fetchStub = async (input: string | URL | Request): Promise<Response> => {
    const path = String(input);
    requests.push(path);
    if (path === '/bff/antiforgery') {
      return Response.json({
        headerName: 'X-CSRF-TOKEN',
        formFieldName: '__RequestVerificationToken',
        requestToken: 'governed-token',
      });
    }
    if (path === '/bff/user') return Response.json({ authenticated: false });
    throw new Error(`unexpected request ${path}`);
  };
  Object.defineProperty(globalThis, 'window', { value: windowStub, configurable: true });
  Object.defineProperty(globalThis, 'document', { value: documentStub, configurable: true });
  Object.defineProperty(globalThis, 'fetch', { value: fetchStub, configurable: true });

  expect(await beginFoundationBffLogout()).toEqual({ localTermination: 'confirmed' });

  expect(requests).toEqual(['/bff/antiforgery', '/bff/user']);
  expect(form).toMatchObject({
    method: 'post',
    action: '/bff/logout',
    target: 'program-kit-provider-logout',
    hidden: true,
  });
  expect(field).toEqual({
    type: 'hidden',
    name: '__RequestVerificationToken',
    value: 'governed-token',
  });
  expect(submitted).toBe(true);
  expect(removed).toBe(true);
  expect(assignments).toEqual(['/bff/signed-out?remote=pending']);
});

function logoutFixture(fetchStub: typeof fetch) {
  const state = { submitted: false, removed: false, closed: false, cleared: false, assignments: [] as string[] };
  const form = {
    method: '', action: '', target: '', hidden: false, append: () => undefined,
    submit: () => { state.submitted = true; }, remove: () => { state.removed = true; },
  };
  Object.defineProperty(globalThis, 'window', { configurable: true, value: {
    open: () => ({ close: () => { state.closed = true; } }),
    location: { assign: (value: string) => state.assignments.push(value) },
  } });
  Object.defineProperty(globalThis, 'document', { configurable: true, value: {
    createElement: (name: string) => name === 'form' ? form : { type: '', name: '', value: '' },
    body: { append: () => undefined },
  } });
  Object.defineProperty(globalThis, 'fetch', { configurable: true, value: fetchStub });
  return state;
}

function tokenResponse(): Response {
  return Response.json({ headerName: 'X-CSRF-TOKEN', formFieldName: '__RequestVerificationToken', requestToken: 'test-token' });
}

test('aborts a hanging antiforgery request before dispatch', async () => {
  let requestSignal: AbortSignal | null | undefined;
  const state = logoutFixture(async (_, options) => {
    requestSignal = options?.signal;
    // Even a stalled transport that ignores abort cannot retain the caller forever.
    return await new Promise<Response>(() => undefined);
  });
  const started = performance.now();
  await expect(beginFoundationBffLogout({ localTerminationTimeoutMilliseconds: 40 })).rejects.toMatchObject({ name: 'TimeoutError' });
  expect(performance.now() - started).toBeLessThan(2000);
  expect(requestSignal?.aborted).toBe(true);
  expect(state).toMatchObject({ submitted: false, closed: true, assignments: [] });
});

test('uses one remaining monotonic budget for antiforgery and acknowledgement', async () => {
  let elapsed = 0;
  Object.defineProperty(globalThis, 'performance', { configurable: true, value: { now: () => elapsed } });
  const signals: Array<AbortSignal | null | undefined> = [];
  const state = logoutFixture(async (input, options) => {
    signals.push(options?.signal);
    if (String(input) === '/bff/antiforgery') {
      elapsed = 90;
      Date.now = () => -1_000_000; // A changed wall clock cannot renew the budget.
      return tokenResponse();
    }
    elapsed = 101;
    return Response.json({ authenticated: false });
  });
  expect(await beginFoundationBffLogout({ localTerminationTimeoutMilliseconds: 100,
    onDispatched: () => { state.cleared = true; },
  })).toEqual({ localTermination: 'unconfirmed' });
  expect(signals).toHaveLength(2);
  expect(signals[1]).toBe(signals[0]);
  expect(state).toMatchObject({ submitted: true, removed: true, cleared: true, closed: false, assignments: [] });
});

test('caller cancellation before submission closes the unused provider window', async () => {
  const caller = new AbortController();
  const state = logoutFixture(async () => {
    caller.abort();
    return tokenResponse();
  });
  await expect(beginFoundationBffLogout({ signal: caller.signal })).rejects.toMatchObject({ name: 'AbortError' });
  expect(state).toMatchObject({ submitted: false, closed: true, assignments: [] });
});

test('caller cancellation after submission leaves cleared private state and reports unknown acknowledgement', async () => {
  const caller = new AbortController();
  const state = logoutFixture(async () => tokenResponse());
  expect(await beginFoundationBffLogout({ signal: caller.signal, onDispatched: () => {
    state.cleared = true; caller.abort();
  } })).toEqual({ localTermination: 'unconfirmed' });
  expect(state).toMatchObject({ submitted: true, removed: true, cleared: true, closed: false, assignments: [] });
});

for (const failure of ['unavailable', 'malformed', 'fetch-stalled', 'body-stalled'] as const) {
  test(`post-dispatch ${failure} session observation never claims sign-out or interrupts provider navigation`, async () => {
    const state = logoutFixture(async input => {
      if (String(input) === '/bff/antiforgery') return tokenResponse();
      if (failure === 'unavailable') throw new TypeError('Test-only unavailable transport.');
      if (failure === 'malformed') return Response.json({ authenticated: 'false' });
      if (failure === 'fetch-stalled') return await new Promise<Response>(() => undefined);
      const response = Response.json({ authenticated: false });
      response.json = () => new Promise<unknown>(() => undefined);
      return response;
    });
    expect(await beginFoundationBffLogout({ localTerminationTimeoutMilliseconds: 40,
      onDispatched: () => { state.cleared = true; },
    })).toEqual({ localTermination: 'unconfirmed' });
    expect(state).toMatchObject({ submitted: true, cleared: true, closed: false, assignments: [] });
  });
}

test('confirmed local deletion does not wait for or assert provider completion', async () => {
  const state = logoutFixture(async input => String(input) === '/bff/antiforgery'
    ? tokenResponse() : Response.json({ authenticated: false }));
  expect(await beginFoundationBffLogout({ signedOutPath: '/public/session-ended',
    onDispatched: () => { state.cleared = true; },
  })).toEqual({ localTermination: 'confirmed' });
  expect(state).toMatchObject({ cleared: true, closed: false, assignments: ['/public/session-ended?remote=pending'] });
});

test('popup refusal and invalid or cancelled budgets do not submit logout', async () => {
  let opened = 0;
  Object.defineProperty(globalThis, 'window', { configurable: true, value: { open: () => { opened++; return null; } } });
  for (const timeout of [0, -1, Infinity, NaN]) {
    await expect(beginFoundationBffLogout({ localTerminationTimeoutMilliseconds: timeout })).rejects.toThrow('finite positive timer duration');
  }
  const caller = new AbortController(); caller.abort();
  await expect(beginFoundationBffLogout({ signal: caller.signal })).rejects.toMatchObject({ name: 'AbortError' });
  expect(opened).toBe(0);
  await expect(beginFoundationBffLogout()).rejects.toThrow('user-initiated top-level window');
  expect(opened).toBe(1);
});

test('closes the provider window when the antiforgery contract fails', async () => {
  let closed = false;
  const windowStub = {
    open: () => ({ close: () => { closed = true; } }),
    location: { assign: () => { throw new Error('failed logout must not navigate'); } },
  };
  Object.defineProperty(globalThis, 'window', { value: windowStub, configurable: true });
  Object.defineProperty(globalThis, 'fetch', {
    value: async () => Response.json({ requestToken: '' }),
    configurable: true,
  });

  await expect(beginFoundationBffLogout()).rejects.toThrow(
    'The BFF antiforgery response does not match the managed contract.',
  );
  expect(closed).toBe(true);
});

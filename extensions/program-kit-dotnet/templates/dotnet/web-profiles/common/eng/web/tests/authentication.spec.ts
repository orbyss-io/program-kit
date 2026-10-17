import { expect, type Browser, type BrowserContext, type Download, type Page, test } from '@playwright/test';
import { personas } from '../persona-fixture.js';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

// Set this in the test worker as well as the runner: provider documents and credential assertions
// must not become an automatic failure DOM artifact. Keep only finite diagnostic categories.
process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';
test.afterEach(async ({}, info) => {
  for (const error of info.errors) {
    const message = info.status === 'timedOut'
      ? `Test timeout of ${info.timeout}ms exceeded. Private authentication payload suppressed.`
      : /^(?:Error: )?browserType\.launch:/.test(error.message ?? '')
        ? 'Error: browserType.launch: Private authentication payload suppressed.'
        : /^(?:Error: )?expect\(/.test(error.message ?? '')
          ? 'Error: expect(private authentication assertion).toPass(); payload suppressed.'
          : 'Private authentication check failed; payload suppressed.';
    for (const key of Object.keys(error)) Reflect.deleteProperty(error, key);
    // Reporters accept the public thrown-value shape. A message would also trigger
    // Playwright's automatic error-context document despite its DOM opt-out.
    error.value = message;
  }
});

const identityAuthority = process.env.PROGRAMKIT_IDENTITY_AUTHORITY ?? 'http://localhost:8080/realms/program-kit';
const identityOrigin = new URL(identityAuthority).origin;

function nativeLogoutLanding(baseURL: string): string {
  const directory = new URL('../compositions/', import.meta.url);
  const contracts: { origins?: { application?: string }; routes?: { signedOutCallback?: { successLocation?: string } } }[] =
    existsSync(directory) ? readdirSync(directory).filter(name => name.endsWith('.json'))
      .map(name => JSON.parse(readFileSync(new URL(name, directory), 'utf8'))) : [];
  const selected = contracts.filter(contract => contract.origins?.application === new URL(baseURL).origin);
  if (contracts.length && selected.length !== 1) throw new Error('Select one emitted native browser contract.');
  const contract = selected[0] ?? JSON.parse(readFileSync(new URL('../web-contract.json', import.meta.url), 'utf8'));
  const path: unknown = contract.routes?.signedOutCallback?.successLocation;
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//'))
    throw new Error('The native signed-out callback contract has no literal local destination.');
  const destination = new URL(path, baseURL);
  if (destination.origin !== new URL(baseURL).origin) throw new Error('The native logout destination is not local.');
  return destination.href;
}


// Only the owner UI and its module are fixture documents. All BFF/Keycloak requests remain native.
// Transpile the shipped adapter itself, rather than rebuilding its protocol in the journey test.
const logoutAdapter = stripTypeScriptTypes(readFileSync(new URL('../bff-session.ts', import.meta.url), 'utf8'), { mode: 'strip' });
const recoveryFocus = stripTypeScriptTypes(readFileSync(new URL('../authentication-recovery-focus.ts', import.meta.url), 'utf8'), { mode: 'strip' });

async function installLogoutPresentation(context: BrowserContext, baseURL: string): Promise<string> {
  const entry = new URL('/__program-kit-owner-logout', baseURL).href;
  const landing = '/__program-kit-owner-session-ended';
  const modulePath = '/__program-kit-owner-logout.js';
  const adapterPath = '/__program-kit-shipped-bff-session.js';
  const focusPath = '/__program-kit-authentication-recovery-focus.js';
  // Native forwarding observation is confined to these fictional owner documents.
  // Neither the BFF/provider documents nor private values become diagnostic inputs.
  await context.addInitScript(({ origin, paths }) => {
    if (location.origin !== origin || !paths.includes(location.pathname)) return;
    const trace = { headingFocusCalled:false, callDocumentFocused:false, headingEverSelected:false,
      headingLastSelected:false, windowFocusSeen:false, visibilityEventSeen:false,
      frameExecuted:false, frameDocumentFocused:false };
    Object.defineProperty(window, '__programKitRecoveryFocusTrace', { value:trace });
    const nativeFocus = HTMLElement.prototype.focus;
    HTMLElement.prototype.focus = function (...args) {
      const heading = this === document.querySelector('main > h1');
      if (heading) { trace.headingFocusCalled = true; trace.callDocumentFocused = document.hasFocus(); }
      Reflect.apply(nativeFocus, this, args);
      if (heading) {
        trace.headingLastSelected = document.activeElement === this;
        trace.headingEverSelected ||= trace.headingLastSelected;
      }
    };
    const nativeFrame = window.requestAnimationFrame;
    window.requestAnimationFrame = callback => nativeFrame.call(window, time => {
      trace.frameExecuted = true; trace.frameDocumentFocused = document.hasFocus(); callback(time);
    });
    window.addEventListener('focus', event => { if (event.target === window) trace.windowFocusSeen = true; });
    document.addEventListener('visibilitychange', () => { trace.visibilityEventSeen = true; });
  }, { origin:new URL(baseURL).origin, paths:[new URL(entry).pathname, landing] });
  await context.route(new URL(adapterPath, baseURL).href, route => route.fulfill({ contentType: 'text/javascript', body: logoutAdapter }));
  await context.route(new URL(focusPath, baseURL).href, route => route.fulfill({ contentType: 'text/javascript', body: recoveryFocus }));
  await context.route(new URL(modulePath, baseURL).href, route => route.fulfill({ contentType: 'text/javascript', body: `
    import { beginFoundationBffLogout } from '${adapterPath}';
    import { focusAuthenticationRecovery } from '${focusPath}';
    const root = document.querySelector('main');
    let disposeRecoveryFocus = () => {};
    function recovery(title, copy) {
      disposeRecoveryFocus();
      root.replaceChildren();
      const heading = document.createElement('h1'); heading.textContent = title; heading.tabIndex = -1;
      const message = document.createElement('p'); message.textContent = copy; message.setAttribute('role', 'status');
      const signIn = document.createElement('a'); signIn.textContent = 'Sign in'; signIn.href = '/bff/login?returnUrl=/';
      root.append(heading, message, signIn); disposeRecoveryFocus = focusAuthenticationRecovery(heading);
    }
    async function observeSession() {
      const reply = await fetch('/bff/user', {credentials:'same-origin', cache:'no-store', redirect:'error', signal:AbortSignal.timeout(5000)});
      if (!reply.ok) throw new Error('Native session observation failed.');
      const session = await reply.json();
      if (typeof session.authenticated !== 'boolean') throw new Error('Native session contract failed.');
      return session.authenticated;
    }
    if (location.pathname === '${landing}') {
      if (await observeSession() === false) recovery('Your application session has ended', 'This application has no active session. Provider sign-out has not been confirmed.');
      else recovery('Your application session is still active', 'You can return to your workspace or try signing out again.');
    } else {
      document.querySelector('button').addEventListener('click', () => {
        void (async () => {
          const result = await beginFoundationBffLogout({signedOutPath:'${landing}', onDispatched:() => recovery('Checking your application session', 'Private content has been cleared.')});
          if (result.localTermination === 'unconfirmed') {
            recovery('Your session status is unconfirmed', 'Private content remains cleared. Check your application session before claiming sign-out.');
            const check = document.createElement('button'); check.type = 'button'; check.textContent = 'Check session';
            check.addEventListener('click', () => { void observeSession().then(authenticated => {
              if (!authenticated) location.assign('${landing}');
              else recovery('Your application session is still active', 'You can return to your workspace or try signing out again.');
            }).catch(() => { root.querySelector('[role=status]').textContent = 'Session status remains unconfirmed. You can check again.'; }); });
            root.append(check);
          }
        })().catch(() => { document.querySelector('[role=status]').textContent = 'Sign out did not start. You can try again.'; });
      });
    }
  ` }));
  const html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Example Workspace</title></head><body><header>Example Workspace</header><main><h1>Example workspace</h1><section data-private-content><input aria-label="Private draft" value="Synthetic private draft"></section><button type="button">Sign out</button><p role="status"></p></main><script type="module" src="' + modulePath + '"></script></body></html>';
  const documentPath = new URL(entry);
  await context.route(url => url.origin === documentPath.origin && url.pathname === documentPath.pathname,
    route => route.fulfill({ contentType: 'text/html', headers: { 'Cache-Control': 'no-store' }, body: html }));
  const publicHtml = html.replace(/<main>[\s\S]*?<\/main>/, '<main></main>');
  await context.route(url => url.origin === documentPath.origin && url.pathname === landing,
    route => route.fulfill({ contentType: 'text/html', headers: { 'Cache-Control': 'no-store' }, body: publicHtml }));
  return entry;
}

async function authenticatedContext(
  browser: Browser,
  baseURL: string,
  persona: (typeof personas)[keyof typeof personas],
): Promise<BrowserContext> {
  const context = await browser.newContext({ baseURL });
  const page = await context.newPage();
  await page.goto('/bff/login?returnUrl=/');
  await page.locator('#username').fill(persona.username);
  await page.locator('#password').fill(persona.password);
  await page.locator('#kc-login').click();
  await page.waitForURL(`${baseURL}/`);
  const session = await context.request.get('/bff/user');
  expect(session.ok()).toBeTruthy();
  expect(await session.json()).toMatchObject({ authenticated: true });
  return context;
}

async function submitLogoutForm(page: Page): Promise<Page> {
  const token = await page.evaluate(async () => {
    const response = await fetch('/bff/antiforgery', { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) throw new Error('Could not obtain the BFF antiforgery token.');
    return await response.json() as {
      headerName: string;
      formFieldName: string;
      requestToken: string;
    };
  });
  expect(token).toMatchObject({
    headerName: 'X-CSRF-TOKEN',
    formFieldName: '__RequestVerificationToken',
  });
  const popup = page.waitForEvent('popup');
  await page.evaluate(({ formFieldName, requestToken }) => {
    const target = 'program-kit-provider-logout';
    window.open('about:blank', target);
    const form = document.createElement('form');
    form.method = 'post';
    form.action = '/bff/logout';
    form.target = target;
    const field = document.createElement('input');
    field.type = 'hidden';
    field.name = formFieldName;
    field.value = requestToken;
    form.append(field);
    document.body.append(form);
    form.submit();
    form.remove();
  }, token);
  return await popup;
}

test('anonymous browser has no BFF session', async ({ request }) => {
  const response = await request.get('/bff/user');
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toEqual({ authenticated: false });
});

test('WEB-V3 same-origin BFF response has the governed browser headers', async ({ request }) => {
  const response = await request.get('/bff/user');
  expect(response.headers()['content-security-policy']).toContain("frame-ancestors 'none'");
  expect(response.headers()['x-frame-options']).toBe('DENY');
  expect(response.headers()['referrer-policy']).toBe('no-referrer');
  expect(response.headers()['permissions-policy']).toContain('camera=()');
  expect(response.headers()['x-content-type-options']).toBe('nosniff');
});

test('fresh native login permits sixteen seconds of human credential entry', async ({ browser, baseURL }) => {
  test.setTimeout(90_000);
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await browser.newContext({ baseURL });
  try {
    const page = await context.newPage();
    await page.goto('/bff/login?returnUrl=/');
    await page.waitForLoadState('load');
    await expect(page.locator('#username')).toBeVisible();
    // Deliberate real elapsed time; a browser fake clock cannot expire server correlation cookies.
    await page.waitForTimeout(16_000);
    await page.locator('#username').fill(personas.user.username);
    await page.locator('#password').fill(personas.user.password);
    await expect(page.locator('#username')).toHaveValue(personas.user.username);
    await expect(page.locator('#password')).toHaveValue(personas.user.password);
    await page.locator('#kc-login').click();
    await page.waitForURL(`${baseURL}/`);
    expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });
  } finally { await context.close(); }
});

test('native logout protocol clears the local session and retains its JSON acknowledgement', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  const page = await context.newPage();
  await page.goto('/');
  await page.reload();
  expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });

  const providerWindow = await submitLogoutForm(page);
  await expect.poll(async () => await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
  await providerWindow.waitForURL(nativeLogoutLanding(baseURL));
  const signedOutUrl = new URL('/bff/signed-out?remote=pending', baseURL).href;
  const signedOut = await page.goto(signedOutUrl);
  expect(signedOut).not.toBeNull();
  expect(page.url()).toBe(signedOutUrl);
  expect(signedOut!.url()).toBe(signedOutUrl);
  expect(signedOut!.status()).toBe(200);
  expect(signedOut!.headers()['content-type']).toMatch(/^application\/json(?:;|$)/i);
  expect(await signedOut!.json()).toEqual({ signedOut: true });
  await providerWindow.close();
  await context.close();
});

test('missing or invalid browser antiforgery logout does not clear the session', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  const page = await context.newPage();
  await page.goto('/');
  const outcomes = await page.evaluate(async () => {
    const missing = await fetch('/bff/logout', { method: 'POST', redirect: 'error' });
    const invalid = await fetch('/bff/logout', {
      method: 'POST',
      headers: { 'X-CSRF-TOKEN': 'invalid' },
      redirect: 'error',
    });
    return [
      { status: missing.status, body: await missing.json() },
      { status: invalid.status, body: await invalid.json() },
    ];
  });
  for (const outcome of outcomes) {
    expect(outcome.status).toBe(400);
    expect(outcome.body).toMatchObject({ code: 'invalid_antiforgery_token' });
  }
  expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });
  await context.close();
});

test('cross-site top-level logout form fails before session mutation', async ({ browser, baseURL }) => {
  const phase = { type: 'program-kit-cross-site-phase', description: 'registered' };
  test.info().annotations.push(phase);
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  phase.description = 'authenticated';
  const applicationOrigin = new URL(baseURL).origin;
  const attackerUrl = new URL('/__program-kit-cross-site-logout-fixture', identityOrigin);
  attackerUrl.hostname = new URL(baseURL).hostname === 'localhost' ? '127.0.0.1' : 'localhost';
  let stopObservingDownload: (() => void) | undefined;
  try {
    // A normal HTML document models the attacker. Firefox's privileged JSON
    // viewer cannot model an ordinary web origin; only this input page is fulfilled.
    await context.route(attackerUrl.href, route => route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: '<!doctype html><html><body>Owned cross-site form fixture</body></html>',
    }));
    phase.description = 'source-registered';
    const attacker = await context.newPage();
    const source = await attacker.goto(attackerUrl.href);
    phase.description = 'source-loaded';
    expect(source?.headers()['content-type']).toContain('text/html');
    phase.description = 'source-content-validated';
    expect(new URL(attacker.url()).origin).toBe(attackerUrl.origin);
    phase.description = 'source-url-validated';
    expect(await attacker.evaluate(() => window.origin)).toBe(attackerUrl.origin);
    phase.description = 'source-principal-validated';
    expect(attackerUrl.hostname).not.toBe(new URL(baseURL).hostname);
    expect(attackerUrl.origin).not.toBe(applicationOrigin);
    phase.description = 'source-validated';
    let rejectionDownloadObserved = false;
    const observeDownload = (download: Download) => {
      if (download.url() === `${applicationOrigin}/bff/logout`) rejectionDownloadObserved = true;
    };
    attacker.on('download', observeDownload);
    stopObservingDownload = () => attacker.off('download', observeDownload);
    const rejectedResponse = attacker.waitForResponse(response =>
      response.url() === `${applicationOrigin}/bff/logout` && response.request().method() === 'POST');
    await attacker.evaluate(origin => {
      const form = document.createElement('form');
      form.method = 'post';
      form.action = `${origin}/bff/logout`;
      document.body.append(form);
      form.submit();
    }, applicationOrigin);
    phase.description = 'submitted';
    const rejected = await rejectedResponse;
    phase.description = 'response-received';
    expect(rejected.request().isNavigationRequest()).toBeTruthy();
    phase.description = 'navigation-request-validated';
    expect(rejected.request().method()).toBe('POST');
    expect(rejected.request().url()).toBe(`${applicationOrigin}/bff/logout`);
    phase.description = 'request-target-validated';
    expect((await rejected.request().allHeaders())['origin']).toBe(attackerUrl.origin);
    phase.description = 'request-validated';
    expect(rejected.status()).toBe(400);
    phase.description = 'status-validated';
    let rejectionText: string;
    try {
      rejectionText = await rejected.text();
    } catch (error) {
      if (rejectionDownloadObserved) phase.description = 'rejection-download-observed';
      if (error instanceof Error) {
        const missingCapturedBody = /^response\.text: Protocol error \(Network\.getResponseBody\): Request "[0-9]{1,20}(?:-redirect[0-9]{1,6})?" is not found(?:\nResponse body is not available for a response that was navigated away from\. Read response\.body\(\) before triggering any navigation\.)?$(?![\s\S])/;
        if (missingCapturedBody.test(error.message)) phase.description = 'rejection-capture-request-missing';
        else if (error.message === `response.text: Response body for POST ${applicationOrigin}/bff/logout was evicted!`)
          phase.description = 'rejection-capture-evicted';
      }
      try {
        await attacker.waitForURL(`${applicationOrigin}/bff/logout`, { timeout: 1000, waitUntil: 'domcontentloaded' });
        if (attacker.url() === `${applicationOrigin}/bff/logout`) {
          const documentText = await attacker.locator('body').evaluate(element => {
            const text = 'innerText' in element ? element.innerText : null;
            return typeof text === 'string' && text.length <= 65536 ? text : null;
          }, undefined, { timeout: 1000 });
          if (attacker.url() === `${applicationOrigin}/bff/logout` && documentText !== null) {
            const documentBody: unknown = JSON.parse(documentText);
            if (typeof documentBody === 'object' && documentBody !== null &&
                'code' in documentBody && documentBody.code === 'invalid_antiforgery_token')
              phase.description = 'rejection-document-validated';
          }
        }
      } catch {
        // Inspection is diagnostic only; retain and rethrow the original SDK failure.
      }
      throw error;
    }
    phase.description = 'rejection-body-read';
    const rejectionBody: unknown = JSON.parse(rejectionText);
    phase.description = 'rejection-body-parsed';
    expect(rejectionBody).toMatchObject({ code: 'invalid_antiforgery_token' });
    phase.description = 'rejection-validated';
    await attacker.waitForURL(`${applicationOrigin}/bff/logout`);
    phase.description = 'navigation-completed';
    expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });
    phase.description = 'session-retained';
  } finally {
    stopObservingDownload?.();
    try { await context.unroute(attackerUrl.href); }
    finally { await context.close(); }
  }
});

test('native provider navigation failure leaves local session absent and retains JSON acknowledgement', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  await context.route(`${identityOrigin}/**`, route => route.abort());
  const page = await context.newPage();
  await page.goto('/');
  const providerWindow = await submitLogoutForm(page);
  await expect.poll(async () => await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
  const signedOutUrl = new URL('/bff/signed-out?remote=unavailable', baseURL).href;
  const signedOut = await page.goto(signedOutUrl);
  expect(signedOut).not.toBeNull();
  expect(page.url()).toBe(signedOutUrl);
  expect(signedOut!.url()).toBe(signedOutUrl);
  expect(signedOut!.status()).toBe(200);
  expect(signedOut!.headers()['content-type']).toMatch(/^application\/json(?:;|$)/i);
  expect(await signedOut!.json()).toEqual({ signedOut: true });
  await providerWindow.close();
  await context.close();
});

async function adapterOwnerJourney(browser: Browser, baseURL: string | undefined, providerUnavailable: boolean, lostObservation = false): Promise<void> {
    if (!baseURL) throw new Error('Playwright baseURL is required.');
    // Only fixed journey checkpoints become reporter properties; no page/provider data is retained.
    const adapterPhase = { type: 'program-kit-logout-adapter-phase', description: 'authenticated-context' };
    test.info().annotations.push(adapterPhase);
    const context = await authenticatedContext(browser, baseURL, personas.user);
    let releaseLogout = () => {};
    let logoutDispatches = 0;
    try {
      adapterPhase.description = 'owner-fixture-entry';
      const entry = await installLogoutPresentation(context, baseURL);
      if (providerUnavailable) await context.route(`${identityOrigin}/**`, route => route.abort());
      if (lostObservation) {
        await context.route(new URL('/bff/user', baseURL).href, route => route.abort());
        const released = new Promise<void>(resolve => { releaseLogout = resolve; });
        // Hold actual dispatch, without fabricating a response or successful
        // termination. Lost observation can finish before the native POST does.
        await context.route(new URL('/bff/logout', baseURL).href, async route => {
          if (route.request().method() === 'POST') {
            logoutDispatches++;
            await released;
          }
          await route.continue();
        });
      }
      const page = await context.newPage(); await page.goto(entry);
      await expect(page.getByLabel('Private draft')).toHaveValue('Synthetic private draft');
      const popup = page.waitForEvent('popup');
      const signOut = page.getByRole('button', { name: 'Sign out', exact: true });
      adapterPhase.description = 'logout-dispatch';
      if (providerUnavailable) await signOut.click();
      else { await signOut.focus(); await page.keyboard.press('Enter'); }
      adapterPhase.description = 'popup-observed';
      const providerWindow = await popup;
      if (lostObservation) {
        adapterPhase.description = 'uncertain-recovery';
        await expect(page.getByRole('heading', { name: 'Your session status is unconfirmed' })).toBeVisible();
        adapterPhase.description = 'uncertain-private-ui-cleared';
        await expect(page.locator('[data-private-content]')).toHaveCount(0);
        // Request-client observation is independent of the browser transport fault above.
        adapterPhase.description = 'uncertain-session-before-dispatch';
        expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });
        releaseLogout();
        adapterPhase.description = 'uncertain-independent-local-session';
        await expect.poll(async () => await (await context.request.get('/bff/user')).json(),
          { timeout: 5000 }).toEqual({ authenticated: false });
        expect(logoutDispatches).toBe(1);
        adapterPhase.description = 'uncertain-reconcile-action';
        await context.unroute(new URL('/bff/user', baseURL).href);
        await page.getByRole('button', { name: 'Check session', exact: true }).click();
      }
      adapterPhase.description = 'ended-heading-visible';
      await expect(page.getByRole('heading', { name: 'Your application session has ended' })).toBeVisible();
      adapterPhase.description = 'ended-heading-focused';
      // The provider popup can own the foreground document. Model the user returning
      // to the application tab; do not focus the heading here. Its native page
      // recovery must already have selected the heading for keyboard navigation.
      await page.bringToFront();
      const heading = page.getByRole('heading', { name: 'Your application session has ended' });
      const focusFacts = { type: 'program-kit-logout-adapter-focus', description: 'owner-state-unavailable' };
      test.info().annotations.push(focusFacts);
      const focusTrace = { type: 'program-kit-logout-adapter-focus-trace', description: 'owner-state-unavailable' };
      test.info().annotations.push(focusTrace);
      try { await expect(heading).toBeFocused(); }
      finally {
        // Observe after the actual assertion, before teardown. Read only booleans from
        // this synthetic owner document; never retain active element text or provider DOM.
        try {
          const location = new URL(page.url());
          if (location.origin === new URL(baseURL).origin && location.pathname === '/__program-kit-owner-session-ended') {
            const state = await heading.evaluate(element => ({
              documentFocused: element.ownerDocument.hasFocus(),
              headingSelected: element.ownerDocument.activeElement === element,
            }), undefined, { timeout: 1000 });
            focusFacts.description = `documentFocused=${state.documentFocused};headingSelected=${state.headingSelected};popupClosed=${providerWindow.isClosed()}`;
            focusTrace.description = await heading.evaluate(element => {
              const trace = Reflect.get(window, '__programKitRecoveryFocusTrace');
              if (!trace) return 'owner-state-unavailable';
              const active = document.activeElement;
              const category = active === element ? 'heading' : active === document.body ? 'body'
                : active === document.documentElement ? 'document' : active === document.querySelector('main > a') ? 'recovery-link'
                  : active === null ? 'none' : 'owner-other';
              return `headingFocusCalled=${trace.headingFocusCalled};callDocumentFocused=${trace.callDocumentFocused};headingEverSelected=${trace.headingEverSelected};headingLastSelected=${trace.headingLastSelected};windowFocusSeen=${trace.windowFocusSeen};visibilityEventSeen=${trace.visibilityEventSeen};frameExecuted=${trace.frameExecuted};frameDocumentFocused=${trace.frameDocumentFocused};activeElement=${category}`;
            }, undefined, {timeout:1000});
          } else focusFacts.description = 'owner-page-unobserved';
        } catch { /* Keep the bounded unavailable state without replacing the original failure. */ }
      }
      adapterPhase.description = 'recovery-link';
      await expect(page.getByRole('link', { name: 'Sign in', exact: true })).toHaveAttribute('href', '/bff/login?returnUrl=/');
      adapterPhase.description = 'provider-status';
      await expect(page.getByRole('status')).toContainText('Provider sign-out has not been confirmed.');
      adapterPhase.description = 'private-ui-cleared';
      await expect(page.locator('[data-private-content]')).toHaveCount(0);
      adapterPhase.description = 'independent-local-session';
      expect(await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
      adapterPhase.description = 'provider-navigation-complete';
      if (!providerUnavailable) await providerWindow.waitForURL(nativeLogoutLanding(baseURL));
      // The application page uses native session evidence, not the popup URL or a remote query hint.
      adapterPhase.description = 'owner-landing-url';
      expect(new URL(page.url()).pathname).toBe('/__program-kit-owner-session-ended');
      await providerWindow.close();
      adapterPhase.description = 'completed';
    } finally { releaseLogout(); await context.close(); }
}

test('shipped logout adapter clears private UI and reaches accessible owner landing', async ({ browser, baseURL }) => {
  await adapterOwnerJourney(browser, baseURL, false);
});

test('shipped logout adapter retains public recovery when provider navigation fails', async ({ browser, baseURL }) => {
  await adapterOwnerJourney(browser, baseURL, true);
});

test('shipped logout adapter reconciles lost local observation without restoring private UI', async ({ browser, baseURL }) => {
  await adapterOwnerJourney(browser, baseURL, false, true);
});

test('configured permission endpoint distinguishes authorized and unauthorized users', async ({ browser, baseURL }) => {
  test.skip(!process.env.PROGRAMKIT_PERMISSION_PROBE_PATH, 'Set PROGRAMKIT_PERMISSION_PROBE_PATH when the first protected slice is mapped.');
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const path = process.env.PROGRAMKIT_PERMISSION_PROBE_PATH!;
  const authorized = await authenticatedContext(browser, baseURL, personas.admin);
  const authorizedResponse = await authorized.request.get(path);
  expect(authorizedResponse.ok()).toBeTruthy();
  await authorized.close();
  const denied = await authenticatedContext(browser, baseURL, personas.wrongRole);
  const deniedResponse = await denied.request.get(path);
  expect(deniedResponse.status()).toBe(403);
  await denied.close();
});

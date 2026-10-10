import { expect, type Browser, type BrowserContext, type Download, type Page, test } from '@playwright/test';
import { personas } from '../persona-fixture.js';

const identityAuthority = process.env.PROGRAMKIT_IDENTITY_AUTHORITY ?? 'http://localhost:8080/realms/program-kit';
const identityOrigin = new URL(identityAuthority).origin;

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

test('real browser form logout clears local state and completes provider navigation', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  const page = await context.newPage();
  await page.goto('/');
  await page.reload();
  expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });

  const providerWindow = await submitLogoutForm(page);
  await expect.poll(async () => await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
  await providerWindow.waitForURL(`${baseURL}/bff/signed-out`);
  await page.goto('/bff/signed-out?remote=pending');
  expect(await page.locator('body').innerText()).toContain('"signedOut":true');
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

test('provider navigation failure cannot restore local access or displace the signed-out page', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  await context.route(`${identityOrigin}/**`, route => route.abort());
  const page = await context.newPage();
  await page.goto('/');
  const providerWindow = await submitLogoutForm(page);
  await expect.poll(async () => await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
  await page.goto('/bff/signed-out?remote=unavailable');
  expect(await page.locator('body').innerText()).toContain('"signedOut":true');
  await providerWindow.close();
  await context.close();
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

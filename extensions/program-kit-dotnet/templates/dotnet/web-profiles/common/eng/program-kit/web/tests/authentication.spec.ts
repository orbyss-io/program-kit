import { expect, type Browser, type BrowserContext, test } from '@playwright/test';

const personas = {
  user: { username: 'local-user', password: 'local-user-only' },
  admin: { username: 'local-admin', password: 'local-admin-only' },
  wrongRole: { username: 'local-wrong-role', password: 'local-wrong-role-only' },
} as const;

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

test('anonymous browser has no BFF session', async ({ request }) => {
  const response = await request.get('/bff/user');
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toEqual({ authenticated: false });
});

test('real provider login, refresh, and local logout use the BFF contract', async ({ browser, baseURL }) => {
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const context = await authenticatedContext(browser, baseURL, personas.user);
  const page = await context.newPage();
  await page.reload();
  expect(await (await context.request.get('/bff/user')).json()).toMatchObject({ authenticated: true });

  const tokenResponse = await context.request.get('/bff/antiforgery');
  const token = (await tokenResponse.json()) as { requestToken: string };
  const logout = await context.request.post('/bff/logout', {
    headers: { 'X-CSRF-TOKEN': token.requestToken },
    maxRedirects: 0,
  });
  expect(logout.status()).toBe(302);
  const providerLocation = logout.headers().location;
  expect(providerLocation).toContain('localhost:8080');
  if (!providerLocation) throw new Error('RP-initiated logout did not return a provider location.');
  await page.route('http://localhost:8080/**', route => route.abort());
  await page.goto(providerLocation).catch(() => undefined);
  expect(await (await context.request.get('/bff/user')).json()).toEqual({ authenticated: false });
  await context.close();
});

test('configured permission endpoint distinguishes authorized and unauthorized users', async ({ browser, baseURL }) => {
  test.skip(!process.env.PROGRAMKIT_PERMISSION_PROBE_PATH, 'Set PROGRAMKIT_PERMISSION_PROBE_PATH when the first protected slice is mapped.');
  if (!baseURL) throw new Error('Playwright baseURL is required.');
  const path = process.env.PROGRAMKIT_PERMISSION_PROBE_PATH!;
  const authorized = await authenticatedContext(browser, baseURL, personas.admin);
  expect((await authorized.request.get(path)).status()).toBe(200);
  await authorized.close();
  const denied = await authenticatedContext(browser, baseURL, personas.wrongRole);
  expect((await denied.request.get(path)).status()).toBe(403);
  await denied.close();
});

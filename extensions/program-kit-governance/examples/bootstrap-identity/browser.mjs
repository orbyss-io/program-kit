// Bounded subset of the shipped authentication.spec.ts mechanism checks.
// Credentials are the existing explicitly non-production local fixture personas.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { chromium } from '@playwright/test';
const { baseURL } = JSON.parse(readFileSync('browser-inputs.json', 'utf8'));
const realm = JSON.parse(readFileSync('realm.json', 'utf8'));
assert.equal(realm.attributes.programKitFixture, 'local-non-production-only');
const browser = await chromium.launch();
try {
  const anonymous = await browser.newContext({ baseURL });
  assert.equal((await anonymous.request.get('/api/permission-probe', { maxRedirects: 0 })).status(), 401);
  assert.equal((await anonymous.request.get('/bff/user')).status(), 200);
  await anonymous.close();
  for (const [name, expected] of [['local-user', 204], ['local-wrong-role', 403]]) {
    const persona = realm.users.find(u => u.username === name);
    const password = persona.credentials.find(c => c.type === 'password').value;
    const context = await browser.newContext({ baseURL });
    try {
      const page = await context.newPage();
      const login = await page.goto('/bff/login?returnUrl=/');
      assert.ok(login?.ok(), `Provider login failed with HTTP ${login?.status()}; inspect preserved provider diagnostics`);
      await page.locator('#username').fill(persona.username);
      await page.locator('#password').fill(password);
      await page.locator('#kc-login').click();
      await page.waitForURL(`${baseURL}/`);
      assert.equal((await (await context.request.get('/bff/user')).json()).authenticated, true);
      assert.equal((await context.request.get('/api/permission-probe')).status(), expected);
      assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length), 0);
      // The pinned publisher explicitly uses this separate name and SameAsRequest
      // only for Development + AllowHttpForLocalDevelopment. HTTPS is a later gate.
      const session = (await context.cookies()).find(c => c.name === 'orbyss-foundation-session-local');
      assert.ok(session?.httpOnly && session?.sameSite === 'Lax');
      assert.equal(session.secure, false);
      const rejected = await context.request.post('/bff/logout', { maxRedirects: 0 });
      assert.equal(rejected.status(), 400);
      assert.equal((await (await context.request.get('/bff/user')).json()).authenticated, true);
      const token = await (await context.request.get('/bff/antiforgery')).json();
      await context.request.post('/bff/logout', { headers: { [token.headerName]: token.requestToken }, maxRedirects: 0 });
      assert.equal((await (await context.request.get('/bff/user')).json()).authenticated, false);
    } finally { await context.close(); }
  }
  console.log('PROGRAM_KIT_BFF_PROVIDER_OK');
} finally { await browser.close(); }

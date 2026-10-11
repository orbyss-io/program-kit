// Maintained login/context adapter. Consumers supply only product assertions.
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const require = createRequire(resolve('package.json'));
const { chromium } = require('@playwright/test');
const baseURL = process.env.PROGRAMKIT_BASE_URL;
const realm = JSON.parse(readFileSync(resolve('../../deploy/keycloak/program-kit-realm.json'), 'utf8'));
if (realm.attributes?.programKitFixture !== 'local-non-production-only') throw new Error('Synthetic realm required');
const browser = await chromium.launch();
const contexts = {};
try {
  for (const [role, username] of Object.entries({user:'local-user',admin:'local-admin',wrongRole:'local-wrong-role'})) {
    const persona = realm.users.find(user => user.username === username);
    const context = contexts[role] = await browser.newContext({baseURL});
    const page = await context.newPage();
    await page.goto('/bff/login?returnUrl=/');
    await page.locator('#username').fill(username);
    await page.locator('#password').fill(persona.credentials.find(item => item.type === 'password').value);
    await page.locator('#kc-login').click();
    await page.waitForURL(`${baseURL}/`);
    const session = await (await context.request.get('/bff/user')).json();
    if (session.authenticated !== true) throw new Error('Actual authenticated context absent');
  }
  const { qualify } = await import(pathToFileURL(process.env.PROGRAMKIT_PRODUCT_ADAPTER));
  const result = await qualify(contexts);
  if (result?.status !== 'passed' || result?.ownedCreateRead !== true) throw new Error('Product adapter did not prove owned create/read');
  writeFileSync(process.env.PROGRAMKIT_QUALIFICATION_OUTPUT, JSON.stringify(result,null,2)+'\n');
} finally {
  await Promise.all(Object.values(contexts).map(context => context.close()));
  await browser.close();
}

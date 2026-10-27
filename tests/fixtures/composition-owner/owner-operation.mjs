// Test-only extension of the maintained generated browser journey. No screenshots, DOM or token evidence.
import { readFileSync, writeFileSync } from 'node:fs';
import { chromium, webkit, firefox } from 'playwright';

const [planPath, outputPath] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planPath, 'utf8'));
const realm = JSON.parse(readFileSync(plan.realm, 'utf8'));
const engines = { chromium, webkit, firefox };
const evidence = { status: 'checking', checks: [] };
let phase = 'launch';
function require(value) { if (!value) throw new Error('owner operation contract failed'); }
try {
  for (const engine of plan.engines) {
    const browser = await engines[engine].launch({ headless: true });
    const contexts = [];
    try {
      const anonymous = await browser.newContext(); contexts.push(anonymous);
      require((await anonymous.request.get(plan.origin + '/api/owned-notes/11111111-1111-4111-8111-111111111111')).status() === 401);
      const clients = [];
      for (const username of ['local-user', 'local-admin', 'local-wrong-role']) {
        phase = 'native-login';
        const context = await browser.newContext(); contexts.push(context);
        const page = await context.newPage();
        const user = realm.users.find(row => row.username === username);
        require(user?.enabled === true);
        const credential = user.credentials.find(row => row.type === 'password' && row.temporary === false);
        await page.goto(plan.origin + '/bff/login?returnUrl=' + encodeURIComponent('/'), { waitUntil: 'load' });
        await page.locator('#username').fill(username);
        await page.locator('#password').fill(credential.value);
        await page.locator('#kc-login').click();
        await page.waitForURL(plan.origin + '/', { waitUntil: 'domcontentloaded', timeout: 30000 });
        const session = await context.request.get(plan.origin + '/bff/user');
        require(session.status() === 200 && (await session.json()).authenticated === true);
        const tokenResponse = await context.request.get(plan.origin + '/bff/antiforgery');
        const token = await tokenResponse.json();
        require(typeof token.headerName === 'string' && typeof token.requestToken === 'string');
        clients.push({ context, token });
        await page.close();
      }
      const headers = client => ({ [client.token.headerName]: client.token.requestToken });
      phase = 'permission-denial';
      require((await clients[2].context.request.post(plan.origin + '/api/owned-notes', { headers: headers(clients[2]) })).status() === 403);
      phase = 'owned-product-write';
      const ids = [];
      for (const client of clients.slice(0, 2)) {
        const response = await client.context.request.post(plan.origin + '/api/owned-notes', { headers: headers(client) });
        require(response.status() === 201);
        const note = await response.json(); require(typeof note.id === 'string'); ids.push(note.id);
      }
      require(ids[0] !== ids[1]);
      phase = 'exact-owner-read';
      for (let index = 0; index < 2; index++) {
        const own = await clients[index].context.request.get(plan.origin + '/api/owned-notes/' + ids[index]);
        require(own.status() === 200 && (await own.json()).value === 'synthetic-owner-note');
        const other = await clients[index].context.request.get(plan.origin + '/api/owned-notes/' + ids[1-index] + '?owner=local-admin');
        require(other.status() === 404);
      }
      evidence.checks.push({ engine, nativeLogin: true, permissionDenial: true, ownedWrites: 2, exactOwnerReads: 2, foreignReadsDenied: 2 });
    } finally {
      for (const context of contexts) await context.close();
      await browser.close();
    }
  }
  evidence.status = 'passed';
} catch {
  evidence.status = 'failed'; evidence.phase = phase; process.exitCode = 2;
}
writeFileSync(outputPath, JSON.stringify(evidence, null, 2) + '\n');

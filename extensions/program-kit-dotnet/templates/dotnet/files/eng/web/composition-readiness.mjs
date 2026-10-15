// Direct library use retains only allowlisted evidence, including on failure.
// No test-runner screenshots, DOM/error contexts, traces or token dumps exist.
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { chromium, webkit, firefox } from 'playwright';

const [planPath, outputPath] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planPath, 'utf8'));
const engines = { chromium, webkit, firefox };
const evidence = { schemaVersion: 2, status: 'checking', planSha256: createHash('sha256').update(readFileSync(planPath)).digest('hex'), launches: [], checks: [] };
let current = { phase: 'launch' };
function require(value) { if (!value) throw new Error('contract check failed'); }
try {
  for (const engine of plan.engines) {
    current = { engine, phase: 'launch' };
    const browser = await engines[engine].launch({ headless: true });
    const launch = { engine, launched: true, closed: false };
    evidence.launches.push(launch);
    try {
      if (plan.launchOnly) continue;
      const context = await browser.newContext();
      try {
        for (const host of plan.hosts) {
          current = { engine, host: host.id, phase: 'anonymous-entry' };
          const anonymous = await browser.newContext();
          try {
            const session = await anonymous.request.get(host.origin + '/bff/user');
            current.sessionStatus = session.status();
            current.cacheControl = session.headers()['cache-control'] ?? null;
            require(session.status() === 200);
            require((await session.json()).authenticated === false);
            require((session.headers()['cache-control'] ?? '').includes('no-store'));
            if (host.page) {
              const entry = await anonymous.request.get(host.origin + host.page, { maxRedirects: 0 });
              current.entryStatus = entry.status();
              const target = entry.headers().location ? new URL(entry.headers().location, host.origin) : null;
              current.challengePath = target?.pathname ?? null;
              require(entry.status() === 302 && target?.origin === host.origin && target.pathname === '/bff/login');
            }
          } finally { await anonymous.close(); }
          current.phase = 'login';
          const page = await context.newPage();
          try {
            const navigation = await page.goto(host.origin + '/bff/login?returnUrl=' + encodeURIComponent(host.page ?? '/'), { waitUntil: 'domcontentloaded' });
            current.navigationStatus = navigation?.status() ?? null;
            current.pagePath = new URL(page.url()).pathname;
            const username = page.locator('#username');
            const targetUrl = host.origin + (host.page ?? '/');
            const loginRequired = await Promise.race([
              username.waitFor({ state: 'visible', timeout: 30000 }).then(() => true),
              page.waitForURL(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 }).then(() => false),
            ]);
            current.credentialAttempt = loginRequired;
            if (loginRequired) {
              current.phase = 'login-credentials';
              const realm = JSON.parse(readFileSync(host.realm, 'utf8'));
              const persona = realm.users.find(value => value.username === 'local-user');
              require(persona?.enabled === true);
              const credential = persona.credentials.find(value => value.type === 'password' && value.temporary === false);
              require(credential?.value);
              require(await page.locator('link[href*="program-kit.css"]').count() > 0);
              // Provider page initialization can still replace/reset fields after
              // DOMContentLoaded. Finish that lifecycle before entering credentials.
              await page.waitForLoadState('load');
              await username.fill(persona.username);
              await page.locator('#password').fill(credential.value);
              current.inputValuesPresent = (await username.inputValue()) === persona.username &&
                (await page.locator('#password').inputValue()) === credential.value;
              require(current.inputValuesPresent);
              current.phase = 'login-submit';
              await page.locator('#kc-login').click();
              current.pagePath = new URL(page.url()).pathname;
            }
            current.phase = 'login-callback';
            await page.waitForURL(host.origin + (host.page ?? '/'), { waitUntil: 'domcontentloaded', timeout: 30000 });
            current.phase = 'authenticated-session';
            const session = await context.request.get(host.origin + '/bff/user');
            require(session.status() === 200 && (await session.json()).authenticated === true);
            if (plan.privacyProbe) {
              current.phase = 'privacy-failure-check';
              await page.evaluate(() => {
                const sentinel = document.createElement('p');
                sentinel.textContent = 'PROGRAMKIT_PRIVATE_FAILURE_SENTINEL';
                document.body.append(sentinel);
              });
              require(false); // Owned negative case, after a real authenticated page.
            }
            if (host.page) {
              current.phase = 'authenticated-page';
              require((await context.request.get(host.origin + host.page)).status() === 200);
              // Foundation owns the mount/status containers; product markup can
              // change immediately after scaffold without invalidating readiness.
              await page.locator('#foundation-form > *').first().waitFor({ state: 'attached', timeout: 15000 });
              await page.locator('#foundation-status').waitFor({ state: 'hidden', timeout: 15000 });
              if (host.expectedHeading) require(await page.getByRole('heading', { name: host.expectedHeading, exact: true }).count() === 1);
            }
            // The already-authenticated first app must survive signing into the second.
            for (const previous of evidence.checks.filter(value => value.engine === engine)) {
              require((await (await context.request.get(previous.origin + '/bff/user')).json()).authenticated === true);
            }
            if (host.productPath) {
              current.phase = 'consumer-feature';
              const response = await context.request.get(host.origin + host.productPath);
              require(response.status() === 200);
              require(JSON.stringify(await response.json()) === JSON.stringify(host.productResponse));
            }
            for (const check of host.pageChecks ?? []) {
              current.phase = 'additional-page-access';
              const response = await context.request.get(host.origin + check.path, { maxRedirects: 0 });
              current.additionalPageStatus = response.status();
              require(response.status() === check.status);
              if (check.denialPath) {
                const target = new URL(response.headers().location, host.origin);
                require(target.origin === host.origin && target.pathname === check.denialPath);
                require((await context.request.get(host.origin + check.path)).status() === 403);
              }
            }
            evidence.checks.push({ engine, host: host.id, origin: host.origin, authenticated: true,
              hostedAssetsLoaded: Boolean(host.page), consumerFeature: Boolean(host.productPath) });
          } catch {
            current.pagePath = new URL(page.url()).pathname;
            // Retain a fixed diagnostic category, never the provider's message,
            // DOM, cookies' values or a callback query string.
            const messages = await page.locator('#input-error, #kc-error-message, .alert-error').allTextContents().catch(() => []);
            const text = messages.join(' ').toLowerCase();
            current.identityError = text.includes('invalid username or password') ? 'invalid-credentials'
              : text.includes('cookie') ? 'identity-cookie'
              : text.includes('expired') ? 'expired-authentication'
              : text.includes('already logged') ? 'existing-session'
              : text ? 'other-provider-error' : 'none';
            throw new Error('contract check failed');
          } finally { await page.close(); }
        }
      } finally { await context.close(); }
    } finally {
      try { await browser.close(); }
      catch { current = { engine, phase: 'close' }; throw new Error('browser close failed'); }
      launch.closed = true;
    }
  }
  evidence.status = 'ready';
} catch {
  evidence.status = 'failed';
  evidence.failure = current; // Deliberately exclude browser errors, bodies and DOM.
  process.exitCode = 2;
} finally {
  writeFileSync(outputPath, JSON.stringify(evidence, null, 2) + '\n');
}

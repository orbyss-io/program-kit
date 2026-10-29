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
            const session = await anonymous.request.get(host.origin + (host.pathBase ?? '') + '/bff/user');
            current.sessionStatus = session.status();
            current.cacheControl = session.headers()['cache-control'] ?? null;
            require(session.status() === 200);
            require((await session.json()).authenticated === false);
            require((session.headers()['cache-control'] ?? '').includes('no-store'));
            for (const selected of host.entries ?? (host.page ? [{ path: host.page, mode: 'Authenticated' }] : [])) {
              require(selected.mode === 'Public' || selected.mode === 'Authenticated');
              const entry = await anonymous.request.get(host.origin + selected.path, { maxRedirects: 0 });
              current.entryStatus = entry.status();
              const target = entry.headers().location ? new URL(entry.headers().location, host.origin) : null;
              current.challengePath = target?.pathname ?? null;
              if (selected.mode === 'Public') {
                require(entry.status() === 200 && target === null && (entry.headers()['content-type'] ?? '').includes('text/html'));
              } else {
                require(entry.status() === 302 && target?.origin === host.origin && target.pathname === (host.pathBase ?? '') + '/bff/login');
              }
            }
          } finally { await anonymous.close(); }
          current.phase = 'login';
          const page = await context.newPage();
          try {
            const navigation = await page.goto(host.origin + (host.pathBase ?? '') + '/bff/login?returnUrl=' + encodeURIComponent(host.page ?? (host.pathBase ?? '') + '/'), { waitUntil: 'domcontentloaded' });
            current.navigationStatus = navigation?.status() ?? null;
            current.pagePath = new URL(page.url()).pathname;
            const username = page.locator('#username');
            const targetUrl = host.origin + (host.page ?? (host.pathBase ?? '') + '/');
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
            await page.waitForURL(host.origin + (host.page ?? (host.pathBase ?? '') + '/'), { waitUntil: 'domcontentloaded', timeout: 30000 });
            current.phase = 'authenticated-session';
            const session = await context.request.get(host.origin + (host.pathBase ?? '') + '/bff/user');
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
              require((await (await context.request.get(previous.origin + (previous.pathBase ?? '') + '/bff/user')).json()).authenticated === true);
            }
            if (host.productPath) {
              current.phase = 'consumer-feature';
              const response = await context.request.get(host.origin + (host.pathBase ?? '') + host.productPath);
              require(response.status() === 200);
              require(JSON.stringify(await response.json()) === JSON.stringify(host.productResponse));
            }
            for (const check of host.pageChecks ?? []) {
              current.phase = 'additional-page-access';
              const response = await context.request.get(host.origin + (host.pathBase ?? '') + check.path, { maxRedirects: 0 });
              current.additionalPageStatus = response.status();
              require(response.status() === check.status);
              if (check.denialPath) {
                const target = new URL(response.headers().location, host.origin);
                require(target.origin === host.origin && target.pathname === (host.pathBase ?? '') + check.denialPath);
                require((await context.request.get(host.origin + (host.pathBase ?? '') + check.path)).status() === 403);
              }
            }
            if (host.typedOperation) {
              current.phase = 'typed-client-operation';
              const tokenResponse = await context.request.get(host.origin + (host.pathBase ?? '') + '/bff/antiforgery');
              require(tokenResponse.status() === 200);
              const token = await tokenResponse.json();
              require(typeof token.headerName === 'string' && typeof token.requestToken === 'string');
              current.operationDispatched = true;
              const result = await page.evaluate(async ({ token, body }) => {
                const adapter = window.programKitTypedExample;
                if (!adapter || typeof adapter.storeLabel !== 'function') throw new Error('Typed example adapter is absent.');
                return await adapter.storeLabel(body, token.headerName, token.requestToken, AbortSignal.timeout(15000));
              }, { token, body: host.typedOperation.body });
              require(JSON.stringify(result) === JSON.stringify(host.typedOperation.response));
              const observed = await context.request.get(host.origin + (host.pathBase ?? '') + '/api/sample-label');
              require(observed.status() === 200 && JSON.stringify(await observed.json()) === JSON.stringify(result));
            }
            if (host.presentationProbe) {
              current.phase = 'native-generated-controls';
              const effects = [];
              page.on('request', request => {
                const path = new URL(request.url()).pathname;
                if (/\/bff\/(?:antiforgery|logout)$/u.test(path) || path === (host.pathBase ?? '') + '/api/sample-label' && request.method() === 'POST')
                  effects.push(request.method());
              });
              const editor = page.getByRole('textbox', { name: 'Example draft', exact: true });
              await editor.fill('Fictional retained draft');
              const signOut = page.getByRole('button', { name: host.presentationProbe.signOutText, exact: true });
              await signOut.click(); await page.getByRole('dialog').waitFor();
              require(effects.length === 0);
              await page.keyboard.press('Escape'); await page.getByRole('dialog').waitFor({ state: 'hidden' });
              require(await editor.inputValue() === 'Fictional retained draft' && effects.length === 0);
              require((await (await context.request.get(host.origin + (host.pathBase ?? '') + '/bff/user')).json()).authenticated === true);
              const nativeUnsavedState = () => page.evaluate(async prefix => {
                const response = await fetch(prefix + '/configuration', { cache: 'no-store' });
                if (!response.ok) throw new Error('Native presentation configuration unavailable.');
                const selected = await response.json();
                const native = await import(selected.modulePath);
                return native.unsavedWork(selected.surface).getState();
              }, host.presentationProbe.routePrefix);
              require(await nativeUnsavedState() === 'dirty');
              await context.clearCookies();
              // Exercise the installed observer against the actual expired
              // session before navigation can create a fresh module registry.
              await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
              await editor.waitFor({ state: 'detached' });
              require(await nativeUnsavedState() === 'clean');
              // Actual navigation/back additionally exercises native lifecycle;
              // no replacement presentation or protocol is injected.
              await page.goto(host.origin + host.presentationProbe.routePrefix + '/expired');
              await page.goBack({ waitUntil: 'domcontentloaded' });
              await page.waitForFunction(() => {
                const draft = document.querySelector('textarea[aria-label="Example draft"]');
                return !draft || !draft.checkVisibility();
              });
              require(effects.length === 0);
              require((await (await context.request.get(host.origin + (host.pathBase ?? '') + '/bff/user')).json()).authenticated === false);
              current.nativeGeneratedControls = true;
            }
            evidence.checks.push({ engine, host: host.id, origin: host.origin, pathBase: host.pathBase ?? '', authenticated: true,
              hostedAssetsLoaded: Boolean(host.page), consumerFeature: Boolean(host.productPath),
              typedOperation: Boolean(host.typedOperation), nativeGeneratedControls: current.nativeGeneratedControls === true });
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

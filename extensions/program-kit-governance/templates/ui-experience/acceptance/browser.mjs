import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium, firefox, webkit } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { recordDurabilityCase } from './durability.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const manifest = JSON.parse(await readFile(resolve(root, 'publication.json'), 'utf8'));
const resources = new Map(manifest.resources.map(r => [r.route, r]));
resources.set('/__tailwind.css', { file: 'acceptance/tailwind-compiled.css', contentType: 'text/css; charset=utf-8' });
resources.set('/__keycloak-brand.css', { file: 'integration/keycloak-brand.css', contentType: 'text/css; charset=utf-8' });
const archetypes = ['journey', 'product-shell', 'workspace', 'content-hub', 'showcase'];
for (const name of archetypes) resources.set(`/__gallery/${name}`, { file: `acceptance/archetypes/${name}.html`, contentType: 'text/html; charset=utf-8' });
const authStates = ['login', 'login-success', 'login-error', 'session-expired', 'logout-confirmation', 'logout-progress', 'logout-success', 'logout-error'];
const modern = JSON.parse(await readFile(resolve(root, 'acceptance/report.json'), 'utf8')).presentation === 'modern-product-v1';
if (modern) for (const state of authStates) resources.set(`/__auth/${state}`, { file: `integration/auth/${state}.html`, contentType: 'text/html; charset=utf-8' });
const supportedCases = ['gallery', 'forms', 'motion', 'auth'];
const caseArgument = process.argv.find(value => value.startsWith('--cases='));
const selectedCases = new Set((caseArgument?.slice('--cases='.length) || supportedCases.join(',')).split(',').filter(Boolean));
const durabilityArgument = process.argv.find(value => value.startsWith('--durability-contract='));
if (durabilityArgument) selectedCases.add('durability');
assert(selectedCases.size && [...selectedCases].every(value => [...supportedCases, 'durability'].includes(value)), 'Unsupported or empty browser case selection');
if (selectedCases.has('durability') && !durabilityArgument) throw new Error('PKB001 durability requires a consumer-owned real server contract');
let durabilityAdapter = null;
if (durabilityArgument) {
  try { durabilityAdapter = await import(pathToFileURL(resolve(durabilityArgument.slice('--durability-contract='.length))).href); }
  catch { throw new Error('PKB001 real server durability adapter could not be loaded'); }
}
if (durabilityAdapter && typeof durabilityAdapter.createContract !== 'function') throw new Error('PKB001 durability adapter must export createContract');
if (!modern && [...selectedCases].some(value => !['gallery', 'durability'].includes(value)) && caseArgument) throw new Error('Modern cases require modern-product-v1');
const server = createServer(async (request, response) => {
  const route = new URL(request.url, 'http://127.0.0.1').pathname;
  const resource = resources.get(route);
  if (!resource) { response.writeHead(404); response.end(); return; }
  try { response.setHeader('Content-Type', resource.contentType); response.end(await readFile(resolve(root, resource.file))); }
  catch { response.writeHead(500); response.end('Fixture read failed'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const results = [], errors = [];
const evidence = resolve(root, 'acceptance/browser-evidence');
await mkdir(evidence, { recursive: true });

const supportedEngines = [
  { name: 'chromium', browserType: chromium },
  { name: 'webkit', browserType: webkit },
  { name: 'firefox', browserType: firefox },
];
const engineArgument = process.argv.find(value => value.startsWith('--engines='));
const requestedEngineNames = (engineArgument?.slice('--engines='.length) || 'chromium,firefox,webkit')
  .split(',').map(value => value.trim()).filter(Boolean);
const unknownEngines = requestedEngineNames.filter(name => !supportedEngines.some(engine => engine.name === name));
assert.deepEqual(unknownEngines, [], `Unsupported browser engines: ${unknownEngines.join(', ')}`);
const selectedEngineNames = new Set(requestedEngineNames);
const engines = supportedEngines.filter(engine => selectedEngineNames.has(engine.name));
assert(engines.length > 0, 'At least one browser engine is required');
const deviceProfiles = [
  { name: 'phone-portrait', engine: 'chromium', viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true },
  { name: 'phone-landscape', engine: 'chromium', viewport: { width: 844, height: 390 }, deviceScaleFactor: 3, isMobile: true },
  { name: 'tablet-portrait', engine: 'webkit', viewport: { width: 768, height: 1024 }, deviceScaleFactor: 2, isMobile: true },
  { name: 'tablet-landscape', engine: 'webkit', viewport: { width: 1024, height: 768 }, deviceScaleFactor: 2, isMobile: true },
];

async function securePage(page, label) {
  page.on('pageerror', error => errors.push(`${label}: ${error.message}`));
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
}

async function assertNoPageOverflow(page, label) {
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${label} page overflow`);
}

async function verifyDesktop(engine, browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'en-US', timezoneId: 'UTC' });
  const page = await context.newPage();
  await securePage(page, engine);
  try {
    if (engine === 'chromium') {
      // Verify consumer public documents really expose their content before JavaScript executes.
      for (const resource of manifest.resources.filter(r => r.contentType.startsWith('text/html'))) {
        const response = await context.request.get(origin + resource.route);
        assert.equal(response.status(), 200);
        const raw = await response.text();
        assert(raw.includes('<h1') && raw.includes('rel="canonical"') && raw.includes('application/ld+json'));
      }
    }
    for (const archetype of archetypes) {
      for (const scheme of ['light', 'dark']) {
        const label = `${engine}/${archetype}/${scheme}`;
        await page.emulateMedia({ colorScheme: scheme, reducedMotion: 'reduce', forcedColors: 'none' });
        await page.setViewportSize({ width: 1440, height: 1000 });
        await page.goto(`${origin}/__gallery/${archetype}`);
        await page.getByRole('heading', { level: 1 }).waitFor();
        await assertNoPageOverflow(page, label);
        const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
        assert.deepEqual(axe.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), [], `${label} accessibility`);
        await page.keyboard.press('Tab');
        await assert.doesNotReject(() => page.getByRole('link', { name: 'Skip to content' }).waitFor());
        assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Skip to content');
        const opener = page.getByRole('button', { name: 'Open confirmation' });
        await opener.focus(); await page.keyboard.press('Enter');
        assert.equal(await page.locator('dialog').evaluate(d => d.open), true);
        assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Cancel');
        await page.keyboard.press('Tab');
        assert.equal(await page.evaluate(() => document.activeElement.closest('dialog') !== null), true);
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('dialog').evaluate(d => d.open), false);
        assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Open confirmation');
        await page.screenshot({ path: resolve(evidence, `${engine}-${archetype}-${scheme}.png`), fullPage: true, animations: 'disabled' });
        // Narrow viewport plus doubled root text is a reflow approximation, not actual browser zoom certification.
        await page.setViewportSize({ width: 320, height: 900 });
        await page.evaluate(() => { document.documentElement.dir = 'rtl'; document.documentElement.style.fontSize = '200%'; });
        await assertNoPageOverflow(page, `${label}/rtl-200-percent`);
        const target = await opener.boundingBox();
        assert(target.height >= 44 && target.width >= 44, `${label} touch target`);
        if (engine === 'chromium') {
          await page.emulateMedia({ forcedColors: 'active' });
          await opener.focus();
          assert.equal(await opener.evaluate(el => getComputedStyle(el).transitionDuration), '0s');
          assert.notEqual(await opener.evaluate(el => getComputedStyle(el).outlineStyle), 'none');
        }
        results.push({ engine, archetype, scheme, axe: 'passed', keyboard: 'passed', reflowRtl: 'passed', reducedMotion: 'passed', forcedColors: engine === 'chromium' ? 'passed' : 'not-emulated' });
      }
    }
    if (engine === 'chromium') {
      await page.goto(`${origin}/__gallery/product-shell`);
      await page.emulateMedia({ colorScheme: 'light', forcedColors: 'none' });
      await page.addStyleTag({ url: origin + '/__tailwind.css' });
      await page.evaluate(() => {
        const sample = document.createElement('div'); sample.id = 'tailwind-bridge';
        sample.className = 'bg-primary text-on-primary rounded-brand font-sans'; sample.textContent = 'Tailwind bridge';
        document.querySelector('main').append(sample);
      });
      for (const colorScheme of ['light', 'dark']) {
        await page.emulateMedia({ colorScheme });
        const colors = await page.evaluate(() => {
          const native = getComputedStyle(document.querySelector('[data-pk-dialog]'));
          const utility = getComputedStyle(document.getElementById('tailwind-bridge'));
          return { native: [native.color, native.backgroundColor, native.borderRadius], utility: [utility.color, utility.backgroundColor, utility.borderRadius] };
        });
        assert.deepEqual(colors.utility, colors.native, `Tailwind/native ${colorScheme} semantic parity`);
      }
    }
  } finally {
    await context.close();
  }
}

async function verifyTouchDevice(profile, browser) {
  const context = await browser.newContext({
    viewport: profile.viewport,
    screen: profile.viewport,
    deviceScaleFactor: profile.deviceScaleFactor,
    hasTouch: true,
    isMobile: profile.isMobile,
    locale: 'en-US',
    timezoneId: 'UTC',
  });
  const page = await context.newPage();
  await securePage(page, profile.name);
  try {
    for (const archetype of archetypes) {
      const label = `${profile.engine}/${profile.name}/${archetype}`;
      await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
      await page.goto(`${origin}/__gallery/${archetype}`);
      await page.getByRole('heading', { level: 1 }).waitFor();
      await assertNoPageOverflow(page, label);
      const opener = page.getByRole('button', { name: 'Open confirmation' });
      const target = await opener.boundingBox();
      assert(target.height >= 44 && target.width >= 44, `${label} touch target`);
      await opener.tap();
      assert.equal(await page.locator('dialog').evaluate(d => d.open), true);
      await page.getByRole('button', { name: 'Cancel' }).tap();
      assert.equal(await page.locator('dialog').evaluate(d => d.open), false);
      await page.screenshot({ path: resolve(evidence, `${profile.engine}-${profile.name}-${archetype}.png`), fullPage: true, animations: 'disabled' });
      results.push({ engine: profile.engine, device: profile.name, archetype, touch: 'passed', sizing: 'passed', orientation: profile.name.endsWith('landscape') ? 'landscape' : 'portrait' });
    }
  } finally {
    await context.close();
  }
}

async function verifyModern(engine, browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage(); await securePage(page, `${engine}/modern`);
  try {
    if (selectedCases.has('forms')) {
      await page.goto(`${origin}/__gallery/product-shell`);
      const form = page.locator('[data-pk-demo-form]');
      const name = form.locator('#example-name'), description = form.locator('#example-description');
      await description.fill('Keep this draft');
      await form.getByRole('button', { name: 'Save example' }).click();
      await form.locator('[data-pk-error-summary]').waitFor();
      assert.equal(await name.getAttribute('aria-invalid'), 'true');
      assert((await name.getAttribute('aria-describedby')).includes('example-name-hint'));
      assert.equal(await description.inputValue(), 'Keep this draft');
      assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-pk-error-summary')), true);
      assert.equal(await name.evaluate(el => getComputedStyle(el).borderTopWidth), '2px');
      await form.getByRole('link', { name: 'Enter a name.' }).click();
      assert.equal(await name.evaluate(el => el === document.activeElement), true);
      await name.fill('Example'); await form.getByRole('button', { name: 'Save example' }).click();
      await form.locator('[data-pk-operation-status]').filter({ hasText: 'Example saved' }).waitFor();
      assert.equal(await name.getAttribute('aria-invalid'), null);
      assert.equal(await description.inputValue(), 'Keep this draft');
      await page.evaluate(async () => {
        const { bindOperation } = await import('/assets/interactions.mjs');
        const form = document.querySelector('[data-pk-demo-form]');
        window.fixtureCalls = 0;
        window.fixtureDispose = bindOperation(form, () => { window.fixtureCalls++; return new Promise(resolve => { window.fixtureResolve = resolve; }); });
        form.requestSubmit(); form.requestSubmit();
      });
      assert.equal(await page.evaluate(() => window.fixtureCalls), 1);
      assert.equal(await form.getAttribute('aria-busy'), 'true');
      assert.equal(await form.getByRole('button', { name: 'Save example' }).isDisabled(), true);
      await page.evaluate(() => window.fixtureResolve({ state: 'conflict', message: 'Review the latest version before reapplying your draft.' }));
      await form.locator('[data-pk-operation-status]').filter({ hasText: 'Review the latest version' }).waitFor();
      assert.equal(await name.inputValue(), 'Example');
      await page.evaluate(async () => {
        const { bindOperation } = await import('/assets/interactions.mjs');
        bindOperation(document.querySelector('[data-pk-demo-form]'), async () => { throw new Error('Response lost'); });
      });
      await form.getByRole('button', { name: 'Save example' }).click();
      await form.locator('[data-pk-operation-status]').filter({ hasText: 'couldn’t confirm' }).waitFor();
      assert.equal(await form.getAttribute('data-pk-state'), 'unknown');
      assert.equal(await description.inputValue(), 'Keep this draft');
      await page.evaluate(async () => {
        const { bindOperation } = await import('/assets/interactions.mjs');
        bindOperation(document.querySelector('[data-pk-demo-form]'), async () => ({ state: 'failure', message: 'Service unavailable. Your draft is still here.' }));
      });
      await form.getByRole('button', { name: 'Save example' }).click();
      await form.locator('[data-pk-operation-status]').filter({ hasText: 'Service unavailable' }).waitFor();
      assert.equal(await description.inputValue(), 'Keep this draft');
      await page.evaluate(async () => {
        const { bindOperation } = await import('/assets/interactions.mjs');
        bindOperation(document.querySelector('[data-pk-demo-form]'), async () => ({ state: 'validation', errors: {} }), { pending: 'Bezig…', unknown: 'Resultaat onbekend.' });
      });
      await form.getByRole('button', { name: 'Save example' }).click();
      await form.locator('[data-pk-operation-status]').filter({ hasText: 'Resultaat onbekend.' }).waitFor();
      await page.evaluate(async () => {
        const { bindOperation } = await import('/assets/interactions.mjs');
        const form = document.querySelector('[data-pk-demo-form]');
        const dispose = bindOperation(form, () => new Promise(resolve => { window.fixtureResolve = resolve; }));
        form.requestSubmit(); dispose();
        window.fixtureResolve({ state: 'success', message: 'Late success must not replace current state' });
      });
      assert.equal(await form.locator('[data-pk-operation-status]').textContent(), 'Saving…');
      assert.equal(await form.getByRole('button', { name: 'Save example' }).isDisabled(), false);
      // Server-admitted text remains text, not markup, and summaries link to actual fields.
      await page.evaluate(async () => {
        const { presentFormErrors } = await import('/assets/interactions.mjs');
        presentFormErrors(document.querySelector('[data-pk-demo-form]'), { 'example-name': '<img src=x onerror=alert(1)> is not a valid name' });
      });
      assert.equal(await form.locator('.pk-error img').count(), 0);
      results.push({ engine, case: 'forms', validation: 'passed', preservedInput: 'passed', conflict: 'passed', unknown: 'passed', malformedOutcome: 'passed', serviceFailure: 'passed', duplicateSubmission: 'passed', staleCallback: 'passed' });
    }
    if (selectedCases.has('motion')) {
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.goto(`${origin}/__gallery/product-shell`);
      const opener = page.getByRole('button', { name: 'Open confirmation' });
      assert(parseFloat(await opener.evaluate(el => getComputedStyle(el).transitionDuration)) > 0);
      await opener.click();
      assert(parseFloat(await page.locator('dialog').evaluate(el => getComputedStyle(el).animationDuration)) > 0);
      assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Cancel');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('dialog').evaluate(el => el.open), false);
      await page.emulateMedia({ reducedMotion: 'reduce' }); await opener.click();
      assert.equal(await opener.evaluate(el => getComputedStyle(el).transitionDuration), '0s');
      assert.equal(await page.locator('dialog').evaluate(el => getComputedStyle(el).animationName), 'none');
      await page.keyboard.press('Escape');
      results.push({ engine, case: 'motion', normalAndReducedMotion: 'passed', interruptedDialog: 'passed' });
    }
    if (selectedCases.has('auth')) {
      for (const state of authStates) {
        for (const scheme of ['light', 'dark']) {
          await page.emulateMedia({ colorScheme: scheme, reducedMotion: 'no-preference' });
          await page.setViewportSize({ width: 390, height: 844 });
          await page.goto(`${origin}/__auth/${state}`);
          assert.equal(await page.locator('body').getAttribute('data-auth-state'), state);
          await assertNoPageOverflow(page, `${engine}/${state}/${scheme}`);
          assert.equal(await page.locator('[data-pk-slot]').count(), 1);
          assert.equal(await page.locator('input[type=password]').count(), 0);
          const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
          assert.deepEqual(axe.violations.map(v => v.id), [], `${engine}/${state}/${scheme}`);
          await page.screenshot({ path: resolve(evidence, `${engine}-auth-${state}-${scheme}.png`), animations: 'disabled' });
        }
      }
      // Cascade fixture: v2's important white header and the scaffold's gradient.
      // This tests the brand bridge; actual selected-provider flow acceptance remains separate.
      for (const scheme of ['light', 'dark']) {
        await page.emulateMedia({ colorScheme: scheme });
        await page.setContent(`<!doctype html><html class="login-pf"><head>
          <style>#kc-header-wrapper { color: white !important; }
          .pf-v5-c-button.pf-m-primary { background: linear-gradient(#4f46e5, #06b6d4); }
          </style><link rel="stylesheet" href="${origin}/__keycloak-brand.css"></head><body>
          <header id="kc-header-wrapper">Brand presentation fixture</header>
          <main class="pf-v5-c-login__main"><button id="recovery-submit" class="pf-v5-c-button pf-m-primary">Reset password</button></main>
          </body></html>`, { waitUntil: 'networkidle' });
        const colors = await page.evaluate(() => {
          const expected = document.createElement('div');
          expected.style.color = 'var(--pk-on-surface)';
          expected.style.backgroundColor = 'var(--pk-raised)';
          document.body.append(expected);
          const value = { header: getComputedStyle(document.querySelector('#kc-header-wrapper')).color,
            expectedHeader: getComputedStyle(expected).color,
            card: getComputedStyle(document.querySelector('.pf-v5-c-login__main')).backgroundColor,
            expectedCard: getComputedStyle(expected).backgroundColor };
          expected.style.color = 'var(--pk-on-primary)';
          expected.style.backgroundColor = 'var(--pk-primary)';
          const button = getComputedStyle(document.querySelector('#recovery-submit'));
          Object.assign(value, { button: button.backgroundColor, expectedButton: getComputedStyle(expected).backgroundColor,
            buttonText: button.color, expectedButtonText: getComputedStyle(expected).color, buttonImage: button.backgroundImage });
          expected.remove();
          return value;
        });
        for (const role of ['header', 'card', 'button', 'buttonText']) {
          assert.equal(colors[role], colors['expected' + role[0].toUpperCase() + role.slice(1)], `${engine}/Keycloak-v2/${scheme}/${role}`);
        }
        assert.equal(colors.buttonImage, 'none', `${engine}/Keycloak-v2/${scheme}/scaffold-gradient`);
      }
      results.push({ engine, case: 'auth', brandedStates: 'passed', keycloakBrandCascade: 'passed', providerFlow: 'consumer acceptance required' });
    }
  } finally { await context.close(); }
}

try {
  for (const { name, browserType } of engines) {
    const browser = await browserType.launch();
    try {
      if (selectedCases.has('gallery')) {
        await verifyDesktop(name, browser);
        for (const profile of deviceProfiles.filter(candidate => candidate.engine === name)) {
          await verifyTouchDevice(profile, browser);
        }
      }
      if (modern) await verifyModern(name, browser);
      if (selectedCases.has('durability')) {
        await recordDurabilityCase(durabilityAdapter.createContract, { browser, engine: name }, results);
      }
    } finally {
      await browser.close();
    }
  }
  assert.deepEqual(errors, []);
} finally {
  await new Promise(resolve => server.close(resolve));
  await writeFile(resolve(evidence, 'report.json'), JSON.stringify({ results, errors,
    engines: requestedEngineNames,
    cases: modern ? [...selectedCases] : [...selectedCases].filter(c => c === 'gallery' || c === 'durability'),
    scope: 'Selected desktop engines plus their emulated touch phone/tablet fixture checks; not full WCAG certification, physical-device/virtual-keyboard proof, actual browser zoom, assistive-technology task acceptance, or production field performance.' }, null, 2));
}
console.log(`UI browser acceptance passed: ${results.length} recorded scenario groups.`);

import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { chromium, firefox, webkit } from '__PLAYWRIGHT__';
import AxeBuilder from '__AXE__';
import { modules } from '__PRESENTATION_RECORDING__';

const [output, engines] = process.argv.slice(2);
const requested = engines.split(',');
const types = { chromium, firefox, webkit };
const server = createServer(async (request, response) => {
  const url = new URL(request.url, 'http://localhost');
  const mode = url.searchParams.get('state') ?? 'mounted';
  const before = url.searchParams.has('before');
  try {
    if (Object.hasOwn(modules, url.pathname)) {
      response.setHeader('Content-Type', 'text/javascript'); response.end(modules[url.pathname]);
    } else if (url.pathname === '/auth/assets/v1/page.css') {
      response.setHeader('Content-Type', 'text/css'); response.end('');
    } else if (url.pathname.endsWith('.html')) {
      response.setHeader('Content-Type', 'text/html');
      response.end(await readFile(resolve(output, url.pathname.slice(1))));
    } else if (url.pathname.includes('/bootstrap/')) {
      const theme = url.pathname.split('/')[3];
      if (request.headers.referer?.includes('state=loading')) {
        // Keep the actual selected loader in its loading state without business effects.
        return;
      }
      response.setHeader('Content-Type', 'application/json');
      const value = JSON.parse(await readFile(resolve(output, theme + '.json')));
      value.runtime += '?state=' + (request.headers.referer?.includes('state=failed') ? 'failed' : 'mounted');
      response.end(JSON.stringify(value));
    } else if (url.pathname.endsWith('.css')) {
      response.setHeader('Content-Type', 'text/css');
      const name = url.pathname.includes('/static/') ? 'foundation.css' : 'runtime.css';
      // CSS inherits page query via referer; the before case uses the retained old scaffold.
      const previous = request.headers.referer?.includes('before=1');
      response.end(await readFile(resolve(output, name === 'runtime.css' && previous ? 'before-runtime.css' : name)));
    } else if (url.pathname.includes('/static/')) {
      response.setHeader('Content-Type', 'text/javascript');
      response.end(await readFile(resolve(output, 'loader.js')));
    } else if (url.pathname.endsWith('runtime.js')) {
      response.setHeader('Content-Type', 'text/javascript');
      response.end(mode === 'failed' ? 'export function mount(){throw new Error("fixture mount failure");}' : await readFile(resolve(output, 'runtime.js')));
    } else {
      response.writeHead(404); response.end();
    }
  } catch { response.writeHead(500); response.end('Owned fixture failed'); }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const origin = 'http://127.0.0.1:' + server.address().port;
const result = { scope: 'Exact selected renderer and loader + Vite generated runtime/CSS; not full publisher host activation.',
  visitedScope: 'Browsers mask visited computed colors. Assert actual authored visited rule/token contrast against rendered surface; no visited-history inference.',
  axeScope: 'Axe serious/critical checks cover loading, mounted and failed states with page scripting enabled. No-script uses real disabled-script DOM, contrast, semantics and focus; async axe callbacks cannot run in that context.',
  before: [], after: [], failures: [] };

function luminance(rgb) {
  const values = rgb.map(value => { const s = value / 255; return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; });
  return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
}
function ratio(a, b) { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
function rgb(value) { return value.match(/[\d.]+/g).slice(0, 3).map(Number); }

async function check(browser, engine, theme, colorScheme, state, before) {
  const started = performance.now();
  const context = await browser.newContext({ colorScheme, javaScriptEnabled: state !== 'noscript', viewport: { width: 320, height: 700 } });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const phase = async value => await writeFile(resolve(output, 'phase.json'), JSON.stringify({ engine, theme, colorScheme, state, phase: value }));
  try {
    await phase('navigation');
    await page.goto(origin + '/' + theme + '.html?state=' + state + (before ? '&before=1' : ''), { waitUntil: 'commit' });
    await page.locator('h1').first().waitFor();
    if (state === 'mounted') await page.locator('#foundation-status').waitFor({ state: 'hidden' });
    const startupToOperationMs = performance.now() - started;
    if (state === 'failed') await page.locator('#foundation-status[role=alert]').waitFor();
    if (state === 'noscript') await page.locator('noscript p').waitFor();
    await phase('authored-controls');
    // Controlled authored content exercises inherited envelope colors and native controls.
    // This is fixture DOM, distinct from the generated app's real mount assertion above.
    await page.evaluate(() => {
      const section = document.createElement('section');
      section.innerHTML = '<h2>Controls</h2><p><a href="#fixture-target">Read more</a></p><label for="fixture-input">Name</label><input id="fixture-input" placeholder="Name"><button>Continue</button>';
      document.querySelector('main').append(section);
    });
    const colors = await page.evaluate(() => {
      const background = element => {
        for (let current = element; current; current = current.parentElement) {
          const value = getComputedStyle(current).backgroundColor;
          if (value !== 'rgba(0, 0, 0, 0)' && value !== 'transparent') return value;
        }
        return getComputedStyle(document.documentElement).backgroundColor;
      };
      const selectors = ['body', 'main', 'h1', 'h2', 'p', 'a', 'input', 'button', '#foundation-status', 'noscript p'];
      const values = selectors.flatMap(selector => [...document.querySelectorAll(selector)]
        .filter(node => node.getClientRects().length).map(node => ({ selector, foreground: getComputedStyle(node).color, background: background(node) })));
      return { values, surface: getComputedStyle(document.querySelector('main')).backgroundColor,
        visited: getComputedStyle(document.documentElement).getPropertyValue('--pk-visited').trim(),
        visitedRule: [...document.styleSheets].flatMap(sheet => [...sheet.cssRules]).some(rule => rule.selectorText === 'a:visited' && rule.style.color === 'var(--pk-visited)'),
        reflow: document.documentElement.scrollWidth <= 320 };
    });
    const contrasts = colors.values.map(value => ({ ...value, ratio: ratio(rgb(value.foreground), rgb(value.background)) }));
    await phase('contrast');
    const violations = contrasts.filter(value => value.ratio < 4.5);
    let visitedRatio = null;
    if (!before) {
      assert(colors.visitedRule, 'Authored visited link rule is absent');
      visitedRatio = ratio(colors.visited.slice(1).match(/../g).map(value => parseInt(value, 16)), rgb(colors.surface));
      assert(visitedRatio >= 4.5, 'Visited link token contrast failed');
      assert(colors.reflow, '320px envelope reflow failed');
      await page.locator('a').focus();
      const focus = await page.locator('a').evaluate(node => ({ width: getComputedStyle(node).outlineWidth, color: getComputedStyle(node).outlineColor }));
      assert.equal(focus.width, '3px');
      assert(ratio(rgb(focus.color), rgb(colors.surface)) >= 3, 'Focus contrast failed');
      if (state === 'noscript') {
        assert.equal(await page.locator('#foundation-form > *').count(), 0);
        assert(await page.locator('noscript p').isVisible());
      } else {
        await phase('axe');
        const accessibility = await new AxeBuilder({ page }).analyze();
        const serious = accessibility.violations.filter(value => ['serious', 'critical'].includes(value.impact));
        assert.deepEqual(serious.map(value => value.id), [], 'Serious accessibility violations');
      }
      assert.equal(violations.length, 0, JSON.stringify(violations));
    }
    return { engine, theme, colorScheme, state, startupToOperationMs, contrasts, visitedRatio, violations };
  } finally { await context.close(); }
}

try {
  for (const engine of requested) {
    const browser = await types[engine].launch({ headless: true });
    try {
      for (const theme of ['blue', 'green', 'slate']) for (const colorScheme of ['light', 'dark']) {
        result.before.push(await check(browser, engine, theme, colorScheme, 'mounted', true));
        for (const state of ['loading', 'mounted', 'failed', 'noscript']) {
          try { result.after.push(await check(browser, engine, theme, colorScheme, state, false)); }
          catch (error) { result.failures.push({ engine, theme, colorScheme, state, message: error.message }); }
          await writeFile(resolve(output, 'progress.json'), JSON.stringify({ before: result.before.length, after: result.after.length, failures: result.failures }, null, 2));
        }
      }
    } finally { await browser.close(); }
  }
  assert(result.before.some(value => value.violations.length), 'Retained before scaffold did not reproduce contrast defect');
  assert.equal(result.failures.length, 0, JSON.stringify(result.failures));
  result.status = 'passed';
  console.log(`${result.after.length} selected renderer palette cases passed; before defect reproduced in ${result.before.filter(value => value.violations.length).length} cases.`);
} catch (error) { result.status = 'failed'; console.error(error.message); process.exitCode = 2; }
finally {
  await writeFile(resolve(output, 'result.json'), JSON.stringify(result, null, 2));
  server.closeAllConnections();
  await new Promise(done => server.close(done));
}

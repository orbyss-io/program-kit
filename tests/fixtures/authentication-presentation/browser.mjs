import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { chromium, webkit, firefox } from '__PLAYWRIGHT__';

// These are exact HTML bytes emitted by the compiled owner example. This server only serves
// presentation; it does not simulate Foundation cookies, a BFF, Keycloak, or callback expiry.
const output = process.argv[2];
const engines = process.argv[3].split(',');
const server = createServer(async (request, response) => {
  const name = new URL(request.url, 'http://fixture.invalid').pathname.slice(1);
  if (!['error-anonymous.html', 'error-existing.html', 'session-ended.html', 'session-existing.html', 'login-restored.html', 'denied-restored.html', 'session-restored.html'].includes(name)) {
    response.writeHead(404).end(); return;
  }
  response.writeHead(200, {'content-type':'text/html; charset=utf-8', 'cache-control':'no-store'});
  response.end(await readFile(output + '/' + name));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = 'http://127.0.0.1:' + server.address().port;
const results = [];
try {
  for (const engine of engines) {
    const browser = await ({chromium, webkit, firefox})[engine].launch({headless:true});
    try {
      const page = await browser.newPage();
      for (const [name, title, existing] of [
        ['error-anonymous.html', 'Sign-in needs attention', false],
        ['error-existing.html', 'Sign-in needs attention', true],
        ['session-ended.html', 'Your application session has ended', false],
        ['session-existing.html', 'Your application session is still active', true],
        ['login-restored.html', 'Sign-in needs attention', false],
        ['denied-restored.html', 'Sign-in needs attention', false],
        ['session-restored.html', 'Your application session has ended', false],
      ]) {
        await page.goto(origin + '/' + name);
        assert.equal(await page.title(), title + ' — Example <Workspace>');
        const heading = page.getByRole('heading', {name:title,exact:true});
        assert.equal(await heading.isVisible(), true);
        assert.equal(await page.locator('main[aria-labelledby="recovery-title"]').count(), 1);
        await page.waitForFunction(() => document.activeElement?.id === 'recovery-title');
        assert.equal(await page.getByRole('link', {name:'Continue to your workspace'}).count(), existing ? 1 : 0);
        const retry = page.getByRole('link', {name:'Start a fresh sign-in',exact:true});
        assert.equal(await retry.getAttribute('href'), '/tenant/bff/login?returnUrl=%2Ftenant%2Fworkspace');
        const traversal = 'Tab';
        await page.keyboard.press(traversal);
        assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'A', engine + ':' + name + ':' + traversal);
        assert.equal(await page.locator('script').count(), 0);
        results.push({engine, page:name, branded:true, headingFocus:true, keyboardRecovery:true, traversal});
      }
    } finally { await browser.close(); }
  }
  console.log(JSON.stringify({scope:'Compiled owner presentation HTML in real browsers; no Foundation/provider/consumer authentication proof.',results}));
} finally { await new Promise(resolve => server.close(resolve)); }

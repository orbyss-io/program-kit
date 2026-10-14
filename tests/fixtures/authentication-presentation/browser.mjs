import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { stripTypeScriptTypes } from 'node:module';
import { chromium, webkit, firefox } from '__PLAYWRIGHT__';

// These are exact HTML bytes emitted by the compiled owner example. This server only serves
// presentation; it does not simulate Foundation cookies, a BFF, Keycloak, or callback expiry.
const output = process.argv[2];
const engines = process.argv[3].split(',');
const focusModule = stripTypeScriptTypes(await readFile(output + '/../authentication-recovery-focus.ts', 'utf8'), {mode:'strip'});
const server = createServer(async (request, response) => {
  const name = new URL(request.url, 'http://fixture.invalid').pathname.slice(1);
  if (name === 'tenant/assets/authentication-recovery-focus.js') {
    response.writeHead(200, {'content-type':'text/javascript', 'cache-control':'no-store'}).end(focusModule); return;
  }
  if (!['error-anonymous.html', 'error-existing.html', 'session-ended.html', 'session-existing.html', 'login-restored.html', 'denied-restored.html', 'session-restored.html'].includes(name)) {
    response.writeHead(404).end(); return;
  }
  response.writeHead(200, {'content-type':'text/html; charset=utf-8', 'cache-control':'no-store',
    'content-security-policy': "default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"});
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
        await page.waitForFunction(() => document.hasFocus() && document.activeElement?.id === 'recovery-title');
        assert.equal(await page.getByRole('link', {name:'Continue to your workspace'}).count(), existing ? 1 : 0);
        const retry = page.getByRole('link', {name:'Start a fresh sign-in',exact:true});
        assert.equal(await retry.getAttribute('href'), '/tenant/bff/login?returnUrl=%2Ftenant%2Fworkspace');
        const traversal = 'Tab';
        await page.keyboard.press(traversal);
        assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'A', engine + ':' + name + ':' + traversal);
        assert.equal(await page.locator('script').count(), 1);
        assert.equal(await page.locator('script').getAttribute('src'), '/tenant/assets/authentication-recovery-focus.js');
        assert.equal(await page.locator('script').textContent(), '');
        results.push({engine, page:name, branded:true, headingFocus:true, keyboardRecovery:true, traversal});
      }
      const foreground = await browser.newPage(); await foreground.goto('about:blank');
      await foreground.bringToFront();
      await page.goto(origin + '/session-ended.html');
      await page.bringToFront();
      await page.waitForFunction(() => document.hasFocus() && document.activeElement?.id === 'recovery-title');
      results.push({engine, case:'background-owner-activation', headingFocus:true});
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'A');
      await foreground.bringToFront(); await page.bringToFront();
      assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'A');
      results.push({engine, case:'selected-recovery-control-preserved', userFocusPreserved:true});
      await foreground.close();
      const noScript = await browser.newContext({javaScriptEnabled:false});
      try {
        const fallback = await noScript.newPage(); await fallback.goto(origin + '/session-ended.html');
        assert.equal(await fallback.getByRole('heading', {name:'Your application session has ended',exact:true}).isVisible(), true);
        assert.equal(await fallback.getByRole('link', {name:'Start a fresh sign-in',exact:true}).getAttribute('href'), '/tenant/bff/login?returnUrl=%2Ftenant%2Fworkspace');
        assert.equal(await fallback.getByRole('status').textContent(), 'This application has no active session. Provider sign-out has not been confirmed; its session may still be active.');
        results.push({engine, case:'no-script-public-recovery', publicRecovery:true});
      } finally { await noScript.close(); }
    } finally { await browser.close(); }
  }
  console.log(JSON.stringify({scope:'Compiled owner presentation HTML in real browsers; no Foundation/provider/consumer authentication proof.',results}));
} finally { await new Promise(resolve => server.close(resolve)); }

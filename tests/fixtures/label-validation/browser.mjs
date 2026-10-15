import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const [workspace, playwrightModule, engineNames] = process.argv.slice(2);
const playwright = await import(pathToFileURL(playwrightModule).href);
const generated = await readFile(workspace + '/generated/labels.js', 'utf8');
const observations = [];
for (const engine of engineNames.split(',')) {
  if (!['chromium', 'firefox', 'webkit'].includes(engine)) throw new Error('Unsupported engine: ' + engine);
  const browser = await playwright[engine].launch({ headless: true });
  try {
    const context = await browser.newContext(engine === 'chromium' ? { permissions: ['clipboard-read', 'clipboard-write'] } : {});
    const page = await context.newPage();
    let admissionRequests = 0;
    page.on('request', request => {
      if (new URL(request.url()).pathname === '/action-admissions') admissionRequests++;
    });
    await page.route('**/*', route => new URL(route.request().url()).pathname === '/action-admissions'
      ? route.fulfill({ contentType: 'application/json', body: '{"admitted":true}' })
      : route.fulfill({ contentType: 'text/html', body: '<label for="label">Display label</label><textarea id="label" rows="1"></textarea><button id="create">Create</button><p id="error" role="alert"></p><input id="native" type="text">' }));
    await page.goto('https://normalization.invalid');
    await page.addScriptTag({ type: 'module', content: generated + `
      const field = document.querySelector('#label');
      window.admissions = 0;
      document.querySelector('#create').addEventListener('click', async () => {
        const result = normalizeLabel('displayLabel', field.value);
        document.querySelector('#error').textContent = result.valid ? '' : result.error.code;
        field.setAttribute('aria-invalid', String(!result.valid));
        if (result.valid) {
          await fetch('/action-admissions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: result.value }) });
          window.admissions++;
        }
      });
      window.validationReady = true;
    ` });
    await page.waitForFunction(() => window.validationReady === true);
    const raw = ' ' + 'x'.repeat(120) + ' ';
    if (engine === 'chromium') {
      await page.evaluate(value => navigator.clipboard.writeText(value), raw);
      await page.locator('#label').focus(); await page.keyboard.press('Control+V');
    } else {
      await page.locator('#label').focus(); await page.keyboard.insertText(raw);
    }
    assert.equal(await page.locator('#label').inputValue(), raw);
    await page.locator('#create').click();
    await page.waitForFunction(() => window.admissions === 1);
    assert.equal(await page.evaluate(() => window.admissions), 1);
    assert.equal(admissionRequests, 1);
    const overlong = 'x'.repeat(121);
    await page.locator('#label').fill('');
    if (engine === 'chromium') {
      await page.evaluate(value => navigator.clipboard.writeText(value), overlong);
      await page.locator('#label').focus(); await page.keyboard.press('Control+V');
    } else {
      await page.locator('#label').focus(); await page.keyboard.insertText(overlong);
    }
    await page.locator('#create').click();
    assert.equal(await page.locator('#label').inputValue(), overlong);
    assert.equal(await page.locator('#error').textContent(), 'normalized_length');
    assert.equal(await page.evaluate(() => window.admissions), 1);
    assert.equal(admissionRequests, 1);
    const controlled = '\tValid label\n';
    await page.locator('#label').fill('');
    if (engine === 'chromium') {
      await page.evaluate(value => navigator.clipboard.writeText(value), controlled);
      await page.locator('#label').focus(); await page.keyboard.press('Control+V');
      await page.locator('#native').focus(); await page.keyboard.press('Control+V');
      assert.equal(await page.locator('#native').inputValue(), '\tValid label');
    } else {
      await page.locator('#label').focus(); await page.keyboard.insertText(controlled);
    }
    assert.equal(await page.locator('#label').inputValue(), controlled);
    await page.locator('#create').click();
    assert.equal(await page.locator('#error').textContent(), 'control_character');
    assert.equal(await page.locator('#label').inputValue(), controlled);
    assert.equal(await page.evaluate(() => window.admissions), 1);
    assert.equal(admissionRequests, 1);
    observations.push({ engine, rawInputPreserved: true, validAdmissionHttpRequests: admissionRequests, invalidAdmissionHttpRequests: 0,
      clipboardPaste: engine === 'chromium', overlongClipboardPaste: engine === 'chromium', nativeTextInputStripsLf: engine === 'chromium',
      scope: 'Observed browser request guard with synthetic admission response; native server refusal tested separately.' });
  } finally { await browser.close(); }
}
console.log(JSON.stringify({ observations }));

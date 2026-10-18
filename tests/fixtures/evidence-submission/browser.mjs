import assert from 'node:assert/strict';
import {writeFile,copyFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {chromium, webkit, firefox} from '__PLAYWRIGHT__';
import AxeBuilder from '__AXE__';

const [origin, output, engineList] = process.argv.slice(2);
// Actual selected native document -> maintained generator -> current consumer compiler -> served client.
const generate = spawnSync(process.execPath, ['__OPENAPI_TYPESCRIPT__',output+'/evidence.openapi.json','-o',output+'/client-source/types.ts'], {encoding:'utf8'});
await writeFile(output+'/client-generate.stdout.txt',generate.stdout);
await writeFile(output+'/client-generate.stderr.txt',generate.stderr);
assert.equal(generate.status,0,'native OpenAPI client generation failed');
const compiler = ['__TYPESCRIPT__',output+'/client-source/client.ts','--outDir',output+'/client-built','--strict','--skipLibCheck','--module','ES2022','--moduleResolution','bundler','--target','ES2023'];
const compile = spawnSync(process.execPath,compiler,{encoding:'utf8'});
await writeFile(output+'/client-compile.stdout.txt',compile.stdout);
await writeFile(output+'/client-compile.stderr.txt',compile.stderr);
assert.equal(compile.status,0,'actual generated-client adapter did not compile');
await copyFile(output+'/client-built/client.js',output+'/web/client.js');
await writeFile(output+'/client-source/invalid.ts',"import type {components} from './types'; const invalid:components['schemas']['EvidenceRequest']={title:'x',date:'2026-10-18',content:7};\n");
const invalid = spawnSync(process.execPath,['__TYPESCRIPT__',output+'/client-source/invalid.ts','--noEmit','--strict','--skipLibCheck','--module','ES2022','--moduleResolution','bundler','--target','ES2023'],{encoding:'utf8'});
await writeFile(output+'/client-invalid.stdout.txt',invalid.stdout);
await writeFile(output+'/client-invalid.stderr.txt',invalid.stderr);
assert.notEqual(invalid.status,0,'independent invalid wire type compiled');
const outcomes = [];
for (const engine of engineList.split(',')) {
  const browser = await ({chromium, webkit, firefox})[engine].launch({headless:true});
  const context = await browser.newContext({viewport:{width:1280,height:1000}});
  try {
    const page = await context.newPage();
    const faults = [];
    page.on('pageerror', error => faults.push(error.name));
    const preparations = [];
    let acceptCount = 0;
    page.on('request', request => {
      if (request.method() === 'POST' && request.url().endsWith('/desk/api/evidence')) preparations.push(request.postDataJSON());
      if (request.method() === 'POST' && /\/accept$/u.test(request.url())) acceptCount++;
    });
    await page.goto(origin);
    await page.getByRole('heading', {name:'Put the right evidence in view.'}).waitFor();
    await page.locator('#private-workspace:not([hidden])').waitFor();
    assert.equal(await page.locator('#empty').isVisible(), true);
    await page.screenshot({path:`${output}/${engine}-desktop-empty.png`,fullPage:true});
    await page.getByRole('button', {name:'Review submission',exact:true}).click();
    assert.equal(await page.locator('[data-pk-error-summary]').isVisible(), true);
    assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-pk-error-summary')), true);
    await page.screenshot({path:`${output}/${engine}-desktop-errors.png`,fullPage:true});
    assert.equal(preparations.length, 0);
    const title = `Browser evidence ${engine}`;
    await page.getByLabel('Evidence date', {exact:true}).fill('2026-10-18');
    const file = {name:'fictional-note.txt',mimeType:'text/plain',buffer:Buffer.from('fictional browser evidence')};
    await page.getByLabel('Text file', {exact:true}).setInputFiles(file);
    // Commit the date editor before awaiting the current generation. WebKit can
    // defer its change event until blur, correctly invalidating an earlier read.
    await page.locator('#title').focus();
    await page.getByRole('status').filter({hasText:'fictional-note.txt is ready'}).waitFor();
    // Inject only after file/date preparation, immediately at the boundary under test.
    await page.locator('#title').evaluate(input => {input.value='\u0001invalid title';});
    assert.equal(await page.locator('#title').inputValue(),'\u0001invalid title');
    await page.getByRole('button', {name:'Review submission',exact:true}).click();
    await page.locator('#title-error').filter({hasText:'Check the title and current file before review.'}).waitFor();
    assert.equal(preparations.length,0);
    await page.getByLabel('Evidence title', {exact:true}).fill(title);
    await page.getByRole('button', {name:'Sign out',exact:true}).click();
    const nativeDialog = page.getByRole('dialog', {name:'Sign out?',exact:true});
    await nativeDialog.waitFor();
    await page.screenshot({path:`${output}/${engine}-native-signout.png`});
    await nativeDialog.getByRole('button', {name:'Keep working',exact:true}).click();
    assert.equal(await page.getByLabel('Evidence title', {exact:true}).inputValue(), title);
    assert.equal(preparations.length, 0);
    await page.getByRole('button', {name:'Review submission',exact:true}).click();
    await page.getByRole('dialog', {name:'Submit this evidence?',exact:true}).waitFor();
    await page.getByRole('button', {name:'Keep editing',exact:true}).click();
    assert.equal(await page.evaluate(() => document.activeElement.id), 'review');
    assert.equal(preparations.length, 0);
    await page.getByRole('button', {name:'Review submission',exact:true}).click();
    const rendered = await new AxeBuilder({page}).analyze();
    assert.deepEqual(rendered.violations.map(value => value.id), []);
    await page.screenshot({path:`${output}/${engine}-desktop-confirmation.png`});
    let retained;
    await page.route('**/desk/api/evidence/*/accept', async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 200);
      retained = await response.json();
      await route.abort('failed');
    });
    await page.getByRole('button', {name:'Confirm and submit',exact:true}).click();
    await page.getByRole('button', {name:'Check retained submission',exact:true}).waitFor();
    await page.screenshot({path:`${output}/${engine}-desktop-unknown.png`,fullPage:true});
    assert.equal(preparations.length, 1);
    assert.equal(acceptCount, 1);
    assert.equal(preparations[0].title, title);
    assert.equal(preparations[0].date, '2026-10-18');
    assert.equal(Buffer.from(preparations[0].content,'base64').toString(), 'fictional browser evidence');
    // Later edits cannot replace the exact confirmed request or dispatch another acceptance.
    await page.getByLabel('Evidence title', {exact:true}).fill('Edited after uncertain completion');
    await page.getByRole('button', {name:'Check retained submission',exact:true}).click();
    await page.getByRole('status').filter({hasText:`${title} accepted for review.`}).waitFor();
    assert.equal(await page.locator('#receipts li').count(), 1);
    assert.equal(preparations.length, 1); assert.equal(acceptCount, 1);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({path:`${output}/${engine}-mobile-accepted.png`,fullPage:true});
    const mobile = await new AxeBuilder({page}).analyze();
    assert.deepEqual(mobile.violations.map(value => value.id), []);
    // Exact selected session module hides/clears private DOM on failed fresh observation.
    await page.route('**/bff/user', route => route.fulfill({status:200,contentType:'application/json',body:'{"authenticated":false}'}));
    await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow')));
    await page.getByText('Session unavailable. Return through the workspace entry.', {exact:true}).waitFor();
    assert.equal(await page.locator('#private-workspace').textContent(), '');
    // A real FileReader completes into controlled late crypto. Actual native sign-out
    // disposes the UI before the hash resumes; the continuation must remain silent.
    const pending = await context.newPage();
    pending.on('pageerror',error => faults.push(error.name));
    let pendingRequests=0;
    pending.on('request',request => {if(request.method()==='POST') pendingRequests++;});
    await pending.addInitScript(() => {
      const original=crypto.subtle.digest.bind(crypto.subtle);
      crypto.subtle.digest=async (...arguments_) => {
        await new Promise(resolve => {window.releaseFictionalHash=resolve;});
        const result=await original(...arguments_);
        window.fictionalHashCompleted=true;
        return result;
      };
    });
    await pending.goto(origin);
    await pending.locator('#private-workspace:not([hidden])').waitFor();
    await pending.getByLabel('Evidence date',{exact:true}).fill('2026-10-18');
    await pending.getByLabel('Text file',{exact:true}).setInputFiles(file);
    await pending.waitForFunction(() => typeof window.releaseFictionalHash==='function');
    await pending.getByRole('button',{name:'Sign out',exact:true}).click();
    await pending.getByRole('dialog',{name:'Sign out?',exact:true}).getByRole('button',{name:'Sign out',exact:true}).click();
    await pending.waitForFunction(() => document.querySelector('#private-workspace').textContent==='');
    await pending.evaluate(() => window.releaseFictionalHash());
    await pending.waitForFunction(() => window.fictionalHashCompleted===true);
    await pending.evaluate(() => new Promise(requestAnimationFrame));
    assert.equal(pendingRequests,0);
    assert.equal(await pending.locator('#private-workspace').textContent(),'');
    await pending.close();
    assert.deepEqual(faults, []);
    outcomes.push({engine, receipt:retained, actualControls:true, nativeConfirmation:true, sessionBoundary:true,
      empty:true, fieldErrorsAndFocus:true, immutableConfirmation:true, lostAcknowledgment:true,
      retainedReconciliation:true, acceptanceRequests:acceptCount, desktopMobile:true, axe:true, signOutDuringCrypto:true});
  } finally { await context.close(); await browser.close(); }
}
await writeFile(output + '/browser-result.json', JSON.stringify({outcomes,nativeDocumentGeneratedClient:true,strictClientCompilation:true,invalidWireTypeRejected:true,limits:['Fictional identity/session projections; native modules execute but no real BFF/provider login or sign-out claim.','Runtime native document and generator; no new cold package export, breaking-change comparison or package qualification claim.','Screens and axe support human review; they do not establish product acceptance.']},null,2));
console.log('Actual evidence browser outcomes: ' + outcomes.length);

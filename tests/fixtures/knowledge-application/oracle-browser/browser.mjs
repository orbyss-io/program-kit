import { createRequire } from 'node:module';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
const args = Object.fromEntries(process.argv.slice(2).map(v => { const i = v.indexOf('='); return [v.slice(2,i),v.slice(i+1)]; }));
const require = createRequire(args.modules ? join(resolve(args.modules),'package.json') : import.meta.url);
const { chromium, firefox, webkit, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
function version(id) {
  let directory=dirname(require.resolve(id));
  for(let i=0;i<5;i++,directory=dirname(directory)) {
    const path=join(directory,'package.json');
    if(existsSync(path)) { const value=JSON.parse(readFileSync(path,'utf8')); if(value.name===id)return value.version; }
  }
  throw new Error('Installed oracle package metadata missing');
}
if (version('@playwright/test') !== '1.62.1' || version('@axe-core/playwright') !== '4.13.0') throw new Error('Oracle runtime pins differ from reviewed fixture');
const url = new URL(args.url);
if (url.protocol !== 'http:' || !['127.0.0.1','localhost','[::1]'].includes(url.hostname)) throw new Error('Disposable loopback required');
const report = {schemaVersion:1,status:'failed',checks:[],engines:[]};
mkdirSync(dirname(args.output),{recursive:true});
try {
  for (const name of (args.engines ?? 'chromium,firefox,webkit').split(',')) {
    const engine = {chromium,firefox,webkit}[name];
    if (!engine) throw new Error('Unknown browser engine');
    const browser = await engine.launch({headless:true});
    try {
      const context = await browser.newContext();
      const page = await context.newPage();
      await page.route('**/*', route => new URL(route.request().url()).origin === url.origin ? route.continue() : route.abort());
      const reset = await context.request.post(url.origin + '/__acceptance/reset');
      expect(reset.status()).toBe(200);
      await page.goto(url.origin);
      await expect(page.getByRole('heading',{name:'Equipment lending',exact:true})).toBeVisible();
      await page.getByRole('button',{name:'Reserve camera',exact:true}).click();
      await expect(page.getByRole('status')).toHaveText('Reserved');
      await page.getByRole('button',{name:'Confirm reservation',exact:true}).click();
      await expect(page.getByRole('alert')).toHaveText('Confirm your acknowledgement before continuing.');
      await expect(page.getByRole('status')).toHaveText('Reserved');
      await page.getByRole('checkbox',{name:'I confirm this reservation',exact:true}).check();
      await page.getByRole('button',{name:'Confirm reservation',exact:true}).click();
      await expect(page.getByRole('status')).toHaveText('Confirmed');
      await expect(page.getByRole('button',{name:'Cancel reservation',exact:true})).toBeDisabled();
      const accessibility = await new AxeBuilder({page}).analyze();
      const serious = accessibility.violations.filter(v => ['serious','critical'].includes(v.impact));
      expect(serious,JSON.stringify(serious)).toEqual([]);
      await page.screenshot({path:join(dirname(args.output),name+'.png'),fullPage:true});
      report.checks.push({id:'browser-reserve-acknowledge-confirm',engine:name,status:'passed'},
                         {id:'accessible-validation',engine:name,status:'passed'});
      report.engines.push({name,version:browser.version()});
    } finally { await browser.close(); }
  }
  report.status='passed';
} finally { writeFileSync(args.output,JSON.stringify(report,null,2)+'\n'); }

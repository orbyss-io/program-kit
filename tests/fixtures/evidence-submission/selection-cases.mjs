import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const selected = await import(pathToFileURL(process.argv[2]));
const createFileSelection = options => selected.createFileSelection({maximumBytes:16384,maximumTitleLength:80,...options});
const cases = [];
const file = {name:'fictional.txt',size:1};
const date = '2026-10-18';
const bytes = new Uint8Array([120]).buffer;
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes,no) => { resolve=yes; reject=no; });
  return {promise,resolve,reject};
}
const tick = () => new Promise(resolve => setTimeout(resolve,0));
for (const reason of ['file','date','navigation','session']) {
  const first = deferred(), second = deferred();
  let calls=0, aborted=0;
  const selection = createFileSelection({read:()=>({promise:++calls === 1 ? first.promise : second.promise,abort(){aborted++;}}),digest:async()=> 'digest'});
  const stale = selection.select(file,date);
  selection.invalidate(reason);
  const current = selection.select(file,'2026-10-19');
  second.resolve(bytes); await current;
  first.reject(new Error('PRIVATE_STALE_FAILURE')); await stale;
  assert.equal(selection.current().kind,'ready'); assert.equal(selection.current().date,'2026-10-19');
  assert.equal(aborted,1); selection.dispose(); cases.push(reason+'-stale-read-failure-suppressed');
}
{
  const late=deferred(); let count=0;
  const selection=createFileSelection({read:()=>({promise:Promise.resolve(bytes),abort(){}}),digest:()=>++count===1?late.promise:Promise.resolve('new-digest')});
  const stale=selection.select(file,date); await tick();
  await selection.select(file,'2026-10-19'); late.resolve('old-digest'); await stale;
  assert.equal(selection.current().hash,'new-digest');
  const confirmed=selection.confirm('Exact confirmed title');
  selection.invalidate(); assert.equal(confirmed.title,'Exact confirmed title'); assert.equal(confirmed.date,'2026-10-19');
  assert.equal(confirmed.content,'eA=='); assert.equal(Object.isFrozen(confirmed),true);
  cases.push('late-crypto-success-suppressed-and-confirmation-immutable');
}
{
  const late=deferred(); let count=0;
  const selection=createFileSelection({read:()=>({promise:Promise.resolve(bytes),abort(){}}),digest:()=>++count===1?late.promise:Promise.resolve('current')});
  const stale=selection.select(file,date); await tick(); await selection.select(file,date);
  late.reject(new Error('PRIVATE_OLD_CRYPTO')); await stale;
  assert.equal(selection.current().hash,'current'); cases.push('late-crypto-failure-cannot-clear-current-selection');
}
{
  let aborted=0;
  const selection=createFileSelection({read:()=>({promise:new Promise(()=>{}),abort(){aborted++;}}),timeoutMilliseconds:5});
  await selection.select(file,date); assert.equal(selection.current().kind,'failed'); assert.equal(aborted,1);
  assert.throws(()=>selection.confirm('x')); cases.push('bounded-reader-deadline-and-current-failure');
}
{
  let count=0;
  const selection=createFileSelection({read:()=>({promise:++count===1?Promise.reject(new Error('PRIVATE_CURRENT')):Promise.resolve(bytes),abort(){}}),digest:async()=> 'ok'});
  await selection.select(file,date); assert.equal(selection.current().kind,'failed');
  assert.equal(JSON.stringify(selection.current()).includes('PRIVATE'),false);
  await selection.select(file,date); assert.equal(selection.current().kind,'ready');
  selection.dispose(); assert.throws(()=>selection.confirm('x')); cases.push('current-failure-allows-explicit-reselection-and-disposal');
}
for (const size of [0,16385]) {
  let reads=0;
  const selection=createFileSelection({read(){reads++; throw new Error('must not read');}});
  await selection.select({...file,size},date); assert.equal(reads,0); assert.equal(selection.current().kind,'failed');
  cases.push('size-'+size+'-rejects-before-reader-allocation');
}
console.log(JSON.stringify({cases,limits:['Controlled FileReader/crypto races plus separate real browser FileReader; crypto itself is not cancelled.','No server or arbitrary file format claim.']}));

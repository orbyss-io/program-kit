import assert from 'node:assert/strict';
import fs from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

// Execute the actual emitted adapter. Only TypeScript annotations/type imports
// are stripped; transport and admission functions are not replaced.
const source = fs.readFileSync(process.argv[2], 'utf8');
const javascript = stripTypeScriptTypes(source);
const { storeLabel } = await import(`data:text/javascript;base64,${Buffer.from(javascript).toString('base64')}`);
let effects = 0;
let expectedSignal;
let reply = { policy: 'configured-ready' };
const json = body => new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } });
globalThis.fetch = async (_path, options) => {
  effects++;
  assert.equal(options.signal, expectedSignal, 'the caller owns the complete deadline; no fresh stage budget');
  assert.equal(options.credentials, 'same-origin');
  assert.equal(options.cache, 'no-store');
  assert.equal(options.redirect, 'error');
  return json(reply);
};
const run = (value = { policy: 'edited' }, token = 'fictional', header = 'X-CSRF-TOKEN', signal = new AbortController().signal) => {
  expectedSignal = signal;
  return storeLabel(value, header, token, signal);
};

assert.deepEqual(await run(), { policy: 'configured-ready' });
reply = { policy: '', extraPermittedResponseField: true };
assert.deepEqual(await run(), { policy: '' }, 'empty string and tolerant additional fields remain valid');
for (const invalid of [null, [], {}, { policy: null }, { policy: 12 }, 'wrong']) {
  reply = invalid;
  const before = effects;
  await assert.rejects(run());
  assert.equal(effects, before + 1, 'one dispatch, no uncertain-write retry');
}
reply = { policy: 'ready' };
for (const token of [undefined, null, 12, true, {}, '']) {
  const before = effects;
  expectedSignal = new AbortController().signal;
  await assert.rejects(storeLabel({ policy: 'edited' }, 'X-CSRF-TOKEN', token, expectedSignal));
  assert.equal(effects, before, 'invalid token must reject before dispatch');
}
for (const request of [null, [], {}, { policy: null }, { policy: 42 }, { policy: 'valid', unexpected: 1 }]) {
  const before = effects;
  await assert.rejects(run(request));
  assert.equal(effects, before, 'strict request admission precedes effects');
}
let before = effects;
await assert.rejects(run({ policy: 'edited' }, 'fictional', 'Other-Header'));
assert.equal(effects, before);
const canceled = new AbortController(); canceled.abort();
await assert.rejects(run({ policy: 'edited' }, 'fictional', 'X-CSRF-TOKEN', canceled.signal));
assert.equal(effects, before, 'canceled admission performs no write');

// Byte ceilings come from the sample's actual 1024/2048 native JSON profiles.
const requestFraming = new TextEncoder().encode(JSON.stringify({ policy: '' })).byteLength;
await run({ policy: 'a'.repeat(1024 - requestFraming) });
before = effects;
await assert.rejects(run({ policy: 'a'.repeat(1025 - requestFraming) }));
assert.equal(effects, before);
const responseFraming = requestFraming;
reply = { policy: 'a'.repeat(2048 - responseFraming) };
assert.equal((await run()).policy.length, 2048 - responseFraming);
reply = { policy: 'a'.repeat(2049 - responseFraming) };
await assert.rejects(run());

let canceledBody = false;
const bodyStop = new AbortController();
let observedResponse;
globalThis.fetch = async (_path, options) => {
  effects++;
  assert.equal(options.signal, bodyStop.signal);
  const stream = new ReadableStream({
    pull(controller) { bodyStop.abort(); controller.enqueue(new TextEncoder().encode('{"policy":"late"}')); },
    cancel() { canceledBody = true; },
  });
  observedResponse = new Response(stream, { headers: { 'content-type': 'application/json' } });
  return observedResponse;
};
before = effects;
await assert.rejects(run({ policy: 'edited' }, 'fictional', 'X-CSRF-TOKEN', bodyStop.signal));
assert.equal(effects, before + 1);
assert.equal(canceledBody, true, 'owned body enumeration is canceled');
assert.equal(observedResponse.body.locked, false, 'owned reader lock is released');
console.log('EMITTED_CLIENT_VALID_TOLERANT_AND_BOUNDARY_ADMISSION_PASSED');

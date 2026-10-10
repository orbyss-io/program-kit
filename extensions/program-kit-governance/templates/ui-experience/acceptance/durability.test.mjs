// Sequencing guards for the real-server adapter; these are not runtime durability acceptance.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { verifyServerDraftDurability, runDurabilityContract, recordDurabilityCase } from './durability.mjs';

const expectedDraft = { id: 'synthetic-draft', version: 7, content: { text: 'private draft sentinel' } };
function fixture({ before = expectedDraft, after = expectedDraft, readiness = [true], status = 200 } = {}) {
  const calls = [], diagnostics = [];
  let restarted = false, poll = 0;
  return { calls, diagnostics, contract: {
    expectedDraft, draftPath: '/draft', authenticatedReadinessPath: '/ready', attempts: 3, intervalMs: 0,
    record: value => diagnostics.push(value),
    request: { async get(path) {
      calls.push(path);
      return { status: () => status, json: async () => path === '/ready'
        ? { authenticated: restarted ? readiness[Math.min(poll++, readiness.length - 1)] : true }
        : restarted ? after : before };
    } },
    async restart() { calls.push('restart'); restarted = true; },
    async authenticate() { calls.push('authenticate'); },
    async inspect() { calls.push('inspect'); }
  } };
}
test('exact server acknowledgement precedes restart and authenticated readiness precedes inspection', async () => {
  const f = fixture({ readiness: [false, true] });
  await verifyServerDraftDurability(f.contract);
  assert.deepEqual(f.calls, ['/ready', '/draft', 'restart', 'authenticate', '/ready', '/ready', '/draft', 'inspect']);
});
test('stale version, different identity or content never permits restart', async () => {
  for (const before of [{ ...expectedDraft, version: 6 }, { ...expectedDraft, id: 'wrong' },
                        { ...expectedDraft, content: { text: 'different' } }]) {
    const f = fixture({ before });
    await assert.rejects(verifyServerDraftDurability(f.contract), /PKB002 server draft acknowledgement timed out/);
    assert(!f.calls.includes('restart'));
    assert(!JSON.stringify(f.diagnostics).includes('private draft sentinel'));
  }
});
test('authenticated readiness timing failure is distinct from recovered data mismatch', async () => {
  const unready = fixture({ readiness: [false] });
  await assert.rejects(verifyServerDraftDurability(unready.contract), /PKB003 authenticated readiness timed out/);
  assert(!unready.calls.includes('inspect'));
  assert.equal(unready.calls.filter(p => p === '/draft').length, 1);
  const lost = fixture({ after: { ...expectedDraft, version: 6 } });
  await assert.rejects(verifyServerDraftDurability(lost.contract), /PKB004 recovered server draft differs/);
  assert(!lost.calls.includes('inspect'));
});
test('HTTP and thrown request diagnostics omit URLs, credentials, bodies and source text', async () => {
  const f = fixture({ status: 503 });
  await assert.rejects(verifyServerDraftDurability(f.contract), /PKB003/);
  assert.deepEqual(f.diagnostics[0], { stage: 'before-restart-readiness', attempt: 1, status: 503, outcome: 'http' });
  f.contract.request.get = async () => { throw new Error('source.cs password=private draft sentinel'); };
  let message;
  try { await verifyServerDraftDurability(f.contract); } catch (error) { message = error.message; }
  assert(!message.includes('password'));
  assert(!JSON.stringify(f.diagnostics).includes('source.cs'));
});
test('missing actual restart/authentication/draft/inspection contracts fail closed', async () => {
  for (const missing of ['request', 'restart', 'authenticate', 'inspect', 'expectedDraft', 'draftPath', 'authenticatedReadinessPath']) {
    const f = fixture(); delete f.contract[missing];
    await assert.rejects(verifyServerDraftDurability(f.contract), /PKB001/);
    assert.equal(f.calls.length, 0);
  }
});
test('selected publisher authenticated shape works and redirect/anonymous responses cannot pass', async () => {
  const f = fixture();
  const original = f.contract.request.get;
  let disposed = 0;
  f.contract.request.get = async path => {
    const result = await original(path);
    const json = result.json;
    return { ...result, json: async () => path === '/ready' ? { isAuthenticated: true } : json(),
      dispose: async () => { disposed++; } };
  };
  f.contract.isAuthenticatedResponse = value => value?.isAuthenticated === true;
  await verifyServerDraftDurability(f.contract);
  assert.equal(disposed, 4);
  const redirect = fixture({ status: 302 });
  await assert.rejects(verifyServerDraftDurability(redirect.contract), /PKB003/);
  assert(!redirect.calls.includes('restart'));
});
test('fixture cleanup runs after failure and preserves primary checkpoint diagnostic', async () => {
  const f = fixture({ before: { ...expectedDraft, version: 6 } });
  let closed = false;
  f.contract.close = async () => { closed = true; throw new Error('private source cleanup stack'); };
  await assert.rejects(runDurabilityContract(async () => f.contract, {}), error =>
    /PKB002 server draft acknowledgement/.test(error.message) && /PKB005.*cleanup/.test(error.message)
    && !error.message.includes('private source'));
  assert(closed);
});
test('restart cannot mutate the expected acknowledgement to conceal data loss', async () => {
  const expected = { id: 'draft', version: 7, content: { text: 'saved' } };
  const f = fixture({ before: expected, after: { ...expected, version: 6 } });
  f.contract.expectedDraft = expected;
  const restart = f.contract.restart;
  f.contract.restart = async () => { await restart(); expected.version = 6; };
  await assert.rejects(verifyServerDraftDurability(f.contract), /PKB004/);
});
test('failed checkpoints retain source-free HTTP/status evidence without an optional recorder', async () => {
  for (const [label, configure, code, outcome] of [
    ['unavailable', f => { f.contract.request.get = async () => { throw new Error('source.cs token=private'); }; }, 'PKB003', 'unavailable'],
    ['server503', f => { f.contract.request.get = async () => ({ status: () => 503 }); }, 'PKB003', 'http'],
    ['redirect', f => { f.contract.request.get = async () => ({ status: () => 302 }); }, 'PKB003', 'http'],
    ['data-loss', () => {}, 'PKB004', 'mismatch']
  ]) {
    const f = fixture({ after: { ...expectedDraft, version: 6 } });
    delete f.contract.record; configure(f);
    const results = [];
    f.contract.close = async () => {};
    await assert.rejects(recordDurabilityCase(async () => f.contract, { engine: 'chromium' }, results), error => {
      assert.equal(error.code, code, label);
      assert.equal(error.diagnostics.at(-1).outcome, outcome, label);
      return true;
    });
    const report = JSON.parse(JSON.stringify({ results }));
    assert.equal(report.results[0].status, 'failed', label);
    assert.equal(report.results[0].code, code, label);
    assert.equal(report.results[0].diagnostics.at(-1).outcome, outcome, label);
    assert(!JSON.stringify(report).includes('private'));
    assert(!JSON.stringify(report).includes('source.cs'));
  }
});
test('optional recorder failure/mutation and cleanup failure retain checkpoint evidence', async () => {
  const f = fixture({ status: 503 });
  f.contract.record = value => { value.status = 'secret'; throw new Error('private source'); };
  f.contract.close = async () => { throw new Error('private cleanup'); };
  const results = [];
  await assert.rejects(recordDurabilityCase(async () => f.contract, { engine: 'webkit' }, results), error => {
    assert.equal(error.code, 'PKB003');
    assert.equal(error.cleanupFailed, true);
    assert(error.diagnostics.every(d => d.status === 503));
    return true;
  });
  assert.equal(results[0].cleanupFailed, true);
  assert.equal(results[0].diagnosticRecorderFailed, true);
  assert.equal(results[0].diagnostics.length, 3);
  assert(!JSON.stringify(results).includes('private'));
  assert(!JSON.stringify(results).includes('secret'));
});

// The consumer supplies the real server request context and fixture-owned restart.
// No HTTP body, URL, account, draft or exception/source text enters diagnostics.
class DurabilityFailure extends Error {
  constructor(code, message, diagnostics = [], diagnosticRecorderFailed = false) {
    super(`${code} ${message}`);
    this.code = code;
    this.diagnostics = diagnostics.map(item => ({ ...item }));
    this.diagnosticRecorderFailed = diagnosticRecorderFailed;
  }
}
function fail(code, message, diagnostics, diagnosticRecorderFailed) {
  throw new DurabilityFailure(code, message, diagnostics, diagnosticRecorderFailed);
}
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  return value;
}
function sameDraft(actual, expected) {
  return actual && Object.hasOwn(actual, 'content') && actual.id === expected.id && actual.version === expected.version
    && JSON.stringify(canonical(actual.content)) === JSON.stringify(canonical(expected.content));
}
export async function verifyServerDraftDurability(contract) {
  const { request, expectedDraft, draftPath, authenticatedReadinessPath, restart, authenticate, inspect,
    record = () => {}, attempts = 30, intervalMs = 200, requestTimeoutMs = 2000,
    draftFromResponse = value => value, isAuthenticatedResponse = value => value?.authenticated === true } = contract ?? {};
  if (!request || typeof request.get !== 'function' || !expectedDraft || typeof expectedDraft.id !== 'string'
      || !expectedDraft.id || !(Number.isInteger(expectedDraft.version) || typeof expectedDraft.version === 'string' && expectedDraft.version)
      || !Object.hasOwn(expectedDraft, 'content') || expectedDraft.content === undefined
      || typeof draftPath !== 'string' || !draftPath || typeof authenticatedReadinessPath !== 'string' || !authenticatedReadinessPath
      || [restart, authenticate, inspect, record, draftFromResponse, isAuthenticatedResponse].some(f => typeof f !== 'function')
      || !Number.isInteger(attempts) || attempts < 1 || attempts > 120
      || !Number.isInteger(intervalMs) || intervalMs < 0 || intervalMs > 1000
      || !Number.isInteger(requestTimeoutMs) || requestTimeoutMs < 1 || requestTimeoutMs > 5000)
    fail('PKB001', 'real server durability contract is incomplete');
  let expected;
  try { expected = JSON.parse(JSON.stringify(expectedDraft)); }
  catch { fail('PKB001', 'expected draft must be JSON-compatible'); }
  const diagnostics = [];
  let diagnosticRecorderFailed = false;
  const checkpointFail = (code, message) => fail(code, message, diagnostics, diagnosticRecorderFailed);
  const observe = (stage, attempt, status, outcome) => {
    const item = { stage, attempt, status, outcome };
    diagnostics.push(item);
    // Optional telemetry must neither mutate retained status nor hide the checkpoint outcome.
    try { record({ ...item }); } catch { diagnosticRecorderFailed = true; }
  };
  async function response(path, stage, attempt) {
    let status = null, result;
    try {
      result = await request.get(path, { timeout: requestTimeoutMs, maxRedirects: 0 });
      status = result.status();
      if (!Number.isInteger(status) || status < 100 || status > 599) status = null;
      if (status !== 200) { observe(stage, attempt, status, 'http'); return null; }
      const body = await result.json();
      return { body, status };
    } catch { observe(stage, attempt, status, 'unavailable'); return null; }
    finally {
      try { if (typeof result?.dispose === 'function') await result.dispose(); }
      catch { checkpointFail('PKB005', 'HTTP response cleanup failed'); }
    }
  }
  async function poll(path, stage, matches, code, message) {
    for (let attempt = 1; attempt <= attempts; attempt++) {
      const result = await response(path, stage, attempt);
      if (result) {
        let matched = false;
        try { matched = matches(result.body) === true; } catch { /* omit payload/adapter diagnostics */ }
        observe(stage, attempt, result.status, matched ? 'matched' : 'mismatch');
        if (matched) return;
      }
      if (attempt < attempts) await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    checkpointFail(code, message);
  }
  await poll(authenticatedReadinessPath, 'before-restart-readiness', isAuthenticatedResponse,
    'PKB003', 'authenticated readiness timed out before restart');
  await poll(draftPath, 'server-draft-acknowledgement', value => !!sameDraft(draftFromResponse(value), expected),
    'PKB002', 'server draft acknowledgement timed out; restart was not performed');
  try { await restart(); } catch { checkpointFail('PKB005', 'fixture-owned restart failed'); }
  try { await authenticate(); } catch { checkpointFail('PKB005', 'fixture-owned authentication failed after restart'); }
  await poll(authenticatedReadinessPath, 'after-restart-readiness', isAuthenticatedResponse,
    'PKB003', 'authenticated readiness timed out after restart; data recovery was not inspected');
  const recovered = await response(draftPath, 'recovered-server-draft', 1);
  if (!recovered) checkpointFail('PKB006', 'recovered server draft HTTP request failed after authenticated readiness');
  let matches = false;
  try { matches = !!sameDraft(draftFromResponse(recovered.body), expected); } catch { /* source-free */ }
  observe('recovered-server-draft', 1, recovered.status, matches ? 'matched' : 'mismatch');
  if (!matches) checkpointFail('PKB004', 'recovered server draft differs after authenticated readiness');
  try { await inspect(); } catch { checkpointFail('PKB005', 'consumer inspection failed after recovery checkpoints'); }
  return { status: 'passed', diagnostics, diagnosticRecorderFailed };
}

export async function runDurabilityContract(createContract, inputs) {
  let contract;
  try { contract = await createContract(inputs); }
  catch { fail('PKB001', 'real server durability contract preparation failed'); }
  if (typeof contract?.close !== 'function') fail('PKB001', 'durability contract must clean up its owned server fixture');
  let primaryFailure;
  try { return await verifyServerDraftDurability(contract); }
  catch (error) {
    primaryFailure = error instanceof DurabilityFailure ? error : new DurabilityFailure('PKB005', 'durability checkpoint failed');
    throw primaryFailure;
  }
  finally {
    try { await contract.close(); }
    catch {
      const cleanup = 'PKB005 real server durability fixture cleanup failed';
      const error = primaryFailure ?? new DurabilityFailure('PKB005', 'real server durability fixture cleanup failed');
      if (primaryFailure) error.message += `; ${cleanup}`;
      error.cleanupFailed = true;
      throw error;
    }
  }
}

// The maintained browser entrypoint uses this for both success and failed-report evidence.
export async function recordDurabilityCase(createContract, inputs, results) {
  const engine = inputs.engine;
  try {
    const outcome = await runDurabilityContract(createContract, inputs);
    results.push({ engine, case: 'durability', ...outcome });
    return outcome;
  } catch (error) {
    const failure = error instanceof DurabilityFailure ? error : new DurabilityFailure('PKB005', 'durability checkpoint failed');
    results.push({ engine, case: 'durability', status: 'failed', code: failure.code,
      diagnostics: failure.diagnostics, diagnosticRecorderFailed: failure.diagnosticRecorderFailed,
      cleanupFailed: failure.cleanupFailed === true });
    throw failure;
  }
}

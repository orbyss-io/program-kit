"""Maintained semantic transition example; actual consumer/server/browser acceptance remains owned."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
example = ROOT / 'extensions/program-kit-governance/references/operation-recovery-example.mjs'
script = r'''
import assert from 'node:assert/strict';
const {recovery} = await import(process.argv[1]);
const initial = {values: {insurer: 'Retained name', holder: 'Retained holder'}, operationId: null, editable: true, reconcile: false};
for (const kind of ['validation-rejected-without-effect', 'admission-expired-before-acceptance']) {
  const prepared = recovery(initial, {kind: 'prepared', operationId: 'server-original'});
  assert.equal(recovery(prepared, {kind, operationId: 'older', field: 'insurer'}), prepared);
  const corrected = recovery(prepared, {kind, operationId: 'server-original', field: 'insurer'});
  assert.deepEqual(corrected.values, initial.values);
  assert.equal(corrected.editable, true); assert.equal(corrected.operationId, null);
  assert.equal(corrected.reconcile, false); assert.equal(corrected.focus, 'insurer');
  // Correction grants explicit later preparation; it does not prepare itself.
  assert.equal(recovery(corrected, {kind: 'prepared', operationId: 'server-next'}).operationId, 'server-next');
}
for (const kind of ['response-lost', 'completion-unknown', 'receipt-unknown']) {
  const prepared = recovery(initial, {kind: 'prepared', operationId: 'server-original'});
  const unknown = recovery(prepared, {kind, operationId: 'server-original'});
  assert.deepEqual(unknown.values, initial.values); assert.equal(unknown.editable, false);
  assert.equal(unknown.reconcile, true); assert.equal(unknown.operationId, 'server-original');
  assert.throws(() => recovery(unknown, {kind: 'prepared', operationId: 'server-new'}));
  assert.equal(recovery(unknown, {kind: 'http-error', status: 400}).operationId, 'server-original');
  assert.equal(recovery(unknown, {kind: 'http-error', status: 409}).operationId, 'server-original');
  assert.equal(recovery(unknown, {kind: 'http-error', status: 404}).operationId, 'server-original');
  assert.equal(recovery(unknown, {kind: 'accepted-status', operationId: 'different-owner'}), unknown);
  assert.equal(recovery(unknown, {kind: 'accepted-status', operationId: 'server-original'}).outcome, 'accepted');
}
console.log('12 semantic recovery cases passed; no actual server/browser acceptance claimed.');
'''
result = subprocess.run([shutil.which('node'), '--input-type=module', '-e', script, example.as_uri()], cwd=ROOT, capture_output=True, text=True, timeout=30)
if result.returncode: raise AssertionError(result.stdout + result.stderr)
print(result.stdout.strip())

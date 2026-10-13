import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { normalizeLabel } from './generated/labels.js';
import { normalizeLabel as normalizeOwned } from './generated/owned-constructor.js';
import { normalizeLabel as normalizeIdentity, labelValidationMetadata, validationDescriptorSha256 } from './generated/identity.js';

const undeclared = ['constructor', 'toString', '__proto__', 'unknown', 'displayLabel\n', null, 0];
for (const key of undeclared) {
  assert.throws(() => normalizeLabel(key, 'safe'), error => error instanceof Error && error.message === 'PKV003 label validation rule is not declared');
}
assert.deepEqual(normalizeOwned('constructor', ' safe '), { valid: true, value: 'safe' });
assert.equal(normalizeOwned('constructor', 'x'.repeat(121)).valid, false);
assert.equal(normalizeOwned('constructor', '\tsafe').valid, false);
assert.throws(() => normalizeOwned('toString', 'safe'), /PKV003 label validation rule is not declared/);

const descriptorBytes = await readFile('identity-descriptor.json');
const descriptor = JSON.parse(descriptorBytes);
assert.deepEqual(labelValidationMetadata, descriptor);
assert.equal(validationDescriptorSha256, createHash('sha256').update(descriptorBytes).digest('hex'));
assert.equal(labelValidationMetadata.owner, 'TRIM_UNITS');
assert.equal(labelValidationMetadata.contractId, 'DIGEST.METADATA.TRIM_UNITS');
assert.equal(labelValidationMetadata.rules.TRIM_UNITS.ruleId, 'METADATA.TRIM_UNITS.DIGEST');
for (const raw of [' safe ', '\ufeffsafe', '\xa0safe\xa0', '😀'.repeat(60), 'x'.repeat(121), '\tsafe']) {
  assert.deepEqual(normalizeIdentity('TRIM_UNITS', raw), normalizeLabel('displayLabel', raw));
}
console.log(JSON.stringify({ undeclaredRuntimeKeysRejected: undeclared.length, boundedConfigurationError: true,
  explicitlyOwnedConstructorAdmitted: true, descriptorIdentitiesPreserved: true, descriptorDigestMatches: true }));

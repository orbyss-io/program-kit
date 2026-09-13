"""API ownership gates reject missing, stale and mismatched contract evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from api_proof import validate, affected_operations
from lifecycle_state import lifecycle_sha256


class ApiTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='api-proof-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.feature = self.root / 'specs/001-reserve'; self.feature.mkdir(parents=True)
        (self.feature / 'plan.md').write_text('Compose stable operations; retain V1 request/response identity.')
        self.write('.program-kit/openapi-contracts.json', {'schemaVersion': 1, 'contracts': ['contracts/reservations.json']})
        self.write('contracts/reservations.json', {'identity': 'Reservations', 'baseline': 'contracts/baseline.json', 'artifact': 'artifacts/openapi.json'})
        self.write('contracts/baseline.json', {'openapi': '3.0.3', 'paths': {}})
        self.write('artifacts/openapi.json', {'openapi': '3.0.3', 'paths': {'/reservations': {'post': {'operationId': 'Reserve'}}}})
        self.write('specs/001-reserve/artifact-ownership.json', {'apiOperations': ['Reserve']})
        for path in ('src/Reservations.Api/Feature.cs', 'src/Reservations.Api/Operations/Reserve/Endpoint.cs', 'tests/Reservations/Reserve.cs'):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('// source-shape gate fixture')
        self.proof = {'schemaVersion': 1, 'contracts': [{'identity': 'Reservations', 'producerCheckIds': ['dto-parity'],
                      'compatibilityCheckIds': ['v1-client'], 'versionDecision': 'specs/001-reserve/plan.md',
                      'baselineSha256': lifecycle_sha256(self.root / 'contracts/baseline.json'), 'newContract': False}],
                      'operations': [{'id': 'Reserve', 'owner': 'Reservations', 'contract': 'Reservations', 'method': 'POST',
                                      'route': '/reservations', 'designRef': 'specs/001-reserve/plan.md', 'checkIds': ['reserve'],
                                      'layout': 'operation-folder', 'composition': 'src/Reservations.Api/Feature.cs',
                                      'sources': {'endpoint': 'src/Reservations.Api/Operations/Reserve/Endpoint.cs',
                                                  'tests': 'tests/Reservations/Reserve.cs'}}]}
        self.checks = {'dto-parity', 'v1-client', 'reserve'}
        self.proof['contracts'][0]['artifactSha256'] = lifecycle_sha256(self.root / 'artifacts/openapi.json')

    def write(self, name, value):
        path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))

    def check(self, phase='delivery'):
        self.write('specs/001-reserve/api-proof.json', self.proof)
        return validate(self.root, self.feature, phase, self.checks)

    def test_operation_layout_and_existing_baseline_pass(self):
        self.check()

    def test_missing_named_behavior_fails(self):
        self.checks.remove('v1-client')
        with self.assertRaisesRegex(ValueError, 'old-client'):
            self.check()

    def test_changed_baseline_cannot_silently_rebaseline(self):
        self.write('contracts/baseline.json', {'changed': True})
        with self.assertRaisesRegex(ValueError, 'baseline changed'):
            self.check()

    def test_missing_old_baseline_is_not_a_new_contract(self):
        (self.root / 'contracts/baseline.json').unlink()
        with self.assertRaisesRegex(ValueError, 'baseline is missing'):
            self.check('after-plan')
        self.proof['contracts'][0].update(newContract=True, baselineSha256=None)
        self.check('after-plan')
        with self.assertRaisesRegex(ValueError, 'baseline is missing'):
            self.check()

    def test_composition_cannot_be_claimed_as_operation_folder(self):
        self.proof['operations'][0]['sources']['endpoint'] = 'src/Reservations.Api/Feature.cs'
        with self.assertRaisesRegex(ValueError, 'Composition must delegate'):
            self.check()
        self.proof['operations'][0].update(layout='small-operation', layoutRationale='Bodyless permission probe delegates all behavior to managed policy.')
        self.check()

    def test_exported_identity_and_source_presence_are_enforced(self):
        self.write('artifacts/openapi.json', {'paths': {'/reservations': {'post': {'operationId': 'Changed'}}}})
        self.proof['contracts'][0]['artifactSha256'] = lifecycle_sha256(self.root / 'artifacts/openapi.json')
        with self.assertRaisesRegex(ValueError, 'identity/route'):
            self.check()

    def test_multiple_operations_cannot_share_route_and_verb(self):
        second = copy.deepcopy(self.proof['operations'][0]); second['id'] = 'Cancel'
        self.proof['operations'].append(second)
        self.write('specs/001-reserve/artifact-ownership.json', {'apiOperations': ['Reserve', 'Cancel']})
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.check('after-plan')

    def test_multiple_operation_folders_preserve_independent_wire_identities(self):
        second = copy.deepcopy(self.proof['operations'][0])
        second.update(id='Cancel', method='DELETE', route='/reservations/{id}')
        second['sources'] = {'endpoint': 'src/Reservations.Api/Operations/Cancel/Endpoint.cs',
                             'tests': 'tests/Reservations/Cancel.cs'}
        for relative in second['sources'].values():
            path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('// scoped source')
        self.proof['operations'].append(second)
        self.write('specs/001-reserve/artifact-ownership.json', {'apiOperations': ['Reserve', 'Cancel']})
        self.write('artifacts/openapi.json', {'paths': {'/reservations': {'post': {'operationId': 'Reserve'}},
                                                     '/reservations/{id}': {'delete': {'operationId': 'Cancel'}}}})
        self.proof['contracts'][0]['artifactSha256'] = lifecycle_sha256(self.root / 'artifacts/openapi.json')
        self.check()

    def test_retirement_requires_removed_route_and_preserved_compatibility_tests(self):
        old = {'paths': {'/reservations': {'post': {'operationId': 'Reserve'}}}}
        self.write('contracts/baseline.json', old)
        self.proof['contracts'][0]['baselineSha256'] = lifecycle_sha256(self.root / 'contracts/baseline.json')
        self.proof['operations'][0]['retired'] = True
        (self.root / self.proof['operations'][0]['sources']['endpoint']).unlink()
        with self.assertRaisesRegex(ValueError, 'remains published'):
            self.check()
        self.write('artifacts/openapi.json', {'paths': {}})
        self.proof['contracts'][0]['artifactSha256'] = lifecycle_sha256(self.root / 'artifacts/openapi.json')
        self.check()
        (self.root / self.proof['operations'][0]['sources']['tests']).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing API tests'):
            self.check()

    def test_changed_generated_document_requires_new_bound_evidence(self):
        self.write('artifacts/openapi.json', {'paths': {}})
        with self.assertRaisesRegex(ValueError, 'document changed'):
            self.check()

    def test_removing_operation_evidence_cannot_remove_obligation(self):
        self.proof['operations'] = []
        with self.assertRaises(ValueError):
            self.check()

    def test_nested_schema_change_reaches_affected_operation(self):
        old = {'paths': {'/reservations': {'get': {'operationId': 'Read', 'responses': {'200': {'$ref': '#/components/schemas/Page'}}}}},
               'components': {'schemas': {'Page': {'items': {'$ref': '#/components/schemas/Reservation'}}, 'Reservation': {'type': 'string'}}}}
        current = copy.deepcopy(old); current['components']['schemas']['Reservation']['type'] = 'integer'
        self.assertEqual({('get', '/reservations')}, affected_operations(old, current))

    def test_unmapped_generated_operation_is_rejected(self):
        self.write('artifacts/openapi.json', {'paths': {'/reservations': {'post': {'operationId': 'Reserve'}, 'delete': {'operationId': 'Unplanned'}}}})
        self.proof['contracts'][0]['artifactSha256'] = lifecycle_sha256(self.root / 'artifacts/openapi.json')
        with self.assertRaisesRegex(ValueError, 'lack scoped ownership'):
            self.check()


if __name__ == '__main__':
    unittest.main()

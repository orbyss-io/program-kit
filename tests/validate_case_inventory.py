"""No count, renamed case, skip, stale source or empty execution can replace obligations."""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'), str(ROOT / 'tests')]
import case_inventory as cases
from owned_fixture import FixtureDirectory


class CaseInventoryTests(unittest.TestCase):
    def test_original_obligation_lineage_preserves_exact_reviewed_identities_owners_and_required_targets(self):
        path = ROOT / 'docs/reviews/maintenance-regression-lineage-2026-10-16.json'
        value = json.loads(path.read_bytes())
        self.assertEqual('b27a73f7cef1bbdd47f7a6f5831bbc6da8c4ad4967fa4bbc95cddffa86d57620', value['originalPacketManifestSha256'])
        projection = [{'module': module['originalModule'], 'source': module['originalSourceSha256'],
            'packet': module['sanitizedSha256'], 'case': row['originalCase'], 'ast': row['originalCaseAstSha256'],
            'owner': row['disposition'], 'targets': row['requiredCurrentCases'], 'retired': row['consumerObligationRetired']}
            for module in value['modules'] for row in module['cases']]
        self.assertEqual('c2dfa7e52b820fb4f0f5b9c5bebd454dbfeb0eb278dfac89603ef5c15ef8e7b7',
            cases.digest(json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()))
        current = ROOT / 'tests/shared-regression-cases.json'; contract = json.loads(current.read_bytes())
        self.assertEqual(cases.digest(current.read_bytes()), value['currentContractSha256'])
        required = {case for module in contract['modules'] for case in module['cases']}
        for row in projection:
            self.assertIs(row['retired'], False)
            if row['owner'] == 'current-shared-case-mapping':
                self.assertTrue(row['targets']); self.assertTrue(set(row['targets']) <= required)
            else:
                self.assertEqual('consumer-owned-preserved', row['owner'])
        # This protects the reviewed translation. It does not certify that the
        # actual consumer-specific assertions ran or that semantic coverage is complete.

    def setUp(self):
        self.temp = FixtureDirectory(prefix='case-contract-'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.module = 'synthetic_required_cases'
        self.source = self.root / (self.module + '.py'); self.manifest = self.root / 'original-cases.json'

    def declare(self, text, methods=('test_original',), platforms=None):
        self.source.write_text('import unittest\n' + text, encoding='utf-8')
        value = {'schemaVersion': 1, 'inputs': [], 'modules': [{'module': self.module, 'path': self.source.name,
            'sha256': cases.digest(self.source.read_bytes()), 'cases': {self.module + '.Required.' + name:
                platforms or ['Windows', 'Linux'] for name in methods}}]}
        self.manifest.write_text(json.dumps(value), encoding='utf-8'); self.anchor = cases.digest(self.manifest.read_bytes())
        return value

    def run_contract(self, selected=None):
        return cases.execute(self.root, self.manifest.name, self.anchor, selected)

    def test_actual_case_and_fresh_process_bind_original_sources_and_leave_contract_unchanged(self):
        self.declare('class Required(unittest.TestCase):\n def test_original(self): self.assertEqual(7, 7)\n')
        before = self.manifest.read_bytes(); source = self.source.read_bytes()
        result = self.run_contract(); self.assertEqual('passed', result['status'])
        self.assertEqual({self.module + '.Required.test_original': 'passed'}, result['executedCases'])
        native = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/case_inventory.py'),
            '--project-root', str(self.root), '--contract', self.manifest.name, '--contract-sha256', self.anchor],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(0, native.returncode, native.stdout + native.stderr)
        self.assertEqual(before, self.manifest.read_bytes()); self.assertEqual(source, self.source.read_bytes())
        self.assertFalse(result['productAcceptanceEstablished']); self.assertFalse(result['publisherAuthenticityEstablished'])

    def test_126_unrelated_passes_cannot_replace_one_required_identity(self):
        text = 'class Required(unittest.TestCase):\n' + ''.join(' def test_unrelated_' + str(n) + '(self): pass\n' for n in range(126))
        self.declare(text)
        with self.assertRaisesRegex(ValueError, 'counts cannot substitute identities'): self.run_contract()
        record = json.loads(next((self.root / 'artifacts/tests/toolkit-cases').glob('*/results.json')).read_text())
        self.assertEqual({}, record['executedCases']); self.assertEqual('failed', record['status'])

    def test_skipped_failed_error_expected_failure_and_empty_cases_cannot_pass(self):
        bodies = [" @unittest.skip('omitted')\n def test_original(self): pass\n",
                  ' def test_original(self): self.fail("required failure")\n',
                  ' def test_original(self): raise RuntimeError("required error")\n',
                  ' @unittest.expectedFailure\n def test_original(self): self.fail("required failure")\n']
        for body in bodies:
            self.declare('class Required(unittest.TestCase):\n' + body)
            with self.assertRaisesRegex(ValueError, 'execution was missing'): self.run_contract()
        self.declare('class Required(unittest.TestCase): pass\n')
        with self.assertRaisesRegex(ValueError, 'case/module set changed'): self.run_contract()

    def test_same_case_name_wrong_body_or_rehashed_contract_cannot_borrow_original_review(self):
        value = self.declare('class Required(unittest.TestCase):\n def test_original(self): pass\n')
        self.source.write_text('import unittest\nclass Required(unittest.TestCase):\n def test_original(self): self.fail("substituted body")\n')
        with self.assertRaisesRegex(ValueError, 'source differs'): self.run_contract()
        value['modules'][0]['sha256'] = cases.digest(self.source.read_bytes())
        self.manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'review anchor'): self.run_contract()

    def test_duplicate_leaf_and_load_tests_removal_are_rejected_before_execution(self):
        base = 'class Required(unittest.TestCase):\n def test_original(self): raise AssertionError("must not execute")\n'
        for loader in ('return unittest.TestSuite()', 'return unittest.TestSuite([Required("test_original"), Required("test_original")])'):
            self.declare(base + 'def load_tests(loader, tests, pattern):\n ' + loader + '\n')
            with self.assertRaisesRegex(ValueError, 'case/module set changed'): self.run_contract()

    def test_explicit_other_platform_is_not_executed_and_no_required_case_means_no_success(self):
        other = 'Linux' if platform.system() == 'Windows' else 'Windows'
        self.declare('class Required(unittest.TestCase):\n def test_original(self): self.fail("wrong platform")\n', platforms=[other])
        with self.assertRaisesRegex(ValueError, 'no required current-platform cases'): self.run_contract()

    def test_unknown_module_missing_source_and_unreadable_inventory_fail_without_fallback(self):
        self.declare('class Required(unittest.TestCase):\n def test_original(self): pass\n')
        with self.assertRaisesRegex(ValueError, 'unknown/empty'): self.run_contract(['unknown_replacement'])
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, 'source missing'): self.run_contract()
        self.manifest.unlink()
        with self.assertRaisesRegex(ValueError, 'inventory is missing'): self.run_contract()

    def test_source_changed_during_case_is_retained_as_failed_execution(self):
        self.declare('from pathlib import Path\nclass Required(unittest.TestCase):\n def test_original(self): Path(__file__).write_text("changed during execution")\n')
        with self.assertRaisesRegex(ValueError, 'changed during execution'): self.run_contract()
        record = json.loads(next((self.root / 'artifacts/tests/toolkit-cases').glob('*/results.json')).read_text())
        self.assertEqual({self.module + '.Required.test_original': 'passed'}, record['executedCases'])
        self.assertEqual('failed', record['status'])

    def test_declared_mechanism_inputs_are_required_and_cannot_change_during_execution(self):
        value = self.declare('from pathlib import Path\nclass Required(unittest.TestCase):\n def test_original(self): Path("mechanism.py").write_text("modified")\n')
        value['inputs'] = ['mechanism.py']
        self.manifest.write_text(json.dumps(value)); self.anchor = cases.digest(self.manifest.read_bytes())
        with self.assertRaisesRegex(ValueError, 'input is missing'): self.run_contract()
        (self.root / 'mechanism.py').write_bytes(b'original production input')
        with self.assertRaisesRegex(ValueError, 'mechanism/source input changed'): self.run_contract()
        records = [json.loads(path.read_text()) for path in (self.root / 'artifacts/tests/toolkit-cases').glob('*/results.json')]
        executed = next(row for row in records if row['executedCases'])
        self.assertEqual(cases.digest(b'original production input'), executed['inputSha256']['mechanism.py'])
        self.assertEqual('failed', executed['status'])


if __name__ == '__main__': unittest.main()

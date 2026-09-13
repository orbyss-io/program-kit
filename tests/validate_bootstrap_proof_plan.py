"""Native shell proof-stage regressions; real Python probes, no coding agent."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from bootstrap_proof_plan import execute, PLAN, require_proven_closure
from bootstrap_lifecycle import LEDGER, load, write, source_digest
from validate_governance_state import roadmap


class ProofPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-proof-plan-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        docs = self.root / 'docs/architecture'
        docs.mkdir(parents=True)
        write(docs / 'bootstrap-decisions.json', {})
        write(docs / 'architecture-map.json', {'decisions': []})
        (docs / 'specification-roadmap.md').write_text(roadmap(status='Blocked'), encoding='utf-8')
        write(self.root / LEDGER, {'schema_version': '1.0', 'sources': [{
            'path': 'docs/architecture/bootstrap-decisions.json', 'sha256': source_digest(docs / 'bootstrap-decisions.json'),
            'prerequisites': ['runtime']}], 'prerequisites': [{
            'id': 'runtime', 'source_ids': ['runtime'], 'affected_slices': ['SPEC-001'],
            'disposition': 'architecture', 'trigger': 'before-implementation', 'owner': 'Fixture owner',
            'task': 'Verify Python persistence protocol', 'rationale': 'A durable write must survive reopening',
            'status': 'open', 'evidence': []}]})
        self.recipe = docs / 'probe.py'
        self.recipe.write_text("import sqlite3\nfrom pathlib import Path\nc=sqlite3.connect('probe.db')\nc.execute('create table evidence (value integer)')\nc.execute('insert into evidence values (7)')\nc.commit()\nc.close()\nc=sqlite3.connect('probe.db')\nassert c.execute('select value from evidence').fetchone() == (7,)\nc.close()\nPath('compatibility-results.xml').write_text('<testsuite><testcase classname=\"Probe\" name=\"persist\"/></testsuite>')\n", encoding='utf-8')
        write(self.recipe.with_suffix('.contract.json'), {'schemaVersion': 1, 'checks': [
            {'id': 'persist', 'kind': 'runtime-compatibility', 'testCases': ['Probe.persist']}]})
        self.plan = {'schemaVersion': 1, 'probes': [{'id': 'runtime', 'recipe': 'docs/architecture/probe.py', 'timeout': 10}],
                     'readyWhenProven': [{'id': 'SPEC-001', 'prerequisites': ['runtime'], 'rationale': 'Only remaining architecture condition'}]}
        write(self.root / PLAN, self.plan)

    def test_actual_proof_closes_only_scoped_condition_and_resume_reuses(self):
        self.assertEqual(1, len(execute(self.root)))
        self.assertEqual(['runtime'], require_proven_closure(self.root))
        self.assertEqual('closed', load(self.root / LEDGER)['prerequisites'][0]['status'])
        self.assertIn('**Status**: Ready', (self.root / 'docs/architecture/specification-roadmap.md').read_text(encoding='utf-8'))
        self.assertEqual([], execute(self.root))
        self.assertEqual(1, len(list(self.root.rglob('proof.json'))))

    def test_reuse_rejects_unproven_and_different_planned_recipe(self):
        with self.assertRaisesRegex(ValueError, 'must pass'):
            require_proven_closure(self.root)
        execute(self.root)
        other = self.recipe.with_name('other.py')
        other.write_bytes(self.recipe.read_bytes())
        other.with_suffix('.contract.json').write_bytes(self.recipe.with_suffix('.contract.json').read_bytes())
        self.plan['probes'][0]['recipe'] = 'docs/architecture/other.py'
        write(self.root / PLAN, self.plan)
        with self.assertRaisesRegex(ValueError, 'matching passing proof'):
            require_proven_closure(self.root)

    def test_windows_long_nuget_paths_are_removed_without_losing_sibling_evidence(self):
        import os
        from bootstrap_lifecycle import compatibility_scratch
        attempt = self.root / 'attempt'
        attempt.mkdir()
        preserved = attempt / 'stderr.txt'
        preserved.write_text('preserved failure', encoding='utf-8')
        with compatibility_scratch(attempt) as directory:
            scratch = Path(directory)
            long = scratch / ('a' * 100) / ('b' * 100) / ('c' * 80)
            native = Path('\\\\?\\' + str(long)) if os.name == 'nt' else long
            native.mkdir(parents=True)
            (native / 'package.nuspec').write_text('evidence', encoding='utf-8')
        self.assertFalse(scratch.exists())
        self.assertEqual('preserved failure', preserved.read_text(encoding='utf-8'))

    def test_failed_proof_preserved_without_promoting_or_retrying(self):
        self.recipe.write_text('raise RuntimeError("intentional probe rejection")', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Compatibility failed'):
            execute(self.root)
        self.assertEqual('open', load(self.root / LEDGER)['prerequisites'][0]['status'])
        self.assertIn('**Status**: Blocked', (self.root / 'docs/architecture/specification-roadmap.md').read_text(encoding='utf-8'))
        self.assertEqual(1, len(list(self.root.rglob('proof.json'))))

    def test_incomplete_conditional_scope_fails_before_execution(self):
        self.plan['readyWhenProven'][0]['prerequisites'] = []
        write(self.root / PLAN, self.plan)
        with self.assertRaisesRegex(ValueError, 'every affected|/readyWhenProven/0/prerequisites'):
            execute(self.root)
        self.assertEqual([], list(self.root.rglob('proof.json')))

    def test_later_invalid_recipe_blocks_before_any_probe(self):
        ledger = load(self.root / LEDGER)
        import copy
        second = copy.deepcopy(ledger['prerequisites'][0])
        second['id'] = 'later'
        ledger['prerequisites'].append(second)
        write(self.root / LEDGER, ledger)
        self.plan['probes'].append({'id': 'later', 'recipe': 'docs/architecture/missing.py', 'timeout': 10})
        self.plan['readyWhenProven'][0]['prerequisites'].append('later')
        write(self.root / PLAN, self.plan)
        with self.assertRaisesRegex(ValueError, 'existing repository-local Python'):
            execute(self.root)
        self.assertEqual([], list(self.root.rglob('proof.json')))


if __name__ == '__main__':
    unittest.main()

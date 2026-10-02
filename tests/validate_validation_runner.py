"""Receipt coverage and dependency-selection regressions; no external execution."""
import copy
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_validation as runner


class JournalTests(unittest.TestCase):
    def test_receipt_rejects_missing_failed_changed_and_duplicate_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / 'inventory.json'
            checks = [{'id': 'one', 'command': ['{python}', 'check.py'], 'group': 'release',
                       'needs': [], 'platforms': ['Windows', 'Linux']}]
            inventory.write_text(json.dumps({'checks': checks}))
            log = root / 'one.log'
            log.write_text('actual result')
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            step = {'id': 'one', 'command': [sys.executable, 'check.py'], 'exitCode': 0,
                    'startedAt': 'start', 'finishedAt': 'end', 'log': 'one.log', 'logSha256': digest(log)}
            value = {'source': {'commit': 'abc', 'tree': 'abc'}, 'platform': runner.platform.system(),
                     'inventorySha256': digest(inventory), 'browserEngines': 'chromium', 'steps': [step]}
            with patch.object(runner, 'ROOT', root), patch.object(runner, 'INVENTORY', inventory), patch('write_release_receipt.git', return_value='abc'):
                self.assertEqual('one', runner.validate_journal(value)[0]['id'])
                for mutation in ('missing', 'failed', 'command', 'duplicate', 'source', 'inventory', 'log'):
                    bad = copy.deepcopy(value)
                    if mutation == 'missing': bad['steps'] = []
                    if mutation == 'failed': bad['steps'][0]['exitCode'] = 1
                    if mutation == 'command': bad['steps'][0]['command'].append('--skip')
                    if mutation == 'duplicate': bad['steps'].append(copy.deepcopy(step))
                    if mutation == 'source': bad['source']['commit'] = 'old'
                    if mutation == 'inventory': bad['inventorySha256'] = 'old'
                    if mutation == 'log': bad['steps'][0]['logSha256'] = 'old'
                    with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                        runner.validate_journal(bad)

    def test_inventory_dependencies_precede_consumers_and_development_is_bounded(self):
        for system in ('Windows', 'Linux'):
            seen = set()
            for check in runner.selected('Release', system):
                self.assertTrue(set(check['needs']) <= seen, check['id'])
                seen.add(check['id'])
        self.assertTrue(all(c['group'] == 'development' for c in runner.selected('Development')))


class SourceGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.inventory = self.root / 'inventory.json'
        self.checks = [{'id': name, 'command': ['{python}', name + '.py'],
                       'group': 'release', 'needs': [], 'platforms': ['Windows', 'Linux']}
                      for name in ('first', 'second')]
        self.inventory.write_text(json.dumps({'checks': self.checks}))
        self.state = {'HEAD': 'abc', 'HEAD^{tree}': 'tree', 'dirty': ''}
        def fake_git(root, *args):
            return self.state[args[1]] if args[0] == 'rev-parse' else self.state['dirty']
        for mocked in (patch.object(runner, 'ROOT', self.root),
                       patch.object(runner, 'INVENTORY', self.inventory),
                       patch('write_release_receipt.git', side_effect=fake_git)):
            mocked.start()
            self.addCleanup(mocked.stop)
        self.value = {'source': {'commit': 'abc', 'tree': 'tree'},
                      'inventorySha256': hashlib.sha256(self.inventory.read_bytes()).hexdigest(),
                      'steps': [{'id': 'first', 'exitCode': 0}]}

    def test_clean_source_allows_continuation(self):
        runner.require_unchanged_release_source(self.value, 'after first')

    def test_commits_trees_tracked_and_untracked_edits_are_rejected(self):
        for field, changed in (('HEAD', 'new'), ('HEAD^{tree}', 'new'),
                               ('dirty', ' M scripts/check.py'), ('dirty', '?? new-check.py')):
            with self.subTest(field=field, changed=changed):
                previous = self.state[field]
                self.state[field] = changed
                with self.assertRaisesRegex(ValueError, 'PROGRAM_KIT_RELEASE_SOURCE_CHANGED'):
                    runner.require_unchanged_release_source(self.value, 'after first')
                self.state[field] = previous

    def test_inventory_changes_are_rejected(self):
        self.inventory.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Validation inventory changed'):
            runner.require_unchanged_release_source(self.value, 'after first')

    def test_failure_preserves_check_results_and_names_the_changed_source(self):
        self.state['dirty'] = ' M scripts/check.py'
        journal = self.root / 'journal.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(runner.guard_release_source(self.value, journal, 'after first'))
        result = json.loads(journal.read_text())
        self.assertEqual([{'id': 'first', 'exitCode': 0}], result['steps'])
        self.assertEqual('source-changed', result['status'])
        self.assertIn('scripts/check.py', result['diagnostic'])
        self.assertIn('cannot create a Release receipt', result['diagnostic'])

    def test_edit_during_check_stops_next_check_and_receipt(self):
        def check(command, *, evidence_directory, **kwargs):
            evidence_directory.mkdir(parents=True)
            for name in ('workflow.stdout.log', 'workflow.stderr.log'):
                (evidence_directory / name).write_text('')
            self.state['dirty'] = ' M scripts/other-agent-fix.py'
            return SimpleNamespace(exitCode=0, timedOut=False, cleanupComplete=True,
                                   logsDrained=True, as_dict=lambda: {})
        with patch.object(sys, 'argv', ['run_validation.py', '--suite', 'Release', '--approved', '--receipt']), \
                patch.dict(runner.os.environ, {}, clear=True), \
                patch('live.v2.supervisor.run_supervised', side_effect=check) as supervised, \
                patch.object(runner.subprocess, 'run') as receipt, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, runner.main())
        supervised.assert_called_once()
        receipt.assert_not_called()
        journal = next((self.root / 'artifacts/validation-runs').glob('*/journal.json'))
        result = json.loads(journal.read_text())
        self.assertEqual(['first'], [step['id'] for step in result['steps']])
        self.assertEqual('source-changed', result['status'])


if __name__ == '__main__':
    unittest.main()

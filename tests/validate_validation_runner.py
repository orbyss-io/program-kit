"""Receipt coverage and dependency-selection regressions; no external execution."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
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


if __name__ == '__main__':
    unittest.main()

"""Real loopback/process-restart calibration; never a coding agent or reference admission."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from live.v2.lending_host import verify
from live.v2.lending_oracle import LendingOracle
from live.v2.cli import supervisor_environment
from live.v2.common import LiveContractError, load_object


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lending-oracle-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'consumer'
        self.project.mkdir()
        self.contract = load_object(ROOT / 'tests/live/scenarios/knowledge-application/v1/http-contract.json')
        self.server = ROOT / 'tests/fixtures/knowledge-application/oracle-calibration/server.py'

    def exercise(self, mutant=''):
        return verify([sys.executable, str(self.server), mutant], self.project, self.root / 'evidence',
                      supervisor_environment(), self.contract, timeout=60)

    def test_real_restart_and_http_semantics_pass_with_process_evidence(self):
        result = self.exercise()
        self.assertEqual('passed', result['status'])
        self.assertEqual(3, len(result['hosts']))
        self.assertEqual(3, len({h['pid'] for h in result['hosts']}))
        self.assertTrue(all(h['cleanupComplete'] and h['logsDrained'] for h in result['hosts']))
        self.assertEqual(7, len(result['checks']))

    def test_denied_side_effect_is_detected(self):
        with self.assertRaisesRegex(LiveContractError, 'policy-before-effects'):
            self.exercise('denied-effect')
        report = load_object(self.root / 'evidence/http-acceptance.json')
        self.assertEqual('failed', report['status'])
        self.assertTrue(report['hosts'][0]['cleanupComplete'])

    def test_replay_side_effect_is_detected(self):
        with self.assertRaisesRegex(LiveContractError, 'idempotent-replay'):
            self.exercise('duplicate-reserve')

    def test_restart_data_loss_is_detected(self):
        with self.assertRaisesRegex(LiveContractError, 'durable-restart-preserves-identity'):
            self.exercise('lost-restart')

    def test_duplicate_recovery_notification_is_detected(self):
        with self.assertRaisesRegex(LiveContractError, 'single-notification-recovery'):
            self.exercise('duplicate-retry')

    def test_illegal_transition_is_detected(self):
        with self.assertRaisesRegex(LiveContractError, 'illegal-transition-no-effects'):
            self.exercise('illegal-transition')

    def test_external_host_is_rejected(self):
        with self.assertRaisesRegex(LiveContractError, 'LOOPBACK'):
            LendingOracle('https://example.com', lambda: None, self.contract)


if __name__ == '__main__':
    unittest.main()

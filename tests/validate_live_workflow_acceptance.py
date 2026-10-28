"""Offline retirement boundaries and retained one-use phase authorization; no workers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from owned_fixture import FixtureDirectory

from live.v2 import authorization as auth, cli, workflow_acceptance as workflow
from live.v2.bootstrap_provisioning import BootstrapProvisioner
from live.v2.common import LiveContractError, load_object, validate

ROOT = Path(__file__).resolve().parents[1]


class RetiredPaidBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = FixtureDirectory(prefix='retired-paid-bootstrap-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.schema = load_object(ROOT / 'tests/live/schemas/v2/authorization.schema.json')
        self.profile = {'integration':'codex', 'launcherVersion':'fictional-test', 'model':'fictional-test',
                        'reasoningEffort':'high', 'sandbox':'workspace-write', 'timeoutSeconds':60}
        self.arguments = {'scenario':{'id':'fictional-test', 'version':'1', 'digest':'a'*64},
                          'candidate':{'releaseReceipt':'fictional-test.json', 'releaseReceiptSha256':'b'*64},
                          'checkpoint':{'checkpointId':'fictional-test', 'digest':'c'*64},
                          'agent_profile':self.profile}

    def test_retired_authority_stops_before_any_read_write_or_consumption(self):
        for phase in auth.RETIRED_PHASES:
            with self.subTest(phase=phase):
                path = self.root / (phase + '.json')
                path.write_text('fictional preserved original', encoding='utf-8')
                before = path.read_bytes()
                with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                    auth.issue_authorization(path, {}, phase=phase, bootstrap_sessions=8, **self.arguments)
                with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                    auth.validate_authorization(path, {}, phase=phase, scenario_digest='a'*64,
                                                candidate_receipt_digest='b'*64, checkpoint_digest=None)
                with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                    auth.consume_authorization(path, {'phase':phase}, self.root / 'consumed')
                self.assertEqual(before, path.read_bytes())
                self.assertFalse((self.root / 'consumed').exists())
                with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                    auth.session_limit(phase, 8)

    def test_retired_python_dispatch_and_provisioner_never_touch_inputs(self):
        with patch.object(cli, '_phase_inputs', side_effect=AssertionError('must not inspect inputs')), \
             patch.object(cli, 'run_supervised', side_effect=AssertionError('must not dispatch')):
            for operation in (lambda: cli.bootstrap(argparse.Namespace()),
                              lambda: workflow.issue(argparse.Namespace()),
                              lambda: workflow.run(argparse.Namespace()),
                              lambda: workflow.driver(self.root / 'missing-job.json'),
                              lambda: workflow.reserve_dispatch(self.root / 'counter.json', 8, 'old', 'step'),
                              lambda: workflow.controlled_fault(self.root, self.root, None),
                              lambda: BootstrapProvisioner(self.root / 'missing-project', self.root / 'evidence')):
                with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                    operation()
        self.assertEqual([], list(self.root.iterdir()))

    def test_retired_cli_commands_refuse_without_reading_missing_authority(self):
        for relative, arguments in (
            ('tests/live/v2/cli.py', ['bootstrap']),
            ('tests/live/v2/cli.py', ['session-limit', '--phase', 'bootstrap-checkpoint', '--release-receipt', 'missing.json']),
            ('tests/live/v2/workflow_acceptance.py', ['run', '--authorization', 'missing.json']),
            ('tests/live/v2/workflow_acceptance.py', ['driver', '--job', 'missing.json']),
            ('tests/live/v2/workflow_acceptance.py', ['authorize', '--phase', 'workflow-resume'])):
            result = subprocess.run([sys.executable, str(ROOT / relative), *arguments], cwd=self.root,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(3, result.returncode, result.stdout + result.stderr)
            self.assertIn('LIVE_BOOTSTRAP_WORKFLOW_RETIRED', result.stderr)
            self.assertIn('$speckit-program-kit-governance-product-intake', result.stderr)
        self.assertEqual([], list(self.root.iterdir()))

    def test_powershell_retirement_precedes_receipt_model_and_authorization_lookup(self):
        shell = shutil.which('pwsh') or shutil.which('powershell')
        if not shell:
            self.skipTest('PowerShell is unavailable; Python boundaries are independently checked')
        for relative, arguments in (
            ('scripts/New-LiveBootstrapCheckpoint.ps1', []),
            ('scripts/New-LiveBootstrapCheckpoint.ps1', ['-Authorization', 'missing.json']),
            ('scripts/New-LiveAcceptanceAuthorization.ps1', ['-Phase', 'bootstrap-checkpoint']),
            ('scripts/New-LiveAcceptanceAuthorization.ps1', ['-Phase', 'workflow-resume'])):
            result = subprocess.run([shell, '-NoProfile', '-NonInteractive', '-File', str(ROOT / relative), *arguments],
                                    cwd=self.root, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('LIVE_BOOTSTRAP_WORKFLOW_RETIRED', result.stdout + result.stderr)
        self.assertEqual([], list(self.root.iterdir()))

    def test_independent_phases_retain_checkpoint_binding_limits_and_one_use(self):
        self.assertEqual({'building-block-consumer', 'feature-intake', 'feature-planning', 'feature-plan-tasks',
                          'feature-setup', 'feature-delivery', 'upgrade-consumer', 'upgrade-continuation'}, auth.PHASES)
        for phase in auth.PHASES:
            with self.subTest(phase=phase):
                path = self.root / (phase + '.json')
                manifest = auth.issue_authorization(path, self.schema, phase=phase, **self.arguments)
                self.assertEqual(1, manifest['limits']['maximumPaidSessions'])
                checked = auth.validate_authorization(path, self.schema, phase=phase, scenario_digest='a'*64,
                                                       candidate_receipt_digest='b'*64, checkpoint_digest='c'*64)
                with self.assertRaisesRegex(LiveContractError, 'CHECKPOINT_MISMATCH'):
                    auth.validate_authorization(path, self.schema, phase=phase, scenario_digest='a'*64,
                                                candidate_receipt_digest='b'*64, checkpoint_digest='d'*64)
                auth.consume_authorization(path, checked, self.root / 'consumed')
                with self.assertRaisesRegex(LiveContractError, 'REPLAYED'):
                    auth.consume_authorization(path, manifest, self.root / 'consumed')
        with self.assertRaisesRegex(LiveContractError, 'CHECKPOINT_REQUIRED'):
            auth.issue_authorization(self.root / 'missing-parent.json', self.schema, phase='feature-intake',
                                     **{**self.arguments, 'checkpoint':None})

    def test_historical_authorization_schema_remains_readable_without_execution_authority(self):
        path = self.root / 'historical.json'
        manifest = auth.issue_authorization(path, self.schema, phase='building-block-consumer', **self.arguments)
        manifest.update(phase='bootstrap-checkpoint', checkpoint=None)
        manifest['limits']['maximumPaidSessions'] = 8
        path.write_text(json.dumps(manifest), encoding='utf-8')
        before = path.read_bytes()
        validate(load_object(path), self.schema)
        self.assertEqual(before, path.read_bytes())
        with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
            auth.consume_authorization(path, manifest, self.root / 'consumed')
        self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()

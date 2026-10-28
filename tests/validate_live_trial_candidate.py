"""Development trial receipts never imply Release validation or authorize a paid worker."""
import copy
import os
from owned_fixture import FixtureDirectory
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from live.v2 import trial_candidate as trial
from live.v2 import cli
from live.v2.candidate import bootstrap_session_limit, validate_candidate_receipt, validate_release_receipt
from live.v2.authorization import issue_authorization, validate_authorization
from live.v2.common import LiveContractError, atomic_write_json, load_object

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'tests/live/schemas/v2'


class TrialTests(unittest.TestCase):
    def setUp(self):
        temporary = FixtureDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / 'trial.json'
        artifacts = []
        for name in sorted(trial.artifact_names('0.12.0')):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic unit-test artifact', encoding='utf-8')
            artifacts.append(trial.file_record(self.root,path))
        logs = []
        for name in trial.STEPS:
            for stream in ('stdout','stderr'):
                path = self.root / f'artifacts/preparation/{name}/workflow.{stream}.log'
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('synthetic unit-test log',encoding='utf-8')
                logs.append(trial.file_record(self.root,path))
        catalog = self.root / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
        atomic_write_json(catalog, {})
        self.value = {'schemaVersion':'2.0','status':'development-trial-prepared','acceptanceScope':'development-trial-only',
                      'releaseValidationPassed':False,'version':'0.12.0','source':{'commit':'a'*40,'tree':'b'*40,'clean':True},
                      'platform':{'system':'test','release':'test','machine':'test'},
                      'toolchains':dict.fromkeys(('python','dotnet','node','npm','git','specify','codex'),'unit-test'),
                      'steps':[{'id':name,'command':['unit-test'],'exitCode':0,'startedAt':'test','finishedAt':'test'} for name in trial.STEPS],
                      'preparationLogs':logs,'artifacts':artifacts,'catalog':{'sha256':'c'*64},'startedAt':'test','finishedAt':'test'}
        atomic_write_json(self.path,self.value)
        mocked = patch.object(trial.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='c'*64))
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_explicit_trial_selection_accepts_exact_evidence(self):
        value, digest = validate_candidate_receipt(self.root,self.path,SCHEMAS,'development-trial')
        self.assertFalse(value['releaseValidationPassed'])
        self.assertEqual(len(digest),64)

    def test_complete_tooling_archive_is_bound_and_cannot_be_omitted(self):
        name = 'artifacts/program-kit-tooling-0.12.0.zip'
        self.assertIn(name, {row['path'] for row in self.value['artifacts']})
        changed = copy.deepcopy(self.value)
        changed['artifacts'] = [row for row in changed['artifacts'] if row['path'] != name]
        atomic_write_json(self.path, changed)
        with self.assertRaisesRegex(LiveContractError, 'ARTIFACT_INVENTORY_MISMATCH'):
            trial.validate_trial_receipt(self.root, self.path, SCHEMAS)
        atomic_write_json(self.path, self.value)
        (self.root / name).write_bytes(b'changed complete tooling')
        with self.assertRaisesRegex(LiveContractError, 'EVIDENCE_CHANGED'):
            trial.validate_trial_receipt(self.root, self.path, SCHEMAS)

    def test_trial_is_rejected_by_release_schema_and_default_loader(self):
        for action in (lambda:validate_release_receipt(self.root,self.path,load_object(SCHEMAS/'release-receipt.schema.json')),
                       lambda:validate_candidate_receipt(self.root,self.path,SCHEMAS)):
            with self.assertRaises(LiveContractError):
                action()

    def test_changed_archive_or_log_invalidates_trial(self):
        for record in (self.value['artifacts'][0],self.value['preparationLogs'][0]):
            path = self.root / record['path']
            before = path.read_bytes()
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(LiveContractError,'EVIDENCE_CHANGED'):
                trial.validate_trial_receipt(self.root,self.path,SCHEMAS)
            path.write_bytes(before)

    def test_incomplete_preparation_cannot_be_sealed(self):
        changed = copy.deepcopy(self.value)
        changed['steps'].pop()
        atomic_write_json(self.path,changed)
        with self.assertRaisesRegex(LiveContractError,'STEPS_MISSING'):
            trial.validate_trial_receipt(self.root,self.path,SCHEMAS)

    def test_trial_cannot_claim_release_success(self):
        self.value['releaseValidationPassed'] = True
        atomic_write_json(self.path,self.value)
        with self.assertRaises(LiveContractError):
            trial.validate_trial_receipt(self.root,self.path,SCHEMAS)

    def test_bootstrap_limit_refuses_before_reading_package_or_receipt(self):
        with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
            bootstrap_session_limit(self.root, {})

    def test_bootstrap_authorization_cannot_be_reissued(self):
        original = self.path.read_bytes()
        with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
            issue_authorization(self.path, {}, phase='bootstrap-checkpoint', scenario={}, candidate={},
                                checkpoint=None, agent_profile={}, bootstrap_sessions=8)
        self.assertEqual(original, self.path.read_bytes())

    def test_worker_path_removes_missing_and_duplicate_entries_without_reordering(self):
        first, second = self.root / 'first', self.root / 'second'
        first.mkdir()
        second.mkdir()
        original = os.pathsep.join(map(str,(first,self.root/'missing',second,first)))
        with patch.object(cli.shutil,'which',return_value=None):
            self.assertEqual(cli.compact_windows_path(original),os.pathsep.join(map(str,(first,second))))

    def test_worker_path_refuses_tool_selection_changes_or_remaining_overflow(self):
        with patch.object(Path,'is_dir',return_value=True), patch.object(cli.shutil,'which',side_effect=['before','after']):
            with self.assertRaisesRegex(LiveContractError,'PATH_SELECTION_CHANGED'):
                cli.compact_windows_path('test')
        entries = os.pathsep.join(f'{index}-'+'x'*200 for index in range(50))
        with patch.object(Path,'is_dir',return_value=True):
            with self.assertRaisesRegex(LiveContractError,'PATH_TOO_LONG'):
                cli.compact_windows_path(entries)

    def test_retired_bootstrap_precedes_authority_consumption_or_worker(self):
        with patch.object(cli, '_phase_inputs', side_effect=AssertionError('must not inspect authority')), \
             patch.object(cli, 'consume_authorization') as consume, patch.object(cli, 'run_supervised') as worker:
            with self.assertRaisesRegex(LiveContractError, 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED'):
                cli.bootstrap(SimpleNamespace(authorization='unused'))
            consume.assert_not_called()
            worker.assert_not_called()


if __name__ == '__main__':
    unittest.main()

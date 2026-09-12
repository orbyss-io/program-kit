"""Development trial receipts never imply Release validation or authorize a paid worker."""
import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from live.v2 import trial_candidate as trial
from live.v2.candidate import bootstrap_session_limit, validate_candidate_receipt, validate_release_receipt
from live.v2.authorization import issue_authorization, validate_authorization
from live.v2.common import LiveContractError, atomic_write_json, load_object

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'tests/live/schemas/v2'


class TrialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
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

    def test_bootstrap_limit_tracks_verified_seven_eight_and_nine_step_packages(self):
        path = self.root / 'artifacts/program-kit-bootstrap-0.12.0.zip'
        for count in (7,8,9):
            with zipfile.ZipFile(path,'w') as package:
                package.writestr('workflow.yml', 'steps:\n' + ''.join(f'  - id: step-{number}\n    type: command\n' for number in range(count)))
            receipt = {'version':'0.12.0','artifacts':[trial.file_record(self.root,path)]}
            self.assertEqual(bootstrap_session_limit(self.root,receipt),count)
        path.write_bytes(b'changed archive')
        with self.assertRaisesRegex(LiveContractError,'WORKFLOW_HASH_MISMATCH'):
            bootstrap_session_limit(self.root,receipt)

    def test_bootstrap_authorization_requires_verified_count_and_rejects_limit_change(self):
        arguments = {'phase':'bootstrap-checkpoint','scenario':{'id':'test','version':'1','digest':'a'*64},
                     'candidate':{'releaseReceipt':'test','releaseReceiptSha256':'b'*64}, 'checkpoint':None,
                     'agent_profile':{'integration':'codex','launcherVersion':'test','model':'test','reasoningEffort':'high','sandbox':'workspace-write','timeoutSeconds':60}}
        schema = load_object(SCHEMAS / 'authorization.schema.json')
        with self.assertRaisesRegex(LiveContractError,'VERIFIED_WORKFLOW_LIMIT_REQUIRED'):
            issue_authorization(self.path,schema,**arguments)
        manifest = issue_authorization(self.path,schema,bootstrap_sessions=8,**arguments)
        self.assertEqual(manifest['limits']['maximumPaidSessions'],8)
        expected = {'phase':'bootstrap-checkpoint','scenario_digest':'a'*64,'candidate_receipt_digest':'b'*64,'checkpoint_digest':None,'bootstrap_sessions':8}
        validate_authorization(self.path,schema,**expected)
        for wrong in (7,9):
            manifest['limits']['maximumPaidSessions'] = wrong
            atomic_write_json(self.path,manifest)
            with self.assertRaisesRegex(LiveContractError,'SESSION_LIMIT'):
                validate_authorization(self.path,schema,**expected)


if __name__ == '__main__':
    unittest.main()

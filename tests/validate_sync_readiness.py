from __future__ import annotations

import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import repository_sync as sync
import sync_readiness as readiness
import package_execution


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='program-kit-readiness-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.restore = sync.provider('program-kit-building-blocks/scripts/restore_dependencies.py')
        self.feature = 'specs/RM01'
        sync.write(self.root / self.feature / 'artifact-ownership.json', {
            'profiles':['typescript-vite'], 'artifacts':[{'path':'web/package.json'}]})
        self.setup = {'phase':'implementation', 'feature':self.feature,
                      'targets':[], 'javascript':True, 'dotnet':False}
        sync.write(self.root / 'web/package.json', {'dependencies':{'react':'19.2.8'}})
        sync.write(self.root / 'web/package-lock.json', {'lockfileVersion':3})
        sync.write(self.root / '.program-kit/evidence/toolchain.json', {'satisfied':True})
        self.lock = readiness.dependencies(self.root, self.setup, {})

    def evidence(self):
        return {'mode':'locked', 'satisfied':True,
                'subjects':[{'ecosystem':item['ecosystem'], 'subject':item['subject']} for item in self.restore.restore_commands(self.root,self.lock,'locked')],
                'inputDigest':package_execution.canonical_hash(self.restore.input_basis(self.root, self.lock)),
                'nativeLocks':self.restore.native_lock_records(self.root)}

    def test_current_locked_proof_invalidates_for_each_dependency_input(self):
        proof = self.evidence()
        self.restore.verify_evidence(self.root, self.lock, proof)
        for relative in ('web/package.json', 'web/package-lock.json', '.program-kit/evidence/toolchain.json'):
            path = self.root / relative
            before = path.read_bytes()
            if relative.endswith('toolchain.json'):
                sync.write(path, {'satisfied':False})
            else:
                path.write_bytes(before + b'\n')
            with self.assertRaisesRegex(RuntimeError, 'stale|changed'):
                self.restore.verify_evidence(self.root, self.lock, proof)
            path.write_bytes(before)
        self.restore.verify_evidence(self.root, self.lock, proof)

    def test_renew_proof_is_not_locked_verification(self):
        proof = self.evidence()
        proof['mode'] = 'renew'
        with self.assertRaisesRegex(RuntimeError, 'locked'):
            self.restore.verify_evidence(self.root, self.lock, proof)

    def test_generated_dependency_plan_tracks_owned_targets_only(self):
        sync.write(self.root / 'future/package.json', {'dependencies':{'react':'19.2.8'}})
        self.assertEqual([target['path'] for target in self.lock['targets']], ['web/package.json'])
        self.assertEqual(self.lock, readiness.dependencies(self.root, self.setup, {}))
        self.assertEqual(len(self.lock['planDigest']), 64)

    def test_planning_does_not_require_application_skeleton_but_setup_does(self):
        (self.root / 'web/package.json').unlink()
        with patch.object(readiness, 'graph_errors', return_value=[]):
            plan_errors = readiness.blockers(self.root, {**self.setup, 'phase':'after-plan'}, [], self.restore)
            setup_errors = readiness.blockers(self.root, {**self.setup, 'phase':'implementation-setup'}, [], self.restore)
        self.assertEqual(plan_errors, [])
        self.assertTrue(any('skeleton' in message for message in setup_errors))

    def test_deleted_dependency_subject_receipt_cannot_pass(self):
        sync.write(self.root / '.program-kit/sync/dependencies.json', {'targets':[]})
        with patch.object(readiness, 'graph_errors', return_value=[]):
            errors = readiness.blockers(self.root, self.setup, [], self.restore)
        self.assertTrue(any('subjects changed' in error for error in errors))

    def test_stale_reviewed_restore_request_stops_before_process(self):
        lock_path = self.root / '.program-kit/sync/dependencies.json'
        sync.write(lock_path, self.lock)
        request_path = self.root / 'reviewed.json'
        sync.write(request_path, self.restore.restore_request(self.root, lock_path, self.lock, 'renew'))
        sync.write(self.root / 'web/package.json', {'dependencies':{'react':'19.2.9'}})
        arguments = ['restore', 'renew', '--target', str(self.root), '--lock', '.program-kit/sync/dependencies.json',
                     '--request', 'reviewed.json', '--approved']
        with patch.object(sys, 'argv', arguments), patch.object(package_execution, 'execute') as execute:
            self.assertEqual(self.restore.main(), 2)
            execute.assert_not_called()

    def test_interrupted_restore_resumes_only_unfinished_unchanged_subject(self):
        sync.write(self.root / 'web2/package.json', {'dependencies':{'react':'19.2.8'}})
        second = {**self.lock['targets'][0], 'id':'second', 'path':'web2/package.json'}
        lock = {**self.lock, 'targets':self.lock['targets'] + [second]}
        sync.write(self.root / '.program-kit/sync/dependencies.json', lock)
        calls = []
        fail = True
        def execute(repository, evidence, packages, arguments, cwd, timeout):
            calls.append(cwd.name)
            if cwd.name == 'web2' and fail:
                raise ValueError('simulated interrupted second subject')
            sync.write(cwd / 'package-lock.json', {'lockfileVersion':3})
            return subprocess.CompletedProcess([], 0, '', ''), {}
        args = ['restore','renew','--target',str(self.root),'--lock','.program-kit/sync/dependencies.json','--approved']
        with patch.object(sys, 'argv', args), patch.object(package_execution, 'execute', side_effect=execute):
            self.assertEqual(self.restore.main(), 2)
            fail = False
            self.assertEqual(self.restore.main(), 0)
        self.assertEqual(calls, ['web','web2','web2'])


if __name__ == '__main__':
    unittest.main()

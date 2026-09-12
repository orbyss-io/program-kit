"""Offline Phase 1 behavior, provenance and installed-runtime acceptance."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'extensions/program-kit-governance/scripts'
EXTENSION = ROOT / 'extensions/program-kit-delivery'
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(EXTENSION / 'scripts'))
import json_schema
import schema_runtime
import delivery_authority as authority
import delivery_contract as contract
import delivery


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='program-kit-delivery-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.profile = json.loads((EXTENSION / 'references/azure-default.json').read_text())
        self.artifact = {'repositoryId': 'R1', 'commit': 'a' * 40, 'path': 'docs/plan.md', 'sha256': 'b' * 64}

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def install(self):
        shutil.copytree(EXTENSION, self.root / '.specify/extensions/program-kit-delivery')

    def config(self, enabled=False):
        self.install()
        snapshot = self.write('.program-kit/delivery/profiles/policy.json', self.profile)
        binding = {'schemaVersion': 1, 'recordType': 'binding', 'state': 'enabled' if enabled else 'prepared',
            'space': self.profile['space'], 'repositoryId': 'R1', 'teamId': 'T1', 'provider': 'azure',
            'profile': {'repositoryId': 'policy-repo', 'commit': 'a' * 40, 'path': 'delivery/profile.json',
                'sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(), 'snapshot': snapshot.relative_to(self.root).as_posix()},
            'activationId': 'A1' if enabled else None, 'artifactPaths': {'roadmap': 'docs/architecture/specification-roadmap.md'},
            'teamDefaults': {'area': None, 'iteration': None},
            'workBindings': {'SPEC-1': {'requirementId': 'REQ-1', 'executionMode': 'direct', 'taskId': None}}}
        history = {'schemaVersion': 1, 'recordType': 'history', 'records': []}
        if enabled:
            history['records'] = [self.event(binding, 'A1', 'activate')]
        self.write(authority.BINDING, binding)
        self.write(authority.HISTORY, history)
        return binding, history

    def event(self, binding, identity, action, previous=None):
        return {'id': identity, 'action': action, 'actorId': 'owner', 'decisionRef': 'approved-synthetic-decision',
                'previousDigest': authority.digest(previous) if previous else None,
                'bindingDigest': authority.digest(binding), 'profileDigest': binding['profile']['sha256'],
                'providerEvidence': self.artifact}

    def work(self):
        return {'schemaVersion': 1, 'recordType': 'work', 'id': 'E1', 'kind': 'epic',
                'title': 'Recover interrupted checkout', 'outcome': 'Customers can safely retry', 'businessOwnerId': 'owner'}

    def test_disabled_needs_no_runtime_credentials_or_network(self):
        with patch('socket.socket', side_effect=AssertionError('network')), patch.object(authority, 'runtime', side_effect=AssertionError('runtime')):
            self.assertEqual(authority.require_admission(self.root, 'implementation')['state'], 'disabled')

    def test_defaults_are_valid_proposals_without_self_commit(self):
        for provider in ('azure', 'github'):
            profile = json.loads((EXTENSION / f'references/{provider}-default.json').read_text())
            contract.validate_profile(profile)
            self.assertNotIn('profileRevision', profile)

    def test_preparation_retains_local_authority(self):
        binding, _ = self.config()
        result = delivery.prepare(self.root, binding)
        self.assertEqual(result['providerCalls'], 0)
        self.assertEqual(authority.inspect(self.root)['authority'], 'local')

    def test_enabled_configuration_does_not_mint_admission(self):
        self.config(True)
        self.assertEqual(authority.inspect(self.root)['authority'], 'platform')
        for activity in ('refinement', 'implementation', 'delivery', 'acceptance'):
            with self.assertRaisesRegex(ValueError, 'PKD_ADAPTER_UNAVAILABLE'):
                authority.require_admission(self.root, activity)

    def test_missing_enabled_runtime_is_explicit(self):
        self.config(True)
        shutil.rmtree(self.root / '.specify/extensions/program-kit-delivery')
        with self.assertRaisesRegex(ValueError, 'PKD_EXTENSION_MISSING'):
            authority.inspect(self.root)

    def test_one_missing_record_never_disables(self):
        self.config(True)
        (self.root / authority.BINDING).unlink()
        with self.assertRaisesRegex(ValueError, 'PKD_CONFIG_MISSING'):
            authority.inspect(self.root)

    def test_malformed_and_duplicate_keys_are_rejected(self):
        self.config()
        for raw in ('{"state":"prepared","state":"disabled"}', '{broken', 'NaN'):
            (self.root / authority.BINDING).write_text(raw)
            with self.assertRaises(ValueError):
                authority.inspect(self.root)

    def test_changed_binding_and_snapshot_are_rejected(self):
        binding, history = self.config(True)
        self.write(authority.BINDING, dict(binding, teamId='other-team'))
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            authority.inspect(self.root)
        self.write(authority.BINDING, binding)
        self.write(binding['profile']['snapshot'], dict(self.profile, tagNamespace='changed'))
        with self.assertRaisesRegex(ValueError, 'snapshot digest mismatch'):
            authority.inspect(self.root)

    def test_binding_revision_changes_need_new_accepted_record(self):
        binding, _ = self.config(True)
        binding['profile']['commit'] = 'c' * 40
        self.write(authority.BINDING, binding)
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            authority.inspect(self.root)

    def test_no_local_config_override(self):
        self.config(True)
        path = self.root / '.specify/extensions/program-kit-governance/program-kit-governance-config.local.yml'
        path.parent.mkdir(parents=True)
        path.write_text('delivery:\n  enabled: false\n  binding: other.json\n')
        with self.assertRaisesRegex(ValueError, 'PKD_ADAPTER_UNAVAILABLE'):
            authority.require_admission(self.root, 'implementation')

    def test_prepare_cannot_replace_connected_history(self):
        binding, _ = self.config(True)
        with self.assertRaisesRegex(ValueError, 'PKD_ACTIVATION_REQUIRED'):
            delivery.prepare(self.root, dict(binding, state='prepared', activationId=None))

    def test_handwritten_disconnect_cannot_restore_authority(self):
        binding, history = self.config(True)
        disconnected = dict(binding, state='disabled', activationId='D1')
        history['records'].append(self.event(disconnected, 'D1', 'disconnect', history['records'][-1]))
        self.write(authority.BINDING, disconnected)
        self.write(authority.HISTORY, history)
        with self.assertRaisesRegex(ValueError, 'PKD_DISCONNECT_UNAVAILABLE'):
            authority.inspect(self.root)

    def git(self, *args):
        result = subprocess.run(['git', '-c', 'safe.directory=' + self.root.as_posix(), '-c', 'core.excludesFile=',
            '-c', 'user.name=Delivery Test', '-c', 'user.email=delivery@example.invalid', '-c', 'commit.gpgsign=false', *args],
            cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deleting_both_files_does_not_erase_committed_activation(self):
        self.config(True)
        self.git('init')
        self.git('add', '.program-kit/delivery')
        self.git('commit', '-m', 'Synthetic activation baseline')
        (self.root / authority.BINDING).unlink()
        (self.root / authority.HISTORY).unlink()
        with self.assertRaisesRegex(ValueError, 'PKD_CONFIG_MISSING'):
            authority.inspect(self.root)

    def test_committed_history_prefix_cannot_be_replaced(self):
        binding, history = self.config(True)
        self.git('init'); self.git('add', '.program-kit/delivery'); self.git('commit', '-m', 'Baseline')
        history['records'][0]['actorId'] = 'different-owner'
        self.write(authority.HISTORY, history)
        with self.assertRaisesRegex(ValueError, 'PKD_HISTORY_CHANGED'):
            authority.inspect(self.root)

    def test_minimal_epic_needs_only_three_business_inputs(self):
        self.assertTrue(contract.validate_work(self.work(), 'draft')['valid'])
        with self.assertRaises(ValueError):
            contract.validate_work(dict(self.work(), outcome=''), 'draft')

    def test_refinement_does_not_require_a_plan(self):
        work = dict(self.work(), kind='requirement', scope='Retry current payment', nonGoals='Refund redesign',
            architecturePrerequisites='Existing payment boundary accepted', acceptanceCriteria=[{'id': 'AC-1', 'criterion': 'Retry preserves one payment'}])
        self.assertTrue(contract.validate_work(work, 'refinement')['valid'])
        with self.assertRaises(ValueError):
            contract.validate_work(work, 'implementation')

    def implementation_work(self):
        work = contract.normalize_work(dict(self.work(), kind='requirement', scope='Retry', nonGoals='Refunds', architecturePrerequisites='Accepted',
            acceptanceCriteria=[{'id': 'AC-1', 'criterion': 'No duplicate charge'}], accountableExecutorId='developer',
            verificationPlan='Integration suite', dependencyAssessment='Contract ready', coordinationAssessment='No known conflict', technicalArtifacts=[self.artifact]))
        work['acceptedBasis'] = {'businessDigest': contract.business_digest(work), 'artifactDigest': authority.digest(work['technicalArtifacts']), 'actorId': 'owner', 'decisionRef': 'accepted-plan'}
        return work

    def test_implementation_content_never_grants_provider_admission(self):
        self.assertFalse(contract.validate_work(self.implementation_work(), 'implementation')['deliveryAdmission'])

    def test_changed_business_or_technical_basis_blocks_content_readiness(self):
        work = self.implementation_work()
        for changed in (dict(work, outcome='Different business scope'), dict(work, architecturePrerequisites='Different architecture direction'),
                        dict(work, technicalArtifacts=[]), dict(work, openDecisions=['Which API?'])):
            with self.assertRaises(ValueError):
                contract.validate_work(changed, 'implementation')

    def test_tasks_need_meaningful_parent_contribution(self):
        with self.assertRaises(ValueError):
            contract.validate_work(dict(self.work(), kind='task'), 'draft')
        task = dict(self.work(), kind='task', parentRequirementId='REQ-1', contribution='Verify receiving integration')
        self.assertTrue(contract.validate_work(task, 'draft')['valid'])

    def test_non_object_inputs_are_contract_errors(self):
        for value in (None, [], 'invalid'):
            with self.assertRaisesRegex(ValueError, 'PKD_CONTRACT_INVALID'):
                contract.validate_work(value, 'draft')
            with self.assertRaisesRegex(ValueError, 'PKD_CONTRACT_INVALID'):
                delivery.prepare(self.root, value)

    def test_direct_and_delegated_work_are_exclusive(self):
        work = dict(self.work(), kind='requirement', taskIds=['TASK-1'])
        with self.assertRaises(ValueError):
            contract.validate_work(work, 'draft')
        self.assertTrue(contract.validate_work(dict(work, executionMode='delegated'), 'draft')['valid'])

    def test_binding_delegation_requires_task_identity(self):
        binding, history = self.config()
        binding['workBindings']['SPEC-1']['executionMode'] = 'delegated'
        with self.assertRaises(ValueError):
            contract.validate_configuration(self.root, binding, history)

    def test_core_entrypoints_stop_before_local_lifecycle_can_authorize(self):
        import governance_state, lifecycle_state, specification_intake
        self.config(True)
        original = Path.cwd()
        try:
            os.chdir(self.root)
            for function in (lambda: governance_state.validate_roadmap(True), governance_state.evaluate_readiness,
                             lambda: specification_intake.check(self.root, 'SPEC-1'),
                             lambda: specification_intake.confirm(self.root, 'SPEC-1', 'hash', 'human', 'yes')):
                with self.assertRaisesRegex(ValueError, 'PKD_ADAPTER_UNAVAILABLE'):
                    function()
            self.assertEqual(lifecycle_state.verify_before_implement(self.root, self.root / 'specs/one'), 2)
            preflight = subprocess.run([sys.executable, str(CORE / 'implementation_preflight.py'),
                '--repository', str(self.root), '--feature-dir', 'specs/one'], capture_output=True, text=True)
            self.assertEqual(preflight.returncode, 2, preflight.stderr)
            self.assertIn('PKD_ADAPTER_UNAVAILABLE', preflight.stderr)
            view = governance_state._roadmap_view([{'id': 'SPEC-1', 'title': 'Outcome', 'Status': 'Delivered'}])
            self.assertNotIn('`Delivered`', view)
            self.assertIn('Provider assessment required', view)
        finally:
            os.chdir(original)

    def test_installed_cli_is_offline_and_default_disabled(self):
        self.install()
        installed_core = self.root / '.specify/extensions/program-kit-governance/scripts'
        installed_core.mkdir(parents=True)
        for name in ('delivery_authority.py', 'json_schema.py', 'schema_runtime.py', 'contract_shapes.py', 'json-schema-requirements.txt'):
            shutil.copy2(CORE / name, installed_core / name)
        # Use the already provisioned pinned runtime; do not download during validation.
        shutil.copytree(schema_runtime.runtime_path(), schema_runtime.runtime_path(self.root))
        script = self.root / '.specify/extensions/program-kit-delivery/scripts/delivery.py'
        result = subprocess.run([sys.executable, str(script), '--repository', str(self.root), 'status'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['state'], 'disabled')
        result = subprocess.run([sys.executable, str(script), 'validate-profile', '--input', str(EXTENSION / 'references/azure-default.json')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['providerVerified'])


if __name__ == '__main__':
    unittest.main()

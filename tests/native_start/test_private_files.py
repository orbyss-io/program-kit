"""Private lifecycle and selected dependency regressions; no consumer data."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import composition_model as model
import composition_run as run
from composition_fixture import two_apps


def graph():
    value = two_apps(ROOT)
    value['authority'] = {'architectureMap': 'docs/architecture/map.json', 'decisionIds': ['fixture']}
    value['resources']['evidence'] = {'kind': 'privateFiles', 'ownerRef': 'application'}
    value['bindings'].append({'kind': 'privateFiles', 'filesRef': 'evidence', 'hostRef': 'application-host',
        'shellRef': 'application-shell', 'featureRef': 'feature-0', 'setting': 'Root'})
    model.environment(value)['evidence'] = {'directory': 'artifacts/private-evidence/policies'}
    return model.validate(value)


class PrivateFilesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.graph = graph()

    def test_first_provision_retains_bytes_and_removed_resource_history(self):
        run.provision_private_files(self.root, self.graph)
        directory = model.private_directories(self.graph, repository=self.root)['evidence']
        payload = directory / 'synthetic.bin'; payload.write_bytes(bytes(range(256)))
        history = run.provision_private_files(self.root, self.graph)
        self.assertEqual(bytes(range(256)), payload.read_bytes())
        removed = deepcopy(self.graph)
        del removed['resources']['evidence']; del model.environment(removed)['evidence']
        removed['bindings'] = [row for row in removed['bindings'] if row['kind'] != 'privateFiles']
        self.assertEqual(history, run.provision_private_files(self.root, removed))
        payload.unlink(); directory.rmdir()
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            run.provision_private_files(self.root, self.graph)
        self.assertFalse(directory.exists())

    def test_ordinary_run_cannot_provision_or_relocate_storage(self):
        with self.assertRaisesRegex(ValueError, 'explicit preparation'):
            run.provision_private_files(self.root, self.graph, create=False)
        run.provision_private_files(self.root, self.graph)
        model.environment(self.graph)['evidence']['directory'] = 'artifacts/private-evidence/new'
        with self.assertRaisesRegex(ValueError, 'location changed'):
            run.provision_private_files(self.root, self.graph)
        self.assertFalse((self.root / 'artifacts/private-evidence/new').exists())

    def test_prior_verified_mount_is_retained_even_without_new_lifecycle_fields(self):
        directory = self.root / model.environment(self.graph)['evidence']['directory']
        directory.mkdir(parents=True)
        document = {'name': run.project(self.root, self.graph), 'services': {'host': {'volumes': [
            {'type': 'bind', 'source': str(directory), 'target': '/private-evidence/evidence', 'read_only': False}]}}}
        compose = self.root / 'artifacts/composition/compose.json'
        run.write(compose, document)
        run.write(self.root / run.STATE, {'project': document['name'], 'compose': 'artifacts/composition/compose.json',
                                       'composeSha256': run.runtime_closure.sha256(compose)})
        directory.rmdir()
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            run.provision_private_files(self.root, self.graph)
        self.assertFalse(directory.exists())

    def test_private_binding_cannot_use_foreign_host_or_duplicate_target(self):
        row = self.graph['bindings'][-1]
        row['hostRef'] = 'assessment-host'
        with self.assertRaisesRegex(ValueError, 'foreign placement'):
            model.validate(self.graph)
        row['hostRef'] = 'application-host'
        self.graph['resources']['other'] = {'kind': 'privateFiles', 'ownerRef': 'application'}
        model.environment(self.graph)['other'] = {'directory': 'artifacts/private-evidence/other'}
        self.graph['bindings'].append({**row, 'filesRef': 'other', 'section': 'evidencefiles', 'setting': 'root'})
        with self.assertRaisesRegex(ValueError, 'duplicate private'):
            model.validate(self.graph)

    def test_private_roots_reject_public_stage_source_nested_and_alias(self):
        for relative in ('web/policy-web/private', 'artifacts/runtime/policies/private', 'src/hidden', 'tests/private',
                         'tools/private', 'runtime/policies', '../outside'):
            with self.subTest(relative=relative):
                model.environment(self.graph)['evidence']['directory'] = relative
                with self.assertRaises(ValueError):
                    model.validate(self.graph, None)
        model.environment(self.graph)['evidence']['directory'] = 'artifacts/private-evidence/policies'
        self.graph['resources']['other'] = {'kind': 'privateFiles', 'ownerRef': 'application'}
        model.environment(self.graph)['other'] = {'directory': 'artifacts/private-evidence/policies/nested'}
        self.graph['bindings'].append({**self.graph['bindings'][-1], 'filesRef': 'other', 'setting': 'OtherRoot'})
        with self.assertRaisesRegex(ValueError, 'overlap'):
            model.validate(self.graph)

    def test_production_environment_cannot_select_development_private_adapter(self):
        self.graph['environments']['production'] = deepcopy(self.graph['environments']['development'])
        with self.assertRaisesRegex(ValueError, 'Development/Test'):
            model.validate(self.graph)

    def test_retained_root_cannot_be_retargeted_through_symlink(self):
        run.provision_private_files(self.root, self.graph)
        directory = model.private_directories(self.graph, repository=self.root)['evidence']
        directory.rmdir()
        other = self.root / 'artifacts/private-evidence/other'; other.mkdir()
        try:
            directory.symlink_to(other, target_is_directory=True)
        except OSError:
            self.skipTest('Directory symlink creation is unavailable on this test host; CI exercises it')
        self.addCleanup(directory.unlink)
        with self.assertRaisesRegex(ValueError, 'location changed'):
            run.provision_private_files(self.root, self.graph)

    def test_new_posix_permissions_are_nonrecursive_and_preserve_operator_roots(self):
        if run.os.name == 'nt':
            self.skipTest('POSIX ownership initialization; covered by Linux CI')
        run.provision_private_files(self.root, self.graph)
        command = Mock(); command.output.return_value = '1654\n'
        run.prepare_private_permissions(self.root, self.graph, 'host@sha256:fixture', command)
        args = command.run.call_args.args[0]
        self.assertIn('chmod 2770', args[-4]); self.assertNotIn('-R', ' '.join(args))
        command.reset_mock()
        run.prepare_private_permissions(self.root, self.graph, 'host@sha256:fixture', command)
        command.run.assert_not_called(); command.output.assert_not_called()

    def test_compose_mount_is_private_writable_and_does_not_create_missing_root(self):
        contract = {'serviceImages': {'postgresql': 'db', 'keycloak': 'identity'}}
        resolved = {'hostImage': 'host', 'hosts': {'application-host': {'runtimeStage': 'artifacts/runtime/policies',
            'shells': ['application-shell'], 'publicOrigin': 'http://127.0.0.1:5000'}}}
        env = model.environment(self.graph)
        credentials = {env[name]['credentialRef']: 'synthetic' for name in model.resources(self.graph, 'database')}
        credentials[run.variable('server-admin:postgresql')] = 'synthetic'
        credentials[run.variable('identity-admin:product-identity')] = 'synthetic'
        credentials[env['application-client']['credentialRef']] = 'synthetic'
        document, _ = run.compose_model(self.root, self.graph, contract, resolved, credentials)
        host = document['services'][run.service('application-host')]
        private = [mount for mount in host['volumes'] if mount['target'].startswith('/private-evidence/')]
        self.assertEqual(1, len(private)); self.assertFalse(private[0]['read_only'])
        self.assertEqual({'create_host_path': False}, private[0]['bind'])
        self.assertEqual('/private-evidence/evidence', host['environment']['CShells__Shells__policies__Configuration__EvidenceFiles__Root'])
        self.assertFalse(Path(private[0]['source']).exists())

    def test_dependencies_wait_only_selected_closure_preserving_existing_containers(self):
        command = Mock()
        document = {'services': {run.service('one'): {'depends_on': {'db': {}, 'identity': {}}},
            run.service('two'): {'depends_on': {'unrelated': {}}}, 'db': {}, 'identity': {}, 'unrelated': {}}}
        run.ensure_dependencies(command, ['docker', 'compose'], document, ['one'], {})
        arguments = command.run.call_args.args[0]
        self.assertEqual(['db', 'identity'], arguments[-2:])
        self.assertIn('--no-recreate', arguments); self.assertIn('--wait', arguments)
        self.assertNotIn('unrelated', arguments); self.assertNotIn('--force-recreate', arguments)

    def test_unhealthy_prerequisite_failure_propagates_before_host_activation(self):
        command = Mock(); command.run.side_effect = ValueError('unhealthy')
        document = {'services': {run.service('one'): {'depends_on': {'db': {}}}, 'db': {}}}
        with self.assertRaisesRegex(ValueError, 'unhealthy'):
            run.ensure_dependencies(command, ['docker', 'compose'], document, ['one'], {})
        self.assertEqual(1, command.run.call_count)


if __name__ == '__main__':
    unittest.main()

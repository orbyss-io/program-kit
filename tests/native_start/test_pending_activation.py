"""Pending prepared activation remains distinct from changed-source selection."""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import importlib
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import composition_run as run
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
from composition_fixture import two_apps


class PendingActivationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.graph = two_apps(ROOT)
        self.hosts = {'application-host': {'runtimeStage': 'artifacts/app', 'publicOrigin': 'http://fixture-app'},
                      'assessment-host': {'runtimeStage': 'artifacts/assessment', 'publicOrigin': 'http://fixture-assessment'}}
        self.document = {'services': {run.service(name): {} for name in self.hosts}}
        compose = self.root / 'artifacts/composition/docker-compose.json'
        run.write(compose, self.document)
        self.receipt = {'status': 'prepared', 'topologyFingerprint': 'fixture', 'project': 'fixture',
                        'compose': compose.relative_to(self.root).as_posix(), 'composeSha256': run.runtime_closure.sha256(compose),
                        'pendingActivationHosts': list(self.hosts), 'privateFiles': {'retained': 'untouched'}}
        run.write(self.root / run.STATE, self.receipt)
        for name in self.hosts:
            run.write(self.root / 'artifacts/composition/closures' / (name + '.json'), {'sourceInputs': {}})
        self.command = Mock()
        self.build = Mock()
        self.dependencies = Mock()
        self.ready = Mock(return_value=True)
        self.browser = Mock(return_value={'checks': {'fixture': True}})
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        replacements = {'selected': (self.graph, {}, {'hosts': self.hosts}), 'topology_fingerprint': 'fixture',
                        'private_credentials': {}, 'compose_model': (self.document, {})}
        for name, result in replacements.items():
            self.stack.enter_context(patch.object(run, name, return_value=result))
        for name, result in {'Commands': self.command, 'build': self.build, 'ensure_dependencies': self.dependencies,
                             'browser_check': self.browser}.items():
            self.stack.enter_context(patch.object(run, name, result if name != 'Commands' else Mock(return_value=result)))
        self.stack.enter_context(patch.object(run, 'provision_private_files'))
        self.stack.enter_context(patch.object(run.runtime_closure, 'source_inputs', return_value={}))
        self.stack.enter_context(patch.object(run.runtime_closure, 'source_scope', return_value={}))
        self.validate = self.stack.enter_context(patch.object(run.runtime_closure, 'validate'))
        self.stack.enter_context(patch.object(run.qualification, 'ready', self.ready))
        self.stack.enter_context(patch.object(foundation_fixture, 'poll', side_effect=lambda predicate, **_: predicate()))

    def execute(self, selected=None):
        output = io.StringIO()
        with redirect_stdout(output):
            run.run(self.root, selected_hosts=selected, update=True)
        return json.loads(output.getvalue())

    def saved(self):
        return run.read(self.root / run.STATE)

    def test_plain_update_activates_fresh_prepared_bundle_without_rebuilding_it(self):
        def browser(*args, **kwargs):
            self.assertEqual(list(self.hosts), self.saved()['pendingActivationHosts'])
            return {'checks': {'fixture': True}}
        self.browser.side_effect = browser
        result = self.execute()
        self.assertEqual('ready', result['status'])
        self.assertEqual(set(self.hosts), set(result['updatedHosts']))
        self.build.assert_not_called()
        self.assertEqual([], self.saved()['pendingActivationHosts'])
        self.assertEqual(self.receipt['privateFiles'], self.saved()['privateFiles'])
        self.assertEqual(2, self.ready.call_count)
        args = self.command.run.call_args_list[0].args[0]
        self.assertIn('--force-recreate', args)
        self.assertIn('--no-deps', args)

    def test_requested_host_preserves_unrelated_pending_activation(self):
        result = self.execute(['application-host'])
        self.assertEqual(['application-host'], result['updatedHosts'])
        self.assertEqual(['assessment-host'], self.saved()['pendingActivationHosts'])
        self.build.assert_called_once()

    def test_changed_and_pending_hosts_are_unioned_without_duplicate_activation(self):
        self.receipt['pendingActivationHosts'] = ['assessment-host']
        run.write(self.root / run.STATE, self.receipt)
        run.write(self.root / 'artifacts/composition/closures/application-host.json', {'sourceInputs': {'changed': 'old'}})
        result = self.execute()
        self.assertEqual(set(self.hosts), set(result['updatedHosts']))
        self.assertEqual(['application-host'], self.build.call_args.kwargs['selected_hosts'])
        self.assertEqual([], self.saved()['pendingActivationHosts'])

    def test_fresh_active_bundle_reports_unchanged_without_claiming_new_readiness(self):
        self.receipt['pendingActivationHosts'] = []
        run.write(self.root / run.STATE, self.receipt)
        self.assertEqual({'status': 'unchanged', 'updatedHosts': [], 'productAcceptance': False}, self.execute())
        self.command.run.assert_not_called(); self.browser.assert_not_called(); self.build.assert_not_called()

    def test_newly_rebuilt_bundle_remains_pending_after_failed_readiness_then_plain_retry(self):
        self.receipt['pendingActivationHosts'] = []
        run.write(self.root / run.STATE, self.receipt)
        closure = self.root / 'artifacts/composition/closures/application-host.json'
        run.write(closure, {'sourceInputs': {'changed': 'old'}})
        self.build.side_effect = lambda *_, **__: run.write(closure, {'sourceInputs': {}})
        self.browser.side_effect = ValueError('fixture failed readiness after fresh build')
        with self.assertRaisesRegex(ValueError, 'after fresh build'):
            self.execute()
        self.assertEqual(['application-host'], self.saved()['pendingActivationHosts'])
        self.build.assert_called_once()
        self.build.reset_mock(); self.browser.side_effect = None
        self.assertEqual(['application-host'], self.execute()['updatedHosts'])
        self.build.assert_not_called()
        self.assertEqual([], self.saved()['pendingActivationHosts'])

    def test_failed_dependency_activation_http_or_browser_keeps_pending_until_retry(self):
        for boundary in ('dependency', 'activation', 'http', 'browser'):
            with self.subTest(boundary=boundary):
                run.write(self.root / run.STATE, self.receipt)
                self.dependencies.side_effect = ValueError('fixture dependency') if boundary == 'dependency' else None
                self.command.run.side_effect = ValueError('fixture activation') if boundary == 'activation' else None
                self.ready.side_effect = ValueError('fixture http') if boundary == 'http' else None
                self.browser.side_effect = ValueError('fixture browser') if boundary == 'browser' else None
                with self.assertRaisesRegex(ValueError, 'fixture'):
                    self.execute()
                self.assertEqual(list(self.hosts), self.saved()['pendingActivationHosts'])
                for target in (self.dependencies, self.command.run, self.ready, self.browser):
                    target.side_effect = None
                self.assertEqual('ready', self.execute()['status'])
                self.assertEqual([], self.saved()['pendingActivationHosts'])

    def test_stale_prepared_closure_fails_before_activation_and_retains_pending(self):
        self.validate.side_effect = ValueError('fixture stale closure')
        with self.assertRaisesRegex(ValueError, 'stale closure'):
            self.execute()
        self.dependencies.assert_not_called()
        self.assertEqual(list(self.hosts), self.saved()['pendingActivationHosts'])

    def test_foreign_pending_host_is_not_silently_discarded(self):
        self.receipt['pendingActivationHosts'] = ['foreign-host']
        run.write(self.root / run.STATE, self.receipt)
        with self.assertRaisesRegex(ValueError, 'activation identities'):
            self.execute()
        self.command.run.assert_not_called()

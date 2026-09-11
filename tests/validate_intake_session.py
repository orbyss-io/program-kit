"""Bounded offline launcher tests. No installation or coding agent is started."""
from __future__ import annotations

import importlib.util
from contextlib import nullcontext
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('intake_session', ROOT / 'scripts/intake_session.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IntakeSessionTests(unittest.TestCase):
    def setUp(self):
        self.print_patch = patch('builtins.print')
        self.print_patch.start()
        self.addCleanup(self.print_patch.stop)
        self.scratch = tempfile.TemporaryDirectory(prefix='intake-evidence-test-')
        self.record = Path(self.scratch.name) / 'evidence'
        self.record.mkdir()
        self.workspace = Path(tempfile.mkdtemp(prefix='program-kit-intake-')).resolve()
        self.owner = uuid.uuid4().hex
        (self.workspace / '.intake-session-owner').write_text(self.owner)
        self.state = dict(workspace=str(self.workspace), tempParent=str(self.workspace.parent),
                          owner=self.owner, startedAt='2026-01-01T00:00:00+00:00',
                          codexHome=str(Path(self.scratch.name) / 'codex'))
        module.save(self.record / 'session.json', self.state)

    def tearDown(self):
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.scratch.cleanup()

    def history(self, cwd=None):
        sessions = Path(self.state['codexHome']) / 'sessions'
        sessions.mkdir(parents=True, exist_ok=True)
        path = sessions / ('rollout-' + uuid.uuid4().hex + '.jsonl')
        records = [dict(type='session_meta', payload=dict(id='test-session', cwd=str(cwd or self.workspace))),
                   dict(type='response_item', payload=dict(type='message', role='user',
                        content=[dict(type='input_text', text='Build a café portal')]))]
        path.write_text('\n'.join(json.dumps(row) for row in records), encoding='utf-8')
        return path

    def test_normal_exit_archives_transcript_before_cleanup(self):
        (self.workspace / 'product-idea.md').write_text('Product', encoding='utf-8')
        self.history()
        state = module.finish(self.record, 0)
        self.assertFalse(self.workspace.exists())
        self.assertEqual(state['transcriptStatus'], 'captured')
        self.assertEqual(state['intakeStatus'], 'absent')
        self.assertIn('café', (self.record / 'conversation.md').read_text(encoding='utf-8'))
        with zipfile.ZipFile(self.record / 'consumer.zip') as archive:
            self.assertEqual(archive.read('product-idea.md'), b'Product')

    def test_missing_transcript_retains_workspace(self):
        state = module.finish(self.record, 0)
        self.assertEqual(state['cleanup'], 'retained')
        self.assertEqual(state['transcriptStatus'], 'unavailable')
        self.assertTrue(self.workspace.exists())

    def test_validation_distinguishes_draft_confirmed_and_invalid(self):
        path = self.workspace / 'docs/architecture/bootstrap-intake.json'
        path.parent.mkdir(parents=True)
        for status, code, expected, command in (
            ('draft', 0, 'valid-draft', 'validate-draft'),
            ('confirmed', 0, 'valid-confirmed', 'validate'),
            ('confirmed', 2, 'invalid', 'validate'),
        ):
            path.write_text(json.dumps({'status': status}), encoding='utf-8')
            with patch.object(module, 'run', return_value=code) as run:
                state = module.finish(self.record, 0, keep=True, prepare_only=True)
                self.assertEqual(state['intakeStatus'], expected)
                self.assertEqual(run.call_args.args[0][2], command)

    def test_malformed_intake_preserved_as_validation_error(self):
        path = self.workspace / 'docs/architecture/bootstrap-intake.json'
        path.parent.mkdir(parents=True)
        path.write_text('{broken', encoding='utf-8')
        state = module.finish(self.record, 0, keep=True, prepare_only=True)
        self.assertEqual(state['intakeStatus'], 'validation-error')
        self.assertTrue((self.record / 'consumer.zip').exists())

    def test_only_exact_consumer_history_exported(self):
        unrelated = self.history(Path(self.scratch.name))
        self.assertEqual(module.export_conversation(self.state, self.record), [])
        self.assertFalse((self.record / unrelated.name).exists())

    def test_setup_only_cleans_without_agent_history(self):
        with patch.object(module, 'export_conversation', side_effect=AssertionError('must not inspect history')):
            state = module.finish(self.record, 0, prepare_only=True)
        self.assertEqual(state['status'], 'setup-only')
        self.assertFalse(self.workspace.exists())

    def test_failed_cli_preserves_workspace_even_with_transcript(self):
        self.history()
        module.finish(self.record, 130)
        self.assertTrue(self.workspace.exists())

    def test_keep_workspace(self):
        self.history()
        module.finish(self.record, 0, keep=True)
        self.assertTrue(self.workspace.exists())

    def test_archive_failure_never_deletes(self):
        with patch.object(module.zipfile, 'ZipFile', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                module.finish(self.record, 0, prepare_only=True)
        self.assertTrue(self.workspace.exists())

    def test_ownership_and_parent_guards(self):
        for updates in ({'owner': 'wrong'}, {'workspace': str(self.workspace.parent)},
                        {'tempParent': str(self.workspace / 'wrong')}):
            state = dict(self.state, **updates)
            with self.assertRaises((RuntimeError, FileNotFoundError)):
                module.owned_workspace(state)
        self.assertTrue(self.workspace.exists())

    def test_link_guard(self):
        link = self.workspace / 'external'
        try:
            link.symlink_to(self.record, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not permit creating symlinks')
        try:
            with self.assertRaises(RuntimeError):
                module.checked_files(self.workspace)
        finally:
            link.unlink()

    def test_launcher_is_interactive_not_workflow_or_automation(self):
        source = (ROOT / 'scripts/Start-IntakeSession.ps1').read_text(encoding='utf-8')
        for required in ('CODEX_THREAD_ID', 'IsInputRedirected', 'Read-Host', '--no-alt-screen',
                         '--sandbox', 'workspace-write', 'finally', '-CommandType Application'):
            self.assertIn(required, source)
        for forbidden in ('codex exec', 'Start-Process', 'workflow run', 'dangerously-bypass', 'Stop-Process'):
            self.assertNotIn(forbidden, source)
        for workflow in ('ci.yml', 'release.yml'):
            self.assertNotIn('Start-IntakeSession.ps1', (ROOT / '.github/workflows' / workflow).read_text())

    def test_install_uses_bundle_not_preinstalled_extensions(self):
        resolver = SimpleNamespace(uv_windows_specify_environment=lambda _: None)
        with patch.object(module, 'candidate_catalogs', return_value=nullcontext('http://127.0.0.1:1')), \
                patch.dict('sys.modules', {'upgrade_program_kit': resolver}), \
                patch.object(module, 'run', return_value=0) as run:
            module.install_components('specify', 'git', self.workspace, self.record)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(any(command[1:3] == ['bundle', 'install'] for command in commands))
        self.assertFalse(any(command[1:3] == ['extension', 'add'] for command in commands))
        self.assertTrue(any(command[1:3] == ['workflow', 'add'] for command in commands))
        self.assertEqual(commands[-1][1:4], ['preset', 'catalog', 'remove'])

    def test_install_failure_stops_before_later_steps(self):
        resolver = SimpleNamespace(uv_windows_specify_environment=lambda _: None)
        with patch.object(module, 'candidate_catalogs', return_value=nullcontext('http://127.0.0.1:1')), \
                patch.dict('sys.modules', {'upgrade_program_kit': resolver}), \
                patch.object(module, 'run', return_value=1) as run:
            with self.assertRaises(RuntimeError):
                module.install_components('specify', 'git', self.workspace, self.record)
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()

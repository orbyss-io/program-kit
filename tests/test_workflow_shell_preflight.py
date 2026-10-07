"""Regression coverage for real Windows shell lookup and pre-dispatch ordering."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name == 'tests' else HERE.parents[2]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
if not SCRIPTS.is_dir():
    SCRIPTS = ROOT / '.specify/extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
import workflow_shell_preflight as probe
import workflow_lifecycle as candidate


@unittest.skipUnless(os.name == 'nt', 'Windows cmd.exe regression')
class WindowsShellLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = shutil.which('python')
        cls.short_path = str(Path(cls.python).parent) + ';' + str(Path(os.environ['SYSTEMROOT']) / 'System32')
        cls.long_path = cls.short_path + ';' + ('C:/nonexistent/path-padding;' * 400)

    def test_actual_shell_accepts_short_path(self):
        with mock.patch.dict(os.environ, {'PATH': self.short_path}):
            result = probe.verify_shell_launch(ROOT)
        self.assertEqual(result['exitCode'], 0)
        self.assertFalse(result['codingAgentStarted'])

    def test_absolute_python_succeeds_when_cmd_lookup_fails(self):
        with mock.patch.dict(os.environ, {'PATH': self.long_path}):
            direct = subprocess.run([self.python, '--version'], capture_output=True)
            shell = subprocess.run('python --version', shell=True, capture_output=True)
            with self.assertRaisesRegex(probe.ShellPreflightError, '8191'):
                probe.verify_shell_launch(ROOT)
        self.assertEqual(direct.returncode, 0)
        self.assertNotEqual(shell.returncode, 0)

    def test_oversized_path_stops_before_any_probe_process(self):
        runner = mock.Mock(side_effect=AssertionError('must stop before shell execution'))
        with mock.patch.dict(os.environ, {'PATH': self.long_path}):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'not a workspace-write'):
                probe.verify_shell_launch(ROOT, runner=runner)
        runner.assert_not_called()

    def test_runtime_prefix_cannot_push_an_acceptable_inherited_path_over_the_limit(self):
        boundary = self.short_path + ';' + 'x' * (8191 - len(self.short_path) - 1)
        runner = mock.Mock(side_effect=AssertionError('must stop before shell execution'))
        with mock.patch.dict(os.environ, {'PATH': boundary, 'SPECKIT_PYTHON': self.python}):
            probe.check_path(boundary, 'inherited')
            with self.assertRaisesRegex(probe.ShellPreflightError, 'workflow PATH'):
                probe.verify_shell_launch(ROOT, runner=runner)
        runner.assert_not_called()

    def test_unavailable_python_is_reported_before_dispatch(self):
        with mock.patch.dict(os.environ, {'PATH': 'C:/nonexistent/workflow-tools'}):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'python is unavailable'):
                probe.verify_shell_launch(ROOT)

    def test_other_shell_failure_is_not_a_permission_failure(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess('probe', 1, '', 'shell launch failed'))
        with mock.patch.dict(os.environ, {'PATH': self.short_path}):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'through the workflow shell'):
                probe.verify_shell_launch(ROOT, runner=runner)

    def test_different_interpreter_is_rejected(self):
        output = json.dumps({'marker': 'PROGRAMKIT_SHELL_OK', 'python': 'C:/other/python.exe'})
        runner = mock.Mock(return_value=subprocess.CompletedProcess('probe', 0, output, ''))
        with mock.patch.dict(os.environ, {'PATH': self.short_path}):
            with self.assertRaises(probe.ShellPreflightError):
                probe.verify_shell_launch(ROOT, runner=runner)

    def test_failed_resume_stops_before_worker_schema_and_history(self):
        with tempfile.TemporaryDirectory(prefix='program-kit-shell-preflight-test-') as directory:
            temporary_root = Path(directory).resolve()
            self.assertTrue(temporary_root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            state_paths = [temporary_root / '.specify/workflows/runs/source/state.json',
                           temporary_root / '.specify/workflows/runs/child/state.json',
                           temporary_root / '.specify/workflows/resumptions/source.json']
            for path in state_paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"test_fixture": "must remain unchanged"}', encoding='utf-8')
            hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in state_paths}
            inventory = set(temporary_root.rglob('*'))
            for command in ('run', 'resume', 'reopen'):
                with self.subTest(command=command), mock.patch.dict(os.environ, {'PATH': self.long_path}), \
                     mock.patch.object(sys, 'argv', ['workflow_lifecycle.py', command, '--run-id', 'source']), \
                     mock.patch.object(candidate.Path, 'cwd', return_value=temporary_root), \
                     mock.patch('python_runtime.environment', side_effect=AssertionError('dependency probe reached')) as runtime, \
                     mock.patch('codex_worker_policy.worker_environment', side_effect=AssertionError('worker policy reached')) as worker, \
                     mock.patch.object(candidate, 'prepare_schema_runtimes', side_effect=AssertionError('schema setup reached')) as schema, \
                     mock.patch.object(candidate, 'execution_lock', side_effect=AssertionError('execution lock reached')) as lock, \
                     contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(candidate.main(), 1)
                    self.assertIn('WORKFLOW_SHELL_PREFLIGHT', errors.getvalue())
                    worker.assert_not_called()
                    schema.assert_not_called()
                    runtime.assert_not_called()
                    lock.assert_not_called()
            self.assertEqual(hashes, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in state_paths})
            self.assertEqual(inventory, set(temporary_root.rglob('*')))


class ShellContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='program-kit-shell-contract-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.python = shutil.which('python')
        self.assertIsNotNone(self.python)
        self.path = str(Path(self.python).parent)
        if os.name == 'nt':
            self.path += os.pathsep + str(Path(os.environ['SYSTEMROOT']) / 'System32')
        else:
            self.path += os.pathsep + '/usr/bin' + os.pathsep + '/bin'

    def test_probe_uses_the_same_shell_mode_as_the_installed_adapter_and_restores_environment(self):
        from specify_cli.workflows.step.shell import ShellStep
        from specify_cli.workflows.base import StepContext
        import python_runtime
        with mock.patch.dict(os.environ, {'PATH': self.path, 'SPECKIT_PYTHON': self.python}):
            original = dict(os.environ)
            captured = []
            def runner(command, **kwargs):
                captured.append((command, kwargs))
                return subprocess.run(command, **kwargs)
            verified = probe.verify_shell_launch(self.root, runner=runner)
            self.assertEqual(original, dict(os.environ))
            command, kwargs = captured[0]
            self.assertTrue(kwargs['shell'])
            self.assertEqual(self.root, kwargs['cwd'])
            self.assertEqual(python_runtime.invocation_values(self.python)['PATH'], kwargs['env']['PATH'])
            with mock.patch.dict(os.environ, kwargs['env'], clear=True):
                result = ShellStep().execute({'run': command, 'timeout': 30}, StepContext(project_root=str(self.root)))
            self.assertEqual(0, result.output['exit_code'], result.output)
            self.assertEqual(verified['python'], json.loads(result.output['stdout'])['python'])
            self.assertEqual(original, dict(os.environ))

    def test_recorded_interpreter_is_used_when_inherited_python_differs(self):
        record = self.root / '.specify/python-runtime.json'
        record.parent.mkdir()
        record.write_text(json.dumps({'contractVersion': 1, 'executable': sys.executable}))
        with mock.patch.dict(os.environ, {'PATH': self.path, 'SPECKIT_PYTHON': ''}):
            original = dict(os.environ)
            result = probe.verify_shell_launch(self.root)
            self.assertEqual(sys.executable, result['selectedPython'])
            self.assertTrue(Path(result['python']).samefile(sys.executable))
            self.assertEqual(original, dict(os.environ))

    def test_exit_zero_without_the_structured_marker_is_rejected(self):
        for output in ('', 'not json', '{}', json.dumps({'marker': 'wrong', 'python': self.python})):
            runner = mock.Mock(return_value=subprocess.CompletedProcess('probe', 0, output, ''))
            with self.subTest(output=output), mock.patch.dict(os.environ, {'PATH': self.path, 'SPECKIT_PYTHON': self.python}):
                with self.assertRaisesRegex(probe.ShellPreflightError, 'through the workflow shell'):
                    probe.verify_shell_launch(self.root, runner=runner)

    def test_timeout_retains_root_cause_without_dispatch(self):
        runner = mock.Mock(side_effect=subprocess.TimeoutExpired('fixture shell probe', 30))
        with mock.patch.dict(os.environ, {'PATH': self.path, 'SPECKIT_PYTHON': self.python}):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'timed out.*no worker'):
                probe.verify_shell_launch(self.root, runner=runner)


if __name__ == '__main__':
    unittest.main(verbosity=2)

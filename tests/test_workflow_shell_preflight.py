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
import windows_workflow_path as windows_path


@unittest.skipUnless(os.name == 'nt', 'Windows cmd.exe regression')
class WindowsShellLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = shutil.which('python')
        cls.short_path = str(Path(cls.python).parent) + ';' + str(Path(os.environ['SYSTEMROOT']) / 'System32')
        cls.long_path = cls.short_path + ';' + ('C:/nonexistent/path-padding;' * 400)
        cls.directories = tempfile.TemporaryDirectory(prefix='program-kit-large-valid-path-')
        cls.addClassCleanup(cls.directories.cleanup)
        fixture_root = Path(cls.directories.name).resolve()
        assert fixture_root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        paths = []
        for index in range(100):
            directory = fixture_root / (f'tool-{index:03}-' + 'long-directory-name-' * 4)
            directory.mkdir()
            paths.append(str(directory))
        cls.uncompactable_path = cls.short_path + ';' + ';'.join(paths)

    def test_actual_shell_accepts_short_path(self):
        with mock.patch.dict(os.environ, {'PATH': self.short_path}):
            result = probe.verify_shell_launch(ROOT)
        self.assertEqual(result['exitCode'], 0)
        self.assertFalse(result['codingAgentStarted'])

    def test_absolute_python_succeeds_when_cmd_lookup_fails(self):
        with mock.patch.dict(os.environ, {'PATH': self.long_path}):
            direct = subprocess.run([self.python, '--version'], capture_output=True)
            shell = subprocess.run('python --version', shell=True, capture_output=True)
            repaired = probe.verify_shell_launch(ROOT)
        self.assertEqual(direct.returncode, 0)
        self.assertNotEqual(shell.returncode, 0)
        self.assertEqual(repaired['exitCode'], 0)
        self.assertLessEqual(repaired['pathCharacters'], 8191)
        self.assertTrue(repaired['windowsPathPrepared'])

    def test_unrepresentable_usable_path_stops_before_any_probe_process(self):
        runner = mock.Mock(side_effect=AssertionError('must stop before shell execution'))
        with mock.patch.dict(os.environ, {'PATH': self.uncompactable_path}), \
             mock.patch.object(windows_path, 'short_directory', side_effect=lambda directory: directory):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'after automatic PATH preparation'):
                probe.verify_shell_launch(ROOT, runner=runner)
        runner.assert_not_called()

    def test_runtime_prefix_cannot_push_an_acceptable_inherited_path_over_the_limit(self):
        boundary = self.short_path + ';' + 'x' * (8191 - len(self.short_path) - 1)
        with mock.patch.dict(os.environ, {'PATH': boundary, 'SPECKIT_PYTHON': self.python}):
            probe.check_path(boundary, 'inherited')
            result = probe.verify_shell_launch(ROOT)
        self.assertEqual(result['exitCode'], 0)
        self.assertLessEqual(result['pathCharacters'], 8191)

    def test_duplicate_usable_directories_are_removed_without_changing_tool_selection(self):
        import python_runtime
        value = ';'.join([self.short_path] * 200)
        with mock.patch.dict(os.environ, {'PATH': value, 'SPECKIT_PYTHON': self.python}):
            original = dict(os.environ)
            result = probe.verify_shell_launch(ROOT)
            with python_runtime.environment(ROOT) as resolved_python:
                self.assertLessEqual(len(os.environ['PATH']), 8191)
                self.assertTrue(Path(shutil.which('python')).samefile(resolved_python))
            self.assertEqual(original, dict(os.environ))
        self.assertEqual(result['exitCode'], 0)

    def test_npm_style_codex_launcher_retains_its_node_fallback_without_starting_an_agent(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Pinned Node is required for the Windows launcher fixture')
        with tempfile.TemporaryDirectory(prefix='program-kit-npm-launcher-') as directory:
            tools = Path(directory) / 'tools with spaces'
            tools.mkdir()
            (tools / 'codex.cmd').write_text('@echo off\nnode -e "console.log(\'NODE_PATH_OK\')"\n')
            inherited = str(tools) + ';' + self.long_path + ';' + str(Path(node).parent)
            with mock.patch.dict(os.environ, {'PATH': inherited, 'SPECKIT_PYTHON': self.python}):
                result = probe.verify_shell_launch(ROOT)
                import python_runtime
                values = python_runtime.invocation_values(self.python)
                self.assertTrue(Path(shutil.which('node', path=values['PATH'])).samefile(node))
                launched = subprocess.run('codex', shell=True, env=values, capture_output=True, text=True)
            self.assertEqual(launched.returncode, 0, launched.stderr)
            self.assertEqual(launched.stdout.strip(), 'NODE_PATH_OK')
            self.assertFalse(result['codingAgentStarted'])

    def test_unreadable_tool_directory_is_retained_and_short_names_preserve_identity(self):
        with tempfile.TemporaryDirectory(prefix='program-kit-tool-identity-') as directory:
            original_stat = os.stat
            def denied(path, **kwargs):
                if os.path.normcase(os.path.abspath(path)) == os.path.normcase(directory):
                    raise PermissionError('fixture access denied')
                return original_stat(path, **kwargs)
            with mock.patch.object(windows_path.os, 'stat', side_effect=denied):
                prepared = windows_path.prepare_path(self.short_path + ';' + directory, self.python)
            self.assertIn(directory, prepared.split(';'))
            self.assertTrue(Path(windows_path.short_directory(directory)).samefile(directory))

    def test_app_alias_is_resolved_only_without_a_record_and_probe_failures_remain_errors(self):
        import python_runtime
        with tempfile.TemporaryDirectory(prefix='program-kit-runtime-alias-') as directory:
            root = Path(directory)
            with mock.patch.dict(os.environ, {'SPECKIT_PYTHON': self.python}), \
                 mock.patch.object(windows_path, 'canonical_python', return_value=sys.executable) as canonical:
                self.assertEqual(sys.executable, python_runtime.selected(root))
                canonical.assert_called_once_with(self.python)
                record = root / '.specify/python-runtime.json'
                record.parent.mkdir()
                record.write_text(json.dumps({'contractVersion': 1, 'executable': self.python}))
                canonical.reset_mock()
                self.assertEqual(self.python, python_runtime.selected(root))
                canonical.assert_not_called()
            with mock.patch.object(windows_path.sys, 'executable', 'C:/other/python.exe'), \
                 mock.patch.object(windows_path.subprocess, 'run', side_effect=subprocess.TimeoutExpired('Python identity', 30)):
                with self.assertRaisesRegex(windows_path.WindowsPathError, 'timed out.*no worker'):
                    windows_path.canonical_python(self.python)

    def test_unavailable_python_is_reported_before_dispatch(self):
        with mock.patch.dict(os.environ, {'PATH': 'C:/nonexistent/workflow-tools'}):
            with self.assertRaisesRegex(probe.ShellPreflightError, 'PKT030.*python.*detected=missing'):
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
                with self.subTest(command=command), mock.patch.dict(os.environ, {'PATH': self.uncompactable_path}), \
                     mock.patch.object(windows_path, 'short_directory', side_effect=lambda directory: directory), \
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

    def test_repaired_path_reaches_worker_policy_and_is_restored_on_failure(self):
        with tempfile.TemporaryDirectory(prefix='program-kit-prepared-dispatch-') as directory:
            root = Path(directory)
            def stop_at_worker(*args):
                self.assertLessEqual(len(os.environ['PATH']), 8191)
                self.assertEqual('fixture-originator', os.environ['CODEX_SESSION_ID'])
                raise ValueError('fixture stop before worker dispatch')
            with mock.patch.dict(os.environ, {'PATH': self.long_path, 'SPECKIT_PYTHON': self.python,
                                              'CODEX_SESSION_ID': 'fixture-originator'}), \
                 mock.patch.object(sys, 'argv', ['workflow_lifecycle.py', 'run']), \
                 mock.patch.object(candidate.Path, 'cwd', return_value=root), \
                 mock.patch.object(candidate, 'execution_lock', return_value=contextlib.nullcontext()), \
                 mock.patch('codex_worker_policy.worker_environment', side_effect=stop_at_worker) as worker, \
                 mock.patch.object(candidate, 'WorkflowEngine') as engine, \
                 contextlib.redirect_stderr(io.StringIO()) as errors:
                original = dict(os.environ)
                self.assertEqual(candidate.main(), 1)
                self.assertIn('fixture stop before worker dispatch', errors.getvalue())
                worker.assert_called_once()
                engine.assert_not_called()
                self.assertEqual(original, dict(os.environ))
            self.assertEqual([], list(root.iterdir()))


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
            self.assertEqual(python_runtime.invocation_values(verified['selectedPython'])['PATH'], kwargs['env']['PATH'])
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

    def test_source_launcher_scopes_old_runtime_without_changing_installation_or_gates(self):
        scripts = self.root / '.specify/extensions/program-kit-governance/scripts'
        scripts.mkdir(parents=True)
        # Released selection API, deliberately without the new PATH module.
        # The downloaded launcher must work under its documented new filename.
        (scripts / 'python_runtime.py').write_text(
            'import os,json,shutil\nfrom pathlib import Path\n'
            'def selected(root):\n'
            '    record=root/".specify/python-runtime.json"\n'
            '    saved=json.loads(record.read_text()) if record.is_file() else {}\n'
            '    return os.environ.get("SPECKIT_PYTHON") or saved.get("executable") or shutil.which("python")\n')
        child = scripts / 'workflow_lifecycle.py'
        # Simulate an old lifecycle's repeated runtime prefix and native shell.
        # No Spec Kit engine, coding-agent CLI or workflow worker is invoked.
        child.write_text('import json,os,sys,subprocess\nfrom pathlib import Path\n'
                         'values=dict(os.environ)\n'
                         'values["PATH"]=str(Path(values["SPECKIT_PYTHON"]).parent)+os.pathsep+values["PATH"]\n'
                         'result=subprocess.run("python --version",shell=True,env=values,capture_output=True)\n'
                         'print(json.dumps({"shellExit":result.returncode,"args":sys.argv[1:],'
                         '"originator":values.get("CODEX_SESSION_ID"),"pathLength":len(values["PATH"])}))\n'
                         'raise SystemExit(int(os.environ.get("PROGRAM_KIT_TEST_EXIT","0")))\n')
        before = {p: p.read_bytes() for p in scripts.iterdir()}
        environment = dict(os.environ, PATH=self.path + os.pathsep + 'missing-padding' * 1000,
                           SPECKIT_PYTHON=sys.executable, CODEX_SESSION_ID='fixture-originator')
        args = ['run', '--input', 'bootstrap_intake=docs/architecture/plan with spaces.json',
                '--input', 'integration=auto']
        launcher = self.root / 'Start-ProgramKitWorkflow.py'
        shutil.copyfile(SCRIPTS / 'windows_workflow_path.py', launcher)
        for code in (0, 37):
            environment['PROGRAM_KIT_TEST_EXIT'] = str(code)
            result = subprocess.run([sys.executable, str(launcher), *args], cwd=self.root,
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(code, result.returncode, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(0, value['shellExit'])
            self.assertEqual(args, value['args'])
            self.assertEqual('fixture-originator', value['originator'])
            if os.name == 'nt':
                self.assertLessEqual(value['pathLength'], 8191)
        self.assertEqual(before, {p: p.read_bytes() for p in scripts.iterdir() if p.is_file()})

    def test_current_release_bootstrap_instructions_supply_the_source_launcher(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        if 'Latest available release: **[v0.12.9]' in readme:
            self.assertIn('da44715c563db7eb4d2ffe471ac3120729713c9c/extensions/program-kit-governance/scripts/windows_workflow_path.py', readme)
            self.assertIn('python .\\Start-ProgramKitWorkflow.py run', readme)
            self.assertIn('normal user-owned', readme)


if __name__ == '__main__':
    unittest.main(verbosity=2)

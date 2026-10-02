"""Deterministic interpreter, generated instruction, and worker regressions; no agents."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import python_runtime as runtime
import codex_bootstrap_preflight as preflight


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_separate_python3_is_never_selected_and_unavailable_python3_is_irrelevant(self):
        for python3 in ('different-python-without-yaml', None):
            def which(name):
                return sys.executable if name == 'python' else python3
            with self.subTest(python3=python3), patch.dict(os.environ, {}, clear=True), \
                    patch.object(runtime.shutil, 'which', side_effect=which) as lookup, \
                    patch.object(runtime.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, sys.executable + '\n', '')) as run:
                self.assertEqual(os.path.abspath(sys.executable), runtime.resolve(self.root))
                lookup.assert_called_once_with('python')
                self.assertEqual(sys.executable, run.call_args.args[0][0])

    def test_missing_dependency_and_unsupported_version_fail_before_dispatch(self):
        for diagnostic in ("ModuleNotFoundError: No module named 'yaml'", 'Python >=3.11 is required'):
            with patch.dict(os.environ, {'SPECKIT_PYTHON': sys.executable}, clear=True), \
                    patch.object(runtime.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', diagnostic)):
                with self.assertRaisesRegex(ValueError, 'before agent dispatch') as error:
                    runtime.resolve(self.root)
                self.assertIn(diagnostic, str(error.exception))

    def test_actual_selected_environment_without_yaml_is_rejected_without_fallback(self):
        environment = self.root / 'no-yaml'
        venv.EnvBuilder(with_pip=False).create(environment)
        executable = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        with patch.dict(os.environ, {'SPECKIT_PYTHON': str(executable)}, clear=True):
            with self.assertRaisesRegex(ValueError, "No module named 'yaml'"):
                runtime.resolve(self.root)

    def test_legacy_generated_instruction_blocks_even_when_selected_python_is_healthy(self):
        resolver = self.root / preflight.PYTHON_RESOLVER
        resolver.parent.mkdir(parents=True)
        resolver.write_text('print("TEMPLATE_CONTENT")')
        skill = self.root / preflight.CONSTITUTION_SKILL
        skill.parent.mkdir(parents=True)
        skill.write_text('python3 ' + preflight.PYTHON_RESOLVER.as_posix())
        with patch.object(runtime, 'resolve', return_value=sys.executable):
            with self.assertRaisesRegex(RuntimeError, 'Generated core constitution'):
                preflight.verify_windows_resolver(self.root, 'py', resolver)

    def test_resolver_is_probed_on_posix_too_and_preserves_root_cause(self):
        with patch.object(preflight, 'verify_git_worktree'), \
                patch.object(preflight, 'inspect_script_runtime', return_value=('py', self.root / 'resolver.py')), \
                patch.object(preflight, 'verify_windows_resolver', side_effect=RuntimeError('PyYAML is required for composition')) as probe:
            result = preflight.evaluate_preflight('codex', self.root, environ={}, platform_name='posix')
        probe.assert_called_once()
        self.assertEqual('script-runtime-blocked', result['action'])
        self.assertIn('PyYAML is required for composition', result['diagnostic'])

    def test_environment_restores_path_and_selection_after_failure(self):
        with patch.dict(os.environ, {'PATH': 'original'}, clear=True), \
                patch.object(runtime, 'resolve', return_value=sys.executable), \
                patch.object(runtime.shutil, 'which', return_value=sys.executable):
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                with runtime.environment(self.root):
                    self.assertEqual(sys.executable, os.environ['SPECKIT_PYTHON'])
                    raise RuntimeError('fixture')
            self.assertEqual('original', os.environ['PATH'])
            self.assertNotIn('SPECKIT_PYTHON', os.environ)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.base import StepContext
        self.step = CommandStep()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context = StepContext(project_root=str(self.root))

    def execute(self, worker, **config):
        result = {'exit_code': 0, 'stdout': 'original diagnostic stream', 'stderr': '', 'worker_result': worker}
        with patch.object(type(self.step), '_try_dispatch', return_value=result):
            return self.step.execute({'id': 'constitution-draft', 'command': 'constitution', **config}, self.context)

    def test_zero_exit_blocked_worker_remains_failed_with_diagnostic(self):
        worker = {'status': 'blocked', 'diagnostic': 'PyYAML is required to resolve preset template composition.'}
        result = self.execute(worker)
        self.assertEqual('failed', result.status.value)
        self.assertTrue(result.output['process_succeeded'])
        self.assertEqual(worker, result.output['worker_result'])
        self.assertEqual(worker['diagnostic'], result.error)
        self.assertEqual('original diagnostic stream', result.output['stdout'])

    def test_completed_worker_without_artifact_is_failed(self):
        result = self.execute({'status': 'completed', 'diagnostic': ''}, required_artifacts=['constitution.md'])
        self.assertEqual('failed', result.status.value)
        self.assertIn('did not produce', result.error)

    def test_unchanged_template_is_rejected_by_authoritative_validator(self):
        (self.root / 'constitution.md').write_text('[PROJECT NAME] template')
        from specify_cli.workflows import worker_result
        with patch.object(worker_result.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, '', 'unchanged constitution template')), \
                patch('specify_cli.python_runtime.resolve_python_interpreter', return_value=sys.executable):
            result = self.execute({'status': 'completed', 'diagnostic': ''}, required_artifacts=['constitution.md'], artifact_validator=['validator.py'])
        self.assertEqual('failed', result.status.value)
        self.assertIn('unchanged constitution template', result.error)

    def test_valid_artifact_retains_hash_and_process_outcome(self):
        (self.root / 'constitution.md').write_text('Draft')
        result = self.execute({'status': 'completed', 'diagnostic': ''}, required_artifacts=['constitution.md'])
        self.assertEqual('completed', result.status.value)
        self.assertEqual(64, len(result.output['artifacts'][0]['sha256']))

    def test_real_codex_adapter_preserves_structured_result_without_starting_codex(self):
        from specify_cli.integrations import get_integration
        def runner(argv, **kwargs):
            Path(argv[argv.index('--output-last-message') + 1]).write_text(json.dumps({'status': 'blocked', 'diagnostic': 'missing yaml'}))
            self.assertIn('--output-schema', argv)
            return subprocess.CompletedProcess(argv, 0, 'evidence', '')
        with patch('specify_cli.integrations.codex.subprocess.run', side_effect=runner):
            result = get_integration('codex').dispatch_command('constitution', project_root=self.root)
        self.assertEqual('missing yaml', result['worker_result']['diagnostic'])
        self.assertEqual('evidence', result['stdout'])

    def test_missing_structured_result_and_nonzero_process_are_failures(self):
        from specify_cli.integrations import get_integration
        for code in (0, 1):
            with patch('specify_cli.integrations.codex.subprocess.run', return_value=subprocess.CompletedProcess([], code, 'original worker evidence', '')):
                dispatch = get_integration('codex').dispatch_command('constitution', project_root=self.root)
            self.assertEqual('failed', dispatch['worker_result']['status'])
            with patch.object(type(self.step), '_try_dispatch', return_value=dispatch):
                result = self.step.execute({'id': 'draft', 'command': 'constitution'}, self.context)
            self.assertEqual('failed', result.status.value)
            self.assertEqual('original worker evidence', result.output['stdout'])


class GeneratedConsumerTests(unittest.TestCase):
    def test_generated_core_constitution_and_extension_commands_bind_validated_python(self):
        from specify_cli.integrations.base import IntegrationBase
        with tempfile.TemporaryDirectory(prefix='program-kit-generated-runtime-') as directory:
            root = Path(directory)
            poison = root / 'different-environment'
            poison.mkdir()
            (poison / ('python3.cmd' if os.name == 'nt' else 'python3')).write_text('exit 99\n')
            env = dict(os.environ, PATH=str(poison) + os.pathsep + os.environ['PATH'])
            env.pop('SPECKIT_PYTHON', None)
            result = subprocess.run([sys.executable, '-c', 'from specify_cli import main; main()',
                'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                '--script', 'py', '--ignore-agent-tools'], cwd=root, env=env,
                capture_output=True, encoding='utf-8', errors='replace', timeout=90)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            text = (root / preflight.CONSTITUTION_SKILL).read_text(encoding='utf-8')
            selected = json.loads((root / '.specify/python-runtime.json').read_text())['executable']
            self.assertIn(selected.replace('\\', '/'), text.replace('\\', '/'))
            self.assertNotIn('python3 ', text)
            preflight.verify_windows_resolver(root, 'py', root / preflight.PYTHON_RESOLVER)
            extension = IntegrationBase.bind_python_commands('python .specify/extensions/test/validate.py', root)
            self.assertIn(selected, extension)


if __name__ == '__main__':
    from spec_kit_source_fixture import run_patched
    code = run_patched(__file__)
    if code is not None:
        raise SystemExit(code)
    unittest.main()

"""Public Spec Kit compatibility and Program Kit native runtime checks; no workers."""
import json
import os
from pathlib import Path
import re
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


def selected_cli_pin(root=ROOT):
    pins = set(re.findall(r'specify-cli==([0-9.]+)',
                         (root / '.github/workflows/ci.yml').read_text(encoding='utf-8')))
    if len(pins) != 1:
        raise ValueError('CI must select one exact public Spec Kit version')
    return pins.pop()


class PublicCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_native_runtime_uses_selected_python_with_different_or_absent_python3(self):
        for python3 in ('different-python-without-yaml', None):
            def which(name):
                return sys.executable if name == 'python' else python3
            with self.subTest(python3=python3), patch.dict(os.environ, {}, clear=True), \
                    patch.object(runtime.shutil, 'which', side_effect=which) as lookup, \
                    patch.object(runtime.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, sys.executable + '\n', '')):
                self.assertEqual(os.path.abspath(sys.executable), runtime.resolve(self.root))
                lookup.assert_called_once_with('python')

    def test_active_manifests_and_ci_share_the_public_cli_baseline(self):
        import yaml
        from packaging.specifiers import SpecifierSet
        manifests = [ROOT/'bundle.yml', *ROOT.glob('extensions/*/extension.yml'),
                     *ROOT.glob('presets/*/preset.yml'), *ROOT.glob('workflows/*/workflow.yml')]
        selected = selected_cli_pin()
        self.assertIn(selected, SpecifierSet('>=1.1.1,<2.0.0'))
        for path in manifests:
            with self.subTest(path=path):
                supported = SpecifierSet(yaml.safe_load(path.read_text(encoding='utf-8'))['requires']['speckit_version'])
                self.assertIn('1.1.1', supported)
                self.assertIn(selected, supported)
                self.assertNotIn('1.0.1', supported)
                self.assertNotIn('2.0.0', supported)
        for name in ('ci.yml','release.yml'):
            text = (ROOT/'.github/workflows'/name).read_text(encoding='utf-8')
            pins = re.findall(r'specify-cli==([0-9.]+)', text)
            self.assertTrue(pins, 'Missing exact public CLI pin: ' + name)
            self.assertEqual({selected}, set(pins))

    def test_disagreeing_ci_pins_are_rejected(self):
        path = self.root / '.github/workflows/ci.yml'
        path.parent.mkdir(parents=True)
        path.write_text('specify-cli==1.1.1\nspecify-cli==1.1.2\n')
        with self.assertRaisesRegex(ValueError, 'one exact'):
            selected_cli_pin(self.root)

    def test_missing_native_dependency_and_unsupported_version_preserve_diagnostic(self):
        for diagnostic in ("ModuleNotFoundError: No module named 'yaml'", 'Python >=3.11 is required'):
            with patch.dict(os.environ, {'SPECKIT_PYTHON': sys.executable}, clear=True), \
                    patch.object(runtime.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', diagnostic)):
                with self.assertRaisesRegex(ValueError, 'before agent dispatch') as error:
                    runtime.resolve(self.root)
                self.assertIn(diagnostic, str(error.exception))

    def test_real_native_environment_without_yaml_is_rejected(self):
        environment = self.root / 'no-yaml'
        venv.EnvBuilder(with_pip=False).create(environment)
        executable = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        with patch.dict(os.environ, {'SPECKIT_PYTHON': str(executable)}, clear=True):
            with self.assertRaisesRegex(ValueError, "No module named 'yaml'"):
                runtime.resolve(self.root)

    def test_upstream_python3_skill_is_not_rejected_for_missing_private_core_contract(self):
        resolver = self.root / preflight.PYTHON_RESOLVER
        resolver.parent.mkdir(parents=True)
        resolver.write_text('print("TEMPLATE_CONTENT")')
        skill = self.root / preflight.CONSTITUTION_SKILL
        skill.parent.mkdir(parents=True)
        original = 'python3 ' + preflight.PYTHON_RESOLVER.as_posix()
        skill.write_text(original)
        def runner(argv, **kwargs):
            self.assertEqual(sys.executable, argv[0])
            return subprocess.CompletedProcess(argv, 0, json.dumps({'TEMPLATE_CONTENT': 'Constitution template'}), '')
        with patch.object(runtime, 'resolve', return_value=sys.executable):
            preflight.verify_windows_resolver(self.root, 'py', resolver, runner=runner)
        self.assertEqual(original, skill.read_text())

    def test_actual_public_package_generates_an_accepted_unmodified_consumer(self):
        import importlib.metadata
        self.assertEqual(selected_cli_pin(), importlib.metadata.version('specify-cli'))
        environment = dict(os.environ, SPECKIT_PYTHON=sys.executable)
        result = subprocess.run([sys.executable, '-c', 'from specify_cli import main; main()',
            'init', '.', '--force', '--non-interactive', '--integration', 'codex',
            '--script', 'py', '--ignore-agent-tools'], cwd=self.root, env=environment,
            capture_output=True, encoding='utf-8', errors='replace', timeout=90)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        skill = self.root / preflight.CONSTITUTION_SKILL
        original = skill.read_bytes()
        # Public core selects python when python3 is absent from the invocation
        # PATH. Both upstream choices must remain accepted and unmodified.
        self.assertRegex(original, rb'\bpython(?:3)? \.specify/scripts/python/resolve_template\.py constitution-template --json')
        with patch.dict(os.environ, {'SPECKIT_PYTHON': sys.executable}):
            flavor, resolver = preflight.inspect_script_runtime(self.root, 'codex')
            self.assertEqual('py', flavor)
            preflight.verify_windows_resolver(self.root, flavor, resolver)
        self.assertEqual(original, skill.read_bytes())

    def test_resolver_probe_failure_preserves_root_cause(self):
        with patch.object(preflight, 'verify_git_worktree'), \
                patch.object(preflight, 'inspect_script_runtime', return_value=('py', self.root / 'resolver.py')), \
                patch.object(preflight, 'verify_windows_resolver', side_effect=RuntimeError('PyYAML is required for composition')) as probe:
            result = preflight.evaluate_preflight('codex', self.root, environ={}, platform_name='posix')
        probe.assert_called_once()
        self.assertEqual('script-runtime-blocked', result['action'])
        self.assertIn('PyYAML is required for composition', result['diagnostic'])

    def test_native_environment_restores_caller_after_failure(self):
        with patch.dict(os.environ, {'PATH': 'original'}, clear=True), \
                patch.object(runtime, 'resolve', return_value=sys.executable), \
                patch.object(runtime.shutil, 'which', return_value=sys.executable):
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                with runtime.environment(self.root):
                    self.assertEqual(sys.executable, os.environ['SPECKIT_PYTHON'])
                    raise RuntimeError('fixture')
            self.assertEqual('original', os.environ['PATH'])
            self.assertNotIn('SPECKIT_PYTHON', os.environ)


    def test_zero_exit_worker_without_output_fails_the_native_artifact_gate(self):
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.step.command import CommandStep
        from specify_cli.workflows.base import RunStatus
        script = ROOT / 'extensions/program-kit-governance/scripts/bootstrap_context.py'
        definition = WorkflowDefinition({'schema_version': '1.0',
            'workflow': {'id': 'program-kit-bootstrap', 'name': 'Public core artifact regression'},
            'steps': [
                {'id': 'architecture-dispatch', 'type': 'command',
                 'command': 'speckit.program-kit-governance.architecture', 'integration': 'codex'},
                {'id': 'validate-architecture-output', 'type': 'shell',
                 'run': f'"{sys.executable}" "{script}" validate-output --stage architecture --json'}]})
        with patch.object(CommandStep, '_try_dispatch', return_value={
                'exit_code': 0, 'stdout': 'worker turn ended', 'stderr': ''}):
            state = WorkflowEngine(self.root).execute(definition, run_id='public-core-missing-output')
        self.assertEqual(RunStatus.FAILED, state.status)
        self.assertEqual('validate-architecture-output', state.current_step_id)
        self.assertEqual(0, state.step_results['architecture-dispatch']['output']['exit_code'])
        diagnostic = str(state.step_results[state.current_step_id])
        self.assertIn('Required architecture output is missing', diagnostic)
        self.assertIn('PROGRAM_KIT_WORKER_ARTIFACT_CONTRACT', diagnostic)


if __name__ == '__main__':
    unittest.main()

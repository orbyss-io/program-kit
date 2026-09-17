"""Workflow entry runtime preflight; no coding-agent sessions."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import json
import shutil
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
import workflow_lifecycle as workflow


class WorkflowRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pk-runtime-boundary-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = str(self.root / 'engine/python.exe')
        self.shell = str(self.root / 'shell/python.exe')

    def test_both_interpreters_are_provisioned_then_isolated_validated(self):
        with patch.object(sys, 'executable', self.engine), patch.object(workflow.shutil, 'which', return_value=self.shell), \
                patch.object(workflow.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            workflow.prepare_schema_runtimes(self.root)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual([os.path.normcase(p) for p in [self.engine, self.engine, self.shell, self.shell]],
                         [c[0] for c in commands])
        self.assertEqual(['setup', '--project-root', str(self.root)], commands[0][2:])
        self.assertEqual(['-I', '-c'], commands[1][1:3])
        self.assertIn('validate_value', commands[1][3])
        self.assertEqual(commands[0][1:], commands[2][1:])

    def test_same_interpreter_is_not_provisioned_twice(self):
        with patch.object(workflow.shutil, 'which', return_value=sys.executable), \
                patch.object(workflow.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            workflow.prepare_schema_runtimes(self.root)
        self.assertEqual(2, run.call_count)

    def test_failed_setup_or_import_stops_at_boundary(self):
        for failure_index in range(4):
            results = [subprocess.CompletedProcess([], 0, '', '')] * failure_index
            results.append(subprocess.CompletedProcess([], 1, '', 'broken dependency'))
            with self.subTest(command=failure_index), patch.object(sys, 'executable', self.engine), \
                    patch.object(workflow.shutil, 'which', return_value=self.shell), \
                    patch.object(workflow.subprocess, 'run', side_effect=results) as run:
                with self.assertRaisesRegex(workflow.WorkflowLifecycleError, 'before agent dispatch.*broken dependency'):
                    workflow.prepare_schema_runtimes(self.root)
                self.assertEqual(failure_index + 1, run.call_count)

    def test_timeout_and_missing_shell_are_clear_preflight_errors(self):
        with patch.object(workflow.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(workflow.WorkflowLifecycleError, 'python is unavailable'):
                workflow.prepare_schema_runtimes(self.root)
        with patch.object(workflow.shutil, 'which', return_value=sys.executable), \
                patch.object(workflow.subprocess, 'run', side_effect=subprocess.TimeoutExpired('setup', 360)):
            with self.assertRaisesRegex(workflow.WorkflowLifecycleError, 'WORKFLOW_RUNTIME_PREFLIGHT'):
                workflow.prepare_schema_runtimes(self.root)

    def test_entry_commands_fail_before_engine_or_artifact_mutation(self):
        for command in ('run', 'resume', 'reopen'):
            with self.subTest(command=command), patch.object(sys, 'argv', ['workflow_lifecycle.py', command]), \
                    patch.object(Path, 'cwd', return_value=self.root), \
                    patch.object(workflow, 'prepare_schema_runtimes', side_effect=workflow.WorkflowLifecycleError('WORKFLOW_RUNTIME_PREFLIGHT')), \
                    patch.object(workflow, 'WorkflowEngine') as engine, \
                    patch.object(workflow.governance, 'configure_paths') as configure, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(1, workflow.main())
                engine.assert_not_called()
                configure.assert_not_called()


def mixed_python_trial(shell_python):
    """Explicit real two-version terminal regression, with unmodified shell steps."""
    import yaml
    import validate_workflow_resumption as fixture
    import schema_runtime
    shell_python = Path(shell_python).absolute()
    shell_tag = subprocess.check_output([str(shell_python), '-c',
        'import sys; print(sys.implementation.cache_tag)'], text=True).strip()
    if shell_tag == sys.implementation.cache_tag:
        raise AssertionError('Mixed regression requires different Python versions')
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='pk-real-mixed-python-') as temporary:
        root = Path(temporary)
        os.chdir(root)
        try:
            fixture.setup(root)
            engine_cache = schema_runtime.runtime_path(root)
            engine_cache.rename(root / 'preserved-engine-runtime')
            scripts = root / '.specify/extensions/program-kit-governance/scripts'
            subprocess.run([str(shell_python), str(scripts / 'schema_runtime.py'), 'setup'], check=True)
            assert not engine_cache.exists(), 'Engine cache must be absent at reproduction start'
            shipped = yaml.safe_load((fixture.fixture.ROOT / 'workflows/program-kit-bootstrap/workflow.yml').read_text(encoding='utf-8'))
            definition = {'workflow': shipped['workflow'], 'steps': [s for s in shipped['steps']
                if s['id'] in {'readiness', 'require-readiness', 'complete-bootstrap'}]}
            definition['workflow']['version'] = '0.3.1'  # Synthetic fixture installation version.
            (root / 'terminal-test.yml').write_text(yaml.safe_dump(definition), encoding='utf-8')
            installed = root / '.specify/workflows/program-kit-bootstrap/workflow.yml'
            installed.parent.mkdir(parents=True, exist_ok=True)
            installed.write_text(yaml.safe_dump(definition), encoding='utf-8')
            runner = root / 'terminal-test.py'
            runner.write_text('''import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / '.specify/extensions/program-kit-governance/scripts'))
import workflow_lifecycle as workflow
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine, RunState
from specify_cli.workflows.steps.command import CommandStep
def forbidden(*args, **kwargs):
    raise AssertionError('This test must never start a coding agent')
CommandStep._try_dispatch = forbidden
root = Path.cwd()
mode = sys.argv[1]
if mode in {'fixed', 'resume'}:
    sys.argv = ['workflow_lifecycle.py', 'run' if mode == 'fixed' else 'resume', '--run-id', 'fixed']
    assert workflow.main() == 0
    state = RunState.load('fixed', root)
else:
    state = WorkflowEngine(root).execute(WorkflowDefinition.from_yaml(root / 'terminal-test.yml'), run_id=mode)
if state.status.value == 'completed':
    workflow.governance.configure_paths()
    workflow.governance.validate_completion()
    workflow.validate_engine_completion(root)
print(json.dumps({'status': state.status.value, 'step': state.current_step_id,
                  'output': state.step_results[state.current_step_id].get('output')}))
''', encoding='utf-8')
            # Use a bounded test PATH: accumulated historical fixture paths on a
            # developer host can exceed cmd.exe's environment-variable limit.
            directories = [str(shell_python.parent)]
            for tool in ('specify', 'uv', 'git'):
                executable = shutil.which(tool)
                if executable:
                    directories.append(str(Path(executable).parent))
            if os.name == 'nt':
                directories.append(str(Path(os.environ['SystemRoot']) / 'System32'))
            else:
                directories.extend(['/usr/bin', '/bin'])
            env = dict(os.environ, PATH=os.pathsep.join(dict.fromkeys(directories)), PYTHONUTF8='1')
            assert Path(shutil.which('python', path=env['PATH'])).samefile(shell_python)
            for mode in ('before', 'fixed', 'resume'):
                if mode == 'resume':
                    # Re-entry provisions the engine cache again without
                    # rerunning work or rewriting accepted authority.
                    engine_cache.rename(root / 'preserved-fixed-runtime')
                    completion = (root / fixture.g.BOOTSTRAP_COMPLETION).read_bytes()
                result = subprocess.run([sys.executable, str(runner), mode], env=env, cwd=root,
                                        capture_output=True, encoding='utf-8', timeout=600)
                if result.returncode:
                    raise AssertionError(result.stdout + result.stderr)
                value = json.loads(result.stdout.strip().splitlines()[-1])
                if mode == 'before':
                    assert value['status'] == 'failed' and value['step'] == 'complete-bootstrap', value
                    assert 'SCHEMA_RUNTIME_MISSING' in value['output']['stderr'], value
                else:
                    assert value['status'] == 'completed', value
                    if mode == 'resume':
                        assert completion == (root / fixture.g.BOOTSTRAP_COMPLETION).read_bytes()
                print(json.dumps({'mode': mode, 'engine': sys.implementation.cache_tag,
                                  'shell': shell_tag, 'status': value['status'], 'step': value['step']}))
            assert engine_cache.is_dir()
        finally:
            os.chdir(previous)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--mixed-python':
        mixed_python_trial(sys.argv[2])
    else:
        unittest.main()

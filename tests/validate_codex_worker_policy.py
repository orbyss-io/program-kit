"""Deterministic worker-permission regressions; no coding agents or paid calls."""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import contextlib
import io
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import codex_worker_policy as policy
import codex_bootstrap_preflight as preflight


def expect_block(operation, phrase='PROGRAM_KIT_CODEX_WORKSPACE_WRITE'):
    try:
        operation()
    except policy.WorkerPolicyError as error:
        assert phrase in str(error), str(error)
    else:
        raise AssertionError('Unsafe or unsupported worker policy was accepted')


def main():
    for args in ('--sandbox read-only', '--sandbox danger-full-access', '-sdanger-full-access',
                 '--dangerously-bypass-approvals-and-sandbox', '--add-dir C:/', '--worktree',
                 '-c sandbox_mode="danger-full-access"', '-c permissions.default=all',
                 '-c sandbox_workspace_write.writable_roots=[]', '--approve-for-me',
                 '--permission-profile full', '--cd C:/', '--full-auto', '--model', '"broken'):
        expect_block(lambda: policy.parse_extra(args))
    for args in ('', '--sandbox workspace-write --sandbox workspace-write'):
        expect_block(lambda: policy.parse_extra(args, require_write=True))
    assert policy.parse_extra('--sandbox=workspace-write -m "model name" --json', require_write=True) == ['-m', 'model name', '--json']
    assert policy.parse_extra('-s workspace-write -c \'model_reasoning_effort="high"\'') == ['-c', 'model_reasoning_effort="high"']

    with tempfile.TemporaryDirectory(prefix='program-kit-worker-policy-') as temporary:
        root = Path(temporary).resolve()
        ambient = {key: value for key, value in os.environ.items() if key not in preflight.CODEX_AGENT_ENVIRONMENT_KEYS}
        ambient[policy.EXTRA_ARGS] = '--model "fixture model" --sandbox workspace-write --json'
        original = ambient[policy.EXTRA_ARGS]
        observed = []

        def inspect():
            argv = ['fixture-codex', 'exec', 'Program Kit permission check', *shlex.split(os.environ[policy.EXTRA_ARGS])]
            policy.parse_extra(shlex.join(argv[3:]), require_write=True)
            observed.append(argv)
            return argv

        def sandbox_fixture(command, **kwargs):
            assert command[:2] == ['fixture-codex', 'sandbox']
            assert command[command.index('--permission-profile') + 1] == ':workspace'
            assert '--include-managed-config' in command
            assert kwargs['cwd'] == root and kwargs['timeout'] == 60
            child = command[command.index('--') + 1:]
            assert child[:2] == [shutil.which('python'), '-I']
            # Execute the probe script directly as a fixture, never Codex.
            return subprocess.run(child, **kwargs)

        with patch.dict(os.environ, ambient, clear=True), patch.object(policy, 'inspect_adapter', inspect), \
             patch.object(policy, 'require_core_contract'), \
             patch.object(preflight, 'evaluate_preflight', return_value={'action': 'continue', 'script_flavor': 'py'}):
            with policy.worker_environment(root, 'codex', runner=sandbox_fixture):
                assert shlex.split(os.environ[policy.EXTRA_ARGS]).count('--sandbox') == 1
            assert os.environ[policy.EXTRA_ARGS] == original
            records = list((root / '.specify/workflows/worker-preflights').glob('*.json'))
            record = json.loads(records[0].read_text())
            assert record['status'] == 'passed' and record['adapterArgv'] == observed[0]
            if os.name == 'nt':
                assert record['probe']['writesVerified'] and record['probe']['codingAgentStarted'] is False
                assert record['probe']['sandboxReadbackVerified'] and record['probe']['cleanupVerified']
            assert not list(root.rglob('.program-kit-write-probe-*'))
            assert not (root / 'docs').exists(), 'Only probe-created empty directories should be removed'

            # A process can return zero without creating any files. Probe and
            # artifact contracts must both reject that result.
            def no_writes(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 0, 'PROGRAM_KIT_WRITE_PROBE_OK', '')

            if os.name == 'nt':
                def blocked_scope():
                    with policy.worker_environment(root, 'codex', runner=no_writes):
                        raise AssertionError('Dispatch was reached without write access')
                expect_block(blocked_scope)
                assert os.environ[policy.EXTRA_ARGS] == original
                assert any(json.loads(p.read_text())['status'] == 'blocked' for p in
                           (root / '.specify/workflows/worker-preflights').glob('*.json'))
            with policy.worker_environment(root, 'claude', runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError())):
                assert os.environ[policy.EXTRA_ARGS] == original
            os.environ.pop(policy.EXTRA_ARGS)
            try:
                with policy.worker_environment(root, 'codex', runner=sandbox_fixture):
                    raise RuntimeError('Fixture workflow failed after dispatch')
            except RuntimeError:
                pass
            assert policy.EXTRA_ARGS not in os.environ
            os.environ['CODEX_THREAD_ID'] = 'fixture-agent'
            expect_block(lambda: policy.worker_environment(root, 'codex').__enter__(), 'PROGRAM_KIT_CODEX_AGENT_BOUNDARY')

        # Test installed adapter behavior with no actual subprocess dispatch.
        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            raise AssertionError('Run this validator with the installed Specify interpreter')
        with patch.dict(os.environ, ambient, clear=True):
            old = os.environ.pop(policy.EXTRA_ARGS)
            before = get_integration('codex').build_exec_args('fixture', output_json=False)
            assert '--sandbox' not in before, before
            os.environ[policy.EXTRA_ARGS] = '--sandbox workspace-write'
            # Exercise the real Spec Kit argv builder, without requiring Codex
            # to be installed in deterministic CI or starting its executable.
            with patch.object(policy.shutil, 'which', return_value='fixture-codex') as executable:
                after = policy.inspect_adapter()
                executable.assert_called_once()
            assert after[0] == 'fixture-codex'
            assert after[1:3] == ['exec', 'Program Kit permission check']
            assert after[-2:] == ['--sandbox', 'workspace-write']
            os.environ[policy.EXTRA_ARGS] = old
            with patch.object(type(get_integration('codex')), 'build_exec_args', return_value=['codex', 'exec', 'fixture']):
                expect_block(policy.inspect_adapter)

        with patch.object(preflight, 'verify_git_worktree'), \
             patch.object(preflight, 'verify_windows_resolver'), \
             patch.object(preflight, 'inspect_script_runtime', return_value=('py', root / 'resolver.py')):
            blocked = preflight.evaluate_preflight('codex', root, environ={}, platform_name='posix', check_worker_access=True)
            assert blocked['action'] == 'worker-access-blocked'
            ready = preflight.evaluate_preflight('codex', root, environ={policy.EXTRA_ARGS: '--sandbox workspace-write'},
                                                platform_name='posix', check_worker_access=True)
            assert ready == {'action': 'continue', 'script_flavor': 'py'}
            untouched = preflight.evaluate_preflight('claude', root, environ={}, check_worker_access=True)
            assert untouched['action'] == 'continue'
            saved = root / '.specify/workflows/runs/other-integration/inputs.json'
            saved.parent.mkdir(parents=True)
            saved.write_text(json.dumps({'inputs': {'integration': 'claude'}}))
            explicit = preflight.evaluate_preflight('auto', root, current_run_id='other-integration',
                                                    environ={}, check_worker_access=True)
            assert explicit == {'action': 'continue', 'script_flavor': 'not-applicable'}
            with patch('proxy_bootstrap.active', return_value=True):
                proxy = preflight.evaluate_preflight('codex', root, current_run_id='proxy-fixture',
                    environ={'CODEX_THREAD_ID': 'fixture'}, platform_name='posix', check_worker_access=True)
                assert proxy == {'action': 'continue', 'script_flavor': 'py'}

        # Exercise both CLI entry paths without executing schemas, an engine or
        # workers. A paused gate and its history remain engine-owned.
        import workflow_lifecycle as workflow
        state = SimpleNamespace(run_id='fixture', status=workflow.RunStatus.PAUSED,
                                current_step_id='review-assessment', error=None,
                                step_results={}, inputs={'integration': 'codex'})
        events = []
        @contextlib.contextmanager
        def scope(project, requested):
            assert project == root and requested == 'codex'
            events.append('enter')
            try:
                yield
            finally:
                events.append('exit')
        def executed(*args, **kwargs):
            assert events[-1] == 'schemas'
            events.append('engine')
            return state
        for command in ('run', 'resume'):
            events.clear()
            arguments = ['workflow_lifecycle.py', command, '--run-id', 'fixture']
            if command == 'run':
                arguments.extend(['--input', 'integration=codex'])
            with patch.object(sys, 'argv', arguments), patch.object(Path, 'cwd', return_value=root), \
                 patch('python_runtime.environment', return_value=contextlib.nullcontext()), \
                 patch.object(policy, 'worker_environment', scope), \
                 patch.object(workflow.RunState, 'load', return_value=state), \
                 patch.object(workflow, 'execution_lock', return_value=contextlib.nullcontext()), \
                 patch.object(workflow, 'prepare_schema_runtimes', side_effect=lambda *a: events.append('schemas')), \
                 patch.object(workflow, 'require_enabled'), patch.object(workflow.governance, 'configure_paths'), \
                 patch.object(workflow.WorkflowEngine, 'load_workflow', return_value=object()), \
                 patch.object(workflow, 'execute_definition', side_effect=executed), \
                 patch.object(workflow, 'resume', side_effect=executed), contextlib.redirect_stdout(io.StringIO()):
                assert workflow.main() == 0
            assert events == ['enter', 'schemas', 'engine', 'exit'], (command, events)

        # Distinguish the worker artifact contract from process success, while
        # retaining all existing semantic validators and review gates.
        import bootstrap_context
        with patch.object(bootstrap_context, 'governance_contract', return_value={'paths': {}}), \
             patch.object(bootstrap_context, 'resolved_output_contract', return_value={
                 'artifact_byte_budgets': {'docs/architecture/missing.md': 100},
                 'artifact_target_bytes': {'docs/architecture/missing.md': 50}}):
            try:
                bootstrap_context.validate_stage_output(root, 'assessment')
            except bootstrap_context.ContextError as error:
                assert 'Required assessment output is missing' in str(error)
                assert 'PROGRAM_KIT_WORKER_ARTIFACT_CONTRACT' in str(error)
            else:
                raise AssertionError('Missing artifacts were accepted')

    # The CLI wraps both run and resume, including resumes past initial preflight.
    lifecycle = (ROOT / 'extensions/program-kit-governance/scripts/workflow_lifecycle.py').read_text()
    assert "if args.command in {'run', 'resume'}:" in lifecycle
    assert "dispatch_scope.enter_context(worker_environment" in lifecycle
    assert lifecycle.index('dispatch_scope.enter_context') < lifecycle.index('prepare_schema_runtimes(root)', lifecycle.index('def main()'))
    assert 'dispatch_scope.close()' in lifecycle
    print('Codex argv, scoped permissions, write-probe failure, and artifact contracts passed; no coding agent started.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

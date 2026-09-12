"""Native engine regression: stage retry, NOT READY, preserved history and completion."""
from __future__ import annotations

import copy
import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

import validate_bootstrap_lifecycle as fixture
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine, RunState
from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.steps.command import CommandStep
from specify_cli.workflows.steps.shell import ShellStep

import workflow_lifecycle as workflow

g, life = fixture.governance, fixture.lifecycle


def shell(identity, command):
    return {'id': identity, 'type': 'shell', 'run': command, 'output_format': 'json'}


def agent(identity):
    return {'id': identity, 'type': 'command', 'command': 'speckit.program-kit-governance.readiness',
            'integration': 'codex', 'input': {'args': identity}}


def definition(steps):
    return WorkflowDefinition({'schema_version': '1.0',
        'workflow': {'id': 'program-kit-bootstrap', 'name': 'Native lifecycle regression', 'version': '0.3.1'},
        'inputs': {'integration': {'type': 'string', 'default': 'codex'},
                   'bootstrap_intake': {'type': 'string', 'default': 'docs/architecture/bootstrap-intake.json'},
                   'bootstrap_verdict': {'type': 'string', 'default': ''}}, 'steps': steps})


GOV = 'python .specify/extensions/program-kit-governance/scripts/governance_state.py '
FLOW = 'python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py '


def ready_tail():
    return [agent('readiness'), shell('validate-readiness-output', GOV + 'evaluate-readiness'),
            shell('require-readiness', GOV + 'require-readiness'),
            shell('complete-bootstrap', FLOW + 'step complete --run-id {{ context.run_id }}')]


def setup(root):
    fixture.setup(root)
    g.write_review('bootstrap')
    g.accept_bootstrap('approve')
    (root / g.READINESS_REPORT).write_text('**Status**: READY\n\nCurrent reviewed evidence agrees.\n', encoding='utf-8')


def main():
    original_shell = ShellStep.execute
    def execute(self, config, context):
        config = copy.deepcopy(config)
        config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
        return original_shell(self, config, context)
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='program-kit-workflow-resume-') as temporary:
        root = Path(temporary)
        os.chdir(root)
        try:
            with patch.object(ShellStep, 'execute', execute), patch.object(sys.stdin, 'isatty', return_value=False):
                setup(root)
                approval = (root / g.BOOTSTRAP_APPROVAL).read_bytes()
                constitution = (root / g.CONSTITUTION).read_bytes()
                report = root / g.READINESS_REPORT
                architecture = root / 'docs/architecture/architecture.md'
                good_architecture = architecture.read_bytes()
                calls = []
                def arch_dispatch(self, command, integration, model, args, context):
                    calls.append(args)
                    if args == 'architecture-dispatch':
                        if calls.count('architecture-dispatch') == 1:
                            architecture.unlink()
                        else:
                            architecture.write_bytes(good_architecture)
                    return {'exit_code': 0, 'stdout': 'producer finished', 'stderr': ''}
                steps = [shell('accepted-prefix', 'python -c "print(1)"'),
                         shell('prepare-architecture-context', 'python -c "print(1)"'),
                         agent('architecture-dispatch'),
                         shell('validate-architecture-output', 'python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py validate-output --stage architecture --json'),
                         {'id': 'review-bootstrap', 'type': 'gate', 'message': 'Review exact repaired fixture',
                          'show_file': 'docs/architecture/reviews/bootstrap-review.md',
                          'options': ['approve', 'reject'], 'on_reject': 'retry', 'verdict_input': 'bootstrap_verdict'},
                         *ready_tail()]
                with patch.object(CommandStep, '_try_dispatch', arch_dispatch):
                    first = WorkflowEngine(root).execute(definition(steps), run_id='architecture-retry')
                    assert first.status == RunStatus.FAILED and first.current_step_id == 'validate-architecture-output'
                    prefix = copy.deepcopy(first.step_results['accepted-prefix'])
                    second = workflow.resume(root, first.run_id)
                    assert second.status == RunStatus.PAUSED and second.current_step_id == 'review-bootstrap'
                    assert second.step_results['accepted-prefix'] == prefix
                    assert calls.count('architecture-dispatch') == 2
                    assert not (root / g.BOOTSTRAP_COMPLETION).exists()
                    third = workflow.resume(root, first.run_id, {'bootstrap_verdict': 'approve'})
                    assert third.status == RunStatus.COMPLETED, (third.current_step_id, third.step_results.get(third.current_step_id), third.error)
                    workflow.validate_engine_completion(root)
                    assert workflow.resume(root, first.run_id).status == RunStatus.COMPLETED
                    assert calls.count('architecture-dispatch') == 2
                assert (root / g.BOOTSTRAP_APPROVAL).read_bytes() == approval
                assert (root / g.CONSTITUTION).read_bytes() == constitution
                # A pending/forged final record cannot be mistaken for engine success.
                saved = RunState.load(first.run_id, root)
                saved.status = RunStatus.FAILED
                saved.save()
                try:
                    g.validate_completion()
                except g.GovernanceStateError:
                    pass
                else:
                    raise AssertionError('Premature completion was accepted')
                saved.status = RunStatus.COMPLETED
                saved.save()
                (root / g.BOOTSTRAP_COMPLETION).unlink()

                dispatch_count = 0
                def readiness_dispatch(self, command, integration, model, args, context):
                    nonlocal dispatch_count
                    dispatch_count += 1
                    if args == 'readiness':
                        report.write_text('**Status**: NOT READY\n- Blocker: fixture | Owner: Architecture | Next: Reconcile evidence\n', encoding='utf-8')
                    elif command == 'speckit.program-kit-governance.readiness':
                        report.write_text('**Status**: READY\n\nReviewed unchanged authority and current evidence.\n', encoding='utf-8')
                    return {'exit_code': 0, 'stdout': 'fixture producer', 'stderr': ''}
                with patch.object(CommandStep, '_try_dispatch', readiness_dispatch):
                    failed = WorkflowEngine(root).execute(definition(ready_tail()), run_id='readiness-retry')
                    assert failed.status == RunStatus.FAILED and failed.current_step_id == 'require-readiness'
                    assert not (root / g.BOOTSTRAP_COMPLETION).exists()
                    original_state = (workflow.run_directory(root, failed.run_id) / 'state.json').read_bytes()
                    resumed = workflow.resume(root, failed.run_id)
                    assert resumed.status == RunStatus.COMPLETED, (resumed.current_step_id, resumed.step_results.get(resumed.current_step_id), resumed.error)
                    assert resumed.run_id != failed.run_id
                    assert (workflow.run_directory(root, failed.run_id) / 'state.json').read_bytes() == original_state
                    assert (root / g.BOOTSTRAP_APPROVAL).read_bytes() == approval
                    workflow.validate_engine_completion(root)
                    count = dispatch_count
                    assert workflow.resume(root, failed.run_id).run_id == resumed.run_id
                    assert dispatch_count == count
                (root / g.BOOTSTRAP_COMPLETION).unlink()
                # Native reproduction of the historical sole-abort routing. No
                # fabricated historical state is used for the positive recovery test.
                historical = definition(ready_tail()[:2] + [
                    {**shell('complete-bootstrap', GOV + 'complete-bootstrap'), 'continue_on_error': True},
                    {'id': 'confirm-completion-failure', 'type': 'gate', 'message': 'Historical abort-only fixture',
                     'options': ['abort'], 'on_reject': 'abort', 'verdict_input': 'bootstrap_verdict'}])
                with patch.object(CommandStep, '_try_dispatch', readiness_dispatch):
                    aborted = WorkflowEngine(root).execute(historical, inputs={'bootstrap_verdict': 'abort'}, run_id='historical-abort')
                    assert aborted.status == RunStatus.ABORTED
                    old = (workflow.run_directory(root, aborted.run_id) / 'state.json').read_bytes()
                    # Interrupt the real continuation engine at its readiness
                    # dispatch; it must pause and resume without repeating closure.
                    seen = []
                    def interrupted(self, command, integration, model, args, context):
                        seen.append(command)
                        if command == 'speckit.program-kit-governance.readiness' and seen.count(command) == 1:
                            raise KeyboardInterrupt()
                        return readiness_dispatch(self, command, integration, model, args, context)
                    with patch.object(CommandStep, '_try_dispatch', interrupted):
                        paused = workflow.resume(root, aborted.run_id)
                        assert paused.status == RunStatus.PAUSED and paused.current_step_id == 'recovery-readiness'
                        assert not (root / g.BOOTSTRAP_COMPLETION).exists()
                        done = workflow.resume(root, aborted.run_id)
                        assert done.status == RunStatus.COMPLETED, done.error
                        assert seen.count('speckit.program-kit-governance.bootstrap-recovery') == 1
                    assert (workflow.run_directory(root, aborted.run_id) / 'state.json').read_bytes() == old
                    assert (root / g.BOOTSTRAP_APPROVAL).read_bytes() == approval
                    workflow.validate_engine_completion(root)
                rejected = definition([{'id': 'review-bootstrap', 'type': 'gate', 'message': 'Semantic rejection',
                                       'options': ['approve', 'reject'], 'on_reject': 'abort', 'verdict_input': 'bootstrap_verdict'}])
                rejected_state = WorkflowEngine(root).execute(rejected, inputs={'bootstrap_verdict': 'reject'}, run_id='semantic-rejection')
                try:
                    workflow.resume(root, rejected_state.run_id)
                except life.LifecycleError as error:
                    assert 'semantic rejection' in str(error)
                else:
                    raise AssertionError('Semantic rejection was converted into technical resumption')
                (root / g.BOOTSTRAP_COMPLETION).unlink()
                changed_calls = []
                def changed_dispatch(self, command, integration, model, args, context):
                    changed_calls.append(command)
                    if command == 'speckit.program-kit-governance.bootstrap-recovery':
                        architecture.write_bytes(architecture.read_bytes() + b'\nReviewed clarification of the first-slice narrative.\n')
                    return readiness_dispatch(self, command, integration, model, args, context)
                with patch.object(CommandStep, '_try_dispatch', changed_dispatch):
                    failed = WorkflowEngine(root).execute(definition(ready_tail()), run_id='changed-authority')
                    assert failed.status == RunStatus.FAILED
                    try:
                        workflow.resume(root, failed.run_id, {'recovery_verdict': 'approve'})
                    except workflow.WorkflowLifecycleError:
                        pass
                    else:
                        raise AssertionError('Future unseen review was preapproved')
                    paused = workflow.resume(root, failed.run_id)
                    assert paused.status == RunStatus.PAUSED and paused.current_step_id == 'review-recovery', paused.error
                    assert (root / g.BOOTSTRAP_APPROVAL).read_bytes() == approval
                    assert not (root / g.BOOTSTRAP_COMPLETION).exists()
                    workflow.resume(root, failed.run_id)
                    assert changed_calls.count('speckit.program-kit-governance.bootstrap-recovery') == 1
                    done = workflow.resume(root, failed.run_id, {'recovery_verdict': 'approve'})
                    assert done.status == RunStatus.COMPLETED, (done.current_step_id, done.step_results.get(done.current_step_id))
                    assert changed_calls.count('speckit.program-kit-governance.bootstrap-recovery') == 1
                    assert (root / g.BOOTSTRAP_APPROVAL).read_bytes() != approval
                    assert (root / g.CONSTITUTION).read_bytes() == constitution
                    workflow.validate_engine_completion(root)
                    assert workflow.resume(root, failed.run_id).run_id == done.run_id
                try:
                    workflow.execute_definition(root, definition(ready_tail()), {}, failed.run_id)
                except workflow.WorkflowLifecycleError as error:
                    assert 'already exists' in str(error)
                else:
                    raise AssertionError('An existing run was overwritten')
                with workflow.execution_lock(root):
                    try:
                        workflow.resume(root, failed.run_id)
                    except workflow.WorkflowLifecycleError as error:
                        assert 'already active' in str(error)
                    else:
                        raise AssertionError('Concurrent governed execution was accepted')
                history = root / '.specify/workflows/resumption-history/architecture-retry'
                assert any((entry / 'inputs.json').is_file() and (entry / 'workflow.yml').is_file()
                           for entry in history.iterdir())
                # Saved-definition migration has separate unit evidence. Its
                # fixture reaches a native gate; it does not claim live success.
                migration = root / 'migration-case'
                migration.mkdir()
                migration_steps = [shell('preserved-prefix', 'python -c "print(1)"'),
                    {'id': 'review-bootstrap', 'type': 'gate', 'message': 'Migration review fixture',
                     'options': ['approve', 'reject'], 'on_reject': 'retry', 'verdict_input': 'bootstrap_verdict'},
                    shell('changed-suffix', 'python -c "print(2)"')]
                old_definition = definition(migration_steps)
                old_definition.data['workflow']['version'] = '0.10.2'
                old_definition = WorkflowDefinition(old_definition.data)
                migration_state = WorkflowEngine(migration).execute(old_definition, run_id='saved-migration')
                assert migration_state.status == RunStatus.PAUSED
                prefix = copy.deepcopy(migration_state.step_results['preserved-prefix'])
                current = copy.deepcopy(old_definition.data)
                current['workflow']['version'] = '0.11.0'
                current['steps'][-1]['run'] = 'python -c "print(3)"'
                installed = migration / '.specify/workflows/program-kit-bootstrap/workflow.yml'
                installed.parent.mkdir(parents=True)
                installed.write_text(yaml.safe_dump(current), encoding='utf-8')
                migrated = workflow.migrate_suffix(migration, migration_state, old_definition, 'review-bootstrap')
                assert migrated.version == '0.11.0'
                assert migrated.steps[0] == old_definition.steps[0]
                assert migrated.steps[-1] == current['steps'][-1]
                assert migration_state.step_results['preserved-prefix'] == prefix
                current['steps'][1]['verdict_input'] = 'another_verdict'
                current['inputs']['another_verdict'] = {'type': 'string', 'default': ''}
                installed.write_text(yaml.safe_dump(current), encoding='utf-8')
                before = (workflow.run_directory(migration, migration_state.run_id) / 'workflow.yml').read_bytes()
                try:
                    workflow.migrate_suffix(migration, migration_state, old_definition, 'review-bootstrap')
                except workflow.WorkflowLifecycleError as error:
                    assert 'review gate contract changed' in str(error)
                else:
                    raise AssertionError('Migration silently changed the pending human gate')
                assert (workflow.run_directory(migration, migration_state.run_id) / 'workflow.yml').read_bytes() == before
                print('Native engine stage retry, review pause, NOT READY continuation, idempotency and completion binding passed.')
        finally:
            os.chdir(previous)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Deterministic paid-workflow guards; never starts a coding agent."""
from __future__ import annotations

import copy
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml
import validate_workflow_resumption as fixture
from live.v2.authorization import issue_authorization, validate_authorization
from live.v2.common import LiveContractError, atomic_write_json, canonical_sha256, load_object
from live.v2.workflow_acceptance import driver, reserve_dispatch, reported_usage, reviewed_input
from specify_cli.workflows.steps.command import CommandStep
from specify_cli.workflows.steps.shell import ShellStep

ROOT = Path(__file__).resolve().parents[1]


def rejects(action, code):
    try:
        action()
    except LiveContractError as error:
        assert code in str(error), str(error)
    else:
        raise AssertionError('Expected ' + code)


def main():
    previous = Path.cwd()
    schema = load_object(ROOT / 'tests/live/schemas/v2/authorization.schema.json')
    with tempfile.TemporaryDirectory(prefix='program-kit-live-workflow-') as temporary:
        base = Path(temporary)
        profile = {'integration': 'codex', 'launcherVersion': 'test-only', 'model': 'test-only',
                   'reasoningEffort': 'test-only', 'sandbox': 'workspace-write', 'timeoutSeconds': 60}
        scenario = {'id': 'test-only', 'version': '1', 'digest': '1' * 64}
        candidate = {'releaseReceipt': 'test-only.json', 'releaseReceiptSha256': '2' * 64}
        binding = {'fixture': 'test-only', 'version': '1', 'parentManifest': None, 'verdictInput': None, 'verdict': None}
        for phase in ('workflow-fresh', 'workflow-failure', 'workflow-resume'):
            checkpoint = {'checkpointId': 'test-only', 'digest': '3' * 64} if phase == 'workflow-resume' else None
            path = base / (phase + '.json')
            manifest = issue_authorization(path, schema, phase=phase, scenario=scenario, candidate=candidate,
                agent_profile=profile, checkpoint=checkpoint, workflow=binding)
            assert manifest['limits']['maximumPaidSessions'] == 8
            validate_authorization(path, schema, phase=phase, scenario_digest='1' * 64,
                                   candidate_receipt_digest='2' * 64, checkpoint_digest='3' * 64 if checkpoint else None)
        rejects(lambda: reviewed_input(None, 'approve'), 'FUTURE_VERDICT_FORBIDDEN')
        rejects(lambda: reviewed_input({'review': {'input': 'bootstrap_verdict', 'options': ['approve', 'reject']}}, None), 'ACTUAL_GATE_VERDICT_REQUIRED')
        counter = base / 'counter.json'
        reserve_dispatch(counter, 1, 'fixture', 'producer')
        before = counter.read_bytes()
        rejects(lambda: reserve_dispatch(counter, 1, 'fixture', 'second'), 'SESSION_LIMIT_EXCEEDED')
        assert counter.read_bytes() == before
        event = '{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3}}'
        usage = reported_usage({'step_results': {'producer': {'output': {'stdout': event}}}},
                               [{'step': 'producer', 'run_id': 'fixture'}], 'fixture')
        assert usage['tokens'] == {'input_tokens': 12, 'output_tokens': 3} and usage['cost'] is None
        project = base / 'project'
        project.mkdir()
        evidence = base / 'evidence'
        evidence.mkdir()
        os.chdir(project)
        try:
            fixture.setup(project)
            installed = project / '.specify/workflows/program-kit-bootstrap/workflow.yml'
            installed.write_text(yaml.safe_dump(fixture.definition(fixture.ready_tail()).data), encoding='utf-8')
            consumed = load_object(base / 'workflow-failure.json')
            job = {'project': str(project), 'nativeRun': 'controlled-native', 'sourceRun': None, 'faultPending': True,
                   'consumedAuthorization': str(base / 'workflow-failure.json'),
                   'consumption': {'authorizationSha256': canonical_sha256(consumed)}}
            atomic_write_json(evidence / 'job.json', job)
            original_shell = ShellStep.execute
            def execute(self, config, context):
                config = copy.deepcopy(config)
                config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
                return original_shell(self, config, context)
            def dispatch(self, command, integration, model, args, context):
                (project / fixture.g.READINESS_REPORT).write_text('**Status**: READY\n\nCurrent test authority agrees.\n', encoding='utf-8')
                return {'exit_code': 0, 'stdout': event, 'stderr': ''}
            with patch.object(CommandStep, '_try_dispatch', dispatch), patch.object(ShellStep, 'execute', execute):
                assert driver(evidence / 'job.json') == 2
            result = load_object(evidence / 'native-result.json')
            assert result['status'] == 'failed' and result['current_step'] == 'require-readiness'
            assert (evidence / 'fault.json').is_file()
            assert len(load_object(evidence / 'dispatches.json')['dispatches']) == 1
            assert not (project / fixture.g.BOOTSTRAP_COMPLETION).exists()
            try:
                driver(evidence / 'job.json')
            except FileExistsError:
                pass
            else:
                raise AssertionError('A consumed driver job was replayed')
        finally:
            os.chdir(previous)
    print('Live workflow authorization, real native controlled-failure guard, dispatch budget and replay tests passed; no coding agents started.')


if __name__ == '__main__':
    main()

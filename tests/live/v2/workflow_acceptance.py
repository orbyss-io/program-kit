"""Opt-in real workflow segments, selected by versioned fixture and one-use authority.

A segment ends at a real human gate or terminal engine outcome. A subsequent
paid segment requires a new authorization bound to that exact saved checkpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import subprocess
import uuid
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from live.v2.authorization import consume_authorization, issue_authorization, validate_authorization
from live.v2.candidate import install_candidate_from_receipt, validate_release_receipt
from live.v2.cli import (SECRET_KEYS, WorkflowProgress, candidate_packages, execution_workspace,
                         preflight, repository_root, schemas, tool_version, validate_agent_launcher,
                         worker_environment, worker_guidance)
from live.v2.common import (LiveContractError, atomic_write_json, canonical_sha256, file_inventory,
                            load_object, safe_relative, sha256_file, utc_now, validate)
from live.v2.fixture_catalog import resolve_fixture
from live.v2.supervisor import run_supervised

PHASES = ('workflow-fresh', 'workflow-failure', 'workflow-resume')


def walk(value):
    if isinstance(value, list):
        for child in value:
            yield from walk(child)
    elif isinstance(value, dict):
        if 'id' in value and 'type' in value:
            yield value
        for child in value.values():
            if isinstance(child, (list, dict)):
                yield from walk(child)


def review_gate(project: Path, run_id: str) -> dict | None:
    import yaml
    directory = project / '.specify/workflows/runs' / run_id
    state = load_object(directory / 'state.json')
    if state['status'] != 'paused':
        return None
    definition = yaml.safe_load((directory / 'workflow.yml').read_text(encoding='utf-8'))
    gate = next((step for step in walk(definition['steps'])
                 if step['id'] == state['current_step_id'] and step['type'] == 'gate'), None)
    if not gate:
        return None
    path = gate.get('show_file')
    if path:
        for key, value in load_object(directory / 'inputs.json')['inputs'].items():
            path = path.replace('{{ inputs.' + key + ' }}', str(value))
        packet = project / safe_relative(path)
        if not packet.resolve().is_relative_to(project.resolve()):
            raise LiveContractError('LIVE_REVIEW_PACKET_OUTSIDE_PROJECT')
        digest = sha256_file(packet)
    else:
        digest = None
    return {'step': gate['id'], 'input': gate.get('verdict_input'), 'options': gate['options'],
            'packet': path, 'sha256': digest, 'message': gate.get('message', '')}


def parent_checkpoint(root: Path, path: Path) -> tuple[dict, Path]:
    parent = load_object(path)
    validate(parent, load_object(schemas(root) / 'workflow-run.schema.json'))
    if parent.get('kind') != 'workflow-lifecycle' or parent.get('schemaVersion') != '2.1':
        raise LiveContractError('LIVE_WORKFLOW_PARENT_REQUIRED')
    project = (root / safe_relative(parent['workspace'])).resolve()
    if not project.is_relative_to((root / 'artifacts/live-v2-w').resolve()):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_NOT_DISPOSABLE')
    if parent['projectInventory'] != file_inventory(project):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_CHANGED')
    if not parent['process']['cleanupComplete'] or not parent['process']['logsDrained']:
        raise LiveContractError('LIVE_WORKFLOW_PARENT_CLEANUP_INCOMPLETE')
    if parent['native']['status'] in {'completed', 'aborted'}:
        raise LiveContractError('LIVE_WORKFLOW_PARENT_NOT_RESUMABLE')
    if review_gate(project, parent['native']['run_id']) != parent['review']:
        raise LiveContractError('LIVE_WORKFLOW_REVIEW_CHANGED')
    return parent, project


def reviewed_input(parent: dict | None, verdict: str | None) -> dict:
    gate = parent.get('review') if parent else None
    if gate:
        if not gate['input'] or verdict not in gate['options']:
            raise LiveContractError('LIVE_WORKFLOW_ACTUAL_GATE_VERDICT_REQUIRED')
        return {'verdictInput': gate['input'], 'verdict': verdict}
    if verdict:
        raise LiveContractError('LIVE_WORKFLOW_FUTURE_VERDICT_FORBIDDEN')
    return {'verdictInput': None, 'verdict': None}


def issue(args) -> int:
    if not args.confirmed:
        raise LiveContractError('LIVE_AUTHORIZATION_INTERACTIVE_CONFIRMATION_REQUIRED')
    root = repository_root()
    selected = resolve_fixture(args.fixture, args.fixture_version)
    if selected['kind'] != 'workflow-lifecycle':
        raise LiveContractError('LIVE_WORKFLOW_FIXTURE_KIND_REQUIRED')
    receipt_path = Path(args.release_receipt).resolve()
    receipt, receipt_sha = validate_release_receipt(root, receipt_path, load_object(schemas(root) / 'release-receipt.schema.json'))
    preflight(root, receipt)
    parent = None
    checkpoint = None
    if args.checkpoint:
        parent, _ = parent_checkpoint(root, Path(args.checkpoint).resolve())
        if parent['candidate'] != receipt_sha or parent['scenario'] != selected['authority']:
            raise LiveContractError('LIVE_WORKFLOW_PARENT_AUTHORITY_MISMATCH')
        checkpoint = {'checkpointId': parent['runId'], 'digest': sha256_file(Path(args.checkpoint))}
    if (args.phase == 'workflow-resume') != bool(parent):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_PHASE_MISMATCH')
    profile = {'integration': 'codex', 'launcherVersion': args.launcher_version, 'model': args.model,
               'reasoningEffort': args.reasoning_effort, 'sandbox': 'workspace-write',
               'timeoutSeconds': args.timeout_seconds}
    validate_agent_launcher(profile)
    workflow = {'fixture': args.fixture, 'version': args.fixture_version,
                'parentManifest': str(Path(args.checkpoint).resolve()) if parent else None,
                **reviewed_input(parent, args.verdict)}
    manifest = issue_authorization(Path(args.output).resolve(), load_object(schemas(root) / 'authorization.schema.json'),
        phase=args.phase, scenario=selected['authority'],
        candidate={'releaseReceipt': str(receipt_path), 'releaseReceiptSha256': receipt_sha},
        agent_profile=profile, checkpoint=checkpoint, expires_minutes=args.expires_minutes, workflow=workflow)
    print(json.dumps({'authorizationId': manifest['authorizationId'], 'path': args.output,
                      'fixture': selected['authority'], 'phase': args.phase}))
    return 0


def reserve_dispatch(counter: Path, limit: int, run_id: str, step: str) -> None:
    records = load_object(counter)['dispatches'] if counter.exists() else []
    if len(records) >= limit:
        raise LiveContractError('LIVE_AUTHORIZATION_SESSION_LIMIT_EXCEEDED')
    records.append({'run_id': run_id, 'step': step, 'reservedAt': utc_now()})
    atomic_write_json(counter, {'dispatches': records})


def reported_usage(state: dict, dispatches: list[dict], run_id: str) -> dict:
    selected = {record['step'] for record in dispatches if record['run_id'] == run_id}
    totals = {}
    reports = 0
    for identity in selected:
        output = state.get('step_results', {}).get(identity, {}).get('output', {})
        for line in output.get('stdout', '').splitlines():
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(event, dict) or event.get('type') != 'turn.completed' or not isinstance(event.get('usage'), dict):
                continue
            reports += 1
            for key, value in event['usage'].items():
                if isinstance(value, int) and not isinstance(value, bool):
                    totals[key] = totals.get(key, 0) + value
    return {'tokens': totals or None, 'reportedTurns': reports, 'cost': None,
            'note': 'Only usage emitted by current-segment Codex turn.completed events is counted; monetary cost is unavailable.'}


def controlled_fault(project: Path, evidence: Path, lifecycle) -> None:
    if not lifecycle.verdict(project)['eligible']:
        raise LiveContractError('LIVE_CONTROLLED_FAULT_REQUIRES_ACTUAL_READY')
    report = project / 'docs/architecture/readiness-report.md'
    shutil.copyfile(report, evidence / 'readiness-before-fault.md')
    before = sha256_file(report)
    report.write_text('**Status**: NOT READY\n\n- Blocker: controlled-live-fault | Owner: Live test supervisor | Next: Resume through the supported workflow and regenerate readiness from unchanged approved authority.\n', encoding='utf-8')
    atomic_write_json(evidence / 'fault.json', {'kind': 'controlled-readiness-failure',
        'beforeSha256': before, 'afterSha256': sha256_file(report), 'injectedAt': utc_now()})


def driver(job_path: Path) -> int:
    job = load_object(job_path)
    evidence = job_path.parent
    project = Path(job['project']).resolve()
    sys.path.insert(0, str(project / '.specify/extensions/program-kit-governance/scripts'))
    import workflow_lifecycle as workflow
    if workflow.RunState is None:
        return subprocess.run([str(workflow.installed_interpreter()), str(Path(__file__).resolve()),
                               'driver', '--job', str(job_path)], check=False).returncode
    # One supervisor invocation owns this exact segment; direct replays cannot
    # dispatch another paid worker, including after a crash.
    with (evidence / 'driver.claim').open('x', encoding='utf-8') as handle:
        handle.write(sha256_file(job_path))
    consumed = load_object(Path(job['consumedAuthorization']))
    if canonical_sha256(consumed) != job['consumption']['authorizationSha256']:
        raise LiveContractError('LIVE_WORKFLOW_CONSUMED_AUTHORITY_CHANGED')
    if project != Path.cwd().resolve() or evidence.resolve().is_relative_to(project):
        raise LiveContractError('LIVE_WORKFLOW_DRIVER_BOUNDARY_MISMATCH')
    workflow.governance.configure_paths()
    original = workflow.WorkflowEngine
    counter = evidence / 'dispatches.json'

    class SupervisedEngine(original):
        def __init__(self, root):
            super().__init__(root)
            self.live_run = None
            self.on_step_start = self.before_step

        def execute(self, definition, *args, **kwargs):
            self.live_run = kwargs['run_id']
            return super().execute(definition, *args, **kwargs)

        def resume(self, run_id, *args, **kwargs):
            self.live_run = run_id
            return super().resume(run_id, *args, **kwargs)

        def before_step(self, step_id, label):
            definition = workflow.definition_for(project, self.live_run)
            current = next(step for step in workflow.walk_steps(definition.steps) if step['id'] == step_id)
            if current['type'] == 'command':
                reserve_dispatch(counter, consumed['limits']['maximumPaidSessions'], self.live_run, step_id)
            if job['faultPending'] and step_id == 'require-readiness' and not (evidence / 'fault.json').exists():
                controlled_fault(project, evidence, workflow.lifecycle)

    workflow.WorkflowEngine = SupervisedEngine
    inputs = {}
    binding = consumed['workflow']
    if binding['verdictInput']:
        inputs[binding['verdictInput']] = binding['verdict']
    try:
        if job['sourceRun']:
            state = workflow.resume(project, job['sourceRun'], inputs)
        else:
            with workflow.execution_lock(project):
                definition = workflow.WorkflowEngine(project).load_workflow('program-kit-bootstrap')
                state = workflow.execute_definition(project, definition,
                    {'bootstrap_intake': 'docs/architecture/bootstrap-intake.json', 'integration': 'codex',
                     'auto_approve_and_ratify': False}, job['nativeRun'])
        if state.status.value == 'completed':
            workflow.governance.validate_completion()
            workflow.validate_engine_completion(project)
        value = {'run_id': state.run_id, 'status': state.status.value,
                 'current_step': state.current_step_id, 'error': state.error}
        atomic_write_json(evidence / 'native-result.json', value)
        print(json.dumps(value))
        return 0 if state.status.value in {'completed', 'paused'} else 2
    finally:
        workflow.WorkflowEngine = original


def run(args) -> int:
    root = repository_root()
    auth_path = Path(args.authorization).resolve()
    raw = load_object(auth_path)
    phase = raw['phase']
    if phase not in PHASES:
        raise LiveContractError('LIVE_WORKFLOW_PHASE_REQUIRED')
    binding = raw['workflow']
    selected = resolve_fixture(binding['fixture'], binding['version'])
    receipt, receipt_sha = validate_release_receipt(root, Path(raw['candidate']['releaseReceipt']),
                                                   load_object(schemas(root) / 'release-receipt.schema.json'))
    preflight(root, receipt)
    parent = None
    project = None
    if binding['parentManifest']:
        parent, project = parent_checkpoint(root, Path(binding['parentManifest']))
        if parent['candidate'] != receipt_sha or parent['scenario'] != selected['authority']:
            raise LiveContractError('LIVE_WORKFLOW_PARENT_AUTHORITY_MISMATCH')
    if (phase == 'workflow-resume') != bool(parent):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_PHASE_MISMATCH')
    reviewed = reviewed_input(parent, binding['verdict'])
    if reviewed['verdictInput'] != binding['verdictInput']:
        raise LiveContractError('LIVE_WORKFLOW_GATE_INPUT_CHANGED')
    authorization = validate_authorization(auth_path, load_object(schemas(root) / 'authorization.schema.json'),
        phase=phase, scenario_digest=selected['authority']['digest'], candidate_receipt_digest=receipt_sha,
        checkpoint_digest=sha256_file(Path(binding['parentManifest'])) if parent else None)
    validate_agent_launcher(authorization['agentProfile'])
    token = uuid.uuid4().hex[:8]
    run_id = f'workflow-{token}'
    evidence = root / 'artifacts/live-acceptance/v2/runs' / run_id
    evidence.mkdir(parents=True)
    setup = []
    if project is None:
        project = execution_workspace(root, token)
        shutil.copytree(Path(selected['directory']) / 'fixture', project)
        setup = install_candidate_from_receipt(root, project, candidate_packages(root, token), receipt, evidence / 'setup')
        worker_guidance(project)
        scenario = load_object(Path(selected['directory']) / 'scenario.json')
        for record in scenario['fixtureInventory']:
            if sha256_file(project / safe_relative(record['path'])) != record['sha256']:
                raise LiveContractError('LIVE_WORKFLOW_INSTALLED_FIXTURE_CHANGED')
    consumed_directory = root / 'artifacts/live-acceptance/v2/authorizations/consumed'
    consumption = consume_authorization(auth_path, authorization, consumed_directory)
    job = {'project': str(project), 'nativeRun': f'live-{token}',
           'sourceRun': parent['native']['run_id'] if parent else None,
           'faultPending': parent['faultPending'] if parent else phase == 'workflow-failure',
           'consumedAuthorization': str(consumed_directory / f"{authorization['authorizationId']}.json"),
           'consumption': consumption}
    job_path = evidence / 'job.json'
    atomic_write_json(job_path, job)
    environment = worker_environment(project, authorization['agentProfile'])
    environment['SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS'] += ' --json'
    progress = WorkflowProgress(project)
    progress.start()
    try:
        result = run_supervised([sys.executable, str(Path(__file__).resolve()), 'driver', '--job', str(job_path)],
            cwd=project, environment=environment, evidence_directory=evidence / 'worker',
            timeout_seconds=authorization['agentProfile']['timeoutSeconds'],
            secrets=[os.environ.get(key, '') for key in SECRET_KEYS])
    finally:
        progress.stop()
    result_path = evidence / 'native-result.json'
    native = load_object(result_path) if result_path.exists() else {
        'run_id': job['sourceRun'] or job['nativeRun'], 'status': 'inconclusive', 'current_step': None}
    if not result_path.exists():
        visited = set()
        while native['run_id'] not in visited:
            visited.add(native['run_id'])
            mapping = project / '.specify/workflows/resumptions' / f"{native['run_id']}.json"
            if not mapping.is_file():
                break
            native['run_id'] = load_object(mapping)['continuation_run']
    # Preserve the native state even if a process stopped before writing its summary.
    native_directory = project / '.specify/workflows/runs' / native['run_id']
    saved = {}
    if (native_directory / 'state.json').exists():
        saved = load_object(native_directory / 'state.json')
        native.update(status=saved['status'], current_step=saved['current_step_id'])
        shutil.copytree(native_directory, evidence / 'native-run')
    clean = result.cleanupComplete and result.logsDrained and not result.timedOut and not result.operatorCancellationRecorded
    gate = review_gate(project, native['run_id']) if native_directory.exists() else None
    completed = native['status'] == 'completed' and result.exitCode == 0 and clean and result_path.exists()
    fault = load_object(evidence / 'fault.json') if (evidence / 'fault.json').exists() else None
    status = 'completed' if completed else 'paused' if native['status'] == 'paused' and clean else 'failed'
    dispatches = load_object(evidence / 'dispatches.json')['dispatches'] if (evidence / 'dispatches.json').exists() else []
    manifest = {'schemaVersion': '2.1', 'kind': 'workflow-lifecycle', 'runId': run_id, 'phase': phase,
        'status': status, 'native': native, 'review': gate, 'candidate': receipt_sha,
        'scenario': selected['authority'], 'authorization': consumption, 'agentProfile': authorization['agentProfile'],
        'parent': {'path': binding['parentManifest'], 'sha256': authorization['checkpoint']['digest']} if parent else None,
        'executionKind': parent['executionKind'] if parent else ('controlled-failure' if job['faultPending'] else 'fresh'),
        'fault': fault, 'faultPending': job['faultPending'] and fault is None,
        'workspace': project.relative_to(root).as_posix(), 'projectInventory': file_inventory(project),
        'dispatches': dispatches,
        'process': result.as_dict(), 'setup': setup, 'finishedAt': utc_now(),
        'usage': reported_usage(saved, dispatches, native['run_id'])}
    # Checking the catalog again proves the immutable repository fixture was not changed.
    if resolve_fixture(binding['fixture'], binding['version']) != selected:
        raise LiveContractError('LIVE_WORKFLOW_FIXTURE_CHANGED_DURING_RUN')
    path = evidence / 'manifest.json'
    validate(manifest, load_object(schemas(root) / 'workflow-run.schema.json'))
    atomic_write_json(path, manifest)
    print(json.dumps({'status': status, 'native': native, 'review': gate, 'manifest': str(path)}))
    return 0 if completed or status == 'paused' else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    auth = commands.add_parser('authorize')
    auth.add_argument('--phase', choices=PHASES, required=True)
    for name in ('release-receipt', 'model', 'reasoning-effort', 'launcher-version', 'output'):
        auth.add_argument('--' + name, required=True)
    auth.add_argument('--fixture', default='price-calculator-approved-intake')
    auth.add_argument('--fixture-version', default='1')
    auth.add_argument('--checkpoint')
    auth.add_argument('--verdict')
    auth.add_argument('--timeout-seconds', type=int, default=7200)
    auth.add_argument('--expires-minutes', type=int, default=30)
    auth.add_argument('--confirmed', action='store_true')
    execution = commands.add_parser('run')
    execution.add_argument('--authorization', required=True)
    child = commands.add_parser('driver')
    child.add_argument('--job', required=True)
    inspect = commands.add_parser('inspect-parent')
    inspect.add_argument('--checkpoint', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'authorize':
            return issue(args)
        if args.command == 'run':
            return run(args)
        if args.command == 'driver':
            return driver(Path(args.job).resolve())
        parent, project = parent_checkpoint(repository_root(), Path(args.checkpoint).resolve())
        print(json.dumps({'native': parent['native'], 'review': parent['review']}, indent=2))
        if parent['review'] and parent['review']['packet']:
            print((project / parent['review']['packet']).read_text(encoding='utf-8'))
        return 0
    except (LiveContractError, OSError, ValueError, KeyError) as error:
        print(f'Live workflow contract: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

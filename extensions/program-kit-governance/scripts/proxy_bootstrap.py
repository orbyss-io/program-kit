"""Explicit same-session bootstrap rehearsal; native engine, no agent dispatch."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import proxy_intake

DIRECTORY = Path('.specify/proxy-bootstrap')
BINDING = DIRECTORY / 'session.json'
ENVIRONMENT = 'PROGRAM_KIT_PROXY_BOOTSTRAP_SESSION'
MODE = 'simulated-proxy'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def binding(root):
    root = root.resolve()
    value = load(root / BINDING)
    if (value.get('kind') != 'same-session-proxy-bootstrap' or value.get('authority') != 'none'
            or value.get('root') != str(root) or value.get('independentLiveWorker') is not False
            or not value.get('runId', '').startswith('proxy-')):
        raise ValueError('Invalid or relocated proxy bootstrap binding')
    for name, key in ((proxy_intake.MARKER, 'proxySha256'),
                      (proxy_intake.INTAKE, 'intakeSha256'),
                      (Path('.intake-session-owner'), 'ownerSha256'),
                      (Path('product-idea.md'), 'scenarioSha256')):
        if proxy_intake.digest(root / name) != value[key]:
            raise ValueError('Proxy bootstrap input changed: ' + name.as_posix())
    return value


def active(root, run_id=None):
    """Only an explicit, root-bound proxy invocation can consume simulated evidence."""
    if not os.environ.get(ENVIRONMENT):
        return False
    value = binding(root)
    if os.environ[ENVIRONMENT] != value['session'] or (run_id and run_id != value['runId']):
        raise ValueError('Proxy bootstrap invocation does not match its bound session/run')
    return True


def require_active(root, run_id=None):
    if not active(root, run_id):
        raise ValueError('Simulated proxy evidence is valid only inside its explicit bootstrap rehearsal')


@contextlib.contextmanager
def installer_cache(root):
    previous = os.environ.get('UV_CACHE_DIR')
    os.environ['UV_CACHE_DIR'] = str(root.resolve() / '.program-kit/cache/proxy-uv')
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop('UV_CACHE_DIR', None)
        else:
            os.environ['UV_CACHE_DIR'] = previous


@contextlib.contextmanager
def invocation(root):
    value = binding(root)
    previous = os.environ.get(ENVIRONMENT)
    os.environ[ENVIRONMENT] = value['session']
    try:
        with installer_cache(root):
            yield value
    finally:
        if previous is None:
            os.environ.pop(ENVIRONMENT, None)
        else:
            os.environ[ENVIRONMENT] = previous


def prepare(root):
    from specify_cli.workflows.engine import WorkflowEngine, validate_workflow
    if (root / BINDING).exists():
        raise ValueError('Proxy bootstrap already prepared; use advance to preserve its history')
    result = proxy_intake.verify(root)
    if result['scope'] != 'full-intake':
        raise ValueError('Bootstrap rehearsal requires a validated full proxy intake')
    definition = WorkflowEngine(root).load_workflow('program-kit-bootstrap')
    errors = validate_workflow(definition)
    if errors:
        raise ValueError('; '.join(errors))
    # Preparation may use a different Python than the interactive intake. Reuse
    # the existing pinned, project-local installer for this engine interpreter.
    import schema_runtime
    with installer_cache(root):
        schema_runtime.setup(root)
    value = {'schemaVersion': 1, 'kind': 'same-session-proxy-bootstrap', 'authority': 'none',
             'independentLiveWorker': False, 'root': str(root.resolve()),
             'session': uuid.uuid4().hex, 'runId': 'proxy-' + uuid.uuid4().hex[:12],
             'workflowSha256': canonical(definition.data),
             'proxySha256': proxy_intake.digest(root / proxy_intake.MARKER),
             'intakeSha256': proxy_intake.digest(root / proxy_intake.INTAKE),
             'ownerSha256': proxy_intake.digest(root / '.intake-session-owner'),
             'scenarioSha256': proxy_intake.digest(root / 'product-idea.md')}
    write(root / DIRECTORY / 'workflow.json', definition.data)
    write(root / DIRECTORY / 'intake-evidence.json', result)
    write(root / BINDING, value)
    return {'status': 'prepared', 'runId': value['runId'], 'authority': 'none'}


def pending(root):
    value = binding(root)
    request = load(root / DIRECTORY / 'pending.json')
    state = load(root / '.specify/workflows/runs' / value['runId'] / 'state.json')
    if (request['runId'] != value['runId'] or state['status'] != 'paused'
            or state['current_step_id'] != request['step']):
        raise ValueError('Proxy request is not the current paused native step')
    return request


def respond(root, note, files, choice=None):
    request = pending(root)
    if not note.strip():
        raise ValueError('Record the work or simulated review rationale')
    if request['type'] == 'gate':
        if choice not in request['options']:
            raise ValueError('Choose one of the current review options')
        files = [request['show_file']]
    elif choice is not None:
        raise ValueError('Producer completion cannot supply a review verdict')
    if not files:
        raise ValueError('Bind at least one produced artifact; validators determine correctness')
    hashes = {}
    for name in files:
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Evidence must be an existing file inside the disposable consumer')
        hashes[path.relative_to(root.resolve()).as_posix()] = proxy_intake.digest(path)
    value = {'requestSha256': canonical(request), 'authority': 'none', 'answerSource': 'assistant-simulated',
             'note': note, 'artifacts': hashes, 'choice': choice}
    # Preserve every review/repair response rather than replacing its provenance.
    write(root / DIRECTORY / 'response-history' / (uuid.uuid4().hex + '.json'),
          {'step': request['step'], **value})
    write(root / DIRECTORY / 'responses' / (request['step'] + '.json'), value)
    return {'status': 'response-recorded', 'step': request['step'], 'authority': 'none'}


def step_response(root, request):
    path = root / DIRECTORY / 'responses' / (request['step'] + '.json')
    if not path.is_file():
        return None
    value = load(path)
    if value.get('requestSha256') != canonical(request) or value.get('authority') != 'none':
        raise ValueError('Proxy response belongs to a different request')
    for name, digest in value['artifacts'].items():
        if proxy_intake.digest(root / name) != digest:
            raise ValueError('Proxy response evidence changed: ' + name)
    return value


def rehearsal_engine(root):
    from specify_cli.workflows.engine import WorkflowEngine
    from specify_cli.workflows.base import StepResult, StepStatus
    from specify_cli.workflows.expressions import evaluate_expression

    class Handoff:
        def __init__(self, kind):
            self.kind = kind

        def execute(self, config, context):
            request = {'runId': context.run_id, 'step': config['id'], 'type': self.kind,
                       'authority': 'none', 'independentLiveWorker': False}
            if self.kind == 'command':
                request.update(command=config['command'], input={key: evaluate_expression(val, context)
                    for key, val in config.get('input', {}).items()})
            else:
                request.update(options=config['options'], show_file=config.get('show_file'),
                               message=evaluate_expression(config.get('message', ''), context))
                # Technical stop gates are blockers, never simulated approvals.
                if not request['show_file']:
                    return StepResult(status=StepStatus.FAILED, output=request, error=request['message'])
                request['reviewSha256'] = proxy_intake.digest(root / request['show_file'])
            response = step_response(root, request)
            if response is None:
                write(root / DIRECTORY / 'pending.json', request)
                return StepResult(status=StepStatus.PAUSED, output=request)
            if self.kind == 'gate' and response['choice'] == 'reject':
                return StepResult(status=StepStatus.PAUSED, output={**request, 'choice': 'reject'})
            output = {**request, 'response': response, 'dispatched': False}
            if self.kind == 'gate':
                output['choice'] = response['choice']
            return StepResult(status=StepStatus.COMPLETED, output=output)

    class RehearsalShell:
        def __init__(self, original):
            self.original = original

        def execute(self, config, context):
            require_active(root, context.run_id)
            if config['id'] == 'complete-bootstrap':
                import governance_state
                governance_state.configure_paths()
                readiness = governance_state.evaluate_readiness()
                if not readiness['eligible']:
                    return StepResult(status=StepStatus.FAILED, output=readiness, error='Proxy bootstrap is not readiness-eligible')
                result = {'status': 'rehearsal-completed', 'authority': 'none',
                          'runId': context.run_id, 'independentLiveWorker': False,
                          'limitation': 'Simulated review decisions; no consumer bootstrap completion authority.'}
                write(root / DIRECTORY / 'result.json', result)
                return StepResult(status=StepStatus.COMPLETED, output=result)
            adapted = dict(config)
            # Native shell steps otherwise depend on a possibly absent `python`
            # command. Bind this adapter to the same installed engine interpreter.
            if adapted.get('run', '').startswith('python '):
                adapted['run'] = '"' + sys.executable + '" ' + adapted['run'][7:]
            if '--approval-mode interactive' in adapted.get('run', ''):
                adapted['run'] = adapted['run'].replace('--approval-mode interactive', '--approval-mode simulated-proxy')
            return self.original.execute(adapted, context)

    class RehearsalEngine(WorkflowEngine):
        def _execute_steps(self, steps, context, state, registry, *, step_offset=0):
            adapted = dict(registry)
            adapted['command'] = Handoff('command')
            adapted['gate'] = Handoff('gate')
            if not isinstance(adapted['shell'], RehearsalShell):
                adapted['shell'] = RehearsalShell(adapted['shell'])
            return super()._execute_steps(steps, context, state, adapted, step_offset=step_offset)

    return RehearsalEngine(root)


def advance(root):
    import workflow_lifecycle
    from specify_cli.workflows.engine import WorkflowDefinition
    with workflow_lifecycle.execution_lock(root), invocation(root) as value:
        engine = rehearsal_engine(root)
        definition = engine.load_workflow('program-kit-bootstrap')
        if canonical(definition.data) != value['workflowSha256']:
            raise ValueError('Installed workflow changed; retain evidence and prepare a fresh rehearsal')
        run_path = root / '.specify/workflows/runs' / value['runId']
        if (run_path / 'state.json').exists():
            if canonical(WorkflowDefinition.from_yaml(run_path / 'workflow.yml').data) != value['workflowSha256']:
                raise ValueError('Saved native workflow changed')
            state = engine.resume(value['runId'])
        else:
            state = engine.execute(definition, inputs={'bootstrap_intake': proxy_intake.INTAKE.as_posix(),
                'integration': 'codex', 'auto_approve_and_ratify': False}, run_id=value['runId'])
        result = {'runId': state.run_id, 'status': state.status.value, 'step': state.current_step_id,
                  'error': state.error, 'authority': 'none', 'independentLiveWorker': False}
        write(root / DIRECTORY / 'native-result.json', result)
        if result['status'] == 'paused':
            result['request'] = pending(root)
        return result


def tool(root, arguments):
    """Run an installed producer helper in the explicitly scoped proxy process tree."""
    request = pending(root)
    if request['type'] != 'command' or not arguments:
        raise ValueError('Producer tools require a paused producer command')
    path = (root / arguments[0]).resolve()
    extensions = (root / '.specify/extensions').resolve()
    if (not path.is_relative_to(extensions) or path.suffix != '.py' or not path.is_file()
            or path.name in {'workflow_lifecycle.py', 'proxy_bootstrap.py'}):
        raise ValueError('Tool must be an installed Python producer helper, not an outer workflow')
    with invocation(root):
        return subprocess.run([sys.executable, str(path), *arguments[1:]], cwd=root, check=False).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'advance', 'respond', 'tool', 'status'])
    parser.add_argument('--note', default='')
    parser.add_argument('--file', action='append', default=[])
    parser.add_argument('--choice')
    args, remaining = parser.parse_known_args()
    root = Path.cwd().resolve()
    try:
        if args.command in {'prepare', 'advance'}:
            import workflow_lifecycle
            if workflow_lifecycle.RunState is None:
                return subprocess.run([str(workflow_lifecycle.installed_interpreter()), str(Path(__file__).resolve()), *sys.argv[1:]], check=False).returncode
        if args.command == 'tool':
            return tool(root, remaining[1:] if remaining[:1] == ['--'] else remaining)
        if remaining:
            raise ValueError('Unexpected arguments')
        if args.command == 'prepare':
            result = prepare(root)
        elif args.command == 'advance':
            result = advance(root)
        elif args.command == 'respond':
            result = respond(root, args.note, args.file, args.choice)
        else:
            result = load(root / DIRECTORY / 'native-result.json')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if result.get('status') == 'failed' else 0
    except (ValueError, OSError) as error:
        print('Proxy bootstrap failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

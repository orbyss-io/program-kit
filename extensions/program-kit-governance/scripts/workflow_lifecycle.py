"""Program Kit workflow-engine integration for bounded, auditable resumption.

Producers, human gates, validators and completion execute as native Spec Kit
steps. Legacy terminal runs remain immutable; their continuations are real
engine runs with explicit lineage, never replacement product intake.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import uuid
import copy
import re
import shlex
import subprocess
from pathlib import Path

import bootstrap_lifecycle as lifecycle
import bootstrap_context
import bootstrap_recovery as recovery
import governance_state as governance
try:
    from specify_cli.workflows.engine import RunState, WorkflowDefinition, WorkflowEngine, validate_workflow
    from specify_cli.workflows.base import RunStatus
except ModuleNotFoundError as error:
    if not error.name.startswith('specify_cli'):
        raise
    RunState = WorkflowDefinition = WorkflowEngine = RunStatus = None


class WorkflowLifecycleError(ValueError):
    pass


from bootstrap_stages import STAGE_STARTS
FINAL_FAILURES = {'readiness', 'validate-readiness-output', 'require-readiness', 'complete-bootstrap'}


def run_directory(root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise WorkflowLifecycleError('Invalid Program Kit workflow run ID')
    return root / '.specify/workflows/runs' / run_id


def installed_interpreter() -> Path:
    """Use the installed Specify launcher interpreter, preserving its dependencies.

    The user's `python` and an isolated uv/pipx `specify` commonly differ. Never
    mix binary site-packages across Python versions or install another toolchain.
    """
    launcher_name = shutil.which('specify')
    if not launcher_name:
        raise WorkflowLifecycleError('The installed Specify launcher is unavailable on PATH')
    launcher = Path(launcher_name).resolve()
    payload = launcher.read_bytes()
    marker = payload.rfind(b'#!') if os.name == 'nt' else 0
    if marker < 0 or payload[marker:marker + 2] != b'#!':
        raise WorkflowLifecycleError('Cannot resolve the installed Specify interpreter from its launcher')
    line = payload[marker + 2:].splitlines()[0].decode('utf-8').strip()
    tokens = shlex.split(line, posix=os.name != 'nt')
    if len(tokens) != 1:
        raise WorkflowLifecycleError('Specify launcher requires an unsupported interpreter wrapper')
    interpreter = Path(tokens[0].strip('"')) if tokens else Path()
    if not interpreter.is_absolute() or not interpreter.is_file():
        raise WorkflowLifecycleError('Specify launcher does not identify an available absolute Python interpreter')
    if RunState is None and interpreter.absolute() == Path(sys.executable).absolute():
        raise WorkflowLifecycleError('The installed Specify interpreter cannot import its workflow engine')
    # Preserve a virtual environment's interpreter symlink on POSIX. Resolving
    # it to the base binary would lose that environment's installed packages.
    return interpreter.absolute()


@contextlib.contextmanager
def execution_lock(root: Path):
    """The OS releases this lock after interruption/process death; no PID probes."""
    path = root / '.specify/workflows/program-kit-lifecycle.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if path.stat().st_size == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise WorkflowLifecycleError('A governed workflow execution is already active') from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def snapshot(root: Path, state: RunState) -> Path:
    directory = root / '.specify/workflows/resumption-history' / state.run_id / uuid.uuid4().hex
    directory.mkdir(parents=True)
    sources = run_directory(root, state.run_id)
    records = {}
    for name in ('state.json', 'workflow.yml', 'log.jsonl', 'inputs.json'):
        source = sources / name
        if source.is_file():
            shutil.copyfile(source, directory / name)
            records[name] = lifecycle.digest(source)
    # Snapshot malformed producer output too: an invalid ledger must not prevent
    # the stage responsible for correcting it from being resumed.
    try:
        artifacts = set(governance.bootstrap_artifacts())
    except (governance.GovernanceStateError, ValueError, KeyError, TypeError):
        artifacts = {p.relative_to(root) for p in (root / 'docs/architecture').rglob('*')
                     if p.is_file() and not any(part in {'bin', 'obj', 'node_modules'} for part in p.parts)}
    # Invalidated evidence remains available even when downstream authority is revoked.
    for relative in {*artifacts, *governance.ASSESSMENT_ARTIFACTS,
                     governance.CONSTITUTION, governance.RATIFICATION,
                     governance.BOOTSTRAP_APPROVAL, governance.BOOTSTRAP_COMPLETION,
                     governance.READINESS_REPORT, lifecycle.RESULT}:
        source = root / relative
        if source.is_file():
            digest = lifecycle.digest(source)
            shutil.copyfile(source, directory / digest)
            records[relative.as_posix()] = digest
    lifecycle.write(directory / 'manifest.json', records)
    return directory


def definition_for(root: Path, run_id: str) -> WorkflowDefinition:
    require_enabled(root)
    definition = WorkflowDefinition.from_yaml(run_directory(root, run_id) / 'workflow.yml')
    if definition.id != 'program-kit-bootstrap':
        raise WorkflowLifecycleError('Only Program Kit bootstrap workflows support this lifecycle')
    errors = validate_workflow(definition)
    if errors:
        raise WorkflowLifecycleError('Saved workflow is invalid: ' + '; '.join(errors))
    return definition


def require_enabled(root: Path, state: RunState | None = None) -> None:
    from proxy_intake import forbid_authority
    forbid_authority(root)
    owner = getattr(state, 'installed_registry_root', None)
    if owner:
        owner_path = Path(owner)
        if not owner_path.is_absolute() or not owner_path.is_dir() or any(p.is_symlink() for p in [owner_path, *owner_path.parents]):
            raise WorkflowLifecycleError('Installed workflow owner is unavailable; cannot safely resume')
        root = owner_path
    registry = root / '.specify/workflows/workflow-registry.json'
    if registry.is_file():
        record = lifecycle.load(registry).get('workflows', {}).get('program-kit-bootstrap', {})
        if not isinstance(record, dict):
            raise WorkflowLifecycleError('Installed Program Kit bootstrap registry entry is corrupted')
        if not record.get('enabled', True):
            raise WorkflowLifecycleError('Installed Program Kit bootstrap workflow is disabled')


def migrate_suffix(root: Path, state: RunState, saved: WorkflowDefinition, restart: str) -> WorkflowDefinition:
    if state.inputs.get('source_run'):
        # Only the known historical readiness suffix may change. The original
        # lineage manifest and approved prefix remain immutable history.
        installed = continuation_definition(root)
        if saved.version == installed.version or restart != 'recovery-readiness':
            return saved
        if (saved.version, installed.version) != ('0.12.0', '0.12.1'):
            raise WorkflowLifecycleError('No reviewed continuation readiness migration for this version')
        recovery.manifest(root, state.inputs['source_run'])
        governance.validate_bootstrap(True, True)
        old_index = next(i for i, s in enumerate(saved.steps) if s['id'] == 'recovery-readiness')
        new_index = next(i for i, s in enumerate(installed.steps) if s['id'] == 'prepare-recovery-readiness')
        old_tail = saved.steps[old_index:]
        new_tail = installed.steps[new_index + 1:]
        if (len(old_tail) != len(new_tail) or old_tail[1:] != new_tail[1:]
                or {k: v for k, v in old_tail[0].items() if k != 'input'}
                != {k: v for k, v in new_tail[0].items() if k != 'input'}):
            raise WorkflowLifecycleError('Unknown saved continuation readiness suffix; maintenance required')
        data = copy.deepcopy(saved.data)
        data['workflow']['version'] = installed.version
        data['steps'] = copy.deepcopy(saved.steps[:old_index]) + copy.deepcopy(installed.steps[new_index:])
        result = WorkflowDefinition(data)
        errors = validate_workflow(result)
        if errors:
            raise WorkflowLifecycleError('Invalid continuation migration: ' + '; '.join(errors))
        destination = run_directory(root, state.run_id) / 'workflow.yml'
        before = lifecycle.digest(destination)
        import yaml
        temporary = destination.with_suffix('.yml.tmp')
        temporary.write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
        temporary.replace(destination)
        state.append_log({'event': 'continuation_readiness_migration', 'from_version': saved.version,
                          'to_version': installed.version, 'previous_sha256': before,
                          'current_sha256': lifecycle.digest(destination)})
        return result
    installed_path = root / '.specify/workflows/program-kit-bootstrap/workflow.yml'
    if not installed_path.is_file():
        return saved
    installed = WorkflowEngine(root).load_workflow('program-kit-bootstrap')
    if saved.version == installed.version:
        return saved
    if (saved.version, installed.version) not in {
        ('0.10.1', '0.11.0'), ('0.10.2', '0.11.0'),
        ('0.10.1', '0.12.0'), ('0.10.2', '0.12.0'), ('0.11.0', '0.12.0'),
    }:
        raise WorkflowLifecycleError(f'No reviewed saved-workflow migration from {saved.version} to {installed.version}')
    old_index = next((i for i, s in enumerate(saved.steps) if s['id'] == restart), None)
    new_index = next((i for i, s in enumerate(installed.steps) if s['id'] == restart), None)
    if old_index is None or new_index is None:
        raise WorkflowLifecycleError('Saved workflow does not expose the supported migration boundary')
    # Retain exactly the successful prefix, replace only the invalidated suffix
    # with the installed, schema-validated workflow's current steps.
    data = copy.deepcopy(installed.data)
    data['steps'] = copy.deepcopy(saved.steps[:old_index]) + copy.deepcopy(installed.steps[new_index:])
    result = WorkflowDefinition(data)
    errors = validate_workflow(result)
    if errors:
        raise WorkflowLifecycleError('Saved-workflow migration is invalid: ' + '; '.join(errors))
    if state.status == RunStatus.PAUSED:
        old_gate = next((s for s in walk_steps(saved.steps) if s['id'] == state.current_step_id), {})
        new_gate = next((s for s in walk_steps(result.steps) if s['id'] == state.current_step_id), {})
        if old_gate.get('type') == 'gate' and any(old_gate.get(k) != new_gate.get(k)
                                                  for k in ('type', 'verdict_input', 'options', 'show_file', 'on_reject')):
            raise WorkflowLifecycleError('Saved review gate contract changed; regenerate and review before migration')
    before = lifecycle.digest(run_directory(root, state.run_id) / 'workflow.yml')
    import yaml
    destination = run_directory(root, state.run_id) / 'workflow.yml'
    temporary = destination.with_suffix('.yml.tmp')
    temporary.write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
    temporary.replace(destination)
    state.append_log({'event': 'saved_workflow_migration', 'from_version': saved.version,
                      'to_version': installed.version, 'restart_step': restart,
                      'previous_sha256': before, 'current_sha256': lifecycle.digest(destination)})
    return result


def all_step_ids(steps):
    return {step['id'] for step in walk_steps(steps) if isinstance(step.get('id'), str)}


def walk_steps(value):
    if isinstance(value, list):
        for child in value:
            yield from walk_steps(child)
    elif isinstance(value, dict):
        if 'id' in value and 'type' in value:
            yield value
        for child in value.values():
            if isinstance(child, (list, dict)):
                yield from walk_steps(child)


@contextlib.contextmanager
def execution_owner(root: Path, run_id: str):
    path = root / '.specify/workflows/lifecycle-executions' / f'{run_id}.json'
    lifecycle.write(path, {'run_id': run_id, 'active': True})
    try:
        yield
    finally:
        state_path = run_directory(root, run_id) / 'state.json'
        if state_path.is_file() and lifecycle.load(state_path)['status'] != 'running':
            lifecycle.write(path, {'run_id': run_id, 'active': False})


def execute_definition(root: Path, definition: WorkflowDefinition, inputs: dict, run_id: str) -> RunState:
    require_enabled(root)
    errors = validate_workflow(definition)
    if errors:
        raise WorkflowLifecycleError('; '.join(errors))
    if run_directory(root, run_id).exists():
        raise WorkflowLifecycleError('Run ID already exists; use resume to preserve its history')
    with execution_owner(root, run_id):
        return WorkflowEngine(root).execute(definition, inputs=inputs, run_id=run_id,
                                            installed_workflow_id='program-kit-bootstrap')


def validate_engine_completion(root: Path) -> None:
    record = lifecycle.load(root / governance.BOOTSTRAP_COMPLETION)
    binding = record.get('workflow')
    if not isinstance(binding, dict):
        raise WorkflowLifecycleError('Project completion has no workflow-engine completion binding')
    directory = run_directory(root, binding['run_id'])
    state = lifecycle.load(directory / 'state.json')
    definition_path = directory / 'workflow.yml'
    last = state.get('step_results', {}).get('complete-bootstrap', {})
    if (state.get('run_id') != binding['run_id'] or state.get('workflow_id') != 'program-kit-bootstrap'
            or state.get('status') != 'completed'
            or last.get('status') != 'completed' or last.get('output', {}).get('exit_code') != 0
            or lifecycle.digest(definition_path) != binding.get('workflow_sha256')):
        raise WorkflowLifecycleError('Bootstrap completion requires the bound workflow engine to finish successfully')
    inputs = lifecycle.load(directory / 'inputs.json')['inputs']
    if binding.get('source_run') != inputs.get('source_run'):
        raise WorkflowLifecycleError('Completion source lineage differs from the native run')
    if binding.get('source_run'):
        source_run = binding['source_run']
        recovery.manifest(root, source_run)
        mapping = lifecycle.load(root / '.specify/workflows/resumptions' / f'{source_run}.json')
        if mapping['continuation_run'] != binding['run_id']:
            raise WorkflowLifecycleError('Completion is not the recorded native continuation')


def complete_step(root: Path, run_id: str, source_run: str | None = None) -> dict:
    state = RunState.load(run_id, root)
    if state.status != RunStatus.RUNNING or state.current_step_id != 'complete-bootstrap':
        raise WorkflowLifecycleError('Completion is an internal running workflow step')
    if source_run != state.inputs.get('source_run'):
        raise WorkflowLifecycleError('Completion cannot change native source lineage')
    governance.complete_bootstrap()
    record = lifecycle.load(root / governance.BOOTSTRAP_COMPLETION)
    record['workflow'] = {'run_id': run_id,
                          'workflow_sha256': lifecycle.digest(run_directory(root, run_id) / 'workflow.yml')}
    if source_run:
        recovery.manifest(root, source_run)
        record['workflow']['source_run'] = source_run
    lifecycle.write(root / governance.BOOTSTRAP_COMPLETION, record)
    return {'recorded': True, 'workflow_run': run_id,
            'valid_only_after_engine_completion': True}


def continuation_definition(root: Path) -> WorkflowDefinition:
    path = Path(__file__).resolve().parent.parent / 'references/bootstrap-continuation.yml'
    definition = WorkflowDefinition.from_yaml(path)
    errors = validate_workflow(definition)
    if errors:
        raise WorkflowLifecycleError('; '.join(errors))
    return definition


def source_ready(root: Path, source_run: str) -> bool:
    recovery.manifest(root, source_run)
    try:
        governance.validate_bootstrap(True, True)
        return bool(lifecycle.verdict(root)['eligible'])
    except (governance.GovernanceStateError, lifecycle.LifecycleError):
        return False


def prepare_recovery_readiness(root: Path, run_id: str, source_run: str) -> dict:
    """Generate the same bounded input/output contract as fresh readiness."""
    recovery.manifest(root, source_run)
    governance.validate_bootstrap(True, True)
    path, payload = bootstrap_context.build_context(root, run_id, 'readiness')
    bootstrap_context.validate_context(root, run_id, 'readiness')
    # Fail before paid dispatch on missing/unreadable declared inputs. Worker-side
    # access is additionally verified by the cross-identity Windows regression.
    for name in payload['reading_policy']['allowed_sources']:
        (root / name).read_bytes()
    return {'context': path.relative_to(root).as_posix(),
            'sha256': lifecycle.digest(path), 'bytes': path.stat().st_size,
            'validation_commands': payload['output_contract']['validation_commands']}


def continuation(root: Path, source: RunState, inputs: dict, *, reuse_prepared_recovery: bool = False) -> RunState:
    mapping_path = root / '.specify/workflows/resumptions' / f'{source.run_id}.json'
    if mapping_path.is_file():
        if reuse_prepared_recovery:
            raise WorkflowLifecycleError('Prepared recovery reuse applies only when creating the continuation; resume the existing continuation without the flag')
        mapping = lifecycle.load(mapping_path)
        if (mapping['source_state_sha256'] != lifecycle.digest(run_directory(root, source.run_id) / 'state.json')
                or mapping['source_workflow_sha256'] != lifecycle.digest(run_directory(root, source.run_id) / 'workflow.yml')):
            raise WorkflowLifecycleError('Preserved source run changed after continuation was created')
        child = mapping['continuation_run']
        if (run_directory(root, child) / 'state.json').is_file():
            return resume_unlocked(root, child, inputs)
    else:
        recovery.prepare(root, source.run_id)
        definition = continuation_definition(root)
        prepared_hash = None
        if reuse_prepared_recovery:
            prepared_hash = recovery.require_prepared_review(root, source.run_id)
            data = copy.deepcopy(definition.data)
            # Only the correction producer is omitted. Proof validation, packet
            # generation, human approval, readiness and completion remain native.
            data['steps'] = [step for step in data['steps'] if step['id'] != 'route-recovery-correction']
            definition = WorkflowDefinition(data)
        child = f'{source.run_id}-r-{uuid.uuid4().hex[:8]}'
        mapping = {'source_run': source.run_id, 'continuation_run': child,
                   'continuation_definition': definition.data,
                   'source_state_sha256': lifecycle.digest(run_directory(root, source.run_id) / 'state.json'),
                   'source_workflow_sha256': lifecycle.digest(run_directory(root, source.run_id) / 'workflow.yml')}
        if prepared_hash:
            mapping['prepared_review_sha256'] = prepared_hash
        lifecycle.write(mapping_path, mapping)
    definition = WorkflowDefinition(mapping['continuation_definition'])
    values = {'source_run': source.run_id, 'integration': source.inputs.get('integration', 'codex')}
    values.update(inputs)
    state = execute_definition(root, definition, values, child)
    if state.status == RunStatus.COMPLETED:
        governance.validate_completion()
        validate_engine_completion(root)
    return state


def resume_unlocked(root: Path, run_id: str, inputs: dict, *, reuse_proven_closure: bool = False, reuse_prepared_recovery: bool = False) -> RunState:
    state = RunState.load(run_id, root)
    require_enabled(root, state)
    definition = definition_for(root, run_id)
    if reuse_prepared_recovery:
        if inputs:
            raise WorkflowLifecycleError('Prepared recovery reuse cannot supply inputs or preapprove its future review gate')
        if (reuse_proven_closure or state.status != RunStatus.FAILED
                or state.current_step_id not in FINAL_FAILURES or state.inputs.get('source_run')):
            raise WorkflowLifecycleError('Prepared recovery reuse requires an original failed approved-bootstrap readiness run')
        return continuation(root, state, inputs, reuse_prepared_recovery=True)
    if reuse_proven_closure:
        if state.status != RunStatus.FAILED or state.current_step_id != 'execute-compatibility-proofs':
            raise WorkflowLifecycleError('Proven closure reuse applies only to a failed compatibility shell step')
        from bootstrap_proof_plan import require_proven_closure
        require_proven_closure(root)
    # Resolve lineage before checking a verdict against the child's actual gate.
    if (root / '.specify/workflows/resumptions' / f'{run_id}.json').is_file():
        return continuation(root, state, inputs)
    for key, value in inputs.items():
        if not key.endswith('_verdict') and value != state.inputs.get(key):
            raise WorkflowLifecycleError(f'Resumption cannot change saved workflow input {key}')
    verdicts = {key: value for key, value in inputs.items() if key.endswith('_verdict') and value}
    current = state.step_results.get(state.current_step_id, {})
    gate = next((step for step in walk_steps(definition.steps) if step.get('id') == state.current_step_id), {})
    if verdicts and (state.status != RunStatus.PAUSED or current.get('type') != 'gate'
                     or set(verdicts) != {gate.get('verdict_input')}):
        raise WorkflowLifecycleError('A verdict may be supplied only at the actual paused review gate, never ahead of regenerated artifacts')
    if state.status == RunStatus.COMPLETED:
        governance.validate_completion()
        validate_engine_completion(root)
        return state
    if state.status == RunStatus.ABORTED:
        # prepare() accepts only the exact historical technical abort signature;
        # semantic user rejection remains terminal.
        return continuation(root, state, inputs)
    if state.status == RunStatus.RUNNING:
        owner_path = root / '.specify/workflows/lifecycle-executions' / f'{run_id}.json'
        if not owner_path.is_file() or lifecycle.load(owner_path) != {'run_id': run_id, 'active': True}:
            raise WorkflowLifecycleError('Running workflow has no released lifecycle owner; its liveness must not be assumed')
        # Acquiring this integration's exclusive OS lock proves its owner ended.
        archived = snapshot(root, state)
        state.status = RunStatus.FAILED
        state.error = 'Previous workflow execution owner ended before a terminal state was saved'
        state.append_log({'event': 'execution_owner_lost', 'snapshot': str(archived)})
        state.save()
    if state.status == RunStatus.FAILED and state.current_step_id in FINAL_FAILURES and not state.inputs.get('source_run'):
        return continuation(root, state, inputs)
    if state.status not in (RunStatus.PAUSED, RunStatus.FAILED):
        raise WorkflowLifecycleError(f'Cannot resume {state.status.value}')
    if state.status == RunStatus.PAUSED and not state.inputs.get('source_run'):
        installed = WorkflowEngine(root).load_workflow('program-kit-bootstrap')
        if installed.version != definition.version:
            archived = snapshot(root, state)
            restart = definition.steps[state.current_step_index]['id']
            previous_ids = all_step_ids(definition.steps[state.current_step_index:])
            definition = migrate_suffix(root, state, definition, restart)
            invalidated = previous_ids | all_step_ids(definition.steps[state.current_step_index:])
            state.step_results = {key: value for key, value in state.step_results.items() if key not in invalidated}
            state.inputs = WorkflowEngine(root)._resolve_inputs(definition, state.inputs)
            state.append_log({'event': 'paused_workflow_migration', 'snapshot': str(archived),
                              'invalidated_steps': sorted(invalidated), 'restart_step': restart})
            state.save()
    if state.status == RunStatus.FAILED:
        restart = STAGE_STARTS.get(state.current_step_id, state.current_step_id)
        if state.current_step_id.startswith('require-') and state.current_step_id.endswith('-answers'):
            from bootstrap_handoff import retry_stage
            from bootstrap_stages import STAGES
            stage = state.current_step_id.removeprefix('require-').removesuffix('-answers')
            owner = retry_stage(root, run_id, stage, completing=True)
            if owner:
                restart = STAGES[owner]['restart']
        if state.current_step_id.startswith('require-') and state.current_step_id.endswith('-handoff'):
            from bootstrap_stages import STAGES
            from bootstrap_handoff import retry_stage
            stage = state.current_step_id.removeprefix('require-').removesuffix('-handoff')
            if stage in STAGES:
                owner = retry_stage(root, run_id, stage)
                if owner:
                    restart = STAGES[owner]['restart']
        if state.inputs.get('source_run'):
            if state.current_step_id == 'recovery-require-ready':
                verdict = lifecycle.verdict(root)
                if {item['id'] for item in verdict.get('blockers', [])} == {'READINESS-CURRENT-EVIDENCE'}:
                    # This is a producer-input failure, not a request to redraft
                    # already-approved architecture or rerun compatibility proofs.
                    restart = 'prepare-recovery-readiness'
            if restart == 'prepare-recovery-readiness':
                recovery.manifest(root, state.inputs['source_run'])
                governance.validate_bootstrap(True, True)
                if not any(s['id'] == restart for s in definition.steps):
                    restart = 'recovery-readiness'  # migrate the historical suffix below
        if reuse_proven_closure:
            restart = 'execute-compatibility-proofs'
        starts = [index for index, step in enumerate(definition.steps) if step['id'] == restart]
        if not starts:
            # A nested gate/acceptance failure must return to its owning stage,
            # never silently continue from an unrelated top-level offset.
            raise WorkflowLifecycleError(f'No supported producer restart for {state.current_step_id}; maintenance required')
        archived = snapshot(root, state)
        invalidated = all_step_ids(definition.steps[starts[0]:])
        definition = migrate_suffix(root, state, definition, restart)
        index = starts[0]
        invalidated.update(all_step_ids(definition.steps[index:]))
        state.step_results = {key: value for key, value in state.step_results.items() if key not in invalidated}
        state.current_step_index = index
        state.current_step_id = definition.steps[index]['id']
        for name in ('assessment_verdict', 'constitution_verdict', 'bootstrap_verdict', 'recovery_verdict'):
            if name in state.inputs:
                state.inputs[name] = ''
        if 'auto_approve_and_ratify' in state.inputs:
            state.inputs['auto_approve_and_ratify'] = False
        state.inputs = WorkflowEngine(root)._resolve_inputs(definition, state.inputs)
        # Keep approved prefix authority. Downstream completion is no longer valid.
        if restart in {'prepare-assessment-context', 'prepare-research-context', 'require-research-handoff'}:
            # A producer must be able to correct its own decisions before a fresh
            # review. The original approval is preserved in the snapshot above.
            (root / governance.ASSESSMENT_APPROVAL).unlink(missing_ok=True)
            (root / governance.BOOTSTRAP_APPROVAL).unlink(missing_ok=True)
        for relative in (governance.BOOTSTRAP_COMPLETION, lifecycle.RESULT):
            (root / relative).unlink(missing_ok=True)
        state.append_log({'event': 'stage_resumption', 'restart_step': state.current_step_id,
                          'invalidated_steps': sorted(invalidated), 'snapshot': str(archived),
                          'saved_workflow_sha256': lifecycle.digest(run_directory(root, run_id) / 'workflow.yml')})
        state.save()
    if (state.status == RunStatus.PAUSED and state.inputs.get('source_run')
            and state.current_step_id == 'recovery-readiness'):
        prepare_recovery_readiness(root, run_id, state.inputs['source_run'])
    with execution_owner(root, run_id):
        result = WorkflowEngine(root).resume(run_id, inputs=inputs or None)
    if result.status == RunStatus.COMPLETED:
        governance.validate_completion()
        validate_engine_completion(root)
    return result


def resume(root: Path, run_id: str, inputs: dict | None = None, *, reuse_proven_closure: bool = False, reuse_prepared_recovery: bool = False) -> RunState:
    with execution_lock(root):
        return resume_unlocked(root, run_id, inputs or {}, reuse_proven_closure=reuse_proven_closure,
                               reuse_prepared_recovery=reuse_prepared_recovery)


def reopen(root: Path, run_id: str, stage: str) -> dict:
    """Explicit operator reopens decision authority without dispatching a producer."""
    from bootstrap_stages import STAGES
    if stage not in {'assessment', 'research', 'architecture'}:
        raise WorkflowLifecycleError('Reopen the owning assessment, research or architecture stage')
    with execution_lock(root):
        state = RunState.load(run_id, root)
        if state.status not in {RunStatus.FAILED, RunStatus.PAUSED, RunStatus.COMPLETED} or state.inputs.get('source_run'):
            raise WorkflowLifecycleError('Reopen requires a stopped primary bootstrap run')
        definition = WorkflowDefinition.from_yaml(run_directory(root, run_id) / 'workflow.yml')
        restart = 'require-research-handoff' if stage == 'research' else STAGES[stage]['restart']
        matches = [i for i, step in enumerate(definition.steps) if step['id'] == restart]
        if not matches:
            raise WorkflowLifecycleError('This historical workflow has no supported decision handoff; preserve it and start a new trial')
        archived = snapshot(root, state)
        response = run_directory(root, run_id) / 'decision-responses.json'
        if response.is_file():
            shutil.copyfile(response, archived / response.name)
            response.unlink()
        index = matches[0]
        invalidated = all_step_ids(definition.steps[index:])
        state.step_results = {k: v for k, v in state.step_results.items() if k not in invalidated}
        state.current_step_index, state.current_step_id = index, restart
        state.status, state.error = RunStatus.FAILED, 'Operator reopened ' + stage + ' decisions'
        for name in ('assessment_verdict', 'constitution_verdict', 'bootstrap_verdict'):
            state.inputs[name] = ''
        state.inputs['auto_approve_and_ratify'] = False
        for relative in (governance.BOOTSTRAP_APPROVAL, governance.BOOTSTRAP_COMPLETION, lifecycle.RESULT):
            (root / relative).unlink(missing_ok=True)
        if stage in {'assessment', 'research'}:
            (root / governance.ASSESSMENT_APPROVAL).unlink(missing_ok=True)
        state.append_log({'event': 'operator_reopened_decisions', 'stage': stage, 'snapshot': str(archived)})
        state.save()
        return {'run_id': run_id, 'status': 'reopened', 'stage': stage, 'next': 'Record corrected answers, then resume the same run'}


def step(root: Path, action: str, run_id: str, source_run: str | None, verdict: str | None) -> dict:
    state = RunState.load(run_id, root)
    expected = {'complete': 'complete-bootstrap', 'verify-source': 'verify-recovery-source',
                'review': 'recovery-review', 'accept': 'recovery-accept',
                'synchronize': 'recovery-synchronize', 'evaluate': 'recovery-evaluate',
                'readiness-context': 'prepare-recovery-readiness'}
    if (state.status != RunStatus.RUNNING or state.current_step_id != expected.get(action)
            or state.inputs.get('source_run') != source_run):
        raise WorkflowLifecycleError('This helper executes only as its matching native workflow step')
    if action == 'complete':
        return complete_step(root, run_id, source_run)
    if not source_run:
        raise WorkflowLifecycleError('Continuation steps require source-run lineage')
    if action == 'verify-source':
        return {'reuse_approval': source_ready(root, source_run)}
    if action == 'review':
        value = recovery.review(root, source_run)
        approved = lifecycle.load(root / governance.BOOTSTRAP_APPROVAL)
        value['needs_approval'] = approved['artifacts'] != recovery.basis()
        return value
    if action == 'accept':
        return recovery.accept(root, source_run, verdict)
    if action == 'synchronize':
        return recovery.synchronize(root, source_run)
    if action == 'evaluate':
        return recovery.evaluate(root, source_run)
    if action == 'readiness-context':
        return prepare_recovery_readiness(root, run_id, source_run)
    raise WorkflowLifecycleError(f'Unknown internal step {action}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'resume', 'reopen', 'step', 'validate-completion'])
    parser.add_argument('action', nargs='?')
    parser.add_argument('--run-id')
    parser.add_argument('--source-run')
    parser.add_argument('--verdict')
    parser.add_argument('--stage', choices=['assessment', 'research', 'architecture'])
    parser.add_argument('--input', action='append', default=[])
    parser.add_argument('--reuse-proven-closure', action='store_true', help='Resume repaired compatibility proofs without repeating their paid authoring stage; requires current passing evidence for every planned probe')
    parser.add_argument('--reuse-prepared-recovery', action='store_true', help='Create an approved-bootstrap continuation from a current prepared recovery review and passing proofs, retaining the human approval gate')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        if (args.reuse_proven_closure or args.reuse_prepared_recovery) and args.command != 'resume':
            raise WorkflowLifecycleError('Recovery reuse flags require resume')
        if RunState is None and args.command != 'validate-completion':
            return subprocess.run([str(installed_interpreter()), str(Path(__file__).resolve()), *sys.argv[1:]], check=False).returncode
        governance.configure_paths()
        with contextlib.redirect_stdout(io.StringIO()) if args.command == 'step' else contextlib.nullcontext():
            if args.command == 'reopen':
                value = reopen(root, args.run_id, args.stage)
            elif args.command == 'step':
                value = step(root, args.action, args.run_id, args.source_run, args.verdict)
            elif args.command == 'validate-completion':
                governance.validate_completion()
                validate_engine_completion(root)
                value = {'status': 'completed', 'engine_verified': True}
            else:
                inputs = dict(item.split('=', 1) for item in args.input)
                if args.command == 'resume':
                    state = resume(root, args.run_id, inputs, reuse_proven_closure=args.reuse_proven_closure,
                                   reuse_prepared_recovery=args.reuse_prepared_recovery)
                else:
                    with execution_lock(root):
                        require_enabled(root)
                        definition = WorkflowEngine(root).load_workflow('program-kit-bootstrap')
                        state = execute_definition(root, definition, inputs, args.run_id or uuid.uuid4().hex[:8])
                        if state.status == RunStatus.COMPLETED:
                            governance.validate_completion()
                            validate_engine_completion(root)
                value = {'run_id': state.run_id, 'status': state.status.value,
                         'current_step': state.current_step_id, 'error': state.error}
                if state.status == RunStatus.FAILED:
                    from compatibility_diagnostics import sanitize
                    output = state.step_results.get(state.current_step_id, {}).get('output', {})
                    detail = output.get('stderr') or output.get('stdout')
                    if detail:
                        value['diagnostic'] = sanitize(str(detail))[-4000:]
                    value['evidence'] = str(run_directory(root, state.run_id) / 'state.json')
        print(json.dumps(value))
        return 0 if args.command in {'step', 'reopen'} or value.get('status', 'completed') == 'completed' else 2
    except (ValueError, OSError, KeyError, governance.GovernanceStateError, lifecycle.LifecycleError, bootstrap_context.ContextError) as error:
        print(f'Program Kit workflow lifecycle: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

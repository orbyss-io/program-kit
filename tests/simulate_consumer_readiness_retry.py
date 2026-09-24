"""Opt-in deterministic retry of a copied consumer. Never dispatches a coding agent."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = args.project.resolve()
    output = args.output.resolve()
    project = Path(tempfile.gettempdir()) / ('pkrc-' + uuid.uuid4().hex[:8])
    project.mkdir()
    for name in ('docs', '.specify', '.agents', 'acceptance'):
        if (original / name).is_dir():
            shutil.copytree(original / name, project / name,
                ignore=shutil.ignore_patterns('__pycache__', 'resumption-history', 'bin', 'obj', 'node_modules', 'cache', 'scratch-*'))
    schema = Path('.program-kit/cache/json-schema')
    shutil.copytree(original / schema, project / schema)
    os.chdir(project)
    sys.path.insert(0, str(project / '.specify/extensions/program-kit-governance/scripts'))
    import workflow_lifecycle as workflow
    import governance_state as governance
    import bootstrap_lifecycle as lifecycle
    from bootstrap_proof_plan import require_proven_closure
    from specify_cli.workflows.steps.command import CommandStep
    from specify_cli.workflows.steps.shell import ShellStep
    from specify_cli.workflows.base import RunStatus

    governance.configure_paths()
    mapping = lifecycle.load(project / '.specify/workflows/resumptions' / f'{args.source_run}.json')
    child = mapping['continuation_run']
    old = lifecycle.load(workflow.run_directory(project, child) / 'state.json')
    approval = (project / governance.BOOTSTRAP_APPROVAL).read_bytes()
    source_state = (workflow.run_directory(project, args.source_run) / 'state.json').read_bytes()
    require_proven_closure(project)
    dispatches = []
    terminal_output = []
    original_shell = ShellStep.execute

    def shell(self, config, context):
        config = copy.deepcopy(config)
        config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
        return original_shell(self, config, context)

    def producer(self, command, integration, model, arguments, context):
        assert command == 'speckit.program-kit-governance.readiness', command
        dispatches.append(command)
        match = re.search(r'Read (\S+/program-kit-context/readiness.json) first', arguments)
        assert match, 'Missing current context'
        brief = lifecycle.load(project / match[1])
        assert brief['run_id'] == child
        for relative in brief['reading_policy']['allowed_sources']:
            (project / relative).read_bytes()
        index = project / brief['evidence_index']['path']
        assert lifecycle.digest(index) == brief['evidence_index']['sha256']
        for artifact in lifecycle.load(index)['artifacts']:
            assert lifecycle.digest(project / artifact['path']) == artifact['sha256']
        (project / governance.READINESS_REPORT).write_text(
            '**Status**: READY\n\nSIMULATED readiness producer for deterministic retry validation only. '
            'This is not a live architecture assessment.\n', encoding='utf-8')
        batch = brief['output_contract']['validation_commands'][0].split()
        batch[0] = sys.executable
        result = subprocess.run(batch, capture_output=True, text=True, encoding='utf-8')
        assert result.returncode == 0, result.stderr
        assert lifecycle.load(project / lifecycle.RESULT)['eligible']
        terminal_output.append(result.stdout.strip())
        return {'exit_code': 0, 'stdout': 'Explicitly simulated producer', 'stderr': ''}

    with patch.object(ShellStep, 'execute', shell), patch.object(CommandStep, '_try_dispatch', producer), \
            patch.object(sys.stdin, 'isatty', return_value=False):
        state = workflow.resume(project, args.source_run)
    assert state.status == RunStatus.COMPLETED, (state.current_step_id, state.error)
    assert len(dispatches) == 1
    assert (project / governance.BOOTSTRAP_APPROVAL).read_bytes() == approval
    assert (workflow.run_directory(project, args.source_run) / 'state.json').read_bytes() == source_state
    prefix = {key: value for key, value in old['step_results'].items()
              if key not in {'recovery-readiness', 'recovery-evaluate', 'recovery-require-ready', 'complete-bootstrap'}}
    assert all(state.step_results[key] == value for key, value in prefix.items())
    workflow.validate_engine_completion(project)
    require_proven_closure(project)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'kind': 'isolated-native-retry-with-simulated-readiness', 'project': str(project),
              'source_run': args.source_run, 'continuation': child, 'status': state.status.value,
              'paid_sessions_started': 0, 'simulated_producer_calls': len(dispatches),
              'preserved_prefix_steps': len(prefix), 'approval_unchanged': True,
              'original_run_unchanged': True, 'passing_proofs_preserved': True,
              'terminal_output': terminal_output, 'completion_binding_valid': True}
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

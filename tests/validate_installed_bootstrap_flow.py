"""All shipped bootstrap steps, real shell validators, fictional authoring/reviews.

This tests mechanical composition, not the quality of an agent's reasoning. No
agent runs. External provider integration has separate executed inventory checks.
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import validate_bootstrap_lifecycle as fixture
import workflow_lifecycle as lifecycle
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.steps.command import CommandStep
from specify_cli.workflows.steps.shell import ShellStep

ROOT = Path(__file__).resolve().parents[1]


def scenario(mode):
    previous = Path.cwd()
    version = (ROOT / 'VERSION').read_text().strip()
    with tempfile.TemporaryDirectory(prefix='pk-installed-flow-') as directory:
        root = Path(directory).resolve()
        os.chdir(root)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fixture.setup(root)
            fixture.fixture.write_installation(root, version)
            decisions_path = root / 'docs/architecture/bootstrap-decisions.json'
            decisions = fixture.lifecycle.load(decisions_path)
            decisions['default_profile']['version'] = version
            fixture.lifecycle.write(decisions_path, decisions)
            # Replace test-helper source copies with the real distribution payload.
            # Only these newly created, owned fixture directories can be removed.
            for name in ('governance', 'building-blocks', 'dotnet'):
                target = root / '.specify/extensions' / ('program-kit-' + name)
                if root not in target.resolve().parents:
                    raise AssertionError('Fixture path escaped its owned directory')
                shutil.rmtree(target)
                with zipfile.ZipFile(ROOT / 'artifacts' / f'program-kit-{name}-{version}.zip') as archive:
                    archive.extractall(target)
            installed = root / '.specify/workflows/program-kit-bootstrap'
            with zipfile.ZipFile(ROOT / 'artifacts' / f'program-kit-bootstrap-{version}.zip') as archive:
                archive.extractall(installed)
            for name in ('bootstrap-assessment-approval.json', 'bootstrap-approval.json', 'bootstrap-completion.json'):
                (root / '.specify/governance' / name).unlink(missing_ok=True)
            (root / '.specify/memory/constitution-ratification.json').unlink(missing_ok=True)
            fixture.lifecycle.write(root / '.specify/integration.json', {'default_integration': 'claude'})
            fixture.lifecycle.write(root / 'docs/architecture/bootstrap-proof-plan.json',
                                    {'schemaVersion': 1, 'probes': [], 'readyWhenProven': []})
            # Bind the fictional confirmed intake once, before workflow execution.
            intake_path = root / 'docs/architecture/bootstrap-intake.json'
            intake = fixture.lifecycle.load(intake_path)
            for record in intake['artifacts'].values():
                path = root / record['path']
                record.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
            fixture.lifecycle.write(intake_path, intake)
            assessment_path = root / 'docs/architecture/bootstrap-assessment.md'
            assessment = assessment_path.read_bytes()
            definition = WorkflowDefinition.from_yaml(installed / 'workflow.yml')
            run_id = 'installed-' + mode
            calls, shells = [], []
            original = ShellStep.execute

            def shell(self, config, context):
                config = copy.deepcopy(config)
                config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
                shells.append(config['id'])
                result = original(self, config, context)
                if result.status.value == 'failed':
                    print(mode, config['id'], result.output, flush=True)
                return result

            def dispatch(self, command, integration, model, args, context):
                calls.append(command)
                allowed = {'speckit.constitution'} | {'speckit.program-kit-governance.' + name for name in
                           ('assessment', 'research', 'architecture', 'tooling', 'roadmap', 'bootstrap-closure')}
                if command not in allowed:
                    raise AssertionError('No fixture author for new command: ' + command)
                if command.endswith('.assessment'):
                    if mode == 'resume' and calls.count(command) == 1:
                        assessment_path.unlink()
                    else:
                        assessment_path.write_bytes(assessment)
                if command == 'speckit.constitution':
                    fixture.governance.begin()
                    (root / fixture.governance.CONSTITUTION).write_text(fixture.fixture.constitution(), encoding='utf-8')
                if command.endswith('.research'):
                    brief = fixture.lifecycle.load(root / f'.specify/workflows/runs/{run_id}/program-kit-context/research.json')
                    decisions_path = root / 'docs/architecture/bootstrap-decisions.json'
                    decisions = fixture.lifecycle.load(decisions_path)
                    decisions['toolchain'] = {'source': 'program-kit-default', 'pins': brief['managed_profile_pins']['pins'], 'override_reason': ''}
                    fixture.lifecycle.write(decisions_path, decisions)
                if command.endswith('.architecture'):
                    fixture.fixture.write_bootstrap_artifacts(fixture.governance, root, fixture.governance._load_architecture_module())
                    choices = fixture.lifecycle.load(root / 'docs/architecture/bootstrap-decisions.json')['choices']
                    baseline = root / 'docs/architecture/decisions/bootstrap-baseline.md'
                    baseline.write_text(baseline.read_text().replace('program-kit-standard 0.3.1', 'program-kit-standard ' + version) + ''.join('\n' + c['id'] + ': ' + c['decision'] + '\n' for c in choices), encoding='utf-8')
                if command.endswith('.roadmap'):
                    items = []
                    if mode in ('deferred', 'discovery'):
                        items = [fixture.item(trigger='before-implementation' if mode == 'deferred' else 'before-specification')]
                        roadmap = root / fixture.governance.ROADMAP
                        roadmap.write_text(roadmap.read_text().replace('**Status**: Ready', '**Status**: Candidate'), encoding='utf-8')
                    fixture.ledger(root, items)
                return {'exit_code': 0, 'stdout': 'Fictional fixture author; no coding agent started.', 'stderr': ''}

            inputs = {'bootstrap_intake': 'docs/architecture/bootstrap-intake.json', 'integration': 'claude',
                      'auto_approve_and_ratify': True}
            with patch.object(ShellStep, 'execute', shell), patch.object(CommandStep, '_try_dispatch', dispatch), patch.object(sys.stdin, 'isatty', return_value=False):
                state = WorkflowEngine(root).execute(definition, inputs, run_id=run_id)
                if mode == 'resume':
                    assert state.status.value == 'failed' and state.current_step_id == 'validate-assessment-output', state.error
                    assert not (root / fixture.governance.BOOTSTRAP_COMPLETION).exists()
                    state = lifecycle.resume(root, run_id)
                    reviews = {'review-assessment': ('assessment_verdict', 'approve'),
                               'review-constitution': ('constitution_verdict', 'ratify'),
                               'review-bootstrap': ('bootstrap_verdict', 'approve')}
                    for _ in range(3):
                        if state.status.value != 'paused':
                            break
                        key, verdict = reviews[state.current_step_id]
                        state = lifecycle.resume(root, run_id, {key: verdict})
                assert state.status.value == 'completed', (mode, state.current_step_id, state.error)
            lifecycle.validate_engine_completion(root)
            assert 'complete-bootstrap' in shells
            assert all(step['id'] in state.step_results for step in definition.data['steps'])
            if mode in ('deferred', 'discovery'):
                items = fixture.lifecycle.load(root / fixture.lifecycle.LEDGER)['prerequisites']
                assert items and all(i['status'] == 'open' for i in items)
                phase = 'implementation' if mode == 'deferred' else 'specification'
                eligibility = fixture.lifecycle.phase_eligibility(root,
                    fixture.governance.roadmap_records(root / fixture.governance.ROADMAP), 'SPEC-001', phase)
                assert not eligibility['eligible'], 'Completion must not waive the deferred phase obligation'
            print(f'Installed workflow {mode}: completed; real shell validations, fictional authoring/reviews.', flush=True)
        finally:
            os.chdir(previous)


def main():
    for mode in ('complete', 'deferred', 'discovery', 'resume'):
        scenario(mode)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

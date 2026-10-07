"""Provide applicable knowledge; ordinary engineering commands enforce completion.

The historical evidence reader is historical_phase_evidence.py. This command
never creates feature dossiers or consumes bootstrap/ratification receipts.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import subprocess
from pathlib import Path
from feature_context import context


_engineering = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(_engineering))
from test_results import test_results, require, text
from repository_architecture import validate_planned

def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Feature path escapes repository')
    return path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def catalog():
    return read(Path(__file__).resolve().parents[1] / 'references/phase-obligations.json')


def intent(root, feature, phase='implementation', affected_paths=()):
    return context(root, feature, phase, affected_paths)


def model(root, feature, phase='planning', affected_paths=()):
    tags = intent(root, feature, phase, affected_paths)
    registry_phase = 'after-plan' if phase == 'tasks' else phase
    return {'schemaVersion': 1, 'feature': feature.relative_to(root).as_posix(),
            'requirements': [r for r in catalog()['requirements']
                             if r['when'] in tags and registry_phase in r['phases']
                             and (not r.get('mechanism') or r['mechanism'] in tags)]}


def project(root, feature, phase, affected_paths=()):
    """Return regenerable context without writing into the feature's design files."""
    return model(root, feature, phase, affected_paths)


def render(value, phase, detailed=False):
    lines = [f'# Applicable guidance: {phase}', '',
             'Record concrete decisions and tests in plan.md/tasks.md. No separate review receipts are required.',
             'Conditional guidance applies only when its stated conditions hold.',
             'Use these summaries first. Section pointers are optional focused lookup, not a reading checklist.',
             'Use --only <id> for its example, diagnostics and focused reference sections.', '']
    actions = {
        'planning': 'Make design decisions and name their cheapest reliable tests. No application tests run during planning.',
        'after-plan': 'Review changed design decisions and the planned graph. Carry real-provider tests into the tasks.',
        'tasks': 'Create test tasks before their corresponding behavior and carry prerequisites. Do not execute proofs while drafting.',
        'after-tasks': 'Check the finalized graph and run normal read-only analyze once. Drafting is not implementation.',
        'implementation': 'Use focused red/green/refactor tests. Progress saves and resumes are not full acceptance boundaries.',
        'delivery': 'Run complete acceptance at feature/domain closure or formal review handoff, then review changed responsibilities.',
    }
    lines += [actions[phase], '']
    for rule in value['requirements']:
        guidance = rule['requirement'] if detailed else rule.get('guidance', {}).get(phase, rule['requirement'])
        lines += [f"## {rule['id']}", guidance,
                  'Enforcement: ' + rule['enforcement']['kind']]
        if detailed:
            lines.append('Example: ' + rule['example'])
        if detailed and rule['enforcement'].get('diagnostics'):
            lines.append('Compiler diagnostics: ' + ', '.join(rule['enforcement']['diagnostics']))
        for source, sections in rule.get('sections', {}).items() if detailed else ():
            lines.append('Focused lookup: ' + source + ': ' + '; '.join(sections))
        lines.append('')
    return '\n'.join(lines)


def check(root, feature, phase, affected_paths=()):
    if phase in ('after-plan', 'after-tasks', 'implementation'):
        validate_planned_architecture(root, feature)
    if phase == 'delivery':
        execute(root, feature)
    return model(root, feature, phase, affected_paths)


def validate_planned_architecture(root, feature):
    """Fail on incompatible planned ownership before affected source/build work."""
    path = root / 'eng/architecture.json'
    if not path.is_file():
        declarations = '\n'.join((feature / name).read_text(encoding='utf-8')
            for name in ('plan.md', 'research.md', 'data-model.md') if (feature / name).is_file())
        if '.csproj' in declarations:
            raise ValueError('Declare the planned compilation graph in eng/architecture.json before affected implementation')
        return
    validate_planned(root, read(path))


def execute(root, feature, scope='Acceptance', changed_from=None):
    command = root / 'eng/Invoke-RepositoryVerification.ps1'
    if not command.is_file():
        raise ValueError('Application verification is not configured. Supply eng/Invoke-RepositoryVerification.ps1 or run the project build/tests; no completion claim is established.')
    import shutil
    executable = shutil.which('pwsh') or shutil.which('powershell')
    if not executable:
        raise ValueError('PowerShell is required by the configured engineering command')
    from datetime import datetime, timezone
    import uuid
    from execution_history import cleanup
    directory = root / 'artifacts/program-kit/runs' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    marker = directory / 'run.json'
    value = {'schemaVersion':1, 'owner':'program-kit', 'status':'running',
             'scope':scope, 'feature':feature.relative_to(root).as_posix(),
             'startedAtUtc':datetime.now(timezone.utc).isoformat(),
             'command':[executable, '-NoProfile', '-File', str(command)]}
    if scope != 'Acceptance':
        value['command'] += ['-Scope', scope, '-FeatureDirectory', feature.relative_to(root).as_posix()]
        if changed_from:
            value['command'] += ['-ChangedFrom', changed_from]
    marker.write_text(json.dumps(value))
    try:
        with (directory / 'stdout.log').open('w',encoding='utf-8') as out, (directory / 'stderr.log').open('w',encoding='utf-8') as err:
            result = subprocess.run(value['command'], cwd=root, stdout=out, stderr=err, timeout=900)
    except (OSError, subprocess.SubprocessError) as error:
        value.update(status='failed', diagnostic=str(error), finishedAtUtc=datetime.now(timezone.utc).isoformat())
        marker.write_text(json.dumps(value))
        raise
    value.update(status='completed' if result.returncode == 0 else 'failed', exitCode=result.returncode,
                 finishedAtUtc=datetime.now(timezone.utc).isoformat())
    marker.write_text(json.dumps(value))
    cleanup(root)
    print('Engineering logs: ' + directory.relative_to(root).as_posix())
    if result.returncode:
        raise ValueError(f'Application verification failed ({result.returncode}); correct the reported code/configuration issue and rerun eng/Invoke-RepositoryVerification.ps1')
    return {'applicationChecksPassed': scope == 'Acceptance', 'scopedChecksPassed': True,
            'acceptanceEstablished': scope == 'Acceptance', 'releaseReadinessEstablished': False}


def finish(root, feature, handoff=False):
    """A task checkpoint is progress; only actual closure/handoff runs acceptance."""
    tasks = feature / 'tasks.md'
    require(tasks.is_file(), 'Locate tasks.md before claiming feature closure')
    from task_draft import load
    content, draft_state = load(tasks)
    pending = len(re.findall(r'^\s*-\s+\[ \]\s+', content, re.M))
    draft = '> Draft:' in content or bool(draft_state and draft_state.get('status') != 'complete')
    if not handoff and (pending or draft):
        return {'status': 'in-progress', 'pendingTasks': pending, 'draft': draft,
                'applicationChecksPassed': False, 'acceptanceEstablished': False,
                'instruction': 'Save progress. Run only affected tests for changed code; resume the remaining tasks. No full acceptance at this checkpoint.'}
    require(handoff or bool(re.search(r'^\s*-\s+\[[xX]\]\s+', content, re.M)),
            'Feature closure requires completed tasks or an explicit formal handoff')
    return execute(root, feature)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('project', 'check', 'verify', 'finish'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phase', default='planning', choices=('planning','after-plan','tasks','after-tasks','implementation','delivery'))
    parser.add_argument('--only', help='Return one applicable obligation for a focused follow-up')
    parser.add_argument('--affected-path', action='append', default=[], help='Focus implementation source lookup on these paths')
    parser.add_argument('--scope', choices=('Acceptance','Affected'), default='Acceptance')
    parser.add_argument('--changed-from', help='Git baseline for Affected verification including worktree and untracked changes')
    parser.add_argument('--handoff', action='store_true', help='Explicit formal review handoff, including intentionally unfinished work')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = inside(root, args.feature_dir)
    try:
        affected = [inside(root, p).relative_to(root).as_posix() for p in args.affected_path]
        result = (finish(root, feature, args.handoff) if args.command == 'finish' else
                  execute(root, feature, args.scope, changed_from=args.changed_from) if args.command == 'verify' else
                  project(root, feature, args.phase, affected) if args.command == 'project' else
                  check(root, feature, args.phase, affected))
        if args.only and args.command not in ('verify', 'finish'):
            result['requirements'] = [r for r in result['requirements'] if r['id'] == args.only]
            if not result['requirements']:
                raise ValueError('Requested obligation is not applicable in this phase')
        print(json.dumps(result) if args.command in ('verify', 'finish') else render(result, args.phase, bool(args.only)))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

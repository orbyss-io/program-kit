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


_engineering = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(_engineering))
from test_results import test_results, require, text

def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Feature path escapes repository')
    return path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def catalog():
    return read(Path(__file__).resolve().parents[1] / 'references/phase-obligations.json')


def intent(root, feature):
    # Plan intent makes guidance available before source exists. Engineering
    # configuration/source establishes applicability again during implementation.
    texts = [p.read_text(encoding='utf-8') for p in feature.glob('*.md')]
    declared = '\n'.join(texts)
    candidates = list((root / 'src').rglob('*.csproj')) + list(feature.rglob('*.csproj'))
    projects = [p for p in candidates if p.relative_to(root).as_posix() in declared
                or p.parent.relative_to(root).as_posix() in declared]
    for p in projects:
        texts.append(p.read_text(encoding='utf-8'))
        texts.extend(s.read_text(encoding='utf-8') for s in p.parent.rglob('*.cs')
                     if not {'bin', 'obj'} & set(s.parts))
    for package in (root / 'src').rglob('package.json'):
        if package.relative_to(root).as_posix() in declared or package.parent.relative_to(root).as_posix() in declared:
            texts.append(package.read_text(encoding='utf-8'))
    content = '\n'.join(texts).lower()
    content = re.sub(r'\bno (?:database|browser)(?: or (?:database|browser))?(?: required)?', '', content)
    tags = {'all'}
    if projects or (root / 'global.json').is_file() or re.search(r'(?<!\w)(c#|\.net|dotnet)(?!\w)', content):
        tags.add('dotnet')
    if re.search(r'\b(browser|frontend|react|vite|typescript)\b', content):
        tags.add('web')
    if re.search(r'\b(http|openapi|endpoint|api)\b', content):
        tags.update(('api', 'http-api'))
    if re.search(r'\b(persistence|database|dbcontext|postgresql|sqlserver|sqlite)\b', content):
        tags.add('persistence')
    if re.search(r'\b(capability|building.block|shellfeature)\b', content):
        tags.add('capabilities')
    return tags


def model(root, feature):
    tags = intent(root, feature)
    return {'schemaVersion': 1, 'feature': feature.relative_to(root).as_posix(),
            'requirements': [r for r in catalog()['requirements'] if r['when'] in tags]}


def project(root, feature, phase):
    """Return regenerable context without writing into the feature's design files."""
    return model(root, feature)


def render(value, phase):
    lines = [f'# Applicable guidance: {phase}', '',
             'Record concrete decisions and tests in plan.md/tasks.md. No separate review receipts are required.',
             'Conditional guidance applies only when its stated conditions hold.', '']
    for rule in value['requirements']:
        lines += [f"## {rule['id']}", rule['requirement'], 'Example: ' + rule['example'],
                  'Guidance: ' + ', '.join(rule['sources']),
                  'Enforcement: ' + rule['enforcement']['kind']]
        if rule['enforcement'].get('diagnostics'):
            lines.append('Compiler diagnostics: ' + ', '.join(rule['enforcement']['diagnostics']))
        for source, sections in rule.get('sections', {}).items():
            lines.append(source + ': ' + '; '.join(sections))
        lines.append('')
    return '\n'.join(lines)


def check(root, feature, phase):
    # Drafting is not blocked by absent metadata. Completion must run engineering.
    if phase == 'delivery':
        execute(root, feature)
    return model(root, feature)


def execute(root, feature):
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
             'startedAtUtc':datetime.now(timezone.utc).isoformat(),
             'command':[executable, '-NoProfile', '-File', str(command)]}
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
    return {'applicationChecksPassed': True, 'releaseReadinessEstablished': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('project', 'check', 'verify'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phase', default='planning', choices=('planning','after-plan','after-tasks','implementation','delivery'))
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = inside(root, args.feature_dir)
    try:
        result = execute(root, feature) if args.command == 'verify' else check(root, feature, args.phase)
        print(json.dumps(result) if args.command == 'verify' else render(result, args.phase))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

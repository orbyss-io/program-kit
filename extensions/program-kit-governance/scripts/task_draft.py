"""Persist task-generation progress in tasks.md; never execute implementation work."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

PREFIX = '<!-- program-kit:tasks-draft '
MARKER = re.compile(r'^<!-- program-kit:tasks-draft (.+) -->$', re.M)


def inputs(root, feature):
    paths = [feature / name for name in ('spec.md', 'plan.md', 'research.md',
                                        'data-model.md', 'quickstart.md')]
    paths += [root / '.specify/memory/constitution.md', root / '.specify/extensions.yml']
    paths += sorted(p for p in (feature / 'contracts').rglob('*') if p.is_file())
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else None for p in paths}


def load(path):
    content = path.read_text(encoding='utf-8') if path.is_file() else ''
    match = MARKER.search(content)
    return content, json.loads(match[1]) if match else None


def store(path, content, state):
    marker = PREFIX + json.dumps(state, separators=(',', ':')) + ' -->'
    content = MARKER.sub(lambda _: marker, content, count=1) if MARKER.search(content) else content + '\n' + marker + '\n'
    # Same-directory replacement keeps either the previous or the next complete checkpoint.
    descriptor, temporary = tempfile.mkstemp(prefix='.tasks-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare(root, feature, phases):
    path = feature / 'tasks.md'
    content, state = load(path)
    current = inputs(root, feature)
    if state:
        changed = sorted(k for k in current.keys() | state['inputs'].keys()
                         if current.get(k) != state['inputs'].get(k))
        return {'status': state['status'], 'completedPhases': state['completed'],
                'remainingPhases': [p for p in state['phases'] if p not in state['completed']],
                'changedInputs': changed, 'tasks': str(path)}
    if content:
        return {'status': 'existing', 'tasks': str(path),
                'instruction': 'Preserve existing tasks, IDs, checked boxes and consumer edits; review only missing or affected phases.'}
    if not phases or len(set(phases)) != len(phases) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', p) for p in phases):
        raise ValueError('Supply unique phase identifiers from the specification, e.g. setup foundation US1 polish')
    for name in ('spec.md', 'plan.md'):
        if not (feature / name).is_file():
            raise ValueError(f'Missing {name}; no draft created')
    state = {'version': 1, 'status': 'draft', 'phases': phases, 'completed': [], 'inputs': current}
    store(path, f'# Tasks: {feature.name}\n\n> Draft: task generation is incomplete. Resume saved phases before analysis or implementation.\n', state)
    return prepare(root, feature, phases)


def save_phase(root, feature, phase, body):
    path = feature / 'tasks.md'
    content, state = load(path)
    if not state or state['status'] != 'draft':
        raise ValueError('Prepare a draft before saving a phase')
    if inputs(root, feature) != state['inputs']:
        raise ValueError('Design inputs changed: review affected saved phases, then acknowledge-inputs; preserve the draft')
    if phase not in state['phases'] or phase in state['completed']:
        raise ValueError('Phase is unplanned or already saved; preserve it and edit only affected tasks directly')
    if not body.strip() or not re.search(r'^## ', body, re.M):
        raise ValueError('Supply a completed phase with a Markdown heading')
    if 'program-kit:tasks-draft' in body or '> Draft:' in body:
        raise ValueError('Phase content cannot contain draft control markers')
    old_ids = re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M)
    new_ids = re.findall(r'^- \[[ xX]\] (T\d+)\b', body, re.M)
    if len(set(old_ids + new_ids)) != len(old_ids + new_ids):
        raise ValueError('Duplicate task IDs; preserve saved IDs and continue numbering')
    state['completed'].append(phase)
    store(path, content.rstrip() + '\n\n' + body.strip() + '\n', state)


def acknowledge(root, feature):
    path = feature / 'tasks.md'
    content, state = load(path)
    if not state or state['status'] != 'draft':
        raise ValueError('Only an existing draft can acknowledge reviewed input changes')
    state['inputs'] = inputs(root, feature)
    store(path, content, state)


def finalize(root, feature):
    path = feature / 'tasks.md'
    content, state = load(path)
    if not state or set(state['completed']) != set(state['phases']):
        raise ValueError('Incomplete draft: save every planned phase before after_tasks/analyze')
    if inputs(root, feature) != state['inputs']:
        raise ValueError('Review changed design inputs before finalizing')
    checklists = re.findall(r'^- \[[ xX]\] (.+)$', content, re.M)
    if not checklists or any(not re.fullmatch(r'T\d{3,} .+', line) for line in checklists):
        raise ValueError('Every task needs a checklist, task ID and description before analysis')
    ids = [line.split()[0] for line in checklists]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate task IDs in saved draft; resolve before analysis')
    state['status'] = 'complete'
    content = content.replace('> Draft: task generation is incomplete. Resume saved phases before analysis or implementation.\n', '')
    store(path, content, state)
    return {'status': 'complete', 'tasks': str(path), 'implementationExecuted': False,
            'instruction': 'Run mandatory after_tasks hooks including read-only speckit.analyze; this checkpoint claims drafting progress only.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'save-phase', 'acknowledge-inputs', 'finalize'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phases', nargs='+')
    parser.add_argument('--phase')
    parser.add_argument('--content-file')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = (root / args.feature_dir).resolve()
    try:
        if not feature.is_relative_to(root) or not feature.is_dir():
            raise ValueError('Feature must be an existing directory inside the repository')
        if not (feature / 'tasks.md').resolve().is_relative_to(feature):
            raise ValueError('Task path escapes feature')
        if args.command == 'prepare':
            result = prepare(root, feature, args.phases)
        elif args.command == 'save-phase':
            if not args.phase or not args.content_file:
                raise ValueError('save-phase requires --phase and --content-file')
            save_phase(root, feature, args.phase, Path(args.content_file).read_text(encoding='utf-8'))
            result = prepare(root, feature, None)
        elif args.command == 'acknowledge-inputs':
            acknowledge(root, feature)
            result = prepare(root, feature, None)
        else:
            result = finalize(root, feature)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

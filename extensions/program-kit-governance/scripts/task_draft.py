"""Persist drafts and a compact current checkpoint in tasks.md; never execute work."""
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
CURRENT = re.compile(r'^<!-- program-kit:current-checkpoint (.+) -->$', re.M)
CURRENT_LIMIT = 8192


def inputs(root, feature):
    paths = [feature / name for name in ('spec.md', 'plan.md', 'research.md',
                                        'data-model.md', 'quickstart.md')]
    paths += [root / '.specify/memory/constitution.md', root / '.specify/extensions.yml']
    paths += [root/'eng/foundation-composition.json', root/'eng/foundation-composition.resolved.json']
    # Latest actual setup outcome is a drafting input, not a drafting action.
    # A newer failure cannot be hidden by retaining a previous successful run.
    outcomes = list((root/'artifacts/tests/runs').glob('foundation-*/result.json'))
    if outcomes:
        latest = max(outcomes, key=lambda path: json.loads(path.read_text(encoding='utf-8')).get('startedAtUtc', ''))
        paths.append(latest)
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
    atomic_write(path, content)


def atomic_write(path, content):
    # Same-directory replacement keeps either the previous or the next complete checkpoint.
    descriptor, temporary = tempfile.mkstemp(prefix='.tasks-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def current(feature):
    path = feature / 'tasks.md'
    content = path.read_text(encoding='utf-8') if path.is_file() else ''
    markers = list(CURRENT.finditer(content))
    if len(markers) > 1 or content.count('<!-- program-kit:current-checkpoint ') != len(markers):
        raise ValueError('Duplicate or malformed current checkpoints; review without discarding retained state')
    if not markers:
        return None
    value = json.loads(markers[0][1])
    if not isinstance(value, dict) or value.get('version') != 1:
        raise ValueError('Unsupported current checkpoint; preserve and review retained state')
    for field in ('baseline', 'outcome', 'next'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError('Malformed current checkpoint: ' + field)
    for field in ('taskIds', 'checks', 'decisions', 'failures'):
        if not isinstance(value.get(field), list) or any(not isinstance(i, str) or not i.strip() for i in value[field]):
            raise ValueError('Malformed current checkpoint: ' + field)
    return value


def checkpoint(feature, update):
    """Replace current state, never append journals or silently discard open failures."""
    path = feature / 'tasks.md'
    if not path.is_file():
        raise ValueError('Locate existing tasks.md before saving progress')
    content = path.read_text(encoding='utf-8')
    prior = current(feature) or {}
    allowed = {'baseline', 'outcome', 'next', 'taskIds', 'checks', 'decisions', 'failures', 'resolvedFailures'}
    if not isinstance(update, dict) or set(update) - allowed:
        raise ValueError('Checkpoint accepts only baseline, outcome, next, taskIds, checks, decisions, failures, resolvedFailures')
    for field in ('baseline', 'outcome', 'next'):
        if not isinstance(update.get(field), str) or not update[field].strip():
            raise ValueError('Checkpoint requires nonempty ' + field)
    if prior and prior['baseline'] != update['baseline']:
        raise ValueError('Preserve the original implementation baseline')
    ids = set(re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M))
    task_ids = update.get('taskIds', prior.get('taskIds', []))
    if not isinstance(task_ids, list) or any(not isinstance(i, str) or i not in ids for i in task_ids):
        raise ValueError('Checkpoint taskIds must reference existing task IDs')
    value = {key: update[key].strip() for key in ('baseline', 'outcome', 'next')}
    value.update(version=1, taskIds=list(dict.fromkeys(task_ids)))
    for field in ('checks', 'decisions', 'failures', 'resolvedFailures'):
        items = update.get(field, [])
        if not isinstance(items, list) or any(not isinstance(i, str) or not i.strip() for i in items):
            raise ValueError('Checkpoint ' + field + ' must be a list of nonempty concise references')
    resolved = set(update.get('resolvedFailures', []))
    if not resolved <= set(prior.get('failures', [])):
        raise ValueError('Resolve only a retained failure after actual relevant checks pass')
    if resolved and not update.get('checks'):
        raise ValueError('Resolving a failure requires the relevant successful check references')
    for field in ('checks', 'decisions', 'failures'):
        retained = [i for i in prior.get(field, []) if field != 'failures' or i not in resolved]
        value[field] = list(dict.fromkeys(update.get(field, retained) if field == 'checks'
                                         else retained + update.get(field, [])))
    serialized = json.dumps(value, ensure_ascii=True, separators=(',', ':'))
    if '-->' in serialized or '\n' in serialized or len(serialized.encode('utf-8')) > CURRENT_LIMIT:
        raise ValueError('Checkpoint must be at most 8192 bytes; use concise references to existing artifacts/plan, never discard unresolved failures')
    marker = '<!-- program-kit:current-checkpoint ' + serialized + ' -->'
    content = CURRENT.sub(lambda _: marker, content, count=1) if CURRENT.search(content) else content.rstrip() + '\n\n' + marker + '\n'
    atomic_write(path, content)
    return value


def _table(content, heading, width):
    if len(re.findall(r'^## ' + re.escape(heading) + r'\s*$', content, re.M)) != 1:
        raise ValueError('Supply exactly one ' + heading)
    section = re.search(r'^## ' + re.escape(heading) + r'\s*\n(.*?)(?=^## |\Z)', content, re.M | re.S)
    if not section:
        raise ValueError('Missing ' + heading)
    rows = []
    for line in section[1].splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip().strip('`') for c in line.strip().strip('|').split('|')]
        if len(cells) != width:
            raise ValueError('Malformed ' + heading + ' table row')
        if all(re.fullmatch(r':?-+:?', c) for c in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        raise ValueError('Empty ' + heading)
    return rows[1:]


def _items(cell):
    if cell.lower() == 'none':
        return []
    parts = [part.strip() for part in cell.split(',')]
    if any(not re.fullmatch(r'[A-Za-z0-9_.:-]+', part) or part.lower() == 'none' for part in parts):
        raise ValueError('Use comma-separated dependency identifiers or explicit none')
    return parts


def validate_operation_graph(content, required=False):
    """Check declared task/gate topology; semantic input review remains required."""
    if not re.search(r'^## Operation dependency map\s*$', content, re.M):
        if required:
            raise ValueError('New operation plan requires Operation dependency map and Task dependency map')
        return False  # Existing approved plans are preserved, never automatically rewritten.
    operations = {}
    for operation, dependencies in _table(content, 'Operation dependency map', 2):
        if operation in operations or not re.fullmatch(r'[A-Za-z0-9_-]+', operation):
            raise ValueError('Invalid or duplicate operation: ' + operation)
        operations[operation] = _items(dependencies)
    tasks = {}
    for task, operation, dependencies, requires, provides in _table(content, 'Task dependency map', 5):
        if task in tasks or not re.fullmatch(r'T\d{3,}', task) or operation not in operations:
            raise ValueError('Invalid task dependency row: ' + task)
        tasks[task] = {'operation': operation, 'dependencies': _items(dependencies),
                       'requires': set(_items(requires)), 'provides': set(_items(provides))}
    checklist = re.findall(r'^- \[[ xX]\] (T\d+)\b', content, re.M)
    if set(tasks) != set(checklist) or len(checklist) != len(set(checklist)):
        raise ValueError('Every unique checklist task must have exactly one dependency row')

    def ancestors(graph):
        saved, active = {}, set()
        def visit(node):
            if node not in graph:
                raise ValueError('Unknown dependency: ' + node)
            if node in active:
                raise ValueError('Cyclic dependency: ' + node)
            if node in saved:
                return saved[node]
            active.add(node)
            result = set(graph[node])
            for parent in graph[node]:
                result.update(visit(parent))
            active.remove(node)
            saved[node] = result
            return result
        for node in graph:
            visit(node)
        return saved

    operation_ancestors = ancestors(operations)
    task_graph = {task: row['dependencies'] for task, row in tasks.items()}
    task_ancestors = ancestors(task_graph)
    for task, row in tasks.items():
        for ancestor in task_ancestors[task]:
            other = tasks[ancestor]['operation']
            if other != row['operation'] and other not in operation_ancestors[row['operation']]:
                raise ValueError('Unexplained cross-operation prerequisite: ' + task + ' -> ' + ancestor)
        provided = set().union(*(tasks[a]['provides'] for a in task_ancestors[task]))
        if row['requires'] - provided:
            raise ValueError('Missing prerequisite gates for ' + task + ': ' + ', '.join(sorted(row['requires'] - provided)))
    return True


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
        raise ValueError('Supply unique operation group identifiers from the specification, e.g. US1_create US1_list closure dependencies')
    for name in ('spec.md', 'plan.md'):
        if not (feature / name).is_file():
            raise ValueError(f'Missing {name}; no draft created')
    state = {'version': 2, 'format': 'operation-plan', 'status': 'draft', 'phases': phases, 'completed': [], 'inputs': current}
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
    validate_operation_graph(content, required=state.get('format') == 'operation-plan')
    state['status'] = 'complete'
    content = content.replace('> Draft: task generation is incomplete. Resume saved phases before analysis or implementation.\n', '')
    store(path, content, state)
    return {'status': 'complete', 'tasks': str(path), 'implementationExecuted': False,
            'instruction': 'Run mandatory after_tasks hooks including read-only speckit.analyze; this checkpoint claims drafting progress only.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'save-phase', 'acknowledge-inputs', 'finalize', 'checkpoint', 'current'))
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
        elif args.command == 'checkpoint':
            if not args.content_file:
                raise ValueError('checkpoint requires --content-file with concise current state JSON')
            result = checkpoint(feature, json.loads(Path(args.content_file).read_text(encoding='utf-8')))
        elif args.command == 'current':
            result = current(feature)
        else:
            result = finalize(root, feature)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

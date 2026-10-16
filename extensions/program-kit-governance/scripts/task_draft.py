"""Persist drafts and a compact current checkpoint in tasks.md; never execute work."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlparse
if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] in ('current', 'review-material'):
    sys.dont_write_bytecode = True
from dotnet_adapter import bootstrap

bootstrap()

PREFIX = '<!-- program-kit:tasks-draft '
MARKER = re.compile(r'^<!-- program-kit:tasks-draft (.+) -->$', re.M)
CURRENT = re.compile(r'^<!-- program-kit:current-checkpoint (.+) -->$', re.M)
CURRENT_LIMIT = 8192
RETAINED_LIMIT = 1024 * 1024
EXPANDED_LIMIT = 16 * RETAINED_LIMIT


def _basis_sites(value):
    """Only owned review fields are interned; arbitrary history remains untouched."""
    delivery = value.get('delivery', {})
    require(isinstance(delivery, dict) and isinstance(delivery.get('checkpoints', {}), dict), 'Malformed retained delivery state')
    for current_review in delivery.get('checkpoints', {}).values():
        require(isinstance(current_review, dict), 'Malformed retained review history')
        histories = current_review.get('materialAssessmentHistory', [])
        require(isinstance(histories, list), 'Malformed material assessment history')
        for review in [current_review, *histories]:
            require(isinstance(review, dict) and isinstance(review.get('decisions', []), list), 'Malformed retained review history')
            for field in ('engineeringInputBasis', 'checkBasis'):
                yield review, field
            if isinstance(review.get('presentation'), dict):
                for field in ('basis', 'materialBasis'):
                    yield review['presentation'], field
            for decision in review.get('decisions', []):
                require(isinstance(decision, dict), 'Malformed retained human decision')
                for field in ('basis', 'materialBasis'):
                    yield decision, field
            assessments = review.get('materialAssessments', [])
            require(isinstance(assessments, list), 'Malformed retained material assessments')
            for assessment in assessments:
                require(isinstance(assessment, dict), 'Malformed retained material assessment')
                for field in ('previousBasis', 'currentBasis', 'contextBasis', 'previousContextBasis', 'checkBasis', 'policy'):
                    yield assessment, field


def _basis_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _store_bases(value):
    saved = copy.deepcopy(value)
    if 'delivery' not in saved:
        return saved
    require('basisStorage' not in saved['delivery'], 'Expanded state cannot contain a second basis store')
    pool = {}
    for site, field in _basis_sites(saved):
        require(field + 'Ref' not in site, 'Supply expanded review provenance, not mixed basis references')
        if field not in site:
            continue
        content = site.pop(field)
        require(isinstance(content, dict) and content, 'Review basis must be a nonempty object')
        identity = hashlib.sha256(_basis_bytes(content)).hexdigest()
        require(identity not in pool or pool[identity] == content, 'Conflicting retained basis identity')
        pool[identity] = content
        site[field + 'Ref'] = identity
    saved['delivery']['basisStorage'] = {'version': 1, 'values': pool}
    saved['version'] = 3  # Storage format only; normal readers return expanded v2.
    return saved


def _expand_bases(value):
    saved = copy.deepcopy(value)
    require(isinstance(saved.get('delivery'), dict), 'Missing retained delivery state')
    storage = saved.get('delivery', {}).pop('basisStorage', None)
    require(isinstance(storage, dict) and set(storage) == {'version', 'values'}
            and storage['version'] == 1 and isinstance(storage['values'], dict),
            'Unsupported retained basis storage; preserve the checkpoint')
    pool, sizes, used = storage['values'], {}, set()
    for identity, content in pool.items():
        require(isinstance(identity, str) and re.fullmatch(r'[0-9a-f]{64}', identity)
                and isinstance(content, dict) and content, 'Malformed retained basis identity')
        encoded = _basis_bytes(content)
        require(hashlib.sha256(encoded).hexdigest() == identity, 'Tampered retained basis')
        sizes[identity] = len(encoded)
    expanded_size = len(_basis_bytes(saved))
    for site, field in _basis_sites(saved):
        require(field not in site, 'Mixed inline/reference review provenance')
        if field + 'Ref' not in site:
            continue
        identity = site.pop(field + 'Ref')
        require(isinstance(identity, str) and identity in pool, 'Missing retained basis reference')
        expanded_size += sizes[identity]
        require(expanded_size <= EXPANDED_LIMIT, 'Retained basis expansion exceeds its bounded reader limit')
        site[field] = copy.deepcopy(pool[identity])
        used.add(identity)
    require(used == set(pool), 'Unreferenced retained basis; preserve and review the checkpoint')
    saved['version'] = 2
    return saved


def _checkpoint_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'Duplicate checkpoint field; preserve retained provenance')
        value[key] = item
    return value


def inputs(root, feature):
    paths = [feature / name for name in ('spec.md', 'plan.md', 'research.md',
                                        'data-model.md', 'quickstart.md')]
    paths += [root / '.specify/memory/constitution.md', root / '.specify/extensions.yml']
    paths += [root/'eng/foundation-composition.json', root/'eng/foundation-composition.resolved.json']
    import retained_inputs
    ownership = retained_inputs.snapshot(root)
    paths += [root / relative for relative in ownership['inputs']]
    if (feature / 'artifact-ownership.json').is_file():
        paths.append(feature / 'artifact-ownership.json')
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
    previous = path.read_bytes() if path.is_file() else None
    descriptor, temporary = tempfile.mkstemp(prefix='.tasks-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
        for attempt in range(5):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as error:
                if os.name != 'nt' or getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                    raise
                # A short Windows sharing/access block may clear. Retrying must
                # never overwrite a concurrent human edit or acquire permissions.
                time.sleep(.02 * (attempt + 1))
                try:
                    unchanged = (path.read_bytes() if path.is_file() else None) == previous
                except OSError:
                    unchanged = False
                if not unchanged:
                    error.add_note('Checkpoint destination changed or became unreadable while replacement was blocked; no retry/write.')
                    raise
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
    require(len(markers[0][1].encode('utf-8')) <= RETAINED_LIMIT, 'Retained checkpoint exceeds its bounded state limit')
    value = json.loads(markers[0][1], object_pairs_hook=_checkpoint_object)
    if not isinstance(value, dict) or value.get('version') not in (1, 2, 3):
        raise ValueError('Unsupported current checkpoint; preserve and review retained state')
    if value['version'] == 3:
        value = _expand_bases(value)
    else:
        require('basisStorage' not in value.get('delivery', {}), 'Basis storage requires its explicit checkpoint version')
    for field in ('baseline', 'outcome', 'next'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError('Malformed current checkpoint: ' + field)
    for field in ('taskIds', 'checks', 'decisions', 'failures'):
        if not isinstance(value.get(field), list) or any(not isinstance(i, str) or not i.strip() for i in value[field]):
            raise ValueError('Malformed current checkpoint: ' + field)
    if 'delivery' in value:
        validate(value['delivery'])
    _progress_history(value)
    return value


def _history_event(sequence, previous, kind, value):
    event = {'sequence': sequence, 'previous': previous, 'kind': kind, 'value': copy.deepcopy(value)}
    return {**event, 'sha256': hashlib.sha256(_basis_bytes(event)).hexdigest()}


def _progress_history(value):
    """Progress references are integrity links, never renewed human authority."""
    history = value.get('progressHistory')
    if history is None:
        snapshot = {key: value[key] for key in ('baseline', 'outcome', 'next', 'taskIds', 'checks', 'decisions', 'failures') if key in value}
        return [_history_event(1, None, 'retained-snapshot', snapshot)]
    require(isinstance(history, list) and history, 'Malformed retained progress history')
    previous = None
    for sequence, event in enumerate(history, 1):
        require(isinstance(event, dict) and set(event) == {'sequence', 'previous', 'kind', 'value', 'sha256'}
                and type(event['sequence']) is int and event['sequence'] == sequence and event['previous'] == previous
                and (event['kind'] == 'checkpoint' or sequence == 1 and event['kind'] == 'retained-snapshot')
                and isinstance(event['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', event['sha256'])
                and isinstance(event['value'], dict),
                'Malformed retained progress history link')
        expected = _history_event(sequence, previous, event['kind'], event['value'])
        require(expected == event, 'Tampered retained progress history reference')
        previous = event['sha256']
    return history


def current_projection(value):
    if value is None:
        return None
    events = _progress_history(value)
    result = {key: copy.deepcopy(value[key]) for key in ('baseline', 'outcome', 'next', 'taskIds', 'checks')}
    result['history'] = {'sha256': events[-1]['sha256'], 'events': len(events),
                         'decisions': len(value['decisions']), 'unresolvedFailures': len(value['failures']),
                         'read': 'current --history', 'authority': 'progress only; retained human decisions are unchanged'}
    if value['failures']:
        result['failureState'] = 'unresolved; inspect retained failures before continuation'
    if 'delivery' in value:
        result['retainedDelivery'] = {'checkpoints': len(value['delivery'].get('checkpoints', {})),
                                     'read': 'current --history; normal continuation guards still apply'}
    return result


def progress_history(feature, reference=None):
    value = current(feature)
    if value is None:
        require(reference is None, 'Missing retained progress history reference')
        return None
    events = _progress_history(value)
    if reference is not None:
        matches = [index for index, event in enumerate(events) if event['sha256'] == reference]
        require(len(matches) == 1, 'Missing or tampered retained progress history reference')
        events = events[:matches[0] + 1]
    return {'scope': 'retained progress; not renewed acceptance', 'sha256': events[-1]['sha256'],
            'events': events, 'current': value if reference is None else None}


def save_current(feature, value, submitted=None):
    path = feature / 'tasks.md'
    content = path.read_text(encoding='utf-8')
    summary = current_projection(value)
    require(len(_basis_bytes(value)) <= EXPANDED_LIMIT, 'Expanded checkpoint exceeds its bounded reader limit')
    serialized = json.dumps(_store_bases(value), ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    summary_size = len(_basis_bytes(summary))
    retained_size = len(serialized.encode())
    if '-->' in serialized or summary_size > CURRENT_LIMIT or retained_size > RETAINED_LIMIT:
        submitted_size = len(_basis_bytes(submitted if submitted is not None else summary))
        history_size = len(_basis_bytes(_progress_history(value)))
        contributors = sorted(((key, len(_basis_bytes(item))) for key, item in value.items()), key=lambda row: row[1], reverse=True)[:4]
        raise ValueError('Checkpoint summary must be at most 8192 bytes and retained state 1048576 bytes; '
                         f'submitted={submitted_size}, merged-current={summary_size}, retained-history={history_size}, '
                         f'retained-state={retained_size}, largest-fields={contributors}. '
                         'Prior state is preserved; inspect current --history and shorten current prose/references, never discard unresolved failures or human decisions.')
    marker = '<!-- program-kit:current-checkpoint ' + serialized + ' -->'
    content = CURRENT.sub(lambda _: marker, content, count=1) if CURRENT.search(content) else content.rstrip() + '\n\n' + marker + '\n'
    atomic_write(path, content)


def checkpoint(feature, update):
    """Replace current prose/checks; retain decisions, open failures and their history."""
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
    if 'delivery' in prior:
        value.update(version=2, delivery=prior['delivery'])
    history = _progress_history(prior) if prior else []
    delta = {field: [item for item in update.get(field, []) if item not in prior.get(field, [])]
             for field in ('decisions', 'failures')}
    delta = {field: items for field, items in delta.items() if items}
    if resolved:
        delta['resolvedFailures'] = update['resolvedFailures']
    if 'checks' in update and update['checks'] != prior.get('checks', []):
        delta['checks'] = update['checks']
    if not history or delta:
        event_value = ({key: copy.deepcopy(value[key]) for key in ('baseline', 'outcome', 'next', 'taskIds', 'checks', 'decisions', 'failures')}
                       if not history else {'baseline': value['baseline'], 'outcome': value['outcome'], 'taskIds': value['taskIds'], **delta})
        history = [*history, _history_event(len(history) + 1, history[-1]['sha256'] if history else None, 'checkpoint', event_value)]
    value['progressHistory'] = history
    save_current(feature, value, submitted=update)
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


def validate_operation_graph(content, required=False, root=None):
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
    validate_verification_obligations(content, tasks, task_ancestors, root)
    return True


def validate_verification_obligations(content, tasks, ancestors, root=None):
    """A broad planned gate must follow every selected owner's test-producing task.

    Native selection checks the declared future changed inputs. It is planning
    evidence; actual execution still enforces meaningful tests and retained failures.
    """
    broad = {task for task, description in re.findall(r'^- \[[ xX]\] (T\d+) (.+)$', content, re.M)
             if re.search(r'\bAffected\b', description)}
    has_map = bool(re.search(r'^## Verification obligations\s*$', content, re.M))
    if not has_map:
        if broad:
            raise ValueError('PKT021 Affected gate requires Verification obligations and Test materialization map: ' + ', '.join(sorted(broad)))
        return
    def paths(cell):
        values = [part.strip().strip('`') for part in cell.split(',')]
        if not values or any(not value or Path(value).is_absolute() or '..' in Path(value).parts for value in values):
            raise ValueError('PKT021 use explicit repository-relative verification owners/inputs')
        return values
    materialization = {}
    for owner, producer, evidence in _table(content, 'Test materialization map', 3):
        if owner in materialization or not owner.endswith('.csproj'):
            raise ValueError('PKT021 invalid or duplicate test owner: ' + owner)
        paths(owner)
        if producer != 'existing':
            if producer not in tasks or evidence != 'none':
                raise ValueError('PKT021 name an actual test-producing task, or existing native evidence: ' + owner)
        else:
            paths(evidence)
            if evidence == 'none' or root is None:
                raise ValueError('PKT021 existing meaningful suite requires verifiable native evidence: ' + owner)
            from repository_verification import evidence_valid
            receipt_path = (root / evidence).resolve()
            if not receipt_path.is_relative_to(root.resolve()) or not receipt_path.is_file():
                raise ValueError('PKT021 missing native test evidence: ' + owner)
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            outcomes = [o for o in receipt.get('outcomes', []) if o.get('project') == owner]
            if receipt.get('schemaVersion') != 2 or not any(o.get('status') == 'completed'
                    and type(o.get('executedTests')) is int and o['executedTests'] >= 1
                    and evidence_valid(root, receipt_path, o) for o in outcomes):
                raise ValueError('PKT021 existing suite lacks valid meaningful native execution: ' + owner)
        materialization[owner] = producer
    covered = set()
    baselines = set()
    for gate, scope, baseline, owners_cell, inputs_cell in _table(content, 'Verification obligations', 5):
        if gate not in tasks or gate in covered or scope not in {'Focused', 'Affected'} or not baseline or baseline == 'none':
            raise ValueError('PKT021 invalid/duplicate verification gate or missing retained baseline: ' + gate)
        if gate in broad and scope != 'Affected':
            raise ValueError('PKT021 an Affected checklist gate must retain its Affected obligation: ' + gate)
        covered.add(gate); baselines.add(baseline)
        owners = set(paths(owners_cell))
        if not owners <= materialization.keys():
            raise ValueError('PKT021 unresolved selected test materialization: ' + gate + '; ' + ', '.join(sorted(owners - materialization.keys())))
        if root is not None:
            from repository_verification import select
            inputs = paths(inputs_cell)
            actual = select(root, scope, projects=sorted(owners) if scope == 'Focused' else (),
                            changed_paths=inputs, planning=True)['projects']
            if set(actual) != owners:
                raise ValueError('PKT021 selected test owners differ from maintained selection: ' + gate + '; actual ' + ', '.join(actual))
        for owner in owners:
            producer = materialization[owner]
            if producer != 'existing' and producer not in ancestors[gate]:
                raise ValueError('PKT021 premature ' + scope + ' gate ' + gate + ': ' + owner + ' is produced by ' + producer + '; add the dependency or move the gate after materialization')
    if broad - covered:
        raise ValueError('PKT021 missing Affected verification obligations: ' + ', '.join(sorted(broad - covered)))
    if len(baselines) != 1:
        raise ValueError('PKT021 preserve one original implementation baseline across verification gates')
    retained = CURRENT.search(content)
    if retained and json.loads(retained[1]).get('baseline') not in baselines:
        raise ValueError('PKT021 verification obligations must retain the original checkpoint baseline')


def prepare(root, feature, phases):
    import retained_inputs
    ownership = retained_inputs.snapshot(root)
    path = feature / 'tasks.md'
    content, state = load(path)
    current = inputs(root, feature)
    if state:
        retained_inputs.validate_document_outputs(root, content, state.get('documentOwnership'))
        changed = sorted(k for k in current.keys() | state['inputs'].keys()
                         if current.get(k) != state['inputs'].get(k))
        return {'status': state['status'], 'completedPhases': state['completed'],
                'remainingPhases': [p for p in state['phases'] if p not in state['completed']],
                'changedInputs': changed, 'tasks': str(path), 'documentOwnership': retained_inputs.summary(ownership)}
    if content:
        retained_inputs.validate_document_outputs(root, content)
        return {'status': 'existing', 'tasks': str(path),
                'documentOwnership': retained_inputs.summary(ownership),
                'instruction': 'Preserve existing tasks, IDs, checked boxes and consumer edits; review only missing or affected phases.'}
    if not phases or len(set(phases)) != len(phases) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', p) for p in phases):
        raise ValueError('Supply unique operation group identifiers from the specification, e.g. US1_create US1_list closure dependencies')
    for name in ('spec.md', 'plan.md'):
        if not (feature / name).is_file():
            raise ValueError(f'Missing {name}; no draft created')

    fresh = POLICY in (feature / 'spec.md').read_text(encoding='utf-8')
    state = {'version': 2, 'format': 'story-plan' if fresh else 'operation-plan', 'status': 'draft', 'phases': phases, 'completed': [], 'inputs': current}
    if ownership['configured']:
        state['documentOwnership'] = ownership
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
    import retained_inputs
    ownership = retained_inputs.validate_document_outputs(root, content.rstrip() + '\n\n' + body.strip(), state.get('documentOwnership'))
    if ownership['configured']:
        state['documentOwnership'] = ownership
    state['completed'].append(phase)
    store(path, content.rstrip() + '\n\n' + body.strip() + '\n', state)


def acknowledge(root, feature):
    path = feature / 'tasks.md'
    content, state = load(path)
    if not state or state['status'] != 'draft':
        raise ValueError('Only an existing draft can acknowledge reviewed input changes')
    import retained_inputs
    ownership = retained_inputs.validate_document_outputs(root, content, state.get('documentOwnership'))
    if ownership['configured']:
        state['documentOwnership'] = ownership
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
    import retained_inputs
    retained_inputs.validate_document_outputs(root, content, state.get('documentOwnership'))
    validate_operation_graph(content, required=state.get('format') in ('operation-plan', 'story-plan'), root=root)
    if state.get('format') == 'story-plan':

        plan(content)
    state['status'] = 'complete'
    content = content.replace('> Draft: task generation is incomplete. Resume saved phases before analysis or implementation.\n', '')
    store(path, content, state)
    return {'status': 'complete', 'tasks': str(path), 'implementationExecuted': False,
            'instruction': 'Run mandatory after_tasks hooks including read-only speckit.analyze; this checkpoint claims drafting progress only.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'save-phase', 'acknowledge-inputs', 'finalize', 'checkpoint', 'current', 'delivery', 'reset', 'review-material'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phases', nargs='+')
    parser.add_argument('--phase')
    parser.add_argument('--content-file')
    parser.add_argument('--apply', action='store_true', help='Apply only an explicitly human-selected unfinished-feature file inventory')
    parser.add_argument('--history', action='store_true', help='Current: explicitly read retained progress and complete delivery provenance')
    parser.add_argument('--history-sha', help='Current --history: resolve an exact retained progress reference')
    parser.add_argument('--checkpoint', help='review-material: retained checkpoint identity to diagnose without writing')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = (root / args.feature_dir).resolve()
    try:
        require(not (args.history or args.history_sha) or args.command == 'current', 'History output applies only to current')
        require(not args.history_sha or args.history, '--history-sha requires --history')
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
            result = current_projection(checkpoint(feature, json.loads(Path(args.content_file).read_text(encoding='utf-8'))))
        elif args.command == 'current':
            result = progress_history(feature, args.history_sha) if args.history else current_projection(current(feature))
        elif args.command == 'review-material':
            require(nonempty(args.checkpoint), 'review-material requires --checkpoint')
            import review_material
            reviews = load_delivery(feature)['checkpoints']
            require(args.checkpoint in reviews, 'Unknown review checkpoint: ' + args.checkpoint)
            result = review_material.explain(root, reviews[args.checkpoint])
        elif args.command == 'reset':
            if not args.content_file:
                raise ValueError('reset requires the concrete reviewed inventory in --content-file')
            request = json.loads(Path(args.content_file).read_text(encoding='utf-8'))
            require(path(root, request['feature']) == feature, 'Reset inventory must match --feature-dir')
            result = reset(root, request, args.apply)
        elif args.command == 'delivery':

            if not args.content_file:
                raise ValueError('delivery requires --content-file with an explicit scoped transition')
            result = transition(root, feature, json.loads(Path(args.content_file).read_text(encoding='utf-8')))
        else:
            result = finalize(root, feature)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error))
        return 2





POLICY = 'program-kit:story-delivery-v1'
STATES = {'pending', 'ready for review', 'changes requested', 'accepted', 'deferred'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def path(root, relative):
    require(nonempty(relative) and not Path(relative).is_absolute(), 'Use a repository-relative basis/reference path')
    result = (root / relative).resolve()
    require(result.is_relative_to(root.resolve()), 'Review input escapes repository')
    return result


def basis(root, paths):
    require(isinstance(paths, list) and paths and len(set(paths)) == len(paths), 'Name unique implementation/configuration basisPaths')
    result = {}
    for relative in paths:
        target = path(root, relative)
        require(target.is_file(), 'Missing reviewed input: ' + relative)
        result[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    return result


def check_artifacts(root, references, *, freshness=True):
    require(isinstance(references, list) and references and all(nonempty(ref) for ref in references),
            'Supply actual relevant successful check artifact references')
    hashes = {}
    for ref in references:
        target = path(root, ref)
        require(target.is_file(), 'Missing check artifact: ' + ref)
        if target.suffix == '.json':
            record = json.loads(target.read_text(encoding='utf-8'))
            require(record.get('status') == 'completed' and record.get('exitCode', 0) == 0,
                    'Failed/incomplete technical checks cannot be waived: ' + ref)
            if 'outcomes' in record:
                require(record['outcomes'] and all(outcome.get('status') == 'completed' for outcome in record['outcomes']),
                        'Required technical outcomes are incomplete: ' + ref)
                # Reuse the maintained native evidence reader when its fingerprints are present.
                from repository_verification import evidence_valid
                for outcome in record['outcomes']:
                    if freshness and outcome.get('fingerprint'):
                        require(evidence_valid(root, target, outcome), 'Stale/corrupt technical evidence: ' + ref)
        elif target.suffix in ('.trx', '.xml'):
            from phase_obligations import test_results
            results = test_results(target, 'trx' if target.suffix == '.trx' else 'junit')
            require(results and all(results.values()), 'Failed/empty technical checks cannot be waived: ' + ref)
        else:
            raise ValueError('Supply a maintained JSON result or TRX/JUnit result, not an unverified log: ' + ref)
        hashes[ref] = hashlib.sha256(target.read_bytes()).hexdigest()
    return hashes


def review_digest(presentation):
    # Same-code changes to user meaning cannot reuse an older authenticated decision.
    scope = {key: presentation[key] for key in ('basis', 'outcome', 'expected', 'limitations')}
    if 'materialBasis' in presentation:
        scope['basis'] = presentation['materialBasis']
    return hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()


def require_policy(root, feature):
    """Adoption is a ratified amendment and fresh feature, never old partial progress."""
    import governance_state as governance
    import os
    previous = Path.cwd()
    prior_paths = {name: getattr(governance, name) for name in ('CONSTITUTION', 'RATIFICATION', 'ROADMAP', 'DECISIONS')}
    try:
        os.chdir(root)
        governance.configure_paths()
        governance.validate_ratification()
        require(POLICY in (root / governance.CONSTITUTION).read_text(encoding='utf-8'),
                'Amend and ratify the constitution for story delivery before fresh feature implementation')
    finally:
        os.chdir(previous)
        for name, prior in prior_paths.items():
            setattr(governance, name, prior)
    for name in ('spec.md', 'plan.md'):
        require(POLICY in (feature / name).read_text(encoding='utf-8'),
                'Fresh specification and all Spec Kit phases are required; abandon the old partial feature: ' + name)


def plan(content, required=True):
    from task_draft import _table, _items
    if '## Story delivery map' not in content:
        require(not required, 'Fresh tasks require Story delivery map; old partial feature progress cannot authorize continuation')
        return {}
    result, seen = {}, set()
    operations = {row[0] for row in _table(content, 'Operation dependency map', 2)}
    tasks = _table(content, 'Task dependency map', 5)
    for story, owned, outcome, walkthrough, estimate, rationale in _table(content, 'Story delivery map', 6):
        ids = _items(owned)
        require(re.fullmatch(r'US[1-9]\d*', story) and story not in result and ids and
                set(ids) <= operations and not seen.intersection(ids), 'Invalid story/operation ownership: ' + story)
        require(nonempty(outcome) and nonempty(walkthrough), 'Story needs useful outcome and independent walkthrough')
        minutes = float(estimate)
        require(math.isfinite(minutes) and minutes > 0 and (minutes <= 120 or (nonempty(rationale) and rationale.lower() != 'none')),
                'Larger story needs disclosed effort and sizing rationale')
        task_ids = [row[0] for row in tasks if row[1] in ids]
        require(task_ids, 'Story must own implementation tasks')
        result[story] = {'operations': ids, 'taskIds': task_ids, 'outcome': outcome,
                         'walkthrough': walkthrough, 'estimateMinutes': minutes, 'rationale': rationale}
        seen.update(ids)
    require(seen == operations - {'closure'}, 'Every product operation must belong to exactly one story')
    return result


def owner_continuation(review, value, operation=None):
    """The latest owner deferral supplies authority; freshness supplies no authority."""
    decisions = review.get('decisions', [])
    presented = review.get('presentation')
    if not decisions or not isinstance(presented, dict) or review.get('human') != 'deferred':
        return False
    decision = decisions[-1]
    permits = review.get('permits', [])
    operations = {op for row in value.get('stories', {}).values() for op in row.get('operations', [])}
    return (decision.get('verdict') == 'deferred' and decision.get('reviewer') == 'owner'
            and decision.get('assignment') == value.get('roles', {}).get('owner')
            and nonempty(decision.get('source')) and isinstance(permits, list) and bool(permits)
            and all(isinstance(permit, str) for permit in permits)
            and len(set(permits)) == len(permits) and set(permits) <= operations
            and permits == decision.get('permits') and decision.get('basis') == presented.get('basis')
            and decision.get('materialBasis') == presented.get('materialBasis')
            and (operation is None or operation in permits))


def assessed_basis(review):
    """An exact human material assessment never changes the original review."""
    events = review.get('materialAssessments', [])
    if not events:
        return None
    require(isinstance(events, list) and review.get('decisions') and isinstance(review.get('presentation'), dict),
            'Material assessment requires retained accepted decision provenance')
    previous = review.get('presentation', {}).get('basis')
    previous_context = None
    decision = hashlib.sha256(_basis_bytes(review['decisions'][-1])).hexdigest()
    for event in events:
        require(isinstance(event, dict) and event.get('version') == 1 and event.get('actor') == 'owner'
                and nonempty(event.get('source')) and event.get('decisionSha256') == decision
                and event.get('previousBasis') == previous and event.get('currentBasis')
                and event.get('previousContextBasis') == previous_context
                and event.get('checks') and event.get('checkBasis') and event.get('changes'),
                'Malformed or rebound material assessment; retain the original decision')
        require(isinstance(event.get('currentBasis'), dict) and set(event['currentBasis']) == set(previous)
                and isinstance(event.get('contextBasis'), dict) and event['contextBasis']
                and isinstance(event.get('policy'), dict) and event['policy']
                and isinstance(event.get('changes'), list), 'Malformed retained material assessment inputs')
        old_inputs = {**(previous_context or {}), **previous}
        new_inputs = {**(event['contextBasis'] if previous_context is not None else {}), **event['currentBasis']}
        changed = {name for name in set(old_inputs) | set(new_inputs) if old_inputs.get(name) != new_inputs.get(name)}
        require(len(event['changes']) == len(changed)
                and {row.get('path') for row in event['changes'] if isinstance(row, dict)} == changed,
                'Retained material assessment must cover the exact changed input set')
        for row in event['changes']:
            before = row.get('before', {})
            require((old_inputs.get(row['path']) is None and before == {'absent': True})
                    or (isinstance(before, dict) and set(before) == {'path', 'sha256'}
                        and before['sha256'] == old_inputs[row['path']]),
                    'Retained material assessment has a changed original binding')
            require('afterSha256' in row and row['afterSha256'] == new_inputs.get(row['path'])
                    and row.get('conclusion') == 'nonmaterial' and nonempty(row.get('rationale'))
                    and isinstance(row.get('effects'), dict)
                    and set(row['effects']) == {'build', 'dependencies', 'packaging', 'runtime'}
                    and all(nonempty(effect) for effect in row['effects'].values()),
                    'Malformed retained material effect assessment')
        require(event.get('presentationSha256') == hashlib.sha256(_basis_bytes(review['presentation'])).hexdigest()
                and event.get('scopeSha256') == hashlib.sha256(_basis_bytes(review.get('materialScope'))).hexdigest(),
                'Material assessment cannot narrow or rewrite the original presentation/scope')
        previous = event['currentBasis']
        previous_context = event['contextBasis']
    return previous


def assessment_policy():
    import handoff_contract
    import retained_inputs
    return {**{name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
               for name in ('task_draft.py', 'review_material.py', 'artifact_ownership.py')},
            'retained_inputs.py': hashlib.sha256(Path(retained_inputs.__file__).read_bytes()).hexdigest(),
            'handoff_contract.py': hashlib.sha256(Path(handoff_contract.__file__).read_bytes()).hexdigest()}


def assessment_context(root):
    """Exact conservative current closure, including newly introduced member inputs.

    This assessment does not confer a standing exclusion on future sibling work.
    Native restore observations use the same inventory as package freshness.
    """
    import handoff_contract
    result = handoff_contract.source_inputs(root)
    excluded = {'bin', 'obj', 'node_modules', 'dist', '__pycache__', '.auth'}
    for directory in ('src', 'tests', 'eng', 'web', 'contracts'):
        for target in (root / directory).rglob('*'):
            relative = target.relative_to(root)
            if target.is_file() and not excluded.intersection(relative.parts) and target.suffix not in ('.pyc', '.pyo'):
                result[relative.as_posix()] = hashlib.sha256(path(root, relative.as_posix()).read_bytes()).hexdigest()
    for target in root.iterdir():
        if target.is_file():
            result[target.name] = hashlib.sha256(path(root, target.name).read_bytes()).hexdigest()
    return result


def assessed_material_state(root, review, raw=None):
    """Shared read-only applicability for refresh and explanation, without new authority."""
    expected = assessed_basis(review)
    require(expected is not None, 'No retained material assessment')
    event = review['materialAssessments'][-1]
    context = assessment_context(root)
    previous_context = event['contextBasis']
    changes = [{'path': name, 'reviewedSha256': previous_context.get(name), 'currentSha256': context.get(name)}
               for name in sorted(set(previous_context) | set(context)) if previous_context.get(name) != context.get(name)]
    try:
        evidence_current = all(check_artifacts(root, item['checks'], freshness=False) == item['checkBasis']
                               for item in review['materialAssessments'])
        originals_current = all(row['before'] == {'absent': True} or
                                hashlib.sha256(path(root, row['before']['path']).read_bytes()).hexdigest()
                                == row['before']['sha256']
                                for item in review['materialAssessments'] for row in item['changes'])
    except (ValueError, OSError, KeyError, TypeError):
        evidence_current = originals_current = False
    result = {'rawBasisCurrent': (raw if raw is not None else basis(root, review['basisPaths'])) == expected,
              'contextCurrent': not changes, 'policyCurrent': event['policy'] == assessment_policy(),
              'evidenceCurrent': evidence_current, 'originalsCurrent': originals_current,
              'changedContextInputs': changes}
    result['current'] = all(result[name] for name in ('rawBasisCurrent', 'contextCurrent', 'policyCurrent',
                                                     'evidenceCurrent', 'originalsCurrent'))
    return result


def validate(value):
    require(isinstance(value, dict) and value.get('version') == 1, 'Malformed story delivery state')
    require(isinstance(value.get('roles'), dict) and 'owner' in value['roles'] and 'requester' in value['roles'], 'Missing review roles')
    for role in value['roles'].values():
        require(isinstance(role, dict) and nonempty(role.get('reference')) and
                role.get('kind') in ('conversation', 'github'), 'Malformed reviewer assignment')
        if role['kind'] == 'github':
            require(role.get('provider') == 'github' and nonempty(role.get('host')) and
                    isinstance(role.get('id'), int) and nonempty(role.get('login')) and
                    nonempty(role.get('confirmation')), 'GitHub assignment must be verified and human confirmed')
    require(isinstance(value.get('stories'), dict) and value['stories'] and
            isinstance(value.get('checkpoints'), dict), 'Missing retained stories/checkpoints')
    for key, review in value['checkpoints'].items():
        require(nonempty(key) and re.fullmatch(r'[A-Za-z0-9_-]+', key), 'Use stable nonempty checkpoint identifiers')
        require(isinstance(review, dict) and review.get('required') is True, 'Every retained checkpoint has its required review obligation')
        require(review.get('human') in STATES and review.get('story') in value['stories'] and
                review.get('reviewer') in value['roles'] and review.get('engineering') in ('pending', 'complete'),
                'Malformed checkpoint disposition/assignment')
        require(isinstance(review.get('decisions'), list), 'Missing decision provenance')
        for decision in review['decisions']:
            require(isinstance(decision, dict) and decision.get('verdict') in ('accepted', 'changes requested', 'deferred') and
                    nonempty(decision.get('source')) and nonempty(decision.get('reviewer')) and
                    isinstance(decision.get('assignment'), dict) and nonempty(decision['assignment'].get('reference')) and
                    isinstance(decision.get('basis'), dict) and decision['basis'] and
                    isinstance(decision.get('permits'), list) and isinstance(decision.get('at'), (int, float)),
                    'Malformed retained human decision provenance')
        if review['human'] in ('accepted', 'deferred'):
            scoped_retained = ((review.get('materialAssessments') or (review.get('materialScope') and isinstance(review.get('presentation'), dict) and
                              review['presentation'].get('materialBasis') and review.get('engineeringInputBasis') and
                              review['decisions'] and review['decisions'][-1].get('materialBasis') == review['presentation']['materialBasis'] and
                              not review.get('stale'))) and not review.get('stale'))
            require((review.get('engineering') == 'complete' or scoped_retained or owner_continuation(review, value))
                    and isinstance(review.get('presentation'), dict) and review['decisions'],
                    'Decision requires complete engineering, presented basis and provenance')
            require(review['decisions'][-1]['verdict'] == review['human'] and
                    review['decisions'][-1]['basis'] == review['presentation'].get('basis'),
                    'Human disposition must match its actual latest decision/basis')
            if review['human'] == 'deferred':
                require(review.get('permits') and review['permits'] == review['decisions'][-1]['permits'],
                        'Deferred scope must match the explicit decision')
        if review.get('presentation'):
            require(all(nonempty(review['presentation'].get(field)) for field in
                        ('entryPoint', 'preparedData', 'walkthrough', 'expected', 'limitations', 'outcome')) and
                    isinstance(review.get('checkBasis'), dict) and review['checkBasis'] and review.get('checks') and review.get('basisPaths'),
                    'Malformed presented journey/verification basis')
        if review.get('materialAssessments'):
            assessed_basis(review)
        histories = review.get('materialAssessmentHistory', [])
        require(isinstance(histories, list), 'Malformed retained material assessment history')
        for archived in histories:
            require(isinstance(archived, dict) and archived.get('version') == 1
                    and archived.get('reviewer') in value['roles'] and archived.get('materialAssessments')
                    and archived.get('decisions') and archived['decisions'][-1].get('verdict') == 'accepted'
                    and not archived.get('materialAssessmentHistory')
                    and isinstance(archived.get('supersededAt'), (int, float))
                    and math.isfinite(archived['supersededAt']), 'Malformed archived material assessment')
            assessed_basis(archived)
    clock = value.get('clock')
    require(isinstance(clock, dict) and isinstance(clock.get('at'), (int, float)) and math.isfinite(clock['at']) and
            isinstance(clock.get('waiting'), bool), 'Malformed active clock')
    require(isinstance(value.get('plan'), dict), 'Missing story plan basis')
    for story, row in value['stories'].items():
        require(story in value['checkpoints'] and isinstance(row.get('operations'), list) and row['operations'] and
                isinstance(row.get('effort'), dict) and set(row['effort']) == set(row['operations']), 'Malformed story effort/operation ownership')
        for subject in [row, *row['effort'].values()]:
            require(all(isinstance(subject.get(field), (int, float)) and math.isfinite(subject[field]) and subject[field] >= 0
                        for field in ('seconds', 'budgetMinutes')) and subject['budgetMinutes'] > 0 and
                        isinstance(subject.get('warned'), bool), 'Malformed accumulated effort')
    active = value.get('active')
    require(active is None or (isinstance(active, dict) and active.get('story') in value['stories'] and
            active.get('operation') in value['stories'][active['story']]['operations']), 'Malformed active work')
    return value


def load_delivery(feature):
    from task_draft import current
    saved = current(feature)
    require(saved and 'delivery' in saved, 'Initialize fresh story delivery state before implementation; old progress grants no authority')
    return copy.deepcopy(validate(saved['delivery']))


def persist(feature, value):
    from task_draft import current, save_current
    saved = current(feature)
    saved['delivery'] = validate(value)
    saved['version'] = 2
    save_current(feature, saved)


def refresh(root, value):
    """Material basis changes reopen affected reviews; unrelated commits are irrelevant."""
    for review in value['checkpoints'].values():
        presented = review.get('presentation')
        if presented:
            try:
                raw = basis(root, review['basisPaths'])
                fresh = raw == review.get('engineeringInputBasis', presented['basis'])
                material_fresh = False
                if review.get('materialScope') and presented.get('materialBasis'):
                    import review_material
                    material_fresh = review_material.basis(root, review['materialScope'], review['basisPaths']) == presented['materialBasis']
                    fresh = fresh and material_fresh
                if review.get('materialAssessments'):
                    material_fresh = assessed_material_state(root, review, raw)['current']
                    fresh = fresh and material_fresh
            except (ValueError, OSError, KeyError, TypeError):
                fresh = False
                material_fresh = False
            try:
                fresh = fresh and check_artifacts(root, review['checks']) == review['checkBasis']
            except (ValueError, OSError, KeyError, TypeError):
                fresh = False
            if not fresh:
                if material_fresh:
                    review.update(engineering='pending')
                else:
                    review.update(human='deferred' if owner_continuation(review, value) else 'pending',
                                  engineering='pending', stale=True)
    return value


def accrue(value, now):
    clock = value['clock']
    require(isinstance(now, (int, float)) and math.isfinite(now) and now >= clock['at'], 'Clock moved backwards; preserve accumulated effort')
    active = value.get('active')
    if active and not clock['waiting'] and not clock.get('suspended', False):
        seconds = now - clock['at']
        story = value['stories'][active['story']]
        operation = story['effort'][active['operation']]
        operation['seconds'] += seconds
        story['seconds'] += seconds
    clock['at'] = now
    warnings = []
    if active:
        story = value['stories'][active['story']]
        for identifier, subject in ((active['story'], story), (active['operation'], story['effort'][active['operation']])):
            if subject['seconds'] >= subject['budgetMinutes'] * 60 and not subject['warned']:
                subject['warned'] = True
                warnings.append({'work': identifier, 'activeMinutes': round(subject['seconds'] / 60, 2),
                    'instruction': 'Report what works, what remains, cause and smallest corrective action; reassess scope. Time alone does not block authorized work.'})
    return warnings


def guard(root, feature, operation=None, closure=False, repair=False):
    import retained_inputs
    retained_inputs.validate_document_outputs(root, (feature / 'tasks.md').read_text(encoding='utf-8'))
    value = refresh(root, load_delivery(feature))
    from task_draft import validate_operation_graph
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    validate_operation_graph(content, required=True, root=root)
    require(plan(content) == value['plan'],
            'Story plan changed; obtain a scope decision and update the affected artifacts/state')
    persist(feature, value)
    return _review_guard(root, feature, value, operation, closure=closure, repair=repair)


def _review_guard(root, feature, value, operation=None, closure=False, repair=False):
    import retained_inputs
    retained_inputs.validate_document_outputs(root, (feature / 'tasks.md').read_text(encoding='utf-8'))
    if operation is None and value.get('active'):
        operation = value['active']['operation']
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    completed = set(re.findall(r'^- \[[xX]\] (T\d+)\b', content, re.M))
    rows = _table(content, 'Task dependency map', 5)
    repairable = repair and any(operation == row[1] and row[0] in completed and
            row[0] in review.get('taskIds', value['stories'][review['story']]['taskIds']) and review.get('presentation')
            for review in value['checkpoints'].values() for row in rows)
    require(not repair or repairable, 'Repair/diagnosis must target an existing presented outcome, never a new product operation')
    unresolved = [key for key, review in value['checkpoints'].items() if review['human'] != 'accepted']
    if closure:
        require(not unresolved, 'Required human reviews remain due before feature acceptance: ' + ', '.join(unresolved))
        require(not load_failures(feature), 'Required technical failures cannot be waived by human approval')
        for review in value['checkpoints'].values():
            require(not review.get('stale'), 'Current human review remains due after material changes')
            require(review['engineering'] == 'complete', 'Current engineering checks remain due after changed review inputs')
            require(check_artifacts(root, review['checks']) == review['checkBasis'], 'Technical evidence changed after story presentation')
        return value
    for key, review in value['checkpoints'].items():
        continuation = owner_continuation(review, value, operation)
        if review.get('presentation') and review['human'] in ('accepted', 'deferred'):
            require(repairable or continuation or review['engineering'] == 'complete', 'Current engineering checks remain due: ' + key)
            if continuation and not repairable:
                require(not load_failures(feature), 'Human continuation cannot waive required technical failures')
                check_artifacts(root, review['checks'], freshness=False)
            else:
                require(repairable or check_artifacts(root, review['checks']) == review['checkBasis'], 'Technical evidence changed after story presentation')
        tasks = review.get('taskIds', value['stories'][review['story']]['taskIds'])
        due = review['human'] in ('ready for review', 'changes requested', 'deferred') or review.get('stale') or (set(tasks) <= completed and review['human'] == 'pending')
        if due:
            permitted = review['human'] == 'deferred' and operation in review.get('permits', [])
            require(permitted or repairable, 'Pause for required human review: ' + key + '; only repair/diagnosis or explicit scoped deferral may proceed')
    return value


def _active_permitted(root, feature, value):
    active = value.get('active')
    if not active:
        return False
    try:
        content = (feature / 'tasks.md').read_text(encoding='utf-8')
        require(plan(content) == value['plan'], 'Changed operation scope')
        _review_guard(root, feature, value, active['operation'], repair=active.get('purpose') in ('repair', 'diagnose'))
        _enabling_tasks(content, active['operation'])
    except (ValueError, OSError, KeyError):
        return False
    return True


def _enabling_tasks(content, operation):
    completed = set(re.findall(r'^- \[[xX]\] (T\d+)\b', content, re.M))
    dependencies = {row[0]: _items(row[1]) for row in _table(content, 'Operation dependency map', 2)}
    tasks = _table(content, 'Task dependency map', 5)
    require(operation in dependencies and all(row[0] in completed for row in tasks if row[1] in dependencies[operation]),
            'Complete the operation actual enabling prerequisites before dependent work')


def load_failures(feature):
    from task_draft import current
    return current(feature).get('failures', [])


def github_read(host, endpoint):
    """Use the existing authenticated GitHub CLI read route; never post or poll."""
    result = subprocess.run(['gh', 'api', '--hostname', host, endpoint], capture_output=True,
                            text=True, encoding='utf-8', timeout=30)
    require(result.returncode == 0, 'GitHub read unavailable; new identity/decision remains pending')
    return json.loads(result.stdout)


def github_reference(reference, reader=github_read):
    parsed = urlparse(reference)
    require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.query,
            'Supply an exact HTTPS GitHub comment or review reference')
    match = re.fullmatch(r'/([^/]+)/([^/]+)/(issues|pull)/(\d+)', parsed.path)
    fragment = re.fullmatch(r'(issuecomment-|pullrequestreview-|discussion_r)(\d+)', parsed.fragment)
    require(match and fragment, 'Supply an exact issue comment, pull request review or review comment reference')
    owner, repo, kind, number = match.groups()
    resource = {'issuecomment-': 'issues/comments', 'pullrequestreview-': 'pulls/' + number + '/reviews',
                'discussion_r': 'pulls/comments'}[fragment[1]]
    record = reader(parsed.hostname, f'repos/{owner}/{repo}/{resource}/{fragment[2]}')
    require(record.get('html_url') == reference and record.get('user', {}).get('type') == 'User',
            'GitHub source reference/author could not be verified')
    return parsed.hostname, record


def initialize(root, feature, request, now):
    from task_draft import current, checkpoint
    require_policy(root, feature)
    require(not (current(feature) or {}).get('delivery'), 'Preserve existing delivery state; use scoped transitions')
    content = (feature / 'tasks.md').read_text(encoding='utf-8')
    require(not re.search(r'^- \[[xX]\]', content, re.M), 'Abandon old implementation/checkmarks; initialize only a fresh feature')
    from task_draft import load as draft_load, validate_operation_graph
    _, draft = draft_load(feature / 'tasks.md')
    require(not draft or draft['status'] == 'complete', 'Finish task drafting/analysis before implementation')
    validate_operation_graph(content, required=True, root=root)
    selected = plan(content)
    require(nonempty(request.get('source')), 'Record the requesting human conversation source')
    value = {'version': 1, 'plan': selected,
             'roles': {'requester': {'kind': 'conversation', 'reference': request['source']},
                       'owner': {'kind': 'conversation', 'reference': request['source']}},
             'stories': {}, 'checkpoints': {}, 'active': None, 'clock': {'at': now, 'waiting': False, 'suspended': False}}
    for story, row in selected.items():
        value['stories'][story] = {**row, 'seconds': 0, 'budgetMinutes': 120, 'warned': False,
            'effort': {op: {'seconds': 0, 'budgetMinutes': 60, 'warned': False} for op in row['operations']}}
        value['checkpoints'][story] = {'story': story, 'required': True, 'reviewer': 'requester',
            'engineering': 'pending', 'human': 'pending', 'basisPaths': [], 'decisions': []}
    saved = current(feature)
    if not saved:
        checkpoint(feature, {'baseline': request['baseline'], 'outcome': 'Fresh story delivery', 'next': 'Start first operation'})
    persist(feature, value)
    return value


def transition(root, feature, request, now=None, reader=github_read):
    now = time.time() if now is None else now
    action = request.get('action')
    if action == 'initialize':
        return {'delivery': initialize(root, feature, request, now), 'acceptanceEstablished': False}
    value = refresh(root, load_delivery(feature))
    warnings = accrue(value, now)
    # Persist measured elapsed/freshness even when a requested transition is rejected.
    persist(feature, value)
    owner = request.get('actor') == 'owner' and not request.get('reference')
    if action == 'start':
        operation = request['operation']
        guard(root, feature, operation, repair=request.get('purpose') in ('repair', 'diagnose'))
        story = next((key for key, row in value['stories'].items() if operation in row['operations']), None)
        require(story, 'Unknown operation; renaming cannot reset effort')
        from task_draft import _table, _items
        content = (feature / 'tasks.md').read_text(encoding='utf-8')
        _enabling_tasks(content, operation)
        active = value.get('active')
        if active and active['story'] != story:
            review = value['checkpoints'][active['story']]
            require(request.get('purpose') in ('repair', 'diagnose') or review['human'] == 'accepted' or (review['human'] == 'deferred' and operation in review.get('permits', [])),
                    'Present and resolve the current story before starting another story')
        value.update(active={'story': story, 'operation': operation})
        if request.get('purpose') in ('repair', 'diagnose'):
            value['active']['purpose'] = request['purpose']
        value['clock'].update(waiting=False, suspended=False)
    elif action in ('present', 'engineering'):
        key = request['checkpoint']
        review = value['checkpoints'][key]
        require(not load_failures(feature), 'Resolve required technical failures before presenting a story')
        checks = check_artifacts(root, request.get('checks'))
        story = value['stories'][review['story']]
        content = (feature / 'tasks.md').read_text(encoding='utf-8')
        completed = set(re.findall(r'^- \[[xX]\] (T\d+)\b', content, re.M))
        require(set(review.get('taskIds', story['taskIds'])) <= completed, 'Complete the checkpoint engineering tasks and relevant checks first')
        review.update(engineering='complete', checks=request['checks'], checkBasis=checks)
        if review.get('basisPaths'):
            review['engineeringInputBasis'] = basis(root, review['basisPaths'])
        if action == 'present':
            prior = copy.deepcopy(review.get('presentation'))
            prior_scope = copy.deepcopy(review.get('materialScope'))
            prior_human = review['human']
            require(all(nonempty(request.get(field)) for field in ('entryPoint', 'preparedData', 'walkthrough', 'expected', 'limitations')),
                    'Present runnable entry point, prepared data/account, walkthrough, expected results and material limitations')
            review['basisPaths'] = request['basisPaths']
            review['presentation'] = {field: request[field] for field in ('entryPoint', 'preparedData', 'walkthrough', 'expected', 'limitations')}
            review['presentation']['basis'] = basis(root, review['basisPaths'])
            review['presentation']['outcome'] = story['outcome']
            if request.get('materialScope') is not None:
                import review_material
                review['materialScope'] = copy.deepcopy(request['materialScope'])
            if review.get('materialScope'):
                import review_material
                review['presentation']['materialBasis'] = review_material.basis(root, review['materialScope'], review['basisPaths'])
            review['engineeringInputBasis'] = basis(root, review['basisPaths'])
            unchanged_acceptance = prior_human == 'accepted' and prior and review_digest(prior) == review_digest(review['presentation'])
            if unchanged_acceptance:
                # Preserve the exact original decision's raw basis. Current raw
                # hashes belong to engineering freshness, not rewritten approval.
                review['presentation']['basis'] = prior['basis']
            elif review.get('materialAssessments'):
                review.setdefault('materialAssessmentHistory', []).append({
                    'version': 1, 'presentation': prior, 'materialScope': prior_scope,
                    'reviewer': review['reviewer'], 'decisions': copy.deepcopy(review['decisions']),
                    'materialAssessments': review.pop('materialAssessments'), 'supersededAt': now})
            review.update(human='accepted' if unchanged_acceptance else 'ready for review', stale=False, permits=[])
            value['clock']['waiting'] = True
    elif action == 'assess-material':
        require(owner and nonempty(request.get('source')),
                'Material assessment requires a separate explicit owner instruction and its actual source')
        review = value['checkpoints'][request['checkpoint']]
        require(review.get('decisions') and review['decisions'][-1]['verdict'] == 'accepted'
                and isinstance(review.get('presentation'), dict), 'Retain an actual prior accepted review')
        require(review['decisions'][-1]['basis'] == review['presentation']['basis']
                and review['decisions'][-1].get('materialBasis') == review['presentation'].get('materialBasis'),
                'Material assessment requires the original accepted presentation; a new presentation needs its own human decision')
        decision = hashlib.sha256(_basis_bytes(review['decisions'][-1])).hexdigest()
        require(request.get('decisionSha256') == decision, 'Bind the exact original accepted decisionSha256')
        require('materialScope' not in request and 'basisPaths' not in request,
                'Material assessment cannot drop inputs or redefine the original review scope')
        require(not load_failures(feature), 'Resolve required technical failures before material assessment')
        completed = set(re.findall(r'^- \[[xX]\] (T\d+)\b', (feature / 'tasks.md').read_text(encoding='utf-8'), re.M))
        require(set(review.get('taskIds', value['stories'][review['story']]['taskIds'])) <= completed,
                'Complete checkpoint engineering tasks before material assessment')
        before = assessed_basis(review) or review['presentation']['basis']
        after = basis(root, review['basisPaths'])
        current_context = assessment_context(root)
        previous_context = review['materialAssessments'][-1]['contextBasis'] if review.get('materialAssessments') else None
        before_inputs = {**(previous_context or {}), **before}
        after_inputs = {**(current_context if previous_context is not None else {}), **after}
        changes = request.get('changes')
        changed = {name for name in set(before_inputs) | set(after_inputs)
                   if before_inputs.get(name) != after_inputs.get(name)}
        require(changed and isinstance(changes, list) and len(changes) == len(changed)
                and {row.get('path') for row in changes if isinstance(row, dict)} == changed,
                'Assess every actually changed basis input exactly once')
        for row in changes:
            original = row.get('before', {})
            effects = row.get('effects', {})
            absent = before_inputs.get(row['path']) is None and previous_context is not None
            require((absent and original == {'absent': True}) or
                    (not absent and isinstance(original, dict) and set(original) == {'path', 'sha256'}
                     and original['sha256'] == before_inputs[row['path']]
                     and hashlib.sha256(path(root, original['path']).read_bytes()).hexdigest() == original['sha256']),
                    'Supply retained exact before bytes matching the accepted input hash')
            require('afterSha256' in row and row['afterSha256'] == after_inputs.get(row['path']) and row.get('conclusion') == 'nonmaterial'
                    and nonempty(row.get('rationale')) and isinstance(effects, dict)
                    and set(effects) == {'build', 'dependencies', 'packaging', 'runtime'}
                    and all(nonempty(effect) for effect in effects.values()),
                    'Record exact after hash and explicit build/dependency/packaging/runtime effect assessment; tests alone are insufficient')
        checks = check_artifacts(root, request.get('checks'))
        event = {'version': 1, 'actor': 'owner', 'source': request['source'], 'at': now,
                 'decisionSha256': decision, 'previousBasis': copy.deepcopy(before), 'currentBasis': after,
                 'presentationSha256': hashlib.sha256(_basis_bytes(review['presentation'])).hexdigest(),
                 'scopeSha256': hashlib.sha256(_basis_bytes(review.get('materialScope'))).hexdigest(),
                 'policy': assessment_policy(), 'changes': copy.deepcopy(changes),
                 'contextBasis': current_context,
                 'checks': request['checks'], 'checkBasis': checks}
        if previous_context is not None:
            event['previousContextBasis'] = previous_context
        review.setdefault('materialAssessments', []).append(event)
        review.update(human='accepted', engineering='complete', stale=False, checks=request['checks'],
                      checkBasis=checks, engineeringInputBasis=after)
    elif action == 'decision':
        key = request['checkpoint']
        review = value['checkpoints'][key]
        verdict = request.get('verdict')
        if verdict in ('accepted', 'deferred') and isinstance(review.get('presentation'), dict):
            check_artifacts(root, review['checks'], freshness=False)
        owner_deferral = owner and verdict == 'deferred' and isinstance(review.get('presentation'), dict)
        require(owner_deferral or (review['human'] in ('ready for review', 'changes requested', 'deferred') and not review.get('stale')),
                'Present a fresh checkpoint before recording a decision')
        require(verdict in ('accepted', 'changes requested', 'deferred'), 'Ambiguous decision remains pending')
        role = value['roles'][review['reviewer']]
        source = request.get('source')
        if request.get('reference'):
            try:
                host, record = github_reference(request['reference'], reader)
                require(role['kind'] == 'github' and host == role['host'] and record['user']['id'] == role['id'], 'Wrong reviewer for checkpoint')
                expected = {'feature': feature.relative_to(root).as_posix(), 'checkpoint': key,
                            'basis': review_digest(review['presentation']), 'verdict': verdict}
                if verdict == 'deferred':
                    expected['permits'] = request.get('permits', [])
                matches = re.findall(r'<!-- program-kit:story-decision (.+?) -->', record.get('body') or '')
                require(len(matches) == 1 and json.loads(matches[0]) == expected, 'GitHub decision does not cover this exact checkpoint/outcome/basis')
                source = request['reference']
            except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
                review['pendingDecision'] = {'reference': request['reference'], 'diagnostic': str(error), 'at': now}
                persist(feature, value)
                return {'status': 'pending', 'diagnostic': str(error), 'warnings': warnings, 'acceptanceEstablished': False}
        else:
            require((role['kind'] == 'conversation' and request.get('actor') == review['reviewer']) or
                    (owner and verdict == 'deferred'), 'Wrong reviewer; delegated GitHub reviewers supply an authenticated decision reference')
            require(nonempty(source), 'Record actual explicit human decision source; silence/tests grant no authority')
        if verdict in ('accepted', 'deferred'):
            require((owner_deferral or review['engineering'] == 'complete') and not load_failures(feature),
                    'Human approval cannot waive required technical failures')
            actual_checks = check_artifacts(root, review['checks'], freshness=not owner_deferral)
            require(owner_deferral or actual_checks == review['checkBasis'], 'Technical evidence changed after story presentation')
        permits = request.get('permits', [])
        if verdict == 'deferred':
            all_ops = {op for row in value['stories'].values() for op in row['operations']}
            require(isinstance(permits, list) and permits and len(set(permits)) == len(permits) and set(permits) <= all_ops,
                    'Deferral requires a bounded explicit list of permitted operations')
            require(owner or len(permits) == 1, 'Broader batch deferral requires the owner decision')
        review.update(human=verdict, permits=permits if verdict == 'deferred' else [])
        review.pop('pendingDecision', None)
        deciding_role = 'owner' if owner else review['reviewer']
        review['decisions'].append({'verdict': verdict, 'reviewer': deciding_role, 'assignment': copy.deepcopy(value['roles'][deciding_role]),
            'source': source, 'basis': review['presentation']['basis'], 'permits': review['permits'], 'at': now})
        if review['presentation'].get('materialBasis'):
            review['decisions'][-1]['materialBasis'] = copy.deepcopy(review['presentation']['materialBasis'])
        value['clock']['waiting'] = (not _active_permitted(root, feature, value)) if verdict == 'deferred' else verdict != 'changes requested'
    elif action in ('verify-reviewer', 'assign'):
        require(owner and nonempty(request.get('source')), 'Only an explicit owner decision may reassign review')
        if request.get('login'):
            host = request.get('host', 'github.com')
            require(re.fullmatch(r'[A-Za-z0-9.-]+', host) and re.fullmatch(r'[A-Za-z0-9-]+', request['login']), 'Invalid GitHub account reference')
            record = reader(host, 'users/' + request['login'])
            require(isinstance(record.get('id'), int) and record.get('type') == 'User' and
                    str(record.get('login', '')).lower() == request['login'].lower(), 'Verify actual GitHub human account')
            if action == 'verify-reviewer':
                return {'verifiedAccount': {'provider': 'github', 'host': host, 'id': record['id'],
                        'login': record['login'], 'reference': record['html_url']}, 'assignmentPending': True,
                        'instruction': 'Obtain actual human confirmation of this exact account before assign.', 'warnings': warnings,
                        'acceptanceEstablished': False}
            require(request.get('confirmedId') == record['id'] and nonempty(request.get('confirmation')),
                    'Obtain human assignment confirmation of the verified stable account ID')
            role = {'kind': 'github', 'provider': 'github', 'host': host, 'id': record['id'],
                    'login': record['login'], 'reference': record['html_url'], 'confirmation': request['confirmation']}
        else:
            require(action == 'assign', 'Nominate a GitHub account for verification')
            role_id = request['role']
            require(role_id == 'requester', 'Conversation decisions are available to the established requesting human')
            role = value['roles']['requester']
        key, role_id = request['checkpoint'], request['role']
        require(role_id != 'owner', 'Owner identity is not a reviewer reassignment')
        if role['kind'] == 'github':
            require(role_id != 'requester', 'Preserve established conversation requester; nominate a distinct GitHub reviewer role')
            if role_id in value['roles']:
                previous = value['roles'][role_id]
                require(all(previous.get(field) == role.get(field) for field in ('kind', 'provider', 'host', 'id')),
                        'Use a distinct role for a different account; never silently reassign other checkpoints')
        value['roles'][role_id] = role
        value['checkpoints'][key]['reviewer'] = role_id
        value['checkpoints'][key]['assignmentSource'] = request['source']
    elif action == 'early-checkpoint':
        require(owner and nonempty(request.get('source')), 'An early progression gate requires explicit human agreement')
        key, story = request['checkpoint'], request['story']
        require(key not in value['checkpoints'] and story in value['stories'], 'Use a new stable checkpoint ID and known story')
        require(set(request['taskIds']) <= set(value['stories'][story]['taskIds']) and request['taskIds'], 'Early checkpoint needs scoped tasks')
        value['checkpoints'][key] = {'story': story, 'required': True, 'reviewer': 'requester', 'taskIds': request['taskIds'],
            'engineering': 'pending', 'human': 'pending', 'basisPaths': [], 'decisions': [], 'agreement': request['source']}
    elif action == 'budget':
        require(owner and nonempty(request.get('source')), 'Only explicit owner effort-budget revisions are allowed')
        subject = value['stories'][request['story']]
        if request.get('operation'):
            subject = subject['effort'][request['operation']]
        require(isinstance(request.get('minutes'), (int, float)) and request['minutes'] > 0, 'Budget must be positive active minutes')
        subject.update(budgetMinutes=request['minutes'], budgetSource=request['source'])
    elif action == 'scope':
        require(owner and nonempty(request.get('source')), 'New requirement/scope needs the explicit owner decision')
        updated = plan((feature / 'tasks.md').read_text(encoding='utf-8'))
        require(set(updated) == set(value['plan']), 'A changed story identity needs fresh specification; never rename work to reset accounting')
        affected = {key for key in updated if updated[key] != value['plan'][key]}
        require(affected and affected == set(request.get('stories', [])), 'Name the exact affected stories for this scope decision')
        for key in affected:
            require(updated[key]['operations'] == value['plan'][key]['operations'], 'Preserve operation identity/effort; reconsider new story boundaries in fresh planning')
            value['stories'][key].update(updated[key])
            for review in value['checkpoints'].values():
                if review['story'] == key:
                    review.update(human='pending', engineering='pending', stale=True, scopeSource=request['source'])
        changed_operations = {op for key in affected for op in updated[key]['operations']}
        for review in value['checkpoints'].values():
            if set(review.get('permits', [])) & changed_operations:
                review.update(human='pending', engineering='pending', stale=True, permits=[], scopeSource=request['source'])
        value['plan'] = updated
        if not _active_permitted(root, feature, value):
            value['clock']['waiting'] = True
    elif action == 'reuse-review':
        source = value['checkpoints'][request['from']]
        target = value['checkpoints'][request['checkpoint']]
        story = value['stories'][target['story']]
        require(source['story'] == target['story'] and source['human'] == 'accepted' and not source.get('stale') and
                source['engineering'] == 'complete' and
                set(source.get('taskIds', story['taskIds'])) == set(story['taskIds']) and
                source['presentation']['outcome'] == story['outcome'], 'Prior review must cover the unchanged complete story outcome')
        require(check_artifacts(root, source['checks']) == source['checkBasis'], 'Prior technical check evidence changed')
        target.update(human='accepted', engineering='complete', basisPaths=source['basisPaths'],
                      presentation=copy.deepcopy(source['presentation']), checks=source['checks'], checkBasis=source['checkBasis'], stale=False,
                      decisions=copy.deepcopy(source['decisions']), reusedFrom=request['from'])
        for field in ('materialScope', 'engineeringInputBasis'):
            if field in source:
                target[field] = copy.deepcopy(source[field])
    elif action in ('wait', 'resume', 'suspend', 'status'):
        if action != 'status':
            value['clock']['waiting'] = action == 'wait' or (action == 'resume' and not _active_permitted(root, feature, value))
            value['clock']['suspended'] = action == 'suspend'
    else:
        raise ValueError('Unknown story delivery transition')
    persist(feature, value)
    return {'delivery': value, 'warnings': warnings, 'acceptanceEstablished': False,
            'instruction': 'Engineering and human dispositions are separate; use start before each operation and finish at closure/handoff.'}


def reset_inventory(root, request):

    feature = path(root, request['feature'])
    require(feature.is_relative_to(root / 'specs') and feature != root / 'specs' and feature.is_dir(), 'Select an existing unfinished feature under specs')
    require(nonempty(request.get('reviewSource')), 'Review the concrete ownership/reset inventory first')
    rows = request.get('files', [])
    require(rows and len({row['path'] for row in rows}) == len(rows), 'Select a bounded unique file inventory')
    selected = {}
    for row in rows:
        target = path(root, row['path'])
        require(row.get('owner') == request['feature'] and target.is_file() and not target.is_symlink(), 'Every selected file needs exclusive unfinished-feature ownership')
        parts = Path(row['path']).parts
        allowed = ('specs', 'src', 'tests', 'web', 'contracts') if request.get('method') == 'fresh-feature-delete-v1' else ('specs', 'src', 'tests')
        require(parts[0] in allowed and not any(p.lower() in
                ('migrations', 'data', '.git', '.specify', '.program-kit') for p in parts),
                'Reset does not authorize toolkit/bootstrap/shared inputs, migrations or data')
        require(not (parts[0] == 'specs' and not target.is_relative_to(feature)), 'Cannot reset another feature')
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        require(row.get('sha256') == digest, 'Reviewed reset input changed: ' + row['path'])
        selected[row['path']] = digest
    for name in ('spec.md', 'plan.md', 'tasks.md'):
        relative = (feature / name).relative_to(root).as_posix()
        require(relative in selected, 'Abandon all old specification/plan/tasks as active work')
    preserved = request.get('preserve', [])
    require(preserved and not set(preserved).intersection(selected), 'Name designated bootstrap/toolkit/shared inputs to preserve')
    hashes = {relative: hashlib.sha256(path(root, relative).read_bytes()).hexdigest() for relative in preserved}
    return selected, hashes


def delete_feature_attempt(root, request, selected, preserved, apply):
    """Delete an explicitly selected attempt without retaining its old contents."""
    feature = path(root, request['feature'])
    # Check lexical ancestors too: resolve() alone would hide an in-repository alias.
    for relative in [request['feature'], *selected]:
        require(Path(relative).as_posix() == relative and '..' not in Path(relative).parts,
                'Delete-only reset needs canonical repository-relative paths')
        target = root / relative
        require(not any(part.is_symlink() or getattr(part, 'is_junction', lambda: False)()
                        for part in (target, *target.parents) if part.is_relative_to(root)),
                'Delete-only reset refuses linked files/directories')
    directories = []
    actual = set()
    for directory, children, filenames in os.walk(feature, followlinks=False):
        folder = Path(directory)
        for name in children:
            child = folder / name
            require(not child.is_symlink() and not getattr(child, 'is_junction', lambda: False)(),
                    'Delete-only reset refuses linked files/directories')
            directories.append(child)
        actual.update((folder / name).relative_to(root).as_posix() for name in filenames)
    expected = {name for name in selected if path(root, name).is_relative_to(feature)}
    require(actual == expected, 'Select every file in the old specification before deleting the complete attempt')
    result = {'status': 'preview', 'method': request['method'], 'deleted': selected, 'preserved': preserved,
              'instruction': 'Retain confirmed intake; execute specify itself, clarification, plan, tasks, analysis and implement anew with the installed release. Do not consult or reuse the old attempt, its archives or Git history as implementation input.'}
    if not apply:
        return result
    require(nonempty(request.get('selectionSource')), 'Apply requires the actual human selection of this exact inventory')
    # No content copies or archive are created. Check all inputs before the first deletion.
    for relative, digest in {**selected, **preserved}.items():
        require(hashlib.sha256(path(root, relative).read_bytes()).hexdigest() == digest, 'Reset input changed before deletion: ' + relative)
    for relative in selected:
        target = path(root, relative)
        require(hashlib.sha256(target.read_bytes()).hexdigest() == selected[relative], 'Reset input changed during deletion: ' + relative)
        target.unlink()
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        require(directory.resolve().is_relative_to(feature), 'Reset directory escapes selected specification')
        directory.rmdir()  # Unknown/new files stop cleanup rather than being removed.
    feature.rmdir()
    result['status'] = 'deleted'
    return result


def reset(root, request, apply=False):

    require(request.get('method') in (None, 'fresh-story-delivery-v1', 'fresh-feature-delete-v1'), 'Unknown reset method')
    selected, preserved = reset_inventory(root, request)
    if request.get('method') == 'fresh-feature-delete-v1':
        return delete_feature_attempt(root, request, selected, preserved, apply)
    result = {'status': 'preview', 'abandoned': selected, 'preserved': preserved,
              'instruction': 'Install released toolkit; amend/review/ratify constitution; rerun specify, clarification, plan, tasks, analysis and implement. No old partial progress may be reused.'}
    if not apply:
        return result
    require(nonempty(request.get('selectionSource')), 'Apply requires the actual human selection of this exact inventory')
    identity = hashlib.sha256(json.dumps(selected, sort_keys=True).encode()).hexdigest()[:16]
    archive = root / '.program-kit/abandoned-features' / (Path(request['feature']).name + '-' + identity)
    require(not archive.exists(), 'Preserve existing abandoned-attempt history; inspect before another reset')
    # Copy and verify every byte before any removal. Failures preserve the archive/remaining source.
    for relative, digest in selected.items():
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, target)
        require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, 'Archive verification failed')
    (archive / 'inventory.json').write_text(json.dumps({**request, 'preserved': preserved}, indent=2), encoding='utf-8')
    for relative, digest in selected.items():
        require(hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, 'Reset input changed during archival')
    for relative in selected:
        (root / relative).unlink()
    result.update(status='abandoned', archive=archive.relative_to(root).as_posix())
    return result




if __name__ == '__main__':
    raise SystemExit(main())

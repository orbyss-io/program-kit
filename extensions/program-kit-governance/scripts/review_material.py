"""Versioned, conservative material projections for existing story checkpoints.

Raw engineering evidence remains independent. Unsupported inputs never establish
unchanged material scope; historical decisions cannot acquire a scope retroactively.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError('Review material scope: ' + message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def read_json(path):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'duplicate JSON property ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'nonfinite JSON ' + value))


def composition_adapter(root):
    installed = root / '.specify/extensions/program-kit-dotnet/scripts/composition_model.py'
    source = installed if installed.is_file() else Path(__file__).resolve().parents[2] / 'program-kit-dotnet/scripts/composition_model.py'
    require(source.is_file(), 'selected composition adapter is unavailable')
    spec = importlib.util.spec_from_file_location('_review_composition', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def composition_projection(value, hosts, environments, adapter):
    adapter.validate(value)
    require(isinstance(hosts, list) and hosts and len(set(hosts)) == len(hosts) and
            set(hosts) <= set(adapter.resources(value, 'host')), 'unknown/empty selected hosts')
    require(isinstance(environments, list) and environments and len(set(environments)) == len(environments) and
            set(environments) <= set(value['environments']) and value['defaultEnvironment'] in environments,
            'unknown/empty selected environments or uncovered active environment')
    selected = set(hosts)
    shells = {shell for host in hosts for shell in adapter.host_shells(value, host)}
    selected.update(shells)
    selected.update(feature for shell in shells for feature in adapter.shell_features(value, shell))
    edges = []
    for row in value['bindings']:
        if row.get('hostRef') in selected or row.get('shellRef') in shells:
            edges.append(row)
            selected.update(row[key] for key in adapter.REFERENCE_KINDS if key in row)
    for row in value['bindings']:
        if ((row['kind'] == 'databaseServer' and row['databaseRef'] in selected) or
                (row['kind'] == 'apiCall' and row['clientRef'] in selected)) and row not in edges:
            edges.append(row)
            selected.update(row[key] for key in adapter.REFERENCE_KINDS if key in row)
    selected.update(value['resources'][name]['authorityRef'] for name in list(selected)
                    if 'authorityRef' in value['resources'][name])
    return {'schemaVersion': value['schemaVersion'], 'compositionId': value['compositionId'],
            'runner': value['runner'], 'defaultEnvironment': value['defaultEnvironment'], 'authority': value.get('authority'),
            'developmentCandidate': value.get('developmentCandidate'),
            'resources': {name: value['resources'][name] for name in sorted(selected)},
            'bindings': [row for row in value['bindings'] if row in edges],
            'environments': {name: {key: row for key, row in value['environments'][name]['resources'].items()
                                    if key in selected} for name in sorted(environments)}}


def story_document_projection(path, row):
    """Retain all shared prose and the explicitly reviewed story sections.

    Known sibling identities are declared in the original scope. Unknown,
    malformed or nested regions fail rather than treating arbitrary later prose
    as unrelated. Markers express reviewed ownership, not semantic inference.
    """
    require(set(row) == {'path', 'kind', 'version', 'stories', 'knownStories'}
            and type(row['version']) is int and row['version'] == 1 and path.suffix == '.md',
            'unsupported story-document projection')
    for field in ('stories', 'knownStories'):
        values = row[field]
        require(isinstance(values, list) and values and all(isinstance(value, str)
                and re.fullmatch(r'[A-Z][A-Z0-9_-]{0,63}', value) for value in values)
                and len(set(values)) == len(values), 'use unique stable story identities in ' + field)
    require(set(row['stories']) <= set(row['knownStories']), 'selected stories must be known')
    sections, shared = {}, []
    active = None
    fence = None
    for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
        delimiter = re.match(r'^[ ]{0,3}(`{3,}|~{3,})([^\n]*)\n?$', line)
        if delimiter:
            token, tail = delimiter.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
        marker = re.fullmatch(r'<!-- program-kit:story-(start|end) ([A-Z][A-Z0-9_-]{0,63}) -->\n?', line)
        if marker:
            require(fence is None, 'story region marker inside fenced code is unsupported')
            operation, identity = marker.groups()
            require(identity in row['knownStories'], 'unknown story region ' + identity)
            if operation == 'start':
                require(active is None and identity not in sections, 'nested/duplicate story region ' + identity)
                sections[identity] = []
                active = identity
            else:
                require(active == identity, 'mismatched story region end ' + identity)
                active = None
        else:
            require('program-kit:story-' not in line, 'malformed story region marker')
            (shared if active is None else sections[active]).append(line)
    require(active is None, 'unclosed story region ' + str(active))
    require(set(row['stories']) <= set(sections), 'missing selected story regions')
    return {'shared': ''.join(shared),
            'stories': {identity: ''.join(sections[identity]) for identity in sorted(row['stories'])}}


def basis(root, scope, paths):
    require(isinstance(scope, dict) and set(scope) == {'schemaVersion', 'inputs'} and type(scope['schemaVersion']) is int and scope['schemaVersion'] == 1,
            'unsupported scope version/fields')
    inputs = scope['inputs']
    require(isinstance(inputs, list) and len(inputs) == len(paths) and
            {row.get('path') for row in inputs if isinstance(row, dict)} == set(paths),
            'classify every raw basis path exactly once')
    implementation = {Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'task_draft.py': hashlib.sha256(Path(__file__).with_name('task_draft.py').read_bytes()).hexdigest()}
    result = {}
    for row in inputs:
        relative = row['path']
        path = (root / relative).resolve()
        require(not Path(relative).is_absolute() and path.is_relative_to(root.resolve()) and path.is_file(),
                'missing/foreign input ' + relative)
        kind = row.get('kind')
        if kind in ('file', 'json'):
            require(set(row) == {'path', 'kind'}, 'unsupported input fields')
            result[relative] = digest(read_json(path)) if kind == 'json' else hashlib.sha256(path.read_bytes()).hexdigest()
        elif kind == 'story-document':
            result[relative] = digest(story_document_projection(path, row))
        elif kind == 'foundation-composition':
            require(set(row) == {'path', 'kind', 'version', 'hosts', 'environments'} and type(row['version']) is int and row['version'] == 1 and
                    relative == 'eng/foundation-composition.json', 'unsupported composition projection')
            adapter, source = composition_adapter(root)
            implementation['composition_model.py'] = hashlib.sha256(source.read_bytes()).hexdigest()
            result[relative] = digest(composition_projection(read_json(path), row['hosts'], row['environments'], adapter))
        elif kind == 'verification':
            require(set(row) == {'path', 'kind', 'version', 'projects'} and type(row['version']) is int and row['version'] == 1 and
                    relative in ('eng/verification.json', 'eng/verification.setup.json'), 'unsupported verification projection')
            value = read_json(path)
            require(isinstance(value, dict) and type(value.get('schemaVersion')) is int and value.get('schemaVersion') == 1 and
                    set(value) <= {'schemaVersion', 'testGroups', 'runnerReuse', 'testOwnershipReplacements', 'owner'},
                    'unknown verification version/fields')
            projects = row['projects']
            require(isinstance(projects, list) and projects and len(set(projects)) == len(projects) and
                    all(isinstance(item, str) and item.endswith('.csproj') for item in projects), 'invalid relevant test projects')
            groups = value.get('testGroups', [])
            require(isinstance(groups, list) and all(isinstance(group, dict) and
                    set(group) <= {'id', 'projects', 'inputs', 'reuse', 'externalState'} and
                    isinstance(group.get('id'), str) and isinstance(group.get('projects'), list) and
                    isinstance(group.get('inputs'), list) for group in groups) and
                    len({group['id'] for group in groups}) == len(groups), 'unknown/ambiguous verification groups')
            relevant = [group for group in groups if set(group['projects']) & set(projects)]
            require(set(projects) <= {project for group in relevant for project in group['projects']}, 'missing relevant verification coverage')
            result[relative] = digest({**value, 'testGroups': relevant})
        else:
            raise ValueError('Review material scope: unsupported projection kind ' + str(kind))
    return {'scopeSha256': digest(scope), 'implementationSha256': digest(implementation), 'inputs': result}


def explain(root, review):
    """Read-only per-input materiality diagnostics; never changes a disposition."""
    scope = review.get('materialScope')
    require(scope is not None, 'checkpoint has no reviewed materialScope; retain whole-file authority until an explicit assessment')
    presented = review.get('presentation', {})
    prior = presented.get('materialBasis')
    require(isinstance(prior, dict), 'checkpoint has no retained material projection; no retrospective approval inferred')
    current = basis(root, scope, review['basisPaths'])
    policy_current = all(current.get(key) == prior.get(key) for key in ('scopeSha256', 'implementationSha256'))
    engineering = review.get('engineeringInputBasis', presented.get('basis', {}))
    rows = []
    for row in scope['inputs']:
        relative = row['path']
        raw = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        unchanged = current['inputs'][relative] == prior.get('inputs', {}).get(relative)
        rows.append({'path': relative, 'kind': row['kind'], 'rawChanged': raw != engineering.get(relative),
                     'materialChanged': not unchanged, 'currentRawSha256': raw,
                     'reason': 'projection definition or implementation changed' if not policy_current else
                               'reviewed material input changed' if not unchanged else
                               'reviewed material projection unchanged; raw engineering freshness remains independent'})
    return {'readOnly': True, 'acceptanceEstablished': False, 'projectionPolicyCurrent': policy_current,
            'materialUnchanged': policy_current and all(not row['materialChanged'] for row in rows), 'inputs': rows}

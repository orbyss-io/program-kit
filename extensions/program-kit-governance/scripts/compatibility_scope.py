"""Bind reviewed runtime proofs to their exact dependency inputs, not bundle defaults."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def validate(contract):
    scope = contract.get('dependencyScope')
    if scope is None: return False
    if (not isinstance(scope, dict) or set(scope) != {'schemaVersion', 'artifactKeys'} or scope['schemaVersion'] != 1
            or not isinstance(scope['artifactKeys'], list) or any(not isinstance(key, str) or not key for key in scope['artifactKeys'])
            or scope['artifactKeys'] != sorted(set(scope['artifactKeys']))):
        raise ValueError('Compatibility dependency scope needs schema 1 and sorted unique artifact keys')
    return True


def catalog(root):
    from repository_sync import provider
    blocks = provider('program-kit-building-blocks/scripts/building_blocks.py')
    effective = blocks.effective_dependency_context(root)
    selection_path = root / 'docs/architecture/building-block-selection.json'
    selection = blocks.load_json(selection_path) if selection_path.is_file() else None
    return blocks, effective['catalog'], selection



def fixture_keys(root, fixtures, extra=()):
    """Every registered direct fixture dependency is in scope and uses accepted pins."""
    blocks, value, _ = catalog(root)
    keys = set(extra)
    for relative, source in fixtures.items():
        path = blocks.repository_path(root, source)
        if Path(relative).suffix == '.csproj':
            references = [('nuget:' + reference.get('Include', ''), reference.get('Version')) for reference in ET.parse(path).iter('PackageReference')]
        elif Path(relative).name == 'package.json':
            package = json.loads(path.read_text(encoding='utf-8'))
            references = [('npm:' + name, pin) for field in ('dependencies', 'devDependencies', 'optionalDependencies') for name, pin in package.get(field, {}).items()]
        else: continue
        for key, version in references:
            if key not in value['packages']: continue
            if version != value['packages'][key]['version']:
                raise ValueError('Compatibility fixture pin differs from accepted dependency profile: ' + key)
            keys.add(key)
    return sorted(keys)


def bindings(root, contract):
    if not validate(contract): return None
    blocks, value, selection = catalog(root)
    declared = set(contract['dependencyScope']['artifactKeys'])
    required = set(fixture_keys(root, contract.get('fixtures', {})))
    if not required <= declared or declared - value['packages'].keys():
        raise ValueError('Compatibility scope omits fixture dependencies or names unregistered artifacts')
    if declared and selection is None:
        raise ValueError('Compatibility artifact scope needs the current selected dependency profile')
    closure = set(declared)
    pending = list(declared)
    while pending:
        key = pending.pop()
        for requirement in value['packages'][key]['requires']:
            child = requirement['package']
            if child not in closure:
                closure.add(child)
                pending.append(child)
    # Dependency-only reviews add revision/authority metadata. The selected
    # architecture choices remain independently bound by design_sources.
    artifacts = {key: copy.deepcopy(value['packages'][key]) for key in sorted(closure)}
    publishers = {value['packages'][key]['family']: value['families'][value['packages'][key]['family']]['repository'] for key in closure}
    return {'schemaVersion': 1, 'artifactKeys': sorted(declared), 'artifacts': artifacts, 'publishers': publishers}


def proof_bindings(root, proof):
    if proof.get('schema_version') != '1.2': return None
    relative = proof.get('dependency_scope', {}).get('contractPath')
    from bootstrap_lifecycle import local, load, digest
    path = local(root, relative) if isinstance(relative, str) else None
    if not path or not any(bound['path'] == relative and bound['sha256'] == digest(path) for bound in proof.get('inputs', [])):
        raise ValueError('Scoped compatibility receipt lacks its exact reviewed contract input')
    current = bindings(root, load(path))
    if current is None: raise ValueError('Scoped compatibility receipt lost its reviewed dependency scope')
    return {'contractPath': relative, 'bindings': current}


def selection_digest(value):
    value = copy.deepcopy(value)
    for field in ('status', 'draftSuggestions', 'catalog', 'revision', 'authority'): value.pop(field, None)
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

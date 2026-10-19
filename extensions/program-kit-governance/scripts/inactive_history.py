"""Explicit, read-only reconciliation of withdrawn application authority for upgrades.

This narrow route admits tooling refresh only. It cannot accept a design, repair a
materialized application, change dependency selections or rewrite historical proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SELECTION = 'docs/architecture/building-block-selection.json'
LOCK = 'eng/building-blocks.lock.json'
COMPOSITION = 'eng/foundation-composition.json'
PROFILE = '.program-kit/dependency-profile.json'


def require(condition, message):
    if not condition:
        raise ValueError('PKU149 ' + message)


def inside(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative
            and not relative.startswith('/') and '..' not in relative.split('/'), 'unsafe inactive-history path')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and
            not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *[p for p in path.parents if p != root and p.is_relative_to(root)])),
            'linked inactive-history input requires owner reconciliation')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate inactive-history field')
        value[key] = item
    return value


def validate(root, declaration, expected, blocks):
    """Recheck exact history, confirmed intake and all surviving native outputs.

    Missing application targets remain historical observations. Existing repository
    pins/tools remain under their native checks. Any actual application target or
    unowned dependency requires the ordinary active-design recovery route.
    """
    root = Path(root).resolve()
    require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'reviewed inactive-history SHA-256 is required')
    source = inside(root, declaration)
    require(source.is_file() and source.stat().st_size <= 2_097_152 and sha(source) == expected,
            'inactive-history declaration changed or missing')
    value = read(source)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'scope', 'rationale', 'intakeRoot', 'withdrawalEvidence', 'historicalSubjects', 'historicalPersistence', 'retainedApplicationTooling', 'inputs'}
            and value['schemaVersion'] == 1 and value['scope'] == 'tooling-only-inactive-history'
            and isinstance(value['rationale'], str) and 0 < len(value['rationale'].strip()) <= 4096,
            'use the reviewed tooling-only inactive-history contract')
    inputs = value['inputs']
    require(isinstance(inputs, dict) and 1 <= len(inputs) <= 10000
            and len({p.casefold() for p in inputs}) == len(inputs), 'invalid inactive-history inventory')
    for relative, digest in inputs.items():
        path = inside(root, relative)
        require(digest is None or isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest), 'invalid history input hash')
        require(not path.is_dir() and sha(path) == digest, 'history input changed or missing: ' + relative)
    subjects = value['historicalSubjects']
    require(isinstance(subjects, dict) and all(isinstance(p, str) and p.startswith('docs/architecture/')
            and p in inputs and inputs[p] is not None and isinstance(reason, str) and reason.strip()
            for p, reason in subjects.items()), 'historical dependency subjects need exact bound paths and reviewed dispositions')
    retained = value['retainedApplicationTooling']
    require(isinstance(retained, dict) and set(retained) <= {'eng/prepare_hosted_pages.py'}
            and all(p in inputs and inputs[p] is not None and isinstance(reason, str) and reason.strip()
                    for p, reason in retained.items()), 'only explicitly bound frontend preparation may remain pending for application use')
    for relative in retained:
        row = blocks.load_json(root / '.program-kit/managed.json').get('files', {}).get(relative, {})
        require(row.get('ownership') == 'managed' and row.get('sourceIdentity') == 'files/' + relative,
                'retained frontend preparation lacks its original source owner')
    selection = read(inside(root, SELECTION))
    blocks.validate_selection(selection)
    blocks.verify_architecture_authority(root, inside(root, SELECTION), selection)
    architecture = selection['authority']['architectureMap']
    model = read(inside(root, architecture))
    required = {SELECTION, LOCK, COMPOSITION, PROFILE, architecture, 'docs/architecture/bootstrap-decisions.json',
                '.specify/governance/migration-completion.json', 'eng/.config/dotnet-tools.json', 'eng/ProgramKit.Packages.props',
                'eng/ProgramKit.Foundation.props'}
    ids = set(selection['authority']['decisionIds'])
    required.update(row['path'] for row in model['decisions'] if row['id'] in ids)
    require(not inside(root, COMPOSITION).exists(), 'composition is present; use active architecture synchronization')
    for target in selection['targets']:
        required.add(target['path'])
        if target['kind'] not in {'repository', 'dotnet-tool-manifest'}:
            require(not inside(root, target['path']).exists(), 'application target is materialized: ' + target['path'])
    lock = read(inside(root, LOCK)) if inside(root, LOCK).is_file() else None
    for output in (lock or {}).get('managedOutputs', []):
        required.add(output['path'])
        if inside(root, output['path']).is_file():
            blocks.check_output(root, output)
    transactions = blocks.transaction_root(root)
    require(not transactions.exists() or transactions.is_dir() and not any(transactions.iterdir()),
            'unfinished building-block transaction requires normal recovery')
    # This catalog selection uses the retained profile owner, never the new default.
    candidate = Path(blocks.__file__).resolve().parents[1] / 'references/orbyss-building-blocks.json'
    catalog_path = blocks.consumer_catalog(root, selection, candidate)
    catalog = blocks.load_json(catalog_path)
    blocks.verify_catalog_binding(selection, catalog)
    required.add(catalog_path.relative_to(root).as_posix()) if catalog_path.is_relative_to(root) else None
    for path in inside(root, '.program-kit/dependency-profiles').rglob('*'):
        if path.is_file(): required.add(path.relative_to(root).as_posix())
    from dependency_audit import audit_exemptions, reject_active_references
    persistence = value['historicalPersistence']
    tool_pin = None
    if persistence is not None:
        require(isinstance(persistence, dict) and set(persistence) == {'profile', 'template'}
                and persistence['profile'] in {'ef-postgresql', 'ef-sqlserver', 'ef-sqlite'},
                'historical persistence needs a finite retained template and profile')
        managed = blocks.load_json(root / '.program-kit/managed.json')
        require(managed.get('persistenceProfile') == persistence['profile'], 'historical persistence profile changed')
        template = inside(root, persistence['template'])
        require(persistence['template'] in inputs and inputs[persistence['template']] is not None
                and not persistence['template'].startswith('.specify/'), 'bind a preserved historical persistence template')
        document = ET.fromstring(template.read_bytes())
        require([node.text for node in document.iter('ProgramKitPersistenceProfile')] == [persistence['profile']],
                'retained persistence template profile differs')
        versions = [node.get('Version') for node in document.iter('PackageVersion')
                    if node.get('Include') == 'Microsoft.EntityFrameworkCore.Design']
        require(len(versions) == 1 and isinstance(versions[0], str) and re.fullmatch(r'\d+\.\d+\.\d+', versions[0]),
                'retained persistence template needs one exact Design tool version')
        tool_pin = versions[0]
    exempt = audit_exemptions(root, lock or {}, inactive_tool_pin=tool_pin, inactive_catalog=catalog)
    historical = {inside(root, relative).resolve() for relative in subjects}
    reject_active_references(root, historical, lock or {})
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if set(relative.parts) & {'.git', '.specify', 'artifacts', 'node_modules', 'bin', 'obj', '__pycache__'}:
            continue
        if path.is_file() and (path.name in {'packages.lock.json', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'dotnet-tools.json'}):
            required.add(relative.as_posix())
        if path.is_file() and (path.suffix in {'.csproj', '.fsproj', '.vbproj'} or path.name == 'package.json'):
            if path.resolve() in exempt or path.resolve() in historical:
                continue
            # Existing toolkit helpers are independently audited by their managed
            # ownership; arbitrary application projects cannot hide in this route.
            managed = blocks.load_json(root / '.program-kit/managed.json').get('files', {}).get(relative.as_posix(), {})
            require(relative.parts[0] == 'eng' and managed.get('ownership') == 'managed'
                    and sha(path) == managed.get('lastWrittenHash', managed.get('installedHash')),
                    'active or customized dependency subject requires normal recovery: ' + relative.as_posix())
    blocks.audit_unmanaged_dependencies(root, catalog, lock, inactive_tool_pin=tool_pin, inactive_history=True)
    intake_root = inside(root, value['intakeRoot'])
    from bootstrap_intake import validate_intake
    validate_intake(intake_root)
    required.update(path.relative_to(root).as_posix() for path in intake_root.rglob('*') if path.is_file())
    evidence = value['withdrawalEvidence']
    require(isinstance(evidence, list) and evidence and all(isinstance(p, str) and p in inputs and inputs[p] is not None for p in evidence),
            'bind original withdrawal evidence; review rationale supplies its interpretation')
    require(required <= inputs.keys(), 'inactive-history inventory omits required originals: ' + ', '.join(sorted(required - inputs.keys())))
    return {'declaration': declaration, 'declarationSha256': expected, 'scope': value['scope'],
            'retainedApplicationTooling': retained,
            'designAcceptanceEstablished': False, 'applicationCorrectnessEstablished': False,
            'pending': ['successor architecture review', 'active composition and placement reconciliation', 'application implementation and acceptance']
                       + ['review and merge retained frontend preparation before application use'] * bool(retained)}


def arguments(binding):
    return ['--inactive-history', binding['declaration'], '--inactive-history-sha256', binding['declarationSha256']] if binding else []

"""Verified offline release guidance and read-only migration planning."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

BASELINE = '0.12.5'
VERIFICATION_CHECKS = {'installation-coherence', 'dependency-verification', 'required-phase-evidence'}


def version_key(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('PKU130 release guidance requires an exact stable version')
    return tuple(map(int, value.split('.')))


def load_index(directory, target):
    directory = Path(directory)
    index = json.loads((directory / 'migration-index.json').read_text(encoding='utf-8'))
    if index.get('schemaVersion') != 1 or index.get('supportedFrom') != BASELINE:
        raise ValueError('PKU130 unsupported release guidance index')
    entries = index['entries']
    versions = [entry['version'] for entry in entries]
    if versions != sorted(set(versions), key=version_key) or target not in versions:
        raise ValueError('PKU130 missing target entry or unordered/duplicate history')
    if not versions or versions[0] != BASELINE:
        raise ValueError('PKU130 migration history is missing its supported baseline')
    for offset, entry in enumerate(entries):
        if 'previous' not in entry or entry['previous'] != (versions[offset - 1] if offset else None):
            raise ValueError('PKU130 migration history has a missing predecessor entry')
        relative = Path(entry['guide'])
        path = (directory / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(directory.resolve()):
            raise ValueError('PKU130 release guide escapes verified inputs')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('PKU130 release guide hash differs: ' + str(relative))
        if not {'automatic', 'review', 'verification', 'recovery'} <= entry.keys():
            raise ValueError('PKU130 incomplete migration entry')
        checks = entry.get('verificationChecks')
        if not isinstance(checks, list) or not checks or len(checks) != len(set(checks)) or set(checks) - VERIFICATION_CHECKS:
            raise ValueError('PKU130 missing or unsupported migration verification checks')
    semantic = index.get('consumerChanges')
    if semantic:
        path = directory / semantic['file']
        if Path(semantic['file']).name != semantic['file'] or hashlib.sha256(path.read_bytes()).hexdigest() != semantic['sha256']:
            raise ValueError('PKU130 consumer semantic metadata differs from verified release guidance')
        validate_changes(json.loads(path.read_text(encoding='utf-8')), versions)
    return index


def validate_changes(value, versions):
    if value.get('schemaVersion') != 1 or not isinstance(value.get('changes'), list):
        raise ValueError('PKU130 unsupported consumer change metadata')
    ids = set()
    for change in value['changes']:
        required = {'id', 'introduced', 'kind', 'summary', 'constraint', 'selectors', 'supportedRetention',
                    'alternatives', 'verification', 'method', 'duePhase', 'supersedes', 'dependencies', 'review'}
        if not required <= change.keys() or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', change['id']) or change['id'] in ids:
            raise ValueError('PKU130 incomplete or duplicate semantic change')
        if change['introduced'] not in versions or change['kind'] not in {'guidance', 'default', 'constraint', 'contract'}:
            raise ValueError('PKU130 invalid semantic applicability')
        if change['duePhase'] not in {'upgrade', 'specification', 'planning', 'tasks', 'implementation', 'delivery', 'production'}:
            raise ValueError('PKU130 invalid semantic due phase')
        for field in ('summary', 'constraint', 'method'):
            if not isinstance(change[field], str) or not change[field].strip():
                raise ValueError('PKU130 semantic change needs ' + field)
        for field in ('supportedRetention', 'alternatives', 'verification'):
            if not isinstance(change[field], list) or not change[field] or not all(isinstance(v, str) and v for v in change[field]):
                raise ValueError('PKU130 semantic change needs ' + field)
        review = change['review']
        if not isinstance(review, dict) or not review.get('basis') or not review.get('route'):
            raise ValueError('PKU130 semantic change requires maintained review provenance')
        selector = change['selectors']
        if not isinstance(selector, dict) or not isinstance(selector.get('paths'), list):
            raise ValueError('PKU130 semantic selectors require paths')
        if not set(change['supersedes'] + change['dependencies']) <= ids:
            raise ValueError('PKU130 semantic references must name earlier maintained changes')
        if change.get('retired') and version_key(change['retired']) <= version_key(change['introduced']):
            raise ValueError('PKU130 invalid semantic retirement')
        ids.add(change['id'])


def semantic_changes(directory, installed, target):
    index = load_index(directory, target)
    source, destination = version_key(installed), version_key(target)
    if source > destination:
        raise ValueError('PKU130 downgrade migration is unsupported')
    asset = index.get('consumerChanges')
    if not asset:
        return {'changes': [], 'limitations': ['Structured semantic coverage is missing; inspect actual release guidance and consumer layout.']}
    changes = json.loads((Path(directory) / asset['file']).read_text(encoding='utf-8'))['changes']
    active = [c for c in changes if version_key(c['introduced']) <= destination and
              (not c.get('retired') or version_key(c['retired']) > destination)]
    superseded = {identity for c in active for identity in c['supersedes']}
    applicable = [c for c in active if c['id'] not in superseded and source < version_key(c['introduced'])]
    return {'changes': applicable, 'limitations': ['Source predates structured history; inspect actual layout without inventing historical approval.']
            if source < version_key(BASELINE) else []}


def plan(directory, installed, target):
    index = load_index(directory, target)
    source = version_key(installed)
    destination = version_key(target)
    if source < version_key(BASELINE):
        return {'schemaVersion': 1, 'fromVersion': installed, 'toVersion': target,
                'status': 'planned', 'layoutInspectionRequired': True, 'migrations': [entry for entry in index['entries']
                    if version_key(entry['version']) <= destination],
                'mutationPerformed': False, 'migrationCompletionEstablished': False,
                'diagnostic': 'Source predates packaged migration history; inspect its actual managed layout '
                              'and preserve unsupported inputs. Version alone requires no approval.'}
    if source > destination:
        raise ValueError('PKU130 downgrade migration is unsupported')
    if installed not in {entry['version'] for entry in index['entries']}:
        raise ValueError('PKU130 source version is missing from verified migration history')
    return {'schemaVersion': 1, 'fromVersion': installed, 'toVersion': target,
            'status': 'planned', 'migrations': [entry for entry in index['entries']
                if source < version_key(entry['version']) <= destination],
            'mutationPerformed': False, 'migrationCompletionEstablished': False}


def require_review(repository, migration_plan):
    """Consume an existing Accepted decision; never create migration approval."""
    if not any(entry.get('substantiveReviewRequired', False) for entry in migration_plan['migrations']):
        return
    repository = Path(repository).resolve()
    digest = hashlib.sha256(json.dumps(migration_plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path = repository / 'docs/architecture/release-migration-review.json'
    if not path.is_file():
        raise ValueError('PKU131 migration needs an Accepted review binding plan SHA-256 ' + digest +
                         '; preserve the plan and review it before installation')
    review = json.loads(path.read_text(encoding='utf-8'))
    # The updater loads this file directly from an extracted bundle. Its sibling
    # scripts are not necessarily importable through the process module path.
    module_name = 'program_kit_guidance_architecture_map'
    specification = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name('architecture_map.py'))
    if specification is None or specification.loader is None:
        raise ValueError('PKU131 bundled architecture ID validator is unavailable')
    architecture = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = architecture
    specification.loader.exec_module(architecture)
    ID = architecture.ID
    decision_id = review.get('decisionId')
    if not isinstance(decision_id, str) or not ID.fullmatch(decision_id):
        raise ValueError('PKU131 migration review decisionId is not a stable Program Kit ID')
    model = json.loads((repository / 'docs/architecture/architecture-map.json').read_text(encoding='utf-8'))
    matches = [item for item in model.get('decisions', []) if item['id'] == decision_id]
    decision = matches[0] if len(matches) == 1 else None
    if review.get('schemaVersion') != 1 or review.get('planSha256') != digest or not decision or decision.get('status') != 'Accepted':
        raise ValueError('PKU131 migration review differs from this plan or lacks Accepted authority')
    decision_path = (repository / decision['path']).resolve()
    if not decision_path.is_relative_to(repository) or hashlib.sha256(decision_path.read_bytes()).hexdigest() != decision.get('sha256'):
        raise ValueError('PKU131 migration decision evidence changed')
    if digest not in decision_path.read_text(encoding='utf-8'):
        raise ValueError('PKU131 Accepted migration decision does not bind this exact plan')


def completion(migration_plan, outcomes):
    """Installation and migration completion remain separate, explicit verdicts."""
    declared = {check for entry in migration_plan['migrations'] for check in entry['verificationChecks']}
    retired = declared & {'required-phase-evidence'}
    checks = sorted(declared - retired)
    missing = [check for check in checks if outcomes.get(check) is not True]
    digest = hashlib.sha256(json.dumps(migration_plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schemaVersion': 1, 'status': 'pending' if missing else 'completed',
            'fromVersion': migration_plan['fromVersion'], 'toVersion': migration_plan['toVersion'],
            'planSha256': digest, 'plan': migration_plan, 'requiredChecks': checks, 'retiredChecks': sorted(retired),
            'retirementReason': 'Feature evidence belongs to application acceptance, not tooling migration',
            'checks': {check: outcomes.get(check) is True for check in checks}, 'pendingChecks': missing,
            'migrationCompletionEstablished': not missing, 'approvalPerformed': False}

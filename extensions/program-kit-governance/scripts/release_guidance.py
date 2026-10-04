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
    return index


def plan(directory, installed, target):
    index = load_index(directory, target)
    source = version_key(installed)
    destination = version_key(target)
    if source < version_key(BASELINE):
        return {'schemaVersion': 1, 'fromVersion': installed, 'toVersion': target,
                'status': 'reviewed-bridge-required', 'migrations': [entry for entry in index['entries']
                    if version_key(entry['version']) <= destination],
                'mutationPerformed': False, 'migrationCompletionEstablished': False,
                'diagnostic': 'Sources older than v0.12.5 require a reviewed bridge; no mutation started.'}
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
    if migration_plan['status'] != 'reviewed-bridge-required' and not any(entry['review'] for entry in migration_plan['migrations']):
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
    checks = sorted({check for entry in migration_plan['migrations'] for check in entry['verificationChecks']})
    missing = [check for check in checks if outcomes.get(check) is not True]
    digest = hashlib.sha256(json.dumps(migration_plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schemaVersion': 1, 'status': 'pending' if missing else 'completed',
            'fromVersion': migration_plan['fromVersion'], 'toVersion': migration_plan['toVersion'],
            'planSha256': digest, 'plan': migration_plan, 'requiredChecks': checks,
            'checks': {check: outcomes.get(check) is True for check in checks}, 'pendingChecks': missing,
            'migrationCompletionEstablished': not missing, 'approvalPerformed': False}

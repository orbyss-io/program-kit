"""Separate offline setup convergence from required consumer phase remediation."""
from pathlib import Path
import json
import os
import re

from phase_obligations import check
from lifecycle_state import atomic_write


def phase_verification_required(root, feature, phase):
    if phase == 'delivery' or (feature / 'tasks.md').is_file():
        return True
    state_path = root / '.program-kit/lifecycle' / (feature.name + '.json')
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    if 'afterTasksAnalysis' in state.get('phases', {}) or any(
            item.get('phase') == 'afterTasksAnalysis' for item in state.get('invalidations', [])):
        return True
    ownership_path = feature / 'artifact-ownership.json'
    ownership = json.loads(ownership_path.read_text()) if ownership_path.is_file() else {}
    for project in ownership.get('runtimeComposition', {}).get('projects', []):
        path = (root / project['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Migration runtime ownership escapes the consumer')
        if path.is_file(): return True
    return False


def migration_phase_ready(remediation):
    # Future specified features still have their own implementation gates. Their
    # unauthored design cannot prevent verification of an installed-tool upgrade.
    if any(type(feature.get('migrationVerificationRequired')) is not bool for feature in remediation['features']):
        raise ValueError('Migration verification lacks explicit feature scope')
    return not remediation['compatibility'] and all(check['ready'] for feature in remediation['features']
        if feature['migrationVerificationRequired'] for check in feature['checks'])


def compatibility_renewal(root: Path):
    """Report changed proof inputs and a human-owned continuation without granting authority."""
    from bootstrap_lifecycle import digest, design_digest, load, local, proof_tooling
    result = {'scope': 'review-required', 'approvalPerformed': False, 'workflowStarted': False,
              'historicalEvidenceChanged': False, 'proofs': [], 'command': None,
              'instruction': 'Run the native continuation in a user-owned terminal. Review its exact packet before accepting; existing confirmations do not approve changed inputs.'}
    try:
        ledger = load(root / 'docs/architecture/bootstrap-prerequisites.json')
        for item in ledger['prerequisites']:
            for evidence in item.get('evidence', []):
                if evidence.get('kind') != 'compatibility':
                    continue
                path = local(root, evidence['path'])
                if digest(path) != evidence['sha256']:
                    raise ValueError('Historical compatibility receipt changed; repair its integrity before renewal')
                proof = load(path)
                scoped = proof.get('schema_version') == '1.2'
                current = proof_tooling(scoped)
                previous = proof.get('tooling_sources', {})
                tooling = [{'path': name, 'beforeSha256': previous.get(name), 'afterSha256': current.get(name)}
                           for name in sorted(set(previous) | set(current)) if previous.get(name) != current.get(name)]
                design = []
                for name, before in proof.get('design_sources', {}).items():
                    selected = local(root, name)
                    after = design_digest(selected, scoped) if selected.is_file() else None
                    if after != before:
                        design.append({'path': name, 'beforeSha256': before, 'afterSha256': after})
                inputs = []
                for bound in proof.get('inputs', []):
                    selected = local(root, bound['path'])
                    after = digest(selected) if selected.is_file() else None
                    if after != bound['sha256']:
                        inputs.append({'path': bound['path'], 'beforeSha256': bound['sha256'], 'afterSha256': after})
                result['proofs'].append({'prerequisite': item['id'], 'path': evidence['path'],
                                        'sha256': evidence['sha256'], 'changedTooling': tooling,
                                        'changedDesign': design, 'changedInputs': inputs})
        completion_path = root / '.specify/governance/bootstrap-completion.json'
        if not completion_path.is_file():
            result['continuationUnavailable'] = 'No completed native bootstrap is recorded; resume the existing bootstrap at its current gate.'
            return result
        completion = load(completion_path)
        run_id = completion.get('workflow', {}).get('run_id')
        if completion.get('status') != 'Completed' or not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
            raise ValueError('Native completion does not identify a valid completed source run')
        # Follow the current completion, including a completed recovery child.
        # Runtime admission verifies the full engine binding before any dispatch.
        result.update(command=['python', '.specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py',
                               'resume', '--run-id', run_id, '--post-bootstrap'], cwd=str(root),
                      executionOwner='human', commandAuthority='suggested continuation; native admission and fresh review remain required')
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        result['continuationUnavailable'] = str(error)
    return result


def assess(root: Path, deferred_persistence=None):
    # Intake's governance validators resolve configured paths from cwd. Upgrader
    # callers may run anywhere; their workspace cannot supply consumer authority.
    root = root.resolve()
    previous = Path.cwd()
    try:
        os.chdir(root)
        return _assess(root, deferred_persistence)
    finally:
        os.chdir(previous)


def _assess(root: Path, deferred_persistence=None):
    from governance_state import roadmap_records, ROADMAP
    from specification_intake import spec_entries
    roadmap = root / ROADMAP
    statuses = {r['id']: r['Status'] for r in roadmap_records(roadmap)} if roadmap.is_file() else {}
    features = []
    compatibility = []
    ledger = root / 'docs/architecture/bootstrap-prerequisites.json'
    if ledger.is_file():
        from bootstrap_lifecycle import validate_prerequisites
        try:
            blockers = validate_prerequisites(root, roadmap_records(roadmap))
            compatibility = [{'id': item['id'], 'ready': False, 'diagnostic': item['task']} for item in blockers]
        except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
            compatibility = [{'id': 'bootstrap-compatibility', 'ready': False, 'diagnostic': str(error),
                              'continuation': 'Review changed tooling/design through the supported native post-bootstrap recovery; preserve historical receipts.',
                              'renewal': compatibility_renewal(root)}]
    for spec in sorted((root / 'specs').glob('*/spec.md')):
        feature = spec.parent
        checks = []
        entries = spec_entries(spec.read_text(encoding='utf-8'))
        phase = 'delivery' if any(statuses.get(e) == 'Delivered' for e in entries) else 'implementation'
        for phase in (phase,):
            try:
                required = ['phase-obligations.json', 'obligation-design.json', 'obligation-review.json']
                if phase == 'delivery':
                    required += ['verification-plan.json', 'verification-results.json']
                missing = [name for name in required if not (feature / name).is_file()]
                if missing:
                    raise ValueError('Renew affected phase evidence: missing ' + ', '.join(missing))
                check(root, feature, phase)
                checks.append({'phase': phase, 'ready': True, 'diagnostic': None})
            except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
                checks.append({'phase': phase, 'ready': False, 'diagnostic': str(error)})
        features.append({'featureDirectory': feature.relative_to(root).as_posix(), 'checks': checks,
                         'migrationVerificationRequired': phase_verification_required(root, feature, phase),
                         'continuation': 'Use installed feature intake if confirmed authority is stale; then phase-context, plan/tasks hooks and required verification. Preserve existing spec identity and consumer code. Review only affected evidence; never synthesize approval or passing receipts.'})
    result = {'schemaVersion': 1, 'scope': 'consumer-phase-readiness',
              'applicationReady': not deferred_persistence and not compatibility and all(c['ready'] for f in features for c in f['checks']),
              'features': features,
              'compatibility': compatibility,
              'deferredPersistenceAdmissions': deferred_persistence or [],
              'note': 'Offline managed setup completion does not establish consumer behavior or delivery acceptance.'}
    atomic_write(root / '.specify/governance/upgrade-remediation.json', result)
    return result

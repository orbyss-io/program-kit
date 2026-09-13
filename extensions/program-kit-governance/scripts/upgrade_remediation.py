"""Separate offline setup convergence from required consumer phase remediation."""
from pathlib import Path

from phase_obligations import check
from lifecycle_state import atomic_write


def assess(root: Path):
    from governance_state import roadmap_records, ROADMAP
    from specification_intake import spec_entries
    roadmap = root / ROADMAP
    statuses = {r['id']: r['Status'] for r in roadmap_records(roadmap)} if roadmap.is_file() else {}
    features = []
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
                         'continuation': 'Use installed feature intake if confirmed authority is stale; then phase-context, plan/tasks hooks and required verification. Preserve existing spec identity and consumer code. Review only affected evidence; never synthesize approval or passing receipts.'})
    result = {'schemaVersion': 1, 'scope': 'consumer-phase-readiness',
              'applicationReady': all(c['ready'] for f in features for c in f['checks']),
              'features': features,
              'note': 'Offline managed setup completion does not establish consumer behavior or delivery acceptance.'}
    atomic_write(root / '.specify/governance/upgrade-remediation.json', result)
    return result

"""Report tooling maintenance independently of application work and old proof records."""
from pathlib import Path

def phase_verification_required(root, feature, phase):
    from consumer_upgrade import scan, request_scope
    result = scan(Path(root), request_scope(Path(root), feature=Path(feature)), phase)
    return not result['canProceed']

def migration_phase_ready(remediation):
    if remediation.get('consumerUpgrade') is not None:
        return remediation['consumerUpgrade'].get('upgradePrepared') is True
    return remediation.get('migrationVerificationEstablished') is True

def compatibility_renewal(root):
    return {'scope':'historical-bootstrap','workflowStarted':False,'approvalPerformed':False,
            'historicalEvidenceChanged':False,'proofs':[],'command':None,
            'instruction':'Historical bootstrap results are retained unchanged. Run current engineering checks for changed application inputs.'}

def assess(root: Path, deferred_persistence=None):
    features = [{'featureDirectory':p.parent.relative_to(root).as_posix(),
                 'migrationVerificationRequired':False,
                 'checks':[], 'continuation':'Continue the normal Spec Kit plan/tasks/implementation flow; run the affected application tests.'}
                for p in sorted((root / 'specs').glob('*/spec.md'))]
    from consumer_upgrade import RECORD, readiness
    scoped = readiness(root) if (root / RECORD).is_file() else None
    if scoped:
        from consumer_upgrade import scan, request_scope
        for feature in features:
            view = scan(root, request_scope(root, feature=root / feature['featureDirectory']), 'implementation')
            feature.update(migrationVerificationRequired=not view['canProceed'],
                           checks=[m['id'] for m in view['migrations']],
                           continuation='Resolve only due affected upgrade work through migration pickup; retain normal plan/tasks and unaffected work.'
                           if not view['canProceed'] else feature['continuation'])
    return {'schemaVersion':1,'scope':'tooling-maintenance','migrationVerificationEstablished':True,
            'consumerUpgrade': scoped,
            'applicationReady':None,'applicationChecksPerformed':False,'releaseReadinessEstablished':False,
            'features':features,'compatibility':[], 'deferredPersistenceAdmissions':deferred_persistence or [],
            'note':'Installation/migration verification does not assert application correctness. Unfinished features and old bootstrap receipts are not upgrade requirements.'}

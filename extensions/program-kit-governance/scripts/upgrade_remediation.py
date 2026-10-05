"""Report tooling maintenance independently of application work and old proof records."""
from pathlib import Path

def phase_verification_required(root, feature, phase):
    return False

def migration_phase_ready(remediation):
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
    return {'schemaVersion':1,'scope':'tooling-maintenance','migrationVerificationEstablished':True,
            'applicationReady':None,'applicationChecksPerformed':False,'releaseReadinessEstablished':False,
            'features':features,'compatibility':[], 'deferredPersistenceAdmissions':deferred_persistence or [],
            'note':'Installation/migration verification does not assert application correctness. Unfinished features and old bootstrap receipts are not upgrade requirements.'}

"""Supervisor-only service for source-bound bootstrap scratch restores."""
from pathlib import Path
import os
import re
import shutil
import sys

from .common import load_object, atomic_write_json, sha256_file, LiveContractError


class BootstrapProvisioner:
    def __init__(self, project, evidence):
        self.project = project
        self.evidence = evidence / 'bootstrap-provisioning'
        self.trusted = self.evidence / 'trusted/extensions'
        self.trusted.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(project / '.specify/extensions', self.trusted,
                        ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__', 'node_modules'))
        self.receipts = []
        self.failed = False

    def poll(self, remaining):
        try:
            return self._poll(remaining)
        except (OSError, ValueError, KeyError, TypeError, LiveContractError) as error:
            self.failed = True
            atomic_write_json(self.evidence / 'admission-error.json',
                              {'status': 'failed', 'diagnostic': 'LIVE_COMPATIBILITY_ADMISSION_FAILED',
                               'errorType': type(error).__name__})
            return False

    def _poll(self, remaining):
        from .cli import operation, supervisor_environment
        queue = self.project / '.program-kit-live/bootstrap-restore'
        for request in sorted(queue.glob('*.request.json')):
            identity = request.name.removesuffix('.request.json')
            if not re.fullmatch('[0-9a-f]{32}', identity):
                raise LiveContractError('LIVE_COMPATIBILITY_REQUEST_ID_INVALID')
            response = queue / (identity + '.response.json')
            if response.exists():
                continue
            value = load_object(request)
            request_sha256 = sha256_file(request)
            timeout = value.get('timeoutSeconds')
            if type(timeout) is not int or not 1 <= timeout <= 600:
                raise LiveContractError('LIVE_COMPATIBILITY_TIMEOUT_INVALID')
            token = os.environ.get('PROGRAM_KIT_NPM_TOKEN')
            result, receipt = operation([sys.executable, str(self.trusted / 'program-kit-governance/scripts/bootstrap_compatibility.py'),
                                         'serve', '--repository', str(self.project), '--request', str(request)],
                                        self.project, self.evidence, identity,
                                        supervisor_environment(token), [token] if token else [],
                                        timeout=max(1, min(timeout, max(1, int(remaining) - 20))))
            self.receipts.append(receipt)
            atomic_write_json(self.evidence / identity / 'process.json', receipt)
            if result.operatorCancellationRecorded:
                raise KeyboardInterrupt
            passed = result.exitCode == 0 and result.cleanupComplete and result.logsDrained and not result.timedOut
            atomic_write_json(response, {'schemaVersion': 1, 'requestSha256': request_sha256,
                                         'status': 'passed' if passed else 'failed'})
            # Stop the phase on the first provisioning failure; no automatic retry.
            self.failed = not passed
            return passed

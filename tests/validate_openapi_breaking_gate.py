"""Exercise the native OpenAPI gate with a real exact-version oasdiff executable.

Only synthetic contracts and explicitly fictional review data are used. This is
tool integration evidence, not approval of a consumer contract change.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from live.v2.supervisor import run_supervised

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(ENG))
import openapi_contracts as contracts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--oasdiff', default=os.environ.get('PROGRAMKIT_OASDIFF_COMMAND') or shutil.which('oasdiff'))
    parser.add_argument('--oasdiff-version', default=(ENG.parent / '.oasdiff-version').read_text().strip())
    parser.add_argument('--script', type=Path, default=ENG / 'openapi_contracts.py',
                        help='Explicit historical script for before/after diagnosis only')
    args = parser.parse_args()
    args.script = args.script.resolve()
    if not args.oasdiff:
        parser.error('An existing exact-version oasdiff executable is required; this validator installs nothing')
    executable = Path(shutil.which(args.oasdiff) or args.oasdiff).resolve()
    if not executable.is_file():
        parser.error('The selected oasdiff executable is unavailable')
    args.oasdiff = str(executable)
    evidence = ROOT / 'artifacts/openapi-breaking-gate' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    result = {'status': 'running', 'fictionalReview': True, 'steps': [],
              'scriptSha256': hashlib.sha256(args.script.read_bytes()).hexdigest(),
              'oasdiffVersion': args.oasdiff_version,
              'oasdiffExecutableSha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'oasdiffExecutable': str(args.oasdiff), 'startedAt': datetime.now(timezone.utc).isoformat()}

    def run(label, command, expected, marker=None):
        directory = evidence / label
        observed = run_supervised([str(x) for x in command], cwd=evidence,
            environment=dict(os.environ, PYTHONUTF8='1'), evidence_directory=directory, timeout_seconds=60)
        result['steps'].append({'id': label, 'exitCode': observed.exitCode,
                               'expectedExitCode': expected, 'cleanupComplete': observed.cleanupComplete,
                               'logsDrained': observed.logsDrained, 'timedOut': observed.timedOut})
        text = ''.join((directory / name).read_text(encoding='utf-8')
                       for name in ('workflow.stdout.log', 'workflow.stderr.log'))
        if (observed.exitCode != expected or observed.timedOut
                or not observed.cleanupComplete or not observed.logsDrained or marker and marker not in text):
            raise ValueError('Unexpected native OpenAPI result: ' + str(directory))

    try:
        contracts.check_tool(args.oasdiff, args.oasdiff_version)
        base = {'openapi': '3.0.3', 'info': {'title': 'Synthetic items', 'version': '1.0.0'},
                'paths': {'/items': {'get': {'operationId': 'ListItems',
                    'responses': {'200': {'description': 'OK'}}}}}}
        changed = copy.deepcopy(base)
        changed['paths']['/items']['get']['parameters'] = [
            {'name': 'X-Required', 'in': 'header', 'required': True, 'schema': {'type': 'string'}}]
        baseline, generated, artifact, approval = [evidence / name for name in
            ('baseline.json', 'generated.json', 'artifact.json', 'approval.json')]
        baseline.write_bytes(contracts.canonical_bytes(base))
        generated.write_bytes(contracts.canonical_bytes(changed))
        # This control establishes the actual tool's default-success behavior;
        # the wrapper must explicitly select the failure threshold.
        run('native-default', [args.oasdiff, 'breaking', baseline, generated, '--format', 'json'], 0, 'new-required-request-parameter')
        run('native-error-threshold', [args.oasdiff, 'breaking', baseline, generated,
                                      '--format', 'json', '--fail-on', 'ERR'], 1, 'new-required-request-parameter')
        command = [sys.executable, args.script, '--generated', generated, '--artifact', artifact,
                   '--baseline', baseline, '--oasdiff', args.oasdiff, '--oasdiff-version', args.oasdiff_version,
                   '--write-generated']
        run('unapproved-breaking', command, 2, 'PKO011')
        approval.write_text(json.dumps({'baselineSha256': contracts.digest(baseline.read_bytes()),
            'revisionSha256': 'stale', 'oasdiffVersion': args.oasdiff_version,
            'approvedBy': 'Synthetic regression only; no consumer approval'}), encoding='utf-8')
        run('stale-review', [*command, '--approval', approval], 2, 'PKO011')
        review = json.loads(approval.read_text())
        review['revisionSha256'] = contracts.digest(contracts.canonical_bytes(changed))
        approval.write_text(json.dumps(review), encoding='utf-8')
        run('exact-fictional-review', [*command, '--approval', approval], 0)
        generated.write_bytes(baseline.read_bytes())
        run('unchanged-without-review', command, 0)
        if contracts.digest(args.script.read_bytes()) != result['scriptSha256']:
            raise ValueError('OpenAPI gate source changed during native qualification')
        result['status'] = 'passed'
        return 0
    except Exception as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    finally:
        (evidence / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('OpenAPI gate evidence: ' + str(evidence / 'results.json'))


if __name__ == '__main__':
    raise SystemExit(main())

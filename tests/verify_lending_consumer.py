"""Independent acceptance of an unchanged completed live lending checkpoint.

Builds and runs real HTTP/restart/browser checks; agent summaries and incomplete
upgrade handoffs cannot establish acceptance. No coding agent is invoked.
"""
import argparse
import sys
import uuid
from pathlib import Path

from live.v2 import cli, sync_stages
from live.v2.common import LiveContractError, atomic_write_json, canonical_sha256, file_inventory, load_object, safe_relative, sha256_file, utc_now, validate
from live.v2.lending_host import PublishedLendingHost, unpack_release_bundle, verify
from live.v2.supervisor import run_supervised

ROOT = Path(__file__).resolve().parents[1]


def verify_run(run_path, bundle_path, browser_modules, engines):
    run = load_object(run_path)
    unsigned = dict(run)
    if unsigned.pop('manifestSha256', None) != canonical_sha256(unsigned):
        raise LiveContractError('LENDING_ACCEPTANCE_RUN_SEAL_CHANGED')
    validate(run, load_object(cli.schemas(ROOT) / 'evidence-manifest.schema.json'))
    if run['phase'] not in {'feature-delivery', 'upgrade-consumer', 'upgrade-continuation'} or run['status'] != 'checkpoint-created':
        raise LiveContractError('LENDING_ACCEPTANCE_COMPLETED_CHECKPOINT_REQUIRED')
    process = run['process']
    if process.get('exitCode') != 0 or not process.get('cleanupComplete') or not process.get('logsDrained'):
        raise LiveContractError('LENDING_ACCEPTANCE_WORKER_INCOMPLETE')
    authorization = load_object(ROOT / 'artifacts/live-acceptance/v2/authorizations/consumed' / (run['authorization']['authorizationId'] + '.json'))
    if canonical_sha256(authorization) != run['authorization']['authorizationSha256'] or authorization['candidate'].get('harnessSha256') != sync_stages.harness_digest():
        raise LiveContractError('LENDING_ACCEPTANCE_AUTHORIZED_HARNESS_CHANGED')
    project = ROOT / safe_relative(run['workspace'])
    checkpoint = load_object(Path(run['checkpoint']))
    validate(checkpoint, load_object(cli.schemas(ROOT) / 'checkpoint.schema.json'))
    if (checkpoint['candidate'] != run['candidate']['releaseReceiptSha256'] or checkpoint['phase'] != run['phase']
            or file_inventory(project) != checkpoint['files']):
        raise LiveContractError('LENDING_ACCEPTANCE_CHECKPOINT_CHANGED')
    evidence = ROOT / 'artifacts/lending-acceptance' / uuid.uuid4().hex[:8]
    evidence.mkdir(parents=True)
    toolchain = load_object(project / '.program-kit/evidence/toolchain.json')
    runtime = cli._load_restore_module(project / '.program-kit/eng/js_toolchain.py')
    for name in ('dotnet', 'node', 'npm'):
        if runtime.version(toolchain['commands'][name], project) != toolchain['required'][name]:
            raise LiveContractError('LENDING_ACCEPTANCE_EXACT_RUNTIME_UNAVAILABLE: ' + name)
    operations = []
    result = {'schemaVersion': 1, 'status': 'failed', 'functionalAcceptance': False,
              'runManifestSha256': sha256_file(run_path), 'checkpointSha256': sha256_file(Path(run['checkpoint'])),
              'consumerInventorySha256': canonical_sha256(checkpoint['files']), 'startedAt': utc_now(), 'operations': operations,
              'scope': 'Independent HTTP/restart/browser behavior plus current installed delivery obligations. Semantic/adoption review remains attributable evidence, not a universal proof.'}
    def operation(command, name, cwd=project):
        process = run_supervised(command, cwd=cwd, environment=cli.supervisor_environment(), evidence_directory=evidence / name, timeout_seconds=180)
        operations.append({'command': command, 'process': process.as_dict()})
        if process.exitCode != 0 or not process.cleanupComplete or not process.logsDrained:
            raise LiveContractError('LENDING_ACCEPTANCE_OPERATION_FAILED: ' + name)
    try:
        dotnet = toolchain['commands']['dotnet']
        operation([*dotnet, 'build', 'Lending.slnx', '--no-restore'], 'dotnet-build')
        operation([sys.executable, str(project / '.program-kit/eng/js_toolchain.py'), '--repository', str(project), 'npm', '--', 'run', 'verify'], 'web-build', project / 'web')
        archive = project / safe_relative(bundle_path)
        manifest = unpack_release_bundle(archive, evidence / 'bundle')
        image = manifest['hostImage']['reference']
        result.update(bundleSha256=sha256_file(archive), hostImage=image)
        operation(['docker', 'pull', image], 'published-host-pull')
        def host_factory(directory, environment):
            return PublishedLendingHost(evidence / 'bundle', image, project, directory, environment)
        contract = load_object(ROOT / 'tests/live/scenarios/knowledge-application/v1/http-contract.json')
        result['http'] = verify(['docker', 'run', image], project, evidence / 'http', cli.supervisor_environment(), contract, host_factory=host_factory)
        environment = {**cli.supervisor_environment(), 'LENDING_FIXTURE_WEB': str(project / 'web/dist')}
        with host_factory(evidence / 'browser/host', environment) as browser_host:
            script = ROOT / 'tests/fixtures/knowledge-application/oracle-browser/browser.mjs'
            operation([*toolchain['commands']['node'], str(script), '--url=' + browser_host.url, '--engines=' + engines,
                       '--modules=' + str(browser_modules), '--output=' + str(evidence / 'browser/results.json')], 'browser-process')
        result['browser'] = load_object(evidence / 'browser/results.json')
        if result['browser']['status'] != 'passed':
            raise LiveContractError('LENDING_ACCEPTANCE_BROWSER_FAILED')
        feature = load_object(project / '.specify/feature.json')['feature_directory']
        operation([sys.executable, str(project / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py'),
                   'check', '--repository', str(project), '--feature-dir', feature, '--phase', 'delivery'], 'delivery-obligations')
        if file_inventory(project) != checkpoint['files']:
            raise LiveContractError('LENDING_ACCEPTANCE_SOURCE_CHANGED_DURING_VERIFICATION')
        result.update(status='passed', functionalAcceptance=True)
    except Exception as error:
        result['diagnostic'] = str(error)
        raise
    finally:
        result['finishedAt'] = utc_now()
        atomic_write_json(evidence / 'acceptance.json', result)
        print('Independent lending acceptance evidence: ' + str(evidence / 'acceptance.json'))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-manifest', type=Path, required=True)
    parser.add_argument('--bundle', required=True, help='Repository-relative application-bundle.zip for the published Foundation host')
    parser.add_argument('--browser-modules', type=Path, required=True)
    parser.add_argument('--engines', default='chromium,webkit')
    args = parser.parse_args()
    verify_run(args.run_manifest.resolve(), args.bundle, args.browser_modules.resolve(), args.engines)

"""Published Forms package/renderer integration. Never invokes a coding agent."""
import argparse
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from repository_sync import audit_toolchain, provider, write
from live.v2.supervisor import run_supervised


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--engines', default='chromium,webkit' if os.name == 'nt' else 'chromium,firefox,webkit')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(engines) != len(set(engines)) or set(engines) - {'chromium', 'webkit', 'firefox'}:
        parser.error('Specify distinct supported browser engines')
    source = ROOT / 'tests/fixtures/knowledge-application/forms-browser-packages'
    package = json.loads((source / 'package.json').read_text(encoding='utf-8'))
    from live.v2.common import sha256_file
    provenance = json.loads((source / 'provenance.json').read_text(encoding='utf-8'))
    for record in provenance['files']:
        if sha256_file(source / record['path']) != record['sha256']:
            raise ValueError('Published Forms fixture source differs from reviewed provenance')
    if args.prepare_only:
        print(json.dumps({'prepared': True, 'paidSessionsStarted': 0, 'packageOperationsStarted': 0,
                          'engines': engines, 'packages': package, 'credentialReference': 'PROGRAM_KIT_NPM_TOKEN'}))
        return 0
    token = os.environ.get('PROGRAM_KIT_NPM_TOKEN')
    if not token:
        print('PROGRAM_KIT_NPM_TOKEN must be set in the invoking terminal. No package operation was started.', file=sys.stderr)
        return 2
    destination = ROOT / 'artifacts/published-forms-browser' / uuid.uuid4().hex[:8]
    shutil.copytree(source, destination)
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ('.nvmrc', '.npm-version'):
        shutil.copyfile(template / name, destination / name)
    audit_toolchain(destination, {'node': (destination / '.nvmrc').read_text().strip(),
                                  'npm': (destination / '.npm-version').read_text().strip()})
    toolchain = json.loads((destination / '.program-kit/evidence/toolchain.json').read_text(encoding='utf-8'))
    node = toolchain['commands']['node']
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    lock = destination / '.program-kit/sync/dependencies.json'
    plan = {'schemaVersion': 1, 'targets': [{'path': 'package.json', 'packages': [{'materializationKind': 'npm-dependency'}]}], 'registryRequirements': []}
    write(lock, plan)
    def operation(command, name, credentials=False):
        environment = os.environ.copy()
        if not credentials:
            environment.pop('PROGRAM_KIT_NPM_TOKEN', None)
        result = run_supervised(command, cwd=destination, environment=environment,
                                evidence_directory=destination / 'evidence' / name,
                                timeout_seconds=600, secrets=[token])
        write(destination / 'evidence' / name / 'process.json', result.as_dict())
        if result.exitCode != 0 or result.timedOut or not result.cleanupComplete or not result.logsDrained:
            raise ValueError('Published Forms test failed; inspect redacted evidence: ' + str(destination / 'evidence' / name))
    operation([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/npm_graph.py'),
               '--repository', str(destination), '--package-json', str(destination / 'package.json'),
               '--evidence', str(destination / '.program-kit/evidence/npm-graph.json')], 'strict-graph', True)
    request = destination / '.program-kit/evidence/building-block-restore-request.json'
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(destination, lock, plan, mode))
        operation([sys.executable, str(executor.__file__), mode, '--target', str(destination), '--lock', str(lock),
                   '--request', str(request), '--approved'], mode, True)
    operation([*node, '--test', 'tests/release-integration.test.mjs'], 'admission')
    operation([*node, 'tests/forms-browser/build.mjs'], 'bundle')
    operation([*node, 'tests/forms-browser/browser.mjs', '--engines=' + args.engines], 'browser')
    print('Published Forms admission and browser checks passed; evidence: ' + str(destination))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)

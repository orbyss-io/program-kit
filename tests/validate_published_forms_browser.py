"""Published Forms package/renderer integration. Never invokes a coding agent."""
import argparse
import json
import hashlib
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
    parser.add_argument('--profile', type=Path, help='Qualify an exact candidate profile instead of the installed new-project default.')
    parser.add_argument('--catalog', type=Path, help='Explicit target catalog for the exact candidate profile.')
    parser.add_argument('--engines', default='chromium,webkit' if os.name == 'nt' else 'chromium,firefox,webkit')
    args = parser.parse_args()
    if args.catalog is not None and args.profile is None:
        parser.error('--catalog requires an explicit --profile')
    engines = args.engines.split(',')
    if not engines or len(engines) != len(set(engines)) or set(engines) - {'chromium', 'webkit', 'firefox'}:
        parser.error('Specify distinct supported browser engines')
    source = ROOT / 'tests/fixtures/knowledge-application/forms-browser-packages'
    package = json.loads((source / 'package.json').read_text(encoding='utf-8'))
    from live.v2.common import sha256_file
    provenance = json.loads((source / 'provenance.json').read_text(encoding='utf-8'))
    for record in provenance['files']:
        if hashlib.sha256((source / record['path']).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != record['sha256']:
            raise ValueError('Published Forms fixture source differs from reviewed provenance')
    # The reviewed fixture defines behavior; its package pins follow the profile
    # being qualified so a new default cannot reuse browser acceptance of old pins.
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
    import building_blocks as blocks
    catalog = (blocks.materialize_dependency_profile(blocks.load_json(args.catalog or blocks.default_catalog(Path(blocks.__file__))),
               blocks.load_json(args.profile)) if args.profile else blocks.new_project_catalog())
    for group in ('dependencies', 'devDependencies'):
        for identity in package.get(group, {}):
            key = 'npm:' + identity
            if key in catalog['packages']:
                package[group][identity] = catalog['packages'][key]['version']
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
    write(destination / 'package.json', package)
    write(destination / 'qualification-profile.json', {'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog),
        'packages': {key: value for group in ('dependencies', 'devDependencies')
                     for key, value in package.get(group, {}).items() if key.startswith('@orbyss-io/')}})
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ('.nvmrc', '.npm-version'):
        shutil.copyfile(template / name, destination / name)
    audit_toolchain(destination, {'node': (destination / '.nvmrc').read_text().strip(),
                                  'npm': (destination / '.npm-version').read_text().strip()})
    toolchain = json.loads((destination / 'artifacts/program-kit/toolchain.json').read_text(encoding='utf-8'))
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
               '--evidence', str(destination / 'artifacts/program-kit/npm-graph.json')], 'strict-graph', True)
    request = destination / 'artifacts/program-kit/building-block-restore-request.json'
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(destination, lock, plan, mode))
        operation([sys.executable, str(executor.__file__), mode, '--target', str(destination), '--lock', lock.relative_to(destination).as_posix(),
                   '--request', request.relative_to(destination).as_posix(), '--approved'], mode, True)
    browser_install = [*node, 'node_modules/playwright/cli.js', 'install']
    if os.name != 'nt':
        browser_install.append('--with-deps')
    operation([*browser_install, *engines], 'browser-install')
    operation([*node, 'tests/forms-browser/build.mjs'], 'bundle')
    operation([*node, 'tests/forms-browser/browser.mjs', '--engines=' + args.engines], 'browser')
    write(destination / 'qualification-result.json', {'satisfied': True, 'engines': engines,
        'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog)})
    print('Published Forms consumer restore, build, and browser checks passed; evidence: ' + str(destination))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)

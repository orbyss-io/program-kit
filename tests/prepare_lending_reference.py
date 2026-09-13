"""Prepare a fictional mixed-stack reference using actual pinned released archives.

No coding agent or historical checkpoint is created. This prepares behavior and
installation evidence; governance/reference admission is a distinct subsequent gate.
"""
import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from live.v2.common import load_object, sha256_file, atomic_write_json, file_inventory, canonical_sha256, LiveContractError
from live.run_bootstrap_acceptance import safe_extract, specify_bridge_command
from live.v2.cli import supervisor_environment
from live.v2.supervisor import run_supervised
from live.v2.lending_host import verify, LendingHost
from repository_sync import audit_toolchain, provider, write


def verify_browser(project, evidence, toolchain, browser_modules, engines):
    host = project / 'tests/Lending.FixtureHost/bin/Debug/net10.0/Lending.FixtureHost.dll'
    browser_script = ROOT / 'tests/fixtures/knowledge-application/oracle-browser/browser.mjs'
    environment = {**supervisor_environment(), 'LENDING_FIXTURE_WEB': str(project / 'web/dist')}
    with LendingHost([*toolchain['commands']['dotnet'], str(host)], project, evidence / 'host', environment) as owned_host:
        command = [*toolchain['commands']['node'], str(browser_script), '--url=' + owned_host.url,
                   '--engines=' + engines, '--modules=' + str(browser_modules), '--output=' + str(evidence / 'results.json')]
        result = run_supervised(command, cwd=project, environment=supervisor_environment(),
                               evidence_directory=evidence / 'process', timeout_seconds=120)
        atomic_write_json(evidence / 'process/process.json', result.as_dict())
        if result.exitCode != 0 or not result.logsDrained or not result.cleanupComplete:
            raise LiveContractError('LENDING_REFERENCE_BROWSER_PROCESS_FAILED')
    record = load_object(evidence / 'results.json')
    if record['status'] != 'passed':
        raise LiveContractError('LENDING_REFERENCE_BROWSER_FAILED')
    return record


def prepare(inputs, destination, browser_modules=None, engines='chromium,webkit'):
    descriptor_path = ROOT / 'tests/live/scenarios/knowledge-application/v1/reference-source.json'
    descriptor = load_object(descriptor_path)
    for asset in descriptor['assets']:
        source = inputs / asset['name']
        if not source.is_file() or sha256_file(source) != asset['sha256']:
            raise LiveContractError('LENDING_REFERENCE_RELEASE_ASSET_CHANGED: ' + asset['name'])
    if destination.exists():
        raise LiveContractError('LENDING_REFERENCE_REQUIRES_NEW_DISPOSABLE_DESTINATION')
    destination.mkdir(parents=True)
    release = destination / 'r'
    safe_extract(inputs / f"program-kit-{descriptor['version']}.zip", release)
    for record in descriptor['sourceFiles']:
        source = descriptor_path.parent / 'reference-source-files' / record['path']
        if sha256_file(source) != record['sha256']:
            raise LiveContractError('LENDING_REFERENCE_RELEASE_SOURCE_CHANGED')
        target = release / record['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    artifacts = release / 'artifacts'
    artifacts.mkdir()
    for asset in descriptor['assets']:
        shutil.copyfile(inputs / asset['name'], artifacts / asset['name'])
    receipt = load_object(inputs / f"release-receipt-{descriptor['version']}.json")
    project = destination / 'consumer'
    shutil.copytree(ROOT / 'tests/fixtures/knowledge-application/reference-consumer', project)
    setup = []
    commands = [['git', 'init'], specify_bridge_command(release, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools')]
    for name in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
        commands.append(specify_bridge_command(release, 'extension', 'add', str(release / 'extensions' / name), '--dev', '--force'))
    commands.append(specify_bridge_command(release, 'preset', 'add', '--dev', str(release / 'presets/program-kit-governance-preset')))
    commands.append(specify_bridge_command(release, 'workflow', 'add', str(inputs / f"program-kit-bootstrap-{descriptor['version']}.zip"), '--dev'))
    commands.append(specify_bridge_command(release, 'bundle', 'install', str(release / 'bundle.yml'), '--integration', 'codex', loopback_http_only=sys.platform == 'win32'))
    for index, command in enumerate(commands):
        result = run_supervised(command, cwd=project, environment=supervisor_environment(),
            evidence_directory=destination / 'evidence/install' / str(index), timeout_seconds=180)
        setup.append({'command': command, 'process': result.as_dict()})
        if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError('LENDING_REFERENCE_LOCAL_RELEASE_INSTALL_FAILED: ' + str(index))
    template = release / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ('global.json', 'NuGet.config', '.nvmrc', '.npm-version'):
        shutil.copyfile(template / name, project / name)
    pins = {'dotnet': load_object(project / 'global.json')['sdk']['version'],
            'node': (project / '.nvmrc').read_text().strip(), 'npm': (project / '.npm-version').read_text().strip()}
    audit_toolchain(project, pins)
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    projects = ['src/Lending.Core/Lending.Core.csproj', 'src/Lending.Storage/Lending.Storage.csproj', 'tests/Lending.FixtureHost/Lending.FixtureHost.csproj']
    plan = {'schemaVersion': 1, 'targets': [*({'path': path, 'packages': [{'materializationKind': 'nuget-project'}]} for path in projects),
                                         {'path': 'web/package.json', 'packages': [{'materializationKind': 'npm-dependency'}]}], 'registryRequirements': []}
    lock = project / '.program-kit/sync/dependencies.json'
    write(lock, plan)
    environment = supervisor_environment()
    operations = []
    def run(command, name, cwd=project):
        result = run_supervised(command, cwd=cwd, environment=environment,
            evidence_directory=destination / 'evidence' / name, timeout_seconds=600)
        atomic_write_json(destination / 'evidence' / name / 'process.json', result.as_dict())
        operations.append({'name': name, 'command': command, 'process': result.as_dict()})
        if result.exitCode != 0 or result.timedOut or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError('LENDING_REFERENCE_PREPARATION_FAILED: ' + name)
    run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/npm_graph.py'), '--repository', str(project),
         '--package-json', str(project / 'web/package.json'), '--evidence', str(project / '.program-kit/evidence/npm-graph.json')], 'npm-graph')
    request = project / '.program-kit/evidence/building-block-restore-request.json'
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(project, lock, plan, mode))
        run([sys.executable, str(executor.__file__), mode, '--target', str(project), '--lock', str(lock), '--request', str(request), '--approved'], mode)
    executor.verify_evidence(project, plan, load_object(project / '.program-kit/evidence/building-block-restore.json'))
    toolchain = load_object(project / '.program-kit/evidence/toolchain.json')
    run([*toolchain['commands']['dotnet'], 'build', 'Lending.slnx', '--no-restore'], 'build-dotnet')
    node = toolchain['commands']['node']
    run([*node, 'node_modules/typescript/bin/tsc'], 'build-typescript', project / 'web')
    run([*node, 'build.mjs'], 'build-web', project / 'web')
    host = project / 'tests/Lending.FixtureHost/bin/Debug/net10.0/Lending.FixtureHost.dll'
    behavior = verify([*toolchain['commands']['dotnet'], str(host)], project, destination / 'evidence/http', environment,
        load_object(ROOT / 'tests/live/scenarios/knowledge-application/v1/http-contract.json'))
    browser_result = None
    if browser_modules:
        browser_result = verify_browser(project, destination / 'evidence/browser', toolchain, browser_modules, engines)
    result = {'schemaVersion': 1, 'kind': 'reference-preparation', 'status': 'behavior-prepared-not-admitted',
              'release': descriptor, 'descriptorSha256': sha256_file(descriptor_path), 'installedSetup': setup,
              'operations': operations, 'httpStatus': behavior['status'], 'toolchain': toolchain,
              'consumerInventory': file_inventory(project), 'fixtureSha256': canonical_sha256(file_inventory(ROOT / 'tests/fixtures/knowledge-application/reference-consumer')),
              'preparationToolSha256': sha256_file(Path(__file__)),
              'remainingAdmission': ['browser-behavior', 'governed-reference-identity', 'architecture-and-extension-proof', 'sealed-reference-provenance'],
              'historicalLiveCheckpoint': False}
    result['installationMode'] = 'Released local component payloads through supported SpecKit component installation; not public-catalog transport acceptance.'
    if browser_result:
        result['browser'] = browser_result
        result['browserRuntimeLockSha256'] = sha256_file(browser_modules / 'package-lock.json')
        result['remainingAdmission'].remove('browser-behavior')
    atomic_write_json(destination / 'preparation.json', result)
    print('Released reference installation, native locks, builds and independent HTTP behavior prepared: ' + str(destination))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', default=str(ROOT / 'artifacts/reference-inputs/v0.11.0'))
    parser.add_argument('--browser-modules', help='Existing restored independent Playwright/axe package directory; exact pins are verified')
    parser.add_argument('--prepared', help='Add separate browser evidence to an unchanged prepared reference; preserves its original preparation receipt')
    parser.add_argument('--engines', default='chromium,webkit')
    args = parser.parse_args()
    # Keep disposable extraction paths below this Windows host's Win32 path bound.
    destination = ROOT / 'artifacts/lr' / uuid.uuid4().hex[:8]
    try:
        if args.prepared:
            destination = Path(args.prepared).resolve()
            original = destination / 'preparation.json'
            prepared = load_object(original)
            if not args.browser_modules or prepared['consumerInventory'] != file_inventory(destination / 'consumer'):
                raise LiveContractError('LENDING_REFERENCE_UNCHANGED_PREPARATION_AND_BROWSER_RUNTIME_REQUIRED')
            evidence = destination / 'evidence' / ('browser-' + uuid.uuid4().hex[:8])
            result = verify_browser(destination / 'consumer', evidence, prepared['toolchain'], Path(args.browser_modules).resolve(), args.engines)
            atomic_write_json(evidence / 'supplement.json', {'kind': 'reference-browser-supplement', 'preparationSha256': sha256_file(original),
                'consumerInventorySha256': canonical_sha256(prepared['consumerInventory']), 'browser': result,
                'browserOracleSha256': sha256_file(ROOT / 'tests/fixtures/knowledge-application/oracle-browser/browser.mjs'),
                'browserRuntimeLockSha256': sha256_file(Path(args.browser_modules) / 'package-lock.json')})
            print('Independent reference browser supplement passed: ' + str(evidence))
        else:
            prepare(Path(args.inputs).resolve(), destination, Path(args.browser_modules).resolve() if args.browser_modules else None, args.engines)
    except (ValueError, RuntimeError, OSError) as error:
        print(str(error) + '; preserved workspace: ' + str(destination), file=sys.stderr)
        raise SystemExit(2)

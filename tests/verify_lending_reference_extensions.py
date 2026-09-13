"""Supplement an unchanged prepared reference with compiled boundary/DI replacement proof."""
import argparse
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from live.v2.common import load_object, file_inventory, canonical_sha256, sha256_file, atomic_write_json, LiveContractError
from live.v2.supervisor import run_supervised
from live.v2.cli import supervisor_environment
from repository_sync import audit_toolchain, provider, write
from phase_obligations import test_results


def verify(prepared):
    original = prepared / 'preparation.json'
    receipt = load_object(original)
    consumer = prepared / 'consumer'
    if receipt['consumerInventory'] != file_inventory(consumer):
        raise LiveContractError('REFERENCE_CONSUMER_CHANGED')
    destination = prepared / 'evidence' / ('extension-' + uuid.uuid4().hex[:8])
    shutil.copytree(ROOT / 'tests/fixtures/knowledge-application/reference-extension-probe', destination)
    for name in ('global.json', 'NuGet.config'):
        shutil.copyfile(consumer / name, destination / name)
    audit_toolchain(destination, {'dotnet': receipt['toolchain']['required']['dotnet']})
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    plan = {'schemaVersion': 1, 'targets': [{'path': 'Probe.csproj', 'packages': [{'materializationKind': 'nuget-project'}]}], 'registryRequirements': []}
    lock = destination / '.program-kit/sync/dependencies.json'
    write(lock, plan)
    request = destination / '.program-kit/evidence/building-block-restore-request.json'
    commands = []
    def run(command, name, cwd=destination):
        result = run_supervised(command, cwd=cwd, environment=supervisor_environment(), evidence_directory=destination / name, timeout_seconds=180)
        atomic_write_json(destination / name / 'process.json', result.as_dict())
        commands.append({'command': command, 'process': result.as_dict()})
        if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
            raise LiveContractError('REFERENCE_EXTENSION_CHECK_FAILED: ' + str(destination / name))
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(destination, lock, plan, mode))
        run([sys.executable, str(executor.__file__), mode, '--target', str(destination), '--lock', str(lock), '--request', str(request), '--approved'], mode)
    dotnet = receipt['toolchain']['commands']['dotnet']
    run([*dotnet, 'build', 'Lending.slnx', '--no-restore'], 'rebuild-consumer', consumer)
    assemblies = {name: sha256_file(consumer / f'src/{name}/bin/Debug/net10.0/{name}.dll') for name in ('Lending.Core', 'Lending.Storage')}
    run([*dotnet, 'run', '--project', 'Probe.csproj', '--no-restore', '-p:ConsumerRoot=' + str(consumer)], 'behavior')
    results = test_results(destination / 'results.xml', 'junit')
    expected = {'ReferenceExtensions.core-dependencies', 'ReferenceExtensions.runtime-resolution-and-replacement'}
    if set(results) != expected or not all(results.values()) or file_inventory(consumer) != receipt['consumerInventory']:
        raise LiveContractError('REFERENCE_EXTENSION_PROOF_INCOMPLETE_OR_SOURCE_CHANGED')
    atomic_write_json(destination / 'supplement.json', {'schemaVersion': 1, 'kind': 'reference-extension-supplement', 'status': 'passed',
        'preparationSha256': sha256_file(original), 'consumerInventorySha256': canonical_sha256(receipt['consumerInventory']),
        'probeSources': file_inventory(ROOT / 'tests/fixtures/knowledge-application/reference-extension-probe'),
        'resultsSha256': sha256_file(destination / 'results.xml'), 'checks': results, 'operations': commands, 'compiledAssemblies': assemblies,
        'scope': 'Actual compiled Core boundary and DI adapter replacement behavior; this does not assert CShell topology for the legacy reference.'})
    print('Reference compiled boundary and replacement behavior passed: ' + str(destination))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', required=True)
    args = parser.parse_args()
    verify(Path(args.prepared).resolve())

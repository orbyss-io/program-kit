"""Real published host compatibility. No coding agent or consumer mutation."""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from repository_sync import audit_toolchain, provider, write
from compatibility_process import run as bounded_run


def runtime_contract_module():
    path = ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime/runtime_probe.py'
    spec = importlib.util.spec_from_file_location('published_host_runtime_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_environment(credential_names=()):
    return runtime_environment_from(os.environ, credential_names)


def retarget_fixture(target, catalog, shared_contracts):
    # All changed restore policy and pins belong to this disposable fixture.
    for project in target.rglob('*.csproj'):
        value = ET.parse(project)
        for reference in value.iter('PackageReference'):
            package = catalog['packages'].get('nuget:' + reference.get('Include', ''))
            if package:
                reference.set('Version', package['version'])
        if shared_contracts:
            pruning = list(value.iter('RestoreEnablePackagePruning'))
            if not pruning:
                group = ET.SubElement(value.getroot(), 'PropertyGroup')
                pruning = [ET.SubElement(group, 'RestoreEnablePackagePruning')]
            for setting in pruning:
                setting.text = 'false'
        value.write(project, encoding='utf-8', xml_declaration=True)


def capture_public_host(target, image, runner=subprocess.run, credential_names=()):
    """Capture the neutral Host at its exact public digest; only CShells contracts are shared."""
    contract = runtime_contract_module()
    contract.validate_public_image(image)
    container = 'pk-public-host-capture-' + uuid.uuid4().hex
    payload = target / 'public-host-payload'
    payload.mkdir()
    operations = []
    environment = runtime_environment(credential_names)

    def command(arguments):
        ordinal = len(operations) + 1
        try:
            result = runner(['docker', *arguments], cwd=target, env=environment,
                            capture_output=True, text=True, timeout=300, check=False)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
            (target / f'image-capture-{ordinal}.stdout').write_text(decoded(error.stdout), encoding='utf-8')
            (target / f'image-capture-{ordinal}.stderr').write_text(decoded(error.stderr), encoding='utf-8')
            operations.append({'args': ['docker', *arguments], 'timedOut': True})
            write(target / 'image-capture-operations.json', operations)
            raise
        (target / f'image-capture-{ordinal}.stdout').write_text(result.stdout or '', encoding='utf-8')
        (target / f'image-capture-{ordinal}.stderr').write_text(result.stderr or '', encoding='utf-8')
        operations.append({'args': ['docker', *arguments], 'exitCode': result.returncode})
        write(target / 'image-capture-operations.json', operations)
        if result.returncode:
            raise RuntimeError('Public image capture command failed; retained operation ' + str(ordinal))
        return (result.stdout or '').strip()

    # Pull deliberately precedes create --pull=never. A warm developer image
    # cannot stand in for the independently selected public digest.
    command(['pull', image])
    creation_attempted = False
    try:
        creation_attempted = True
        command(['create', '--name', container, '--pull=never', '--label', 'program-kit.fixture=host-capture', image])
        inspected = json.loads(command(['inspect', container]))
        if (not isinstance(inspected, list) or len(inspected) != 1
                or inspected[0].get('Config', {}).get('Image') != image):
            raise ValueError('Native capture does not select the requested public image digest')
        image_configuration = inspected[0].get('Config', {})
        if any(str(value).upper().startswith('NUPLANE__') for value in image_configuration.get('Env', []) or []):
            raise ValueError('Public image environment overrides the captured Nuplane configuration')
        if any('nuplane' in str(argument).lower() for argument in
               [*(image_configuration.get('Cmd') or []), *(image_configuration.get('Entrypoint') or [])]):
            raise ValueError('Public image command overrides the captured Nuplane configuration')
        command(['cp', container + ':/app/.', str(payload)])
        proof = contract.public_host_contract(payload, image, inspected[0].get('Image'))
    finally:
        if creation_attempted:
            command(['rm', '-v', container])
    write(target / 'public-host-inputs.json', proof)
    return {'path': 'public-host-payload', 'inputs': 'public-host-inputs.json',
            'inputsSha256': contract.file_sha256(target / 'public-host-inputs.json')}


def cleanup_runtime_container(target, pins, runner=subprocess.run):
    """The parent owns one exact labelled container, including after child timeout."""
    contract = runtime_contract_module()
    name = pins['runtimeContainer']
    contract.require(contract.re.fullmatch(r'pk-compat-[0-9a-f]{32}', name) is not None,
                     'Runtime container is not an exact fixture-owned identity')
    operations = []
    receipt = {'container': name, 'removed': False, 'absent': False}

    def command(arguments):
        result = runner(['docker', *arguments], cwd=target, env=runtime_environment(pins.get('credentialEnvironmentNames', [])),
                        capture_output=True, text=True, timeout=60, check=False)
        ordinal = len(operations) + 1
        (target / f'runtime-cleanup-{ordinal}.stdout').write_text(result.stdout or '', encoding='utf-8')
        (target / f'runtime-cleanup-{ordinal}.stderr').write_text(result.stderr or '', encoding='utf-8')
        operations.append({'args': ['docker', *arguments], 'exitCode': result.returncode})
        if result.returncode:
            raise RuntimeError('Owned runtime cleanup command failed; retained operation ' + str(ordinal))
        return (result.stdout or '').strip()

    def found():
        return command(['ps', '--all', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}']).splitlines()

    try:
        identities = found()
        contract.require(len(identities) <= 1, 'Owned runtime cleanup found ambiguous containers')
        if identities:
            inspected = json.loads(command(['inspect', identities[0]]))
            contract.require(isinstance(inspected, list) and len(inspected) == 1
                             and inspected[0].get('Name') == '/' + name
                             and inspected[0].get('Config', {}).get('Image') == pins['hostImage']
                             and inspected[0].get('Config', {}).get('Labels', {}).get('program-kit.owner') == name,
                             'Runtime container ownership is unconfirmed; refusing deletion')
            command(['rm', '-f', '-v', identities[0]])
            receipt['removed'] = True
        contract.require(not found(), 'Owned runtime container still exists after cleanup')
        receipt['absent'] = True
    finally:
        write(target / 'runtime-cleanup.json', {**receipt, 'operations': operations})


def run_prepared_runtime(target, pins, runner=bounded_run, cleanup_runner=subprocess.run):
    # Native process supervision drains and ends the complete child tree before
    # parent-owned Docker cleanup. This path runs no worker or coding agent.
    try:
        with (target / 'runtime.log').open('wb') as stdout, (target / 'runtime.stderr').open('wb') as stderr:
            # The child explicitly sanitizes credentials/configuration before
            # any native command. Restore credentials never enter its process.
            environment = os.environ.copy()
            try:
                os.environ.clear()
                os.environ.update(runtime_environment_from(environment, pins.get('credentialEnvironmentNames', [])))
                code = runner([sys.executable, 'runtime_probe.py'], target, stdout, stderr, 600)
                write(target / 'runtime-process-result.json', {'exitCode': code, 'boundedTimeoutExitCode': 124})
            finally:
                os.environ.clear()
                os.environ.update(environment)
        return code
    finally:
        cleanup_runtime_container(target, pins, runner=cleanup_runner)


def runtime_environment_from(environment, credential_names=()):
    selected = {name.upper() for name in credential_names}
    return {key: value for key, value in environment.items()
            if not any(part in key.upper() for part in ('TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL', 'CONNECTION_STRING'))
            and key.upper() not in selected
            and not key.upper().startswith(('CSHELLS__', 'FOUNDATION__', 'NUPLANE__'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, help='Exact candidate profile; otherwise exercise the qualified default.')
    parser.add_argument('--catalog', type=Path, help='Explicit target catalog for the exact candidate profile.')
    args = parser.parse_args()
    if args.catalog is not None and args.profile is None:
        parser.error('--catalog requires an explicit --profile')
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
    import building_blocks as blocks
    from public_availability import verify_oci
    selected = blocks.load_json(args.profile) if args.profile else None
    catalog = (blocks.materialize_dependency_profile(blocks.load_json(args.catalog or blocks.default_catalog(Path(blocks.__file__))),
               selected) if selected else blocks.new_project_catalog())
    inputs = {'foundationRelease': catalog['families']['foundation']['releaseVersion'],
              'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog)}
    if inputs['foundationRelease'] == '0.3.0':
        inputs['dependencyProfile'] = selected['id'] if selected else blocks.load_json(blocks.profile_registry() / 'index.json')['default']
    shared_contracts = runtime_contract_module().contracts_profile(inputs)
    host = catalog['packages']['oci:ghcr.io/orbyss-io/foundation-host']
    image = verify_oci(host, catalog['sources'][host['source']])['reference']
    # The runtime recipe intentionally uses --pull=never. Provision its exact
    # digest here instead of depending on a warm developer Docker cache.
    if not shared_contracts:
        subprocess.run(['docker', 'pull', image], check=True, timeout=300)
    target = ROOT / 'artifacts/bootstrap-runtime' / uuid.uuid4().hex[:8]
    shutil.copytree(ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime', target)
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    for name in ['global.json', 'NuGet.config']:
        shutil.copyfile(template / name, target / name)
    shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py', target / 'bounded_process.py')
    # Retarget only this disposable fixture. The installed historical example
    # and all consumer projects retain their original reviewed inputs.
    retarget_fixture(target, catalog, shared_contracts)
    inputs['hostImage'] = image
    if shared_contracts:
        inputs['restoreEnablePackagePruning'] = False
        inputs['credentialEnvironmentNames'] = sorted({source['authentication']['credentialEnvironment']
            for source in catalog['sources'].values() if source.get('authentication', {}).get('credentialEnvironment')})
        inputs['hostPayload'] = capture_public_host(target, image, credential_names=inputs['credentialEnvironmentNames'])
        inputs['runtimeContainer'] = 'pk-compat-' + uuid.uuid4().hex
    write(target / 'runtime-inputs.json', inputs)
    audit_toolchain(target, {'dotnet': '10.0.202'})
    executor = provider('program-kit-building-blocks/scripts/restore_dependencies.py')
    plan = {'schemaVersion': 1, 'targets': [{'path': p, 'packages': [{'materializationKind': 'nuget-project'}]} for p in
            ['Core/Core.csproj', 'Feature/Feature.csproj', 'Boundary/Boundary.csproj']], 'registryRequirements': []}
    lock = target / '.program-kit/sync/dependencies.json'
    write(lock, plan)
    request = target / 'artifacts/program-kit/building-block-restore-request.json'
    for mode in ('renew', 'locked'):
        write(request, executor.restore_request(target, lock, plan, mode))
        with (target / (mode + '.log')).open('w', encoding='utf-8') as log:
            result = subprocess.run([sys.executable, str(executor.__file__), mode, '--target', str(target), '--lock', lock.relative_to(target).as_posix(),
                '--request', request.relative_to(target).as_posix(), '--approved'], cwd=target, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        if result.returncode:
            raise RuntimeError('Restore failed: ' + str(target / (mode + '.log')))
    if shared_contracts:
        runtime_code = run_prepared_runtime(target, inputs)
    else:
        with (target / 'runtime.log').open('w', encoding='utf-8') as log:
            result = subprocess.run([sys.executable, 'runtime_probe.py'], cwd=target, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        runtime_code = result.returncode
    if runtime_code:
        print((target / 'runtime.log').read_text(encoding='utf-8', errors='replace')[-12000:])
        if shared_contracts:
            print((target / 'runtime.stderr').read_text(encoding='utf-8', errors='replace')[-12000:])
    else:
        cases = ET.parse(target / 'compatibility-results.xml').getroot()
        if cases.findall('.//failure') or cases.findall('.//error') or len(cases.findall('testcase')) != 5:
            raise ValueError('Published host fixture did not establish all five compatibility cases')
        if shared_contracts:
            runtime_contract_module().verify_retained_runtime_inputs(target, inputs)
        write(target / 'qualification-result.json', {'satisfied': True, 'inputs': inputs,
            'cases': sorted(case.get('classname') + '.' + case.get('name') for case in cases.findall('testcase')),
            'resultsSha256': blocks.raw_sha256(target / 'compatibility-results.xml'),
            **({'runtimePackageInputsSha256': blocks.raw_sha256(target / 'runtime-package-inputs.json'),
                'runtimeSharedBindingsSha256': blocks.raw_sha256(target / 'runtime-shared-bindings.json'),
                'publicHostEvidence': runtime_contract_module().published_host_evidence(target, inputs)}
               if shared_contracts else {})})
    print('Runtime evidence: ' + str(target))
    return runtime_code


if __name__ == '__main__':
    raise SystemExit(main())

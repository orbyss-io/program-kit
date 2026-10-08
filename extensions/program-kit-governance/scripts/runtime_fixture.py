"""Version-aware preparation shared by qualification and consumer recipes."""
import json
import os
import subprocess
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def runtime_environment(credential_names=()):
    selected = {name.upper() for name in credential_names}
    return {key: value for key, value in os.environ.items()
            if not any(part in key.upper() for part in ('TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL', 'CONNECTION_STRING'))
            and key.upper() not in selected
            and not key.upper().startswith(('CSHELLS__', 'FOUNDATION__', 'NUPLANE__'))}


def retarget_project(payload, catalog, abi):
    value = ET.fromstring(payload)
    for reference in value.iter('PackageReference'):
        identity = reference.get('Include', '')
        package = catalog['packages'].get('nuget:' + identity)
        if package: reference.set('Version', package['version'])
        if identity in abi['pins']: reference.set('Version', abi['pins'][identity])
    release = catalog['families']['foundation']['releaseVersion']
    if tuple(map(int, release.split('.'))) >= (0, 3, 0):
        settings = list(value.iter('RestoreEnablePackagePruning'))
        if not settings: settings = [ET.SubElement(ET.SubElement(value, 'PropertyGroup'), 'RestoreEnablePackagePruning')]
        for setting in settings: setting.text = 'false'
    return ET.tostring(value, encoding='utf-8', xml_declaration=True)


def retarget_fixture(target, catalog, abi):
    for path in target.rglob('*.csproj'):
        path.write_bytes(retarget_project(path.read_bytes(), catalog, abi))


def provision_public_host(target, pins):
    import runtime_probe as contract
    if pins.get('identityImage'):
        import re
        if not re.fullmatch(r'.+:\d[^@\s]*@sha256:[0-9a-f]{64}', pins['identityImage']):
            raise ValueError('Managed identity provisioning requires the exact selected tag and digest')
        subprocess.run(['docker', 'pull', pins['identityImage']],
                       env=runtime_environment(pins.get('credentialEnvironmentNames', [])), check=True, timeout=300)
    if contract.contracts_profile(pins):
        pins['hostPayload'] = capture_public_host(target, pins['hostImage'],
            credential_names=pins.get('credentialEnvironmentNames', []), release=pins['foundationRelease'])
        observed = contract.shared_contract_versions(target / pins['hostPayload']['path'])
        if observed != pins['sharedAbi']['pins']:
            raise ValueError('Captured Host shared ABI differs from verified selected publisher pins')
        pins['runtimeContainer'] = 'pk-compat-' + uuid.uuid4().hex
        write(target / 'runtime-inputs.json', pins)
    else:
        subprocess.run(['docker', 'pull', pins['hostImage']], env=runtime_environment(), check=True, timeout=300)


def capture_public_host(target, image, runner=subprocess.run, credential_names=(), release='0.3.0'):
    """Capture the neutral Host at its exact public digest; only CShells contracts are shared."""
    import runtime_probe as contract
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
        proof = contract.public_host_contract(payload, image, inspected[0].get('Image'),release)
    finally:
        if creation_attempted:
            command(['rm', '-v', container])
    write(target / 'public-host-inputs.json', proof)
    return {'path': 'public-host-payload', 'inputs': 'public-host-inputs.json',
            'inputsSha256': contract.file_sha256(target / 'public-host-inputs.json')}

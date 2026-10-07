"""Synthetic activation on the published host; no consumer host project/image is built.

APIs verified against Foundation v0.2.2 (8d60cdd55e7fb9056c83d614786667c04ef78bdf):
Host/Program.cs, FoundationOpenApiFeature and WebDefaults' PolicyProbeFeature.
Build/pack only the synthetic port/features. Runtime dependencies come from the
coordinator's locked restore. No package resolution or restore happens here.
"""
import hashlib
import json
import os
import re
import shutil
import time
import uuid
import sys
import zipfile
from pathlib import Path
from http.client import HTTPConnection
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

CONTRACTS_PROFILE = 'foundation-0.3.0-build-0.2.0-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
CONTRACTS_PROFILES = {CONTRACTS_PROFILE,
    'foundation-0.3.0-build-0.3.0-exporter-0.2.4-forms-0.2.1-localization-0.1.2'}
HOST_SHARED = {
    'CShells.Abstractions': '0.0.29-preview.147',
    'CShells.AspNetCore.Abstractions': '0.0.29-preview.147',
}
CSHELLS_PREVIEW_SOURCE = 'https://f.feedz.io/valence-works/cshells/nuget/index.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def contracts_profile(pins):
    """Admit the contracts protocol with exact selected release and native image binding."""
    release=pins.get('foundationRelease','')
    version=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',release)
    if not version or tuple(map(int,version.groups())) < (0,3,0):
        require('hostPayload' not in pins, 'Historical profiles cannot supply the new Host binding contract')
        return False
    pattern='foundation-'+re.escape(release)+r'-build-\d+\.\d+\.\d+-exporter-\d+\.\d+\.\d+-forms-\d+\.\d+\.\d+-localization-\d+\.\d+\.\d+(?:-q-[0-9a-f]{8})?'
    require(re.fullmatch(pattern,pins.get('dependencyProfile','')) is not None,
            'Foundation contracts require the exact selected profile identity')
    return True


def host_runtime_inventory(payload):
    paths = [p for p in payload.iterdir() if p.is_file() and p.suffix.lower() in ('.dll', '.json')]
    for directory in (payload / 'runtimes', payload / '.orbyss-foundation'):
        if directory.is_dir():
            paths.extend(p for p in directory.rglob('*') if p.is_file()
                         and (directory.name == 'runtimes' or p.suffix.lower() == '.json'
                              or (p.suffix.lower() == '.txt'
                                  and p.relative_to(directory).parts[0] == 'settings-sources')))
    require(not any(p.is_symlink() or not p.resolve().is_relative_to(payload.resolve()) for p in paths),
            'Host payload contains an unsafe runtime path')
    names = [p.relative_to(payload).as_posix() for p in paths]
    require(len(set(n.casefold() for n in names)) == len(names), 'Host runtime names are ambiguous')
    required = {'Orbyss.Foundation.Host.dll', 'Orbyss.Foundation.Host.deps.json',
                'Orbyss.Foundation.Host.runtimeconfig.json', 'appsettings.json', 'shells.json'}
    require(required <= set(names), 'Public Host payload is missing required runtime configuration')
    return {name: file_sha256(payload / name) for name in sorted(names)}


def shared_contract_versions(payload):
    libraries=json.loads((payload/'Orbyss.Foundation.Host.deps.json').read_text(encoding='utf-8'))['libraries']
    versions={}
    for identity in HOST_SHARED:
        selected=[name.rsplit('/',1)[1] for name in libraries if name.rsplit('/',1)[0].casefold()==identity.casefold()]
        require(len(selected)==1 and re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?',selected[0]) is not None,
                'Public Host shared package version is missing or ambiguous: '+identity)
        versions[identity]=selected[0]
    return versions


def public_host_contract(payload, image, image_id, release='0.3.0'):
    validate_public_image(image)
    require(re.fullmatch(r'sha256:[0-9a-f]{64}', image_id or '') is not None, 'Captured native image ID is invalid')
    inventory = host_runtime_inventory(payload)
    require(not any(Path(name).name.casefold().startswith('orbyss.foundation.')
                    and Path(name).suffix.casefold() == '.dll'
                    and name != 'Orbyss.Foundation.Host.dll' for name in inventory),
            'Neutral public Host cannot carry Foundation runtime DLLs')
    configuration = json.loads((payload / 'appsettings.json').read_text(encoding='utf-8'))
    # Reject optional effective configuration that changes the required shared
    # identity policy. Other configuration remains retained and hash-bound.
    for relative in ('appsettings.Production.json', 'hostsettings.json',
                     '.orbyss-foundation/web-profile.shells.json', 'shells.json'):
        path = payload / relative
        if path.is_file():
            overlay = json.loads(path.read_text(encoding='utf-8')).get('Nuplane', {}).get('Loading', {})
            require('SharedAssemblies' not in overlay
                    or overlay['SharedAssemblies'] == configuration.get('Nuplane', {}).get('Loading', {}).get('SharedAssemblies'),
                    'Public Host effective configuration overrides shared identities')
    shared = configuration.get('Nuplane', {}).get('Loading', {}).get('SharedAssemblies')
    require(isinstance(shared, list) and len(shared) == len(HOST_SHARED),
            'Neutral public Host must configure exactly two CShells shared identities')
    names = []
    for entry in shared:
        require(isinstance(entry, dict) and set(entry) == {'Name', 'PublicKeyToken', 'MajorVersion'}
                and entry.get('Name') in HOST_SHARED and entry.get('PublicKeyToken') is None
                and type(entry.get('MajorVersion')) is int and entry['MajorVersion'] == 0,
                'Public Host shared assembly policy differs from the reviewed contract')
        names.append(entry['Name'])
    require(set(names) == set(HOST_SHARED), 'Public Host shared identities are duplicated or incomplete')
    libraries = json.loads((payload / 'Orbyss.Foundation.Host.deps.json').read_text(encoding='utf-8')).get('libraries', {})
    require(not any(name.rsplit('/', 1)[0].casefold().startswith('orbyss.foundation.')
                    and name.rsplit('/', 1)[0] != 'Orbyss.Foundation.Host' for name in libraries),
            'Neutral public Host cannot reference a Foundation runtime package')
    require([name for name in libraries if name.rsplit('/', 1)[0] == 'Orbyss.Foundation.Host']
            == ['Orbyss.Foundation.Host/'+release], 'Public Host native version differs from the selected release')
    for identity, version in shared_contract_versions(payload).items():
        versions = [name.rsplit('/', 1)[1] for name in libraries
                    if name.rsplit('/', 1)[0].casefold() == identity.casefold()]
        require(versions == [version] and identity + '.dll' in inventory,
                'Public Host shared package version or DLL differs: ' + identity)
    return {'schemaVersion': 1, 'image': image, 'imageId': image_id,
            'hostRuntimeFiles': inventory, 'sharedAssemblies': shared}


def validate_public_image(image):
    require(re.fullmatch(r'ghcr\.io/orbyss-io/foundation-host@sha256:[0-9a-f]{64}', image or '') is not None,
            'Host capture must select an immutable public Foundation image digest')


def prepare_shared_runtime(root, pins, assets, runtime_packages):
    """Prove image/archive identity before excluding any native loader root."""
    require(contracts_profile(pins), 'Shared binding preparation requires the exact contracts profile')
    binding = pins.get('hostPayload', {})
    require(set(binding) == {'path', 'inputs', 'inputsSha256'} and binding['path'] == 'public-host-payload'
            and binding['inputs'] == 'public-host-inputs.json', 'Public Host binding paths are not fixture-owned')
    proof_path = root / binding['inputs']
    require(file_sha256(proof_path) == binding['inputsSha256'], 'Public image capture inputs changed')
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    actual = public_host_contract(root / binding['path'], pins['hostImage'], proof.get('imageId'),pins['foundationRelease'])
    shared_versions=shared_contract_versions(root/binding['path'])
    require(proof == actual, 'Captured public Host payload/configuration differs from its recorded inputs')
    roots = [Path(value) for value in assets['packageFolders']]
    archives, bindings, observed, provenance_inputs = [], [], set(), []
    for identity, library in assets['libraries'].items():
        if library['type'] != 'package':
            continue
        package_id, version = identity.rsplit('/', 1)
        relative = Path(library['path']) / f'{package_id.lower()}.{version.lower()}.nupkg'
        require(not relative.is_absolute() and '..' not in relative.parts, 'Restored package archive path is unsafe')
        found = [p / relative for p in roots if (p / relative).is_file()]
        require(len(found) == 1, 'Restored package archive missing or ambiguous: ' + identity)
        source = found[0]
        with zipfile.ZipFile(source) as archive:
            nuspecs = [name for name in archive.namelist() if name.endswith('.nuspec')]
            require(len(nuspecs) == 1, 'Restored archive metadata is ambiguous: ' + identity)
            metadata = ET.fromstring(archive.read(nuspecs[0]))
            require(metadata.find('./{*}metadata/{*}id').text.casefold() == package_id.casefold()
                    and metadata.find('./{*}metadata/{*}version').text == version,
                    'Restored archive metadata differs from native assets: ' + identity)
            canonical = next((name for name in HOST_SHARED if name.casefold() == package_id.casefold()), None)
            record = {'id': identity, 'archive': source.name, 'sha256': file_sha256(source)}
            if canonical:
                require(canonical not in observed and version == shared_versions[canonical],
                        'Shared package is duplicated or selects another exact version: ' + identity)
                assembly = 'lib/net10.0/' + canonical + '.dll'
                require(archive.namelist().count(assembly) == 1, 'Shared archive must contain the exact net10 DLL: ' + identity)
                digest = hashlib.sha256()
                with archive.open(assembly) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(block)
                require(digest.hexdigest() == proof['hostRuntimeFiles'][canonical + '.dll'],
                        'Public shared archive DLL differs from the captured image: ' + identity)
                provenance_path = source.parent / '.nupkg.metadata'
                provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
                require(provenance.get('source') == CSHELLS_PREVIEW_SOURCE,
                        'CShells shared archive was not restored from the public CShells preview source')
                record['nativeSource'] = provenance['source']
                record['nativeProvenanceSha256'] = file_sha256(provenance_path)
                record['nativeProvenance'] = source.name + '.metadata.json'
                provenance_inputs.append((provenance_path, record['nativeProvenance']))
                bindings.append({**record, 'assemblyPath': assembly, 'assemblySha256': digest.hexdigest(),
                                 'omittedRuntimeRoot': True})
                observed.add(canonical)
            archives.append((source, record, canonical is not None))
    require(observed == set(HOST_SHARED), 'Restored native closure omits a Host shared package')
    require(len({source.name.casefold() for source, _, _ in archives}) == len(archives), 'Archive names are ambiguous')
    retained = root / 'runtime-archive-inputs'
    require(not retained.exists(), 'Full runtime archive inputs must use a new owned directory')
    retained.mkdir()
    for source, record, shared in archives:
        shutil.copyfile(source, retained / source.name)
        if not shared:
            shutil.copyfile(source, runtime_packages / source.name)
    for source, relative in provenance_inputs:
        shutil.copyfile(source, retained / relative)
    (root / 'runtime-package-inputs.json').write_text(json.dumps([record for _, record, _ in archives], indent=2) + '\n', encoding='utf-8')
    (root / 'runtime-shared-bindings.json').write_text(json.dumps(bindings, indent=2) + '\n', encoding='utf-8')
    return proof['sharedAssemblies']


def verify_retained_runtime_inputs(root, pins):
    """Recheck immutable inputs after native execution; outputs do not replace admitted inputs."""
    binding = pins['hostPayload']
    require(file_sha256(root / binding['inputs']) == binding['inputsSha256'], 'Public capture inputs changed during runtime')
    proof = json.loads((root / binding['inputs']).read_text(encoding='utf-8'))
    require(public_host_contract(root / binding['path'], pins['hostImage'], proof['imageId'],pins['foundationRelease']) == proof,
            'Public Host payload changed during runtime')
    records = json.loads((root / 'runtime-package-inputs.json').read_text(encoding='utf-8'))
    retained = root / 'runtime-archive-inputs'
    require(isinstance(records, list) and records and all(isinstance(record, dict)
            and re.fullmatch(r'[^/\\:\x00-\x1f]+\.nupkg', str(record.get('archive', '')))
            and re.fullmatch(r'[0-9a-f]{64}', str(record.get('sha256', ''))) for record in records),
            'Retained runtime archive bindings are malformed')
    require({p.name for p in retained.glob('*.nupkg')} == {record['archive'] for record in records},
            'Retained runtime archive inventory changed')
    require(len({record['archive'].casefold() for record in records}) == len(records), 'Retained archive identities are ambiguous')
    shared_bindings, observed = [], set()
    for record in records:
        require(file_sha256(retained / record['archive']) == record['sha256'], 'Retained runtime archive bytes changed')
        if 'nativeProvenance' in record:
            require(record['nativeProvenance'] == record['archive'] + '.metadata.json', 'Retained provenance path is unsafe')
            require(file_sha256(retained / record['nativeProvenance']) == record['nativeProvenanceSha256'],
                    'Retained public restore provenance changed')
        with zipfile.ZipFile(retained / record['archive']) as archive:
            nuspecs = [name for name in archive.namelist() if name.endswith('.nuspec')]
            require(len(nuspecs) == 1, 'Retained runtime metadata is ambiguous')
            metadata = ET.fromstring(archive.read(nuspecs[0]))
            identity = metadata.find('./{*}metadata/{*}id').text
            version = metadata.find('./{*}metadata/{*}version').text
            require(record['id'].casefold() == (identity + '/' + version).casefold(), 'Retained package identity differs')
            canonical = next((name for name in HOST_SHARED if name.casefold() == identity.casefold()), None)
            if canonical:
                require(canonical not in observed and version == shared_contract_versions(root/binding['path'])[canonical], 'Retained shared versions differ')
                assembly = 'lib/net10.0/' + canonical + '.dll'
                require(archive.namelist().count(assembly) == 1, 'Retained shared archive has no unique net10 DLL')
                digest = hashlib.sha256()
                with archive.open(assembly) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(block)
                require(digest.hexdigest() == proof['hostRuntimeFiles'][canonical + '.dll'], 'Retained shared DLL differs from public Host')
                require(record.get('nativeSource') == CSHELLS_PREVIEW_SOURCE
                        and 'nativeProvenance' in record
                        and json.loads((retained / record['nativeProvenance']).read_text(encoding='utf-8')).get('source') == record['nativeSource'],
                        'Retained CShells public preview restore source differs')
                shared_bindings.append({**record, 'assemblyPath': assembly, 'assemblySha256': digest.hexdigest(), 'omittedRuntimeRoot': True})
                observed.add(canonical)
    require(observed == set(HOST_SHARED), 'Retained shared contract closure is incomplete')
    require(json.loads((root / 'runtime-shared-bindings.json').read_text(encoding='utf-8')) == shared_bindings,
            'Retained shared binding evidence differs from actual image/archive bytes')


def published_host_evidence(root, pins):
    """Portable complete input proof, rechecked by the wrapper and receipt sealer."""
    require(contracts_profile(pins), 'Published Host proof requires the reviewed contracts profile')
    verify_retained_runtime_inputs(root, pins)
    cleanup = json.loads((root / 'runtime-cleanup.json').read_text(encoding='utf-8'))
    process = json.loads((root / 'runtime-process-result.json').read_text(encoding='utf-8'))
    operations = json.loads((root / 'image-capture-operations.json').read_text(encoding='utf-8'))
    require(isinstance(operations, list) and len(operations) == 5
            and [operation.get('args', [None, None])[1] for operation in operations] == ['pull', 'create', 'inspect', 'cp', 'rm']
            and all(operation.get('exitCode') == 0 for operation in operations), 'Public image capture lifecycle did not complete')
    require(cleanup.get('container') == pins['runtimeContainer'] and cleanup.get('absent') is True,
            'Published Host runtime cleanup is unconfirmed')
    require(process.get('exitCode') == 0, 'Published Host native child did not complete')
    retained = [root / pins['hostPayload']['inputs'], root / 'runtime-inputs.json',
                root / 'runtime-package-inputs.json', root / 'runtime-shared-bindings.json',
                root / 'runtime-cleanup.json', root / 'runtime-process-result.json',
                root / 'image-capture-operations.json', root / 'runtime.log', root / 'runtime.stderr',
                root / 'Feature/obj/project.assets.json', root / 'Feature/packages.lock.json',
                root / 'artifacts/program-kit/building-block-restore.json']
    for directory in ('public-host-payload', 'runtime-archive-inputs', 'bundle'):
        retained.extend(path for path in (root / directory).rglob('*') if path.is_file())
    for pattern in ('image-capture-*.stdout', 'image-capture-*.stderr',
                    'runtime-cleanup-*.stdout', 'runtime-cleanup-*.stderr', 'command-*.stdout', 'command-*.stderr'):
        retained.extend(root.glob(pattern))
    require(all(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
                for path in retained), 'Published Host evidence is missing or unsafe')
    files = {path.relative_to(root).as_posix(): file_sha256(path) for path in sorted(set(retained))}
    return {'schemaVersion': 1, 'capture': json.loads((root / pins['hostPayload']['inputs']).read_text(encoding='utf-8')),
            'packages': json.loads((root / 'runtime-package-inputs.json').read_text(encoding='utf-8')),
            'sharedPackages': json.loads((root / 'runtime-shared-bindings.json').read_text(encoding='utf-8')),
            'cleanup': cleanup, 'process': process, 'retainedFiles': files}


def verify_published_host_evidence(root, result):
    require(published_host_evidence(root, result['inputs']) == result.get('publicHostEvidence'),
            'Published Host capture/provenance/native runtime evidence changed')


def main():
    sys.path.insert(0, str(Path.cwd()))  # Coordinator-copied, contract-bound helper.
    from bounded_process import run
    for key in list(os.environ):
        if any(part in key.upper() for part in ['TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL', 'CONNECTION_STRING']):
            os.environ.pop(key)
    root = Path.cwd()
    pins = json.loads(Path('runtime-inputs.json').read_text())
    shared_contracts = contracts_profile(pins)
    if shared_contracts:
        for key in pins.get('credentialEnvironmentNames', []):
            os.environ.pop(key, None)
        for key in list(os.environ):
            if key.upper().startswith(('CSHELLS__', 'FOUNDATION__', 'NUPLANE__')):
                os.environ.pop(key)
    dotnet = json.loads(Path('artifacts/program-kit/toolchain.json').read_text())['commands']['dotnet']
    suite = ET.Element('testsuite', name='Compatibility')
    counter = 0
    def command(args, expected=0):
        nonlocal counter
        counter += 1
        with open(f'command-{counter}.stdout', 'wb') as stdout, open(f'command-{counter}.stderr', 'wb') as stderr:
            code = run(args, root, stdout, stderr, 150)
        output = Path(f'command-{counter}.stdout').read_text(encoding='utf-8', errors='replace')
        error = Path(f'command-{counter}.stderr').read_text(encoding='utf-8', errors='replace')
        if code != expected:
            print(output[-10000:] + error[-10000:])
            raise RuntimeError(f'Compatibility command {counter} returned {code}; expected {expected}')
        return output.strip()
    def case(name, action):
        node = ET.SubElement(suite, 'testcase', classname=name.rsplit('.', 1)[0], name=name.rsplit('.', 1)[1])
        try:
            action()
        except Exception as error:
            ET.SubElement(node, 'failure', message=str(error))
            raise
        finally:
            ET.ElementTree(suite).write('compatibility-results.xml', encoding='utf-8', xml_declaration=True)
    bundle = root / 'bundle'
    packages = bundle / 'packages'
    packages.mkdir(parents=True)
    (packages / '.installed').mkdir()
    for project in ('Core/Core.csproj', 'Feature/Feature.csproj'):
        command([*dotnet, 'pack', project, '--no-restore', '-c', 'Release', '-o', str(packages), '-p:UseSharedCompilation=false'])
    command([*dotnet, 'build', 'Boundary/Boundary.csproj', '--no-restore', '-c', 'Release', '-p:UseSharedCompilation=false'])
    core = str(root / 'Core/bin/Release/net10.0/ProgramKit.Compatibility.Core.dll')
    auditor = [*dotnet, str(root / 'Boundary/bin/Release/net10.0/Boundary.dll'), core]
    def boundaries():
        command(auditor)
        command([*dotnet, 'build', 'Core/Core.csproj', '--no-restore', '-c', 'Release', '-p:InjectForbiddenReference=true', '-p:UseSharedCompilation=false'])
        assert 'FORBIDDEN_CORE_REFERENCE' in command(auditor, expected=42)
    case('Shell.compiled_boundary_positive_and_negative', boundaries)
    assets = json.loads(Path('Feature/obj/project.assets.json').read_text())
    shared_assemblies = [{'Name': n, 'PublicKeyToken': None, 'MajorVersion': 0}
                        for n in ['CShells.Abstractions', 'CShells.AspNetCore.Abstractions']]
    if shared_contracts:
        shared_assemblies = prepare_shared_runtime(root, pins, assets, packages)
    else:
        package_roots = [Path(p) for p in assets['packageFolders']]
        copied = []
        for identity, library in assets['libraries'].items():
            if library['type'] != 'package' or identity.lower().startswith(('cshells.', 'nuplane')):
                continue  # Historical published Host ownership, retained unchanged.
            package_id, version = identity.rsplit('/', 1)
            relative = Path(library['path']) / f'{package_id.lower()}.{version.lower()}.nupkg'
            source = next((p / relative for p in package_roots if (p / relative).is_file()), None)
            if source is None:
                raise RuntimeError('Locked package archive missing: ' + identity)
            shutil.copyfile(source, packages / source.name)
            copied.append({'id': identity, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        Path('runtime-package-inputs.json').write_text(json.dumps(copied, indent=2))
    nuplane = {'Nuplane': {'FeedResolution': {'PackageInstallRoot': '/tmp/compatibility-installed'},
        'Setup': {'AutomaticReconciliation': True, 'PollInterval': '00:00:01',
        'Feeds': [{'Name': 'local-packages', 'DirectoryPath': 'packages', 'IncludePatterns': ['*'], 'Directory': {'Watch': False}}]},
        'Loading': {'Enabled': True, 'DefaultLoadMode': 'HostIntegrated', 'LoadModeSelectionPolicy': 'ExplicitOnly',
                    'SharedAssemblies': shared_assemblies}}}
    (bundle / 'nuplane.settings.json').write_text(json.dumps(nuplane))
    (bundle / 'hostsettings.json').write_text(json.dumps(nuplane))
    shells = {}
    for name, adapter in [('a', 'Default'), ('b', 'Alternate')]:
        features = ['Compatibility.Api', 'Compatibility.' + adapter, 'Orbyss.Foundation.Json.AspNetCore',
                    'Orbyss.Foundation.WebDefaults', 'Orbyss.Foundation.Web.ProblemDetails', 'Orbyss.Foundation.Web.OpenApi']
        shells[name] = {'Features': dict.fromkeys(features, True), 'Configuration': {'WebRouting': {'Path': name}}}
    (bundle / 'shells.json').write_text(json.dumps({'CShells': {'Shells': shells}}))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.glob('*.json')}
    container = pins['runtimeContainer'] if shared_contracts else 'pk-compat-' + uuid.uuid4().hex
    if shared_contracts:
        require(re.fullmatch(r'pk-compat-[0-9a-f]{32}', container) is not None,
                'Runtime container must have an exact parent-owned identity')
    started = False
    url = ''
    def request(path, data=None):
        # This fixture owns a plain HTTP loopback listener. Do not construct the
        # urllib default HTTPS/proxy handlers for it: those can initialize an
        # unrelated machine TLS stack or route private probe traffic to a proxy.
        address = urlsplit(url)
        connection = HTTPConnection(address.hostname, address.port, timeout=5)
        try:
            connection.request('POST' if data is not None else 'GET', path, body=data,
                               headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, response.headers, response.read()
        finally:
            connection.close()
    def ready():
        nonlocal url
        port = command(['docker', 'port', container, '8080/tcp']).split(':')[-1]
        url = 'http://127.0.0.1:' + str(int(port))
        until = time.monotonic() + 75
        while time.monotonic() < until:
            try:
                if request('/a/probe')[0] == 200: return
            except (OSError, TimeoutError, ConnectionError): pass
            time.sleep(.25)
        print(command(['docker', 'logs', container])[-10000:])
        raise RuntimeError('Published host did not activate the fixture')
    try:
        args = ['docker', 'run', '-d', '--name', container, '--pull=never', '-p', '127.0.0.1::8080',
                '--tmpfs', '/app/packages/.installed:rw,mode=1777']
        if shared_contracts:
            args += ['--label', 'program-kit.owner=' + container]
        for name in ['shells.json', 'hostsettings.json', 'nuplane.settings.json', 'packages']:
            args += ['--mount', f'type=bind,source={bundle / name},target=/app/{name},readonly']
        started = True
        command(args + [pins['hostImage']])
        def activation():
            ready()
            assert command(['docker', 'inspect', container, '--format', '{{.Config.Image}}']) == pins['hostImage']
            if shared_contracts:
                image_id = json.loads((root / pins['hostPayload']['inputs']).read_text(encoding='utf-8'))['imageId']
                assert command(['docker', 'inspect', container, '--format', '{{.Image}}']) == image_id
            assert json.loads(request('/a/probe')[2]) == {'value': 'default'}
        case('PublishedHost.exact_image_activation', activation)
        def replacement():
            for shell, value in [('a', 'default'), ('b', 'alternate'), ('a', 'default')]:
                assert json.loads(request('/' + shell + '/probe')[2]) == {'value': value}
        case('Shell.actual_registration_and_replacement', replacement)
        def http():
            status, headers, data = request('/a/probe', b'{"name":"fixture"}')
            assert status == 200 and json.loads(data)['name'] == 'fixture'
            assert headers['X-Frame-Options'] == 'DENY' and headers['Cache-Control'] == 'no-store'
            assert request('/a/probe', b'{"name":"one","name":"two"}')[0] == 400
            assert request('/a/probe', b'{"name":"one","unknown":true}')[0] == 400
            status, _, document = request('/a/_orbyss-foundation/openapi/v1.json')
            assert status == 200
            parsed = json.loads(document)
            assert 'openapi' in parsed and any('/probe' in path for path in parsed['paths'])
        case('PublishedHost.http_profiles_headers_openapi', http)
        def restart():
            command(['docker', 'restart', container]); ready(); replacement()
            assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.glob('*.json')}
        case('PublishedHost.bundle_restart', restart)
    finally:
        if started: command(['docker', 'rm', '-f', '-v', container])
    if shared_contracts:
        verify_retained_runtime_inputs(root, pins)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

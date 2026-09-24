"""Synthetic activation on the published host; no consumer host project/image is built.

APIs verified against Foundation v0.2.2 (8d60cdd55e7fb9056c83d614786667c04ef78bdf):
Host/Program.cs, FoundationOpenApiFeature and WebDefaults' PolicyProbeFeature.
Build/pack only the synthetic port/features. Runtime dependencies come from the
coordinator's locked restore. No package resolution or restore happens here.
"""
import hashlib
import json
import os
import shutil
import time
import uuid
import sys
from pathlib import Path
from http.client import HTTPConnection
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path.cwd()))  # Coordinator-copied, contract-bound helper.
from bounded_process import run


def main():
    for key in list(os.environ):
        if any(part in key.upper() for part in ['TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL', 'CONNECTION_STRING']):
            os.environ.pop(key)
    root = Path.cwd()
    pins = json.loads(Path('runtime-inputs.json').read_text())
    dotnet = json.loads(Path('.program-kit/evidence/toolchain.json').read_text())['commands']['dotnet']
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
    package_roots = [Path(p) for p in assets['packageFolders']]
    copied = []
    for identity, library in assets['libraries'].items():
        if library['type'] != 'package' or identity.lower().startswith(('cshells.', 'nuplane')):
            continue  # These assemblies are owned by the published host.
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
                    'SharedAssemblies': [{'Name': n, 'PublicKeyToken': None, 'MajorVersion': 0} for n in ['CShells.Abstractions', 'CShells.AspNetCore.Abstractions']]}}}
    (bundle / 'nuplane.settings.json').write_text(json.dumps(nuplane))
    (bundle / 'hostsettings.json').write_text(json.dumps(nuplane))
    shells = {}
    for name, adapter in [('a', 'Default'), ('b', 'Alternate')]:
        features = ['Compatibility.Api', 'Compatibility.' + adapter, 'Orbyss.Foundation.Json.AspNetCore',
                    'Orbyss.Foundation.WebDefaults', 'Orbyss.Foundation.Web.ProblemDetails', 'Orbyss.Foundation.Web.OpenApi']
        shells[name] = {'Features': dict.fromkeys(features, True), 'Configuration': {'WebRouting': {'Path': name}}}
    (bundle / 'shells.json').write_text(json.dumps({'CShells': {'Shells': shells}}))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.glob('*.json')}
    container = 'pk-compat-' + uuid.uuid4().hex
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
        for name in ['shells.json', 'hostsettings.json', 'nuplane.settings.json', 'packages']:
            args += ['--mount', f'type=bind,source={bundle / name},target=/app/{name},readonly']
        started = True
        command(args + [pins['hostImage']])
        def activation():
            ready()
            assert command(['docker', 'inspect', container, '--format', '{{.Config.Image}}']) == pins['hostImage']
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
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

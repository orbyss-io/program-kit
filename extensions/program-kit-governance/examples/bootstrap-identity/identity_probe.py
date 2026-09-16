"""Published Foundation BFF + pinned Keycloak; no consumer feature or host build.

Uses the shipped neutral realm/BFF configuration and Foundation v0.2.0 public
IWebShellFeature/permission-policy API. Shared compatibility setup owns restore.
Only scratch settings, local test personas and disposable containers are used.
"""
import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import shutil
import socket
import sys
import time
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path.cwd()))
from bounded_process import run


def main():
    root = Path.cwd()
    inputs = json.loads((root / 'runtime-inputs.json').read_text())
    tools = json.loads((root / '.program-kit/evidence/toolchain.json').read_text())['commands']
    suite = ET.Element('testsuite', name='ProgramKitIdentityCompatibility')
    counter = 0

    def command(args, timeout=20):
        nonlocal counter
        counter += 1
        with open(f'command-{counter}.stdout', 'wb') as stdout, open(f'command-{counter}.stderr', 'wb') as stderr:
            code = run(args, root, stdout, stderr, timeout)
        if code:
            # The compatibility coordinator preserves/redacts this bounded stream
            # before deleting scratch. A scratch-only log is not a usable handoff.
            for suffix in ['stdout', 'stderr']:
                print(Path(f'command-{counter}.{suffix}').read_text(encoding='utf-8', errors='replace')[-4096:], file=sys.stderr)
            raise RuntimeError(f'Identity compatibility command {counter} exited {code}; see preserved compatibility stderr')
        return Path(f'command-{counter}.stdout').read_text(encoding='utf-8').strip()

    def case(name, action):
        node = ET.SubElement(suite, 'testcase', classname='Identity', name=name)
        try:
            action()
        except Exception as error:
            ET.SubElement(node, 'failure', message=str(error))
            raise
        finally:
            ET.ElementTree(suite).write('compatibility-results.xml', encoding='utf-8', xml_declaration=True)

    def wait_http(number, path):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            connection = HTTPConnection('127.0.0.1', number, timeout=3)
            try:
                connection.request('GET', path)
                response = connection.getresponse()
                if response.status == 200:
                    response.read()
                    return
            except (OSError, TimeoutError):
                pass
            finally:
                connection.close()
            time.sleep(.25)
        raise RuntimeError('Timed out waiting for bounded local compatibility endpoint')

    # Hold both reservations together so sequential ephemeral allocations cannot
    # select the same port. Docker publishes only these loopback listeners.
    with socket.socket() as identity_listener, socket.socket() as app_listener:
        identity_listener.bind(('127.0.0.1', 0))
        app_listener.bind(('127.0.0.1', 0))
        identity_port = identity_listener.getsockname()[1]
        app_port = app_listener.getsockname()[1]
    base = f'http://localhost:{app_port}'
    realm = json.loads(Path('realm-source.json').read_text())
    client = json.loads(Path('client-source.json').read_text())
    client.pop('postLogoutRedirectUris')
    client['redirectUris'] = [base + '/signin-oidc']
    client['webOrigins'] = [base]
    client['attributes']['post.logout.redirect.uris'] = base + '/signout-callback-oidc'
    realm['clients'].append(client)
    Path('realm.json').write_text(json.dumps(realm))
    Path('browser-inputs.json').write_text(json.dumps({'baseURL': base}))
    bundle = root / 'bundle'
    packages = bundle / 'packages'
    packages.mkdir(parents=True)
    # Docker cannot create a nested tmpfs mountpoint inside a read-only feed.
    (packages / '.installed').mkdir()
    command([*tools['dotnet'], 'pack', 'Probe.csproj', '--no-restore', '-c', 'Release', '-o', str(packages), '-p:UseSharedCompilation=false'], 90)
    assets = json.loads(Path('obj/project.assets.json').read_text())
    package_roots = [Path(p) for p in assets['packageFolders']]
    copied = []
    for name, library in assets['libraries'].items():
        if library['type'] != 'package' or name.lower().startswith(('cshells.', 'nuplane')):
            continue
        package_id, version = name.rsplit('/', 1)
        relative = Path(library['path']) / f'{package_id.lower()}.{version.lower()}.nupkg'
        source = next((p / relative for p in package_roots if (p / relative).is_file()), None)
        if source is None:
            raise RuntimeError('Locked package archive is unavailable: ' + name)
        shutil.copyfile(source, packages / source.name)
        copied.append({'id': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    Path('runtime-package-inputs.json').write_text(json.dumps(copied, indent=2))
    nuplane = {'Nuplane': {'Setup': {'AutomaticReconciliation': True, 'PollInterval': '00:00:01',
        'Feeds': [{'Name': 'local-packages', 'DirectoryPath': 'packages', 'IncludePatterns': ['*'], 'Directory': {'Watch': False}}]},
        'Loading': {'Enabled': True, 'DefaultLoadMode': 'HostIntegrated', 'LoadModeSelectionPolicy': 'ExplicitOnly',
                    'SharedAssemblies': [{'Name': n, 'PublicKeyToken': None, 'MajorVersion': 0} for n in ['CShells.Abstractions', 'CShells.AspNetCore.Abstractions']]}}}
    for name in ['hostsettings.json', 'nuplane.settings.json']:
        (bundle / name).write_text(json.dumps(nuplane))
    shells = json.loads(Path('shell-source.json').read_text())
    shell = shells['CShells']['Shells']['default']
    shell['Features'].update({'Compatibility.Identity': {}, 'Orbyss.Foundation.Authentication.Assurance': {}})
    # Publisher v0.2.0 requires a nonempty, effective named assurance policy.
    # This proves configuration/activation only, not a consumer assurance design.
    shell['Configuration']['Foundation']['Authentication'] = {'Assurance': {
        'Policies': {'compatibility-fresh': {'MaximumAuthenticationAgeSeconds': 300}}}}
    web = shell['Configuration']['Foundation']['Web']
    web.update(Authority=f'http://localhost:{identity_port}/realms/program-kit',
               BackchannelAuthority='http://identity:8080/realms/program-kit',
               ClientSecret=client['secret'], RolePermissions={'user': ['compatibility.read']})
    (bundle / 'shells.json').write_text(json.dumps(shells))
    suffix = uuid.uuid4().hex
    network, identity, host = ['pk-proof-' + n + '-' + suffix for n in ['net', 'idp', 'host']]
    created = []
    try:
        command(['docker', 'network', 'create', network]); created.append(('network', network))
        command(['docker', 'create', '--name', identity, '--pull=never', '--network', network, '--network-alias', 'identity',
                 '-p', f'127.0.0.1:{identity_port}:8080', '-e', f'KC_HOSTNAME=http://localhost:{identity_port}',
                 '-e', 'KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true',
                 '--mount', f'type=bind,source={root / "realm.json"},target=/opt/keycloak/data/import/realm.json,readonly',
                 '--mount', f'type=bind,source={root / "themes"},target=/opt/keycloak/themes,readonly',
                 inputs['identityImage'], 'start-dev', '--import-realm']); created.append(('container', identity))
        command(['docker', 'start', identity])
        case('pinned_provider_discovery', lambda: wait_http(identity_port, '/realms/program-kit/.well-known/openid-configuration'))
        args = ['docker', 'create', '--name', host, '--pull=never', '--network', network,
                '-e', 'ASPNETCORE_ENVIRONMENT=Development',
                '-p', f'127.0.0.1:{app_port}:8080', '--tmpfs', '/app/packages/.installed:rw,mode=1777']
        for name in ['shells.json', 'hostsettings.json', 'nuplane.settings.json', 'packages']:
            args += ['--mount', f'type=bind,source={bundle / name},target=/app/{name},readonly']
        command([*args, inputs['hostImage']]); created.append(('container', host))
        command(['docker', 'start', host])
        case('published_bff_activation', lambda: wait_http(app_port, '/bff/user'))
        def browser():
            output = command([*tools['node'], 'browser.mjs'], 90)
            if 'PROGRAM_KIT_BFF_PROVIDER_OK' not in output:
                raise RuntimeError('Real browser assertions did not complete')
        case('code_flow_permission_negatives_and_logout', browser)
    except Exception:
        for kind, name in created:
            if kind == 'container':
                try:
                    print(command(['docker', 'logs', '--tail', '60', name])[-8192:], file=sys.stderr)
                except Exception:
                    pass  # Preserve the original failure; cleanup still runs.
        raise
    finally:
        errors = []
        for kind, name in reversed(created):
            try:
                command(['docker', 'rm', '-f', '-v', name] if kind == 'container' else ['docker', 'network', 'rm', name])
            except Exception as error:
                errors.append(str(error))
        if errors:
            raise RuntimeError('Compatibility cleanup failed: ' + '; '.join(errors))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

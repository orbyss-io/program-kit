"""One native composition operation for preparation, run, incremental update and stop.

The typed input and managed reconciliation own configuration. Docker Compose owns
local container lifetimes. Preparation alone acquires dependencies and provisions
owned databases; ordinary run/update preserves them and performs no acquisition.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import time
from urllib.parse import urlsplit
import uuid

import composition_model as model
import composition_render as render
import foundation_qualification as qualification
import runtime_closure
import shell_composition
from program_kit_version import PROGRAM_KIT_VERSION

STATE = 'artifacts/composition/prepared.json'
LIFECYCLE = 'artifacts/composition/lifecycle.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    runtime_closure.atomic_write(Path(path), value)


def require(condition, message):
    if not condition:
        raise ValueError('PKC100 ' + message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def service(name):
    return 'r-' + hashlib.sha256(name.encode()).hexdigest()[:16]


def variable(name):
    return 'PKC_' + hashlib.sha256(name.encode()).hexdigest()[:20].upper()


def project(root, graph):
    return 'program-kit-' + hashlib.sha256((str(root.resolve()).casefold() + '\n' + graph['compositionId']).encode()).hexdigest()[:16]


def selected(root, check_frontends=True):
    graph, contract = render.verify_outputs(root, check_frontends=check_frontends)
    return graph, contract, read(root / render.RESOLVED)


class Commands(qualification.Commands):
    def run(self, command, **arguments):
        # Resolution applies to every nested command, not just the outer wrapper.
        if command and command[0].lower() in ('python', 'python3', 'python.exe', 'python3.exe'):
            from js_toolchain import device
            command = [str(device.require_python(self.root)), *command[1:]]
        return super().run(command, **arguments)

    def output(self, command, **arguments):
        before = set(self.directory.glob('process-*'))
        self.run(command, **arguments)
        created = set(self.directory.glob('process-*')) - before
        require(len(created) == 1, 'ambiguous native process evidence')
        path = created.pop() / 'stdout.log'
        require(path.stat().st_size <= 1_000_000, 'native control output exceeds its bounded size')
        return path.read_text(encoding='utf-8')


def prerequisite(root, command):
    command.run([sys.executable, 'eng/toolchain.py', '--repository', '.'], timeout=120)
    command.run([sys.executable, 'eng/preflight.py', '--require-linux-compose'], timeout=30)


def browser_engines():
    engines = os.environ.get('PROGRAMKIT_BROWSER_ENGINES', 'chromium,webkit').split(',')
    require(engines and len(set(engines)) == len(engines) and
            set(engines) <= {'chromium', 'webkit', 'firefox'}, 'invalid browser engine selection')
    return engines


def browser_check(root, graph, resolved, command, directory, launch_only=False, selected_hosts=None):
    hosts = []
    env = model.environment(graph)
    if not launch_only:
        for name, host in resolved['hosts'].items():
            if selected_hosts and name not in selected_hosts:
                continue
            shell_id = host['shells'][0]
            client = graph['resources'][render.auth_binding(graph, shell_id)['clientRef']]
            authority = env[client['authorityRef']]
            require(authority['mode'] == 'managed', 'external authority requires its qualified authentication readiness adapter')
            pages = [row['path'] for row in model.bindings(graph, 'frontend') if row['shellRef'] == shell_id]
            hosts.append({'id': name, 'origin': host['publicOrigin'], 'page': pages[0] if pages else None,
                          'realm': str(root / ('deploy/keycloak/' + client['authorityRef'] + '/' + authority['realm'] + '-realm.json'))})
    plan = directory / ('browser-launch.json' if launch_only else 'browser-plan.json')
    result = directory / ('browser-launch-result.json' if launch_only else 'browser-result.json')
    write(plan, {'engines': browser_engines(), 'hosts': hosts, 'launchOnly': launch_only})
    command.run(['node', 'eng/web/composition-readiness.mjs', str(plan), str(result)], timeout=180)
    require(read(result)['status'] == 'ready', 'authentication readiness did not pass')
    return read(result)


def prepare_browsers(root, graph, resolved, command, directory):
    npm, environment = qualification.npm_command(root, ['ci', '--ignore-scripts'])
    command.run(npm, cwd=root / 'eng/web', timeout=600, environment=environment)
    install = ['install']
    if os.name != 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true':
        install.append('--with-deps')
    command.run(qualification.playwright_command(root, [*install, *browser_engines()]), timeout=600)
    browser_check(root, graph, resolved, command, directory, launch_only=True)


def private_credentials(root, graph, create=False):
    """Owned local credentials are private inputs; evidence contains no values."""
    path = root / 'artifacts/composition/private/credentials.json'
    private = read(path) if path.is_file() else {}
    env = model.environment(graph)
    values = {}
    for name, row in model.resources(graph, 'database').items():
        ref = env[name]['credentialRef']
        server_id = next(item['serverRef'] for item in model.bindings(graph, 'databaseServer') if item['databaseRef'] == name)
        supplied = os.environ.get(ref)
        if supplied:
            values[ref] = supplied
        elif env[server_id]['mode'] == 'managed':
            if create and ref not in private:
                private[ref] = secrets.token_urlsafe(32)
            require(ref in private, 'owned database credentials are not prepared')
            values[ref] = private[ref]
        else:
            require(False, 'external database credential is required through ' + ref)
    for name in model.resources(graph, 'databaseServer'):
        if env[name]['mode'] == 'managed':
            ref = variable('server-admin:' + name)
            if create and ref not in private:
                private[ref] = secrets.token_urlsafe(32)
            require(ref in private, 'owned server credentials are not prepared')
            values[ref] = private[ref]
    for name in model.resources(graph, 'identityAuthority'):
        if env[name]['mode'] == 'managed':
            ref = variable('identity-admin:' + name)
            if create and ref not in private:
                private[ref] = secrets.token_urlsafe(32)
            require(ref in private, 'owned identity administration credentials are not prepared')
            values[ref] = private[ref]
    for auth in model.bindings(graph, 'authentication'):
        client = graph['resources'][auth['clientRef']]
        if client['profile'] != 'browser-bff':
            continue
        assigned = env[auth['clientRef']]
        authority_id = client['authorityRef']
        ref = assigned['credentialRef']
        require(ref, 'confidential client needs a credential reference')
        if env[authority_id]['mode'] == 'managed':
            realm = read(root / ('deploy/keycloak/' + authority_id + '/' + env[authority_id]['realm'] + '-realm.json'))
            registration = next(row for row in realm['clients'] if row['clientId'] == assigned['clientId'])
            require(not os.environ.get(ref) or os.environ[ref] == registration['secret'],
                    'managed local client secret differs from its generated import; reconcile the binding before run')
            values[ref] = registration['secret']
        else:
            require(os.environ.get(ref), 'external client credential is required through ' + ref)
            values[ref] = os.environ[ref]
    if create:
        write(path, private)
    return values


def connection(database, binding, server_id, server_binding, password):
    host = service(server_id) if server_binding['mode'] == 'managed' else server_binding['host']
    port = 5432 if server_binding['mode'] == 'managed' else server_binding['port']
    username = binding.get('username', database['name'])
    def quote(value):
        return '"' + str(value).replace('"', '""') + '"'
    return 'Host=' + quote(host) + ';Port=' + str(port) + ';Database=' + quote(database['name']) + \
        ';Username=' + quote(username) + ';Password=' + quote(password)


def compose_model(root, graph, contract, resolved, credentials):
    env = model.environment(graph)
    document = {'name': project(root, graph), 'services': {}, 'networks': {'foundation': {}}, 'volumes': {}}
    process_environment = {}
    for name in model.resources(graph, 'databaseServer'):
        if env[name]['mode'] != 'managed':
            continue
        admin = variable('server-admin:' + name)
        process_environment[admin] = credentials[admin]
        document['volumes'][service(name)] = {}
        document['services'][service(name)] = {
            'image': contract['serviceImages']['postgresql'], 'pull_policy': 'never',
            'environment': {'POSTGRES_USER': '_programkit', 'POSTGRES_PASSWORD': '${' + admin + ':?Prepare owned database credentials}',
                            'POSTGRES_DB': 'postgres'}, 'networks': ['foundation'],
            'volumes': [{'type': 'volume', 'source': service(name), 'target': '/var/lib/postgresql'}],
            'healthcheck': {'test': ['CMD-SHELL', 'pg_isready -U _programkit -d postgres'],
                            'interval': '2s', 'timeout': '3s', 'retries': 30}}
    for name in model.resources(graph, 'identityAuthority'):
        binding = env[name]
        if binding['mode'] != 'managed':
            continue
        uri = model.origin(binding['publicOrigin'], name)
        aliases = sorted({urlsplit(binding.get(key, binding['backchannelOrigin'])).hostname
                          for key in ('backchannelOrigin', 'administrationOrigin')})
        document['volumes'][service(name)] = {}
        document['services'][service(name)] = {
            'image': contract['serviceImages']['keycloak'], 'pull_policy': 'never',
            'command': ['start-dev', '--import-realm', '--health-enabled=true'],
            'environment': {'KC_HOSTNAME': binding['publicOrigin'], 'KC_HOSTNAME_BACKCHANNEL_DYNAMIC': 'true',
                            'KC_BOOTSTRAP_ADMIN_USERNAME': '_programkit',
                            'KC_BOOTSTRAP_ADMIN_PASSWORD': '${' + variable('identity-admin:' + name) + ':?Prepare owned identity credentials}'},
            'ports': [{'target': 8080, 'published': str(uri.port), 'host_ip': '127.0.0.1', 'protocol': 'tcp'}],
            'networks': {'foundation': {'aliases': aliases}},
            'volumes': [
                {'type': 'bind', 'source': str(root / ('deploy/keycloak/' + name + '/' + binding['realm'] + '-realm.json')),
                 'target': '/opt/keycloak/data/import/' + binding['realm'] + '-realm.json', 'read_only': True,
                 'bind': {'create_host_path': False}},
                {'type': 'bind', 'source': str(root / ('deploy/keycloak/' + name + '/themes')),
                 'target': '/opt/keycloak/themes', 'read_only': True, 'bind': {'create_host_path': False}},
                {'type': 'volume', 'source': service(name), 'target': '/opt/keycloak/data'}],
            'healthcheck': {'test': ['CMD-SHELL', "exec 3<>/dev/tcp/127.0.0.1/9000 && printf 'GET /health/ready HTTP/1.1\\r\\nHost: localhost\\r\\nConnection: close\\r\\n\\r\\n' >&3 && grep -q UP <&3"],
                            'interval': '2s', 'timeout': '3s', 'retries': 60, 'start_period': '10s'}}
        process_environment[variable('identity-admin:' + name)] = credentials[variable('identity-admin:' + name)]
    for name, host in resolved['hosts'].items():
        stage = root / host['runtimeStage']
        image = resolved['hostImage']
        values = {'ASPNETCORE_ENVIRONMENT': 'Development'}
        dependencies = {}
        for shell_id in host['shells']:
            shell = graph['resources'][shell_id]
            auth = render.auth_binding(graph, shell_id)
            client = graph['resources'][auth['clientRef']]
            if env[client['authorityRef']]['mode'] == 'managed':
                dependencies[service(client['authorityRef'])] = {'condition': 'service_healthy'}
            prefix = 'CShells__Shells__' + shell['name'] + '__Configuration__Foundation__'
            if client['profile'] == 'browser-bff':
                key = variable('client:' + auth['clientRef'])
                process_environment[key] = credentials[env[auth['clientRef']]['credentialRef']]
                values[prefix + 'Web__ClientSecret'] = '${' + key + ':?Prepare the client binding}'
            for row in model.bindings(graph, 'databaseProvider'):
                if row['shellRef'] != shell_id:
                    continue
                database = graph['resources'][row['databaseRef']]
                database_env = env[row['databaseRef']]
                server_id = next(item['serverRef'] for item in model.bindings(graph, 'databaseServer') if item['databaseRef'] == row['databaseRef'])
                if env[server_id]['mode'] == 'managed':
                    dependencies[service(server_id)] = {'condition': 'service_healthy'}
                key = variable('connection:' + row['databaseRef'])
                process_environment[key] = connection(database, database_env, server_id, env[server_id], credentials[database_env['credentialRef']])
                values[prefix + 'PostgreSql__Policies__' + row['policy'] + '__ConnectionString'] = '${' + key + ':?Prepare the database binding}'
        volumes = [{'type': 'bind', 'source': str(stage / file), 'target': '/app/' + file, 'read_only': True,
                    'bind': {'create_host_path': False}} for file in ('hostsettings.json', 'shells.json', 'nuplane.settings.json', 'packages')]
        if (stage / 'shells.json').is_file():
            import hosted_bundle
            staged_shells = shell_composition.load(stage / 'shells.json', True)
            # The stage already contains only admitted bytes. Directory mounts
            # preserve real file-provider/stat behavior on Docker Desktop/Windows.
            hosted_bundle.inventory(stage, staged_shells)
            public_roots = {shell['Configuration']['Foundation']['HostedPages']['Root']
                            for shell in staged_shells['CShells']['Shells'].values()
                            if 'HostedPages' in shell.get('Configuration', {}).get('Foundation', {})}
            volumes += [{'type': 'bind', 'source': str(stage / public_root), 'target': '/app/' + public_root,
                         'read_only': True, 'bind': {'create_host_path': False}}
                        for public_root in sorted(public_roots)]
        uri = model.origin(host['publicOrigin'], name)
        require(uri.scheme == 'http', 'HTTPS execution requires a qualified prepared certificate adapter')
        document['services'][service(name)] = {
            'image': image['reference'] if isinstance(image, dict) else image, 'pull_policy': 'never',
            'environment': values, 'volumes': volumes, 'tmpfs': ['/app/packages/.installed:rw,mode=1777'],
            'depends_on': dependencies, 'networks': ['foundation'],
            'ports': [{'target': 8080, 'published': str(uri.port), 'host_ip': '127.0.0.1' if uri.hostname == 'localhost' else uri.hostname, 'protocol': 'tcp'}]}
    return document, process_environment


def topology_fingerprint(root, graph, contract):
    # Product source is deliberately outside prerequisite invalidation.
    selected = {name: runtime_closure.sha256(root / name) for name in
                (model.INPUT, render.CONTRACT, 'global.json', '.nvmrc', '.npm-version') if (root / name).is_file()}
    selected.update(contract.get('managedOutputs', {}))
    selected['runAdapter'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return model.digest(selected)


def compose_arguments(root, receipt):
    path = root / receipt['compose']
    require(path.resolve().is_relative_to(root), 'composition output escaped repository')
    require(path.is_file() and runtime_closure.sha256(path) == receipt['composeSha256'], 'generated Compose output changed; prepare again')
    return ['docker', 'compose', '-p', receipt['project'], '-f', str(path)]


def latest(root, require_prepared=True):
    path = root / STATE
    require(path.is_file(), 'prepare the selected composition before run')
    value = read(path)
    require(not require_prepared or value.get('status') == 'prepared', 'latest preparation is incomplete or failed')
    return value


def provision_databases(root, graph, command, compose, environment):
    env = model.environment(graph)
    servers = [service(name) for name in model.resources(graph, 'databaseServer') if env[name]['mode'] == 'managed']
    running = set(command.output([*compose, 'ps', '--services', '--status', 'running'], environment=environment).split()) if servers else set()
    if servers:
        command.run([*compose, 'up', '-d', '--pull', 'never', '--wait', '--wait-timeout', '90', *servers], environment=environment, timeout=120)
    for name, database in model.resources(graph, 'database').items():
        server_id = next(row['serverRef'] for row in model.bindings(graph, 'databaseServer') if row['databaseRef'] == name)
        if env[server_id]['mode'] != 'managed':
            continue
        username = env[name].get('username', database['name'])
        require(re.fullmatch(r'[a-z][a-z0-9_]{0,62}', username), 'managed database role must be a literal PostgreSQL identity')
        require(database['name'] not in ('postgres', 'template0', 'template1') and username != '_programkit', 'reserved provider infrastructure identity')
        credentials = private_credentials(root, graph)
        password = credentials[env[name]['credentialRef']]
        quoted = password.replace("'", "''")
        # psql owns execution; no user command text or identifier is evaluated.
        role_sql = f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{username}') THEN CREATE ROLE \"{username}\" LOGIN; END IF; END $$; ALTER ROLE \"{username}\" PASSWORD '{quoted}';"
        command.secrets = (*command.secrets, password)
        command.run([*compose, 'exec', '-T', service(server_id), 'psql', '-U', '_programkit', '-d', 'postgres',
                     '-v', 'ON_ERROR_STOP=1', '-c', role_sql], environment=environment)
        # Conditional CREATE DATABASE cannot run inside a transaction/DO block.
        create_sql = f"SELECT 'CREATE DATABASE \"{database['name']}\" OWNER \"{username}\"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{database['name']}')\\gexec\n"
        script = root / 'artifacts/composition/private' / (service(name) + '.sql')
        script.write_text(create_sql, encoding='utf-8')
        command.run([*compose, 'cp', str(script), service(server_id) + ':/tmp/program-kit-create-database.sql'], environment=environment)
        command.run([*compose, 'exec', '-T', service(server_id), 'psql', '-U', '_programkit', '-d', 'postgres',
                     '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/program-kit-create-database.sql'], environment=environment)
    newly_started = [name for name in servers if name not in running]
    if newly_started:
        # Fresh preparation leaves the foundation stopped; ordinary run measures actual startup.
        command.run([*compose, 'stop', *newly_started], environment=environment)


def build(root, graph, resolved, command, selected_hosts=None, restore=False):
    if restore:
        command.run(['pwsh', '-NoProfile', '-File', 'eng/Restore.ps1', '-Subject', qualification.solution(root)], timeout=900)
    # Frontends are build inputs. Their maintained producer seals admission before pack.
    import prepare_hosted_pages
    prepare_hosted_pages.build(root, graph, command, restore=restore, selected_hosts=selected_hosts)
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    packages = root / 'artifacts/packages' / version / uuid.uuid4().hex
    packages.mkdir(parents=True)
    command.run([sys.executable, 'eng/repository_architecture.py', '--repository', '.', '--manifest', 'eng/architecture.json',
                 '--configuration', 'Release', '--build-subject', qualification.solution(root), '--version', version,
                 '--output', str(command.directory / 'architecture.xml')], timeout=600)
    # Native architecture tooling can establish its own locked restore inputs.
    # Bind the pack only after that step, then rebuild under the sealed snapshot.
    runtime_closure.prepare_pack(root, packages)
    command.run(['dotnet', 'build', qualification.solution(root), '-c', 'Release', '--no-restore', '-p:Version=' + version], timeout=600)
    # Native MSBuild performs incremental compilation; selected-root staging avoids aggregate packages.
    command.run(['dotnet', 'pack', qualification.solution(root), '-c', 'Release', '--no-build', '-p:Version=' + version, '-o', str(packages)], timeout=600)
    runtime_closure.seal_pack(root, packages)
    import release_bundle
    for name, host in resolved['hosts'].items():
        if selected_hosts and name not in selected_hosts:
            continue
        release_bundle.stage(root, packages, root / host['runtimeStage'], evidence=root / 'artifacts/composition/closures' / (name + '.json'),
                             inventory=packages / 'program-kit-pack.json', root_packages=host['rootPackages'], shell_names=host['shellNames'])
        # Empty mountpoint only: immutable archives and writable installation bytes
        # occupy separate mounts, exactly as in the retained qualified fixture.
        (root / host['runtimeStage'] / 'packages/.installed').mkdir(exist_ok=True)


def provision_identities(root, graph, command, compose, environment, credentials):
    import keycloak_composition
    env = model.environment(graph)
    owned = [name for name in model.resources(graph, 'identityAuthority') if env[name]['mode'] == 'managed']
    if not owned:
        return {}
    running = set(command.output([*compose, 'ps', '--services', '--status', 'running'], environment=environment).split())
    state_path = root / 'artifacts/composition/private/identity-state.json'
    previous = read(state_path) if state_path.is_file() else {}
    state = dict(previous)
    try:
        command.run([*compose, 'up', '-d', '--pull', 'never', '--wait', '--wait-timeout', '150',
                     *[service(name) for name in owned]], environment=environment, timeout=210)
        for name in owned:
            realm_path = root / ('deploy/keycloak/' + name + '/' + env[name]['realm'] + '-realm.json')
            state[name] = keycloak_composition.reconcile(graph, name, read(realm_path),
                credentials[variable('identity-admin:' + name)], previous.get(name))
            state[name]['realmSha256'] = runtime_closure.sha256(realm_path)
            write(state_path, state)
        return {name: {'status': state[name]['status'], 'userCountPreserved': True,
                       'registrationCount': len(state[name]['clients'])} for name in owned}
    finally:
        started = [service(name) for name in owned if service(name) not in running]
        if started:
            command.run([*compose, 'stop', *started], environment=environment)


def prepare(root):
    graph, contract, resolved = selected(root, check_frontends=False)
    directory = root / 'artifacts/composition/runs' / ('prepare-' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    started = time.monotonic()
    write(root / STATE, {'status': 'preparing', 'run': directory.relative_to(root).as_posix()})
    command = Commands(root, directory)
    timings = {}
    try:
        before = time.monotonic(); prerequisite(root, command); timings['prerequisitesSeconds'] = round(time.monotonic() - before, 3)
        before = time.monotonic(); prepare_browsers(root, graph, resolved, command, directory)
        timings['browserPreparationSeconds'] = round(time.monotonic() - before, 3)
        before = time.monotonic()
        image = resolved['hostImage']
        env = model.environment(graph)
        images = [image['reference'] if isinstance(image, dict) else image]
        if any(env[name]['mode'] == 'managed' for name in model.resources(graph, 'databaseServer')):
            images.append(resolved['serviceImages']['postgresql'])
        if any(env[name]['mode'] == 'managed' for name in model.resources(graph, 'identityAuthority')):
            images.append(resolved['serviceImages']['keycloak'])
        for image in sorted(set(images)):
            require(re.fullmatch(r'[a-z0-9][a-z0-9._/:+-]*@sha256:[a-f0-9]{64}', image), 'selected image is not immutable')
            command.run(['docker', 'pull', image], timeout=600)
        timings['imagePreparationSeconds'] = round(time.monotonic() - before, 3)
        before = time.monotonic(); build(root, graph, resolved, command, restore=True); timings['restoreBuildStageSeconds'] = round(time.monotonic() - before, 3)
        credentials = private_credentials(root, graph, create=True)
        document, process_env = compose_model(root, graph, contract, resolved, credentials)
        command.secrets = tuple({*credentials.values(), *process_env.values()})
        compose_file = root / 'artifacts/composition/compose.json'
        write(compose_file, document)
        compose = ['docker', 'compose', '-p', document['name'], '-f', str(compose_file)]
        command.run([*compose, 'config', '--quiet'], environment=process_env)
        write(root / LIFECYCLE, {'compositionId': graph['compositionId'], 'project': document['name'],
                                'services': list(document['services']), 'hosts': list(resolved['hosts'])})
        prior_running = set(command.output([*compose, 'ps', '--services', '--status', 'running'], environment=process_env).split())
        before = time.monotonic(); provision_databases(root, graph, command, compose, process_env)
        timings['ownedDatabaseProvisioningSeconds'] = round(time.monotonic() - before, 3)
        before = time.monotonic()
        identities = provision_identities(root, graph, command, compose, process_env, credentials)
        timings['ownedIdentityProvisioningSeconds'] = round(time.monotonic() - before, 3)
        receipt = {'schemaVersion': 2, 'status': 'prepared', 'startedAtUtc': utc(), 'project': document['name'],
                   'compose': compose_file.relative_to(root).as_posix(), 'composeSha256': runtime_closure.sha256(compose_file),
                   'topologyFingerprint': topology_fingerprint(root, graph, contract), 'modelDigest': model.digest(graph),
                   'elapsedSeconds': round(time.monotonic() - started, 3), 'timings': timings,
                   'identityReconciliation': identities, 'pendingActivationHosts': list(resolved['hosts']),
                   'scope': 'Prepared consumer on observed device; no clean OS or product acceptance claim'}
        write(directory / 'result.json', receipt); write(root / STATE, receipt)
        print(json.dumps({'status': 'prepared', 'elapsedSeconds': receipt['elapsedSeconds'], 'timings': timings}))
    except BaseException:
        if 'prior_running' in locals():
            try:
                newly_started = set(command.output([*compose, 'ps', '--services', '--status', 'running'], environment=process_env).split()) - prior_running
                if newly_started:
                    command.run([*compose, 'stop', *sorted(newly_started)], environment=process_env)
            except (ValueError, OSError):
                pass  # Keep the original failed observation and owned cleanup logs.
        result = {'schemaVersion': 2, 'status': 'failed', 'startedAtUtc': utc(), 'elapsedSeconds': round(time.monotonic() - started, 3)}
        if 'document' in locals() and 'compose_file' in locals() and compose_file.is_file():
            result.update(project=document['name'], compose=compose_file.relative_to(root).as_posix(),
                          composeSha256=runtime_closure.sha256(compose_file))
        write(directory / 'result.json', result); write(root / STATE, result)
        raise


def affected_hosts(root, graph, resolved, requested=None):
    """Include native reverse dependencies of every changed owned source input."""
    current = runtime_closure.source_inputs(root)
    affected = set(requested or [])
    for name, host in resolved['hosts'].items():
        evidence = root / 'artifacts/composition/closures' / (name + '.json')
        require(evidence.is_file(), 'host lacks its prepared source closure: ' + name)
        captured = read(evidence).get('sourceInputs')
        if captured != runtime_closure.source_scope(root, root / host['runtimeStage'], current):
            affected.add(name)
    return sorted(affected)


def run(root, selected_hosts=None, update=False):
    import foundation_fixture
    receipt = latest(root)
    graph, contract, resolved = selected(root, check_frontends=not update)
    require(receipt['topologyFingerprint'] == topology_fingerprint(root, graph, contract), 'composition/dependency inputs changed; reconcile and prepare their affected resources')
    if selected_hosts:
        require(set(selected_hosts) <= set(resolved['hosts']), 'unknown selected host')
    if update:
        selected_hosts = affected_hosts(root, graph, resolved, selected_hosts)
        if not selected_hosts:
            print(json.dumps({'status': 'unchanged', 'updatedHosts': [], 'productAcceptance': False}))
            return
    directory = root / 'artifacts/composition/runs' / (('update-' if update else 'run-') + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    command = Commands(root, directory)
    started = time.monotonic()
    result = {'schemaVersion': 2, 'status': 'running', 'startedAtUtc': utc(), 'productAcceptance': False}
    write(directory / 'result.json', result)
    try:
        if update:
            build(root, graph, resolved, command, selected_hosts=selected_hosts)
        for name, host in resolved['hosts'].items():
            if not selected_hosts or name in selected_hosts:
                runtime_closure.validate(root, root / host['runtimeStage'], root / 'artifacts/composition/closures' / (name + '.json'), PROGRAM_KIT_VERSION)
        credentials = private_credentials(root, graph)
        document, process_env = compose_model(root, graph, contract, resolved, credentials)
        command.secrets = tuple({*credentials.values(), *process_env.values()})
        if update:
            path = root / receipt['compose']; write(path, document)
            receipt['composeSha256'] = runtime_closure.sha256(path); write(root / STATE, receipt)
        compose = compose_arguments(root, receipt)
        hosts = selected_hosts or list(resolved['hosts'])
        arguments = [*compose, 'up', '-d', '--pull', 'never', '--wait', '--wait-timeout', '150']
        pending_activation = set(receipt.get('pendingActivationHosts', [])) & set(hosts)
        if not update and pending_activation:
            infrastructure = [name for name in document['services'] if name not in {service(host) for host in resolved['hosts']}]
            if infrastructure:
                command.run([*arguments, *infrastructure], environment=process_env, timeout=210)
            arguments += ['--force-recreate', '--no-deps']
        if update:
            arguments += ['--force-recreate', '--no-deps']
        if selected_hosts or update or pending_activation:
            arguments += [service(name) for name in hosts]
        command.run(arguments, environment=process_env, timeout=210)
        receipt['pendingActivationHosts'] = [name for name in receipt.get('pendingActivationHosts', []) if name not in hosts]
        write(root / STATE, receipt)
        checks = {}
        for name in hosts:
            origin = resolved['hosts'][name]['publicOrigin']
            foundation_fixture.poll(lambda: qualification.ready(origin, '/bff/user'), timeout=60)
            checks[name] = {'hostActivation': True, 'selectedProviderPrepare': 'required by selected feature activation', 'bffAnonymousStatus': 200}
        browser = browser_check(root, graph, resolved, command, directory, selected_hosts=hosts)
        result.update(status='ready', elapsedSeconds=round(time.monotonic() - started, 3), checks=checks,
                      updatedHosts=hosts if update else [],
                      authentication=browser['checks'], scope='Native configured foundation readiness; consumer journey acceptance remains separate')
        write(directory / 'result.json', result)
        print(json.dumps(result))
    except BaseException:
        if 'compose' in locals() and 'process_env' in locals():
            try:
                command.run([*compose, 'logs', '--no-color', '--tail', '100'], environment=process_env)
            except (ValueError, OSError):
                pass  # Preserve the original failure and any captured diagnostic.
        result.update(status='failed', elapsedSeconds=round(time.monotonic() - started, 3)); write(directory / 'result.json', result)
        raise


def status(root):
    path = root / STATE
    preparation = read(path) if path.is_file() else {'status': 'unprepared'}
    return {'schemaVersion': 2, 'preparation': preparation, 'runs': [
        {'path': file.relative_to(root).as_posix(), **read(file)}
        for file in sorted((root / 'artifacts/composition/runs').glob('*/result.json'))]}


def stop(root, hosts=None):
    """Stop owned processes even when new source/configuration cannot be admitted."""
    record = read(root / LIFECYCLE)
    require(record['project'] == project(root, {'compositionId': record['compositionId']}), 'lifecycle record belongs to a different consumer')
    require(not hosts or set(hosts) <= set(record['hosts']), 'unknown lifecycle host selection')
    command = Commands(root, root / 'artifacts/composition/runs' / ('stop-' + uuid.uuid4().hex))
    output = command.output(['docker', 'ps', '-a', '--no-trunc', '--filter',
                             'label=com.docker.compose.project=' + record['project'],
                             '--format', '{{.ID}} {{.Label "com.docker.compose.service"}}'])
    selected_services = {service(name) for name in hosts} if hosts else set(record['services'])
    identifiers = []
    for line in output.splitlines():
        identity, name = line.split()
        require(re.fullmatch(r'[a-f0-9]{64}', identity) and name in record['services'], 'owned lifecycle inventory is invalid')
        if name in selected_services:
            identifiers.append(identity)
    if identifiers:
        command.run(['docker', 'stop', *identifiers], timeout=120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('action', choices=('prepare', 'run', 'update', 'stop', 'status'))
    parser.add_argument('--host', action='append')
    args = parser.parse_args(); root = args.repository.resolve()
    try:
        if args.action == 'prepare':
            prepare(root)
        elif args.action in ('run', 'update'):
            run(root, args.host, args.action == 'update')
        elif args.action == 'status':
            print(json.dumps(status(root), indent=2))
        else:
            stop(root, args.host)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())

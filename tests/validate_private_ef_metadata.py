"""Fresh native EF feature packing/staging/migrations and digest-pinned public Host activation.

Uses only maintained synthetic examples and an owned disposable PostgreSQL container.
The optional local Foundation.Build archive is an explicit candidate, never publication
evidence. No identity login, browser acceptance or consumer application execution is claimed.
"""
from __future__ import annotations

import argparse
import hashlib
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import uuid
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
ENG = TEMPLATE / 'files/eng'
EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/postgresql-lifecycle'
sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(ENG),
               str(ROOT / 'extensions/program-kit-governance/scripts'),
               str(ROOT / 'extensions/program-kit-governance/examples/bootstrap-runtime')]
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_composition
import foundation_fixture
import persistence_selection
import runtime_fixture
import runtime_probe
from central_packages import central_package_versions


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def archive_identity(path):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith('.nuspec')]
        require(len(names) == 1, 'Candidate archive must contain one nuspec')
        root = ET.fromstring(archive.read(names[0]))
        values = {node.tag.rsplit('}', 1)[-1]: node.text for node in root.iter()}
        return values['id'], values['version']


def normalize_generated_migration(value):
    """Ignore generator layout while preserving every quoted native argument."""
    return re.sub(r'"(?:[^"\\]|\\.)*"|\s+',
                  lambda match: match.group() if match.group().startswith('"') else '', value)


def validate_generated_migration(value, expected):
    require(normalize_generated_migration(value) == normalize_generated_migration(expected),
            'Native generated migration changed; review exact schema/types/nullability/identity/PK/index/Down before adapting it')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-version', help='Exact Foundation.Build version; default is the maintained pin')
    parser.add_argument('--build-package', type=Path, help='Explicit local Foundation.Build candidate nupkg')
    parser.add_argument('--expect-tooling-conflict', action='store_true',
                        help='Require successful native packing followed by the original EF Design PKR014 staging failure; no runtime qualification')
    args = parser.parse_args()
    identity = uuid.uuid4().hex
    evidence = ROOT / 'artifacts/private-ef-metadata' / identity
    consumer = ROOT / 'artifacts/t' / ('ef-meta-' + identity[:10])
    evidence.mkdir(parents=True)
    consumer.mkdir(parents=True)
    build_version = args.build_version
    selection = foundation_composition.publisher_contracts(ROOT, selected_packages=[
        *foundation_composition.BASE_PACKAGES, 'Orbyss.Foundation.PostgreSql'])
    packages = selection['packages']
    require(packages['Orbyss.Foundation.PostgreSql'] == '0.3.7', 'This reproduction requires selected Foundation 0.3.7')
    persistence_pins = persistence_selection.packages({'profile': 'ef-postgresql'}, TEMPLATE / 'files')
    ef_version = persistence_pins['Microsoft.EntityFrameworkCore.Design']
    require(ef_version == '10.0.13', 'This reproduction requires the qualified EF Design 10.0.13')
    runtime_probe.validate_public_image(selection['hostImage'])
    secrets = [uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex]
    deployment_password, runtime_password, client_secret = secrets
    result = {'status': 'running', 'consumer': str(consumer), 'selectedHostImage': selection['hostImage'],
              'selectedFoundation': packages, 'selectedEfDesign': ef_version, 'selectedBuild': build_version,
              'cases': [], 'steps': [], 'hostCleanupObserved': False,
              'scope': __doc__, 'publicationEstablished': False,
              'expectedToolingConflict': args.expect_tooling_conflict, 'hostActivationEstablished': False}
    environment = runtime_fixture.runtime_environment()
    environment.update(NUGET_PACKAGES=str(consumer / 'artifacts/nuget'),
                       NUGET_HTTP_CACHE_PATH=str(consumer / 'artifacts/http'),
                       DOTNET_CLI_HOME=str(ROOT / 'artifacts/cache/private-ef-metadata/dotnet'),
                       MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0', PYTHONUTF8='1')
    sequence = 0

    def run(label, command, *, env=None, timeout=180, success=True):
        nonlocal sequence
        sequence += 1
        directory = evidence / (f'{sequence:03d}-' + label)
        observed = foundation_fixture.captured([str(value) for value in command], consumer, directory,
            timeout=timeout, environment=env or environment, secret_values=secrets)
        result['steps'].append({'id': label, 'evidence': str(directory.relative_to(evidence)), **observed})
        require(observed.get('cleanupComplete') and observed.get('logsDrained'), 'Process cleanup or stream drain incomplete: ' + label)
        require((observed.get('exitCode') == 0) == success, 'Unexpected command outcome: ' + str(directory))
        return (directory / 'stdout.log').read_text(encoding='utf-8').strip()

    host = 'pk-private-ef-' + identity
    network = 'pk-private-ef-net-' + identity
    host_requested = False
    network_requested = False
    postgres = None
    source_files = [Path(__file__), ROOT / 'tests/fixtures/private-ef-metadata/PrivateEfFeature.cs',
                    *[EXAMPLE / name for name in ('NativeMigrationContext.cs', 'NativeMigrationDesignFactory.cs',
                        'NativeMigrationEntry.cs', 'NativeMigrationEntryConfiguration.cs', 'NativeMigrationAdmission.cs')]]
    source_basis = [*source_files,
                    *[path for path in TEMPLATE.rglob('*') if path.is_file()
                      and not {'__pycache__', 'node_modules', 'artifacts'}.intersection(path.relative_to(TEMPLATE).parts)],
                    *[path for path in (ROOT / 'extensions/program-kit-dotnet/scripts').rglob('*.py')],
                    *[path for path in (ROOT / 'extensions/program-kit-building-blocks/scripts').rglob('*.py')],
                    ROOT / 'tests/fixtures/private-ef-metadata/ReviewedInitial.cs',
                    ROOT / 'tests/fixtures/private-ef-metadata/ReviewedEntryColumns.cs',
                    ROOT / 'tests/fixtures/private-ef-metadata/NativeInitial.expected.cs.txt',
                    ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py',
                    Path(runtime_fixture.__file__), Path(runtime_probe.__file__), Path(foundation_composition.__file__),
                    Path(persistence_selection.__file__), TEMPLATE / 'files/global.json',
                    TEMPLATE / 'files/eng/ProgramKit.Packages.props',
                    TEMPLATE / 'web-profiles/bff-cookie/eng/web-profile.shells.json']

    def source_hashes():
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_basis}

    source_before = source_hashes()
    try:
        run('scaffold', [sys.executable, ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py',
            '--target', consumer, '--profile-selected', '--foundation-host-accepted',
            '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--persistence-profile', 'ef-postgresql'])
        pins = central_package_versions(consumer)
        build_version = args.build_version or pins['orbyss.foundation.build']
        result['selectedBuild'] = build_version
        require((consumer / 'eng/release_bundle.py').read_bytes() == (ENG / 'release_bundle.py').read_bytes(),
                'Emitted release bundle helper differs from maintained source')
        result['installedReleaseBundleSha256'] = hashlib.sha256((consumer / 'eng/release_bundle.py').read_bytes()).hexdigest()
        (consumer / 'VERSION').write_text('1.0.0\n', encoding='utf-8')
        # Candidate changes belong only to this explicitly isolated fixture.
        engineering_pins = ET.parse(consumer / 'eng/ProgramKit.Packages.props')
        build_pins = [row for row in engineering_pins.iter('PackageVersion')
                      if row.get('Include') == 'Orbyss.Foundation.Build']
        require(len(build_pins) == 1, 'Selected engineering builder pin is absent or ambiguous')
        build_pins[0].set('Version', build_version)
        engineering_pins.write(consumer / 'eng/ProgramKit.Packages.props', encoding='utf-8', xml_declaration=True)
        central = ET.parse(consumer / 'Directory.Packages.props')
        group = ET.SubElement(central.getroot(), 'ItemGroup')
        for package, version in packages.items():
            ET.SubElement(group, 'PackageVersion', Include=package, Version=version)
        # A synthetic native mechanism test selects its exact profile inputs;
        # ordinary consumer persistence admission is not fabricated by this harness.
        for package, version in persistence_pins.items():
            ET.SubElement(group, 'PackageVersion', Include=package, Version=version)
        ET.SubElement(group, 'PackageVersion', Include='Newtonsoft.Json', Version='13.0.3')
        central.write(consumer / 'Directory.Packages.props', encoding='utf-8', xml_declaration=True)
        if args.build_package:
            candidate = args.build_package.resolve()
            require(archive_identity(candidate) == ('Orbyss.Foundation.Build', build_version), 'Candidate identity differs from explicit exact Build selection')
            feed = consumer / 'candidate-feed'
            feed.mkdir()
            shutil.copyfile(candidate, feed / candidate.name)
            config = ET.parse(consumer / 'NuGet.config')
            ET.SubElement(config.getroot().find('packageSources'), 'add', key='explicit-build-candidate', value=str(feed))
            source = ET.SubElement(config.getroot().find('packageSourceMapping'), 'packageSource', key='explicit-build-candidate')
            ET.SubElement(source, 'package', pattern='Orbyss.Foundation.Build')
            config.write(consumer / 'NuGet.config', encoding='utf-8', xml_declaration=True)
            result['candidateSha256'] = hashlib.sha256(candidate.read_bytes()).hexdigest()
        feature = consumer / 'src/ProgramKit.PrivateEfMetadata'
        feature.mkdir(parents=True)
        for source in source_files[2:]:
            shutil.copyfile(source, feature / source.name)
        shutil.copyfile(source_files[1], feature / 'PrivateEfFeature.cs')
        project = feature / 'ProgramKit.PrivateEfMetadata.csproj'
        project.write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<IsPackable>true</IsPackable><PackageId>ProgramKit.PrivateEfMetadata</PackageId>
<AssemblyName>ProgramKit.PrivateEfMetadata</AssemblyName><Version>1.0.0</Version>
<FoundationFeatureIdentity>ProgramKit.PrivateEfMetadata</FoundationFeatureIdentity>
</PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" />
<PackageReference Include="CShells.Abstractions" PrivateAssets="all" />
<PackageReference Include="CShells.AspNetCore.Abstractions" PrivateAssets="all" />
<PackageReference Include="Orbyss.Foundation.PostgreSql" />
<PackageReference Include="Microsoft.EntityFrameworkCore" />
<PackageReference Include="Microsoft.EntityFrameworkCore.Design" PrivateAssets="all"
 IncludeAssets="runtime;build;native;contentfiles;analyzers;buildtransitive" />
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />
<PackageReference Include="Newtonsoft.Json" PrivateAssets="all" />
</ItemGroup></Project>''', encoding='utf-8')
        run('restore', ['dotnet', 'restore', project, '--configfile', 'NuGet.config', '--disable-build-servers'], timeout=300)
        run('locked-restore', ['dotnet', 'restore', project, '--locked-mode', '--configfile', 'NuGet.config', '--disable-build-servers'])
        tool = consumer / '.config/dotnet-tools.json'
        write(tool, {'version': 1, 'isRoot': True, 'tools': {'dotnet-ef': {'version': ef_version, 'commands': ['dotnet-ef']}}})
        run('ef-tool-restore', ['dotnet', 'tool', 'restore', '--configfile', 'NuGet.config'])
        build = ['dotnet', 'build', project, '-c', 'Release', '--no-restore', '--disable-build-servers', '-m:1']
        run('native-build', build)
        ef = ['dotnet', 'tool', 'run', 'dotnet-ef', '--']
        ef_args = ['--project', str(project), '--context', 'NativeMigrationContext', '--configuration', 'Release', '--no-build']
        if not args.expect_tooling_conflict:
            run('ef-author-migration', [*ef, 'migrations', 'add', 'Initial', *ef_args])
            require(len(list((feature / 'Migrations').glob('*ModelSnapshot.cs'))) == 1, 'Native EF snapshot missing')
            migrations = list((feature / 'Migrations').glob('*_Initial.cs'))
            require(len(migrations) == 1, 'Expected one native Initial migration for the synthetic model')
            original_bytes = migrations[0].read_bytes()
            original = original_bytes.decode('utf-8-sig')
            expected = (ROOT / 'tests/fixtures/private-ef-metadata/NativeInitial.expected.cs.txt').read_text()
            validate_generated_migration(original, expected)
            shutil.copytree(feature / 'Migrations', evidence / 'native-generated-migrations')
            # The raw EF migration is retained above. Its generated inline delegates
            # conflict with the mandatory source-readability contract. This fixture
            # supplies a reviewed equivalent using the same native EF operations;
            # identity, generated designer and model snapshot remain untouched.
            shutil.copyfile(ROOT / 'tests/fixtures/private-ef-metadata/ReviewedInitial.cs', migrations[0])
            retained = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in (feature / 'Migrations').glob('*.cs') if path != migrations[0]}
            shutil.copyfile(ROOT / 'tests/fixtures/private-ef-metadata/ReviewedEntryColumns.cs',
                            feature / 'ReviewedEntryColumns.cs')
            result['migrationReviewAdaptation'] = {
                'meaning': 'Synthetic reviewed readable equivalent of native EF Up/Down; raw output retained; no analyzer suppression or human acceptance claim',
                'rawMigrationSha256': hashlib.sha256(original_bytes).hexdigest(),
                'reviewedMigrationSha256': hashlib.sha256(migrations[0].read_bytes()).hexdigest(),
                'retainedIdentityDesignerSnapshot': retained}
            run('migration-build', build)
            require(retained == {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (feature / 'Migrations').glob('*.cs') if path != migrations[0]},
                    'Native migration identity/designer/snapshot changed during review adaptation')
            run('ef-no-model-drift', [*ef, 'migrations', 'has-pending-model-changes', *ef_args])
            run('ef-reviewable-script', [*ef, 'migrations', 'script', '--idempotent', '--output', evidence / 'migration.sql', *ef_args])
            migration_sql = (evidence / 'migration.sql').read_text(encoding='utf-8-sig')
            require(all(text in migration_sql for text in ('__EFMigrationsHistory', 'ef_entries',
                    'IX_ef_entries_Value', 'GENERATED BY DEFAULT AS IDENTITY')),
                    'Native EF script lost required model operations')
            result['cases'].append('native-ef-tooling-reviewed-migration-snapshot-and-model-drift')
        profile = consumer / 'eng/web-profile.shells.json'
        document = json.loads(profile.read_text())
        shell = document['CShells']['Shells']['default']
        # Preserve the actual shipped BFF activations; do not invent missing ones.
        require('Orbyss.Foundation.Json.AspNetCore' in shell['Features'], 'Shipped BFF baseline lacks required Json activation')
        shell['Configuration']['Foundation']['Web']['Authority'] = 'http://localhost:1/realms/synthetic'
        write(profile, document)
        write(consumer / 'shells.json', {'CShells': {'Shells': {'default': {'Features': {'ProgramKit.PrivateEfMetadata': {}}}}}})
        nuplane = json.loads((consumer / 'nuplane.settings.json').read_text())
        nuplane['Nuplane']['FeedResolution'] = {'PackageInstallRoot': '/tmp/private-ef-installed'}
        nuplane['Nuplane']['Loading']['SharedAssemblies'] = [
            {'Name': name, 'PublicKeyToken': None, 'MajorVersion': 0}
            for name in ('CShells.Abstractions', 'CShells.AspNetCore.Abstractions')]
        write(consumer / 'nuplane.settings.json', nuplane)
        output = consumer / 'artifacts/packages/1.0.0'
        release = [sys.executable, consumer / 'eng/release_bundle.py']
        run('prepare-pack', [*release, 'prepare-pack', '--repository', consumer, '--packages', output])
        run('fresh-pack', ['dotnet', 'pack', project, '-c', 'Release', '--no-restore', '--output', output,
                          '--disable-build-servers', '-m:1'])
        run('seal-pack', [*release, 'seal-pack', '--repository', consumer, '--packages', output])
        archive = output / 'ProgramKit.PrivateEfMetadata.1.0.0.nupkg'
        with zipfile.ZipFile(archive) as native:
            descriptor = json.loads(native.read('orbyss-foundation/feature.json'))
        write(evidence / 'packed-feature.json', descriptor)
        required = {item['packageId']: item['minimumVersion'] for item in descriptor['hostProvidedDependencies']}
        if args.expect_tooling_conflict:
            require(required.get('Microsoft.EntityFrameworkCore.Design') == ef_version,
                    'Original bad descriptor was not reproduced after successful native build/pack')
        else:
            for package in ('Microsoft.EntityFrameworkCore.Design', 'Microsoft.CodeAnalysis.CSharp.Workspaces', 'Mono.TextTemplating'):
                require(package not in required, 'Tool-only package leaked into native descriptor: ' + package)
        require(required.get('Newtonsoft.Json') == '13.0.3', 'Shared tooling/private runtime Newtonsoft dependency lost or changed')
        require(required.get('CShells.Abstractions') == pins['cshells.abstractions'], 'Genuine private host contract lost or changed')
        assets = json.loads((feature / 'obj/project.assets.json').read_text())
        require('Microsoft.EntityFrameworkCore.Design/' + ef_version in assets['libraries'], 'Native EF tooling reference was removed')
        result['cases'].append('native-packed-descriptor-preserves-private-shared-runtime')
        if not args.expect_tooling_conflict:
            result['cases'].append('native-packed-descriptor-excludes-tooling')
        stage = consumer / 'artifacts/runtime'
        run('native-stage', [*release, 'stage', '--repository', consumer, '--packages', output,
                            '--output', stage, '--inventory', output / 'program-kit-pack.json'],
                            timeout=300, success=not args.expect_tooling_conflict)
        if args.expect_tooling_conflict:
            logs = evidence / result['steps'][-1]['evidence']
            diagnostic = (logs / 'stdout.log').read_text() + (logs / 'stderr.log').read_text()
            require('PKR014' in diagnostic and 'Microsoft.EntityFrameworkCore.Design' in diagnostic
                    and 'missing' in diagnostic, 'Stage failed without the original EF Design missing-package conflict')
            result['cases'].append('original-pkr014-ef-design-missing-after-successful-native-pack')
            require(source_before == source_hashes(), 'Validator/source inputs changed during the original failure reproduction')
            result.update(status='passed', sourceSha256=source_before,
                          packageSha256=hashlib.sha256(archive.read_bytes()).hexdigest())
            return 0
        staged = {archive_identity(path): path for path in (stage / 'packages').glob('*.nupkg')}
        require(('Newtonsoft.Json', '13.0.3') in staged, 'Private runtime dependency absent from native stage')
        require(not any(package.casefold() == 'microsoft.entityframeworkcore.design' for package, _ in staged), 'Tooling-only package was staged')
        result['cases'].append('ordinary-integrity-validating-stage-with-unchanged-ef-tooling')
        # Docker requires this child mountpoint to exist before overlaying tmpfs
        # beneath the read-only package feed. No package bytes are changed.
        (stage / 'packages/.installed').mkdir()
        policy = json.loads((ROOT / 'extensions/program-kit-dotnet/references/persistence-runtimes.json').read_text())
        run('postgresql-image-pull', ['docker', 'pull', policy['profiles']['ef-postgresql']['image']], timeout=300)
        postgres = foundation_fixture.PostgreSqlFixture(policy['profiles']['ef-postgresql']['image'], evidence / 'postgresql')
        secrets.append(postgres.password)
        with postgres:
            def sql(label, query):
                # Only this fixture's exact owned container can receive SQL.
                postgres.inspect()
                return run(label, ['docker', 'exec', postgres.name, 'psql', '-h', '127.0.0.1', '-X', '-A', '-t',
                                  '-v', 'ON_ERROR_STOP=1', '-U', 'fixture', '-d', 'foundation_fixture', '-c', query])
            sql('provision-identities', f'''CREATE ROLE pk_deploy LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '{deployment_password}';
CREATE ROLE pk_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '{runtime_password}';
GRANT CONNECT,CREATE ON DATABASE foundation_fixture TO pk_deploy;
GRANT CONNECT ON DATABASE foundation_fixture TO pk_runtime;''')
            base = f'Host=127.0.0.1;Port={postgres.port};Database=foundation_fixture;'
            deployment = dict(environment, PK_FIXTURE_EF_DEPLOYMENT=base + 'Username=pk_deploy;Password=' + deployment_password)
            run('ef-deploy', [*ef, 'database', 'update', *ef_args], env=deployment)
            run('ef-deploy-repeat', [*ef, 'database', 'update', *ef_args], env=deployment)
            require(sql('migration-history', 'SELECT count(*) FROM ef_example."__EFMigrationsHistory"') == '1', 'Native migration history was not stable')
            require(sql('native-schema', "SELECT column_name,data_type,is_nullable,is_identity FROM information_schema.columns WHERE table_schema='ef_example' AND table_name='ef_entries' ORDER BY ordinal_position") ==
                    'Id|bigint|NO|YES\nValue|text|NO|NO', 'Native migration did not establish the independently expected schema')
            sql('runtime-grants', '''REVOKE ALL ON SCHEMA ef_example FROM PUBLIC;
GRANT USAGE ON SCHEMA ef_example TO pk_runtime;
GRANT SELECT ON ef_example."__EFMigrationsHistory" TO pk_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON ef_example.ef_entries TO pk_runtime;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA ef_example TO pk_runtime;''')
            result['cases'].append('native-ef-deployment-separate-from-runtime-identity')
            # Capture and verify the selected public payload; never build a substitute Host.
            payload = runtime_fixture.capture_public_host(evidence, selection['hostImage'], release='0.3.7')
            result['publicHostCapture'] = payload
            postgres.inspect()
            network_requested = True
            run('owned-network-create', ['docker', 'network', 'create', '--label', 'program-kit.owner=' + network, network])
            run('owned-network-connect', ['docker', 'network', 'connect', network, postgres.name])
            runtime_connection = (f'Host={postgres.name};Port=5432;Database=foundation_fixture;'
                                  f'Username=pk_runtime;Password={runtime_password};Search Path=ef_example')
            connection_key = 'CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__fixture__ConnectionString'
            secret_key = 'CShells__Shells__default__Configuration__Foundation__Web__ClientSecret'
            host_environment = dict(environment, **{connection_key: runtime_connection, secret_key: client_secret})
            args_host = ['docker', 'run', '--detach', '--name', host, '--pull=never',
                         '--label', 'program-kit.owner=' + host, '--publish', '127.0.0.1::8080',
                         '--network', network, '--env', 'ASPNETCORE_ENVIRONMENT=Development',
                         '--env', connection_key, '--env', secret_key, '--tmpfs', '/app/packages/.installed:rw,mode=1777']
            for name in ('shells.json', 'hostsettings.json', 'nuplane.settings.json', 'packages'):
                args_host += ['--mount', f'type=bind,source={stage / name},target=/app/{name},readonly']
            host_requested = True
            run('published-host-start', [*args_host, selection['hostImage']], env=host_environment)
            require(run('published-host-image', ['docker', 'inspect', host, '--format', '{{.Config.Image}}']) == selection['hostImage'], 'Host selected image changed')
            port = int(run('published-host-port', ['docker', 'port', host, '8080/tcp']).rsplit(':', 1)[1])
            cookies = SimpleCookie()

            def request(path, method='GET', headers=None):
                connection = HTTPConnection('127.0.0.1', port, timeout=5)
                try:
                    selected_headers = dict(headers or {})
                    if cookies:
                        selected_headers['Cookie'] = '; '.join(row.OutputString(attrs=[]) for row in cookies.values())
                    connection.request(method, path, body=b'' if method == 'POST' else None, headers=selected_headers)
                    response = connection.getresponse()
                    for key, value in response.getheaders():
                        if key.lower() == 'set-cookie':
                            cookies.load(value)
                    return response.status, response.read().decode('utf-8')
                finally:
                    connection.close()

            def ready():
                try:
                    code, text = request('/api/private-ef')
                    return code == 200 and json.loads(text) == {'count': 0, 'privateRuntime': 'Newtonsoft.Json'}
                except (OSError, ValueError):
                    return False
            foundation_fixture.poll(ready, timeout=75, interval=.25)
            code, body = request('/bff/antiforgery')
            require(code == 200, 'BFF antiforgery endpoint did not activate')
            antiforgery = json.loads(body)
            require(antiforgery.get('headerName') == 'X-CSRF-TOKEN' and antiforgery.get('requestToken'),
                    'BFF did not issue its native antiforgery contract')
            # Tokens and cookies remain in memory and never enter retained evidence.
            code, body = request('/api/private-ef', 'POST', {antiforgery['headerName']: antiforgery['requestToken']})
            result['databaseWriteHttpStatus'] = code
            require((code, body) == (200, 'written'), 'Published Host database write failed with status ' + str(code))
            code, body = request('/api/private-ef')
            require(code == 200 and json.loads(body)['count'] == 1, 'Published Host database observation failed')
            require(sql('independent-host-effect', "SELECT count(*) FROM ef_example.ef_entries WHERE \"Value\"='published-host-entry'") == '1', 'Independent database write observation failed')
            code, body = request('/bff/user')
            require(code == 200 and json.loads(body)['authenticated'] is False, 'Anonymous BFF endpoint was not activated')
            result['cases'].append('published-host-ef-runtime-write-read-and-anonymous-bff-endpoint')
            result['hostActivationEstablished'] = True
            result['httpObservation'] = {'databaseCount': 1, 'bffAnonymous': True, 'privateRuntime': 'Newtonsoft.Json'}
        require(source_before == source_hashes(), 'Validator/source inputs changed during execution')
        result.update(status='passed', sourceSha256=source_before,
                      packageSha256=hashlib.sha256(archive.read_bytes()).hexdigest())
        return 0
    except BaseException as error:
        diagnostic = str(error)
        for secret in secrets:
            diagnostic = diagnostic.replace(secret, '[REDACTED]')
        result.update(status='failed', diagnostic=diagnostic)
        raise
    finally:
        try:
            if host_requested:
                run('published-host-logs', ['docker', 'logs', host])
                owner = run('published-host-owner', ['docker', 'inspect', host, '--format', '{{index .Config.Labels "program-kit.owner"}}'])
                require(owner == host, 'Refused cleanup of foreign Host container')
                run('published-host-cleanup', ['docker', 'rm', '--force', '--volumes', host])
                remaining = run('published-host-absence', ['docker', 'ps', '--all', '--quiet', '--filter', 'name=^/' + host + '$'])
                result['hostCleanupObserved'] = not remaining
                require(not remaining, 'Owned Host cleanup was not observed')
            if network_requested:
                owner = run('owned-network-owner', ['docker', 'network', 'inspect', network,
                            '--format', '{{index .Labels "program-kit.owner"}}'])
                require(owner == network, 'Refused cleanup of foreign Docker network')
                run('owned-network-cleanup', ['docker', 'network', 'rm', network])
                result['networkCleanupObserved'] = True
        except BaseException as error:
            result.update(status='failed', cleanupDiagnostic=str(error))
            raise
        finally:
            if postgres is not None:
                result['postgresqlCleanup'] = postgres.cleanup
            write(evidence / 'results.json', result)
            print('Private EF metadata evidence: ' + str(evidence / 'results.json'))


if __name__ == '__main__':
    raise SystemExit(main())

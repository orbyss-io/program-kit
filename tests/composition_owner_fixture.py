"""Focused synthetic native owner operation, through the existing composition runner.

The old Build 0.3.2 profile uses a separate nonpackable native EF startup project.
This does not qualify Design as a private dependency in an old packed provider.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid
from xml.etree import ElementTree as ET

PROFILE = 'foundation-0.3.7-build-0.3.2-exporter-0.2.7-forms-0.2.1-localization-0.1.2-q-f51d9f63'
SECRET_ENV = 'PROGRAMKIT_OWNER_HMAC'


def require(value, message):
    if not value:
        raise ValueError(message)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def project_reference(path, reference):
    document = ET.fromstring(path.read_bytes())
    group = ET.SubElement(document, 'ItemGroup')
    ET.SubElement(group, 'ProjectReference', Include=reference)
    path.write_bytes(ET.tostring(document) + b'\n')


def materialize(root, fixture):
    """Author fictional product code in already generated native owners."""
    core = root / 'src/Application.Core'; core.mkdir()
    (core / 'Application.Core.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><PackageId>Application.Core</PackageId><IsPackable>true</IsPackable></PropertyGroup>
</Project>\n''', encoding='utf-8')
    for owner, destination in [('Core', core), ('Api', root / 'src/Application.Api'),
                               ('Provider', root / 'src/Application.PostgreSql')]:
        if owner == 'Provider':
            for source in destination.glob('*.cs'):
                source.unlink()
        for source in (fixture / owner).glob('*.cs'):
            shutil.copyfile(source, destination / source.name)
    for name in ('Api', 'PostgreSql'):
        path = root / f'src/Application.{name}/Application.{name}.csproj'
        project_reference(path, '../Application.Core/Application.Core.csproj')
        document = ET.fromstring(path.read_bytes())
        for parent in document.iter():
            for child in list(parent):
                if child.tag == 'PackageReference' and child.get('Include') == 'Microsoft.EntityFrameworkCore.Design':
                    parent.remove(child)
        if name == 'Api' and not any(item.get('Include') == 'Orbyss.Foundation.Authentication' for item in document.iter('PackageReference')):
            group = ET.SubElement(document, 'ItemGroup')
            ET.SubElement(group, 'PackageReference', Include='Orbyss.Foundation.Authentication')
        path.write_bytes(ET.tostring(document) + b'\n')
    solution = root / 'application.slnx'
    if not solution.exists():
        solutions = list(root.glob('*.slnx')); require(len(solutions) == 1, 'Expected one native solution')
        solution = solutions[0]
    document = ET.fromstring(solution.read_bytes())
    ET.SubElement(document, 'Project', Path='src/Application.Core/Application.Core.csproj')
    solution.write_bytes(ET.tostring(document) + b'\n')
    architecture = root / 'eng/architecture.json'; value = json.loads(architecture.read_bytes())
    value['runtimeComposition']['projects'].append({'path': 'src/Application.Core/Application.Core.csproj',
        'role': 'core', 'projectReferences': [], 'responsibilities': [
            {'name': 'Application.Core.IOwnedNotes', 'kind': 'contract', 'effects': []}]})
    for row in value['runtimeComposition']['projects']:
        if row['path'] in ['src/Application.Api/Application.Api.csproj', 'src/Application.PostgreSql/Application.PostgreSql.csproj']:
            row.setdefault('projectReferences', []).append('src/Application.Core/Application.Core.csproj')
        if row['path'] == 'src/Application.PostgreSql/Application.PostgreSql.csproj':
            row['responsibilities'] = [{'name': 'Application.PostgreSql.OwnedNotes', 'kind': 'persistence',
                'effects': ['owner-qualified note persistence'], 'provides': ['Application.Core.IOwnedNotes']}]
    value['runtimeComposition']['bindings'].append({'capabilityProject': 'src/Application.Core/Application.Core.csproj',
        'capability': 'Application.Core.IOwnedNotes', 'implementationProject': 'src/Application.PostgreSql/Application.PostgreSql.csproj',
        'implementation': 'Application.PostgreSql.OwnedNotes', 'registration': 'Application.PostgreSql.ProviderFeature.ConfigureServices'})
    write(architecture, value)
    tooling = root / 'tools/Owner.Deployment'; tooling.mkdir(parents=True)
    (tooling / 'Owner.Deployment.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup>
  <ItemGroup><ProjectReference Include="../../src/Application.PostgreSql/Application.PostgreSql.csproj" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" PrivateAssets="all" />
    <PackageReference Include="CShells.Abstractions" /></ItemGroup>
</Project>\n''', encoding='utf-8')
    for source in (fixture / 'Tooling').glob('*.cs'):
        shutil.copyfile(source, tooling / source.name)
    write(root / '.config/dotnet-tools.json', {'version': 1, 'isRoot': True,
        'tools': {'dotnet-ef': {'version': '10.0.13', 'commands': ['dotnet-ef'], 'rollForward': False}}})
    central = root / 'Directory.Packages.props'; document = ET.fromstring(central.read_bytes())
    group = ET.SubElement(document, 'ItemGroup')
    ET.SubElement(group, 'PackageVersion', Include='Microsoft.EntityFrameworkCore.Design', Version='10.0.13')
    central.write_bytes(ET.tostring(document) + b'\n')
    shutil.copyfile(fixture / 'owner-operation.mjs', root / 'eng/web/owner-operation.mjs')
    settings = root / 'runtime/policies/shells.json'; value = json.loads(settings.read_bytes())
    configuration = value['CShells']['Shells']['policies'].setdefault('Configuration', {})
    configuration.setdefault('Foundation', {}).setdefault('Web', {}).setdefault('RolePermissions', {})['user'] = ['notes.read', 'notes.write']
    write(settings, value)


def database_script():
    """Only the synthetic admin boundary provisions identities; DDL uses deployment login."""
    return r'''import base64,hashlib,hmac,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'eng'))
import composition_run as run
graph=run.read(root/'eng/foundation-composition.json');contract=run.read(root/run.render.CONTRACT)
resolved=run.read(root/run.render.RESOLVED);credentials=run.private_credentials(root,graph)
_,environment=run.compose_model(root,graph,contract,resolved,credentials)
receipt=run.latest(root,require_prepared=False);command=run.Commands(root,root/'artifacts/composition/runs'/('owner-'+sys.argv[1]))
deployment=os.environ['PROGRAMKIT_OWNER_DEPLOY_PASSWORD']
command.secrets=tuple({*credentials.values(),*environment.values(),deployment})
compose=run.compose_arguments(root,receipt);service=run.service('postgresql')
command.run([*compose,'up','-d','--wait',service],environment=environment)
mode=sys.argv[1]
def sql(statement,user='_programkit',password=None):
    child=dict(environment)
    if password:child['PGPASSWORD']=password
    args=[*compose,'exec','-T']
    if password:args+=['-e','PGPASSWORD']
    args += [service,'psql','-h','127.0.0.1','-U',user,'-d','policies','-At','-v','ON_ERROR_STOP=1','-c',statement]
    if not password:
        # Native fixture admin password is already privately owned by preparation.
        child['PGPASSWORD']=credentials[run.variable('server-admin:postgresql')]
        args=[*compose,'exec','-T','-e','PGPASSWORD',*args[len(compose)+2:]]
    return command.output(args,environment=child).strip()
if mode=='identity':
    sql("CREATE ROLE fixturedeploy LOGIN PASSWORD '"+deployment+"'; ALTER DATABASE policies OWNER TO fixturedeploy;")
    sql('REVOKE CREATE ON SCHEMA public FROM PUBLIC;')
    print(json.dumps({'deploymentIdentity':'fixturedeploy','runtimeIdentity':'policies','runtimeOwnsDatabase':False}))
elif mode=='deploy':
    command.run([*compose,'cp','artifacts/owner-migration.sql',service+':/tmp/owner-migration.sql'],environment=environment)
    child=dict(environment,PGPASSWORD=deployment)
    command.run([*compose,'exec','-T','-e','PGPASSWORD',service,'psql','-h','127.0.0.1','-U','fixturedeploy','-d','policies','-v','ON_ERROR_STOP=1','-f','/tmp/owner-migration.sql'],environment=child)
    sql('GRANT USAGE ON SCHEMA owner_example TO policies; GRANT SELECT ON owner_example.owner_notes TO policies; GRANT SELECT ON public."__EFMigrationsHistory" TO policies;',user='fixturedeploy',password=deployment)
    print(json.dumps({'migrationExecutedAs':'fixturedeploy','runtimeInsertGranted':False}))
elif mode=='grant':
    sql('GRANT INSERT ON owner_example.owner_notes TO policies;',user='fixturedeploy',password=deployment)
    print(json.dumps({'runtimeInsertGranted':True}))
elif mode=='observe':
    # Independent bounded read is kept in memory, so raw identities/digests never enter logs.
    statement='SELECT json_agg(json_build_object(\'issuer\',"OwnerIssuer",\'subject\',"OwnerSubject",\'id\',"Id",\'value\',"Value",\'digest\',encode("Digest",\'hex\')))::text FROM (SELECT * FROM owner_example.owner_notes LIMIT 100) notes;'
    args=[*compose,'exec','-T','-e','PGPASSWORD',service,'psql','-h','127.0.0.1','-U','fixturedeploy','-d','policies','-At','-v','ON_ERROR_STOP=1','-c',statement]
    observed=subprocess.run(args,env=dict(os.environ,**environment,PGPASSWORD=deployment),capture_output=True,timeout=30)
    run.require(observed.returncode==0 and len(observed.stdout)<=65536,'Independent bounded database observation failed')
    rows=json.loads(observed.stdout);run.require(isinstance(rows,list),'Expected actual persisted rows')
    key=base64.b64decode(os.environ['PROGRAMKIT_OWNER_HMAC'],validate=True)
    valid=0
    for row in rows:
        payload='\n'.join(row[field] for field in ('issuer','subject','id','value')).encode()
        expected=hmac.new(key,payload,hashlib.sha256).digest()
        valid+=hmac.compare_digest(expected,bytes.fromhex(row['digest']))
    print(json.dumps({'rows':len(rows),'owners':len({row['subject'] for row in rows}),'issuers':len({row['issuer'] for row in rows}),'externallyVerifiedDigests':valid}))
elif mode=='absent':
    print(sql("SELECT json_build_object('schemaAbsent',to_regnamespace('owner_example') IS NULL,'historyAbsent',to_regclass('public.\"__EFMigrationsHistory\"') IS NULL)::text;"))
elif mode=='restricted':
    print(sql("SELECT json_build_object('rows',(SELECT count(*) FROM owner_example.owner_notes),'insertAllowed',has_table_privilege('policies','owner_example.owner_notes','INSERT'),'schemaCreate',has_schema_privilege('policies','owner_example','CREATE'),'publicCreate',has_schema_privilege('policies','public','CREATE'))::text;"))
'''


def run_owner_operation(args, start):
    kit = start.ROOT; fixture = kit / 'tests/fixtures/composition-owner'
    directory = kit / 'artifacts/t' / ('co-' + uuid.uuid4().hex[:8]); root = directory / 'c'
    (root / 'eng').mkdir(parents=True)
    began = time.monotonic()
    secret = base64.b64encode(os.urandom(32)).decode('ascii')
    environment = dict(os.environ, PROGRAMKIT_OWNER_HMAC=secret,
        PROGRAMKIT_OWNER_DEPLOY_PASSWORD=uuid.uuid4().hex, PROGRAMKIT_BROWSER_ENGINES=args.engines,
        PROGRAMKIT_DEVICE_PYTHON=os.environ.get('PROGRAMKIT_DEVICE_PYTHON') or shutil.which('python') or sys.executable,
        PYTHONUTF8='1')
    # Generated runner inherits inputs through each child environment; no values enter authored files.
    os.environ.update({key: value for key, value in environment.items() if key.startswith('PROGRAMKIT_')})
    result = {'status': 'checking', 'profile': PROFILE, 'steps': [], 'consumer': root.relative_to(kit).as_posix(),
        'scope': 'Synthetic deterministic native execution; no consumer/human/agent acceptance authority',
        'efToolingSeam': 'Nonpackable startup project owns Design10.0.13; runtime target owns context/migrations. Does not qualify private Design in packed Build0.3.2.',
        'budgetSeconds': 300, 'timeoutSeconds': 600}

    def run(label, command, *, expected=0, cwd=root, browser=False):
        before = time.monotonic(); evidence = directory / label
        try:
            if browser:
                start.browser_command(command, cwd, evidence, expected=expected)
            else:
                start.command(command, cwd, evidence, expected=expected, environment=environment)
        finally:
            result['steps'].append({'id': label, 'seconds': round(time.monotonic()-before, 3),
                                    'evidence': evidence.relative_to(directory).as_posix()})
        return (evidence / 'stdout.log').read_text(encoding='utf-8')

    preparation = None
    try:
        graph = start.two_apps(kit, dynamic_ports=True)
        removed = {name for name in graph['resources'] if name.startswith('assessment-') or name == 'audit-db'}
        for name in removed:
            del graph['resources'][name]; graph['environments']['development']['resources'].pop(name, None)
        graph['bindings'] = [row for row in graph['bindings'] if not any(isinstance(value, str) and value in removed for value in row.values())]
        graph['bindings'].append({'kind': 'configurationEnvironment', 'featureRef': 'feature-1',
            'shellRef': 'application-shell', 'setting': 'Example:HmacSecret', 'environmentRef': SECRET_ENV})
        selection, catalog = start.accept_fixture(root, graph, kit, profile=PROFILE)
        write(root / 'composition-proposal.json', graph)
        migration = start.composition_migrate.preview(root, 'composition-proposal.json')
        start.composition_migrate.apply(root, migration['planDigest'], 'composition-proposal.json')
        sync = [sys.executable, str(start.SCRIPTS / 'dotnet_sync.py'), '--target', str(root),
            '--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
        run('scaffold', sync, cwd=kit)
        native = [sys.executable, str(kit / 'extensions/program-kit-building-blocks/scripts/building_blocks.py')]
        options = ['--target', str(root), '--catalog', str(catalog)]
        plan = json.loads(run('native-plan', [*native, 'plan', *options], cwd=kit))
        run('native-apply', [*native, 'apply', *options, '--plan-digest', plan['planDigest']], cwd=kit)
        materialize(root, fixture)
        run('tool-restore', ['dotnet', 'tool', 'restore'])
        run('native-tooling-restore', ['dotnet', 'restore', 'tools/Owner.Deployment/Owner.Deployment.csproj'])
        run('native-tooling-initial-build', ['dotnet', 'build', 'tools/Owner.Deployment/Owner.Deployment.csproj', '--configuration', 'Release', '--no-restore'])
        ef = ['dotnet', 'tool', 'run', 'dotnet-ef', '--']
        target = ['--project', 'src/Application.PostgreSql/Application.PostgreSql.csproj', '--startup-project',
                  'tools/Owner.Deployment/Owner.Deployment.csproj', '--context', 'Application.PostgreSql.PolicyDbContext', '--configuration', 'Release']
        run('native-migration', [*ef, 'migrations', 'add', 'OwnerInitial', *target])
        migrations = list((root / 'src/Application.PostgreSql/Migrations').glob('*_OwnerInitial.cs'))
        require(len(migrations) == 1, 'Native EF did not generate exactly one migration')
        native_source = migrations[0].read_text(encoding='utf-8-sig')
        (directory / 'native-owner-migration.cs.txt').write_text(native_source, encoding='utf-8')
        # Independently authored operations guard the adaptation; generated snapshot/designer remain native.
        from validate_private_ef_metadata import validate_generated_migration
        validate_generated_migration(native_source, (fixture / 'NativeOwnerInitial.expected.cs.txt').read_text(encoding='utf-8'))
        migrations[0].write_bytes((fixture / 'ReviewedOwnerInitial.cs').read_bytes())
        shutil.copyfile(fixture / 'ReviewedOwnerColumns.cs', migrations[0].parent / 'ReviewedOwnerColumns.cs')
        run('native-tooling-build', ['dotnet', 'build', 'tools/Owner.Deployment/Owner.Deployment.csproj', '--configuration', 'Release'])
        run('native-model-check', [*ef, 'migrations', 'has-pending-model-changes', *target, '--no-build'])
        run('native-migration-script', [*ef, 'migrations', 'script', '--idempotent', *target, '--no-build', '--output', 'artifacts/owner-migration.sql'])
        result['migrationSqlSha256'] = hashlib.sha256((root / 'artifacts/owner-migration.sql').read_bytes()).hexdigest()
        result['sourceSha256'] = {path.relative_to(fixture).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in fixture.rglob('*') if path.is_file()}
        run('prepare', [sys.executable, 'eng/composition_run.py', 'prepare'])
        preparation = json.loads((root / 'artifacts/composition/prepared.json').read_bytes())
        emitted = root / 'eng/composition_run.py'
        maintained = kit / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/composition_run.py'
        require(emitted.read_bytes() == maintained.read_bytes(), 'Emitted native runner differs from current maintained source')
        result['emittedRunnerSha256'] = hashlib.sha256(emitted.read_bytes()).hexdigest()
        result['helperSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['selectedHostImage'] = json.loads((root / 'eng/foundation-composition.resolved.json').read_bytes())['hostImage']
        sql = database_script()
        run('deployment-identity', [sys.executable, '-c', sql, 'identity'])
        for label, marker in [('missing-schema', 'OWNER_SCHEMA_REQUIRED'), ('missing-grants', 'OWNER_GRANTS_REQUIRED')]:
            prior_runs = set((root / 'artifacts/composition/runs').iterdir())
            run(label, [sys.executable, 'eng/composition_run.py', 'run'], expected=2)
            fresh_runs = set((root / 'artifacts/composition/runs').iterdir()) - prior_runs
            require(fresh_runs, 'Native rejection produced no new run evidence')
            observed = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for run_path in fresh_runs for path in run_path.rglob('*.log'))
            require(marker in observed, 'Compiled native Host did not produce intended rejection: ' + marker)
            result[label] = {'nativeHostFailureMarker': marker, 'compiledBeforeActivation': True}
            if label == 'missing-schema':
                absence = json.loads(run('schema-preserved-absent', [sys.executable, '-c', sql, 'absent']))
                require(absence == {'schemaAbsent': True, 'historyAbsent': True}, 'Prepare mutated absent native schema/history')
                result[label]['independentDatabaseObservation'] = absence
                run('explicit-native-deployment', [sys.executable, '-c', sql, 'deploy'])
            else:
                restricted = json.loads(run('grants-preserved-restricted', [sys.executable, '-c', sql, 'restricted']))
                require(restricted == {'rows': 0, 'insertAllowed': False, 'schemaCreate': False, 'publicCreate': False}, 'Prepare modified product rows or restricted runtime grants')
                result[label]['independentDatabaseObservation'] = restricted
        run('runtime-grant', [sys.executable, '-c', sql, 'grant'])
        run('native-ready', [sys.executable, 'eng/composition_run.py', 'run'])
        realms = list((root / 'deploy/keycloak').rglob('*realm*.json'))
        require(len(realms) == 1, 'Expected exact generated managed realm')
        realm = realms[0]
        plan = {'realm': str(realm), 'engines': args.engines.split(','),
            'origin': graph['environments']['development']['resources']['application-host']['publicOrigin'],
            'browserCache': str(root / 'artifacts/cache/playwright-browsers'),
            'fixtureSources': result['sourceSha256'], 'realmSha256': hashlib.sha256(realm.read_bytes()).hexdigest(),
            'emittedRunnerSha256': result['emittedRunnerSha256'], 'secretEnvironmentRef': SECRET_ENV}
        write(directory / 'browser-plan.json', plan)
        run('owned-browser-operation', ['node', str(root / 'eng/web/owner-operation.mjs'), str(directory / 'browser-plan.json'), str(directory / 'browser-result.json')], browser=True)
        result['browser'] = json.loads((directory / 'browser-result.json').read_bytes())
        result['identityPreservation'] = json.loads(run('native-identity-reconciliation', [sys.executable, '-c', identity_script()]))
        observed = json.loads(run('independent-database-observation', [sys.executable, '-c', sql, 'observe']))
        require(observed == {'rows': 2*len(args.engines.split(',')), 'owners': 2, 'issuers': 1, 'externallyVerifiedDigests': 2*len(args.engines.split(','))}, 'Independent product effects or externally supplied HMAC key differ')
        result['database'] = observed
        for path in [root / 'artifacts/composition/private/credentials.json', root / 'artifacts/composition/compose.json', root / 'artifacts/composition/prepared.json', root / 'runtime/policies/shells.json']:
            require(path.is_file(), 'Expected actual persistence owner missing: ' + str(path))
            require(secret not in path.read_text(encoding='utf-8'), 'Product secret persisted in public/configuration evidence')
        for path in directory.rglob('*.log'):
            require(secret not in path.read_text(encoding='utf-8', errors='replace'), 'Product secret escaped into diagnostic logs')
        result['status'] = 'passed'
    except BaseException:
        result['status'] = 'failed'
        raise
    finally:
        finish_owner_operation(root, preparation, directory, start.dispose_fixture, result, began)
    return 0


def finish_owner_operation(root, preparation, directory, dispose, result, began):
    """Seal observed cleanup honestly, including setup failure without disposal."""
    result.update(cleanupAttempted=False, cleanupComplete=None,
                  cleanupDisposition='unverified-no-successful-preparation')
    try:
        if preparation is not None:
            result['cleanupAttempted'] = True
            dispose(root, preparation, directory / 'dispose')
            result.update(cleanupComplete=True, cleanupDisposition='completed')
    except BaseException:
        result.update(status='failed', cleanupComplete=False, cleanupDisposition='failed')
        raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic()-began, 3)
        result['withinBudget'] = result['elapsedSeconds'] <= result['budgetSeconds']
        write(directory / 'result.json', result)
        print(json.dumps({'status': result['status'], 'evidence': str(directory), 'elapsedSeconds': result['elapsedSeconds'], 'withinBudget': result['withinBudget']}))


def identity_script():
    """Exercise persisted provider IDs, including unrelated synthetic realm entries."""
    return '''import json,sys
from pathlib import Path
from urllib.parse import quote
root=Path.cwd();sys.path.insert(0,str(root/'eng'))
import composition_run as run
import keycloak_composition as keycloak
graph=run.read(root/'eng/foundation-composition.json');binding=run.model.environment(graph)['product-identity']
credentials=run.private_credentials(root,graph)
password=credentials[run.variable('identity-admin:product-identity')]
admin=keycloak.Administration(binding['publicOrigin'],password)
base='/admin/realms/'+quote(binding['realm'],safe='')
admin.request('POST',base+'/users',{'username':'fixture-retained-user','enabled':True})
admin.request('POST',base+'/clients',{'clientId':'fixture-retained-client','enabled':True,'protocol':'openid-connect'})
def snapshot():
    users={row['username']:row['id'] for row in admin.get(base+'/users?max=100')}
    clients={row['clientId']:row['id'] for row in admin.get(base+'/clients')}
    return users,clients
before=snapshot()
realm=run.read(root/('deploy/keycloak/product-identity/'+binding['realm']+'-realm.json'))
prior=run.read(root/'artifacts/composition/private/identity-state.json')['product-identity']
keycloak.reconcile(graph,'product-identity',realm,password,prior)
after=snapshot()
run.require(before==after,'Native reconciliation changed persisted user or client identities')
run.require('fixture-retained-user' in after[0] and 'fixture-retained-client' in after[1],'Unrelated authored realm identities disappeared')
print(json.dumps({'persistedUserIdsPreserved':True,'persistedClientIdsPreserved':True,'unrelatedUserAndClientPreserved':True,'nativeReconciliation':True}))
'''

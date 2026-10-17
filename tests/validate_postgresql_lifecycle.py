"""Qualify deployment/runtime separation on one owned PostgreSQL container, never a user database."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT/'extensions/program-kit-dotnet/references/examples/postgresql-lifecycle'
sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/scripts'))
import foundation_composition
import composition_model
import composition_render
sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
from central_packages import central_package_versions
from owned_scratch import native_path
import composition_run
from composition_fixture import accept_fixture


def main():
    identity = uuid.uuid4().hex
    evidence = ROOT/'artifacts/postgresql-lifecycle'/identity
    evidence.mkdir(parents=True)
    consumer = ROOT/'artifacts/t'/('pg-'+identity[:12])
    consumer.mkdir(parents=True)
    version = foundation_composition.publisher_contracts(ROOT, selected_packages=['Orbyss.Foundation.PostgreSql'])['packages']['Orbyss.Foundation.PostgreSql']
    policy = ROOT/'extensions/program-kit-dotnet/references/persistence-runtimes.json'
    image = json.loads(policy.read_text())['profiles']['ef-postgresql']['image']
    name = 'program-kit-postgresql-'+identity
    database = 'pk_fixture_'+identity
    deployer = 'pk_deploy_'+identity
    runtime = 'pk_runtime_'+identity
    # Credentials are synthetic and confined to this exact owned container.
    password = 'synthetic-'+uuid.uuid4().hex
    deployment_password = 'synthetic-'+uuid.uuid4().hex
    runtime_password = 'synthetic-'+uuid.uuid4().hex
    def redact(value):
        for secret in (password, deployment_password, runtime_password):
            value = value.replace(secret, '[REDACTED]')
        return value
    env = dict(os.environ)
    env.update(NUGET_PACKAGES=str(consumer/'artifacts/nuget'), NUGET_HTTP_CACHE_PATH=str(consumer/'artifacts/http'),
               DOTNET_CLI_HOME=str(ROOT/'artifacts/cache/postgresql-lifecycle/dotnet'),
               MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0', PYTHONUTF8='1')
    steps = []
    cases = []
    source_files = [Path(__file__), policy, Path(composition_model.__file__), Path(composition_render.__file__),
                    Path(composition_run.__file__), ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json',
                    ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Packages.props', *EXAMPLE.iterdir()]
    source_basis = {file.relative_to(ROOT).as_posix():hashlib.sha256(file.read_bytes()).hexdigest()
                    for file in source_files if file.is_file()}
    result = {'status': 'running', 'scope': 'Synthetic local deployment and native Foundation runtime units; no production migration or ownership repair',
              'image': image, 'selectedFoundationVersion': version, 'consumer': str(consumer), 'steps': steps, 'cases': cases, 'cleanupObserved': False}
    created = False
    def run(label, arguments, *, environment=env, expected=0, timeout=180, sql=None):
        # Native executables receive native Windows spellings; filesystem reads
        # retain the extended paths needed for complete historical knowledge.
        arguments = [native_path(argument) if argument.startswith('\\\\?\\') else argument for argument in arguments]
        environment = {key: native_path(value) if value.startswith('\\\\?\\') else value for key, value in environment.items()}
        observed = subprocess.run(arguments, input=sql, cwd=native_path(consumer), env=environment, capture_output=True,
                                  text=True, encoding='utf-8', timeout=timeout)
        for stream in ('stdout', 'stderr'):
            (evidence/(label+'.'+stream+'.log')).write_text(redact(getattr(observed, stream)), encoding='utf-8')
        # SQL input and environment values stay out of evidence; redact the
        # synthetic credential in Docker's exact creation arguments as well.
        steps.append({'id': label, 'command': [redact(argument) for argument in arguments], 'exitCode': observed.returncode})
        assert (observed.returncode == 0) == (expected == 0), (str(evidence/(label+'.stderr.log')) + '\n' + redact(observed.stderr))
        return observed.stdout.strip()
    def sql(label, text, user='fixture', success=True):
        return run(label, ['docker', 'exec', '-i', name, 'psql', '-h', '127.0.0.1', '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-U', user, '-d', database],
                   sql=text, expected=0 if success else 1)
    try:
        for file in EXAMPLE.iterdir():
            if file.is_file(): shutil.copyfile(file, consumer/file.name)
        shutil.copyfile(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json', consumer/'global.json')
        shutil.copyfile(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/NuGet.config', consumer/'NuGet.config')
        native_version = central_package_versions(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files')['cshells.abstractions']
        pin = '-p:SelectedFoundationVersion='+version+';SelectedCShellsVersion='+native_version
        run('restore', ['dotnet', 'restore', 'PostgreSqlLifecycle.csproj', pin, '--configfile', 'NuGet.config', '--disable-build-servers'], timeout=300)
        run('locked', ['dotnet', 'restore', 'PostgreSqlLifecycle.csproj', pin, '--locked-mode', '--configfile', 'NuGet.config', '--disable-build-servers'])
        run('build', ['dotnet', 'build', 'PostgreSqlLifecycle.csproj', pin, '--no-restore', '--disable-build-servers', '-m:1'])
        dll = str(consumer/'bin/Debug/net10.0/PostgreSqlLifecycle.dll')
        dll_sha256 = hashlib.sha256(Path(dll).read_bytes()).hexdigest()
        template = ROOT/'extensions/program-kit-dotnet/templates/dotnet'
        graph = composition_model.from_legacy(json.loads((template/'compositions/foundation-bff-keycloak-postgresql.json').read_text()))
        host_id = next(iter(composition_model.resources(graph,'host')))
        shell_id = next(iter(composition_model.resources(graph,'shell')))
        feature_id = next(row['featureRef'] for row in composition_model.bindings(graph,'databaseProvider'))
        graph['resources'][shell_id]['name'] = 'fixture'
        graph['resources']['fixture-files'] = {'kind':'privateFiles','ownerRef':'fixture-owner'}
        graph['bindings'].append({'kind':'privateFiles','filesRef':'fixture-files','hostRef':host_id,
                                  'shellRef':shell_id,'featureRef':feature_id,'setting':'Root'})
        for configured in graph['environments'].values():
            configured['resources']['fixture-files'] = {'directory':'artifacts/private/fixture-files'}
        binding_root = consumer/'binding-source'
        binding_root.mkdir()
        accept_fixture(binding_root, graph, ROOT)
        projections = composition_render.materialize(binding_root, graph, template)
        contract = json.loads(projections[composition_render.CONTRACT][0])
        resolved = composition_render.resolve(graph, contract)
        document, _ = composition_run.compose_model(binding_root, graph, contract, resolved, defaultdict(lambda:'synthetic-unsubmitted'))
        binding = composition_model.private_file_bindings(graph)[0]
        emitted = document['services'][composition_run.service(host_id)]['environment']
        value = emitted[binding['environmentKey']]
        flat_key = binding['environmentKey'].replace('__',':')
        native_configuration = {'CShells:Shells:fixture:Features:ProgramKit.PrivateFilesBinding':'true', flat_key:value}
        configuration = evidence/'emitted-provider-binding.json'
        configuration.write_text(json.dumps(native_configuration))
        assert run('actual-emitted-binding',['dotnet',dll,'binding',str(configuration)]) == hashlib.sha256(value.encode()).hexdigest()
        cases.append('actual-emitted-private-key-native-shell-registration')
        for label, alternate in [('invented-key',dict(native_configuration)),('missing-key',dict(native_configuration))]:
            alternate.pop(flat_key)
            if label == 'invented-key': alternate['CShells:Shells:fixture:Configuration:PolicyEvidence:RootPath'] = value
            path = evidence/(label+'.json'); path.write_text(json.dumps(alternate))
            run(label,['dotnet',dll,'binding',str(path)],expected=1)
            cases.append(label+'-native-activation-denied-without-fallback')
        metadata = binding_root/Path(binding['featurePath']).parent/'settings.source.json'
        metadata.parent.mkdir(parents=True)
        declaration = {'schemaVersion':2,'packageId':graph['resources'][feature_id]['packageId'],
                       'sourceSha256':{},'contracts':[{'scope':'fixture-files','complete':True,'settings':[{'path':binding['configurationKey']}]}]}
        metadata.write_text(json.dumps(declaration))
        assert composition_model.provider_binding_declarations(binding_root,graph)[0]['status'].startswith('declared-key-matches')
        declaration['contracts'][0]['settings'][0]['path']='PolicyEvidence:RootPath'
        metadata.write_text(json.dumps(declaration))
        try: composition_model.provider_binding_declarations(binding_root,graph)
        except ValueError as error: assert 'does not cover composition binding' in str(error)
        else: raise AssertionError('Invented declared metadata key admitted')
        cases.append('mismatched-native-source-declaration-diagnosed-before-dependent-work')
        run('container-create', ['docker', 'run', '--detach', '--rm', '--name', name,
             '--label', 'org.orbyss.program-kit.disposable=postgresql-lifecycle', '--publish', '127.0.0.1::5432',
             '--env', 'POSTGRES_USER=fixture', '--env', 'POSTGRES_PASSWORD='+password, '--env', 'POSTGRES_DB='+database, image], timeout=90)
        created = True
        # The entrypoint's temporary Unix-socket server accepts readiness before
        # shutting down. TCP belongs to the final server used by native runtime.
        for attempt in range(100):
            ready = subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','fixture','-d',database], capture_output=True, timeout=5)
            if ready.returncode == 0: break
            time.sleep(.1)
        else: raise AssertionError('Owned database did not become ready')
        port = int(run('container-port', ['docker','port',name,'5432/tcp']).rsplit(':',1)[1])
        sql('provision-identities', f'''COMMENT ON DATABASE "{database}" IS 'program-kit-disposable:{identity}';
CREATE ROLE "{deployer}" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD '{deployment_password}';
CREATE ROLE "{runtime}" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD '{runtime_password}';
GRANT CONNECT,CREATE ON DATABASE "{database}" TO "{deployer}";
GRANT CONNECT ON DATABASE "{database}" TO "{runtime}";
''')
        base = f'Host=127.0.0.1;Port={port};Database={database};'
        preparation_env = dict(env, PK_FIXTURE_DEPLOYMENT=base+'Username='+deployer+';Password='+deployment_password)
        runtime_env = dict(env, PK_FIXTURE_RUNTIME=base+'Username='+runtime+';Password='+runtime_password)
        assert len({password, deployment_password, runtime_password}) == 3
        result['runtimeDeploymentCredentialDistinct'] = True
        # Runtime children receive no deployment/admin connection variables.
        for key in ('PK_FIXTURE_DEPLOYMENT','PGPASSWORD','PGUSER','FOUNDATION_POSTGRES_TEST_CONNECTION'):
            runtime_env.pop(key, None)
        def native(label, mode, environment, success=True):
            return run(label,['dotnet',dll,mode,identity,label],environment=environment,expected=0 if success else 1)
        assert sql('initial-absence',f"SELECT count(*) FROM pg_namespace WHERE nspname='{database}'") == '0'
        cases.append('schema-proved-absent-before-first-parallel-preparation')
        with ThreadPoolExecutor(max_workers=8) as pool:
            outputs = list(pool.map(lambda index: native('prepare-'+str(index),'prepare',preparation_env), range(8)))
        assert outputs.count('created') == 1 and outputs.count('existing') == 7, outputs
        cases.append('eight-real-first-preparations-one-deployment')
        with ThreadPoolExecutor(max_workers=8) as pool:
            pending = [pool.submit(native,'runtime-'+str(index),'runtime',runtime_env) for index in range(8)]
            overlaps = []
            while not all(future.done() for future in pending):
                overlaps.append(int(sql('observe-overlap-'+str(len(overlaps)),
                    f"SELECT count(*) FROM pg_stat_activity WHERE application_name='pk-runtime-{identity}' AND state='active' AND xact_start IS NOT NULL")))
                time.sleep(.05)
            outputs = [future.result() for future in pending]
        assert outputs == ['runtime-admitted']*8
        assert max(overlaps, default=0) >= 2, 'No actual overlapping runtime transactions were observed'
        result['observedConcurrentRuntimeTransactions'] = max(overlaps)
        assert sql('independent-effects',f'SELECT count(*) FROM "{database}".entries') == '8'
        cases.append('eight-concurrent-native-runtime-units-independent-committed-effects')
        # Test grant admission against the shipped lifecycle recipe instead of
        # maintaining a second handwritten synthetic deployment recipe.
        sql('unrelated-table', 'CREATE TABLE public.unrelated_fixture(secret text)')
        for label, statement in [('ddl',f'CREATE TABLE "{database}".forbidden(id int)'),('journal-write',f'DELETE FROM "{database}".journal'),
                                  ('schema-create', 'CREATE SCHEMA runtime_created'),
                                  ('unrelated-table', 'SELECT secret FROM public.unrelated_fixture'),
                                  ('role-escalation',f'ALTER ROLE "{runtime}" SUPERUSER')]:
            sql('runtime-denied-'+label,statement,user=runtime,success=False)
            cases.append('runtime-denied-'+label)
        sql('revoke-delete',f'REVOKE DELETE ON "{database}".entries FROM "{runtime}"')
        native('missing-single-grant','runtime',runtime_env,False)
        assert sql('no-effect-after-denied-admission',f'SELECT count(*) FROM "{database}".entries') == '8'
        sql('restore-delete',f'GRANT DELETE ON "{database}".entries TO "{runtime}"')
        cases.append('one-missing-grant-blocks-runtime-before-effect')
        sql('wrong-revision',f'ALTER TABLE "{database}".journal DROP CONSTRAINT journal_revision_check; UPDATE "{database}".journal SET revision=2')
        native('wrong-revision','runtime',runtime_env,False)
        sql('restore-revision',f'UPDATE "{database}".journal SET revision=1; ALTER TABLE "{database}".journal ADD CONSTRAINT journal_revision_check CHECK(revision=1)')
        cases.append('wrong-revision-denied-without-startup-DDL')
        # Retained mode has no repair path: unexpected objects and owner changes
        # reject before any schema mutation; original data remains visible.
        for kind, statement, undo in [
            ('view',f'CREATE VIEW "{database}".foreign_view AS SELECT 1 AS value',f'DROP VIEW "{database}".foreign_view'),
            ('function',f'CREATE FUNCTION "{database}".foreign_function() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$',f'DROP FUNCTION "{database}".foreign_function()'),
            ('sequence',f'CREATE SEQUENCE "{database}".foreign_sequence',f'DROP SEQUENCE "{database}".foreign_sequence'),
            ('domain',f'CREATE DOMAIN "{database}".foreign_domain AS integer',f'DROP DOMAIN "{database}".foreign_domain')]:
            sql('foreign-'+kind,statement)
            native('reject-'+kind,'prepare',preparation_env,False)
            assert sql('preserve-data-'+kind,f'SELECT count(*) FROM "{database}".entries') == '8'
            sql('remove-fixture-negative-'+kind,undo)
            cases.append('unexpected-'+kind+'-refused-with-data-preserved')
        sql('change-owner',f'ALTER TABLE "{database}".entries OWNER TO fixture')
        native('foreign-owner','prepare',preparation_env,False)
        assert sql('foreign-owner-data-preserved',f'SELECT count(*) FROM "{database}".entries') == '8'
        sql('restore-owner',f'ALTER TABLE "{database}".entries OWNER TO "{deployer}"')
        cases.append('foreign-table-owner-refused-without-transfer')
        assert native('owned-schema-cleanup','cleanup',preparation_env) == 'removed'
        assert sql('schema-cleanup-observed',f"SELECT count(*) FROM pg_namespace WHERE nspname='{database}'") == '0'
        cases.append('schema-cleanup-independently-observed')
        # Even an empty correctly named schema without its original marker is not
        # adopted or silently destroyed. Container removal owns final test cleanup.
        sql('unmarked-schema',f'CREATE SCHEMA "{database}" AUTHORIZATION "{deployer}"')
        native('unmarked-refused','prepare',preparation_env,False)
        assert sql('unmarked-preserved',f"SELECT count(*) FROM pg_namespace WHERE nspname='{database}'") == '1'
        cases.append('unmarked-empty-schema-refused-and-preserved')
        required = json.loads((EXAMPLE/'required-cases.json').read_text())
        assert len(cases)==len(set(cases)) and set(cases)==set(required), 'Required native lifecycle case omitted/substituted'
        executed = {}
        assets = json.loads((consumer/'obj/project.assets.json').read_text())['targets']['net10.0']
        for package, details in assets.items():
            package_id, package_version = package.split('/')
            archive = Path(env['NUGET_PACKAGES'])/package_id.lower()/package_version/(package_id.lower()+'.'+package_version+'.nupkg')
            with zipfile.ZipFile(archive) as native:
                for asset in details.get('runtime', {}):
                    if not asset.endswith('.dll'): continue
                    expected = native.read(asset)
                    actual = consumer/'bin/Debug/net10.0'/Path(asset).name
                    assert actual.read_bytes() == expected, 'Executed native DLL differs from restored archive'
                    executed[actual.name] = {'package':package,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                                            'asset':asset,'sha256':hashlib.sha256(expected).hexdigest()}
        assert source_basis == {file.relative_to(ROOT).as_posix():hashlib.sha256(file.read_bytes()).hexdigest()
                                for file in source_files if file.is_file()}, 'Qualifier source changed during execution'
        assert hashlib.sha256(Path(dll).read_bytes()).hexdigest() == dll_sha256, 'Executed fixture changed during qualification'
        result.update(status='passed', sourceSha256=source_basis,
                      fixtureAssemblySha256=dll_sha256,
                      executedRuntime=executed,
                      packageLockSha256=hashlib.sha256((consumer/'packages.lock.json').read_bytes()).hexdigest())
        return 0
    except BaseException as error:
        result.update(status='failed', diagnostic=redact(str(error)))
        raise
    finally:
        cleanup_error = None
        if created:
            try:
                run('container-cleanup',['docker','rm','--force',name],timeout=30)
                observed = subprocess.run(['docker','ps','-a','--filter','name=^/'+name+'$','--format','{{.ID}}'],capture_output=True,text=True,timeout=15)
                result['cleanupObserved'] = observed.returncode==0 and not observed.stdout.strip()
                assert result['cleanupObserved'], 'Owned container cleanup was not observed'
            except BaseException as error:
                cleanup_error = error
                result.update(status='failed', cleanupDiagnostic=redact(str(error)))
        (evidence/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('PostgreSQL lifecycle evidence: '+str(evidence/'results.json'))
        if cleanup_error is not None: raise cleanup_error


if __name__ == '__main__':
    raise SystemExit(main())

"""Explicit, maintained integration checks of the actual selected consumer package roots.

The probe and its HTTP endpoints are test-only: they are staged in an owned copy of
the sealed production bundle. They are never selected into the production package
graph. Application operation adapters remain application-owned.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import http.client
import json
import os
import re
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import urlsplit
import uuid
import xml.etree.ElementTree as ET
import zipfile

def require(condition, message):
    if not condition:
        raise ValueError(message)

CASES = {
    'host-activation': ['Foundation.actual_selected_feature_activation', 'Foundation.actual_bound_effective_settings'],
    'bff-cookie': ['Foundation.maintained_bff_cookie'],
    'keycloak': ['Foundation.public_issuer_private_backchannel'],
    'postgresql': ['Foundation.provider_connectivity_restart'],
}


def setup_contract(configuration):
    """One authoritative orchestration contract, safe to call during materialization."""
    capabilities = ['host-activation', 'bff-cookie', 'keycloak']
    if configuration['compositionId'].endswith('-postgresql'):
        capabilities.append('postgresql')
    prefix = ['python', 'eng/foundation_qualification.py', '--repository', '.', '--run-directory', '{runDirectory}']
    return {'setup': {'environmentInputs': ['PROGRAMKIT_BROWSER_ENGINES', 'PLAYWRIGHT_BROWSERS_PATH','PROGRAMKIT_IDENTITY_AUTHORITY','PROGRAMKIT_QUALIFY_PRODUCT','GITHUB_ACTIONS'],
                      'steps': [{'id': 'foundation-'+kind, 'stage': kind, 'command': [*prefix, '--stage', kind],
                                 'cwd': '.', 'timeoutSeconds': 1200} for kind in ('restore', 'build', 'services')]},
            'tests': {'capabilities': capabilities,
                      'commands': [{'id': 'foundation-'+capability, 'capability': capability,
                                    'command': [*prefix, '--check', capability], 'cwd': '.', 'timeoutSeconds': 1200,
                                    'result': {'path': '{runDirectory}/'+capability+'.xml', 'format': 'junit',
                                               'cases': CASES[capability]}} for capability in capabilities]}}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def crawler_following_support(root, selected):
    """Capability comes from the exact selected owner, independent of policy permission."""
    path = root/'eng/foundation-settings.contract.json'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == selected['contractSha256'],
            'PKF105 selected settings contract bytes changed')
    owner = 'Orbyss.Foundation.WebDefaults'
    rows = [row for row in json.loads(raw)['contracts'] if row['packageId'] == owner]
    require(len(rows) == 1, 'PKF105 selected response-policy owner contract absent or ambiguous')
    row = rows[0]; metadata = row['metadata']
    version = selected['packages'][owner]
    require(row['version'] == version and metadata['packageId'] == owner and metadata['packageVersion'] == version,
            'PKF105 response-policy capability differs from exact selected package')
    setting_path = 'Foundation:Web:ResponsePolicies:Policies:{policyName}:AllowFollowing'
    settings = [setting for contract in metadata['contracts'] if contract['owner'] == owner
                and contract['scope'] == 'web-response-policy' and contract.get('complete') is True
                for setting in contract['settings'] if setting['path'] == setting_path]
    require(len(settings) <= 1 and all(setting['type'] == 'boolean' for setting in settings),
            'PKF105 selected crawler following capability is invalid or ambiguous')
    return {'supported': bool(settings), 'owner': owner, 'version': version,
            'contractSha256': selected['contractSha256'], 'settingPath': setting_path,
            'meaning': 'Selected typed capability; false policy permission does not disable private-resource denial assertions.'}


def activated_settings(root,selected,configuration,bound):
    """Require actual selected owners, private transport and exact executed archive bytes."""
    owners=bound.get('owners',[])
    expected={('Orbyss.Foundation.WebDefaults','Foundation:Web'),
              ('Orbyss.Foundation.WebDefaults','Foundation:Web:ResponsePolicies'),
              ('Orbyss.Foundation.Json.AspNetCore','Foundation:Json')}
    if 'postgresql' in selected['tests']['capabilities']:
        expected.add(('Orbyss.Foundation.PostgreSql','Foundation:PostgreSql:Policies:application'))
    actual={(row.get('owner'),row.get('section')) for row in owners if row.get('observationStatus','').startswith('activated')}
    require(expected<=actual,'PKF104 selected owner options were not actually activated: '+str(sorted(expected-actual)))
    observed=[bound['authenticationAssembly'],bound['profileAssembly'],*[row for row in owners if row.get('assemblySha256')]]
    for owner in observed:
        archives=list((root/selected['runtimeStage']/'packages').glob(owner['owner']+'.*.nupkg'))
        archives=[path for path in archives if path.name.startswith(owner['owner']+'.'+selected['packages'][owner['owner']]+'.') or
                  path.name==owner['owner']+'.'+selected['packages'][owner['owner']]+'.nupkg']
        require(len(archives)==1,'PKF104 selected owner archive is absent or ambiguous: '+owner['owner'])
        with zipfile.ZipFile(archives[0]) as archive:
            names=[name for name in archive.namelist() if name.startswith('lib/') and name.endswith('/'+owner['owner']+'.dll')]
            require(names and any(hashlib.sha256(archive.read(name)).hexdigest()==owner['assemblySha256'] for name in names),
                    'PKF104 observed owner bytes differ from exact selected package: '+owner['owner'])
    observations=bound['settings']
    private=next(row for row in observations if row['path']=='Foundation:Web:BackchannelAuthority')
    require(private['value']==configuration['identity']['backchannelOrigin']+'/realms/'+configuration['identity']['realm'],
            'PKF104 activated identity private backchannel differs from declared transport')
    bound['provenanceMeaning']='Actual winning shell IConfigurationRoot provider type/index for configured inputs. Host projects deployment inputs into the shell MemoryConfigurationProvider; this is not a reconstructed original JSON/environment provider chain. Actual options values can additionally be normalized by owner delegates.'
    bound['controlledConsumerShellsSha256']=hashlib.sha256((root/'shells.json').read_bytes()).hexdigest()
    bound['configuredSourceView']='effective-settings.configured.json (source projection; deployment secrets forwarded separately through environment)'
    bound['testOnlyOverlays']={'Foundation:Web:RolePermissions':{'admin':['foundation.probe']}}
    bound['testOnlyFeature']='ProgramKit.Qualification.Probe; installed only into owned copied runtime, never the production selected graph'
    import foundation_composition
    contracts=list(foundation_composition.rows(read(root/foundation_composition.CONTRACT)))
    for rows in [bound['settings'],*[row.get('settings',[]) for row in owners]]:
        for observation in rows:
            actual_parts=observation['path'].split(':')
            observation['additionalActiveOwnerRequirements']=[{'owner':owner,'scope':metadata['scope'],
                'constraints':setting['constraints'],'reference':'eng/foundation-settings.contract.json',
                'meaning':'Selected source-backed admission requirements; no second options instance is bound.'}
                for owner,metadata,setting in contracts
                if len(setting['path'].split(':'))==len(actual_parts) and
                   all(declared==actual or declared.startswith('{') for declared,actual in zip(setting['path'].split(':'),actual_parts))]
            for source in observation['sources']:
                if source['provider']=='Microsoft.Extensions.Configuration.Memory.MemoryConfigurationProvider':
                    source['meaning']='Native shell projection; original host provider ordering is not retained in this shell root.'
    return observations


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def local_origin(value):
    uri = urlsplit(value)
    require(uri.scheme == 'http' and uri.hostname in ('localhost', '127.0.0.1') and uri.port,
            'PKF101 executable qualification supports only an explicit disposable loopback Development origin')
    return uri


def bundle_hashes(root, selected):
    bundle = root / selected['runtimeStage']
    require(bundle.is_dir(), 'PKF101 build and stage the actual selected package roots first')
    return {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(bundle.rglob('*')) if p.is_file()}


class Commands:
    def __init__(self, root, directory):
        from openapi_pipeline import repository_nuget_environment
        self.root, self.directory, self.counter = root, directory, 0
        self.secrets=()
        self.environment=repository_nuget_environment(root)

    def run(self, command, *, cwd=None, timeout=300, environment=None, secrets=(), expected=0):
        from foundation_fixture import captured
        self.counter += 1
        evidence = self.directory / ('process-' + uuid.uuid4().hex)
        selected_environment=dict(self.environment,**(environment or {}))
        for name,value in self.environment.items():
            if value.startswith(str(self.root/'artifacts/cache')) or name in ('DOTNET_CLI_TELEMETRY_OPTOUT','DOTNET_SKIP_FIRST_TIME_EXPERIENCE','DOTNET_NOLOGO'):
                selected_environment[name]=value
        observed = captured(command, cwd or self.root, evidence, timeout=timeout,
                            environment=selected_environment, secret_values=(*self.secrets,*secrets))
        require(observed['exitCode'] == expected and observed['logsDrained'] and observed['cleanupComplete'],
                'PKF102 maintained command failed; inspect ' + str(evidence))
        return (evidence / 'stdout.log').read_text(encoding='utf-8').strip()


def solution(root):
    solutions = list(root.glob('*.sln')) + list(root.glob('*.slnx'))
    require(len(solutions) == 1, 'PKF101 expected one real consumer solution')
    return solutions[0].name


def npm_command(root, arguments):
    # The maintained selector owns portable active commands, exact versions,
    # repository cache and TLS trust. Never infer npm's installation layout.
    from js_toolchain import context
    command, environment = context(root, root/'artifacts/program-kit/toolchain.json')
    return [*command, *arguments], environment


def playwright_command(root, arguments):
    return ['node',str(root/'eng/web/node_modules/playwright/cli.js'),*arguments]


def stage(root, selected, kind, directory):
    command = Commands(root, directory)
    stage_started=time.monotonic(); timings={}
    if kind == 'restore':
        before=time.monotonic()
        command.run(['python', 'eng/toolchain.py', '--repository', '.', '--evidence', 'artifacts/program-kit/toolchain.json'], timeout=120)
        timings['toolchainVerificationSeconds']=round(time.monotonic()-before,3)
        before=time.monotonic()
        command.run(['pwsh', '-NoProfile', '-File', 'eng/Restore.ps1', '-Subject', solution(root)], timeout=900)
        timings['nugetAcquisitionRestoreSeconds']=round(time.monotonic()-before,3)
        before=time.monotonic()
        npm, environment = npm_command(root, ['ci'])
        command.run(npm, cwd=root/'eng/web', timeout=600, environment=environment)
        timings['npmAcquisitionRestoreSeconds']=round(time.monotonic()-before,3)
    elif kind == 'build':
        version = (root/'VERSION').read_text(encoding='utf-8').strip()
        import release_bundle
        import runtime_closure
        packages = root/'artifacts/packages'/version/uuid.uuid4().hex
        packages.mkdir(parents=True)
        # Restore.ps1 owns this exact cache. No ambient global package folder can
        # silently turn a measured fresh-cache run into prepared-machine evidence.
        environment = dict(os.environ, NUGET_PACKAGES=str(root/'artifacts/cache/nuget/packages'))
        command.run(['python','eng/repository_architecture.py','--repository','.', '--manifest','eng/architecture.json',
                     '--configuration','Release','--build-subject',solution(root),'--version',version,
                     '--output',str(directory/'architecture.xml')], environment=environment,timeout=600)
        # Native architecture tools may create their own first locked restore.
        # Capture production pack inputs afterwards, then build and seal without
        # accepting any source/toolchain mutation across the pack boundary.
        runtime_closure.prepare_pack(root, packages)
        command.run(['dotnet', 'build', solution(root), '-c', 'Release', '--no-restore', '-p:Version='+version],
                    environment=environment, timeout=600)
        command.run(['dotnet', 'pack', solution(root), '-c', 'Release', '--no-build', '-p:Version='+version,
                     '-o', str(packages)], environment=environment, timeout=600)
        runtime_closure.seal_pack(root, packages)
        release_bundle.stage(root, packages, root/selected['runtimeStage'], inventory=packages/'program-kit-pack.json',
                             root_packages=selected['rootPackages'])
    else:
        # Explicit setup acquires the exact selected immutable images. This
        # starts no service; integration owns disposable lifetimes and retains
        # --pull=never so it activates only these prepared artifact identities.
        images = [selected['hostImage']['reference'] if isinstance(selected['hostImage'], dict) else selected['hostImage'],
                  *selected['serviceImages'].values()]
        require(all(isinstance(image, str) and '://' not in image and re.fullmatch(r'[a-z0-9][a-z0-9._/:+-]*@sha256:[a-f0-9]{64}', image)
                    for image in images), 'PKF101 service preparation requires exact immutable selected image references')
        for image in images:
            command.run(['docker', 'pull', image], timeout=300)
        engines = os.environ.get('PROGRAMKIT_BROWSER_ENGINES', 'chromium,webkit').split(',')
        require(engines and set(engines) <= {'chromium', 'webkit', 'firefox'}, 'PKF101 invalid browser engine selection')
        install = ['install']
        if os.name != 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true':
            install.append('--with-deps')  # System prerequisites belong to the CI-owned runner.
        command.run(playwright_command(root,[*install, *engines]), cwd=root/'eng/web', timeout=600)
    write(directory/(kind+'-timings.json'),{**timings,'elapsedSeconds':round(time.monotonic()-stage_started,3)})


def request(origin, path):
    uri = urlsplit(origin)
    with closing(http.client.HTTPConnection(uri.hostname, uri.port, timeout=3)) as connection:
        connection.request('GET', path)
        response = connection.getresponse()
        return response.status, response.read()


def ready(origin, path):
    try:
        status,data=request(origin,path)
        if status>=500 and path=='/__foundation/settings':
            detail=json.loads(data)
            allowed={key:detail[key] for key in ('status','phase','configurationType','errorType','owner','diagnostic') if key in detail}
            raise ValueError('PKF103 activated observation failed: '+json.dumps(allowed))
        require(status<500,'PKF103 activated host returned HTTP '+str(status)+'; inspect its preserved owner logs')
        return status == 200
    except (OSError, TimeoutError):
        return False


def product_outcome(result, action, phase='first-operation-and-native-tests'):
    """Record opted application proving independently from the maintained platform cases."""
    result['productPhase']={'phase':phase,'status':'running'}
    try:
        action()
        require(result.get('productAcceptance') is True,'PKF105 actual application product acceptance was not established')
        result['productPhase']={'phase':phase,'status':'passed'}
    except (OSError,ValueError,KeyError) as error:
        result['productAcceptance']=False
        result['productPhase']={'phase':phase,'status':'failed','failure':'application-proving-failed','errorType':type(error).__name__,
            'diagnostic':'Application proving failed; inspect owned product/native command streams. Platform cases remain independently recorded.'}
    result.setdefault('productPhases',[]).append(result['productPhase'])


RUNTIME_SNAPSHOT_INPUTS = ('shells.json','hostsettings.json','nuplane.settings.json','packages')


def runtime_snapshot_inputs(base):
    """Hash only deployed config/feed inputs; .installed is owned mutable cache."""
    return {path.relative_to(base).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
            for name in RUNTIME_SNAPSHOT_INPUTS
            for path in ([base/name] if (base/name).is_file() else (base/name).rglob('*'))
            if path.is_file() and path.relative_to(base).parts[:2] != ('packages','.installed')}


def verify_runtime_snapshot(runtime, host, directory, command, expected):
    """Reverse-copy actual deployed inputs before startup and after operations."""
    directory.mkdir()
    for name in RUNTIME_SNAPSHOT_INPUTS:
        command.run(['docker','cp',host+':/app/'+name,str(directory/name)])
    observed = runtime_snapshot_inputs(directory)
    require(expected and observed == expected and runtime_snapshot_inputs(runtime) == expected,
            'PKF101 deployed runtime snapshot inputs changed')
    return {'byteIdentityVerified':True, 'sourceInputs':expected, 'containerCopyInputs':observed,
            'observationDirectory':directory.name, 'excludedMutableCache':'packages/.installed only'}


def copy_runtime_snapshot(runtime, host, directory, command):
    """Install and verify the owned selected snapshot in a stopped immutable Host."""
    expected = runtime_snapshot_inputs(runtime)
    require(all((runtime/name).exists() for name in RUNTIME_SNAPSHOT_INPUTS) and expected,
            'PKF101 selected runtime snapshot inputs missing')
    for name in RUNTIME_SNAPSHOT_INPUTS:
        command.run(['docker','cp',str(runtime/name),host+':/app'])
    return verify_runtime_snapshot(runtime, host, directory, command, expected)


def integration(root, selected, directory, migration_script=None, product_enabled=False):
    """Activate the sealed generated roots, then reuse the installed maintained web tests."""
    from foundation_fixture import poll, PostgreSqlFixture
    import foundation_composition
    started = time.monotonic()
    baseline = bundle_hashes(root, selected)
    command = Commands(root, directory)
    config = foundation_composition.load_configuration(root)
    app = local_origin(config['application']['publicOrigin'])
    public_identity = local_origin(config['identity']['publicOrigin'])
    require(app.port != public_identity.port, 'PKF101 application and public identity listeners conflict')
    require(config['identity']['backchannelOrigin'] != config['identity']['publicOrigin'],
            'PKF101 disposable qualification must exercise the distinct issuer/private transport shape')
    postgres = selected['compositionId'].endswith('-postgresql')
    runtime = directory/'runtime'
    shutil.copytree(root/selected['runtimeStage'], runtime)
    # Docker cannot create a nested tmpfs target under a read-only feed mount.
    (runtime/'packages/.installed').mkdir(exist_ok=True)
    probe = directory/'probe'
    probe.mkdir()
    probe_started=time.monotonic()
    templates = root/'eng/foundation-qualification-support'
    require(templates.is_dir(), 'PKF101 maintained qualification support was not installed')
    for source in templates.iterdir():
        if source.is_file(): shutil.copy2(source, probe/source.name)
    metadata = foundation_composition.read(root/foundation_composition.CONTRACT)
    web_metadata = [setting for owner, _, setting in foundation_composition.rows(metadata)
                    if owner=='Orbyss.Foundation.Authentication' and setting['path'].startswith('Foundation:Web:')]
    require(web_metadata, 'PKF101 selected publisher has no actual authentication options metadata')
    write(probe/'settings.json', web_metadata)
    write(probe/'scopes.json',[scope for document in metadata['contracts'] for scope in document['metadata']['contracts'] if scope.get('settings')])
    feature = probe/'QualificationFeature.cs'
    feature.write_text(feature.read_text().replace('__DEPENDENCIES__', ', '.join('"'+p['featureIdentity']+'"' for p in selected['projects'])), encoding='utf-8')
    for source in (root/'eng/foundation-test-support').glob('*.cs'):
        shutil.copy2(source, probe/source.name)
    csproj = '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><IsPackable>true</IsPackable><PackageId>ProgramKit.Qualification.Probe</PackageId><AssemblyName>ProgramKit.Qualification.Probe</AssemblyName><Version>0.0.1</Version><GenerateDocumentationFile>true</GenerateDocumentationFile><TreatWarningsAsErrors>true</TreatWarningsAsErrors><FoundationFeatureIdentity>ProgramKit.Qualification.Probe</FoundationFeatureIdentity></PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App"/>'
    # Use the same selected package versions as the application, without inventing
    # independent Foundation pins or depending on unpublished source checkouts.
    from xml.etree.ElementTree import parse
    pins = {p.attrib['Include']:p.attrib['Version'] for props in [root/'Directory.Packages.props', *sorted((root/'eng').glob('ProgramKit.*.props'))]
            for p in parse(props).iter('PackageVersion')}
    for identity in ('CShells.Abstractions','CShells.AspNetCore.Abstractions','Orbyss.Foundation.Authentication','Orbyss.Foundation.Analyzers','Orbyss.Foundation.Build'):
        csproj += '<PackageReference Include="'+identity+'" Version="'+pins[identity]+'"'+(' PrivateAssets="all"' if identity!='Orbyss.Foundation.Authentication' else '')+' />'
    csproj += '<None Update="settings.json;scopes.json" CopyToOutputDirectory="PreserveNewest" Pack="true" PackagePath="lib/net10.0/" /></ItemGroup></Project>'
    (probe/'Probe.csproj').write_text(csproj, encoding='utf-8')
    # Disable inherited consumer pack/analyzer requirements for this maintained,
    # standalone test-only assembly; production source remains fully checked.
    environment = dict(os.environ, NUGET_PACKAGES=str(root/'artifacts/cache/nuget/packages'))
    command.run(['dotnet','restore',str(probe/'Probe.csproj'),'--configfile',str(root/'NuGet.config'),
                 '-p:ManagePackageVersionsCentrally=false','-p:ImportDirectoryBuildProps=false','-p:ImportDirectoryBuildTargets=false'], environment=environment)
    command.run(['dotnet','pack',str(probe/'Probe.csproj'),'--no-restore','-c','Release','-o',str(runtime/'packages'),
                 '-p:ManagePackageVersionsCentrally=false','-p:ImportDirectoryBuildProps=false','-p:ImportDirectoryBuildTargets=false'], environment=environment)
    probe_preparation=round(time.monotonic()-probe_started,3)
    suffix = uuid.uuid4().hex
    network, identity, host = ['pk-foundation-'+name+'-'+suffix for name in ('net','identity','host')]
    created = []
    database = None
    result = {'schemaVersion':1, 'status':'running', 'bundleInputs':baseline, 'cases':{}, 'timings':{'testSupportPreparationSeconds':probe_preparation},
              'productionProbeSelected':False, 'productAcceptance':False}
    try:
        command.run(['docker','network','create',network]); created.append(('network',network))
        if postgres:
            database_started=time.monotonic()
            database = PostgreSqlFixture(selected['serviceImages']['postgresql'], directory/'postgresql')
            database.start()
            command.secrets=(database.password,)
            database.command(['network','connect','--alias','foundation-postgresql',network,database.name])
            schema=root/'tests/foundation-product/schema.sql'
            if product_enabled and schema.is_file():
                # Explicit application-owned disposable deployment migration,
                # outside production Prepare and generic provider readiness.
                database.command(['cp',str(schema),database.name+':/tmp/product-schema.sql'])
                database.command(['exec',database.name,'psql','-U','fixture','-d','foundation_fixture','-v','ON_ERROR_STOP=1','-f','/tmp/product-schema.sql'])
            result['timings']['providerReadinessAndProductSchemaSeconds']=round(time.monotonic()-database_started,3)
        realm = read(root/'deploy/keycloak/program-kit-realm.json')
        require(realm['attributes']['programKitFixture'] == 'local-non-production-only', 'PKF101 non-synthetic realm cannot be provisioned')
        interactive=next(client for client in realm['clients'] if client['clientId']==config['identity']['clientId'])
        require(isinstance(interactive.get('secret'),str) and interactive['secret'],'PKF101 synthetic confidential client has no local fixture secret')
        command.secrets=(*command.secrets,interactive['secret'])
        write(directory/'realm.json',realm)
        # Copy the owned synthetic fixture into the stopped container. This
        # creates Keycloak's absent import directory and avoids host file-bind
        # transport failures; startup still owns the actual native realm import.
        import_directory = directory/'identity-import'
        import_directory.mkdir()
        import_file = import_directory/(config['identity']['realm']+'-realm.json')
        shutil.copy2(directory/'realm.json', import_file)
        private = urlsplit(config['identity']['backchannelOrigin'])
        require(private.scheme == 'http' and private.port == 8080 and private.hostname,
                'PKF101 fixture private backchannel must use its owned Docker alias port 8080')
        # Keycloak directory/startup imports require <realm-name>-realm.json.
        # The retained realm payload remains separate from the named import snapshot.
        command.run(['docker','create','--name',identity,'--pull=never','--network',network,'--network-alias',private.hostname,
                     '-p','127.0.0.1:'+str(public_identity.port)+':8080','-e','KC_HOSTNAME='+config['identity']['publicOrigin'],
                     '-e','KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true',
                     '--mount','type=bind,source='+str(root/'deploy/keycloak/themes')+',target=/opt/keycloak/themes,readonly',
                     selected['serviceImages']['keycloak'],'start-dev','--import-realm']); created.append(('container',identity))
        command.run(['docker','cp',str(import_directory),identity+':/opt/keycloak/data/import'])
        # Verify the stopped container received the exact fixture bytes, without
        # emitting credentials or depending on an image-specific checksum tool.
        observed_import = directory/'identity-import-observed'
        command.run(['docker','cp',identity+':/opt/keycloak/data/import',str(observed_import)])
        source_hash = hashlib.sha256(import_file.read_bytes()).hexdigest()
        observed_hash = hashlib.sha256((observed_import/import_file.name).read_bytes()).hexdigest()
        require(source_hash == observed_hash, 'PKF101 synthetic identity import copy changed')
        result['identityImport'] = {'sourceSha256':source_hash, 'containerCopySha256':observed_hash,
            'byteIdentityVerified':True, 'containerFilename':import_file.name,
            'transport':'Exact owned synthetic directory copied into the stopped owned container; native startup import follows'}
        command.run(['docker','start',identity])
        discovery_path = '/realms/'+config['identity']['realm']+'/.well-known/openid-configuration'
        result['timings']['identityReadinessSeconds'] = poll(lambda:ready(config['identity']['publicOrigin'],discovery_path),timeout=150)
        discovery = json.loads(request(config['identity']['publicOrigin'],discovery_path)[1])
        require(discovery['issuer'] == selected['targets']['publicAuthority'], 'PKF103 public issuer was reconstructed from private transport')
        result['cases'][CASES['keycloak'][0]] = True
        shells = read(runtime/'shells.json')
        shell = shells['CShells']['Shells']['default']
        shell['Features']['ProgramKit.Qualification.Probe'] = {}
        shell['Configuration']['Foundation']['Web']['RolePermissions'] = {'admin':['foundation.probe']}
        write(runtime/'shells.json',shells)
        args = ['docker','create','--name',host,'--pull=never','--network',network,
                '-e','ASPNETCORE_ENVIRONMENT=Development','-p','127.0.0.1:'+str(app.port)+':8080',
                '--tmpfs','/app/packages/.installed:rw,mode=1777']
        image = selected['hostImage']['reference'] if isinstance(selected['hostImage'],dict) else selected['hostImage']
        bff_key='CShells__Shells__default__Configuration__Foundation__Web__ClientSecret'
        args.extend(['--env',bff_key])
        host_environment=dict(os.environ,**{bff_key:interactive['secret']})
        if postgres:
            key='CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__application__ConnectionString'
            args.extend(['--env',key])
            host_environment[key]=database.connection().replace('Host=127.0.0.1','Host=foundation-postgresql').replace('Port='+str(database.port),'Port=5432')
        command.run([*args,image],environment=host_environment); created.append(('container',host))
        # Portable owned copies preserve exact activation across host filesystem
        # transports. The same transfer is reused for a recreated migration Host.
        transport = {'phase':'initial', 'before':copy_runtime_snapshot(runtime,host,directory/'runtime-initial-before',command)}
        result['runtimeTransport'] = [transport]
        command.run(['docker','start',host])
        result['timings']['hostReadinessSeconds'] = poll(lambda:ready(config['application']['publicOrigin'],'/bff/user'),timeout=150)
        ready(config['application']['publicOrigin'],'/__foundation/settings')
        bound = json.loads(request(config['application']['publicOrigin'],'/__foundation/settings')[1])
        require(bound['optionsInstance'] == 'activated IOptions<FoundationWebOptions>.Value', 'PKF104 effective view rebound configuration')
        observations = activated_settings(root,selected,config,bound)
        require(observations and any(row['path']=='Foundation:Web:ClientSecret' and row['value']=='<redacted>' for row in observations), 'PKF104 actual effective view omitted secret redaction')
        authority = next(row for row in observations if row['path']=='Foundation:Web:Authority')
        require(authority['value']==selected['targets']['publicAuthority'] and authority['sources'], 'PKF104 actual activated authority/provenance mismatch')
        bound['qualificationRuntimeShellsSha256']=hashlib.sha256((runtime/'shells.json').read_bytes()).hexdigest()
        write(directory/'effective-settings.runtime.json',bound)
        write(directory/'effective-settings.configured.json',foundation_composition.effective_settings(root))
        custom=read(root/'shells.json').get('CShells',{}).get('Shells',{}).get('default',{}).get('Configuration',{}).get('Foundation',{}).get('Web',{})
        if 'RemoteAuthenticationTimeoutSeconds' in custom:
            actual=next(row for row in observations if row['path']=='Foundation:Web:RemoteAuthenticationTimeoutSeconds')
            require(actual['value']==custom['RemoteAuthenticationTimeoutSeconds'],'PKF104 consumer operational override did not bind the activated options')
            require(any(row.get('providerOrdinal') is not None and row.get('path')==actual['path'] for row in actual['sources']),
                    'PKF104 consumer operational override has no actual winning configured provider provenance')
        result['cases'].update({case:True for case in CASES['host-activation']})
        engines = os.environ.get('PROGRAMKIT_BROWSER_ENGINES','chromium,webkit').split(',')
        browser_configuration = directory/'playwright.config.ts'
        browser_configuration.write_text("import { defineConfig } from '"+str(root/'eng/web/node_modules/@playwright/test').replace('\\','/')+"';\nexport default defineConfig({testDir:'"+str(root/'eng/web/tests').replace('\\','/')+"',outputDir:'"+str(directory/'playwright-results').replace('\\','/')+"',forbidOnly:true,retries:0,reporter:[['junit',{includeProjectInTestName:true,outputFile:'"+str(directory/'authentication.xml').replace('\\','/')+"'}]],use:{baseURL:'"+config['application']['publicOrigin']+"',trace:'off',video:'off',screenshot:'off'},projects:"+json.dumps([{'name':e,'use':{'browserName':e}} for e in engines])+"});\n",encoding='utf-8')
        environment = dict(os.environ, PROGRAMKIT_BASE_URL=config['application']['publicOrigin'],PROGRAMKIT_PERMISSION_PROBE_PATH='/api/permission-probe',
                           PROGRAMKIT_IDENTITY_AUTHORITY=selected['targets']['publicAuthority'])
        authentication_started=time.monotonic()
        command.run(playwright_command(root,['test','authentication.spec.ts','--config',str(browser_configuration)]),cwd=root/'eng/web',timeout=600,environment=environment)
        result['timings']['maintainedAuthenticationTestsSeconds']=round(time.monotonic()-authentication_started,3)
        from test_results import test_results
        auth_cases = test_results(directory/'authentication.xml','junit')
        require(auth_cases and all(auth_cases.values()), 'PKF104 maintained authentication cases skipped or failed')
        result['cases'][CASES['bff-cookie'][0]] = True
        product = root/'tests/foundation-product/qualification.mjs'
        operation={}
        def qualify_product():
            nonlocal operation
            require(product.is_file(), 'PKF105 explicit product proving requires an application-owned adapter')
            if product.is_file():
                # The application supplies only its operation assertions. Login,
                # fixtures, lifecycle and reporting remain maintained dependencies.
                environment['PROGRAMKIT_QUALIFICATION_OUTPUT'] = str(directory/'product-operation.json')
                environment['PROGRAMKIT_PRODUCT_ADAPTER'] = str(product)
                result['crawlerFollowingQualification'] = crawler_following_support(root, selected)
                environment['PROGRAMKIT_CRAWLER_FOLLOWING_QUALIFIED'] = 'true' if result['crawlerFollowingQualification']['supported'] else 'false'
                product_started=time.monotonic()
                command.run(['node',str(root/'eng/foundation-qualification-support/product_driver.mjs')],cwd=root/'eng/web',timeout=120,environment=environment)
                result['timings']['firstProductOperationWithSessionsSeconds']=round(time.monotonic()-product_started,3)
                operation = read(directory/'product-operation.json')
                require(operation.get('status')=='passed' and operation.get('ownedCreateRead') is True,
                        'PKF105 product adapter did not establish its real owned create/read operation')
                result['productAcceptance']=True
                result['timings']['integrationToFirstProductOperationSeconds']=round(time.monotonic()-started,3)
                if selected['runner']=='xunit-mtp':
                    from repository_architecture import validate_planned
                    graph=validate_planned(root,read(root/'eng/architecture.json'))
                    test_projects=sorted(path for path,row in graph.items() if row['role']=='test')
                    require(test_projects,'PKF105 native runner requires actual declared test ownership; empty selection establishes no acceptance')
                    journals=set((root/'artifacts/tests/runs').glob('*/result.json'))
                    focused=['python','eng/repository_verification.py','--repository','.', '--scope','Focused',
                             '--configuration','Release','--force','--native-report','xunit-trx',
                             '--reason','Actual generated composition HTTP ownership prerequisite']
                    for project_path in test_projects: focused.extend(['--project',project_path])
                    native_started=time.monotonic()
                    command.run(focused,environment=environment,timeout=600)
                    result['timings']['nativeApplicationTestsSeconds']=round(time.monotonic()-native_started,3)
                    created_journals=set((root/'artifacts/tests/runs').glob('*/result.json'))-journals
                    require(len(created_journals)==1,'PKF105 native Focused execution must retain one fresh scoped receipt')
                    journal=created_journals.pop(); native=read(journal)
                    require(native.get('status')=='completed' and set(native.get('projectsExecuted',[]))==set(test_projects),
                            'PKF105 native Focused evidence did not execute all selected owned projects')
                    outcomes=native.get('outcomes',[])
                    require(len(outcomes)==len(test_projects) and all(row.get('status')=='completed' and row.get('executedTests',0)>=1 for row in outcomes),
                            'PKF105 native selected tests produced no successful nonempty execution evidence')
                    for outcome in outcomes:
                        require(outcome.get('evidence'),'PKF105 native test evidence is missing')
                        require(outcome.get('nativeReport')=='xunit-trx' and outcome.get('nativeCases'),
                                'PKF105 native selected cases were empty, skipped or failed')
                        for relative,expected in outcome['evidence'].items():
                            retained=(root/relative).resolve()
                            require(retained.is_relative_to(journal.parent) and retained.is_file() and hashlib.sha256(retained.read_bytes()).hexdigest()==expected,
                                    'PKF105 retained native evidence missing, outside owned run or changed')
                    result['nativeTests']={'receipt':journal.relative_to(root).as_posix(),'projects':test_projects,
                        'outcomes':[{key:row[key] for key in ('project','executedTests','countKind','nativeReport','nativeCases','evidence')} for row in outcomes],
                        'countMeaning':'Actual selected native TRX cases; maintained wrapper rejects empty, failed and skipped results.'}
        if product_enabled:
            product_outcome(result,qualify_product)
        if migration_script:
            require(result['productAcceptance'], 'PKF107 migration requires a passed actual application proving phase')
            captured_profile=read(root/'.program-kit/managed.json').get('newProjectDependencyProfile')
            require(isinstance(captured_profile,dict) and all(captured_profile.get(key) for key in ('profile','entrySha256','catalogResolutionSha256')),
                    'PKF107 actual captured new-project dependency profile is missing')
            require((root/'eng/building-blocks.catalog.json').is_file() and
                    (not selected.get('developmentCandidate') or (root/'eng/foundation-development-candidate.json').is_file()),
                    'PKF107 actual captured catalogue/candidate profile sources are missing')
            preserved={path.relative_to(root).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [root/'shells.json',root/'docs/architecture/adoption-history.md',root/'.program-kit/dependency-profile.json',
                             root/'eng/building-blocks.catalog.json',root/'eng/foundation-development-candidate.json',
                             *root.glob('src/**/packages.lock.json'),*root.glob('tests/**/packages.lock.json')] if path.is_file()}
            profile=root/'eng/web-profile.shells.json'; original=profile.read_bytes()
            sync_command=['python',str(migration_script),'--target',str(root),'--profile-selected',
                          '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie','--json']
            profile.write_bytes(original+b'\n')
            try: command.run([*sync_command,'--check'],expected=2)
            finally: profile.write_bytes(original)
            command.run(sync_command)
            removed=None
            if selected['runner']=='xunit-mtp':
                changed=read(root/foundation_composition.INPUT)
                removed=changed['projects'].pop()
                changed['runtime']['rootPackages'].remove(removed['packageId'])
                write(root/foundation_composition.INPUT,changed)
                command.run(sync_command)
            selected=foundation_composition.resolve(root)
            transport['after'] = verify_runtime_snapshot(runtime,host,directory/'runtime-initial-after',command,transport['before']['sourceInputs'])
            command.run(['docker','rm','--force','--volumes',host]); created.remove(('container',host))
            migration_build=directory/'migration-build'; migration_build.mkdir()
            command.run(['python','eng/foundation_qualification.py','--repository','.',
                         '--run-directory',migration_build.relative_to(root).as_posix(),'--stage','build'],timeout=900)
            if removed:
                require(removed['featureIdentity'] not in selected['activations'] and
                        not any(path.name.startswith(removed['packageId']+'.') for path in (root/selected['runtimeStage']/'packages').glob('*.nupkg')),
                        'PKF107 removed independent feature escaped selected-root packaging')
            for relative,expected in preserved.items():
                require(hashlib.sha256((root/relative).read_bytes()).hexdigest()==expected,
                        'PKF107 reviewed adoption changed accepted consumer history/operational settings/native locks: '+relative)
            require(read(root/'.program-kit/managed.json').get('newProjectDependencyProfile')==captured_profile,
                    'PKF107 reviewed adoption changed the captured new-project dependency profile identity/hash')
            prior_runtime=(directory/'pre-migration-runtime').resolve()
            require(runtime.resolve().is_relative_to(directory) and prior_runtime.is_relative_to(directory) and not prior_runtime.exists(),
                    'PKF107 disposable runtime move must remain within its owned evidence directory')
            runtime.rename(prior_runtime)
            shutil.copytree(root/selected['runtimeStage'],runtime)
            (runtime/'packages/.installed').mkdir(exist_ok=True)
            # Recompile the maintained observer for the remaining selected
            # dependencies; an absent removed feature must not block activation.
            feature.write_text((templates/'QualificationFeature.cs').read_text().replace('__DEPENDENCIES__',
                ', '.join('"'+project['featureIdentity']+'"' for project in selected['projects'])),encoding='utf-8')
            command.run(['dotnet','pack',str(probe/'Probe.csproj'),'--no-restore','-c','Release','-o',str(runtime/'packages'),
                         '-p:ManagePackageVersionsCentrally=false','-p:ImportDirectoryBuildProps=false','-p:ImportDirectoryBuildTargets=false'],timeout=300)
            changed_shells=read(runtime/'shells.json')
            changed_shells['CShells']['Shells']['default']['Features']['ProgramKit.Qualification.Probe']={}
            changed_shells['CShells']['Shells']['default']['Configuration']['Foundation']['Web']['RolePermissions']={'admin':['foundation.probe']}
            write(runtime/'shells.json',changed_shells)
            command.run([*args,image],environment=host_environment); created.append(('container',host))
            transport = {'phase':'migration', 'before':copy_runtime_snapshot(runtime,host,directory/'runtime-migration-before',command)}
            result['runtimeTransport'].append(transport)
            command.run(['docker','start',host])
            poll(lambda:ready(config['application']['publicOrigin'],'/bff/user'),timeout=150)
            ready(config['application']['publicOrigin'],'/__foundation/settings')
            after=json.loads(request(config['application']['publicOrigin'],'/__foundation/settings')[1])
            activated_settings(root,selected,config,after)
            after['qualificationRuntimeShellsSha256']=hashlib.sha256((runtime/'shells.json').read_bytes()).hexdigest()
            write(directory/'effective-settings.after-migration.json',after)
            if 'RemoteAuthenticationTimeoutSeconds' in custom:
                require(next(row for row in after['settings'] if row['path']=='Foundation:Web:RemoteAuthenticationTimeoutSeconds')['value']==custom['RemoteAuthenticationTimeoutSeconds'],
                        'PKF107 retained operational override lost after actual repack/activation')
            baseline=bundle_hashes(root,selected)
            result['migration']={'status':'passed','preservedInputs':preserved,'liveConsumerMigration':False,
                'capturedDependencyProfile':{'source':'.program-kit/managed.json#newProjectDependencyProfile','value':captured_profile},
                'managedConflictRefused':True,'reviewedSameCandidateReconciliation':True,
                'removedIndependentFeature':removed['featureIdentity'] if removed else None,
                'postMigrationBundleInputs':baseline,'retainedProductAfterUpgrade':False,
                'installerEvidence':'Supplementary maintained installed toolkit upgrade/interruption tests; this case retains real product data through reviewed source sync and selected-root packaging.'}
        if database:
            database.restart()
            command.run(['docker','restart',host])
            poll(lambda:ready(config['application']['publicOrigin'],'/bff/user'),timeout=150)
            ready(config['application']['publicOrigin'],'/__foundation/settings')
            result['cases'][CASES['postgresql'][0]] = True
            if product_enabled and result['productAcceptance']:
                def retained_product():
                    environment['PROGRAMKIT_QUALIFICATION_OUTPUT']=str(directory/'product-retained-after-restart.json')
                    environment['PROGRAMKIT_RETAINED_RESOURCE_ID']=operation['resourceId']
                    command.run(['node',str(root/'eng/foundation-qualification-support/product_driver.mjs')],
                                cwd=root/'eng/web',timeout=120,environment=environment)
                    retained=read(directory/'product-retained-after-restart.json')
                    require(retained.get('retainedAfterRestart') is True,'PKF105 application owner resource lost after actual provider/host restart')
                    if migration_script: result['migration']['retainedProductAfterUpgrade']=True
                product_outcome(result,retained_product,phase='retained-product-after-provider-and-host-restart')
                if migration_script and not result['productAcceptance']: result['migration']['status']='failed'
        transport['after'] = verify_runtime_snapshot(runtime,host,directory/('runtime-'+transport['phase']+'-after'),command,transport['before']['sourceInputs'])
        require(bundle_hashes(root,selected)==baseline,'PKF105 test-only qualification modified production runtime bytes')
        result['status']='passed'
    except BaseException:
        result['status']='failed'
        for kind,name in created:
            if kind=='container':
                try: command.run(['docker','logs',name])
                except Exception: pass
        raise
    finally:
        errors=[]
        for kind,name in reversed(created):
            if kind=='network' and database:
                try: database.close()
                except Exception as error: errors.append(str(error))
                database=None
            try: command.run(['docker','rm','--force','--volumes',name] if kind=='container' else ['docker','network','rm',name])
            except Exception as error: errors.append(str(error))
        if database:
            try: database.close()
            except Exception as error: errors.append(str(error))
        result['cleanupComplete']=not errors
        if errors: result['status']='failed'
        result['elapsedSeconds']=round(time.monotonic()-started,3)
        write(directory/'product-acceptance.json',{'productAcceptance':result['productAcceptance'],
              'phase':result.get('productPhase',{'status':'not-requested'}),'platformStatus':result['status']})
        write(directory/'integration.json',result)
        require(not errors,'PKF105 owned fixture cleanup failed')
    return result


def check(root, selected, capability, directory):
    artifact = directory/'integration.json'
    require(capability in selected['tests']['capabilities'], 'PKF101 check does not belong to selected composition')
    if capability == 'host-activation':
        require(not artifact.exists(), 'PKF106 stale integration artifact cannot establish new readiness')
        result = integration(root,selected,directory,product_enabled=os.environ.get('PROGRAMKIT_QUALIFY_PRODUCT')=='1')
    else:
        require(artifact.is_file(), 'PKF106 actual activation must precede capability projection in this same run')
        result = read(artifact)
    require(result['status']=='passed' and result['cleanupComplete'] and result['bundleInputs']==bundle_hashes(root,selected),
            'PKF106 failed/changed/incomplete integration evidence cannot be reused')
    suite = ET.Element('testsuite',name='FoundationReadiness')
    for case in CASES[capability]:
        require(result['cases'].get(case) is True,'PKF106 actual selected integration case absent: '+case)
        classname,name=case.rsplit('.',1)
        ET.SubElement(suite,'testcase',classname=classname,name=name)
    ET.ElementTree(suite).write(directory/(capability+'.xml'),encoding='utf-8',xml_declaration=True)


def main():
    import foundation_composition
    from openapi_pipeline import repository_nuget_environment
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',default='.')
    parser.add_argument('--run-directory',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage',choices=('restore','build','services'))
    mode.add_argument('--check',choices=tuple(CASES))
    mode.add_argument('--migration',action='store_true',help='Explicit disposable product-data adoption qualification, distinct from readiness')
    parser.add_argument('--sync-script',help='Exact maintained sync entry point for explicit migration qualification')
    parser.add_argument('--product',action='store_true',help='Explicitly prove application assertions independently from platform readiness')
    args=parser.parse_args()
    if args.product: os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='1'
    root=Path(args.repository).resolve()
    directory=(root/args.run_directory).resolve()
    require(directory.is_relative_to(root/'artifacts/tests/runs'),'PKF101 qualification output must use normal consumer test evidence')
    require(directory.is_dir(),'PKF101 readiness coordinator must create a fresh run directory')
    # The maintained repository-isolation environment governs inline packaging,
    # architecture helpers and every descendant, not only the primary restore.
    isolated=repository_nuget_environment(root)
    os.environ.update(isolated)
    write(directory/'acquisition-isolation.json',{name:value for name,value in isolated.items()
          if value.startswith(str(root/'artifacts/cache'))})
    foundation_composition.verify_outputs(root)
    selected=foundation_composition.resolve(root)
    if args.stage: stage(root,selected,args.stage,directory)
    elif args.migration:
        require(args.sync_script and Path(args.sync_script).is_file(),'PKF101 migration requires an available maintained sync entry point')
        integration(root,selected,directory,Path(args.sync_script).resolve(),product_enabled=args.product)
    else: check(root,selected,args.check,directory)
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError) as error:
        print(str(error),file=sys.stderr); raise SystemExit(2)

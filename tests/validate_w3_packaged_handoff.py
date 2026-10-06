"""Explicit private W3 packaged/OCI READY acceptance; no Notes, startup or publication.

All native API export/pipeline receipts are produced by retained engineering. Historical
offline seam tests are separate; this command requires actual matching F6/tool/image inputs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files'
sys.path.insert(0,str(TEMPLATE/'eng'))
import handoff_contract as authority
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
from compatibility_process import run as bounded_run


def require(condition,message):
    if not condition:raise ValueError(message)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def resolve_cli_paths(args):
    """Bind explicit caller paths before any child changes its working directory."""
    for name in ('f6_result','published_tools_result','image_evidence','image_root',
                 'host_native_packages','dotnet','oasdiff','output'):
        path=getattr(args,name)
        require(isinstance(path,Path),'Explicit path argument is required: '+name)
        setattr(args,name,path.resolve())
    return args


def run(command,cwd,log,environment,timeout=600):
    # The maintained native supervisor owns suspended Windows children and their
    # descendants. Its environment is inherited from this single fixture process.
    previous=dict(os.environ)
    try:
        os.environ.clear();os.environ.update(environment)
        with log.open('w',encoding='utf-8') as output:
            code=bounded_run(command,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
    finally:
        os.environ.clear();os.environ.update(previous)
    # A normal supervisor return establishes Windows Job/handle termination even
    # for failure/timeout. POSIX signals the group and waits for the root only;
    # its descendant completion must not be represented as observed evidence.
    write(log.with_suffix('.process.json'),{'exitCode':code,'boundedTimeout':code==124,
          'cleanupPolicyApplied':True,'descendantCleanupObserved':os.name=='nt',
          'cleanupObservation':'windows-job-and-handles' if os.name=='nt' else 'posix-signal-and-root-wait',
          'supervisorSha256':authority.digest(Path(sys.modules['compatibility_process'].__file__))})
    require(code==0,'Native W3 command failed; retained log: '+str(log))


def native_output(command,cwd,log,environment):
    """Capture successful native text through the same owned, bounded supervisor."""
    run(command,cwd,log,environment)
    with log.open('rb') as stream:
        payload=authority.bounded_read(stream,authority.MAX_METADATA,'native observation log')
    return payload.decode('utf-8').strip()


def archives(directory,expected):
    actual={path.name:authority.digest(authority.contained(directory,path.name)) for path in directory.glob('*.nupkg')}
    require(actual==expected,'Exact retained package feed changed, is incomplete or has extra archives.')


def native_fixture_pins(path,observed,candidates,version):
    """Render this disposable fixture's selected observed pins as native literals."""
    tree=ET.parse(path);seen=set()
    for item in tree.iter('PackageVersion'):
        identity=item.get('Include');declared=item.get('Version');key=identity.casefold() if isinstance(identity,str) else ''
        require(key and key not in seen and identity in observed,'Missing/duplicate/unobserved native fixture pin.')
        seen.add(key)
        if declared=='[$(FoundationRuntimeVersion)]':
            require(identity in candidates and observed[identity]==version,'Runtime property pin is outside selected exact candidate family.')
            selected=version
        else:
            selected=declared[1:-1] if isinstance(declared,str) and declared.startswith('[') and declared.endswith(']') else declared
            require(isinstance(selected,str) and re.fullmatch(r'[0-9]+(?:\.[0-9]+){2,3}(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?',selected)
                    and selected==observed[identity],'Fixture pin differs from its actual qualified archive version.')
        item.set('Version',selected)
    require(seen,'Native fixture central pins are absent.')
    tree.write(path,encoding='utf-8',xml_declaration=False)


def selected_consumer_packages(feed,closure,candidates,version):
    """Select qualified API closure and exact Foundation roots, never the full F6 pool."""
    observed={};paths={};folded={}
    def admit(package,identity,native_version):
        key=identity.casefold()
        if key in folded:
            original=folded[key]
            require(original==identity and observed[original]==native_version
                    and authority.digest(paths[original])==authority.digest(package),
                    'Required consumer package identity/version/bytes conflict: '+identity)
            return
        folded[key]=identity;observed[identity]=native_version;paths[identity]=package
    closure_seen=set()
    for package in closure.glob('*.nupkg'):
        identity,native_version,_,_,_=authority.package_parts(package)
        require(identity.casefold() not in closure_seen,'Ambiguous qualified consumer package identity: '+identity)
        closure_seen.add(identity.casefold());admit(package,identity,native_version)
    candidates=list(candidates);expected={identity.casefold():identity for identity in candidates}
    require(len(expected)==len(candidates),'Duplicate exact Foundation candidate identity.')
    found=set()
    for package in feed.glob('*.nupkg'):
        identity,native_version,_,_,_=authority.package_parts(package);key=identity.casefold()
        if key not in expected:continue
        require(identity==expected[key] and key not in found and native_version==version,
                'Missing, wrong-version or ambiguous exact Foundation candidate: '+identity)
        found.add(key);admit(package,identity,native_version)
    require(found==set(expected),'Required exact Foundation candidate archive is missing.')
    return observed,paths


def host_compilation_packages(bindings,feed,host):
    """Admit the two proved Host contracts only as source compilation dependencies."""
    expected={'cshells.abstractions','cshells.aspnetcore.abstractions'};found={}
    require(isinstance(bindings,list) and len(bindings)==2,'Exact two native Host compilation bindings are required.')
    for row in bindings:
        package=authority.contained(feed,row['archive']);identity,version,_,_,assemblies=authority.package_parts(package)
        key=identity.casefold()
        require(key in expected and key not in found and row['identity']==key and row['version']==version
                and row['omittedRuntimeRoot'] is True and authority.digest(package)==row['archiveSha256']
                and row['assemblyPath']=='lib/net10.0/'+row['hostAssembly']
                and assemblies.get(row['hostAssembly'])==row['assemblySha256']
                and authority.digest(authority.contained(host.parent,row['hostAssembly']))==row['assemblySha256'],
                'Native Host compilation archive/version/DLL binding differs.')
        found[key]=(identity,version,package)
    require(set(found)==expected,'Native Host compilation binding is missing.')
    return list(found.values())


def closure_project(path,roots,observed):
    project=ET.Element('Project',{'Sdk':'Microsoft.NET.Sdk'});settings=ET.SubElement(project,'PropertyGroup')
    for name,value in {'TargetFramework':'net10.0','ManagePackageVersionsCentrally':'false',
                       'RestoreEnablePackagePruning':'false','RestorePackagesWithLockFile':'true',
                       'EnableDefaultCompileItems':'false','IsPackable':'false'}.items():ET.SubElement(settings,name).text=value
    items=ET.SubElement(project,'ItemGroup')
    for identity in sorted(roots):
        require(identity in observed,'Exact native closure root is missing: '+identity)
        ET.SubElement(items,'PackageReference',{'Include':identity,'Version':'['+observed[identity]+']'})
    path.parent.mkdir(parents=True);ET.ElementTree(project).write(path,encoding='utf-8',xml_declaration=True)


def retain_native_closure(assets_path,cache,roots,observed,selected,available,output):
    """Keep the actual unpruned native solver result, binding every selected cache archive."""
    assets=authority.read(assets_path);libraries=assets.get('libraries',{});admitted={};source_bytes={}
    require(isinstance(libraries,dict) and libraries,'Native selected closure assets are missing.')
    require({Path(path).resolve() for path in assets.get('packageFolders',{})}=={cache.resolve()},
            'Native closure escaped its owned cold package cache.')
    for directory in available:
        for package in directory.glob('*.nupkg'):
            identity,version,_,_,_=authority.package_parts(package);key=(identity.casefold(),version)
            digest=authority.digest(package)
            require(key not in source_bytes or source_bytes[key]==digest,'Available package identity/version has conflicting bytes.')
            source_bytes[key]=digest
    rows={}
    for key,library in libraries.items():
        require(library.get('type')=='package' and '/' in key,'Native closure bypasses packaged consumption.')
        identity,version=key.rsplit('/',1);folded=identity.casefold()
        require(folded not in admitted,'Native assets select an ambiguous package identity.')
        relative=authority.safe_name(library['path'])+'/'+identity.lower()+'.'+version.lower()+'.nupkg'
        package=authority.contained(cache,relative);native_id,native_version,_,_,_=authority.package_parts(package)
        require(native_id==identity and native_version==version and source_bytes.get((folded,version))==authority.digest(package),
                'Native selected archive differs from admitted input/cache/assets: '+key)
        if identity in roots:
            require(version==observed[identity] and authority.digest(package)==authority.digest(selected[identity]),
                    'Exact native root package version/bytes changed: '+identity)
        target=output/package.name
        require(not target.exists(),'Native selected archive basename is ambiguous.');shutil.copy2(package,target)
        admitted[folded]=identity;rows[identity]={'version':version,'archive':target.name,'sha256':authority.digest(target)}
    require(all(admitted.get(identity.casefold())==identity for identity in roots),'Native closure omits an exact consumer root.')
    return rows


def inputs(args):
    require(args.output and not args.output.exists(),'Select a NEW W3 evidence directory; accepted/failed evidence is immutable.')
    f6=authority.read(args.f6_result);path=args.f6_result.with_name('inputs.json');value=authority.read(path)
    require(f6.get('status')=='passed' and all(f6.get(k) is True for k in ('actualHost','actualNugetPackages','actualPostgreSql','twoShells','neutralHost','actualCustomProblemComposition')),
            'Actual matching packaged neutral Host/F6 acceptance is required.')
    version=value.get('version');require(isinstance(version,str) and '-contracts.' in version,'Select the explicit private development candidate.')
    require(f6.get('version')==version,'F6 version aliases differ.')
    feed=args.f6_result.parent/'feed';archives(feed,value['packages'])
    host=Path(value['executedHost']);require(host.is_file(),'Retained executed Host is missing.')
    for name,sha in value['hostRuntimeFiles'].items():
        require(authority.digest(authority.contained(host.parent,name))==sha,'Retained F6 Host payload changed: '+name)
    tools=authority.read(args.published_tools_result)
    require(tools.get('status')=='official-tools-compatible' and tools.get('runtimeSource')=='private'
            and tools.get('runtimeVersion')==version and tools.get('sdk')=='10.0.202'
            and all(tools.get('checks',{}).get(k) is True for k in ('officialBuild','coldComposition','typedJsonMetadataExported','producerMismatchRejected')),
            'Actual exact-candidate cold public-tool qualification is required.')
    tool_root=args.published_tools_result.parent;archives(tool_root/'closure',tools['stagedPackages'])
    selected_tools=tools.get('officialTools',[])
    require({(x.get('id'),x.get('version')) for x in selected_tools}=={('Orbyss.Foundation.Build','0.1.0'),('Orbyss.Foundation.OpenApi.Exporter','0.2.4')}
            and len(selected_tools)==2,'Exact two actual public-tool identities are required.')
    for name,sha in tools['fixture'].items():
        source=authority.contained(tool_root/'source',name)
        if name=='Api/feature.json':
            with zipfile.ZipFile(tool_root/'closure/PublishedTools.Contract.Api.1.0.0-fixture.1.nupkg') as packed:
                descriptor=authority.loads(packed.read('orbyss-foundation/feature.json').decode('utf-8'))
            current=authority.read(source)
            require(all(current[key]==descriptor[key] for key in ('packageId','schemaVersion','features','sourceSha256')),
                    'Generated native source/feature declaration differs from actual packed metadata.')
            for owning_path,expected in current['sourceSha256'].items():
                normalized=authority.contained(source.parent,owning_path).read_text(encoding='utf-8-sig').replace('\r\n','\n').replace('\r','\n').encode()
                require(hashlib.sha256(normalized).hexdigest()==expected,'Native feature source provenance changed.')
        else:require(authority.digest(source)==sha,'Retained actual API/Core fixture source changed.')
    for native in selected_tools:
        package=tool_root/'official-archives'/(native['id'].lower()+'.'+native['version']+'.nupkg')
        require(native['source']=='https://api.nuget.org/v3/index.json' and authority.digest(package)==native['sha256'],
                'Actual immutable official tool archive is missing or changed.')
    evidence=authority.read(args.image_evidence)
    require(args.image_root.is_dir() and args.host_native_packages.is_dir(),'Retained OCI/native archive roots are required.')
    return value,tools,evidence,feed,host,tool_root


def qualify(args):
    value,tools,evidence,feed,host,tool_root=inputs(args)
    work=args.output.resolve();work.mkdir(parents=True);consumer=work/'consumer';consumer.mkdir()
    version=value['version'];logs=work/'logs';logs.mkdir()
    environment=dict(os.environ,PYTHONUTF8='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',
                     MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_USE_MSBUILD_SERVER='0',GITHUB_SHA=hashlib.sha256(version.encode()).hexdigest()[:40],
                     DOTNET_ROOT=str(args.dotnet.resolve().parent))
    environment['PATH']=str(args.dotnet.resolve().parent)+os.pathsep+environment.get('PATH','')
    sdk=native_output([str(args.dotnet),'--version'],consumer,logs/'sdk.log',environment)
    require(sdk=='10.0.202','The exact pinned SDK202 is required for actual native W3 acceptance.')
    # Ordinary engineering/source only, with no installed toolkit or agent directories.
    for name in tools['fixture']:
        source=authority.contained(tool_root/'source',name);target=consumer/'src'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for name in ('Directory.Build.props','Directory.Build.targets','Directory.Packages.props','PublishedTools.slnx'):
        shutil.copy2(consumer/'src'/name,consumer/name)
        # The retained engineering entry points live at the consumer root; source
        # stays under src so native evidence observes every API/Core file.
        (consumer/'src'/name).unlink()
    solution=ET.parse(consumer/'PublishedTools.slnx')
    for item in solution.iter('Project'):
        relative=authority.safe_name(item.get('Path'))
        item.set('Path','src/'+relative)
    solution.write(consumer/'PublishedTools.slnx',encoding='utf-8',xml_declaration=False)
    shutil.copytree(TEMPLATE/'eng',consumer/'eng',ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('global.json','.nvmrc','.npm-version','.oasdiff-version'):shutil.copy2(TEMPLATE/name,consumer/name)
    # These are inert setup markers, removed before any native engineering command.
    for name in ('.program-kit','.specify','.agents'):(consumer/name).mkdir()
    for name in ('.program-kit','.specify','.agents'):
        target=(consumer/name).resolve();require(target.is_relative_to(consumer.resolve()),'Toolkit marker escaped owned consumer.');shutil.rmtree(target)
    require(not any((consumer/name).exists() for name in ('.program-kit','.specify','.agents')),'Toolkit removal failed.')
    captured_f6=consumer/'artifacts/retained-f6-inputs';captured_f6.mkdir(parents=True)
    for source in feed.glob('*.nupkg'):shutil.copy2(source,captured_f6/source.name)
    archives(captured_f6,value['packages'])
    source_feed=consumer/'artifacts/input-feed';source_feed.mkdir(parents=True)
    candidates=set(value['candidatePackageIdentities'])
    require(len(candidates)==29,'Native fixture requires the complete exact qualified Foundation runtime family.')
    observed,selected=selected_consumer_packages(feed,tool_root/'closure',candidates,version)
    for identity,native_version,package in host_compilation_packages(value['hostProvidedSharedPackages'],feed,host):
        require(identity not in observed,'Host compilation identity unexpectedly appears in deployment selection.')
        observed[identity]=native_version;selected[identity]=package
    for source in selected.values():shutil.copy2(source,source_feed/source.name)
    # Build tooling is retained separately from application deployment inputs.
    build_feed=work/'build-feed';build_feed.mkdir()
    for row in tools['officialTools']:
        if row['id']=='Orbyss.Foundation.Build':
            source=tool_root/'official-archives'/(row['id'].lower()+'.'+row['version']+'.nupkg');shutil.copy2(source,build_feed/source.name)
    for package in (tool_root/'runtime-cache').rglob('*.nupkg'):
        known=source_feed/package.name
        if known.exists():require(authority.digest(known)==authority.digest(package),'Retained native build cache differs from qualified deployment archive.')
        else:
            target=build_feed/package.name
            if target.exists():require(authority.digest(target)==authority.digest(package),'Retained native tooling cache has conflicting bytes.')
            else:shutil.copy2(package,target)
    for row in tools['officialTools']:observed[row['id']]=row['version']
    native_fixture_pins(consumer/'Directory.Packages.props',observed,candidates,version)
    # F6's own behavior fixture packages are input evidence, not this consumer's
    # deployment. Root selection is the actual Foundation family plus the actual
    # qualified API/Core closure; native staging resolves their required archives.
    deployment=consumer/'artifacts/deployment-archives';deployment.mkdir()
    deployment_ids=candidates|{'PublishedTools.Contract.Api','PublishedTools.Contract.Core'}
    configuration=ET.Element('configuration');sources=ET.SubElement(configuration,'packageSources');ET.SubElement(sources,'clear')
    for key,directory in [('inputs',source_feed),('qualified-f6-archives',captured_f6),('build',build_feed)]:
        ET.SubElement(sources,'add',{'key':key,'value':str(directory)})
    ET.ElementTree(configuration).write(consumer/'NuGet.config',encoding='utf-8',xml_declaration=True)
    (consumer/'VERSION').write_text('1.0.0-fixture.1\n',encoding='utf-8')
    settings_source=consumer/'src/SettingsExporter';shutil.copytree(ROOT/'tests/fixtures/application-handoff-native-w3',settings_source)
    cache=work/'native-cache';environment.update(NUGET_PACKAGES=str(cache),DOTNET_CLI_HOME=str(work/'dotnet-home'))
    properties=['-p:FoundationRuntimeVersion='+version]
    for project in (consumer/'PublishedTools.slnx',settings_source/'SettingsExporter.csproj'):
        run([str(args.dotnet),'restore',str(project),'--configfile',str(consumer/'NuGet.config'),'--force-evaluate',*properties],consumer,logs/(project.stem+'-restore.log'),environment)
        run([str(args.dotnet),'restore',str(project),'--configfile',str(consumer/'NuGet.config'),'--locked-mode',*properties],consumer,logs/(project.stem+'-locked-restore.log'),environment)
        run([str(args.dotnet),'build',str(project),'-c','Release','--no-restore',*properties],consumer,logs/(project.stem+'-build.log'),environment)
    # This is a fresh ordinary pack after toolkit removal. Retain its outputs
    # separately; the independently qualified input archives remain immutable.
    native_pack=work/'native-packed';native_pack.mkdir()
    run([str(args.dotnet),'pack',str(consumer/'PublishedTools.slnx'),'-c','Release','--no-build','--no-restore',
         '--output',str(native_pack),*properties],consumer,logs/'native-pack.log',environment)
    packed_ids={authority.package_parts(path)[0] for path in native_pack.glob('*.nupkg')}
    require(packed_ids=={'PublishedTools.Contract.Api','PublishedTools.Contract.Core'},'Fresh native pack did not produce both actual fixture components.')
    native_project=consumer/'artifacts/native-root-selection/RuntimeClosure.csproj'
    closure_project(native_project,deployment_ids,observed)
    closure_command=[str(args.dotnet),'restore',str(native_project),'--configfile',str(consumer/'NuGet.config'),*properties]
    run([*closure_command,'--force-evaluate'],consumer,logs/'native-runtime-closure-restore.log',environment)
    run([*closure_command,'--locked-mode'],consumer,logs/'native-runtime-closure-locked-restore.log',environment)
    native_closure=retain_native_closure(native_project.parent/'obj/project.assets.json',cache,deployment_ids,
        observed,selected,(source_feed,captured_f6,build_feed),deployment)
    settings_dll=settings_source/'bin/Release/net10.0/SettingsExporter.dll'
    run([str(args.dotnet),str(settings_dll),'self-test'],consumer,logs/'application-settings-test.log',environment)
    metadata=native_output([str(args.dotnet),str(settings_dll),'metadata',str(settings_source/'Program.cs')],
                           consumer,logs/'application-settings-metadata.log',environment)
    write(consumer/'contracts/application-settings.json',authority.loads(metadata))
    api_directory=tool_root/'official-exporter'
    shells=authority.read(api_directory/'shells.json')
    # The retained native shell composer uses the preferred direct-object spelling.
    for shell in shells['CShells']['Shells'].values():
        shell['Features']={key:{} if configured is True else configured for key,configured in shell['Features'].items()}
    write(consumer/'shells.json',shells);write(consumer/'hostsettings.json',authority.read(api_directory/'hostsettings.json'))
    write(consumer/'nuplane.settings.json',{'Nuplane':{'Setup':{'Feeds':[]},'Loading':{'Enabled':True}}})
    run([sys.executable,str(consumer/'eng/release_bundle.py'),'stage','--repository',str(consumer),'--packages',str(deployment),
         '--output',str(consumer/'artifacts/release-bundle')],consumer,logs/'native-stage.log',environment)
    refs=['contracts/application-settings.json'];package_ids=[]
    for package in (consumer/'artifacts/release-bundle/packages').glob('*.nupkg'):
        identity,native_version,_,payload,_=authority.package_parts(package);package_ids.append(identity)
        if payload is None:continue
        envelope=authority.loads(payload.decode('utf-8-sig'))
        for contract in envelope['contracts']:
            name='contracts/settings/'+identity+'/'+contract['scope']+'.json';authority.safe_name(name)
            write(consumer/name,{'schemaVersion':envelope['schemaVersion'],'kind':'foundation-package','packageId':identity,
                  'packageVersion':native_version,'packageSha256':authority.digest(package),'scope':contract['scope']});refs.append(name)
    # Copy OCI blobs by their retained names, with image digest preserved and paths owned by this consumer.
    captured=consumer/'contracts/image';captured.mkdir(parents=True)
    prepared=json.loads(json.dumps(evidence))
    for row in [prepared['manifest'],prepared['config']]+([prepared['index']] if 'index' in prepared else [])+prepared['layers']:
        source=authority.contained(args.image_root,row['path']);target=captured/row['sha256'];shutil.copy2(source,target)
        require(authority.digest(target)==row['sha256'],'Retained OCI bytes changed before receiver preparation.')
        row['path']=target.relative_to(consumer).as_posix()
    prepared['nativePackages']=[]
    native_dir=consumer/'contracts/image/native';native_dir.mkdir()
    native_archives=list(args.host_native_packages.glob('*.nupkg'))
    require(1<=len(native_archives)<=64 and sum(p.stat().st_size for p in native_archives)<=1024**3,
            'Captured native archive count/aggregate bytes exceed finite admission.')
    for package in native_archives:
        authority.contained(args.host_native_packages,package.name)
        identity,native_version,_,_,_=authority.package_parts(package);target=native_dir/package.name;shutil.copy2(package,target)
        prepared['nativePackages'].append({'packageId':identity,'packageVersion':native_version,'path':target.relative_to(consumer).as_posix(),'sha256':authority.digest(target)})
    image_path=consumer/'contracts/image/evidence.json';write(image_path,prepared)
    # Admit actual image/source/archive binding before constructing handoff declarations.
    image,_=authority.image_metadata(prepared,prepared['hostImageReference'],lambda name:authority.contained(consumer,name).open('rb'),{})
    require(image['packageVersion']==version and image['assembly']['sha256']==value['host']['sha256'],'Actual image does not contain exact F6 candidate Host.')
    for contract in image['contracts']:
        name='contracts/settings/Host/'+contract['scope']+'.json'
        write(consumer/name,{'schemaVersion':2,'kind':'foundation-host-image','scope':contract['scope'],
              'evidencePath':image_path.relative_to(consumer).as_posix(),'evidenceSha256':authority.digest(image_path)});refs.append(name)
    doc=consumer/'docs/application.md';doc.parent.mkdir();doc.write_text('Private metadata conformance specimen: source-backed typed application defaults, actual cold API export, compiled Foundation package scopes and exact Host integration/image authority. Storage and hosted-service poison sentinels prove metadata-only export. This is not a production rollout or a public availability claim.\n',encoding='utf-8')
    runtime=consumer/'docs/runtime.md';runtime.write_text('Requires the selected Foundation Host and packaged runtime closure. Receivers supply valid secret references and choose deployment/storage/identity policy; metadata export starts none. The fixture settings utility is a pure typed code-construction scope.\n',encoding='utf-8')
    client=consumer/'client';client.mkdir()
    (client/'generate.cjs').write_text("const fs=require('node:fs');const d=JSON.parse(fs.readFileSync('../contracts/api.json','utf8'));if(!d.components?.schemas)throw Error('Missing wire schema');fs.writeFileSync('contract.cjs','module.exports='+JSON.stringify(d.components.schemas)+';\\n');",encoding='utf-8')
    (client/'accept.cjs').write_text("const a=require('node:assert/strict');const schemas=require('./contract.cjs');a.ok(Object.values(schemas).some(x=>x.properties?.values));a.ok(Object.keys(schemas).length>1);a.equal(typeof JSON.stringify({text:'bounded specimen'}),'string');",encoding='utf-8')
    write(client/'package.json',{'name':'w3-contract-client','version':'1.0.0','private':True,'scripts':{'generate':'node generate.cjs','build':'node --check contract.cjs && node accept.cjs'}})
    write(client/'package-lock.json',{'name':'w3-contract-client','version':'1.0.0','lockfileVersion':3,'requires':True,'packages':{'':{'name':'w3-contract-client','version':'1.0.0'}}})
    write(client/'tsconfig.json',{'allowJs':True,'checkJs':False,'files':['contract.cjs'],'noEmit':True})
    stage={'directory':'client','packageJson':'client/package.json','lockFile':'client/package-lock.json'}
    native=authority.read(api_directory/'contract.json')
    contract={**native,'packageClosure':'artifacts/release-bundle/packages','rawDocument':'contracts/raw.json','artifact':'contracts/api.json','baseline':'contracts/baseline.json',
              'compatibility':{'oasdiffVersion':(consumer/'.oasdiff-version').read_text().strip().removeprefix('v'),'approval':'contracts/approval.json'},
              'generator':{**stage,'script':'generate','generatedTypes':'client/contract.cjs'},'application':{**stage,'script':'build','tsconfig':'client/tsconfig.json'}}
    write(consumer/'eng/api.contract.json',contract);write(consumer/'eng/openapi-contracts.json',{'schemaVersion':1,'contracts':['eng/api.contract.json']})
    write(consumer/'eng/application-handoff.json',{'schemaVersion':1,'applicationId':'w3.native.specimen','bundleDescriptor':'artifacts/application-bundle.json',
          'openapiRegistry':'eng/openapi-contracts.json','components':[{'id':'conformance','packages':sorted(package_ids),'contracts':[native['identity']]}],
          'requiredSettingsScopes':{'PublishedTools.Contract.Api':['application-settings']},'categories':{
              'documentation':{'status':'included','reason':'Delivered private conformance purpose.','files':['docs/application.md']},
              'runtime':{'status':'included','reason':'Actual specimen requirements and cold scope.','files':['docs/runtime.md']},
              'settings':{'status':'included','reason':'Actual owning producers; exact package/image authority.','files':refs},
              'assets':{'status':'included','reason':'Actual generated JavaScript schema client.','files':['client/contract.cjs','client/accept.cjs']},
              'migrations':{'status':'not-applicable','reason':'This metadata specimen does not initialize or own a database.','files':[]}}})
    require(args.oasdiff.is_file(),'Reviewed exact pinned oasdiff binary is required before actual native pipeline.')
    oasdiff=consumer/'artifacts/tools/oasdiff'/(consumer/'.oasdiff-version').read_text().strip().removeprefix('v')
    oasdiff.mkdir(parents=True);shutil.copy2(args.oasdiff,oasdiff/('oasdiff.exe' if os.name=='nt' else 'oasdiff'))
    exporter_root=tool_root/'official-tool-cache/orbyss.foundation.openapi.exporter/0.2.4/tools'
    exporter=list(exporter_root.rglob('Orbyss.Foundation.OpenApi.Exporter.dll'))
    require(len(exporter)==1,'Actual restored official exporter implementation is ambiguous or missing.')
    public_exporter=tool_root/'official-archives/orbyss.foundation.openapi.exporter.0.2.4.nupkg'
    with zipfile.ZipFile(public_exporter) as published:
        for name in published.namelist():
            if name.startswith('tools/') and not name.endswith('/'):
                actual=authority.contained(exporter_root.parent,name)
                with published.open(name) as captured:
                    expected=authority.stream_sha256(captured,authority.MAX_ASSEMBLY,name)
                require(authority.digest(actual)==expected,'Installed official exporter payload differs from immutable public archive: '+name)
    run([sys.executable,str(consumer/'eng/openapi_pipeline.py'),'--repository',str(consumer),'--exporter',str(exporter[0]),'--initialize-baselines'],
        consumer,logs/'native-api-pipeline.log',environment)
    pipeline=authority.read(consumer/'artifacts/program-kit/openapi/pipeline.json')
    require(pipeline['satisfied'] is True,'Actual native pipeline did not satisfy API output.')
    export=authority.read(consumer/'artifacts/program-kit/openapi'/ (native['identity']+'-export.json'))
    require(all(export.get('sideEffects',{}).get(key) is False for key in ('listenerStarted','consumerHostedServicesStarted','shellInitializersRun')),
            'Metadata-only export initialized runtime behavior.')
    run([sys.executable,str(consumer/'eng/release_bundle.py'),'describe','--repository',str(consumer),'--staged',str(consumer/'artifacts/release-bundle'),
         '--image','ghcr.io/orbyss-io/foundation-host','--tag','private-'+version,'--digest',prepared['hostImageReference'].split('@')[1],
         '--output',str(consumer/'artifacts/application-bundle.json')],consumer,logs/'native-describe.log',environment)
    run([sys.executable,str(consumer/'eng/application_handoff.py'),'--repository',str(consumer)],consumer,logs/'native-handoff.log',environment)
    index=authority.read(consumer/'artifacts/handoff/index.json');require(index['status']=='ready' and index['schemaVersion']==2,'Native current handoff is not READY2.')
    receiver=work/'receiver';receiver.mkdir();archive=consumer/'artifacts/handoff/application-handoff.zip';shutil.copy2(archive,receiver/archive.name)
    with zipfile.ZipFile(archive) as captured:
        for name in ('verify_handoff.py','handoff_contract.py'):(receiver/name).write_bytes(captured.read(name))
    run([sys.executable,'-I',str(receiver/'verify_handoff.py'),str(receiver/archive.name)],receiver,logs/'independent-receiver.log',environment)
    archives(feed,value['packages']);archives(captured_f6,value['packages']);archives(tool_root/'closure',tools['stagedPackages'])
    write(work/'result.json',{'schemaVersion':1,'status':'passed','runtimeVersion':version,'publicAvailabilityEstablished':False,
          'actualPackagedSettings':True,'actualImageAuthority':True,'nativeEngineeringAfterToolkitRemoval':True,'actualColdApiPipeline':True,
          'independentReadyReceiver':True,'applicationInitialized':False,'NotesRun':False,'paidWorkersStarted':False,
          'f6ResultSha256':authority.digest(args.f6_result),'publishedToolsResultSha256':authority.digest(args.published_tools_result),
          'imageEvidenceSha256':authority.digest(args.image_evidence),'hostImageReference':prepared['hostImageReference'],
          'receiverArchiveSha256':authority.digest(archive),'hostScopes':sorted(c['scope'] for c in image['contracts']),
          'nativePackedArchives':{p.name:authority.digest(p) for p in native_pack.glob('*.nupkg')},
          'nativeCentralPinsSha256':authority.digest(consumer/'Directory.Packages.props'),
          'retainedF6InputPackages':value['packages'],'nativeSelectedClosure':native_closure,
          'actualDeploymentPackageIdentities':sorted(package_ids),
          'settingsAuthorityCount':len(index['settingsAuthorities']),'logs':{p.name:authority.digest(p) for p in logs.iterdir()}})
    print('Actual private W3 READY receiver qualification passed: '+str(work))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--f6-result',type=Path,required=True);parser.add_argument('--published-tools-result',type=Path,required=True)
    parser.add_argument('--image-evidence',type=Path,required=True);parser.add_argument('--image-root',type=Path,required=True)
    parser.add_argument('--host-native-packages',type=Path,required=True);parser.add_argument('--dotnet',type=Path,required=True)
    parser.add_argument('--oasdiff',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=resolve_cli_paths(parser.parse_args())
    try:qualify(args);return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())

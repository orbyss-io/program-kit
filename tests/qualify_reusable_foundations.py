"""Fresh disposable qualification of generated compositions; no live consumers are modified.

Cold means fresh consumer NuGet/npm acquisition caches and isolated browser
downloads. Preinstalled SDK and immutable Docker images are reported explicitly,
never described as a cold machine. Prepared runs reuse the consumer's caches.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'extensions/program-kit-dotnet/scripts'
sys.path.insert(0,str(SCRIPTS))
import foundation_composition as composition
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
from compatibility_process import run


def contract_tests():
    """Failure-contract tests of maintained orchestration; these claim no runtime readiness."""
    import importlib.util
    import http.server
    import threading
    path=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/foundation_qualification.py'
    spec=importlib.util.spec_from_file_location('qualification_contract_test',path)
    adapter=importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    evidence=ROOT/'artifacts/tests/reusable-foundations'/('contracts-'+uuid.uuid4().hex[:16])
    evidence.mkdir(parents=True)
    checks=[]
    def rejected(name,action):
        try: action()
        except ValueError: checks.append(name); return
        raise AssertionError('Invalid readiness evidence admitted: '+name)
    for variant in sorted(composition.VARIANTS):
        selected=adapter.setup_contract({'compositionId':variant})
        expected={'host-activation','bff-cookie','keycloak'} | ({'postgresql'} if variant.endswith('postgresql') else set())
        assert set(selected['tests']['capabilities'])==expected
        assert {row['stage'] for row in selected['setup']['steps']}=={'restore','build','services'}
        assert all(row['result']['cases']==adapter.CASES[row['capability']] for row in selected['tests']['commands'])
    checks.append('finite-supported-compositions-use-authoritative-nonempty-maintained-cases')
    platform={'status':'passed','cases':{case:True for values in adapter.CASES.values() for case in values},'productAcceptance':False}
    def failing_product(): raise ValueError('Expected application assertion failure')
    adapter.product_outcome(platform,failing_product)
    assert platform['status']=='passed' and all(platform['cases'].values()) and platform['productAcceptance'] is False
    assert platform['productPhase']['failure']=='application-proving-failed'
    checks.append('application-failure-remains-visible-without-erasing-platform-cases')
    platform['productAcceptance']=True
    adapter.product_outcome(platform,failing_product,phase='retained-product-after-provider-and-host-restart')
    assert platform['status']=='passed' and all(platform['cases'].values()) and platform['productAcceptance'] is False
    assert platform['productPhase']['phase']=='retained-product-after-provider-and-host-restart'
    checks.append('retained-application-failure-does-not-erase-platform-restart')
    rejected('live-origin-executable-refused',lambda:adapter.local_origin('https://live.example'))
    rejected('selected-configurable-owner-unobserved-refused',lambda:adapter.activated_settings(evidence,
             {'tests':{'capabilities':['host-activation']}},{},{'owners':[]}))
    root=evidence/'consumer'; directory=root/'artifacts/tests/runs/current'; directory.mkdir(parents=True)
    bundle=root/'artifacts/runtime'; bundle.mkdir(); (bundle/'shells.json').write_text('{}')
    selected={'runtimeStage':'artifacts/runtime','tests':{'capabilities':['bff-cookie']}}
    rejected('no-activation-evidence-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result={'status':'failed','cleanupComplete':True,'bundleInputs':adapter.bundle_hashes(root,selected),'cases':{adapter.CASES['bff-cookie'][0]:True}}
    write(directory/'integration.json',result)
    rejected('failed-evidence-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['status']='passed'; result['cleanupComplete']=False; write(directory/'integration.json',result)
    rejected('incomplete-cleanup-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['cleanupComplete']=True; result['bundleInputs']={}; write(directory/'integration.json',result)
    rejected('changed-staged-inputs-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['bundleInputs']=adapter.bundle_hashes(root,selected); result['cases']={}; write(directory/'integration.json',result)
    rejected('missing-actual-case-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'local helper contract')
        def log_message(self,*_): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever); thread.start()
    try: assert adapter.request('http://127.0.0.1:'+str(server.server_port),'/')[0]==200
    finally: server.shutdown(); server.server_close(); thread.join()
    checks.append('native-http-readiness-client-works-and-closes')
    cache_home=evidence/'cache-inventory-fixture'
    for platform,expected in (('win32',cache_home/'AppData/Local/ms-playwright'),
                              ('linux',cache_home/'.cache/ms-playwright'),
                              ('darwin',cache_home/'Library/Caches/ms-playwright')):
        observed=browser_cache_inventory(environment={},platform=platform,home=cache_home)
        assert observed['cachePath']==str(expected) and not observed['directoryExists']
        assert observed['observedDirectories']==[] and observed['browserReadinessEstablished'] is False
    explicit=cache_home/'explicit'; (explicit/'chromium-fixture').mkdir(parents=True)
    (explicit/'marker.txt').write_text('a file is not an installed browser')
    observed=browser_cache_inventory(environment={'PLAYWRIGHT_BROWSERS_PATH':str(explicit)},platform='linux',home=cache_home)
    assert observed['cacheSource']=='PLAYWRIGHT_BROWSERS_PATH' and observed['observedDirectories']==['chromium-fixture']
    assert observed['browserReadinessEstablished'] is False
    for platform,key in (('win32','LOCALAPPDATA'),('linux','XDG_CACHE_HOME')):
        observed=browser_cache_inventory(environment={key:str(cache_home/'override')},platform=platform,home=cache_home)
        assert observed['cachePath']==str(cache_home/'override/ms-playwright')
    observed=browser_cache_inventory(environment={'PLAYWRIGHT_BROWSERS_PATH':'0'},platform='linux',home=cache_home)
    assert observed['cachePath'] is None and not observed['directoryExists'] and not observed['browserReadinessEstablished']
    checks.append('portable-preexisting-browser-cache-inventory-never-claims-readiness')
    write(evidence/'qualification.json',{'status':'passed','checks':checks,'runtimeAcceptanceEstablished':False})
    print('Maintained qualification failure contracts passed: '+str(evidence))
    return 0


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def browser_cache_inventory(*, environment=None, platform=None, home=None):
    """Observe cache directories portably; this never establishes browser readiness."""
    environment = os.environ if environment is None else environment
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    declared = environment.get('PLAYWRIGHT_BROWSERS_PATH')
    if declared == '0':
        cache = None  # Package-local caches depend on the installed Playwright module.
        source = 'package-local; no shared cache selected'
    elif declared:
        cache = Path(declared).expanduser().resolve()
        source = 'PLAYWRIGHT_BROWSERS_PATH'
    elif platform == 'win32':
        cache = Path(environment.get('LOCALAPPDATA') or home/'AppData/Local')/'ms-playwright'
        source = 'Windows ambient cache'
    elif platform == 'darwin':
        cache = home/'Library/Caches/ms-playwright'
        source = 'macOS ambient cache'
    else:
        cache = Path(environment.get('XDG_CACHE_HOME') or home/'.cache')/'ms-playwright'
        source = 'Linux ambient cache'
    exists = cache is not None and cache.is_dir()
    directories = sorted(path.name for path in cache.iterdir() if path.is_dir()) if exists else []
    return {'platform':platform, 'cacheSource':source, 'cachePath':str(cache) if cache is not None else None,
            'directoryExists':exists, 'observedDirectories':directories,
            'browserReadinessEstablished':False,
            'scope':'Pre-setup directory inventory only; installed executables and usability require actual browser checks.'}


def command(args, root, evidence, *, timeout=1800):
    evidence.mkdir(parents=True)
    with (evidence/'stdout.log').open('wb') as out,(evidence/'stderr.log').open('wb') as err:
        code=run(args,root,out,err,timeout)
    write(evidence/'result.json',{'exitCode':code,'command':args})
    if code:
        raise ValueError('Qualification command failed; inspect '+str(evidence))


def candidate(root, feed):
    import dependency_profile
    # Build candidate only from the explicit base already selected by Program Kit.
    resolver=dependency_profile.resolver()
    effective=resolver.effective_dependency_context(root)
    rows={}
    for package in ('Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication.BffCookie'):
        archives=list(feed.glob(package+'.*.nupkg'))
        if len(archives)!=1: raise ValueError('Explicit candidate feed must contain one exact package: '+package)
        archive=archives[0]
        destination=root/'eng/development-packages'/archive.name
        destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(archive,destination)
        import zipfile
        with zipfile.ZipFile(archive) as packed:
            metadata=json.loads(packed.read('orbyss-foundation/settings.json'))
        rows[package]={'path':destination.relative_to(root).as_posix(),'version':metadata['packageVersion'],
                       'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    profile=root/'eng/foundation-development-candidate.json'
    write(profile,{'id':'reusable-foundations-development','baseProfile':effective['profile'],'status':'development-candidate','packages':rows})
    return {'profile':profile.relative_to(root).as_posix(),'sha256':hashlib.sha256(profile.read_bytes()).hexdigest()}


def sync(root, evidence, *, check=False, expected=0):
    args=[sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
          '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie','--json']
    if check: args.append('--check')
    if expected==0: command(args,ROOT,evidence)
    else:
        evidence.mkdir(parents=True)
        with (evidence/'stdout.log').open('wb') as out,(evidence/'stderr.log').open('wb') as err:
            code=run(args,ROOT,out,err,300)
        if code!=expected: raise ValueError('Expected reviewed sync status '+str(expected)+'; inspect '+str(evidence))
        write(evidence/'result.json',{'exitCode':code,'expected':expected})


def scaffold(root, shape, feed, evidence):
    postgres=shape!='base'
    variant='foundation-bff-keycloak'+('-postgresql' if postgres else '')
    config=composition.read(ROOT/'extensions/program-kit-dotnet/templates/dotnet/compositions'/(variant+'.json'))
    config['runner']='xunit-mtp' if shape=='sport' else 'executable'
    config['runtime']['directory']='runtime/nested/persoonlijk' if shape=='sport' else '.'
    if shape=='sport':
        config['identity']['publicOrigin']='http://localhost:18080'
        config['identity']['realm']='sport-qualification'
        extra={'path':'src/Nieuws/Feed.Api/Feed.Api.csproj','packageId':'Feed.Api','featureIdentity':'Feed.Api','role':'implementation'}
        config['projects'].append(extra); config['runtime']['rootPackages'].append(extra['packageId'])
    root.mkdir(parents=True)
    write(root/composition.INPUT,config)
    sync(root,evidence/'initial-sync')
    if feed:
        config['developmentCandidate']=candidate(root,feed)
        write(root/composition.INPUT,config)
        sync(root,evidence/'candidate-sync')
    # Product sources and native tests are application-owned. All fixture/service
    # lifecycle, authentication, reporting and settings capture come from tooling.
    if postgres:
        first=root/config['projects'][0]['path']
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/OwnedResourceFeature.cs',first.parent/'ApiFeature.cs')
        core=root/'src/Product.Core'; core.mkdir(parents=True)
        (core/'Product.Core.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><IsPackable>true</IsPackable><PackageId>Product.Core</PackageId></PropertyGroup></Project>',encoding='utf-8')
        for name in ('IOwnedResources.cs','ResourceOwner.cs','CreateResourceOutcome.cs'):
            shutil.copy2(ROOT/'tests/fixtures/reusable-foundations'/name,core/name)
        project=first.read_text(encoding='utf-8').replace('</Project>',
            '<ItemGroup><ProjectReference Include="../Product.Core/Product.Core.csproj" /></ItemGroup></Project>')
        first.write_text(project,encoding='utf-8')
        provider=root/config['projects'][1]['path']
        provider.write_text(provider.read_text().replace('</Project>','<ItemGroup><ProjectReference Include="../Product.Core/Product.Core.csproj" /></ItemGroup></Project>'),encoding='utf-8')
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/OwnedResources.cs',provider.parent/'OwnedResources.cs')
        feature=provider.parent/'ProviderFeature.cs'
        feature.write_text(feature.read_text().replace('services.AddFoundationPostgreSql',
            'services.AddSingleton<Product.Core.IOwnedResources, OwnedResources>();\n        services.AddFoundationPostgreSql'),encoding='utf-8')
        dependencies=first.read_text().replace('Orbyss.Foundation.Authentication;Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication;Orbyss.Foundation.WebDefaults;Application.PostgreSql')
        first.write_text(dependencies,encoding='utf-8')
        product=root/'tests/foundation-product/qualification.mjs'; product.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/qualification.mjs',product)
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/schema.sql',product.parent/'schema.sql')
    projects=[p['path'] for p in config['projects']]
    if postgres: projects.append('src/Product.Core/Product.Core.csproj')
    if shape=='sport':
        tests=root/'tests/Product/Product.Tests.csproj'; tests.parent.mkdir(parents=True)
        tests.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><IsTestProject>true</IsTestProject><IsPackable>false</IsPackable><UseMicrosoftTestingPlatformRunner>true</UseMicrosoftTestingPlatformRunner></PropertyGroup><ItemGroup><PackageReference Include="xunit.v3.mtp-v2" /></ItemGroup></Project>',encoding='utf-8')
        (tests.parent/'ProductBoundaryTests.cs').write_text('''namespace Qualification.Product;
/// <summary>Native product security assertion against the activated selected host.</summary>
public sealed class ProductBoundaryTests
{
    /// <summary>The browser resource route challenges anonymously without disclosing the resource.</summary>
    [Xunit.Fact]
    public async System.Threading.Tasks.Task AnonymousResourceReadChallengesWithoutDisclosure()
    {
        using var handler = new System.Net.Http.HttpClientHandler { AllowAutoRedirect = false };
        using var client = new System.Net.Http.HttpClient(handler)
        {
            BaseAddress = new System.Uri(System.Environment.GetEnvironmentVariable("PROGRAMKIT_BASE_URL")
                ?? throw new System.InvalidOperationException("Actual host URL required"))
        };
        const string resourcePath = "/resources/fc78aeb7-529f-4906-a9a5-8db4ff8a6ead";
        using var response = await client.GetAsync(resourcePath, Xunit.TestContext.Current.CancellationToken);
        // The selected BFF contract returns401 for /api; this browser route challenges locally.
        Xunit.Assert.Equal(System.Net.HttpStatusCode.Found, response.StatusCode);
        var location = response.Headers.Location;
        Xunit.Assert.NotNull(location);
        var target = new System.Uri(client.BaseAddress, location);
        Xunit.Assert.Equal(client.BaseAddress.GetLeftPart(System.UriPartial.Authority), target.GetLeftPart(System.UriPartial.Authority));
        Xunit.Assert.Equal("/bff/login", target.AbsolutePath);
        Xunit.Assert.Equal("?ReturnUrl=" + System.Uri.EscapeDataString(resourcePath), target.Query);
        Xunit.Assert.Empty(await response.Content.ReadAsStringAsync(Xunit.TestContext.Current.CancellationToken));
    }
}
''',encoding='utf-8')
        packages=root/'Directory.Packages.props'
        test_pins=json.loads((root/'eng/foundation-test-support/packages.json').read_text())
        packages.write_text(packages.read_text().replace('</Project>','<ItemGroup><PackageVersion Include="xunit.v3.mtp-v2" Version="'+test_pins['xunit.v3.mtp-v2']+'" /></ItemGroup></Project>'),encoding='utf-8')
        projects.append(tests.relative_to(root).as_posix())
    (root/'Application.slnx').write_text('<Solution>\n'+''.join('<Project Path="'+p+'" />\n' for p in projects)+'</Solution>\n',encoding='utf-8')
    (root/'VERSION').write_text('0.0.1-development\n' if feed else '0.0.1\n',encoding='utf-8')
    architecture=composition.read(root/'eng/architecture.json')
    if postgres:
        for item in architecture['runtimeComposition']['projects']:
            if item['path'] in (config['projects'][0]['path'],config['projects'][1]['path']):
                item['projectReferences']=['src/Product.Core/Product.Core.csproj']
        architecture['runtimeComposition']['projects'].append({'path':'src/Product.Core/Product.Core.csproj','role':'core','projectReferences':[],
            'responsibilities':[{'name':'Product.Core.IOwnedResources','kind':'contract','effects':[]}]})
        architecture['runtimeComposition']['bindings']=[{'capabilityProject':'src/Product.Core/Product.Core.csproj',
            'implementationProject':config['projects'][1]['path'],'capability':'Product.Core.IOwnedResources',
            'implementation':'Application.PostgreSql.OwnedResources','registration':'Application.PostgreSql.ProviderFeature.ConfigureServices'}]
    if shape=='sport':
        architecture['runtimeComposition']['projects'].append({'path':'tests/Product/Product.Tests.csproj','role':'test','projectReferences':[],
            'responsibilities':[{'name':'ProductBoundaryTests','kind':'test','effects':['Actual HTTP owner-read authentication prerequisite']}]})
    write(root/'eng/architecture.json',architecture)
    # Preserve synthetic accepted history/customization and locks through reviewed sync.
    (root/'docs/architecture/adoption-history.md').write_text('Disposable accepted architecture history. No live consumer adoption.\n',encoding='utf-8')
    if postgres:
        shells=composition.read(root/'shells.json')
        shells['CShells']['Shells']['default'].setdefault('Configuration',{}).setdefault('Foundation',{}).setdefault('Web',{})['RemoteAuthenticationTimeoutSeconds']=11
        write(root/'shells.json',shells)
    sync(root,evidence/'rerun-sync')
    return config


def qualify(root, shape, phase, evidence, generation):
    os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='0' if shape=='base' else '1'
    if phase=='cold' and any(path.is_file() and path.name!='.gitignore' for path in (root/'artifacts/cache').rglob('*')):
        raise ValueError('Cold qualification requires a new consumer and acquisition cache')
    started=time.monotonic()
    command([sys.executable,'eng/foundation_setup.py','--repository','.','--execute'],root,evidence/'readiness')
    runs=sorted((root/'artifacts/tests/runs').glob('foundation-*/result.json'),key=lambda p:p.stat().st_mtime)
    native=json.loads(runs[-1].read_text())
    if native['status']!='ready': raise ValueError('Generated composition failed actual readiness')
    integration=json.loads((runs[-1].parent/'integration.json').read_text())
    if shape!='base' and integration.get('productAcceptance') is not True:
        raise ValueError('First actual authenticated owner operation not established')
    timings={'generationSeconds':round(generation,3), **{row['stage']+'Seconds':row['elapsedSeconds'] for row in native['steps']},
             **{key:value for key,value in json.loads((runs[-1].parent/'restore-timings.json').read_text()).items() if key!='elapsedSeconds'},
             **integration['timings'], 'readinessTotalSeconds':round(time.monotonic()-started,3),
             'generationToFirstOperationUpperBoundSeconds':round(generation+time.monotonic()-started,3) if shape!='base' else None}
    if shape!='base':
        timings['generationToFirstWorkingProductOperationSeconds']=round(generation + sum(row['elapsedSeconds'] for row in native['steps'] if row['stage'] in ('restore','build','services')) + integration['timings']['integrationToFirstProductOperationSeconds'],3)
    result={'shape':shape,'phase':phase,'status':'passed','coldDefinition':'Fresh isolated NuGet/npm caches and browser downloads; preinstalled SDK/Docker images disclosed separately' if phase=='cold' else 'Same consumer acquired dependency/browser caches',
            'newConsumerAuthoredGenericHarnessLines':0,'remainingGenericSetupTasks':0,'timings':timings,
            'readinessArtifact':str(runs[-1].relative_to(ROOT)), 'productionBundle':composition.resolve(root)['runtimeStage']}
    write(evidence/'result.json',result)
    return result


def migrate(root, config, evidence):
    """Real product data stays alive across the maintained reviewed adoption path."""
    owned_orphans={}
    if config['runner']=='xunit-mtp':
        independent=root/config['projects'][-1]['path']
        text=independent.read_text()
        if '<Description>Consumer-owned Sport news feed</Description>' not in text:
            independent.write_text(text.replace('<IsPackable>true</IsPackable>',
                '<IsPackable>true</IsPackable>\n    <Description>Consumer-owned Sport news feed</Description>'),encoding='utf-8')
        source=independent.parent/'ApiFeature.cs'
        if 'ConsumerFeedName' not in source.read_text():
            source.write_text(source.read_text().replace('public sealed class ApiFeature : IWebShellFeature\n{',
                'public sealed class ApiFeature : IWebShellFeature\n{\n    /// <summary>Consumer-owned independent feed identity.</summary>\n    public const string ConsumerFeedName = "Sport news";'),encoding='utf-8')
        owned_orphans={path.relative_to(root).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in (independent,source)}
        write(evidence/'consumer-owned-orphan-inputs.before.json',{'beforeFeatureRemoval':True,'files':owned_orphans})
    directory=root/'artifacts/tests/runs'/('migration-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    command([sys.executable,'eng/foundation_qualification.py','--repository','.','--run-directory',directory.relative_to(root).as_posix(),
             '--migration','--product','--sync-script',str(SCRIPTS/'dotnet_sync.py')],root,evidence/'actual-product-migration')
    result=json.loads((directory/'integration.json').read_text())
    if result['status']!='passed' or not result.get('migration',{}).get('retainedProductAfterUpgrade'):
        raise ValueError('Actual consumer product data did not survive reviewed migration')
    if owned_orphans:
        assert all((root/path).is_file() and hashlib.sha256((root/path).read_bytes()).hexdigest()==expected for path,expected in owned_orphans.items())
        removed=config['projects'][-1]['packageId']
        assert result['migration']['removedIndependentFeature']==config['projects'][-1]['featureIdentity']
        built=list((root/'artifacts/packages').rglob(removed+'.*.nupkg'))
        assert built and not list((root/composition.resolve(root)['runtimeStage']/'packages').glob(removed+'.*.nupkg'))
        result['migration']['preservedConsumerOwnedOrphanInputs']=owned_orphans
        result['migration']['orphanBuiltPackage']={'path':str(max(built,key=lambda p:p.stat().st_mtime).relative_to(root)),
            'excludedFromSelectedRuntime':True}
    write(evidence/'result.json',result['migration'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shape',choices=('base','notes','sport','all'),default='all')
    parser.add_argument('--candidate-feed',type=Path)
    parser.add_argument('--prepared',action='store_true',help='Measure a second acquired-cache run in the same consumer')
    parser.add_argument('--contract-tests',action='store_true',help='Bounded failure-contract checks; starts no external service or package restore')
    parser.add_argument('--engines',default='chromium,webkit',help='Actual maintained browser engines; CI includes Firefox')
    parser.add_argument('--functional-consumer',type=Path,help='Reuse a preserved disposable bundle/cache for functional repairs; establishes no cold timing or readiness receipt')
    parser.add_argument('--migration-consumer',type=Path,help='Resume actual retained-data migration on a preserved disposable consumer; establishes no new timing claim')
    parser.add_argument('--default-readiness',action='store_true',help='With a preserved consumer, run actual default foundation setup without application proving')
    parser.add_argument('--product-failure',nargs='?',const='initial',choices=('initial','retained'),help='With an owned functional consumer, retain real platform success beside an intentionally failed application assertion')
    args=parser.parse_args()
    if args.contract_tests: return contract_tests()
    engines=args.engines.split(',')
    if not engines or not set(engines)<={'chromium','webkit','firefox'}: parser.error('Unsupported browser engine selection')
    os.environ['PROGRAMKIT_BROWSER_ENGINES']=args.engines
    if args.migration_consumer:
        root=args.migration_consumer.resolve()
        if not root.is_relative_to(ROOT/'artifacts/tests/reusable-foundations') or not (root/composition.INPUT).is_file():
            parser.error('Migration must target an owned disposable qualification consumer')
        artifact=ROOT/'artifacts/tests/reusable-foundations'/('migration-repair-'+uuid.uuid4().hex[:16]); artifact.mkdir()
        config=composition.read(root/composition.INPUT)
        if config['runner']=='xunit-mtp' and not any(row['packageId']=='Feed.Api' for row in config['projects']):
            config['projects'].append({'path':'src/Nieuws/Feed.Api/Feed.Api.csproj','packageId':'Feed.Api','featureIdentity':'Feed.Api','role':'implementation'})
            config['runtime']['rootPackages'].append('Feed.Api')
            write(root/composition.INPUT,config)
        sync(root,artifact/'synchronize-reviewed-ownership-repair')
        directory=root/'artifacts/tests/runs'/('migration-preparation-'+uuid.uuid4().hex); directory.mkdir()
        command([sys.executable,'eng/foundation_qualification.py','--repository','.',
            '--run-directory',directory.relative_to(root).as_posix(),'--stage','build'],root,artifact/'prepare-selected-initial-bundle')
        migrate(root,config,artifact/'migration')
        write(artifact/'qualification.json',{'status':'migration-passed','consumer':str(root.relative_to(ROOT)),
              'newColdTimingClaim':False,'actualMigration':str((artifact/'migration/result.json').relative_to(ROOT))})
        print('Actual repaired consumer migration: '+str(artifact))
        return 0
    if args.functional_consumer:
        root=args.functional_consumer.resolve()
        if not root.is_relative_to(ROOT/'artifacts/tests/reusable-foundations') or not (root/composition.INPUT).is_file():
            parser.error('Functional consumer must be a preserved owned disposable qualification consumer')
        artifact=ROOT/'artifacts/tests/reusable-foundations'/('functional-'+uuid.uuid4().hex[:16])
        artifact.mkdir(parents=True)
        sync(root,artifact/'synchronize-repaired-test-support')
        if args.default_readiness:
            if args.product_failure: parser.error('Default readiness and application failure proving are separate modes')
            product=root/'tests/foundation-product/qualification.mjs'
            if not product.is_file(): parser.error('Default independence proof requires an existing owned application adapter')
            before=set((root/'artifacts/tests/runs').glob('*/result.json'))
            os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='0'
            observer=artifact/'command-observer'; observer.mkdir()
            audit=artifact/'command-audit'; audit.mkdir()
            (observer/'sitecustomize.py').write_text('''import json, os, uuid
from pathlib import Path
import foundation_fixture
_original = foundation_fixture.captured
def _observed(command, cwd, directory, **keywords):
    safe = [str(token) for token in command]
    for value in keywords.get('secret_values', ()):
        if value:
            safe = [token.replace(value, '[REDACTED]') for token in safe]
    destination = Path(os.environ['PROGRAMKIT_COMMAND_AUDIT']) / (uuid.uuid4().hex + '.json')
    destination.write_text(json.dumps({'command':safe, 'cwd':str(cwd)}, indent=2), encoding='utf-8')
    return _original(command, cwd, directory, **keywords)
foundation_fixture.captured = _observed
''',encoding='utf-8')
            previous={name:os.environ.get(name) for name in ('PYTHONPATH','PROGRAMKIT_COMMAND_AUDIT')}
            os.environ['PYTHONPATH']=os.pathsep.join((str(observer),str(root/'eng'),previous['PYTHONPATH'] or ''))
            os.environ['PROGRAMKIT_COMMAND_AUDIT']=str(audit)
            try:
                command([sys.executable,'eng/foundation_setup.py','--repository','.', '--execute'],root,artifact/'default-setup')
            finally:
                for name,value in previous.items():
                    if value is None: os.environ.pop(name,None)
                    else: os.environ[name]=value
            added=set((root/'artifacts/tests/runs').glob('*/result.json'))-before
            receipts=[path for path in added if json.loads(path.read_text()).get('kind')=='foundation-readiness']
            if len(receipts)!=1: raise ValueError('Default readiness must retain one actual maintained setup receipt')
            receipt=receipts[0]; observed=json.loads(receipt.read_text()); directory=receipt.parent
            integration=json.loads((directory/'integration.json').read_text())
            product_result=json.loads((directory/'product-acceptance.json').read_text())
            assert observed['status']=='ready' and integration['status']=='passed' and all(integration['cases'].values())
            assert product_result['phase']['status']=='not-requested' and integration['productAcceptance'] is False
            assert 'productPhases' not in integration and 'product' not in integration and 'nativeTests' not in integration
            assert 'firstProductOperationWithSessionsSeconds' not in integration['timings']
            assert 'nativeApplicationTestsSeconds' not in integration['timings']
            assert not any(json.loads(path.read_text()).get('scope')=='Focused' for path in added)
            assert not any((directory/name).exists() for name in ('product-operation.json','product-retained-after-restart.json'))
            recorded=[json.loads(path.read_text()) for path in audit.glob('*.json')]
            assert len(recorded)>20 and any(row['command'][:2]==['docker','run'] for row in recorded)
            assert any(any('playwright' in token for token in row['command']) and 'test' in row['command'] for row in recorded)
            schema_requested=any(any('product-schema.sql' in token or 'foundation-product/schema.sql' in token for token in row['command']) for row in recorded)
            driver_executed=any(any('product_driver.mjs' in token for token in row['command']) for row in recorded)
            native_executed=any(any('repository_verification.py' in token for token in row['command']) and 'Focused' in row['command'] for row in recorded)
            assert not schema_requested and not driver_executed and not native_executed
            write(artifact/'default-readiness.json',{'status':'passed','productAdapterPresent':True,
                'productOptIn':False,'actualPlatformCases':integration['cases'],'productAcceptance':False,
                'productPhase':product_result['phase'],'nativeApplicationRunCreated':native_executed,
                'productDriverOutputCreated':driver_executed,'applicationSchemaDeploymentRequested':schema_requested,
                'actualObservedCommandCount':len(recorded),
                'commandAuditScope':'Test-only Python startup observer of maintained foundation_fixture.captured across owned descendants. Redacted argv and owned cwd only; delegates original command, arguments and supervision unchanged.',
                'commandAudit':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in audit.glob('*.json')},
                'actualReadiness':str(receipt.relative_to(ROOT)),
                'adapterSha256':hashlib.sha256((root/'eng/foundation_qualification.py').read_bytes()).hexdigest()})
            print('Actual default setup independence: '+str(artifact))
            return 0
        directory=root/'artifacts/tests/runs'/('functional-'+uuid.uuid4().hex); directory.mkdir(parents=True)
        product=root/'tests/foundation-product/qualification.mjs'
        original=product.read_bytes() if product.is_file() else None
        os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='1' if original is not None else '0'
        if args.product_failure:
            if original is None: parser.error('Real failed-product qualification requires the owned product fixture')
            if args.product_failure=='initial':
                product.write_text('export async function qualify() { throw new Error("Expected owned application assertion failure"); }\n',encoding='utf-8')
            else:
                needle='  if (process.env.PROGRAMKIT_RETAINED_RESOURCE_ID) {'
                text=original.decode('utf-8')
                if needle not in text: parser.error('Retained-product failure requires the exact owned fixture seam')
                product.write_text(text.replace(needle,needle+'\n    throw new Error("Expected owned retained-product assertion failure");'),encoding='utf-8')
        try:
            command([sys.executable,'eng/foundation_qualification.py','--repository','.',
                     '--run-directory',directory.relative_to(root).as_posix(),'--check','host-activation'],root,artifact/'integration')
            if args.product_failure:
                result=json.loads((directory/'integration.json').read_text())
                if result['status']!='passed' or result['productAcceptance'] is not False or result['productPhase'].get('failure')!='application-proving-failed' or not all(result['cases'].values()):
                    raise ValueError('Actual failed product erased platform proof or concealed application failure')
                write(artifact/'expected-product-failure.json',{'platformStatus':result['status'],'actualPlatformCases':result['cases'],
                     'productAcceptance':False,'productFailure':result['productPhase'],'actualIntegration':str(directory.relative_to(ROOT))})
        finally:
            if args.product_failure and original is not None: product.write_bytes(original)
        write(artifact/'qualification.json',{'status':'functional-checks-passed','actualIntegration':str(directory.relative_to(ROOT)),
              'coldTimingEstablished':False,'foundationReadinessReceiptEstablished':False})
        print('Functional prepared integration: '+str(artifact))
        return 0
    if args.default_readiness: parser.error('Default readiness requires a preserved owned consumer')
    artifact=ROOT/'artifacts/tests/reusable-foundations'/uuid.uuid4().hex[:16]
    artifact.mkdir(parents=True)
    write(artifact/'status.json',{'status':'running'})
    results=[]
    try:
        # Inventory is measured before setup, not retroactively classified.
        for name,args_inventory in [('images',['docker','image','ls','--digests']),('sdk',['dotnet','--list-sdks'])]:
            command(args_inventory,ROOT,artifact/('preexisting-'+name),timeout=30)
        write(artifact/'preexisting-browser-cache/inventory.json',browser_cache_inventory())
        for shape in (('base','notes','sport') if args.shape=='all' else (args.shape,)):
            root=artifact/shape/'consumer'
            start=time.monotonic()
            config=scaffold(root,shape,args.candidate_feed,artifact/shape/'generation')
            generation=time.monotonic()-start
            results.append(qualify(root,shape,'cold',artifact/shape/'cold',generation))
            if args.prepared: results.append(qualify(root,shape,'prepared',artifact/shape/'prepared',0))
            if shape!='base': migrate(root,config,artifact/shape/'migration')
        write(artifact/'qualification.json',{'status':'passed','results':results,
             'publicationQualified':False,'adoption':'Explicit disposable-only development qualification; live Notes/Sport unchanged'})
        write(artifact/'status.json',{'status':'passed'})
    except BaseException as error:
        write(artifact/'status.json',{'status':'failed','failure':str(error),'completed':results})
        print('Retained failed qualification: '+str(artifact),file=sys.stderr)
        raise
    print('Reusable foundations qualification: '+str(artifact))
    return 0


if __name__=='__main__': raise SystemExit(main())

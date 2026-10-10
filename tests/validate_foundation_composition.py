"""Exercise real managed sync and selected public package consumption for finite compositions."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import shutil

ARTIFACT = None
COMMAND_NUMBER = 0

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-dotnet/scripts'
sys.path.insert(0, str(SCRIPTS))
import foundation_composition as composition


def run(command, cwd, expected=0, timeout=240):
    global COMMAND_NUMBER
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if ARTIFACT:
        COMMAND_NUMBER += 1
        stem = ARTIFACT / ('command-'+str(COMMAND_NUMBER))
        stem.with_suffix('.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        stem.with_suffix('.json').write_text(json.dumps({'command':command, 'exitCode':result.returncode, 'expected':expected}), encoding='utf-8')
    if result.returncode != expected:
        if ARTIFACT and Path(cwd) != ROOT:
            retained = ARTIFACT / ('failed-command-'+str(COMMAND_NUMBER))
            shutil.copytree(cwd,retained,ignore=shutil.ignore_patterns('bin','obj','__pycache__','artifacts'))
            normal_evidence = Path(cwd)/'artifacts/program-kit'
            if normal_evidence.is_dir(): shutil.copytree(normal_evidence,retained/'artifacts/program-kit')
            packages = Path(cwd)/'artifacts/packages'
            if packages.is_dir(): shutil.copytree(packages,retained/'artifacts/packages')
        raise AssertionError(str(command) + '\n' + result.stdout + result.stderr)
    return result


def sync(root, check=False, expected=0):
    args = [sys.executable, str(SCRIPTS/'dotnet_sync.py'), '--target', str(root), '--profile-selected',
            '--foundation-host-accepted', '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
    if check: args.append('--check')
    result = run(args, ROOT, expected)
    if not result.stdout.lstrip().startswith('{'):
        raise AssertionError('Sync did not emit a reconciliation plan: '+result.stderr)
    return json.loads(result.stdout.split('committed reconciliation transaction:')[0])


def rejected(value, mutate):
    altered = copy.deepcopy(value); mutate(altered)
    try: composition.validate_configuration(altered)
    except ValueError: return
    raise AssertionError('Invalid composition was accepted')


def retirement_checks(root, value):
    # Leave the independent optional package-build fixture untouched.
    with tempfile.TemporaryDirectory(prefix='program-kit-retirement-') as temporary:
        isolated = Path(temporary)
        shutil.copytree(root, isolated, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('artifacts','bin','obj','__pycache__'))
        _retirement_checks(isolated, value)


def _retirement_checks(root, value):
    """Exercise source ownership through actual feature selection and reconciliation."""
    selected = copy.deepcopy(value)
    extras = [{'path':f'src/Retirement.{kind}/Retirement.{kind}.csproj',
               'packageId':f'Retirement.{kind}', 'featureIdentity':f'Retirement.{kind}',
               'role':'implementation'} for kind in ('Both','SourceOnly','ProjectOnly','AddedSource','Untouched')]
    selected['projects'].extend(extras)
    selected['runtime']['rootPackages'].extend(p['packageId'] for p in extras)
    (root/composition.INPUT).write_bytes(composition.encoded(selected)); sync(root)
    custom = [root/extras[0]['path'], root/'src/Retirement.Both/ApiFeature.cs',
              root/'src/Retirement.SourceOnly/ApiFeature.cs', root/extras[2]['path']]
    retained = {path for project in extras[:4]
                for path in (project['path'], str(Path(project['path']).parent/'ApiFeature.cs').replace('\\','/'))}
    original_state = composition.read(root/'.program-kit/managed.json')
    for path in custom:
        path.write_bytes(path.read_bytes()+b'\n<!-- consumer edit -->\n' if path.suffix=='.csproj'
                         else path.read_bytes()+b'\n// consumer edit\n')
    added_source = 'src/Retirement.AddedSource/OwnedCode.cs'
    (root/added_source).write_bytes(b'namespace Retirement.AddedSource; public sealed class OwnedCode {}\n')
    custom_bytes = {p.relative_to(root).as_posix():p.read_bytes() for p in custom}
    retained_bytes = {path:(root/path).read_bytes() for path in retained | {added_source}}
    sync(root)
    customized_state = composition.read(root/'.program-kit/managed.json')
    for path in custom_bytes:
        # Preserving source does not authenticate a consumer's new bytes.
        assert customized_state['files'][path] == original_state['files'][path]
    assert added_source not in original_state['files'] and added_source not in customized_state['files']
    (root/composition.INPUT).write_bytes(composition.encoded(value))
    preview = sync(root, True, 1)
    assert retained <= set(preview['preserved'])
    assert not preview['conflicts']
    assert not any(a['path'] in retained for a in preview['actions'])
    assert all((root/path).read_bytes()==content for path,content in custom_bytes.items())
    sync(root)
    released = composition.read(root/'.program-kit/managed.json')
    assert all(path not in released['files'] for path in retained)
    assert all((root/path).read_bytes()==content for path,content in retained_bytes.items())
    assert added_source not in released['files']
    assert not (root/extras[4]['path']).exists()
    assert not (root/'src/Retirement.Untouched/ApiFeature.cs').exists()
    resolved = composition.read(root/composition.RESOLVED)
    graph = composition.read(root/'eng/architecture.json')['runtimeComposition']
    features = composition.read(root/'eng/web-profile.shells.json')['CShells']['Shells']['default']['Features']
    for project in extras:
        assert project['packageId'] not in resolved['rootPackages']
        assert (project['path'] in {p['path'] for p in graph['projects']}) == (project in extras[:4])
        assert project['featureIdentity'] not in features
    sync(root, True)
    import importlib.util
    sys.path.insert(0, str(root/'eng'))
    try:
        spec = importlib.util.spec_from_file_location('retirement_architecture', root/'eng/repository_architecture.py')
        architecture_checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(architecture_checker)
        architecture_checker.validate_planned(root, composition.read(root/'eng/architecture.json'))
    finally:
        sys.path.remove(str(root/'eng'))
    physical = {p.relative_to(root).as_posix() for p in (root/'src').rglob('*.csproj')}
    assert physical <= {p['path'] for p in graph['projects']}
    # A second apply cannot silently forget the released source classification.
    sync(root); sync(root, True)
    assert composition.read(root/'eng/architecture.json')['runtimeComposition']['projects'] == graph['projects']
    assert all((root/path).read_bytes()==content for path,content in retained_bytes.items())
    if ARTIFACT:
        (ARTIFACT/(value['compositionId']+'-retirement.json')).write_bytes(composition.encoded({
            'preservedSourceHashes':{path:composition.digest(content) for path,content in retained_bytes.items()},
            'sourceRoles':graph['projects'], 'selectedRoots':resolved['rootPackages'],
            'releasedStateEntries':sorted(retained), 'untouchedProjectRemoved':True,
            'addedConsumerSourceNeverGoverned':added_source,
            'plannedArchitectureValidated':True,'physicalProjectsClassified':True}))

    # Counterexamples enter the same real retirement loop: neither a managed or
    # configuration source nor unrelated/engineering scaffolds get this exception.
    state_path = root/'.program-kit/managed.json'; original = state_path.read_bytes()
    producer = '../../scripts/foundation_composition.py'
    controls = [('eng/retired-managed.cs','managed','foundation',producer),
                ('eng/retired-configuration.cs','configuration','foundation',producer),
                ('eng/retired-architecture.json','scaffold','foundation',producer),
                ('src/OtherContribution.cs','scaffold','base',producer),
                ('src/OtherProducer.csproj','scaffold','foundation','files/other.csproj'),
                ('src/UnknownProducer.cs','scaffold','foundation',None)]
    state = composition.read(state_path)
    for path,ownership,contribution,source_identity in controls:
        state['files'][path] = {'ownership':ownership,'contribution':contribution,
            'baselineHash':composition.digest(b'authenticated'),
            'lastWrittenHash':composition.digest(b'authenticated'),
            'installedHash':composition.digest(b'authenticated')}
        if source_identity is not None: state['files'][path]['sourceIdentity'] = source_identity
        destination=root/path; destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(b'customized consumer bytes')
    state_path.write_bytes(composition.encoded(state))
    before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    conflicts = sync(root, True, 2)
    assert {path for path,_,_,_ in controls} <= {c['path'] for c in conflicts['conflicts']}
    assert not {path for path,_,_,_ in controls} & set(conflicts['preserved'])
    assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    state_path.write_bytes(original)
    for path,_,_,_ in controls: (root/path).unlink()
    sync(root, True)


def main():
    global ARTIFACT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='restore/build/pack actual selected public dependencies')
    parser.add_argument('--candidate-feed', help='Explicit local feed of response-policy development packages')
    parser.add_argument('--variant', choices=sorted(composition.VARIANTS), help='Bounded qualification of one selected composition')
    args = parser.parse_args()
    import uuid
    artifact = ROOT / 'artifacts/foundation-composition' / uuid.uuid4().hex[:8]
    artifact.mkdir(parents=True, exist_ok=True)
    ARTIFACT = artifact
    (artifact/'status.json').write_text(json.dumps({'status':'running','actualPackageBuild':args.build}),encoding='utf-8')
    (artifact/'source-inputs.json').write_text(json.dumps({str(p.relative_to(ROOT)):composition.digest(p.read_bytes()) for p in [
        SCRIPTS/'foundation_composition.py', SCRIPTS/'dotnet_sync.py', Path(__file__), ROOT/'extensions/program-kit-dotnet/templates/dotnet/managed-files.json']}),encoding='utf-8')
    observations = []
    for variant in [args.variant] if args.variant else sorted(composition.VARIANTS):
        source = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions' / (variant+'.json')
        value = composition.read(source)
        value['theme']['branding'] = {'displayName':'Qualified Example','accentColor':'#0088aa'}
        rejected(value, lambda v:v['application'].update({'publicOrigin':'https://app.example/path'}))
        rejected(value, lambda v:v['application'].update({'publicOrigin':'http://localhost:bad'}))
        rejected(value, lambda v:v['identity'].update({'backchannelOrigin':'http://private:65536'}))
        rejected(value, lambda v:v['application'].update({'signedOutCallbackPath':v['application']['callbackPath']}))
        rejected(value, lambda v:v['runtime'].update({'directory':'../escape'}))
        rejected(value, lambda v:v['identity'].update({'clientId':v['identity']['audience']}))
        rejected(value, lambda v:v['theme']['branding'].update({'template':'custom.ftl'}))
        rejected(value, lambda v:v['settings'].update({'ClientSecret':'never-write'}))
        with tempfile.TemporaryDirectory(prefix='program-kit-foundation-') as temporary:
            root = Path(temporary)
            (root/'eng').mkdir(); (root/composition.INPUT).write_bytes(composition.encoded(value))
            if args.candidate_feed:
                feed = root/'.program-kit/development-feed'; feed.mkdir(parents=True)
                candidates = {}
                import zipfile
                for archive in Path(args.candidate_feed).glob('*.nupkg'):
                    with zipfile.ZipFile(archive) as packed:
                        try: metadata = json.loads(packed.read('orbyss-foundation/settings.json'))
                        except KeyError: continue
                    package = metadata['packageId']
                    if package not in {'Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication.BffCookie'}: continue
                    shutil.copy2(archive,feed/archive.name)
                    candidates[package] = {'version':metadata['packageVersion'],'path':(feed/archive.name).relative_to(root).as_posix(),'sha256':composition.digest(archive.read_bytes())}
                profile = {'schemaVersion':1,'id':'reusable-foundations-response-policy-development',
                           'baseProfile':composition.publisher_contracts(root)['profile'],'status':'development-candidate','packages':candidates}
                path = root/'eng/foundation-development-candidate.json'; path.write_bytes(composition.encoded(profile))
                value['developmentCandidate'] = {'profile':path.relative_to(root).as_posix(),'sha256':composition.digest(path.read_bytes())}
                (root/composition.INPUT).write_bytes(composition.encoded(value))
            started = time.perf_counter(); preview = sync(root, True, 1)
            assert not (root/'src').exists()
            sync(root); generation = time.perf_counter()-started
            composition.verify_outputs(root)
            assert composition.read(root/'deploy/keycloak/program-kit-realm.json')['displayName']=='Qualified Example'
            assert '--program-kit-brand-accent: #0088aa' in (root/'deploy/keycloak/themes/program-kit/login/resources/css/program-kit.css').read_text()
            contract = composition.read(root/composition.CONTRACT)
            for budget in (1,30):
                altered_input = copy.deepcopy(value); altered_input['settings']['DiscoveryTimeoutSeconds'] = budget
                assert composition.web_settings(altered_input,contract)['DiscoveryTimeoutSeconds']==budget
            for changed in ({'DiscoveryTimeoutSeconds':31}, {'SessionIdleMinutes':30,'SessionAbsoluteMinutes':29}):
                altered_input = copy.deepcopy(value); altered_input['settings'].update(changed)
                try: composition.web_settings(altered_input,contract)
                except ValueError: pass
                else: raise AssertionError('Selected owner bounds/session relationship were ignored')
            desired_profile = (root/'eng/web-profile.shells.json').read_bytes()
            desired_realm = composition.read(root/'deploy/keycloak/program-kit-realm.json')
            mutations = [lambda r:r['clients'].append({'clientId':'unexpected-spa'}),
                         lambda r:r['clients'][1].update({'redirectUris':['http://localhost:5000/*']}),
                         lambda r:r['clients'][1].update({'secret':''}),
                         lambda r:r['users'][0].update({'realmRoles':[]})]
            for mutation in mutations:
                altered = copy.deepcopy(desired_realm); mutation(altered)
                try: composition.validate_materialized(root,value,contract,desired_profile,composition.encoded(altered))
                except ValueError: pass
                else: raise AssertionError('Invalid fixture security field was accepted')
            sync(root, True)
            resolved = composition.read(root/composition.RESOLVED)
            assert resolved['targets']['publicAuthority'].startswith('http://localhost:8080/')
            assert resolved['targets']['administrationOrigin'] == 'http://program-kit-identity:8080'
            assert not list((root/'src').glob('**/*Composition*.csproj')) and not list((root/'src').glob('**/Program.cs'))
            code = root / value['projects'][0]['path']; feature = code.parent/'ApiFeature.cs'
            feature.write_text(feature.read_text()+'\n// Consumer-owned customization.\n', encoding='utf-8')
            sync(root); assert 'Consumer-owned customization' in feature.read_text()
            value['application']['callbackPath'] = '/callback/custom'
            (root/composition.INPUT).write_bytes(composition.encoded(value)); sync(root)
            assert composition.read(root/composition.RESOLVED)['targets']['redirectUri'].endswith('/callback/custom')
            profile = root/'eng/web-profile.shells.json'; profile.write_text(profile.read_text()+'\n')
            conflicts = sync(root, True, 2); assert 'eng/web-profile.shells.json' in {c['path'] for c in conflicts['conflicts']}, conflicts
            profile.write_bytes(composition.encoded(composition.read(profile)))
            # Rendered JSON format is canonical, so restore authenticated managed bytes.
            sync(root, True)
            # Invalid effective overlays fail before reconciliation creates any byte.
            shells = root/'shells.json'; original_shells = shells.read_bytes()
            invalid_shells = composition.read(shells)
            invalid_shells['CShells']['Shells']['default'].setdefault('Configuration',{}).setdefault('Foundation',{}).setdefault('Web',{})['CallbackPath'] = '/unreviewed'
            shells.write_bytes(composition.encoded(invalid_shells))
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            run([sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
                 '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie'],ROOT,1)
            assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            shells.write_bytes(original_shells)
            invalid_shells['CShells']['Shells']['default']['Configuration']['Foundation']['Web'].clear()
            invalid_shells['CShells']['Shells']['default']['Configuration']['Foundation']['Web']['DiscoveryTimeoutSeconds'] = 31
            shells.write_bytes(composition.encoded(invalid_shells))
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            run([sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
                 '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie'],ROOT,1)
            assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            shells.write_bytes(original_shells)
            realm_path = root/'deploy/keycloak/program-kit-realm.json'; original_realm = realm_path.read_bytes()
            weakened_realm = composition.read(realm_path)
            weakened_realm['clients'][1].update(publicClient=True,secret='')
            realm_path.write_bytes(composition.encoded(weakened_realm))
            try: composition.verify_outputs(root)
            except ValueError: pass
            else: raise AssertionError('Weakened installed confidential-client fixture accepted')
            realm_path.write_bytes(original_realm)
            theme_path = root/'deploy/keycloak/themes/program-kit/login/resources/css/program-kit.css'
            original_theme = theme_path.read_bytes(); theme_path.write_bytes(original_theme+b'\nbody {display:none}\n')
            try: composition.verify_outputs(root)
            except ValueError: pass
            else: raise AssertionError('Unqualified theme customization retained inherited assurance')
            theme_path.write_bytes(original_theme)
            invalid_shells['CShells']['Shells']['default']['Configuration']['Foundation']['Web'].clear()
            invalid_shells['CShells']['Shells']['default']['Configuration']['Foundation']['Web']['BackchannelAuthority'] = 'https://other.example/realms/wrong'
            shells.write_bytes(composition.encoded(invalid_shells))
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            run([sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
                 '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie'],ROOT,1)
            assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            try: composition.verify_outputs(root)
            except ValueError: pass
            else: raise AssertionError('Wrong backchannel realm accepted by installed output validation')
            shells.write_bytes(original_shells)
            view = composition.effective_settings(root, {'Foundation:Web:ClientSecret':'secret-do-not-print'})
            assert 'secret-do-not-print' not in json.dumps(view)
            input_path = root/composition.INPUT; actual_input = input_path.read_bytes()
            substituted = copy.deepcopy(value)
            substituted['setup'] = {'steps':[{'stage':'services','command':[sys.executable,'fake-ready.py']}]}
            input_path.write_bytes(composition.encoded(substituted))
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            run([sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
                 '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie'],ROOT,1)
            assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            input_path.write_bytes(actual_input)
            retirement_checks(root, value)
            measurements = {'variant':variant, 'generationSeconds':generation, 'newGenericHarnessLines':0, 'runtimeDirectory':resolved['runtimeDirectory']}
            if args.build:
                consumer_version = '0.0.1-development' if args.candidate_feed else '0.0.1'
                solution = '<Solution>\n'+'\n'.join('  <Project Path="'+p['path']+'" />' for p in value['projects'])+'\n</Solution>\n'
                (root/'Application.slnx').write_text(solution, encoding='utf-8')
                (root/'VERSION').write_text(consumer_version+'\n', encoding='utf-8')
                started=time.perf_counter()
                restored=run(['dotnet','restore','Application.slnx'], root)
                measurements['restoreSeconds']=time.perf_counter()-started
                started=time.perf_counter()
                built=run(['dotnet','build','Application.slnx','-c','Release','--no-restore','-p:Version='+consumer_version],root)
                measurements['buildSeconds']=time.perf_counter()-started
                sys.path.insert(0,str(root/'eng'))
                import runtime_closure
                runtime_closure.prepare_pack(root,root/'artifacts/packages')
                packed=run(['dotnet','pack','Application.slnx','-c','Release','--no-build','-p:Version='+consumer_version,'-o','artifacts/packages'],root)
                runtime_closure.seal_pack(root,root/'artifacts/packages')
                staged=run([sys.executable,'eng/foundation_composition.py','--repository','.',
                            '--stage-packages','artifacts/packages','--pack-inventory','artifacts/packages/program-kit-pack.json'],root)
                assert (root/resolved['runtimeStage']/'shells.json').is_file()
                assert json.loads((root/'artifacts/program-kit/runtime-closure.json').read_text())['programKitVersion'] == composition.read(root/'.program-kit/managed.json')['programKitVersion']
                actual_packages = {runtime_closure.package_identity(p)[0] for p in (root/resolved['runtimeStage']/'packages').glob('*.nupkg')}
                assert set(value['runtime']['rootPackages']) <= actual_packages
                assert not any('test-support' in p.casefold() for p in actual_packages)
                import zipfile
                for project in value['projects']:
                    package = root/'artifacts/packages'/ (project['packageId']+'.'+consumer_version+'.nupkg')
                    with zipfile.ZipFile(package) as archive:
                        assert 'orbyss-foundation/feature.json' in archive.namelist()
                        assert not any('foundation_setup' in name or 'Probe' in name for name in archive.namelist())
                (artifact/(variant+'-build.log')).write_text(restored.stdout+built.stdout+packed.stdout+staged.stdout, encoding='utf-8')
                retained = artifact/variant/'consumer'
                shutil.copytree(root,retained,ignore=shutil.ignore_patterns('bin','obj','__pycache__','artifacts'))
                for name in ('hostsettings.json','shells.json','nuplane.settings.json'):
                    destination = retained/resolved['runtimeStage']/name; destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(root/resolved['runtimeStage']/name,destination)
                hashes = {p.name:composition.digest(p.read_bytes()) for p in (root/resolved['runtimeStage']/'packages').glob('*.nupkg')}
                (artifact/variant/'runtime-package-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
                shutil.copytree(root/'artifacts/packages',artifact/variant/'packages')
                shutil.copy2(root/'artifacts/program-kit/runtime-closure.json',artifact/variant/'runtime-closure.json')
                if variant.endswith('-postgresql'):
                    removed = value['projects'].pop()
                    value['runtime']['rootPackages'].remove(removed['packageId'])
                    value['compositionId'] = 'foundation-bff-keycloak'
                    value['tests'] = {}  # Re-select the maintained capability envelope for the new variant.
                    (root/composition.INPUT).write_bytes(composition.encoded(value)); sync(root)
                    effective = composition.read(root/'eng/web-profile.shells.json')
                    assert removed['featureIdentity'] not in effective['CShells']['Shells']['default']['Features']
                    assert removed['packageId'] not in composition.read(root/composition.RESOLVED)['rootPackages']
                    assert removed['path'] not in {p['path'] for p in composition.read(root/'eng/architecture.json')['runtimeComposition']['projects']}
            observations.append(measurements)
    (artifact/'qualification.json').write_bytes(composition.encoded({'schemaVersion':1,'checks':['invalid-inputs','metadata-bounds-and-session-relationships','actual-sync-preview-apply','rerun','consumer-customization','managed-drift','callback-regeneration','distinct-identity-addresses','beforewrite-overlay-conflicts','beforewrite-maintained-setup-envelope','installed-realm-security','installed-theme-integrity','redacted-provenance','customized-source-retirement-and-release','untouched-scaffold-retirement','managed-configuration-and-engineering-retirement-conflicts','deselected-orphan-exclusion'] + (['actual-build-pack-selected-root-stage','installed-program-kit-version','provider-removal'] if args.build else []), 'actualPackageBuild':args.build, 'measurements':observations,
        'limitations':['No service/runtime acceptance or first product operation timing is established by this validator.']}))
    (artifact/'status.json').write_text(json.dumps({'status':'passed','actualPackageBuild':args.build}),encoding='utf-8')
    print('Foundation composition selected contracts, synchronization and package checks passed')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        if ARTIFACT:
            (ARTIFACT/'status.json').write_text(json.dumps({'status':'failed','failure':str(error)}),encoding='utf-8')
        raise

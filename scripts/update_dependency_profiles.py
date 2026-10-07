"""Prepare, qualify and promote a new default with its exact publisher knowledge."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extensions/program-kit-building-blocks/scripts'))
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'scripts'))
import building_blocks as blocks
import profile_catalogs
import dependency_maintenance as maintenance

REGISTRY = blocks.profile_registry()
BLUEPRINT = REGISTRY/'catalogs/foundation-0-3-0-settings-v2/target-da6726d988f1dfdd912d2c0e28c56d4bf0498ae188dc45dda17c0f69b8893732.json'


def write(path,value): maintenance.write_json(path,value)


def reference(path,base=ROOT,normalized=False):
    return {'path':path.relative_to(base).as_posix(),
            'sha256':profile_catalogs.source_sha256(path) if normalized else blocks.raw_sha256(path)}


def sync_publisher_engineering(profile):
    """Use the selected public runtime's shared ABI until its successor is published."""
    version=profile['families']['foundation']['releaseVersion']
    url='https://api.nuget.org/v3-flatcontainer/orbyss.foundation.webdefaults/'+version+'/orbyss.foundation.webdefaults.nuspec'
    with urllib.request.urlopen(url,timeout=30) as response: spec=ET.fromstring(response.read(1_048_576))
    repository=next(n for n in spec.iter() if n.tag.rsplit('}',1)[-1]=='repository')
    commit=repository.get('commit')
    if not commit or len(commit)!=40: raise ValueError('Selected publisher source commit is missing')
    url='https://raw.githubusercontent.com/orbyss-io/dotnet-foundation/'+commit+'/Directory.Packages.props'
    with urllib.request.urlopen(url,timeout=30) as response: source=ET.fromstring(response.read(1_048_576))
    pins={n.get('Include'):n.get('Version') for n in source.iter('PackageVersion')}
    contracts_path=REGISTRY/'engineering-contracts.json'
    contracts=blocks.load_json(contracts_path) if contracts_path.exists() else {'schemaVersion':1,'releases':{}}
    contracts['releases'][version]={'sourceCommit':commit,'url':url,
        'pins':{name:pins[name] for name in ('CShells.Abstractions','CShells.AspNetCore.Abstractions')}}
    write(contracts_path,contracts)
    path=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Packages.props'
    text=path.read_text(encoding='utf-8')
    import re
    for identity in ('CShells.Abstractions','CShells.AspNetCore.Abstractions'):
        if not pins.get(identity): raise ValueError('Selected runtime omits its shared contract pin: '+identity)
        text,count=re.subn(r'(<PackageVersion Include="'+re.escape(identity)+r'" Version=")[^"]+("\s*/>)',
                          lambda m:m[1]+pins[identity]+m[2],text)
        if count!=1: raise ValueError('Engineering shared contract pin is ambiguous: '+identity)
    path.write_text(text,encoding='utf-8',newline='\n')


def require_published_foundation(version):
    """Do not adopt artifacts from a failed or partially published stable candidate."""
    url='https://api.nuget.org/v3-flatcontainer/orbyss.foundation.webdefaults/'+version+'/orbyss.foundation.webdefaults.nuspec'
    with urllib.request.urlopen(url,timeout=30) as response: spec=ET.fromstring(response.read(1_048_576))
    commit=next(n for n in spec.iter() if n.tag.rsplit('}',1)[-1]=='repository').get('commit')
    url='https://api.github.com/repos/orbyss-io/dotnet-foundation/actions/workflows/release.yml/runs?status=success&branch='+urllib.parse.quote('v'+version,safe='')+'&per_page=100'
    runs=maintenance.fetch(url)['workflow_runs']
    matching=[run for run in runs if run.get('head_branch')=='v'+version and run.get('head_sha')==commit
              and run.get('status')=='completed' and run.get('conclusion')=='success']
    if not matching: raise ValueError('Latest Foundation artifacts do not have a completed successful tagged Release workflow')
    return {'commit':commit,'workflow':matching[0]['html_url']}


def prepare():
    target=blocks.load_json(BLUEPRINT)
    families={}
    representatives={'foundation':'Orbyss.Foundation.WebDefaults','foundation-build':'Orbyss.Foundation.Build',
                     'forms':'Orbyss.Forms.Abstractions','localization':'Orbyss.Localization.Abstractions'}
    for family,identity in representatives.items():
        families[family]=maintenance.observe({'kind':'nuget','name':identity,'channel':'stable'}, {})['latest']
    exporter=maintenance.observe({'kind':'nuget','name':'Orbyss.Foundation.OpenApi.Exporter','channel':'stable'}, {})['latest']
    publication=require_published_foundation(families['foundation'])
    for family,version in families.items(): target['families'][family]['releaseVersion']=version
    target['families']['foundation']['toolVersions']['Orbyss.Foundation.OpenApi.Exporter']=exporter
    for package in target['packages'].values():
        package['version']=exporter if package['packageId']=='Orbyss.Foundation.OpenApi.Exporter' else families[package['family']]
    target['resolutionRevision']+=1
    blocks.validate_catalog(target)
    identity='foundation-'+families['foundation']+'-build-'+families['foundation-build']+'-exporter-'+exporter+'-forms-'+families['forms']+'-localization-'+families['localization']
    # A new qualification never replaces a registered historical identity.
    index=blocks.load_json(REGISTRY/'index.json')
    current_entry=index['profiles'][index['default']]
    current=blocks.load_json(REGISTRY/current_entry['path'])
    if current['families']==profile_families(target) and current_entry.get('knowledge'):
        sync_publisher_engineering(current)
        blocks.qualified_dependency_profile(REGISTRY,current['id'],blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
        return None
    if identity in index['profiles']:
        identity+='-q-'+uuid.uuid4().hex[:8]
    directory=REGISTRY/'candidates'/identity
    if directory.exists():
        existing=blocks.load_json(directory/'profile.json')
        if existing['families']!=profile_families(target): raise ValueError('Existing candidate identity conflicts with publisher versions')
        sync_publisher_engineering(existing)
        return directory
    directory.mkdir(parents=True)
    base=blocks.default_catalog(Path(blocks.__file__))
    target_path=directory/'catalog.json'; write(target_path,target)
    snapshot=profile_catalogs.prepare(base,target_path,REGISTRY,'candidate-'+uuid.uuid4().hex[:8])
    profile=blocks.dependency_profile_value(target,identity)
    sync_publisher_engineering(profile)
    profile_path=directory/'profile.json'; write(profile_path,profile)
    state={'schemaVersion':1,'profile':reference(profile_path),'catalog':reference(target_path),
           'snapshot':snapshot,'identity':identity,'status':'prepared','publisherRelease':publication}
    write(directory/'state.json',state)
    return directory


def profile_families(catalog):
    return blocks.dependency_profile_value(catalog,'update-comparison')['families']


def command(stage,args):
    result=subprocess.run(args,cwd=ROOT,check=False)
    if result.returncode: raise ValueError('Profile update failed at '+stage+'; candidate/evidence remain preserved')


def new_result(parent,before,filename):
    paths=[p for p in parent.glob('*/'+filename) if p.parent not in before]
    if len(paths)!=1: raise ValueError('Qualification produced ambiguous/missing '+filename)
    return paths[0].parent


def publisher_knowledge(directory,native,profile,host):
    """Copy exact public package facts and frozen source docs, with per-file hashes."""
    destination=directory/'knowledge'; destination.mkdir(exist_ok=False)
    packages=[]; commits=set(); package_sources={}; package_pack=destination/'package.pack'
    archives=[]
    for key,version in profile['artifacts'].items():
        if not key.startswith('nuget:Orbyss.Foundation.'): continue
        identity=key.removeprefix('nuget:')
        filename=identity.lower()+'.'+version.lower()+'.nupkg'
        paths=list((native/'closure').glob(filename))+list((native/'official-archives').glob(filename))
        paths+=list((native/'cache'/identity.lower()/version).glob(filename))
        paths+=list((native/'tool-cache'/identity.lower()/version).glob(filename))
        if not paths or len({blocks.raw_sha256(p) for p in paths})!=1: raise ValueError('Exact candidate knowledge archive is missing/ambiguous: '+identity)
        archives.append(paths[0])
    for path in sorted(archives):
        with zipfile.ZipFile(path) as archive:
            spec=ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.nuspec'))))
            fields={n.tag.rsplit('}',1)[-1]:n.text for n in spec.iter()}
            version=profile['artifacts'].get('nuget:'+fields['id'])
            if fields['version']!=version: raise ValueError('Knowledge package differs from candidate')
            repo=next(n for n in spec.iter() if n.tag.rsplit('}',1)[-1]=='repository')
            source_commit=repo.get('commit')
            if not source_commit or len(source_commit)!=40: raise ValueError('Package knowledge requires an exact publisher commit')
            package_sources.setdefault(source_commit,[]).append(fields['id'])
            if fields['id']!='Orbyss.Foundation.Build' and fields['id']!='Orbyss.Foundation.OpenApi.Exporter': commits.add(repo.get('commit'))
            facts={}; files={}
            for item in archive.infolist():
                if item.is_dir() or item.filename=='.signature.p7s': continue
                if item.file_size>64*1024*1024: raise ValueError('Publisher package exceeds bounded fact policy')
                data=archive.read(item); files[item.filename]=hashlib.sha256(data).hexdigest()
                if ((item.filename.startswith(('orbyss-foundation/','schemas/')) and item.filename.endswith('.json'))
                        or item.filename.startswith('lib/') and item.filename.endswith('.xml')
                        or item.filename.rsplit('/',1)[-1].casefold()=='readme.md'):
                    if len(data)>2*1024*1024: raise ValueError('Publisher fact exceeds two MiB')
                    facts[item.filename]=data.decode('utf-8')
            data=(json.dumps({'id':fields['id'],'version':version,'license':fields.get('license'),
                             'repository':repo.attrib,'payloadFiles':files,'facts':facts},indent=2)+'\n').encode('utf-8')
            if len(data)>16*1_048_576: raise ValueError('Publisher package knowledge exceeds sixteen MiB')
            offset=package_pack.stat().st_size if package_pack.exists() else 0
            with package_pack.open('ab') as stream: stream.write(data)
            packages.append({'id':fields['id'],'version':version,'path':package_pack.relative_to(REGISTRY).as_posix(),
                             'sha256':hashlib.sha256(data).hexdigest(),'byteOffset':offset,'byteLength':len(data)})
    if len(commits)!=1 or not next(iter(commits),None): raise ValueError('Runtime knowledge requires one exact publisher source commit')
    commit=next(iter(commits)); documents=[]; source_pack=destination/'source.pack'
    for source_commit,identities in sorted(package_sources.items()):
        tree=maintenance.fetch('https://api.github.com/repos/orbyss-io/dotnet-foundation/git/trees/'+source_commit+'?recursive=1')
        if tree.get('truncated'): raise ValueError('Publisher guidance inventory is incomplete')
        for item in tree['tree']:
            relative=item['path']
            source=any(relative.startswith('src/'+identity+'/') for identity in identities) and relative.endswith(('.cs','.json','.md','.targets','.props'))
            guide=source_commit==commit and (relative in {'README.md','LICENSE','THIRD-PARTY-NOTICES.md','src/Orbyss.Foundation.Host/NOTICE.md'} or relative.startswith('docs/') and relative.endswith('.md'))
            if item['type']!='blob' or not (guide or source): continue
            url='https://raw.githubusercontent.com/orbyss-io/dotnet-foundation/'+source_commit+'/'+relative
            with urllib.request.urlopen(url,timeout=30) as response: data=response.read(1_048_577)
            if len(data)>1_048_576: raise ValueError('Publisher guidance exceeds one MiB')
            # Indexed text keeps full frozen knowledge within Spec Kit's file limit.
            offset=source_pack.stat().st_size if source_pack.exists() else 0
            with source_pack.open('ab') as stream: stream.write(data)
            documents.append({'path':source_pack.relative_to(REGISTRY).as_posix(),
                              'sha256':hashlib.sha256(data).hexdigest(),'byteOffset':offset,'byteLength':len(data),
                              'publisherPath':relative,'url':url,'sourceCommit':source_commit})
    if not any(d['publisherPath']=='README.md' for d in documents): raise ValueError('Publisher usage guidance is missing')
    value={'schemaVersion':1,'profileId':profile['id'],'releaseVersion':profile['families']['foundation']['releaseVersion'],
           'sourceCommit':commit,'packages':packages,'documents':documents,'sourcePack':reference(source_pack,REGISTRY),
           'packagePack':reference(package_pack,REGISTRY),'hostImage':host['inputs']['hostImage'],
           'boundary':'Exact publisher facts and source guidance; selected architecture and compatibility remain Program Kit/consumer responsibilities.'}
    manifest=destination/'index.json'; write(manifest,value)
    return reference(manifest,REGISTRY)


def qualify(directory,engines):
    import validate_default_dependency_profile as native_qualifier
    from build_dependency_qualification import build
    import public_availability
    state=blocks.load_json(directory/'state.json')
    profile_path=ROOT/state['profile']['path']; target_path=REGISTRY/state['snapshot']['path']
    profile=blocks.load_json(profile_path); catalog=blocks.load_json(target_path)
    sync_publisher_engineering(profile)
    lock=directory/'packages.lock.json'
    if not lock.exists():
        command('native lock',[sys.executable,'tests/validate_default_dependency_profile.py','--profile',str(profile_path),'--catalog',str(target_path),'--prepare-lock',str(lock)])
    snapshot={**state['snapshot'],'path':(REGISTRY/state['snapshot']['path']).relative_to(ROOT).as_posix(),
              'base':reference(REGISTRY/state['snapshot']['base']['path'])}
    recipe=directory/('recipe-'+uuid.uuid4().hex[:8]+'.json')
    write(recipe,{'schemaVersion':1,'id':'qualification-'+uuid.uuid4().hex[:8],
                  'profile':{**reference(profile_path),'id':profile['id']},'families':profile['families'],
                  'catalogSnapshot':snapshot,'nativeLock':reference(lock,normalized=True),
                  'executor':reference(ROOT/'tests/validate_default_dependency_profile.py',normalized=True)})
    native=ROOT/'artifacts/profile-update-native'/uuid.uuid4().hex[:8]
    native_qualifier.qualify(profile_path,native,catalog_path=target_path,native_lock=lock,qualification_recipe=recipe)
    browser_root=ROOT/'artifacts/published-forms-browser'; before=set(browser_root.glob('*'))
    command('browser',[sys.executable,'tests/validate_published_forms_browser.py','--profile',str(profile_path),'--catalog',str(target_path),'--engines='+engines])
    browser=new_result(browser_root,before,'qualification-result.json')
    host_root=ROOT/'artifacts/bootstrap-runtime'; before=set(host_root.glob('*'))
    command('host',[sys.executable,'tests/validate_bootstrap_runtime.py','--profile',str(profile_path),'--catalog',str(target_path)])
    host=new_result(host_root,before,'qualification-result.json')
    available=directory/'availability.json'; write(available,{'artifacts':public_availability.verify(catalog,sorted(catalog['packages']))})
    receipt=build(profile_path,native,browser,available,host,catalog_path=target_path,native_lock=lock,qualification_recipe=recipe)
    proof=directory/'qualification.json'; write(proof,receipt)
    knowledge=publisher_knowledge(directory,native,profile,blocks.load_json(host/'qualification-result.json'))
    state.update(status='qualified',recipe=reference(recipe,REGISTRY),proof=reference(proof,REGISTRY),
                 lockSha256=profile_catalogs.source_sha256(lock),knowledge=knowledge)
    write(directory/'state.json',state)


def promote(directory):
    state=blocks.load_json(directory/'state.json')
    if state.get('status')!='qualified': raise ValueError('Failing/prepared candidates cannot become the default')
    profile_path=ROOT/state['profile']['path']; profile=blocks.load_json(profile_path)
    entry={'path':profile_path.relative_to(REGISTRY).as_posix(),'sha256':blocks.raw_sha256(profile_path),
           'status':'qualified','evidence':state['proof'],'catalogSnapshot':state['snapshot'],
           'qualificationRecipe':state['recipe'],'recipeSha256':profile_catalogs.source_sha256(ROOT/'tests/validate_default_dependency_profile.py'),
           'nativeLockSha256':state['lockSha256'],'knowledge':state['knowledge']}
    receipt=blocks.load_json(REGISTRY/state['proof']['path'])
    entry['allowedActivations']=receipt['scope']['allowedActivations']
    index=blocks.load_json(REGISTRY/'index.json')
    if profile['id'] in index['profiles']: raise ValueError('Preserve historical registration; prepare a new qualification identity')
    index['profiles'][profile['id']]=entry; index['default']=profile['id']
    original=(REGISTRY/'index.json').read_bytes()
    try:
        write(REGISTRY/'index.json',index)
        blocks.qualified_dependency_profile(REGISTRY,profile['id'],blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
    except Exception:
        (REGISTRY/'index.json').write_bytes(original); raise
    print('Promoted tested profile and versioned knowledge: '+profile['id'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','qualify','promote','update'])
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--engines',default='chromium,webkit' if os.name=='nt' else 'chromium,firefox,webkit')
    args=parser.parse_args()
    directory=prepare() if args.command in {'prepare','update'} else args.candidate
    if directory is None and args.command in {'prepare','update'}:
        print('Public profile and publisher knowledge are already current; no duplicate qualification.')
        return
    if directory is None: parser.error('--candidate is required')
    if args.command in {'qualify','update'}: qualify(directory.resolve(),args.engines)
    if args.command in {'promote','update'}: promote(directory.resolve())
    print('Candidate: '+str(directory))


if __name__=='__main__': main()

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
INDEPENDENT_TOOLS = ('Orbyss.Foundation.OpenApi.Exporter', 'Orbyss.Foundation.Analyzers')


def write(path,value): maintenance.write_json(path,value)


def reference(path,base=ROOT,normalized=False):
    path,base=blocks.filesystem_path(path),blocks.filesystem_path(base)
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


def prepare(refresh_publisher_knowledge=False, reason=None, tool=None):
    if refresh_publisher_knowledge and (not isinstance(reason, str) or not reason.strip()):
        raise ValueError('Refreshing publisher knowledge requires an explicit nonempty reason')
    base=blocks.default_catalog(Path(blocks.__file__))
    index=blocks.load_json(REGISTRY/'index.json')
    current_entry=index['profiles'][index['default']]
    current_catalog,current=blocks.qualified_dependency_profile(REGISTRY,index['default'],blocks.load_json(base))
    # Evolve the admitted current contracts, not a historical release's rules.
    # The qualifier also verifies the retained snapshot, profile and evidence.
    target=copy.deepcopy(current_catalog)
    if tool is not None and tool not in INDEPENDENT_TOOLS:
        raise ValueError('Select a registered independent Foundation tool')
    families={}
    representatives={'foundation':'Orbyss.Foundation.WebDefaults','foundation-build':'Orbyss.Foundation.Build',
                     'forms':'Orbyss.Forms.Abstractions','localization':'Orbyss.Localization.Abstractions'}
    for family,identity in representatives.items():
        families[family]=(current['families'][family]['releaseVersion'] if tool else
            maintenance.observe({'kind':'nuget','name':identity,'channel':'stable'}, {})['latest'])
    tools={identity: (current['artifacts']['nuget:'+identity] if tool and tool != identity else
        maintenance.observe({'kind':'nuget','name':identity,'channel':'stable'}, {})['latest'])
        for identity in INDEPENDENT_TOOLS}
    exporter=tools['Orbyss.Foundation.OpenApi.Exporter']
    publication=require_published_foundation(families['foundation'])
    for family,version in families.items(): target['families'][family]['releaseVersion']=version
    # Do not add a redundant analyzer override to unchanged historical profiles.
    for identity,version in tools.items():
        overrides=target['families']['foundation'].setdefault('toolVersions',{})
        if identity in overrides or version != families['foundation']:
            overrides[identity]=version
    for package in target['packages'].values():
        family=target['families'][package['family']]
        package['version']=family.get('toolVersions',{}).get(package['packageId'],families[package['family']])
    # This additive publisher capability belongs only to the new immutable
    # profile snapshot. Historical catalogs/locks retain their original meaning.
    # Public publication is checked above; native qualification below must obtain
    # and inspect the actual package before this candidate can be promoted.
    if tuple(map(int, families['foundation'].split('.'))) >= (0, 3, 6):
        identity = 'nuget:Orbyss.Foundation.Web.Presentation'
        if identity not in target['packages']:
            package = copy.deepcopy(target['packages']['nuget:Orbyss.Foundation.Web.ProblemDetails'])
            package.update(packageId='Orbyss.Foundation.Web.Presentation', version=families['foundation'],
                role='Independently selected native browser presentation, confirmation and private session lifecycle.')
            package['activations'] = [{'featureIdentity': 'Orbyss.Foundation.Web.Presentation', 'targetSlot': 'shell'}]
            target['packages'][identity] = package
    if refresh_publisher_knowledge and current['families'] != profile_families(target):
        raise ValueError('Publisher-knowledge refresh requires unchanged package families; use normal dependency preparation for upgrades')
    target['resolutionRevision']+=1
    blocks.validate_additive_profile_catalog(current_catalog,target)
    blocks.validate_additive_profile_catalog(blocks.load_json(base),target)
    identity='foundation-'+families['foundation']+'-build-'+families['foundation-build']+'-exporter-'+exporter+'-forms-'+families['forms']+'-localization-'+families['localization']
    if tools['Orbyss.Foundation.Analyzers'] != families['foundation']:
        identity+='-analyzer-'+tools['Orbyss.Foundation.Analyzers']
    # A new qualification never replaces a registered historical identity.
    if not refresh_publisher_knowledge and current['families']==profile_families(target) and current_entry.get('knowledge'):
        sync_publisher_engineering(current)
        blocks.qualified_dependency_profile(REGISTRY,current['id'],blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
        return None
    if identity in index['profiles']:
        identity+='-q-'+uuid.uuid4().hex[:8]
    directory=REGISTRY/'candidates'/identity
    if directory.exists():
        existing=blocks.load_json(directory/'profile.json')
        retained=blocks.load_json(directory/'catalog.json')
        blocks.validate_additive_profile_catalog(current_catalog,retained)
        if (existing!=blocks.dependency_profile_value(target,identity)
                or retained!=target):
            raise ValueError('Existing candidate identity conflicts with current contracts or publisher versions')
        sync_publisher_engineering(existing)
        return directory
    directory.mkdir(parents=True)
    target_path=directory/'catalog.json'; write(target_path,target)
    snapshot=profile_catalogs.prepare(base,target_path,REGISTRY,'candidate-'+uuid.uuid4().hex[:8])
    profile=blocks.dependency_profile_value(target,identity)
    sync_publisher_engineering(profile)
    profile_path=directory/'profile.json'; write(profile_path,profile)
    state={'schemaVersion':1,'profile':reference(profile_path),'catalog':reference(target_path),
           'snapshot':snapshot,'identity':identity,'status':'prepared','publisherRelease':publication}
    if refresh_publisher_knowledge:
        state['publisherKnowledgeRefresh'] = {'fromProfile': index['default'], 'reason': reason.strip()}
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


def publisher_archive_facts(archive):
    """Retain exact supported package metadata; the native owner defines its meaning."""
    facts, files = {}, {}
    for item in archive.infolist():
        if item.is_dir() or item.filename == '.signature.p7s':
            continue
        if item.file_size > 64 * 1024 * 1024:
            raise ValueError('Publisher package exceeds bounded fact policy')
        data = archive.read(item)
        files[item.filename] = hashlib.sha256(data).hexdigest()
        if ((item.filename.startswith(('orbyss-foundation/', 'schemas/')) and item.filename.endswith('.json'))
                or item.filename == 'buildTransitive/source-readability-contract.json'
                or item.filename.startswith('lib/') and item.filename.endswith('.xml')
                or item.filename.rsplit('/', 1)[-1].casefold() == 'readme.md'):
            if len(data) > 2 * 1024 * 1024:
                raise ValueError('Publisher fact exceeds two MiB')
            facts[item.filename] = data.decode('utf-8')
    return facts, files


PUBLISHER_GUIDANCE = frozenset({
    'README.md', 'LICENSE', 'THIRD-PARTY-NOTICES.md', 'src/Orbyss.Foundation.Host/NOTICE.md',
    'docs/authentication.md', 'docs/foundation-contracts-adoption.md',
    'docs/host-transport-budgets.md', 'docs/hosted-application-pages.md',
    'docs/json-canonicalization-decision.md', 'docs/package-loader-qualification.md',
})


def publisher_document_selected(relative, identities, runtime_commit):
    """Capture maintained usage guidance, never a publisher's arbitrary work journal."""
    source = any(relative.startswith('src/' + identity + '/') for identity in identities) and relative.endswith(
        ('.cs', '.json', '.md', '.targets', '.props', '.mjs', '.mts', '.css'))
    analyzer_guide = relative == 'docs/ef-migration-authoring.md' and 'Orbyss.Foundation.Analyzers' in identities
    return source or analyzer_guide or runtime_commit and relative in PUBLISHER_GUIDANCE


def publisher_knowledge(directory,native,profile,host):
    """Copy exact public package facts and frozen source docs, with per-file hashes."""
    destination=directory/'knowledge'; destination.mkdir(exist_ok=False)
    from capture_lifecycle_knowledge import capture as capture_lifecycle
    capture_lifecycle(REGISTRY, native/'cache', blocks.load_json(directory/'packages.lock.json'))
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
            if fields['id'] not in ('Orbyss.Foundation.Build', *INDEPENDENT_TOOLS): commits.add(repo.get('commit'))
            facts, files = publisher_archive_facts(archive)
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
            if item['type']!='blob' or not publisher_document_selected(relative,identities,source_commit==commit): continue
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


def retain_browser(profile, identity, reason):
    """Explicit maintainer disposition for unchanged released npm artifacts only."""
    import re
    if not reason or not reason.strip():
        raise ValueError('Retaining unchanged browser evidence requires an explicit reason')
    index=blocks.load_json(REGISTRY/'index.json'); entry=index['profiles'][identity]
    proof=REGISTRY/entry['evidence']['path']
    revision=subprocess.check_output(['git','log','-1','--format=%H','--',str(proof.relative_to(ROOT))],cwd=ROOT,text=True).strip()
    if not re.fullmatch('[a-f0-9]{40}',revision): raise ValueError('Historical browser source revision unavailable')
    paths=[ROOT/'tests/validate_published_forms_browser.py',
           ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/.nvmrc',
           ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/.npm-version']
    paths += [p for p in (ROOT/'tests/fixtures/knowledge-application/forms-browser-packages').rglob('*') if p.is_file()]
    hashes={}
    for path in paths:
        relative=path.relative_to(ROOT).as_posix()
        before=subprocess.check_output(['git','show',revision+':'+relative],cwd=ROOT)
        normalized=lambda data:data.replace(b'\r\n',b'\n')
        if normalized(before)!=normalized(path.read_bytes()): raise ValueError('Browser fixture/toolchain input changed; fresh qualification required: '+relative)
        hashes[relative]=hashlib.sha256(normalized(before)).hexdigest()
    summary=copy.deepcopy(blocks.load_json(proof)['browserIntegration'])
    summary['retainedFrom']={'profileId':identity,'evidence':entry['evidence'],'reason':reason,
                             'inputRevision':revision,'inputs':hashes}
    prior=blocks.retained_browser_evidence(REGISTRY,profile,summary)
    return summary,[a for a in prior['availableArtifacts'] if a['packageKey'].startswith('npm:')]


def qualify(directory,engines,retained_profile=None,reason=None,native_evidence=None,host_evidence=None):
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
    if native_evidence:
        native=native_evidence.resolve()
        if not native.is_relative_to(ROOT/'artifacts/profile-update-native'): raise ValueError('Select explicit owned native profile evidence')
        digest=blocks.load_json(native/'qualification.json')['source']['qualificationRecipeSha256']
        matches=[p for p in directory.glob('recipe-*.json') if blocks.raw_sha256(p)==digest]
        if len(matches)!=1: raise ValueError('Retained native evidence has no exact candidate recipe')
        recipe=matches[0]
    else:
        recipe=directory/('recipe-'+uuid.uuid4().hex[:8]+'.json')
        write(recipe,{'schemaVersion':1,'id':'qualification-'+uuid.uuid4().hex[:8],
                      'profile':{**reference(profile_path),'id':profile['id']},'families':profile['families'],
                      'catalogSnapshot':snapshot,'nativeLock':reference(lock,normalized=True),
                      'executor':reference(ROOT/'tests/validate_default_dependency_profile.py',normalized=True)})
        native=ROOT/'artifacts/profile-update-native'/uuid.uuid4().hex[:8]
        native_qualifier.qualify(profile_path,native,catalog_path=target_path,native_lock=lock,qualification_recipe=recipe)
    retained=None; historical_npm=[]; browser=None
    if retained_profile:
        retained,historical_npm=retain_browser(profile,retained_profile,reason)
    else:
        browser_root=ROOT/'artifacts/published-forms-browser'; before=set(browser_root.glob('*'))
        command('browser',[sys.executable,'tests/validate_published_forms_browser.py','--profile',str(profile_path),'--catalog',str(target_path),'--engines='+engines])
        browser=new_result(browser_root,before,'qualification-result.json')
    if host_evidence:
        host=host_evidence.resolve()
        if not host.is_relative_to(ROOT/'artifacts/bootstrap-runtime'): raise ValueError('Select explicit owned Host profile evidence')
    else:
        host_root=ROOT/'artifacts/bootstrap-runtime'; before=set(host_root.glob('*'))
        command('host',[sys.executable,'tests/validate_bootstrap_runtime.py','--profile',str(profile_path),'--catalog',str(target_path)])
        host=new_result(host_root,before,'qualification-result.json')
    keys=sorted(k for k in catalog['packages'] if not retained or not k.startswith('npm:'))
    available=directory/'availability.json'; write(available,{'artifacts':public_availability.verify(catalog,keys)+historical_npm})
    receipt=build(profile_path,native,browser,available,host,catalog_path=target_path,native_lock=lock,qualification_recipe=recipe,retained_browser=retained)
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
    parser.add_argument('--retain-unchanged-browser', help='Explicit qualified historical profile; identical npm pins and browser fixture/toolchain required. No new browser execution claim.')
    parser.add_argument('--reason', help='Reason for explicit publisher-knowledge refresh or retained unchanged browser evidence')
    parser.add_argument('--refresh-publisher-knowledge', action='store_true', help='Prepare a distinct qualification identity for corrected publisher capture with unchanged package pins; requires --reason')
    parser.add_argument('--tool', choices=INDEPENDENT_TOOLS, help='Prepare/update only this independent tool; retain every other selected package pin')
    parser.add_argument('--native-evidence',type=Path,help='Exact successful candidate native evidence; the normal builder revalidates all inputs, stages and archives')
    parser.add_argument('--host-evidence',type=Path,help='Exact successful candidate Host evidence; the normal builder revalidates all manifests, cases and cleanup')
    args=parser.parse_args()
    if args.refresh_publisher_knowledge and args.command not in {'prepare', 'update'}:
        parser.error('--refresh-publisher-knowledge applies only to prepare/update')
    if args.tool and args.command not in {'prepare','update'}:
        parser.error('--tool applies only to prepare/update')
    directory=prepare(args.refresh_publisher_knowledge, args.reason, args.tool) if args.command in {'prepare','update'} else args.candidate
    if directory is None and args.command in {'prepare','update'}:
        print('Public profile and publisher knowledge are already current; no duplicate qualification.')
        return
    if directory is None: parser.error('--candidate is required')
    if args.command in {'qualify','update'}: qualify(directory.resolve(),args.engines,args.retain_unchanged_browser,args.reason,args.native_evidence,args.host_evidence)
    if args.command in {'promote','update'}: promote(directory.resolve())
    print('Candidate: '+str(directory))


if __name__=='__main__': main()

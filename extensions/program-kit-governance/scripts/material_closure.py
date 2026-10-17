"""Conservative, explicitly reviewed architecture and plain SDK solution projections."""
from pathlib import Path
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET


def require(condition,message):
    if not condition:raise ValueError('Review material closure: '+message)


def local(root,relative):
    require(isinstance(relative,str) and relative and not Path(relative).is_absolute()
            and not re.match(r'^[A-Za-z]:',relative) and '\\' not in relative
            and not {'.','..'}&set(relative.split('/')),'use a contained literal source path')
    path=root/relative
    require(path.resolve().is_relative_to(root.resolve()),'source path escaped reviewed root')
    for entry in (path,*path.parents):
        if entry==root:break
        require(not entry.is_symlink() and not getattr(entry,'is_junction',lambda:False)(),'aliased source needs explicit scope assessment')
    return path


def file_hash(path):
    require(path.is_file() and path.stat().st_size<=16_777_216,'missing or oversized material closure input')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strings(value):
    if isinstance(value,str):return {value}
    if isinstance(value,dict):return set().union(*(strings(item) for item in value.values()))
    if isinstance(value,list):return set().union(*(strings(item) for item in value))
    return set()


def architecture(root,value,selected):
    import architecture_map
    import feature_knowledge
    architecture_map.validate_model(value,root)
    require(isinstance(selected,list) and selected and all(isinstance(item,str) for item in selected)
            and len(selected)==len(set(selected)),'select unique original architecture elements')
    elements={item['id']:item for item in value['elements']}
    require(set(selected)<=set(elements),'unknown selected architecture element')
    # Ancestor metadata is shared, without treating every ancestor child as an
    # owned sibling. Actual boundary dependencies expand to a fixed point.
    ancestors=set()
    pending=list(selected)
    while pending:
        parent=elements[pending.pop()].get('parent')
        if parent and parent not in ancestors:ancestors.add(parent);pending.append(parent)
    expanded=set(selected)
    for _ in range(len(elements)+1):
        projection=feature_knowledge.project(root,sorted(expanded))
        reached={item['id'] for item in projection['elements']}-ancestors
        owner_contexts={item['element'] for item in projection['strategic_model']['bounded_contexts']}
        providers=[item for item in value['strategic_model']['capability_bindings']
                   if {item.get('semantic_owner'),item.get('integration_owner'),item.get('module')}&(owner_contexts|expanded)]
        projection['strategic_model']['capability_bindings']=providers
        reached|=(strings(providers)|strings(projection['strategic_model']['context_relationships']))&set(elements)-ancestors
        if reached<=expanded:break
        expanded|=reached
    else:raise ValueError('Review material closure: architecture dependency closure did not converge')
    projection.update(schema_version=value['schema_version'],model_id=value['model_id'],title=value['title'],
                      configuration=value['configuration'],extensions=value['extensions'],refinements=value.get('refinements',[]))
    strategic=value['strategic_model']
    projection['strategicGlobals']={key:item for key,item in strategic.items() if not isinstance(item,list)}
    projection['strategicGlobals']['decision_refs']=strategic['decision_refs']
    contexts={item['element'] for item in projection['strategic_model']['bounded_contexts']}
    journeys={item['id'] for item in projection['strategic_model']['journeys']}
    projection['strategic_model']['candidate_slices']=[item for item in strategic['candidate_slices']
        if set(item['contexts'])&contexts or item['journey'] in journeys or set(item.get('supporting_journeys',[]))&journeys]
    boundary={item['id'] for item in projection['elements']}
    edges={item['id'] for item in projection['relationships']}
    projection['views']=[{**item,'elements':[name for name in item['elements'] if name in boundary],
                         'relationships':[name for name in item['relationships'] if name in edges],
                         'order':[name for name in item['order'] if name in boundary|edges],
                         'animations':[[name for name in step if name in boundary|edges] for step in item['animations']]}
                        for item in value['views'] if item['scope'] in expanded or
                        set(item['elements'])&expanded or set(item['relationships'])&edges]
    # Unknown/global documentation ownership stays fully bound. Source/decision
    # records cited by the complete selected facts retain their exact authority.
    projection['documentation']=value['documentation']
    cited=strings(projection)
    projection['sources']=value['sources']  # Evidence IDs can be internal to a shared source document.
    projection['decisions']=[item for item in value['decisions'] if item['id'] in cited]
    projection['authorityFiles']={item['path']:file_hash(local(root,item['path']))
        for collection in ('sources','decisions','documentation') for item in projection[collection]}
    return copy.deepcopy(projection)


PROPERTIES={'TargetFramework','OutputType','ImplicitUsings','Nullable','LangVersion','TreatWarningsAsErrors',
            'IsPackable','AssemblyName','RootNamespace','Version','PackageId','Description','Authors',
            'DefineConstants','Deterministic','ContinuousIntegrationBuild','ManagePackageVersionsCentrally',
            'RestorePackagesWithLockFile','EnableNETAnalyzers','AnalysisLevel','AnalysisMode','GenerateDocumentationFile'}
EXCLUDED={'.git','.specify','.program-kit','artifacts','bin','obj','node_modules','__pycache__'}


def xml(path):
    raw=path.read_bytes()
    require(len(raw)<=1_048_576,'oversized XML material input')
    text=raw.decode('utf-8-sig')
    require('<!DOCTYPE' not in text.upper() and '<!ENTITY' not in text.upper(),'unqualified XML declaration')
    return ET.fromstring(text)


def plain_project(root,relative,private):
    path=local(root,relative)
    require(path.suffix=='.csproj' and path.is_file(),'version 1 supports existing plain C# SDK projects only')
    node=xml(path)
    require(node.tag=='Project' and node.attrib=={'Sdk':'Microsoft.NET.Sdk'},'custom/multiple SDK or imports need explicit native scope')
    properties={};references=[]
    for group in node:
        require(not group.attrib and group.tag in ('PropertyGroup','ItemGroup'),'conditional/import/target/custom project policy needs explicit scope')
        for item in group:
            if group.tag=='PropertyGroup':
                require(item.tag in PROPERTIES and not item.attrib and len(item)==0 and item.text is not None
                        and not re.search(r'[$@%]\(|[;*?]',item.text) and item.tag not in properties,
                        'dynamic, repeated or unsupported SDK property')
                properties[item.tag]=item.text.strip()
                if item.tag in ('AssemblyName','RootNamespace','PackageId'):
                    require(re.fullmatch('[A-Za-z0-9_.-]+',properties[item.tag]) is not None,'custom output identity needs native assessment')
            else:
                require(item.tag=='ProjectReference' and set(item.attrib)=={'Include'} and not len(item)
                        and not re.search(r'[$@%*?;]',item.attrib['Include']),'package/custom/dynamic project items require native closure assessment')
                original=path.parent/item.attrib['Include'].replace('\\','/')
                for entry in (original,*original.parents):
                    if entry.is_relative_to(root):
                        require(not entry.is_symlink() and not getattr(entry,'is_junction',lambda:False)(),'aliased project reference needs explicit scope')
                reference=original.resolve()
                require(reference.is_relative_to(root.resolve()),'external project reference needs explicit assessment')
                references.append(reference.relative_to(root.resolve()).as_posix())
    require(re.fullmatch(r'net\d+\.\d+',properties.get('TargetFramework','')) is not None,'multitarget/custom framework needs native closure assessment')
    if private:
        require(properties.get('IsPackable')=='false' and properties.get('OutputType','Library')=='Library',
                'unrelated new members must be explicitly private nonpackable libraries')
    return sorted(references)


def solution(root,path,projects):
    require(path.suffix=='.slnx','version 1 supports plain slnx membership only; retain other solutions whole')
    require(isinstance(projects,list) and projects and len(projects)==len(set(projects)),'select original entry projects explicitly')
    node=xml(path)
    require(node.tag=='Solution' and not node.attrib,'unknown/global solution attributes remain material/unsupported')
    members={}
    for item in node:
        require(item.tag=='Project' and set(item.attrib)=={'Path'} and not len(item),'solution folders/configurations/custom entries need native assessment')
        relative=item.attrib['Path']
        require(relative.casefold() not in {name.casefold() for name in members},'duplicate/case-colliding solution member')
        members[relative]=plain_project(root,relative,private=False)
    require(set(projects)<=set(members),'selected solution root was removed')
    selected=set(projects);pending=list(projects)
    while pending:
        relative=pending.pop()
        references=members.get(relative)
        if references is None:references=plain_project(root,relative,private=False)
        for reference in references:
            if reference not in selected:selected.add(reference);pending.append(reference)
        require(len(selected)<=256,'selected SDK closure exceeds its finite bound')
    for relative in set(members)-selected:plain_project(root,relative,private=True)
    sources={};policies={}
    # Solution/global tooling files are shared material even when the plain SDK
    # adapter has no semantics for them. Never silently ignore a new root policy.
    for file in root.iterdir():
        if file.is_file() and file.resolve()!=path.resolve():
            policies[file.name]=file_hash(local(root,file.name))
    for relative in sorted(selected):
        project=local(root,relative)
        for file in project.parent.rglob('*'):
            if file.is_file() and not EXCLUDED&set(file.relative_to(project.parent).parts):
                name=file.relative_to(root).as_posix();sources[name]=file_hash(local(root,name))
        for directory in (project.parent,*project.parent.parents):
            if not directory.is_relative_to(root):break
            policy_names={'Directory.Build.props','Directory.Build.targets','Directory.Packages.props',
                          'Directory.Solution.props','Directory.Solution.targets','Directory.Build.rsp','MSBuild.rsp',
                          'global.json','NuGet.config','.editorconfig'}
            policy_names.update(file.name for file in directory.iterdir() if file.is_file()
                                and file.suffix.lower() in ('.props','.targets','.rsp'))
            for name in policy_names:
                file=directory/name;key=file.relative_to(root).as_posix()
                policies[key]=file_hash(local(root,key)) if file.exists() else None
                require(not file.is_file() or file.suffix.lower()!='.rsp','native response-file policy requires an explicit native adapter')
                if file.is_file() and file.suffix.lower() in ('.props','.targets'):
                    policy=xml(file)
                    require(policy.tag=='Project' and not policy.attrib,'unqualified shared build policy')
                    for group in policy:
                        require(group.tag=='PropertyGroup' and not group.attrib,'shared imports/targets/items require native closure assessment')
                        for item in group:
                            require(item.tag in PROPERTIES and not item.attrib and not len(item) and item.text is not None
                                    and not re.search(r'[$@%]\(|[;*?]',item.text),'dynamic shared policy needs native assessment')
    require((root/'global.json').is_file(),'bind the selected SDK through an explicit root global.json')
    for parent in root.parents:
        require(not any((parent/name).exists() for name in ('Directory.Build.props','Directory.Build.targets','Directory.Packages.props',
                    'Directory.Solution.props','Directory.Solution.targets','Directory.Build.rsp','MSBuild.rsp')),
                'external inherited build policy requires an explicit native adapter')
    require(len(sources)<=4096,'selected source inventory exceeds its finite bound')
    return {'entryProjects':sorted(projects),'projects':sorted(selected),'sources':sources,'sharedPolicies':policies,
            'policy':'plain-private-sdk-v1; no package/custom/dynamic MSBuild or solution configurations'}

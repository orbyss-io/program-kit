"""Maintained evaluated-MSBuild and compiled metadata recipe; emits real JUnit cases.

Consumer registration/resolution and substitutability tests complement this structural
recipe. Metadata alone cannot establish runtime feature behavior.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from architecture_rules import (ALLOWED_ROLE_REFERENCES, FORBIDDEN_CORE_PACKAGE_PREFIXES,
                                CAPABILITY_IMPLEMENTATION_ROLES, PERSISTENCE_PACKAGE_PREFIXES,
                                ACTIVATABLE_PROJECT_ROLES, validate_project_role)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def inside(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), 'Engineering path escapes repository: ' + str(relative))
    return path

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def is_build_reference(item):
    """Evaluated build/analyzer edges do not create consumer CLR references."""
    return (str(item.get('ReferenceOutputAssembly', '')).casefold() == 'false'
            or str(item.get('OutputItemType', '')).casefold() == 'analyzer')


def project_dependencies(project):
    """Both edge kinds participate in build, source freshness and affected selection."""
    return set(project.get('projectReferences', [])) | set(project.get('buildProjectReferences', []))


TEST_SEAM_CONTRACTS = {
    'pure-core': (),
    'shell-lifecycle': ('CShells.Abstractions',),
    'api-feature': ('CShells.Abstractions', 'CShells.AspNetCore.Abstractions'),
    'activation': ('CShells.Abstractions', 'CShells.AspNetCore.Abstractions'),
}


def test_compile_contracts(project, required=False):
    """Derive direct references from reviewed test use, never the tested project's role."""
    if project.get('role') != 'test':
        return set()
    contracts = set()
    rows = project.get('responsibilities', [])
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows),
            'PKA020 invalid test responsibilities: ' + project['path'])
    require(not required or any(row.get('kind') == 'test' for row in rows),
            'PKA020 unresolved test responsibility: ' + project['path'] + '; declare meaningful test ownership and testSeams')
    for row in rows:
        if row.get('kind') != 'test':
            continue
        seams = row.get('testSeams')
        require(seams is not None or not required,
                'PKA020 unresolved test compile responsibilities: ' + project['path'] + ' / ' + row['name'] + '; declare testSeams')
        if seams is None:
            continue  # Retained manifests have only their previously declared structural scope.
        require(isinstance(seams, list) and seams and all(isinstance(s, str) for s in seams),
                'PKA020 testSeams must name actual direct test uses: ' + project['path'])
        require(set(seams) <= set(TEST_SEAM_CONTRACTS),
                'PKA020 unsupported test seam: ' + project['path'] + '; ' + ', '.join(sorted(set(seams) - set(TEST_SEAM_CONTRACTS))))
        for seam in seams:
            contracts.update(TEST_SEAM_CONTRACTS[seam])
    return contracts


def lifecycle_findings(root, manifest, affected=None):
    """Concrete source/owner prompts for normal review, never semantic certification.

    A bounded source observation cannot resolve all C# aliases/generated bodies.
    Findings name their evidence; absence does not waive the required code review.
    """
    projects = manifest.get('runtimeComposition', {}).get('projects', [])
    selected = {project['path'] for project in projects} if affected is None else set(affected)
    owners = set(selected)
    for project in projects:
        if project['path'] in selected:
            owners.update(project.get('projectReferences', []))
    sources, contributors, findings = {}, [], []
    for project in projects:
        path = project['path']
        if path not in owners: continue
        rows = []
        for file in inside(root, path).parent.rglob('*.cs'):
            if {'obj', 'bin'} & set(file.parts): continue
            content = file.read_text(encoding='utf-8-sig')
            # Do not turn comments/string literals into ownership allegations.
            content = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', ' ', content, flags=re.S)
            relative = file.relative_to(root).as_posix()
            rows.append((relative, content))
            for match in re.finditer(r'\bclass\s+(\w+)(?:\s*\([^;{}]*\))?\s*:\s*([^{}]+)\{', content):
                contracts = set(re.findall(r'\b(?:IShellInitializer|IStartupTask|IBackgroundTask|IRecurringTask)\b', match[2]))
                if contracts:
                    contributors.append((path, relative, match[1], contracts))
        sources[path] = rows
    for project in projects:
        path = project['path']
        if path not in selected: continue
        role = project.get('role')
        try:
            validate_project_role(role, path)
        except ValueError as error:
            findings.append({'id': 'retired-composition-project' if role == 'composition' else 'invalid-project-role',
                             'project': path, 'message': str(error) + (
                                 '; architecture owner must record the actual reviewed role/responsibilities in eng/architecture.json; '
                                 'do not infer or relabel ownership to bypass its duties.' if role != 'composition' else '')})
            continue
        if role not in ACTIVATABLE_PROJECT_ROLES:
            continue
        for owner, owner_source, symbol, contracts in contributors:
            if owner == path: continue
            for relative, content in sources[path]:
                if re.search(r'\b' + re.escape(symbol) + r'\b', content):
                    findings.append({'id': 'foreign-lifecycle-ownership', 'project': path,
                                     'source': relative, 'ownerProject': owner, 'ownerSource': owner_source,
                                     'message': 'Review reference to ' + symbol + ' (' + ', '.join(sorted(contracts)) +
                                                ') owned by another feature. That feature registers its own contribution; do not register its tasks or invoke its preparation from a peer feature.'})
    return findings


def validate_responsibilities(projects, bindings, required=False):
    """Reject declared contradictions; this never certifies the truth of a label."""
    allowed = {
        'core': {'contract', 'pure-policy', 'pure-helper'},
        'helper': {'pure-helper'},
        'implementation': {'runtime', 'http', 'pure-helper'},
        'provider': {'persistence', 'runtime', 'pure-helper'},
        'bridge': {'runtime', 'pure-helper'},
        'test': {'test', 'pure-helper'},
    }
    for path, project in projects.items():
        rows = project.get('responsibilities')
        requires_review = required is True or isinstance(required, (set, list, tuple)) and path in required
        require(rows is not None or not requires_review,
                'Record planned responsibilities in eng/architecture.json before design review: ' + path)
        if rows is None:
            continue  # Older engineering manifests still prove only their structural scope.
        require(isinstance(rows, list) and bool(rows), 'Project responsibilities must be a nonempty list: ' + path)
        names = set()
        for row in rows:
            require(isinstance(row, dict) and isinstance(row.get('name'), str) and row['name'].strip(),
                    'Responsibility requires its meaningful name: ' + path)
            require(row['name'] not in names, 'Duplicate responsibility: ' + row['name'])
            names.add(row['name'])
            require(row.get('kind') in allowed.get(project['role'], set()),
                    'Core/runtime responsibility conflicts with declared project role: ' + path + ' / ' + row['name'])
            effects = row.get('effects')
            require(isinstance(effects, list) and all(isinstance(e, str) and e.strip() for e in effects),
                    'Responsibility effects must be named: ' + path)
            require(project['role'] not in {'core', 'helper'} and row['kind'] not in {'pure-policy', 'pure-helper'}
                    or not effects, 'Core/pure responsibility cannot own runtime effects: ' + path)
            provides = row.get('provides', [])
            require(isinstance(provides, list) and all(isinstance(c, str) and c.strip() for c in provides),
                    'Provided capabilities must be named: ' + path)
            for capability in provides:
                require(any(b['implementationProject'] == path and b['capability'] == capability
                            and b['implementation'] == row['name'] for b in bindings),
                        'Missing planned capability binding: ' + capability + ' -> ' + row['name'])
        contracts = test_compile_contracts(project, requires_review)
        missing = contracts - set(project.get('packageReferences', []))
        require(not missing, 'PKA020 missing direct test compile contracts: ' + path + '; add ' + ', '.join(sorted(missing)) + ' from selected central pins and synchronize packageReferences')


def validate_manifest(root, manifest):
    """Validate the planned compilation graph without restore, builds or source mutation.

    A manifest declares selection, not semantic ownership proof. Compiled checks and
    actual registration/resolution/lifetime tests remain required after implementation.
    """
    root = root.resolve()
    composition = manifest.get('runtimeComposition')
    require(isinstance(composition, dict), 'Declare runtimeComposition in eng/architecture.json')
    rows = composition.get('projects')
    require(isinstance(rows, list), 'Architecture projects must be a list')
    projects = {}
    for project in rows:
        require(isinstance(project, dict) and isinstance(project.get('path'), str), 'Architecture project requires a path')
        path = project['path']
        require(path.endswith('.csproj') and path == Path(path).as_posix() and not Path(path).is_absolute(),
                'Architecture project must use a repository-relative .csproj path: ' + path)
        inside(root, path)
        require(path.casefold() not in {p.casefold() for p in projects}, 'Duplicate architecture project identity: ' + path)
        validate_project_role(project.get('role'), path)
        require('persistenceOwnerNamespaces' not in project,
                'A namespace waiver cannot replace a provider compilation boundary: ' + path)
        projects[path] = project
    bindings = composition.get('bindings', [])
    require(isinstance(bindings, list), 'Architecture bindings must be a list')
    identities = set()
    for binding in bindings:
        require(isinstance(binding, dict), 'Architecture binding must be an object')
        capability = binding.get('capabilityProject')
        implementation = binding.get('implementationProject')
        require(capability in projects and implementation in projects, 'Binding projects must exist in the planned graph')
        require(capability != implementation, 'Capability and implementation require distinct compilation projects')
        require(projects[capability]['role'] == 'core', 'Binding capability must have a Core role: ' + capability)
        require(projects[implementation]['role'] in CAPABILITY_IMPLEMENTATION_ROLES,
                'Binding implementation requires an implementation/provider/bridge role: ' + implementation)
        for key in ('capability', 'implementation', 'registration'):
            require(isinstance(binding.get(key), str) and bool(binding[key].strip()), 'Binding requires ' + key)
        identity = (capability, binding['capability'], implementation, binding['implementation'])
        require(identity not in identities, 'Duplicate capability binding')
        identities.add(identity)
        if 'projectReferences' in projects[implementation]:
            require(capability in projects[implementation]['projectReferences'], 'Binding implementation must reference its Core capability project')
    validate_responsibilities(projects, bindings)
    authorized = set()
    for edge in composition.get('coreReferences', []):
        require(edge.get('fromProject') in projects and edge.get('toProject') in projects,
                'Core exception projects must exist in the planned graph')
        require(projects[edge['fromProject']]['role'] == projects[edge['toProject']]['role'] == 'core',
                'Core exception cannot relabel implementation dependencies')
        require(bool(edge.get('rationale', '').strip()), 'Core exception requires a scoped engineering rationale')
        require(inside(root, edge['verification']).is_file(), 'Core exception test does not exist')
        authorized.add((edge['fromProject'], edge['toProject']))
    edges = set()
    for path, project in projects.items():
        require(not Path(path).stem.endswith('.Core') or project['role'] == 'core', 'Core project role cannot be relabeled: ' + path)
        require(not Path(path).stem.endswith('.Api') or project['role'] == 'implementation', 'API project must have an implementation role: ' + path)
        packages = project.get('packageReferences', [])
        require(isinstance(packages, list) and all(isinstance(p, str) for p in packages), 'Package references must be a list of identities')
        require(not any(p.lower().startswith(PERSISTENCE_PACKAGE_PREFIXES) for p in packages)
                or project['role'] in {'provider', 'test'}, 'Persistence packages must stay in their owning provider/tests: ' + path)
        if project['role'] == 'core':
            require(not any(p.lower().startswith(FORBIDDEN_CORE_PACKAGE_PREFIXES) for p in packages), 'Planned Core leaks a runtime/provider dependency: ' + path)
        references = project.get('projectReferences', [])
        build_references = project.get('buildProjectReferences', [])
        require(all(isinstance(items, list) and all(isinstance(item, str) for item in items)
                    and len(set(items)) == len(items) for items in (references, build_references)),
                'Project and build references must be distinct lists of project identities')
        require(not set(references) & set(build_references), 'A project edge cannot be both CLR and build-only: ' + path)
        for target in references:
            require(target in projects and projects[target]['role'] in ALLOWED_ROLE_REFERENCES[project['role']],
                    f'Forbidden dependency: {path} -> {target}')
            require(project['role'] != projects[target]['role'] or project['role'] != 'core'
                    or (path, target) in authorized, 'Undecided Core-to-Core dependency')
            edges.add((path, target))
        for target in build_references:
            require(target in projects and target != path, 'Build dependency needs a distinct declared project owner: ' + path)
            edges.add((path, target))
    validate_cycles(projects, edges)
    from build_output_recipe import declarations
    for path, project in projects.items():
        if 'buildOutputCopies' in project:
            declarations(root, path, projects)
    return projects


def validate_cycles(projects, edges):
    def visit(node, active, visited):
        require(node not in active, f'Architecture dependency cycle at {node}')
        if node in visited:
            return
        active.add(node)
        for source, target in edges:
            if source == node:
                visit(target, active, visited)
        active.remove(node)
        visited.add(node)
    visited = set()
    for node in projects:
        visit(node, set(), visited)


def validate_planned(root, manifest, require_responsibilities=False):
    projects = validate_manifest(root, manifest)
    validate_responsibilities(projects, manifest['runtimeComposition'].get('bindings', []), require_responsibilities)
    for path, project in projects.items():
        if not (require_responsibilities is True or path in (require_responsibilities or ())):
            continue  # Unrelated retained declarations keep their existing scope.
        name = Path(path).stem
        require(project['role'] != 'core' or name.endswith('.Core'),
                'PKA023 planned Core project requires its .Core identity: ' + path)
        require('feature' not in name.casefold().split('.'),
                'PKA023 use domain/provider language instead of a generic .Feature project segment: ' + path)
        if 'packageId' in project:
            require(project['packageId'] == name, 'PKA023 planned project/package identity differs: ' + path)
    required_contracts = {p: test_compile_contracts(row) for p, row in projects.items()
                          if test_compile_contracts(row)}
    if required_contracts:
        from central_packages import central_package_versions
        pins = central_package_versions(root)
        for path, contracts in required_contracts.items():
            missing = {c for c in contracts if c.casefold() not in pins}
            require(not missing, 'PKA020 missing selected central test contract pins: ' + path + '; ' + ', '.join(sorted(missing)))
    physical = {p.relative_to(root).as_posix() for directory in ('src', 'tests')
                for p in (root / directory).rglob('*.csproj') if not {'obj', 'bin'} & set(p.parts)}
    require(physical <= set(projects), 'Assign an architectural role to new projects in eng/architecture.json: '
            + ', '.join(sorted(physical - set(projects))))
    return projects


def validate_graph(root, manifest, evaluated, compiled):
    projects = validate_manifest(root, manifest)
    require(set(evaluated) == set(projects), 'Evaluated graph must cover every declared project')
    assemblies = {a['name']: a for a in compiled}
    require(len(assemblies) == len(compiled), 'Assembly identities must be unique')
    owners = {evaluated[p]['Properties']['AssemblyName']: p for p in projects}
    require(len(owners) == len(projects) and set(owners) == set(assemblies), 'Compiled inventory differs from evaluated projects')
    edges = set()
    authorized = set()
    for edge in manifest['runtimeComposition'].get('coreReferences', []):
        require(bool(edge.get('rationale', '').strip()), 'Core exception requires a scoped engineering rationale')
        require(inside(root, edge['verification']).is_file(), 'Core exception test does not exist')
        authorized.add((edge['fromProject'], edge['toProject']))
    for relative, project in projects.items():
        data = evaluated[relative]
        friend_type = 'System.Runtime.CompilerServices.InternalsVisibleToAttribute'
        require(not data['Items'].get('InternalsVisibleTo')
                and not any(item.get('Identity') in {friend_type, friend_type.removesuffix('Attribute')}
                            for item in data['Items'].get('AssemblyAttribute', [])),
                'PKA021 friend access is forbidden: ' + relative
                + '; test public capabilities through production registration')
        require(friend_type not in assemblies[data['Properties']['AssemblyName']].get('attributes', []),
                'PKA021 compiled friend access is forbidden: ' + relative
                + '; keep implementation state private and exercise public capabilities')
        refs, build_refs = set(), set()
        for item in data['Items'].get('ProjectReference', []):
            path = Path(item.get('FullPath') or inside(root, relative).parent / item['Identity']).resolve()
            require(path.is_relative_to(root), 'Evaluated project reference escapes repository')
            (build_refs if is_build_reference(item) else refs).add(path.relative_to(root).as_posix())
        require('projectReferences' not in project or refs == set(project['projectReferences']), f'Evaluated references differ from accepted graph: {relative}')
        require(build_refs == set(project.get('buildProjectReferences', [])), f'Evaluated build references differ from accepted graph: {relative}')
        edges.update((relative, target) for target in build_refs)
        packages = set()
        for item in data['Items'].get('PackageReference', []):
            # Verified private engineering imports are outside the consumer runtime graph.
            origin = item.get('DefiningProjectFullPath')
            if (item['Identity'] == 'Orbyss.Foundation.Analyzers' and origin
                    and Path(origin).resolve() == (root / 'eng/ProgramKit.Build.props').resolve()):
                assets = {asset.strip().lower() for asset in item.get('IncludeAssets', '').split(';')}
                require(item.get('PrivateAssets', '').lower() == 'all'
                        and assets and not assets & {'compile', 'all', ''},
                        'Managed analyzer must remain private and outside compile assets')
                continue
            if (item['Identity'] == 'Orbyss.Foundation.Build' and origin
                    and Path(origin).resolve() == (root / 'eng/ProgramKit.Build.targets').resolve()):
                assets = {asset.strip().lower() for asset in item.get('IncludeAssets', '').split(';')}
                require(item.get('PrivateAssets', '').lower() == 'all'
                        and assets == {'build', 'buildtransitive'},
                        'Managed descriptor builder must remain private with only build assets')
                continue
            packages.add(item['Identity'])
        require('packageReferences' not in project or packages == set(project['packageReferences']), f'Evaluated package references differ: {relative}')
        require(test_compile_contracts(project) <= packages,
                'PKA020 evaluated direct test compile contracts differ from responsibilities: ' + relative)
        persistence_packages = {name for name in packages if name.lower().startswith(PERSISTENCE_PACKAGE_PREFIXES)}
        require(not persistence_packages or project['role'] in {'provider', 'test'},
                'Persistence packages must stay in their owning provider/tests: ' + relative)
        design = next((item for item in data['Items'].get('PackageReference', []) if item['Identity'] == 'Microsoft.EntityFrameworkCore.Design'), None)
        require(design is None or design.get('PrivateAssets', '').lower() == 'all', 'EF Design must remain private engineering tooling: ' + relative)
        actual = assemblies[data['Properties']['AssemblyName']]
        require(project['role'] in {'provider', 'test'} or not any(
            name.lower().startswith(PERSISTENCE_PACKAGE_PREFIXES) for name in actual['references']),
            'Persistence compiled dependencies must stay in their owning provider/tests: ' + relative)
        require(project['role'] in {'core', 'test'} or not any('.Core.' in t['name'] or t['name'].startswith('Core.')
                for t in actual['types']), 'Core types require a separate Core compilation project: ' + relative)
        require(project['role'] in {'implementation', 'test'} or not any('.Api.' in t['name'] or t['name'].startswith('Api.')
                for t in actual['types']), 'API types require a separate API implementation project: ' + relative)
        compiled_refs = {owners[name] for name in actual['references'] if name in owners}
        require(compiled_refs <= refs, f'Compiled project edge is absent from declared/evaluated graph: {relative}')
        if project['role'] == 'core':
            require(not any(name.lower().startswith(FORBIDDEN_CORE_PACKAGE_PREFIXES) for name in set(actual['references']) | packages),
                    f'Compiled Core leaks a runtime/provider dependency: {relative}')
        for target in refs | compiled_refs:
            require(target in projects and projects[target]['role'] in ALLOWED_ROLE_REFERENCES[project['role']],
                    f'Forbidden dependency: {relative} -> {target}')
            if project['role'] == projects[target]['role'] == 'core':
                require((relative, target) in authorized, 'Undecided Core-to-Core dependency')
            edges.add((relative, target))
    validate_cycles(projects, edges)
    by_project = {p: {t['name']: t for t in assemblies[evaluated[p]['Properties']['AssemblyName']]['types']} for p in projects}
    type_records = [t for a in compiled for t in a['types'] if t['name'] != '<Module>']
    all_types = {}
    for item in type_records:
        all_types.setdefault(item['name'], []).append(item)
    def implements(name, capability, seen):
        if name == capability:
            return True
        if name in seen or name not in all_types:
            return False
        seen.add(name)
        candidates = all_types[name]
        require(len(candidates) == 1,
                'Ambiguous capability type names need an assembly-aware equivalent verifier')
        item = candidates[0]
        return any(implements(parent, capability, seen) for parent in [*item['interfaces'], item['baseType']])
    for binding in manifest['runtimeComposition'].get('bindings', []):
        capability = by_project[binding['capabilityProject']].get(binding['capability'])
        implementation = by_project[binding['implementationProject']].get(binding['implementation'])
        require(capability and capability['isInterface'] and implementation and not implementation['isInterface'], 'Binding must name real compiled interface and implementation types')
        require(implements(binding['implementation'], binding['capability'], set()), 'Compiled provider does not implement its capability')
        owner, separator, method = binding['registration'].rpartition('.')
        require(separator and method in by_project[binding['implementationProject']].get(owner, {}).get('methods', []),
                'Binding registration entry point does not exist in the implementation assembly')
    listed = {(b['capabilityProject'], b['capability'], b['implementationProject'], b['implementation'])
              for b in manifest['runtimeComposition'].get('bindings', [])}
    capabilities = [(p, t['name']) for p in projects if projects[p]['role'] == 'core'
                    for t in by_project[p].values() if t['isInterface']]
    for path in projects:
        if projects[path]['role'] not in CAPABILITY_IMPLEMENTATION_ROLES:
            continue
        for item in by_project[path].values():
            if item['isInterface'] or item.get('isAbstract', False):
                continue
            for owner, capability in capabilities:
                if any(implements(parent, capability, set()) for parent in [*item['interfaces'], item['baseType']]):
                    require((owner, capability, path, item['name']) in listed,
                            f'Unlisted active capability binding: {capability} -> {item["name"]} in {path}')
    return {'evaluated-and-compiled-graph', 'compiled-capability-bindings'}


def evaluate_project(root, relative, configuration='Debug', version=None, framework=None):
    """Query actual imported/conditional settings without executing a target or restore.

    This is evaluation, not compiled dependency or runtime acceptance. MSBuild
    remains the native project owner; callers must select trusted repository input.
    """
    path = inside(root, relative)
    require(path.is_file(), 'Missing project for native evaluation: ' + relative)
    require(bool(re.fullmatch(r'[A-Za-z0-9_. -]+', configuration)), 'Select one native configuration identity')
    if framework:
        declared = evaluate_project(root, relative, configuration, version)
        properties = declared['Properties']
        targets = (properties.get('TargetFrameworks') or properties.get('TargetFramework', '')).split(';')
        require(framework in targets, 'Selected target framework is not declared by the project')
        if not properties.get('TargetFrameworks'):
            return declared
    from owned_scratch import native_path
    command = ['dotnet', 'msbuild', native_path(path), '-nologo', f'-p:Configuration={configuration}',
               '-getProperty:AssemblyName,TargetPath,Configuration,ManagePackageVersionsCentrally,TargetFramework,TargetFrameworks,NETCoreSdkVersion,MSBuildProjectFullPath,FoundationSourceReadability,FoundationSourceReadabilityContract,RunAnalyzers,RunAnalyzersDuringBuild,EnableNETAnalyzers,EnforceCodeStyleInBuild,GenerateMSBuildEditorConfigFile,SkipCompilerExecution,NoWarn,WarningsNotAsErrors,DesignTimeBuild,ProvideCommandLineArgs',
               '-getItem:ProjectReference,PackageReference,PackageVersion,FrameworkReference,InternalsVisibleTo,AssemblyAttribute,Compile']
    if version:
        command.append('-p:Version=' + version)
    if framework:
        require(bool(re.fullmatch(r'[A-Za-z0-9.\-]+', framework)), 'Select a native target framework identity')
        command.append('-p:TargetFramework=' + framework)
    result = subprocess.run(command, cwd=native_path(root), capture_output=True, text=True, encoding='utf-8',
                            check=True, timeout=120)
    return json.loads(result.stdout)


def execute(root, manifest, configuration, feature=None, build_subject=None, version=None):
    validate_planned(root, manifest)
    declared = [p['path'] for p in manifest['runtimeComposition']['projects']]
    require(len(set(declared)) == len(declared), 'Duplicate architecture project identity')
    physical = {p.relative_to(root).as_posix() for directory in ('src', 'tests')
                for p in (root / directory).rglob('*.csproj') if not {'obj', 'bin'} & set(p.parts)}
    require(physical <= set(declared), 'Assign an architectural role to new projects in eng/architecture.json: '
            + ', '.join(sorted(physical - set(declared))))
    require(all(p['role'] in ALLOWED_ROLE_REFERENCES for p in manifest['runtimeComposition']['projects']),
            'Unknown architecture role')
    # One fresh build session owns the graph inspected below. There is no
    # --no-build acceptance switch and no reliance on cached DLL timestamps.
    if build_subject:
        subject = inside(root, build_subject)
        require(subject.is_file() and subject.suffix in {'.sln', '.slnx'}, 'Build subject must be a repository solution')
        listed = subprocess.run(['dotnet', 'sln', str(subject), 'list'], cwd=root, capture_output=True,
                                text=True, encoding='utf-8', check=True, timeout=60).stdout
        covered = {(subject.parent / line.strip().replace('\\', '/')).resolve() for line in listed.splitlines()
                   if line.strip().endswith('.csproj')}
        require({inside(root, p) for p in declared} <= covered, 'Build solution must include every declared architecture project')
        arguments = ['dotnet', 'build', str(subject), '--no-restore', '--configuration', configuration,
                     '--nologo', '-v:q']
        if version:
            arguments.append('-p:Version=' + version)
        subprocess.run(arguments, cwd=root, capture_output=True, text=True, encoding='utf-8', check=True, timeout=300)
    elif declared:
        # A traversal builds all projects in one MSBuild process; shared references
        # are scheduled by MSBuild instead of separate dotnet build processes.
        import tempfile
        directory = root / 'artifacts/cache/architecture'
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='build-', dir=directory) as temporary:
            traversal = ET.Element('Project')
            target = ET.SubElement(traversal, 'Target', Name='Build')
            ET.SubElement(target, 'MSBuild', Projects=';'.join(str(inside(root, p)) for p in declared),
                          Targets='Build', BuildInParallel='true', Properties='Configuration=' + configuration)
            project = Path(temporary) / 'Architecture.proj'
            ET.ElementTree(traversal).write(project, encoding='utf-8', xml_declaration=True)
            subprocess.run(['dotnet', 'msbuild', str(project), '-nologo', '-verbosity:quiet', '-target:Build'],
                           cwd=root, capture_output=True, text=True, encoding='utf-8', check=True, timeout=300)
    if not declared:
        return validate_graph(root, manifest, {}, [])
    evaluated = {}
    paths = []
    for project in manifest['runtimeComposition']['projects']:
        path = inside(root, project['path'])
        data = evaluate_project(root, project['path'], configuration, version)
        evaluated[project['path']] = data
        assembly = Path(data['Properties']['TargetPath']).resolve()
        require(assembly.is_relative_to(root) and assembly.is_file(), 'Build current assemblies before architecture verification')
        paths.append(str(assembly))
    data_packages = {p['Identity'] for value in evaluated.values() for p in value['Items'].get('PackageReference', [])
                     if p['Identity'].startswith(('Microsoft.EntityFrameworkCore', 'Npgsql', 'Microsoft.Data.SqlClient', 'Microsoft.Data.Sqlite'))}
    if data_packages:
        require(any(p['role'] == 'provider' for p in manifest['runtimeComposition']['projects']), 'Persistence dependencies require a provider boundary')
    helper = Path(__file__).parent / 'assembly_graph/AssemblyGraph.csproj'
    result = subprocess.run(['dotnet', 'run', '--project', str(helper), '--configuration', 'Release',
                             '--no-launch-profile', '--', *paths], cwd=root, capture_output=True,
                            text=True, encoding='utf-8', check=True, timeout=180)
    lines = [line for line in result.stdout.splitlines() if line.startswith('[{')]
    require(len(lines) == 1, 'Compiled metadata reader produced ambiguous output')
    return validate_graph(root, manifest, evaluated, json.loads(lines[0]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--configuration', default='Debug')
    parser.add_argument('--output')
    parser.add_argument('--planned', action='store_true', help='Validate declared roles/edges/bindings without restore or builds')
    parser.add_argument('--build-subject', help='Build this complete solution once, then inspect its current graph')
    parser.add_argument('--version', help='Version property for the owned solution build')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    suite = ET.Element('testsuite', name='ProgramKit.Architecture')
    try:
        manifest_path = inside(root, args.manifest)
        if args.planned:
            validate_planned(root, read(manifest_path))
            checks = {'planned-compilation-graph'}
        else:
            require(bool(args.output), 'Compiled verification requires --output')
            checks = execute(root, read(manifest_path), args.configuration, manifest_path.parent.relative_to(root).as_posix(),
                             args.build_subject, args.version)
        for check in sorted(checks):
            ET.SubElement(suite, 'testcase', classname='ProgramKit.Architecture', name=check)
        status = 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        case = ET.SubElement(suite, 'testcase', classname='ProgramKit.Architecture', name='required-architecture')
        ET.SubElement(case, 'failure').text = str(error)
        detail = (error.stdout or '') + (error.stderr or '') if isinstance(error, subprocess.CalledProcessError) else ''
        print(str(error) + ('\n' + detail if detail else ''), file=sys.stderr)
        status = 2
    if args.output:
        output = inside(root, args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(suite).write(output, encoding='utf-8', xml_declaration=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())

"""Maintained evaluated-MSBuild and compiled metadata recipe; emits real JUnit cases.

Consumer registration/resolution and substitutability tests complement this structural
recipe. Metadata alone cannot establish runtime feature behavior.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from architecture_rules import (ALLOWED_ROLE_REFERENCES, FORBIDDEN_CORE_PACKAGE_PREFIXES,
                                CAPABILITY_IMPLEMENTATION_ROLES, PERSISTENCE_PACKAGE_PREFIXES)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def inside(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), 'Engineering path escapes repository: ' + str(relative))
    return path

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate_responsibilities(projects, bindings, required=False):
    """Reject declared contradictions; this never certifies the truth of a label."""
    allowed = {
        'core': {'contract', 'pure-policy', 'pure-helper'},
        'helper': {'pure-helper'},
        'implementation': {'runtime', 'http', 'pure-helper'},
        'provider': {'persistence', 'runtime', 'pure-helper'},
        'bridge': {'runtime', 'pure-helper'},
        'composition': {'composition', 'pure-helper'},
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
        require(project.get('role') in ALLOWED_ROLE_REFERENCES, 'Unknown architecture role: ' + path)
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
        require(isinstance(references, list), 'Project references must be a list')
        for target in references:
            require(target in projects and projects[target]['role'] in ALLOWED_ROLE_REFERENCES[project['role']],
                    f'Forbidden dependency: {path} -> {target}')
            require(project['role'] != projects[target]['role'] or project['role'] != 'core'
                    or (path, target) in authorized, 'Undecided Core-to-Core dependency')
            edges.add((path, target))
    validate_cycles(projects, edges)
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
        refs = set()
        for item in data['Items'].get('ProjectReference', []):
            path = Path(item.get('FullPath') or inside(root, relative).parent / item['Identity']).resolve()
            require(path.is_relative_to(root), 'Evaluated project reference escapes repository')
            refs.add(path.relative_to(root).as_posix())
        require('projectReferences' not in project or refs == set(project['projectReferences']), f'Evaluated references differ from accepted graph: {relative}')
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
        if projects[path]['role'] not in CAPABILITY_IMPLEMENTATION_ROLES | {'composition'}:
            continue
        for item in by_project[path].values():
            if item['isInterface'] or item.get('isAbstract', False):
                continue
            for owner, capability in capabilities:
                if any(implements(parent, capability, set()) for parent in [*item['interfaces'], item['baseType']]):
                    require((owner, capability, path, item['name']) in listed,
                            f'Unlisted active capability binding: {capability} -> {item["name"]} in {path}')
    return {'evaluated-and-compiled-graph', 'compiled-capability-bindings'}


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
        command = ['dotnet', 'msbuild', str(path), '-nologo', f'-p:Configuration={configuration}',
                   '-getProperty:AssemblyName,TargetPath,ManagePackageVersionsCentrally', '-getItem:ProjectReference,PackageReference,PackageVersion']
        if version:
            command.append('-p:Version=' + version)
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding='utf-8', check=True, timeout=120)
        data = json.loads(result.stdout)
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

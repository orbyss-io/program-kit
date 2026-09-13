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

from artifact_ownership import ALLOWED_ROLE_REFERENCES, FORBIDDEN_CORE_PACKAGE_PREFIXES
from phase_obligations import inside, read, require


def validate_graph(root, manifest, evaluated, compiled):
    projects = {p['path']: p for p in manifest['runtimeComposition']['projects']}
    require(set(evaluated) == set(projects), 'Evaluated graph must cover every declared project')
    assemblies = {a['name']: a for a in compiled}
    require(len(assemblies) == len(compiled), 'Assembly identities must be unique')
    owners = {evaluated[p]['Properties']['AssemblyName']: p for p in projects}
    require(len(owners) == len(projects) and set(owners) == set(assemblies), 'Compiled inventory differs from evaluated projects')
    edges = set()
    authorized = set()
    for edge in manifest['runtimeComposition'].get('coreReferences', []):
        decision = inside(root, edge['decision'])
        content = decision.read_text(encoding='utf-8')
        import re
        require(bool(re.search(r'(?im)^\s*(?:\*\*)?Status(?:\*\*)?\s*:\s*(?:\*\*)?Accepted\b', content)), 'Core exception requires an Accepted ADR')
        require(inside(root, edge['verification']).is_file(), 'Core exception test does not exist')
        authorized.add((edge['fromProject'], edge['toProject']))
    for relative, project in projects.items():
        data = evaluated[relative]
        refs = set()
        for item in data['Items'].get('ProjectReference', []):
            path = Path(item.get('FullPath') or inside(root, relative).parent / item['Identity']).resolve()
            require(path.is_relative_to(root), 'Evaluated project reference escapes repository')
            refs.add(path.relative_to(root).as_posix())
        require(refs == set(project['projectReferences']), f'Evaluated references differ from accepted graph: {relative}')
        packages = {item['Identity'] for item in data['Items'].get('PackageReference', [])}
        require(packages == set(project['packageReferences']), f'Evaluated package references differ: {relative}')
        actual = assemblies[data['Properties']['AssemblyName']]
        compiled_refs = {owners[name] for name in actual['references'] if name in owners}
        require(compiled_refs <= refs, f'Compiled project edge is absent from declared/evaluated graph: {relative}')
        if project['role'] == 'core':
            require(not any(name.lower().startswith(FORBIDDEN_CORE_PACKAGE_PREFIXES) for name in actual['references']),
                    f'Compiled Core leaks a runtime/provider dependency: {relative}')
        for target in refs | compiled_refs:
            require(target in projects and projects[target]['role'] in ALLOWED_ROLE_REFERENCES[project['role']],
                    f'Forbidden dependency: {relative} -> {target}')
            if project['role'] == projects[target]['role'] == 'core':
                require((relative, target) in authorized, 'Undecided Core-to-Core dependency')
            edges.add((relative, target))
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
    by_project = {p: {t['name']: t for t in assemblies[evaluated[p]['Properties']['AssemblyName']]['types']} for p in projects}
    type_records = [t for a in compiled for t in a['types'] if t['name'] != '<Module>']
    all_types = {t['name']: t for t in type_records}
    require(len(all_types) == len(type_records), 'Ambiguous duplicate compiled type names need an assembly-aware equivalent verifier')
    def implements(name, capability, seen):
        if name == capability:
            return True
        if name in seen or name not in all_types:
            return False
        seen.add(name)
        item = all_types[name]
        return any(implements(parent, capability, seen) for parent in [*item['interfaces'], item['baseType']])
    for binding in manifest['runtimeComposition'].get('bindings', []):
        capability = by_project[binding['capabilityProject']].get(binding['capability'])
        implementation = by_project[binding['implementationProject']].get(binding['implementation'])
        require(capability and capability['isInterface'] and implementation and not implementation['isInterface'], 'Binding must name real compiled interface and implementation types')
        require(implements(binding['implementation'], binding['capability'], set()), 'Compiled provider does not implement its capability')
        owner, separator, method = binding['registration'].rpartition('.')
        require(separator and method in by_project[binding['implementationProject']].get(owner, {}).get('methods', []),
                'Binding registration entry point does not exist in the implementation assembly')
    return {'evaluated-and-compiled-graph', 'compiled-capability-bindings'}


def execute(root, manifest, configuration, feature=None):
    evaluated = {}
    paths = []
    for project in manifest['runtimeComposition']['projects']:
        path = inside(root, project['path'])
        # A prior DLL's existence is not evidence for current sources. Rebuild the
        # evaluated inputs without admitting a network restore from verification.
        subprocess.run(['dotnet', 'build', str(path), '--no-restore', '--configuration', configuration,
                        '--nologo', '-v:q'], cwd=root, capture_output=True, text=True,
                       encoding='utf-8', check=True, timeout=180)
        command = ['dotnet', 'msbuild', str(path), '-nologo', f'-p:Configuration={configuration}',
                   '-getProperty:AssemblyName,TargetPath,ManagePackageVersionsCentrally', '-getItem:ProjectReference,PackageReference,PackageVersion']
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding='utf-8', check=True, timeout=120)
        data = json.loads(result.stdout)
        evaluated[project['path']] = data
        assembly = Path(data['Properties']['TargetPath']).resolve()
        require(assembly.is_relative_to(root) and assembly.is_file(), 'Build current assemblies before architecture verification')
        paths.append(str(assembly))
    data_packages = {p['Identity'] for value in evaluated.values() for p in value['Items'].get('PackageReference', [])
                     if p['Identity'].startswith(('Microsoft.EntityFrameworkCore', 'Npgsql', 'Microsoft.Data.SqlClient', 'Microsoft.Data.Sqlite'))}
    require(not data_packages or manifest.get('persistenceOwners'), 'Evaluated persistence packages require scoped data-owner admission')
    if manifest.get('persistenceOwners'):
        from repository_sync import provider
        persistence = provider('program-kit-dotnet/scripts/persistence_selection.py')
        # CLI callers locate the active feature; its accepted admission remains the authority.
        selection = persistence.resolve(root, feature)
        selection['owners'] = [owner for owner in selection['owners'] if owner['owner'] in manifest['persistenceOwners']]
        template = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files'
        persistence.validate_evaluated(selection, template, evaluated)
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
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    suite = ET.Element('testsuite', name='ProgramKit.Architecture')
    try:
        manifest_path = inside(root, args.manifest)
        checks = execute(root, read(manifest_path), args.configuration, manifest_path.parent.relative_to(root).as_posix())
        for check in sorted(checks):
            ET.SubElement(suite, 'testcase', classname='ProgramKit.Architecture', name=check)
        status = 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        case = ET.SubElement(suite, 'testcase', classname='ProgramKit.Architecture', name='required-architecture')
        ET.SubElement(case, 'failure').text = str(error)
        detail = (error.stdout or '') + (error.stderr or '') if isinstance(error, subprocess.CalledProcessError) else ''
        print(str(error) + ('\n' + detail if detail else ''), file=sys.stderr)
        status = 2
    output = inside(root, args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(output, encoding='utf-8', xml_declaration=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())

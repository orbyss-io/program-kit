"""Select and run native development tests without claiming application acceptance.

Full acceptance remains Invoke-RepositoryVerification.ps1's default. Unknown
ownership never falls back silently to every test, packaging or runtime startup.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
import os
import platform
import re
from pathlib import Path
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

from repository_architecture import inside, read, require, validate_planned

SHARED_INPUTS = ('global.json', '.editorconfig', 'NuGet.config', 'NuGet.Config',
                 '.globalconfig', '*.ruleset', '.config/**',
                 'Directory.Build.*', 'Directory.Packages.props', 'eng/ProgramKit.*',
                 'eng/*.json', 'eng/*.py', 'eng/*.ps1')

EXCLUDED_PARTS = {'bin', 'obj', '.git', 'artifacts', 'node_modules'}
CONTROLLED_ENVIRONMENT = ('DOTNET_ROLL_FORWARD', 'DOTNET_ROOT', 'DOTNET_ROOT_X64',
    'DOTNET_ROOT_X86', 'DOTNET_MULTILEVEL_LOOKUP', 'DOTNET_ADDITIONAL_DEPS',
    'DOTNET_SHARED_STORE', 'DOTNET_STARTUP_HOOKS', 'NUGET_PACKAGES',
    'NUGET_FALLBACK_PACKAGES', 'MSBuildSDKsPath', 'MSBUILD_EXE_PATH',
    'DOTNET_ENVIRONMENT', 'ASPNETCORE_ENVIRONMENT', 'DOTNET_SYSTEM_GLOBALIZATION_INVARIANT',
    'CI', 'Version', 'TargetFramework', 'TargetFrameworks', 'RuntimeIdentifier',
    'RuntimeIdentifiers', 'DefineConstants', 'LangVersion', 'Platform',
    'ContinuousIntegrationBuild', 'TreatWarningsAsErrors',
    'LANG', 'LC_ALL', 'TZ')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def configuration(root):
    path = root / 'eng/verification.json'
    value = read(path) if path.is_file() else {'schemaVersion': 1, 'testGroups': []}
    require(value.get('schemaVersion') == 1, 'PKV003 unsupported verification configuration')
    require('runnerReuse' not in value or isinstance(value['runnerReuse'], bool),
            'PKV003 runnerReuse must be a boolean')
    require(isinstance(value.get('testGroups', []), list), 'PKV003 testGroups must be an array')
    for group in value.get('testGroups', []):
        require(isinstance(group, dict), 'PKV003 testGroup must be an object')
        require(all(key not in group or isinstance(group[key], bool) for key in ('reuse', 'externalState')),
                'PKV003 reuse and externalState must be booleans')
    return value


def design_context(path):
    return path == '.specify/memory/constitution.md' or bool(re.fullmatch(
        r'specs/[^/]+/(?:spec|plan|tasks|research|data-model|quickstart)\.md|specs/[^/]+/checklists/[^/]+\.md', path))


def normalize(root, path):
    candidate = inside(root, path)
    require(candidate != root and not Path(path).is_absolute(), 'PKV001 use repository-relative input paths')
    return candidate.relative_to(root).as_posix()


def ownership_replacements(root, graph=None):
    """Explicit migration of retired test owners; no aliases for still-active tests."""
    rows = configuration(root).get('testOwnershipReplacements', [])
    require(isinstance(rows, list), 'PKV003 testOwnershipReplacements must be an array')
    if not rows:
        return {}
    graph = graph if graph is not None else validate_planned(root, read(root/'eng/architecture.json'))
    tests = {p for p, row in graph.items() if row['role'] == 'test'}
    mappings = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'predecessor', 'successors'},
                'PKV003 ownership replacement requires predecessor and successors')
        predecessor = row['predecessor']; successors = row['successors']
        require(isinstance(predecessor, str) and isinstance(successors, list) and successors
                and all(isinstance(p, str) for p in successors), 'PKV003 invalid test ownership replacement')
        predecessor = normalize(root, predecessor)
        successors = [normalize(root, p) for p in successors]
        require(predecessor.endswith('.csproj') and all(p.endswith('.csproj') for p in successors)
                and predecessor not in graph and not inside(root, predecessor).exists() and predecessor not in mappings
                and len(set(successors)) == len(successors),
                'PKV003 ambiguous ownership replacement; predecessor must be retired and unique')
        mappings[predecessor] = successors
    def leaves(project, active):
        require(project not in active, 'PKV003 cyclic test ownership replacements')
        if project not in mappings:
            require(project in tests, 'PKV003 replacement successors must be current declared test projects')
            return {project}
        return set().union(*(leaves(p, active | {project}) for p in mappings[project]))
    return {p: sorted(leaves(p, set())) for p in mappings}


def changed_inputs(root, baseline):
    require(bool(baseline) and not baseline.startswith('-'), 'PKV002 supply a valid Git baseline')
    subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', baseline + '^{commit}'],
                   check=True, capture_output=True, timeout=30)
    # A comparison to the worktree includes committed, staged and unstaged edits.
    # Disable rename collapsing so both the old and new owners are selected.
    changed = subprocess.check_output(['git', '-C', str(root), 'diff', '--no-renames', '--name-only',
                                      '-z', baseline, '--'], timeout=30)
    untracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--others',
                                        '--exclude-standard', '-z'], timeout=30)
    return sorted({normalize(root, p.decode('utf-8')) for p in (changed + untracked).split(b'\0') if p})


def test_arguments(arguments):
    """Filters are framework-owned; callers cannot turn a test run into discovery."""
    forbidden = {'--list-tests', '--help', '-h', '-?', '--info', '--ignore-exit-code',
                 '--minimum-expected-tests', '--no-build', '--no-restore', '--solution',
                 '--project', '--directory', '--test-modules', '--root-directory',
                 '--config-file', '--server', '--', '--property', '-p',
                 '--logger', '-l', '--results-directory', '--collect',
                 '--environment', '-e'}
    forbidden.update({'--report-xunit-trx', '--report-xunit-trx-filename', '--fail-skips'})
    for argument in arguments:
        key = argument.split('=', 1)[0].split(':', 1)[0].lower()
        require(not argument.startswith('@') and key not in forbidden,
                'PKV004 test arguments cannot bypass execution, zero-test failure or project selection: ' + argument)
    return list(arguments)


def reference_free_import(root, path, seen, allow_missing=False):
    """Allow ordinary literal build policy imports, never hidden graph edges."""
    path = path.resolve()
    require(path.is_relative_to(root) and (path.is_file() or allow_missing and not path.exists()),
            'PKV003 unavailable/external imports need a consumer evaluated graph adapter')
    if path in seen:
        return
    seen.add(path)
    if not path.is_file():
        return  # Preserve the missing literal optional import in the fingerprint.
    for node in ET.parse(path).getroot().iter():
        kind = node.tag.rsplit('}', 1)[-1]
        require(kind != 'ProjectReference',
                'PKV003 inherited/imported project graphs need a consumer evaluated graph adapter')
        if kind == 'Import':
            value = node.get('Project', '')
            require(value and not any(c in value for c in '$*;') and not node.get('Sdk'),
                    'PKV003 dynamic imports need a consumer evaluated graph adapter')
            condition = node.get('Condition', '').strip()
            optional = condition in {"Exists('" + value + "')", 'Exists("' + value + '")'}
            require(not condition or optional, 'PKV003 conditional imports need a consumer evaluated graph adapter')
            reference_free_import(root, path.parent / value.replace('\\', '/'), seen, optional)


def literal_edges(root, projects):
    """Do not narrow from stale or incomplete declared project edges.

    Dynamic/imported ProjectReference selection requires the consumer's evaluated
    graph adapter. Ordinary literal graphs are checked against project source.
    """
    imports = set()
    for relative, project in projects.items():
        require('projectReferences' in project, 'PKV003 affected selection needs complete projectReferences or an evaluated graph adapter')
        path = inside(root, relative)
        if not path.exists():
            continue  # Deleted project identity still selects its former callers.
        source = ET.parse(path).getroot()
        references = set()
        for node in source.iter():
            kind = node.tag.rsplit('}', 1)[-1]
            require(kind != 'Import', 'PKV003 imported project graphs need a consumer evaluated graph adapter')
            if kind != 'ProjectReference':
                continue
            value = node.get('Include', '')
            require(value and not any(c in value for c in '$*;') and not node.get('Condition'),
                    'PKV003 dynamic project references need a consumer evaluated graph adapter')
            target = (path.parent / value.replace('\\', '/')).resolve()
            require(target.is_relative_to(root), 'PKV001 project reference escapes repository')
            references.add(target.relative_to(root).as_posix())
        require(references == set(project['projectReferences']),
                'PKV003 projectReferences differ from source; update or evaluate the graph before narrowing tests: ' + relative)
    ancestors = {root}
    for relative in projects:
        ancestors.update(p for p in inside(root, relative).parents if p.is_relative_to(root))
    for parent in ancestors:
        for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props'):
            path = parent / name
            if not path.is_file():
                continue
            reference_free_import(root, path, imports)


def history(root):
    entries = []
    for path in (root / 'artifacts/tests/runs').glob('*/result.json'):
        value = read(path)
        if value.get('scope') not in {'Focused', 'Affected'}:
            continue
        arguments = tuple(value.get('testArguments', []))
        if value.get('schemaVersion') == 2:
            for outcome in value.get('outcomes', []):
                if outcome.get('status') == 'completed' and not evidence_valid(root, path, outcome):
                    outcome = {**outcome, 'status': 'incomplete'}
                entries.append((value.get('startedAtUtc', ''), path, arguments, outcome))
        elif value.get('schemaVersion') == 1:
            for project in value.get('projects', []):
                entries.append((value.get('startedAtUtc', ''), path, arguments,
                                {'project': project, 'status': value.get('status')}))
    return sorted(entries, key=lambda entry: (entry[0], str(entry[1])))


def unresolved_failures(root):
    """A full pass clears all project failures; a filtered pass clears only its coverage."""
    failed = {}
    entries = history(root)
    for _, path, arguments, outcome in entries:
        project = outcome['project']
        key = (project, arguments)
        if outcome.get('status') == 'completed':
            if not arguments:
                failed = {k: v for k, v in failed.items() if k[0] != project}
            else:
                failed.pop(key, None)
        else:
            failed[key] = {'project': project, 'testArguments': list(arguments),
                'reason': 'Previous failed, interrupted or incomplete execution needs successful coverage.',
                'run': path.relative_to(root).as_posix()}
    replacements = ownership_replacements(root)
    mapping_hash = digest(json.dumps(replacements, sort_keys=True).encode())
    def paid_successors(identity):
        paid = set()
        for _, path, arguments, outcome in entries:
            if arguments or outcome.get('status') != 'completed' or outcome['project'] not in identity['successors']:
                continue
            evidence = outcome.get('ownershipEvidence')
            if evidence in outcome.get('evidence', {}) and evidence_valid(root, path, outcome) and identity in read(inside(root, evidence)):
                paid.add(outcome['project'])
        return paid
    for key, row in list(failed.items()):
        successors = replacements.get(row['project'])
        if not successors:
            continue
        identity = {'predecessor': row['project'], 'testArguments': row['testArguments'],
                    'failedRun': row['run'], 'failureSha256': digest((root/row['run']).read_bytes()),
                    'successors': successors, 'mappingSha256': mapping_hash}
        paid = paid_successors(identity)
        if paid == set(successors):
            del failed[key]
        else:
            row.update(successors=successors, pendingSuccessors=sorted(set(successors) - paid),
                       ownershipCoverage=identity,
                       reason='Retired failed owner requires fresh unfiltered successor regression coverage.')
    obligations = list(failed.values())
    for predecessor, successors in replacements.items():
        identity = {'predecessor': predecessor, 'successors': successors, 'mappingSha256': mapping_hash}
        pending = sorted(set(successors) - paid_successors(identity))
        if pending:
            obligations.append({'kind': 'ownership-replacement', 'project': predecessor,
                'testArguments': [], 'successors': successors, 'pendingSuccessors': pending,
                'ownershipCoverage': identity,
                'reason': 'Retired test-owner mapping requires fresh unfiltered successor regression coverage.'})
    return obligations


def pending_failures(root, tests):
    failed = {p for row in unresolved_failures(root) for p in row.get('pendingSuccessors', [row['project']])}
    require(failed <= tests, 'PKV003 previously failing tests are no longer declared; resolve their ownership before narrowing')
    return failed


def select(root, scope, projects=(), changed_paths=(), baseline=None):
    root = root.resolve()
    manifest = read(root / 'eng/architecture.json')
    graph = validate_planned(root, manifest)
    physical = {p.relative_to(root).as_posix() for directory in ('src', 'tests')
                for p in (root / directory).rglob('*.csproj') if not {'bin', 'obj'} & set(p.parts)}
    require(physical <= set(graph), 'PKV003 assign architectural roles and edges to new projects before selecting affected tests')
    tests = {p for p, row in graph.items() if row['role'] == 'test'}
    replacements = ownership_replacements(root, graph)
    requested = {normalize(root, p) for p in projects}
    require(requested <= tests, 'PKV001 focused projects must have a test role in eng/architecture.json')
    paths = {normalize(root, p) for p in changed_paths}
    if scope == 'Focused':
        require(bool(requested), 'PKV002 Focused requires at least one named test project')
        selected = requested
    else:
        require(scope == 'Affected', 'PKV002 scope must be Focused or Affected')
        require(not requested, 'PKV002 Affected selects the complete dependent test set; use Focused for named projects')
        require(baseline or paths, 'PKV002 Affected needs a baseline or the complete changed input paths')
        if baseline:
            paths.update(changed_inputs(root, baseline))
        require(bool(paths), 'PKV002 no changed inputs; reuse current results rather than claiming a new test run')
        literal_edges(root, graph)
        known_input_owners = input_owners(root, graph)
        config = configuration(root)
        selected, affected = set(), set()
        context_paths = set()
        for path in paths:
            matched = False
            if any(fnmatchcase(path, pattern) for pattern in SHARED_INPUTS):
                selected.update(tests)
                matched = True
            owners = [p for p in graph if path == p or path.startswith(str(Path(p).parent).replace('\\', '/') + '/')]
            if owners:
                longest = max(len(str(Path(p).parent)) for p in owners)
                affected.update(p for p in owners if len(str(Path(p).parent)) == longest)
                matched = True
            retired = [p for p in replacements if path == p or path.startswith(Path(p).parent.as_posix() + '/')]
            if retired:
                longest = max(len(Path(p).parent.as_posix()) for p in retired)
                selected.update(s for p in retired if len(Path(p).parent.as_posix()) == longest for s in replacements[p])
                matched = True
            declared = {project for pattern, project in known_input_owners if fnmatchcase(path, pattern)}
            if declared:
                affected.update(declared)
                matched = True
            for group in config.get('testGroups', []):
                group_projects = set(group.get('projects', []))
                require(group_projects and group_projects <= tests, 'PKV003 testGroups must name declared test projects')
                if any(fnmatchcase(path, pattern) for pattern in group.get('inputs', [])):
                    selected.update(group_projects)
                    matched = True
            if not matched and design_context(path):
                context_paths.add(path)
                matched = True
            require(matched, 'PKV003 unknown verification input ' + path + '; map its tests or use a deliberate acceptance boundary')
        while True:
            expanded = affected | {p for p, row in graph.items() if set(row['projectReferences']) & affected}
            if expanded == affected:
                break
            affected = expanded
        selected.update(tests & affected)
        selected.update(pending_failures(root, tests))
        require(selected or len(context_paths) != len(paths),
                'PKV002 only design context changed; no native run was executed. Reuse current actual results and review the changed design.')
        require(bool(selected), 'PKV003 changed responsibilities have no dependent tests; add coverage or a scoped consumer adapter')
    return {'schemaVersion': 1, 'scope': scope, 'projects': sorted(selected), 'changedInputs': sorted(paths),
            'baseline': baseline, 'acceptanceEstablished': False}


def runner_kind(root):
    runner = configuration(root).get('runner', 'auto')
    require(runner in {'auto', 'mtp', 'vstest', 'adapter'}, 'PKV005 unsupported test runner')
    if runner == 'auto':
        runner = ('mtp' if read(root / 'global.json').get('test', {}).get('runner') ==
                  'Microsoft.Testing.Platform' else 'vstest')
    if runner == 'adapter':
        path = root / 'eng/verification-runner.py'
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
                'PKV005 runner adapter must be the contained regular eng/verification-runner.py file')
    return runner


def toolchain_identity(root):
    # Observe the selected SDK/runtime, not merely the desired version in global.json.
    native = subprocess.check_output(['dotnet', '--info'], cwd=root, timeout=30)
    return {'dotnet': digest(native), 'python': sys.version, 'platform': platform.platform(),
            'machine': platform.machine()}


def file_items(root, path):
    result = set()
    allowed_target_nodes = {'Target', 'PropertyGroup', 'ItemGroup', 'Error', 'Warning', 'Message'}
    tree = ET.parse(path).getroot()
    for target in tree.iter():
        if target.tag.rsplit('}', 1)[-1] == 'Target':
            for child in target:
                require(child.tag.rsplit('}', 1)[-1] in allowed_target_nodes,
                        'PKV003 custom build tasks need an evaluated graph adapter')
    for node in tree.iter():
        kind = node.tag.rsplit('}', 1)[-1]
        if kind not in {'Compile', 'Content', 'None', 'AdditionalFiles', 'EmbeddedResource', 'Analyzer'}:
            continue
        for attribute in ('Include', 'Update'):
            value = node.get(attribute)
            if not value:
                continue
            require(not Path(value).is_absolute() and not any(c in value for c in '$;'),
                    'PKV003 dynamic item inputs need an evaluated graph adapter')
            for matched in path.parent.glob(value.replace('\\', '/')):
                require(matched.resolve().is_relative_to(root), 'PKV003 external item inputs need an evaluated graph adapter')
                if matched.is_file():
                    result.add(matched)
            if not any(c in value for c in '*?'):
                target = (path.parent / value).resolve()
                require(target.is_relative_to(root), 'PKV003 external item inputs need an evaluated graph adapter')
                result.add(target)
    return result


def input_owners(root, graph):
    """Select callers of literal inherited imports/items, including deleted glob inputs."""
    owners = []
    for project in graph:
        target = inside(root, project)
        sources = {target}
        ancestors = [target.parent, *(p for p in target.parent.parents if p.is_relative_to(root))]
        for parent in ancestors:
            for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props'):
                path = parent / name
                owners.append((path.relative_to(root).as_posix(), project))
                if path.is_file():
                    reference_free_import(root, path, sources)
            for name in ('.editorconfig', '.globalconfig'):
                owners.append(((parent / name).relative_to(root).as_posix(), project))
        for path in sources:
            owners.append((path.relative_to(root).as_posix(), project))
            if not path.is_file():
                continue
            file_items(root, path)  # Fail closed before assuming complete literal ownership.
            for node in ET.parse(path).getroot().iter():
                if node.tag.rsplit('}', 1)[-1] not in {'Compile', 'Content', 'None', 'AdditionalFiles', 'EmbeddedResource', 'Analyzer'}:
                    continue
                for key in ('Include', 'Update'):
                    value = node.get(key)
                    if value:
                        item = (path.parent / value.replace('\\', '/')).resolve()
                        require(item.is_relative_to(root), 'PKV003 external item ownership needs an evaluated graph adapter')
                        owners.append((item.relative_to(root).as_posix(), project))
    return owners


def input_snapshot(root, project, graph, observation=None, stable_sources=False):
    """Conservative literal graph snapshot; dynamic build inputs must fail closed."""
    observation = observation if observation is not None else {}
    file_hashes = observation.setdefault('fileHashes', {})
    package_files = observation.setdefault('packageFiles', {})
    def file_hash(path):
        path = path.resolve()
        if path not in file_hashes:
            file_hashes[path] = digest(path.read_bytes()) if path.is_file() else None
        return file_hashes[path]
    closure = {project}
    while True:
        expanded = closure | {edge for p in closure for edge in graph[p]['projectReferences']}
        if expanded == closure:
            break
        closure = expanded
    paths, imports = set(), set()
    ancestors = {root}
    for relative in closure:
        target = inside(root, relative)
        directory = target.parent
        ancestors.update(p for p in directory.parents if p.is_relative_to(root))
        ancestors.add(directory)
        paths.add(target)
        if directory.exists():
            paths.update(p for p in directory.rglob('*') if p.is_file() and
                         not EXCLUDED_PARTS & set(p.relative_to(root).parts))
        if target.is_file():
            paths.update(file_items(root, target))
        # Restore assets and generated source are real build inputs, even when ignored.
        if not stable_sources:
            for name in ('project.assets.json', 'project.nuget.cache'):
                paths.add(directory / 'obj' / name)
            if (directory / 'obj').exists():
                paths.update((directory / 'obj').rglob('*.cs'))
    for parent in ancestors:
        for pattern in ('Directory.Build.*', 'Directory.Packages.props', '*.ruleset', '.editorconfig'):
            for path in parent.glob(pattern):
                if path.is_file():
                    paths.add(path)
                    if path.suffix in {'.props', '.targets'}:
                        reference_free_import(root, path, imports)
    paths.update(imports)
    for path in imports:
        if path.is_file():
            paths.update(file_items(root, path))
    for pattern in SHARED_INPUTS:
        paths.update(p for p in root.glob(pattern) if p.is_file())
    paths.update(p for p in (root / '.config').rglob('*') if p.is_file())
    # Managed/native harness, adapters and their policy are shared execution inputs.
    paths.update(p for p in (root / 'eng').rglob('*') if p.is_file() and
                 not EXCLUDED_PARTS & set(p.relative_to(root).parts) and '__pycache__' not in p.parts)
    for group in configuration(root).get('testGroups', []):
        if project in group.get('projects', []):
            for pattern in group.get('inputs', []):
                require(not Path(pattern).is_absolute() and '..' not in Path(pattern).parts,
                        'PKV003 test input patterns must stay inside the repository')
                # Enumerate only the explicit mapping prefix; generated ignored artifacts
                # are included when mapped, without scanning unrelated logs/package caches.
                prefix = []
                for part in Path(pattern).parts:
                    if any(c in part for c in '*?['):
                        break
                    prefix.append(part)
                base = inside(root, Path(*prefix)) if prefix else root
                listing = observation.setdefault('mappedFiles', {})
                if base not in listing:
                    listing[base] = tuple(base.rglob('*')) if base.is_dir() else (base,)
                paths.update(p for p in listing[base] if p.is_file() and
                             fnmatchcase(p.relative_to(root).as_posix(), pattern))
    snapshot = {}
    for path in sorted(paths):
        if stable_sources and 'obj' in path.relative_to(root).parts:
            continue  # Explicit restore/compiler-generated outputs can change during build.
        require(path.resolve().is_relative_to(root), 'PKV003 external or symlink build inputs need an evaluated graph adapter')
        snapshot[path.relative_to(root).as_posix()] = file_hash(path)
    for relative in closure:
        assets = inside(root, relative).parent / 'obj/project.assets.json'
        if not assets.is_file():
            continue
        resolved = read(assets)
        for library, entry in resolved.get('libraries', {}).items():
            if entry.get('type') != 'package':
                continue
            package = entry.get('path')
            require(package and not Path(package).is_absolute() and '..' not in Path(package).parts,
                    'PKV003 malformed restored package path')
            folders = [Path(p) / package for p in resolved.get('packageFolders', {})]
            available = next((p for p in folders if p.is_dir()), None)
            require(available is not None, 'PKV003 restored package inputs missing; restore before scoped checks')
            # Package assemblies, analyzers and buildTransitive files can change outside Git.
            if available not in package_files:
                package_files[available] = tuple(p for p in available.rglob('*') if p.is_file())
            for source in package_files[available]:
                snapshot['restored:' + library + '/' + source.relative_to(available).as_posix()] = file_hash(source)
    return snapshot


def fingerprints(root, projects, arguments, build_configuration, toolchain, stable_sources=False):
    graph = validate_planned(root, read(root / 'eng/architecture.json'))
    literal_edges(root, graph)
    names = configuration(root).get('environmentInputs', [])
    require(isinstance(names, list) and all(isinstance(n, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', n) for n in names),
            'PKV003 environmentInputs must list names of relevant controlled environment variables')
    require(not any(re.search(r'(?:TOKEN|PASSWORD|SECRET|CREDENTIAL|(?:^|_)KEY(?:$|_))', n.upper()) for n in names),
            'PKV003 environmentInputs must be non-secret controlled inputs; credentials cannot be snapshotted')
    result = {}
    observation = {}
    policy_names = {}
    argument_files, _ = argument_inputs(root, arguments)
    for project in projects:
        inputs = input_snapshot(root, project, graph, observation, stable_sources)
        project_names = set(CONTROLLED_ENVIRONMENT) | set(names)
        # MSBuild imports environment properties before evaluating repository XML.
        # Only the project's actual transitive/inherited policy contributes names.
        for relative in inputs:
            if relative.startswith('restored:') or Path(relative).suffix not in {'.csproj', '.props', '.targets'}:
                continue
            source = inside(root, relative)
            if source not in policy_names:
                policy_names[source] = set(re.findall(r'\$\(([A-Za-z_][A-Za-z0-9_]*)\)',
                    source.read_text(encoding='utf-8'))) if source.is_file() else set()
            project_names.update(policy_names[source])
        require(not any(re.search(r'(?:TOKEN|PASSWORD|SECRET|CREDENTIAL|(?:^|_)KEY(?:$|_))', n.upper()) and n in os.environ for n in project_names),
                'PKV003 secret environment properties cannot be snapshotted; isolate credential use from scoped native checks')
        # Non-secret values never enter evidence/console, only the combined fingerprint.
        environment = {name: digest(os.environ[name].encode()) if name in os.environ else None
                       for name in sorted(project_names)}
        state = {'inputs': inputs, 'environment': environment,
                 'toolchain': toolchain, 'configuration': build_configuration,
                 'testArguments': arguments, 'argumentInputs': argument_files, 'runner': runner_kind(root)}
        result[project] = digest(json.dumps(state, sort_keys=True).encode())
    return result


def argument_inputs(root, arguments):
    files, unknown = {}, False
    filters = {'--filter', '-f', '--filter-uid', '--filter-trait', '--filter-not-trait',
               '--filter-class', '--filter-method', '--filter-namespace', '--filter-query', '--filter-not-query'}
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        key, separator, value = argument.partition('=')
        if key in filters | {'--settings', '-s'}:
            if not separator:
                index += 1
                require(index < len(arguments), 'PKV004 test filter/settings argument requires a value')
                value = arguments[index]
            if key in {'--settings', '-s'}:
                relative = normalize(root, value)
                path = inside(root, relative)
                require(path.is_file(), 'PKV004 runsettings input must be an existing contained repository file')
                files[relative] = digest(path.read_bytes())
        else:
            # Unknown native flags may name files or dynamic execution inputs. Execute them
            # normally, but never infer that identical strings establish fresh coverage.
            unknown = True
        index += 1
    return files, unknown


def evidence_valid(root, path, outcome):
    if outcome.get('status') != 'completed' or not outcome.get('fingerprint') or outcome.get('executedTests', 0) < 1:
        return False
    logs = outcome.get('evidence', {})
    if not logs:
        return False
    for relative, expected in logs.items():
        candidate = inside(root, relative)
        if not candidate.is_file() or not candidate.resolve().is_relative_to(path.parent) or digest(candidate.read_bytes()) != expected:
            return False
    return True


def plan(root, selection, arguments, build_configuration='Debug', reason='', toolchain=None, force=False, native_report=None):
    arguments = test_arguments(arguments)
    require(native_report in (None, 'xunit-trx') and (native_report is None or runner_kind(root) == 'mtp'),
            'PKV004 native report requires the selected xUnit/MTP runner capability')
    require(selection['scope'] != 'Focused' or arguments or len(selection['projects']) == 1 or reason.strip(),
            'PKV002 unfiltered multi-project Focused checks need an explicit --reason for their dependency scope')
    current = fingerprints(root, selection['projects'], arguments, build_configuration,
                           toolchain if toolchain is not None else toolchain_identity(root))
    reusable = {}
    invalid = set()
    for _, path, coverage, outcome in history(root):
        project = outcome['project']
        if project not in current or coverage != tuple(arguments):
            continue
        reusable.pop(project, None)
        if outcome.get('fingerprint') == current[project] and evidence_valid(root, path, outcome) and (
                native_report is None or outcome.get('nativeReport') == native_report):
            reusable[project] = {'project': project, 'run': path.relative_to(root).as_posix(),
                                 'reason': 'Exact successful coverage and current input/toolchain/environment fingerprint match.'}
        else:
            invalid.add(project)
    unresolved = unresolved_failures(root)
    config = configuration(root)
    _, unknown_arguments = argument_inputs(root, arguments)
    unmanaged_environment = any(os.environ.get(n) for n in (
        'DOTNET_ADDITIONAL_DEPS', 'DOTNET_SHARED_STORE', 'DOTNET_STARTUP_HOOKS',
        'MSBuildSDKsPath', 'MSBUILD_EXE_PATH'))
    if unmanaged_environment or force:
        reusable.clear()  # External dynamic execution inputs are not safe to reuse.
    nonreusable = set()
    if unknown_arguments or runner_kind(root) == 'adapter' and config.get('runnerReuse') is not True:
        nonreusable.update(selection['projects'])
    for group in config.get('testGroups', []):
        if group.get('externalState') or group.get('reuse') is False:
            nonreusable.update(group.get('projects', []))
    for project in nonreusable:
        reusable.pop(project, None)
    # Never reuse a pass to conceal later unresolved failures, even with different coverage.
    for row in unresolved:
        reusable.pop(row['project'], None)
        for successor in row.get('pendingSuccessors', []):
            reusable.pop(successor, None)
    needed = [{'project': p, 'reason': ('Unresolved execution failure or retired-owner successor coverage.' if any(r['project'] == p or p in r.get('pendingSuccessors', []) for r in unresolved)
                 else 'Explicit fresh execution requested.' if force
                 else 'External dynamic environment inputs block result reuse.' if unmanaged_environment
                 else 'Native arguments or mutable external/provider checks have no safe reusable identity.' if p in nonreusable
                 else 'Inputs or retained evidence changed.' if p in invalid else 'No current successful result for this exact coverage.')}
              for p in selection['projects'] if p not in reusable]
    return {**selection, 'schemaVersion': 2, 'testArguments': arguments, 'configuration': build_configuration,
            'nativeReport': native_report,
            'reason': reason or ('Named Focused test projects.' if selection['scope'] == 'Focused'
                                else 'Affected dependencies from the complete retained implementation baseline.'),
            'fingerprints': current, 'needed': needed, 'reusable': list(reusable.values()), 'unresolved': unresolved}


def execute(root, selection, arguments, configuration='Debug', restore=False, reason='', force=False, native_report=None):
    arguments = test_arguments(arguments)
    observed_toolchain = toolchain_identity(root)
    selection = plan(root, selection, arguments, configuration, reason, observed_toolchain, force, native_report)
    print(json.dumps(selection))
    projects = [row['project'] for row in selection['needed']]
    if not projects:
        print('Reused current successful checks; no new execution receipt was created. ' +
              json.dumps(selection['reusable']))
        return selection
    runner = runner_kind(root)
    directory = root / 'artifacts/tests/runs' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    result = {**selection, 'status': 'running', 'projectsExecuted': projects,
              'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'steps': [],
              'outcomes': [{'project': p, 'status': 'pending'} for p in projects]}
    output = directory / 'result.json'
    build_logs = []
    def save():
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def run(command):
        step = {'command': command, 'status': 'running'}
        result['steps'].append(step); save()
        started = time.perf_counter()
        stdout = directory / f'{len(result["steps"]):02d}.stdout.log'
        stderr = directory / f'{len(result["steps"]):02d}.stderr.log'
        with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
            native = subprocess.run(command, cwd=root, stdout=out, stderr=err, timeout=900)
        step.update(exitCode=native.returncode, elapsedSeconds=round(time.perf_counter() - started, 3),
                    status='completed' if native.returncode == 0 else 'failed')
        save()
        require(native.returncode == 0, 'PKV006 scoped engineering command failed; inspect ' + str(directory))
        return [stdout, stderr]
    save()
    try:
        for project in projects:
            if restore:
                build_logs.extend(run(['dotnet', 'restore', project, '--locked-mode', '--configfile', str(root / 'NuGet.config')]))
        before_build = fingerprints(root, projects, arguments, configuration, toolchain_identity(root), stable_sources=True)
        if len(projects) == 1:
            build_logs.extend(run(['dotnet', 'build', projects[0], '--no-restore', '-c', configuration]))
        else:
            traversal = ET.Element('Project')
            target = ET.SubElement(traversal, 'Target', Name='Build')
            ET.SubElement(target, 'MSBuild', Projects=';'.join(str(inside(root, p)) for p in projects),
                          Targets='Build', BuildInParallel='true', Properties='Configuration=' + configuration)
            project = directory / 'SelectedTests.proj'
            ET.ElementTree(traversal).write(project, encoding='utf-8', xml_declaration=True)
            build_logs.extend(run(['dotnet', 'msbuild', str(project), '-nologo', '-verbosity:quiet', '-target:Build']))
        require(before_build == fingerprints(root, projects, arguments, configuration, toolchain_identity(root), stable_sources=True),
                'PKV006 source/configuration/toolchain changed during build; binaries cannot establish current coverage')
        built = fingerprints(root, projects, arguments, configuration, observed_toolchain)
        for index, outcome in enumerate(result['outcomes']):
            project = outcome['project']
            outcome.update(status='running', fingerprint=built[project]); save()
            if runner == 'mtp':
                report_arguments = []
                if native_report:
                    test_directory = directory / f'tests-{index}'
                    test_directory.mkdir()
                    report_arguments = ['--fail-skips', 'on', '--report-xunit-trx',
                                        '--report-xunit-trx-filename', 'result.trx',
                                        '--results-directory', str(test_directory)]
                logs = run(['dotnet', 'test', '--project', project, '--no-build', '-c', configuration,
                            '--minimum-expected-tests', '1', *report_arguments, *arguments])
                count = 1  # MTP enforces this lower bound; this is not a reported total.
                if native_report:
                    from test_results import test_results
                    trx = test_directory / 'result.trx'
                    require(trx.is_file(), 'PKV006 selected xUnit/MTP must retain its named native execution report')
                    cases = test_results(trx, 'trx')
                    require(cases and all(cases.values()), 'PKV006 selected xUnit/MTP cases are empty, skipped or failing')
                    count = len(cases)
                    outcome.update(nativeReport=native_report, nativeCases=list(cases))
                    logs.append(trx)
            elif runner == 'vstest':
                test_directory = directory / f'tests-{index}'
                logs = run(['dotnet', 'test', project, '--no-build', '--no-restore', '-c', configuration,
                            '--logger', 'trx;LogFileName=result.trx', '--results-directory', str(test_directory), *arguments])
                trx = test_directory / 'result.trx'
                require(trx.is_file(), 'PKV006 VSTest must produce its retained TRX execution evidence')
                counters = [n for n in ET.parse(trx).getroot().iter() if n.tag.rsplit('}', 1)[-1] == 'Counters']
                require(len(counters) == 1, 'PKV006 VSTest TRX must contain execution counters')
                count = int(counters[0].get('executed', '0'))
                require(int(counters[0].get('failed', '0')) == 0 and int(counters[0].get('error', '0')) == 0,
                        'PKV006 VSTest reported failed tests')
                require(int(counters[0].get('notExecuted', '0')) == 0,
                        'PKV006 VSTest skipped selected tests; required coverage remains unresolved')
                logs.append(trx)
            else:
                request = directory / f'adapter-{index}.request.json'
                response = directory / f'adapter-{index}.result.json'
                request.write_text(json.dumps({'schemaVersion': 1, 'repository': str(root),
                    'project': project, 'configuration': configuration, 'testArguments': arguments,
                    'outputDirectory': str(directory), 'restoreRequested': restore}), encoding='utf-8')
                logs = run([sys.executable, str(root / 'eng/verification-runner.py'),
                            '--request', str(request), '--result', str(response)])
                require(response.is_file(), 'PKV006 runner adapter must return actual execution evidence')
                native = read(response)
                require(native.get('schemaVersion') == 1 and native.get('status') == 'completed',
                        'PKV006 runner adapter did not report successful execution')
                count = native.get('executedTests', 0)
                require(isinstance(count, int) and not isinstance(count, bool), 'PKV006 invalid adapter test count')
                evidence = native.get('evidence', [])
                require(isinstance(evidence, list) and evidence, 'PKV006 runner adapter must retain native execution evidence')
                for relative in evidence:
                    path = inside(root, relative)
                    require(path.is_file() and path.resolve().is_relative_to(directory),
                            'PKV006 adapter evidence must be a regular file within this managed run')
                    logs.append(path)
                logs.extend([request, response])
            require(count >= 1, 'PKV006 selected module executed zero tests')
            after = fingerprints(root, [project], arguments, configuration, toolchain_identity(root))[project]
            require(after == built[project], 'PKV006 inputs or toolchain changed during test execution; rerun affected checks')
            ownership = [row['ownershipCoverage'] for row in selection['unresolved']
                         if not arguments and project in row.get('pendingSuccessors', [])]
            if ownership:
                ownership_path = directory/f'ownership-{index}.json'
                ownership_path.write_text(json.dumps(ownership, sort_keys=True) + '\n', encoding='utf-8')
                logs.append(ownership_path)
                outcome['ownershipEvidence'] = ownership_path.relative_to(root).as_posix()
            outcome.update(status='completed', executedTests=count,
                countKind='minimum-enforced' if runner == 'mtp' and not native_report else 'reported',
                evidence={p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in build_logs + logs})
            save()
        result['status'] = 'completed'
    except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
        result.update(status='failed', diagnostic=str(error))
        for outcome in result['outcomes']:
            if outcome['status'] != 'completed':
                outcome['status'] = 'failed'
        raise
    except KeyboardInterrupt:
        result.update(status='interrupted', diagnostic='Observed operator interruption; acceptance remains unestablished.')
        for outcome in result['outcomes']:
            if outcome['status'] != 'completed':
                outcome['status'] = 'interrupted'
        raise
    finally:
        result['finishedAtUtc'] = datetime.now(timezone.utc).isoformat()
        save()
    print('Scoped checks passed; application acceptance is not established. Logs: ' + str(directory))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--scope', choices=('Focused', 'Affected'), required=True)
    parser.add_argument('--project', action='append', default=[])
    parser.add_argument('--changed-path', action='append', default=[])
    parser.add_argument('--changed-from')
    parser.add_argument('--feature-dir', help='Context only; never used as the sole test-selection boundary')
    parser.add_argument('--configuration', default='Debug')
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--reason', default='', help='Dependency reason for unfiltered multi-project Focused coverage')
    parser.add_argument('--force', action='store_true', help='Execute fresh checks after external runtime/provider state changed')
    parser.add_argument('--native-report', choices=('xunit-trx',), help='Require selected xUnit/MTP named native results; reject skipped tests')
    parser.add_argument('--plan', action='store_true', help='Print selection without building or executing tests')
    parser.add_argument('--test-argument', action='append', default=[])
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        selection = select(root, args.scope, args.project, args.changed_path, args.changed_from)
        if args.feature_dir:
            selection['feature'] = normalize(root, args.feature_dir)
        arguments = test_arguments(args.test_argument)
        if args.plan:
            print(json.dumps(plan(root, selection, arguments, args.configuration, args.reason, force=args.force, native_report=args.native_report)))
        else:
            execute(root, selection, arguments, args.configuration, args.restore, args.reason, args.force, args.native_report)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

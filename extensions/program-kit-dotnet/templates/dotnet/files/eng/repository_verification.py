"""Select and run native development tests without claiming application acceptance.

Full acceptance remains Invoke-RepositoryVerification.ps1's default. Unknown
ownership never falls back silently to every test, packaging or runtime startup.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
import re
from pathlib import Path
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

from repository_architecture import inside, read, require, validate_planned

SHARED_INPUTS = ('global.json', '.editorconfig', 'NuGet.config', 'NuGet.Config',
                 'Directory.Build.*', 'Directory.Packages.props', 'eng/ProgramKit.*',
                 'eng/architecture.json', 'eng/architecture_rules.py', 'eng/verification.json')


def design_context(path):
    return path == '.specify/memory/constitution.md' or bool(re.fullmatch(
        r'specs/[^/]+/(?:spec|plan|tasks|research|data-model|quickstart)\.md|specs/[^/]+/checklists/[^/]+\.md', path))


def normalize(root, path):
    candidate = inside(root, path)
    require(candidate != root and not Path(path).is_absolute(), 'PKV001 use repository-relative input paths')
    return candidate.relative_to(root).as_posix()


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
                 '--config-file', '--server', '--', '--property', '-p'}
    for argument in arguments:
        key = argument.split('=', 1)[0].split(':', 1)[0].lower()
        require(not argument.startswith('@') and key not in forbidden,
                'PKV004 test arguments cannot bypass execution, zero-test failure or project selection: ' + argument)
    return list(arguments)


def reference_free_import(root, path, seen):
    """Allow ordinary literal build policy imports, never hidden graph edges."""
    path = path.resolve()
    require(path.is_relative_to(root) and path.is_file(),
            'PKV003 unavailable/external imports need a consumer evaluated graph adapter')
    if path in seen:
        return
    seen.add(path)
    for node in ET.parse(path).getroot().iter():
        kind = node.tag.rsplit('}', 1)[-1]
        require(kind != 'ProjectReference',
                'PKV003 inherited/imported project graphs need a consumer evaluated graph adapter')
        if kind == 'Import':
            value = node.get('Project', '')
            require(value and not any(c in value for c in '$*;') and not node.get('Sdk'),
                    'PKV003 dynamic imports need a consumer evaluated graph adapter')
            reference_free_import(root, path.parent / value.replace('\\', '/'), seen)


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


def pending_failures(root, tests):
    """A filtered success cannot erase a previously failing project regression."""
    latest = {}
    for path in sorted((root / 'artifacts/tests/runs').glob('*/result.json')):
        value = read(path)
        if value.get('schemaVersion') != 1 or value.get('scope') not in {'Focused', 'Affected'}:
            continue
        if value.get('status') == 'completed' and value.get('testArguments'):
            continue
        for project in value.get('projects', []):
            stamp = value.get('startedAtUtc', '')
            if project not in latest or stamp > latest[project][0]:
                latest[project] = (stamp, value.get('status'))
    failed = {project for project, (_, status) in latest.items() if status != 'completed'}
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
        configuration = root / 'eng/verification.json'
        config = read(configuration) if configuration.is_file() else {'schemaVersion': 1, 'testGroups': []}
        require(config.get('schemaVersion') == 1, 'PKV003 unsupported verification configuration')
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


def execute(root, selection, arguments, configuration='Debug', restore=False):
    arguments = test_arguments(arguments)
    require(read(root / 'global.json').get('test', {}).get('runner') == 'Microsoft.Testing.Platform',
            'PKV005 scoped fallback requires the selected MTP runner; use a consumer adapter for other test systems')
    directory = root / 'artifacts/tests/runs' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    result = {**selection, 'status': 'running', 'testArguments': arguments,
              'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'steps': []}
    output = directory / 'result.json'
    def save():
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def run(command):
        step = {'command': command, 'status': 'running'}
        result['steps'].append(step); save()
        started = time.perf_counter()
        with (directory / f'{len(result["steps"]):02d}.stdout.log').open('w', encoding='utf-8') as out, \
             (directory / f'{len(result["steps"]):02d}.stderr.log').open('w', encoding='utf-8') as err:
            native = subprocess.run(command, cwd=root, stdout=out, stderr=err, timeout=900)
        step.update(exitCode=native.returncode, elapsedSeconds=round(time.perf_counter() - started, 3),
                    status='completed' if native.returncode == 0 else 'failed')
        save()
        require(native.returncode == 0, 'PKV006 scoped engineering command failed; inspect ' + str(directory))
    save()
    try:
        for project in selection['projects']:
            if restore:
                run(['dotnet', 'restore', project, '--locked-mode', '--configfile', str(root / 'NuGet.config')])
        if len(selection['projects']) == 1:
            run(['dotnet', 'build', selection['projects'][0], '--no-restore', '-c', configuration])
        else:
            traversal = ET.Element('Project')
            target = ET.SubElement(traversal, 'Target', Name='Build')
            ET.SubElement(target, 'MSBuild', Projects=';'.join(str(inside(root, p)) for p in selection['projects']),
                          Targets='Build', BuildInParallel='true', Properties='Configuration=' + configuration)
            project = directory / 'SelectedTests.proj'
            ET.ElementTree(traversal).write(project, encoding='utf-8', xml_declaration=True)
            run(['dotnet', 'msbuild', str(project), '-nologo', '-verbosity:quiet', '-target:Build'])
        for project in selection['projects']:
            run(['dotnet', 'test', '--project', project, '--no-build', '-c', configuration,
                 '--', '--minimum-expected-tests', '1', *arguments])
        result['status'] = 'completed'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    except KeyboardInterrupt:
        result.update(status='interrupted', diagnostic='Observed operator interruption; acceptance remains unestablished.')
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
    parser.add_argument('--plan', action='store_true', help='Print selection without building or executing tests')
    parser.add_argument('--test-argument', action='append', default=[])
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        selection = select(root, args.scope, args.project, args.changed_path, args.changed_from)
        if args.feature_dir:
            selection['feature'] = normalize(root, args.feature_dir)
        arguments = test_arguments(args.test_argument)
        print(json.dumps(selection))
        if not args.plan:
            execute(root, selection, arguments, args.configuration, args.restore)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

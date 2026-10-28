"""Retained installed-layout native scaffold journey; no retired lifecycle or coding agent."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from owned_fixture import FixtureDirectory, filesystem_path, native_path


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n', encoding='utf-8')


def scenario(directory, *, installed_consumer=None):
    review = Path(filesystem_path(Path(directory).resolve())); review.mkdir(parents=True, exist_ok=True)
    consumer = Path(filesystem_path(installed_consumer)) if installed_consumer is not None else review / 'consumer'
    consumer.mkdir(parents=True, exist_ok=installed_consumer is not None)
    state_path = consumer / '.program-kit/managed.json'
    # In the source-copy journey, establish an independently pre-existing,
    # nonempty fictional native baseline before fixture authoring. True installed
    # callers retain their actual original state, captured before all setup.
    if not state_path.exists() and installed_consumer is None:
        marker = b'Fictional toolkit-owned baseline; source generation must preserve it.\n'
        write(consumer / 'eng/fictional-native-owned.txt', marker)
        write(state_path, {'schemaVersion': 2, 'files': {
            'eng/fictional-native-owned.txt': {'sha256': hashlib.sha256(marker).hexdigest()}}})
    initial_state = state_path.read_bytes() if state_path.is_file() else None
    protected = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in consumer.rglob('*') if path.is_file()}

    def author(path, value):
        """Author absent fixture inputs; preserve every pre-existing installed asset."""
        if path in protected:
            expected = value if isinstance(value, bytes) else (
                value if isinstance(value, str) else json.dumps(value, indent=2) + '\n').encode('utf-8')
            if path.read_bytes() != expected:
                raise ValueError('Pre-existing installed/authored asset preserved: ' + str(path))
            return
        write(path, value)
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    result = {'status': 'running', 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
              'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'fixtureSourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'commands': [], 'scope': 'Fictional existing native owners; real installed-layout preview/apply, analyzer compilation and independent application behavior. No HTTP/database/browser/product acceptance.'}
    started = time.perf_counter()

    def run(name, arguments, expected=0):
        before = time.perf_counter()
        child = subprocess.run(list(map(str, arguments)), cwd=native_path(consumer), capture_output=True,
                               text=True, encoding='utf-8', timeout=120)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'command': list(map(str, arguments)), 'cwd': native_path(consumer),
            'expectedExit': expected, 'actualExit': child.returncode, 'elapsedSeconds': round(time.perf_counter() - before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(), 'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        if child.returncode != expected:
            raise AssertionError(name + ': inspect retained actual command/streams')
        try: return json.loads(child.stdout)
        except ValueError: return child.stdout + child.stderr

    def snapshot(name, paths):
        for relative in paths:
            path = consumer / relative
            if path.is_file(): write(review / 'snapshots' / name / relative, path.read_bytes())

    try:
        if installed_consumer is None:
            for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
                shutil.copytree(filesystem_path(ROOT / 'extensions' / name), consumer / '.specify/extensions' / name,
                                ignore=shutil.ignore_patterns('__pycache__'))
        extensions = consumer / '.specify/extensions'
        scaffold = extensions / 'program-kit-governance/scripts/coding_scaffold.py'
        owners = {'core': 'src/Notes.Core/Notes.Core.csproj', 'runtime': 'src/Notes.Runtime/Notes.Runtime.csproj',
                  'api': 'src/Notes.Http/Notes.Http.csproj', 'provider': 'src/Notes.Store/Notes.Store.csproj',
                  'test': 'tests/Label.Tests/Label.Tests.csproj', 'frontend': 'web/app',
                  'generatedTypes': 'tools/openapi/labels/generated/types.ts'}
        # Actual native input, never a task-state, qualification receipt or approval substitute.
        if not state_path.exists():
            author(state_path, {'schemaVersion': 2, 'files': {}})
        author(consumer / 'Directory.Build.props', '''<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework>
<ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><GenerateDocumentationFile>true</GenerateDocumentationFile>
<TreatWarningsAsErrors>true</TreatWarningsAsErrors><FoundationSourceReadability>true</FoundationSourceReadability>
<NuGetAudit>false</NuGetAudit></PropertyGroup><ItemGroup>
<PackageReference Include="Orbyss.Foundation.Analyzers" Version="0.3.7" PrivateAssets="all"/></ItemGroup></Project>''')
        author(consumer / 'Directory.Build.targets', '<Project/>')
        author(consumer / 'NuGet.Config', '<configuration><packageSources><clear/></packageSources></configuration>')
        author(consumer / '.editorconfig', (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig').read_bytes())
        packages = {'core': [], 'runtime': ['Orbyss.Foundation.Execution'],
                    'api': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'],
                    'provider': ['Orbyss.Foundation.PostgreSql'], 'test': []}
        roles = {'core': 'core', 'runtime': 'implementation', 'api': 'implementation', 'provider': 'provider', 'test': 'test'}
        kinds = {'core': 'pure-policy', 'runtime': 'runtime', 'api': 'http', 'provider': 'persistence', 'test': 'test'}
        declarations = []
        for key, role in roles.items():
            project = consumer / owners[key]
            references = [] if key == 'core' else [owners['core']]
            if key == 'test': references += [owners[name] for name in ('runtime', 'api', 'provider')]
            items = ''.join('<PackageReference Include="' + name + '" Version="0.3.7"/>' for name in packages[key])
            if key == 'api': items += '<PackageReference Include="CShells.Abstractions" Version="0.0.31"/>'
            for target in references:
                import os
                relative = os.path.relpath(consumer / target, project.parent).replace('\\', '/')
                items += '<ProjectReference Include="' + relative + '"/>'
            if key != 'core': items += '<FrameworkReference Include="Microsoft.AspNetCore.App"/>'
            properties = '<OutputType>Exe</OutputType>' if key == 'test' else ''
            author(project, '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>' + properties + '</PropertyGroup><ItemGroup>' + items + '</ItemGroup></Project>')
            declarations.append({'path': owners[key], 'role': role, 'projectReferences': references,
                'responsibilities': [{'name': key + 'Labels', 'kind': kinds[key], 'effects': []}]})
        author(consumer / 'eng/architecture.json', {'runtimeComposition': {'projects': declarations}})
        author(consumer / 'web/app/package.json', {'name': 'fictional-labels', 'private': True})
        author(consumer / 'eng/openapi-contracts.json', {'contracts': ['contracts/labels.contract.json']})
        author(consumer / 'contracts/labels.contract.json', {'generator': {'generatedTypes': owners['generatedTypes']}, 'application': {'directory': owners['frontend']}})
        author(consumer / 'specs/001-label/owners.json', owners)
        author(consumer / 'specs/001-label/tasks.md', '# Fictional source-realization task\n- [ ] Inspect and realize the existing native label owners.\n')
        for source in (ROOT / 'tests/fixtures/typed-operation-runtime').glob('*.cs'):
            author(consumer / 'tests/Label.Tests/Labels' / source.name, source.read_bytes())

        def command(action='preview', digest=None, unit='typed-label'):
            return [sys.executable, scaffold, action, '--repository', '.', '--feature-dir', 'specs/001-label',
                    '--unit', unit, '--owners', 'specs/001-label/owners.json', *(['--plan-digest', digest] if digest else [])]

        state_before = (consumer / '.program-kit/managed.json').read_bytes()
        if initial_state is not None:
            assert state_before == initial_state, 'Original actual native state must survive fixture setup'
        tasks_before = (consumer / 'specs/001-label/tasks.md').read_bytes()
        plan = run('01-native-preview', command())
        paths = [row['path'] for row in plan['actions']]
        assert all(row['kind'] == 'create' for row in plan['actions']) and not plan['conflicts']
        assert all(not (consumer / path).exists() for path in paths)
        write(review / 'snapshots/preview.json', plan)

        # Partial/manual old-root adoption must be preserved before duplicate types exist.
        legacy = consumer / 'src/Notes.Core/ILabelOperations.cs'
        write(legacy, '// Independently authored earlier recipe; preserve.\n')
        original_legacy = legacy.read_bytes()
        conflict = run('02-legacy-preview', command(), 2)
        assert any(row.get('kind') == 'legacy-placement' for row in conflict['conflicts'])
        run('03-late-legacy-invalidates-preview', command('apply', plan['planDigest']), 2)
        assert legacy.read_bytes() == original_legacy and all(not (consumer / path).exists() for path in paths)
        snapshot('legacy-preserved', ['src/Notes.Core/ILabelOperations.cs']); legacy.unlink()

        applied = run('04-create-owned-source', command('apply', plan['planDigest']))
        assert set(applied['created']) == set(paths)
        snapshot('created', paths)
        repeat = run('05-identical-preview', command())
        assert all(row['kind'] == 'unchanged' for row in repeat['actions'])
        noop = run('06-idempotent-apply', command('apply', repeat['planDigest']))
        assert noop['created'] == [] and noop['transactionId'] is None
        build = ['dotnet', 'build', owners['test'], '--configuration', 'Release', '--nologo', '-m:1', '--disable-build-servers']
        execute = ['dotnet', 'run', '--project', owners['test'], '--configuration', 'Release', '--no-build', '--no-restore']
        run('07-actual-positive-native-build', build)
        positive = run('08-independent-application', execute)
        assert 'NATIVE_OUTER_DEADLINE_FRESHNESS_CALLER_AND_CONFIG_PASSED' in positive

        source = consumer / 'src/Notes.Runtime/Labels/LabelOperations.cs'
        original = source.read_bytes(); effect = b'await store.WriteAsync(value, deadline.Token);'
        assert original.count(effect) == 1, 'Preserve the independent missing-effect seam'
        source.write_bytes(original.replace(effect, b'// Deliberately omitted effect.'))
        run('09-negative-native-build', build)  # Compiler/setup failure cannot satisfy the negative.
        child = subprocess.run(execute, cwd=native_path(consumer), capture_output=True, text=True, encoding='utf-8', timeout=120)
        write(review / 'output/10-independent-negative.stdout.txt', child.stdout)
        write(review / 'output/10-independent-negative.stderr.txt', child.stderr)
        assert child.returncode != 0 and 'committed label representation' in child.stdout + child.stderr
        result['independentNegative'] = {'command': execute, 'exitCode': child.returncode,
            'marker': 'committed label representation', 'successfulNativeBuild': True}
        snapshot('invalid', ['src/Notes.Runtime/Labels/LabelOperations.cs'])
        source.write_bytes(original + b'\n// Consumer-authored customization; preserved by regeneration.\n')
        customized = source.read_bytes()
        conflict = run('11-customization-preview', command(), 2)
        assert conflict['conflicts'] and source.read_bytes() == customized
        run('12-customization-apply-preserves-source', command('apply', plan['planDigest']), 2)
        assert source.read_bytes() == customized
        run('13-manual-edit-native-build', build)
        positive = run('14-manual-edit-independent-application', execute)
        assert 'NATIVE_OUTER_DEADLINE_FRESHNESS_CALLER_AND_CONFIG_PASSED' in positive
        run('15-unsupported-unit-native-rejection', command(unit='unknown-pattern'), 2)
        snapshot('customized', paths)
        assert (consumer / '.program-kit/managed.json').read_bytes() == state_before
        assert (consumer / 'specs/001-label/tasks.md').read_bytes() == tasks_before
        assert all(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
                   for path, expected in protected.items()), 'Pre-existing installed source changed'
        result.update(status='passed', elapsedSeconds=round(time.perf_counter() - started, 3),
                      finalWorkingInputsDigest=input_snapshot()['digest'], created=paths,
                      managedStatePreserved=True, tasksPreserved=True, authoredSourcePreserved=True,
                      preexistingProtectedFiles=len(protected), managedStateBeforeSha256=hashlib.sha256(state_before).hexdigest(),
                      scope='Installed-layout native scaffold; actual selected analyzer builds and independent runtime oracle; no archive installation, HTTP/database/client/browser or human acceptance claim.')
        assert result['workingInputsDigest'] == result['finalWorkingInputsDigest'], 'Maintained source changed during fixture'
        write(review / 'index.md', '''# Native scaffold actual-output review

This fictional native-owner fixture runs installed-layout copies. It needs no retired task lifecycle or pattern ledger. The ordinary feature tasks remain untouched. Actual native HTTP/database/generated-client qualification retains its separate owner.

1. Inspect [native preview](output/01-native-preview.stdout.txt), [created tree](snapshots/created), [legacy conflict](output/02-legacy-preview.stdout.txt) and [late-file rejection](output/03-late-legacy-invalidates-preview.stdout.txt). Earlier authored source remains byte-identical; no duplicate is created.
2. Inspect [positive native build](output/07-actual-positive-native-build.stdout.txt) with the selected analyzer enabled, then [independent application behavior](output/08-independent-application.stdout.txt). Core/runtime/provider/API remain separately compiled and application tests mirror Labels ownership.
3. Compare [omitted-effect source](snapshots/invalid/src/Notes.Runtime/Labels/LabelOperations.cs), [successful negative build](output/09-negative-native-build.stdout.txt), and [actual behavioral failure](output/10-independent-negative.stderr.txt). The independently expected committed representation catches the missing write.
4. Inspect [customization preservation](output/12-customization-apply-preserves-source.stdout.txt) and [manual-edit behavior](output/14-manual-edit-independent-application.stdout.txt). New business source stays consumer-owned; native managed state and task progress remain byte-identical.

Exact commands, streams, hashes, source identities and costs remain in [results](results.json). Prior failed review directories are preserved. This proves exercised generation/preservation/application mechanics, not arbitrary semantic detection, agent obedience or product acceptance.
''')
        return result
    except BaseException as error:
        result.update(status='failed', failureType=type(error).__name__, elapsedSeconds=round(time.perf_counter() - started, 3)); raise
    finally:
        write(review / 'results.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--review', action='store_true'); args = parser.parse_args()
    if args.review:
        directory = ROOT / 'artifacts/f4-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
        print('Retained native scaffold review: ' + str(directory / 'index.md'), flush=True)
        scenario(directory)
    else:
        with FixtureDirectory() as directory: scenario(directory)


if __name__ == '__main__': main()

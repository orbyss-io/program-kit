"""Actual installed skill, cold native rebuild and deterministic eng deletion contract.

Fictional consumer only. No agent, application/service start or device provisioning.
Every child stream, including failed expectations, stays in this fixture's artifacts.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()
            and p.relative_to(root).parts[0] != 'eng'
            and not {'artifacts', '.git', 'bin', 'obj', '__pycache__'} & set(p.relative_to(root).parts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', default='artifacts')
    args = parser.parse_args()
    record = ROOT / 'artifacts' / ('de-' + uuid.uuid4().hex[:8])
    root = record / 'consumer space'
    root.mkdir(parents=True)
    started = time.monotonic()
    commands = []
    # Model the same explicit device preparation as CI setup-python without
    # changing the host/global PATH or installing/copying a runtime.
    child_environment = {**os.environ, 'PATH': str(Path(sys.executable).resolve().parent) + os.pathsep + os.environ['PATH'],
                         'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                         'DOTNET_CLI_TELEMETRY_OPTOUT': '1', 'DOTNET_NOLOGO': '1'}

    def run(label, argv, expected=0, cwd=root):
        begin = time.monotonic()
        result = subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=120,
                                env=child_environment)
        (record / (label + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
        (record / (label + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
        commands.append({'label': label, 'command': list(map(str, argv)), 'exitCode': result.returncode,
                         'elapsedSeconds': round(time.monotonic() - begin, 3)})
        (record / 'results.json').write_text(json.dumps({'commands': commands}, indent=2) + '\n')
        assert result.returncode == expected, label + ': inspect ' + str(record)
        return result

    def run_default(label, argv, cwd=root):
        if os.name != 'nt':
            return run(label, argv, cwd=cwd)
        # This host's CMD startup does not use inherited PATH overrides. Prepare
        # the fictional terminal itself, exactly as a human/CI prepares tools,
        # then run the unchanged native command. No product dispatch override.
        directories = [Path(sys.executable).parent, Path(shutil.which('dotnet')).parent,
                       Path(os.environ['SystemRoot']) / 'System32']
        path = os.pathsep.join(map(str, directories))
        assert not any(char in path for char in ('%', '"', '\r', '\n'))
        terminal = record / (label + '.cmd')
        terminal.write_text('@echo off\nset "PATH=' + path + '"\n'
                            + subprocess.list2cmdline(list(map(str, argv))) + '\n',
                            encoding='utf-8', newline='\r\n')
        return run(label, [os.environ['COMSPEC'], '/d', '/v:off', '/c', terminal], cwd=cwd)

    def remove_eng():
        target = (root / 'eng').resolve()
        assert target.parent == root.resolve() and target.name == 'eng'
        shutil.rmtree(target)

    try:
        # Install exact component archives through native Spec Kit bundle and
        # extension owners; the command becomes a real integration skill.
        from validate_package_smoke import extract
        from local_bundle_fixture import install_local_bundle
        import specify_cli
        version = (ROOT / 'VERSION').read_text().strip()
        assets = (ROOT / args.assets_dir).resolve()
        expanded = record / 'packages'
        for name in ('program-kit-tooling', 'program-kit-governance', 'program-kit-building-blocks',
                     'program-kit-dotnet', 'program-kit-governance-preset'):
            extract(assets / f'{name}-{version}.zip', expanded / name)
        bridge = [sys.executable, ROOT / 'scripts/invoke_specify.py', '--site-packages',
                  Path(specify_cli.__file__).parent.parent, '--']
        run('native-init', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                            '--script', 'py', '--ignore-agent-tools'])
        sources = {('extensions', name): expanded / name for name in
                   ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet')}
        sources[('presets', 'program-kit-governance-preset')] = expanded / 'program-kit-governance-preset'
        install_local_bundle(root, expanded / 'program-kit-tooling', bridge, run,
                             component_sources=sources, integration='codex')
        skill = root / '.agents/skills/speckit-program-kit-dotnet-regenerate-eng/SKILL.md'
        assert skill.is_file() and '${PWD}/scripts/regenerate_eng.py' in skill.read_text() and '.specify/extensions/program-kit-dotnet/scripts/regenerate_eng.py' not in skill.read_text()
        (root / '.gitattributes').write_text('# Authored attribute rule remains durable.\n*.consumer binary\n', newline='\n')
        installed = root / '.specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py'
        approvals = ['--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved']
        run('installed-engineering', [sys.executable, installed, '--target', root, '--web-profile', 'none', *approvals])
        assert (root / '.gitattributes').read_text().startswith('# Authored attribute rule remains durable.\n*.consumer binary\n')
        # App-owned source and overrides, written outside disposable eng.
        project = root / 'src/Probe'; project.mkdir(parents=True)
        (project / 'Probe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        (project / 'Program.cs').write_text('''#if !DISPOSABLE_ENG_PROBE
#error selected consumer policy was lost
#endif
/// <summary>Exercises the native selected build policy.</summary>
internal static class Program
{
    /// <summary>Returns success after actual compilation.</summary>
    private static int Main()
    {
        return 0;
    }
}
''')
        props = root / 'Directory.Build.props'
        props.write_text(props.read_text().replace('</Project>', '<PropertyGroup><DefineConstants>$(DefineConstants);DISPOSABLE_ENG_PROBE</DefineConstants></PropertyGroup></Project>'))
        (root / 'Consumer.slnx').write_text('<Solution><Project Path="src/Probe/Probe.csproj" /></Solution>')
        (root / 'scripts/consumer-script.py').write_bytes(b'# Consumer-authored script.\n')
        (root / 'tools/consumer-tool.txt').write_bytes(b'Consumer-authored helper source.\n')
        for name in ('.agents', '.specify'):
            target = (root / name).resolve()
            assert target.parent == root.resolve()
            shutil.rmtree(target)
        assert not (root / 'eng').exists(), 'installed source must have no eng authority'
        native = ['dotnet', 'build', 'Consumer.slnx', '--nologo', '--verbosity', 'minimal',
                  '-p:ProgramKitPythonCommand=' + sys.executable]
        baseline = run('cold-native-build', native)
        assert 'Probe.dll' in baseline.stdout
        assets = json.loads((project / 'obj/project.assets.json').read_text())
        identity = next(name for name in assets['libraries'] if name.startswith('Orbyss.Foundation.Analyzers/'))
        library = assets['libraries'][identity]
        package = next(path for folder in assets['packageFolders']
                       for path in (Path(folder) / library['path']).glob('*.nupkg'))
        # Actual SDK-owned NuGet metadata helper at its emitted tools/ location;
        # compare to the independently restored assets authority, not our recipe.
        hashed = run('native-package-hash-helper', [sys.executable, '-I', '-c',
            'import sys; from pathlib import Path; root=Path(sys.argv[1]); '
            'sys.path.insert(0,str(root/"scripts")); import release_bundle; '
            'print(release_bundle.nuget_content_hash(root,Path(sys.argv[2])))', root, package])
        assert hashed.stdout.strip() == library['sha512']
        assert list((root / 'artifacts/tools/nuget-content-hash').rglob('PackageHash.dll')), 'native helper was not actually compiled'
        first = {p.relative_to(root / 'eng').as_posix(): p.read_bytes() for p in (root / 'eng').rglob('*') if p.is_file()}
        protected = snapshot(root)
        remove_eng()
        graph_config = root / 'config/program-kit/restore-graph.json'
        graph_config.write_text(json.dumps({'schemaVersion': 1, 'adapter': 'native-msbuild',
            'configuration': 'Debug', 'sdkVersion': json.loads((root / 'global.json').read_text())['sdk']['version']}), newline='\n')
        protected = snapshot(root)
        graph_probe = '''import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
import native_restore_graph as graph
assert not graph.native_lock_document({'version':99,'dependencies':{}})
assert not graph.native_lock_document({'version':2,'dependencies':[]})
assert not graph.native_lock_document({'version':2,'dependencies':{},'foreign':'authored'})
environment={**os.environ,'NUGET_PACKAGES':sys.argv[3]}
try:
 result=graph.evaluate(Path(sys.argv[1]),['src/Probe/Probe.csproj'],environment)
 print('READONLY_NATIVE_GRAPH_PASSED')
except ValueError as error:
 print(str(error),file=sys.stderr)
 raise SystemExit(2)
'''
        graph_command = [sys.executable, '-I', '-c', graph_probe, root,
            ROOT / 'extensions/program-kit-building-blocks/scripts', next(iter(assets['packageFolders']))]
        observed = run('native-readonly-restore-graph', graph_command)
        assert 'READONLY_NATIVE_GRAPH_PASSED' in observed.stdout
        assert not (root / 'eng').exists() and protected == snapshot(root)
        build_targets = root / 'config/program-kit/build/ProgramKit.Build.targets'
        original_targets = build_targets.read_bytes()
        build_targets.write_text(build_targets.read_text().replace('/scripts/regenerate_eng.py', '/scripts/other.py'))
        rejected = run('altered-maintained-restore-hook-rejected', graph_command, 2)
        assert 'regeneration target differs' in rejected.stderr and not (root / 'eng').exists()
        build_targets.write_bytes(original_targets)
        project_file = project / 'Probe.csproj'; original_project = project_file.read_bytes()
        project_file.write_text(project_file.read_text().replace('</Project>',
            '<Target Name="FictionalRestoreHook" BeforeTargets="Restore"><WriteLinesToFile File="forbidden-hook.txt" Lines="bad"/></Target></Project>'))
        rejected = run('arbitrary-restore-hook-rejected', graph_command, 2)
        assert 'restore-target override/hook' in rejected.stderr
        assert not (root / 'eng').exists() and not (project / 'forbidden-hook.txt').exists()
        project_file.write_bytes(original_project)
        for name in ('architecture.json', 'unwritten-profile.json'):
            project_file.write_text(project_file.read_text().replace('</Project>',
                '<PropertyGroup><NuGetLockFilePath>$(MSBuildProjectDirectory)/../../config/program-kit/'
                + name + '</NuGetLockFilePath></PropertyGroup></Project>'))
            before_output_probe = snapshot(root)
            rejected = run('durable-restore-output-rejected-' + name, graph_command, 2)
            assert 'restore output would overwrite retained/foreign ownership' in rejected.stderr
            assert before_output_probe == snapshot(root) and not (root / 'eng').exists()
            project_file.write_bytes(original_project)
        assert not (root / 'config/program-kit/unwritten-profile.json').exists()
        # Force actual compilation, independently of incremental build timestamps.
        python_ready = run_default('default-python-readiness', ['python', '--version'])
        assert ('Python ' + (root / '.python-version').read_text().strip()) in python_ready.stdout + python_ready.stderr
        resolved_python = run_default('default-python-identity', ['python', '-c', 'import sys; print(sys.executable)'])
        assert Path(resolved_python.stdout.strip()).resolve() == Path(sys.executable).resolve()
        run_default('delete-eng-native-rebuild', [*native[:-1], '--no-restore', '-t:Rebuild'])
        assert protected == snapshot(root), 'authored source, selected dependencies or locks changed'
        assert first == {p.relative_to(root / 'eng').as_posix(): p.read_bytes() for p in (root / 'eng').rglob('*') if p.is_file()}
        run('human-regeneration', [sys.executable, root / 'scripts/regenerate_eng.py'])
        run('ci-readonly-check', [sys.executable, root / 'scripts/regenerate_eng.py', '--check'])
        authored = root / 'config/program-kit/architecture.json'
        document = json.loads(authored.read_text())
        document['runtimeComposition']['projects'] = [{'path': 'src/Probe/Probe.csproj', 'role': 'implementation'}]
        authored.write_text(json.dumps(document), encoding='utf-8', newline='\n')
        run('authored-edit-regeneration', [sys.executable, root / 'scripts/regenerate_eng.py'])
        assert json.loads((root / 'eng/architecture.json').read_text()) == document
        run_default('native-architecture-metadata-helper', [sys.executable, root / 'scripts/repository_architecture.py',
            '--repository', root, '--manifest', 'config/program-kit/architecture.json',
            '--output', root / 'artifacts/architecture.xml'])
        protected = snapshot(root)
        # Prove the mandatory native policy remains active after deletion.
        rejected = run('analyzer-policy-rejection', [*native, '--no-restore', '-t:Rebuild', '-p:RunAnalyzers=false'], 1)
        assert 'PKQ003' in rejected.stdout + rejected.stderr
        assert protected == snapshot(root)
        # Missing required feed/pin/input rejects before recreating eng or
        # changing any durable bytes; no fallback to ambient feeds/defaults.
        for relative in ('NuGet.config', '.python-version', 'config/program-kit/architecture.json'):
            missing = root / relative
            original = missing.read_bytes(); missing.unlink(); remove_eng()
            before = snapshot(root)
            failed = run('missing-' + missing.name.replace('.', '-'),
                         [sys.executable, root / 'scripts/regenerate_eng.py'], 2)
            assert relative in failed.stderr and not (root / 'eng').exists()
            assert before == snapshot(root)
            missing.write_bytes(original)
            run('restore-' + missing.name.replace('.', '-'), [sys.executable, root / 'scripts/regenerate_eng.py'])
        recipe_path = root / 'config/program-kit/engineering.json'
        recipe_bytes = recipe_path.read_bytes()
        recipe = json.loads(recipe_bytes); recipe['toolkitVersion'] = '0.0.0-fictional-missing'
        recipe_path.write_text(json.dumps(recipe)); remove_eng()
        failed = run('missing-selected-toolkit', [sys.executable, root / 'scripts/regenerate_eng.py'], 2)
        assert 'selected toolkit version' in failed.stderr and not (root / 'eng').exists()
        recipe_path.write_bytes(recipe_bytes)
        run('restore-selected-toolkit', [sys.executable, root / 'scripts/regenerate_eng.py'])
        foreign = record / 'foreign consumer'
        shutil.copytree(root / 'scripts', foreign / 'scripts')
        (foreign / 'scripts/repository_architecture.py').write_text('raise RuntimeError("foreign helper was executed")\n')
        remove_eng()
        before = snapshot(root)
        failed = run('external-generator-rejected', [sys.executable, foreign / 'scripts/regenerate_eng.py', '--repository', root], 2)
        assert 'target consumer generator' in failed.stderr and 'foreign helper was executed' not in failed.stderr
        assert before == snapshot(root) and not (root / 'eng').exists()
        run('target-generator-restored', [sys.executable, root / 'scripts/regenerate_eng.py'])
        spec = importlib.util.spec_from_file_location('fixture_generator', root / 'scripts/regenerate_eng.py')
        generator = importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)
        before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        with patch.object(generator, 'project', return_value={'config/program-kit/architecture.json': b'bad projection'}):
            try:
                generator.regenerate(root)
            except ValueError as error:
                assert 'strictly below root eng/' in str(error)
            else:
                raise AssertionError('Projection escaped disposable output owner')
        assert before == {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        # The actual repository ignore parser, independent of generated metadata.
        run('git-init', ['git', 'init', '.'])
        run('eng-ignored', ['git', 'check-ignore', 'eng/inputs.json'])
        run('eng-untracked', ['git', 'ls-files', '--error-unmatch', 'eng/inputs.json'], 1)
        assert protected == snapshot(root)
        run('commit-native-source', ['git', '-c', 'user.name=Program Kit Fixture',
            '-c', 'user.email=fixture@example.invalid', '-c', 'core.autocrlf=true', 'add', '.'])
        run('commit-native-baseline', ['git', '-c', 'user.name=Program Kit Fixture',
            '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Fictional standalone engineering baseline'])
        cold = record / 'cold clone'
        run('cold-clone', ['git', '-c', 'core.autocrlf=true', 'clone', '--no-local', root, cold])
        assert not (cold / 'eng').exists() and not (cold / '.agents').exists() and not (cold / '.specify').exists()
        assert (cold / 'scripts/regenerate_eng.py').read_bytes() == (root / 'scripts/regenerate_eng.py').read_bytes()
        cold_source = snapshot(cold)
        run('cold-clone-native-build', native, cwd=cold)
        assert cold_source == snapshot(cold), 'cold build changed authored source or selected locks'
        legacy = record / 'legacy'; (legacy / 'eng/photo_worker').mkdir(parents=True)
        (legacy / 'eng/photo_worker/custom.py').write_bytes(b'# Fictional app-owned source.\n')
        before = {p.relative_to(legacy).as_posix(): p.read_bytes() for p in legacy.rglob('*') if p.is_file()}
        failed = run('legacy-source-preserved', [sys.executable,
                     ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py', '--target', legacy, *approvals], 2)
        assert 'PKE002' in failed.stderr
        assert before == {p.relative_to(legacy).as_posix(): p.read_bytes() for p in legacy.rglob('*') if p.is_file()}
        legacy_ui = record / 'legacy-ui'; (legacy_ui / '.program-kit/ui').mkdir(parents=True)
        for name in ('profile', 'content'):
            source = ROOT / 'extensions/program-kit-governance/templates/ui-experience' / (name + '.json')
            (legacy_ui / '.program-kit/ui' / (name + '.json')).write_bytes(source.read_bytes())
        before = {p.relative_to(legacy_ui).as_posix(): p.read_bytes() for p in legacy_ui.rglob('*') if p.is_file()}
        failed = run('legacy-ui-preserved', [sys.executable,
            ROOT / 'extensions/program-kit-governance/scripts/ui_profile.py', 'init', '--target', legacy_ui], 1)
        assert 'Legacy UI inputs exist' in failed.stderr
        assert before == {p.relative_to(legacy_ui).as_posix(): p.read_bytes() for p in legacy_ui.rglob('*') if p.is_file()}
        selected = record / 'legacy-selected-profile'; (selected / '.program-kit').mkdir(parents=True)
        registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
        index = json.loads((registry / 'index.json').read_text())
        identity = next(name for name in index['profiles'] if name != index['default'])
        entry = index['profiles'][identity]; profile = json.loads((registry / entry['path']).read_text())
        (selected / '.program-kit/managed.json').write_text(json.dumps({'newProjectDependencyProfile': {
            'profile': identity, 'entrySha256': entry['sha256'], 'catalogResolutionSha256': profile['catalogResolutionSha256']}}))
        before = {p.relative_to(selected).as_posix(): p.read_bytes() for p in selected.rglob('*') if p.is_file()}
        failed = run('legacy-profile-query-preserved', [sys.executable,
            ROOT / 'extensions/program-kit-building-blocks/scripts/publisher_knowledge.py', '--target', selected], 1)
        assert 'legacy selected dependency authority' in failed.stderr and 'no new-project default was substituted' in failed.stderr
        assert before == {p.relative_to(selected).as_posix(): p.read_bytes() for p in selected.rglob('*') if p.is_file()}
        # A real composition owner emits nondefault bindings; an ordinary
        # offline consumer must restore and actually consume its deleted views.
        composed = record / 'composition'
        (composed / 'config/program-kit').mkdir(parents=True)
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
        import composition_model as model
        import dotnet_sync
        attributes_fixture = record / 'unicode-attributes'; attributes_fixture.mkdir()
        owned_path = 'web/Équipe space/generated.ts'
        model.local_path(owned_path, 'fictional Unicode owned path')
        rules = dotnet_sync.owned_text_attributes({owned_path: {'ownership': 'managed'}})
        (attributes_fixture / '.gitattributes').write_text('\n'.join(rules) + '\n', encoding='utf-8', newline='\n')
        run('unicode-git-init', ['git', 'init', '.'], cwd=attributes_fixture)
        attr = run('unicode-attribute-lookup', ['git', 'check-attr', '-z', 'eol', '--', owned_path], cwd=attributes_fixture)
        assert attr.stdout.split('\0') == [owned_path, 'eol', 'lf', '']
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
        graph = model.from_legacy(json.loads((template / 'compositions/foundation-bff-keycloak.json').read_text()))
        graph['resources']['application-host']['runtimeDirectory'] = 'runtime/projection-fixture'
        graph['resources']['application-shell']['pathBase'] = '/products/projection'
        (composed / model.INPUT).write_text(json.dumps(graph))
        run('compose-nondefault', [sys.executable, ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py',
                                '--target', composed, '--web-profile', 'bff-cookie', *approvals])
        recipe_path = composed / 'config/program-kit/engineering.json'
        outside_identity = json.loads(recipe_path.read_text())['runtime']['scripts/device_toolchain.py']
        outside_helper = (composed / 'scripts/device_toolchain.py').read_bytes()
        run('composition-only-reconciliation', [sys.executable, ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py',
            '--target', composed, '--web-profile', 'bff-cookie', '--composition-only', *approvals])
        assert json.loads(recipe_path.read_text())['runtime']['scripts/device_toolchain.py'] == outside_identity
        assert (composed / 'scripts/device_toolchain.py').read_bytes() == outside_helper
        run('composition-only-regeneration', [sys.executable, composed / 'scripts/regenerate_eng.py'])
        recipe_bytes = recipe_path.read_bytes()
        recipe = json.loads(recipe_bytes); recipe['toolkitVersion'] = '1.0.0-preview.999'
        recipe_path.write_text(json.dumps(recipe), newline='\n')
        protected_recipe = snapshot(composed)
        rejected = run('cross-version-composition-only-rejected', [sys.executable,
            ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py', '--target', composed,
            '--web-profile', 'bff-cookie', '--composition-only', *approvals], 2)
        assert 'cannot cross selected toolkit versions' in rejected.stderr and protected_recipe == snapshot(composed)
        recipe_path.write_bytes(recipe_bytes)
        before = snapshot(composed)
        original_outputs = {p.relative_to(composed / 'eng').as_posix(): p.read_bytes()
                            for p in (composed / 'eng').rglob('*') if p.is_file()}
        assert (composed / 'eng').resolve().parent == composed.resolve()
        shutil.rmtree(composed / 'eng')
        observed = run('consume-restored-projection', [sys.executable, '-I', '-c',
            'import sys,json; from pathlib import Path; root=Path.cwd(); sys.path.insert(0,str(root/"scripts")); '
            'import composition_run; graph,contract,resolved=composition_run.selected(root); '
            'print(json.dumps(resolved))'], cwd=composed)
        resolved = json.loads(observed.stdout)
        assert resolved['hosts']['application-host']['runtimeStage'] == 'artifacts/runtime/projection-fixture'
        web = json.loads((composed / 'eng/web/compositions/application-shell.json').read_text())
        assert web['routes']['oidcCallback']['path'] == '/products/projection/signin-oidc'
        for relative, data in original_outputs.items():
            assert (composed / 'eng' / relative).read_bytes() == data
        assert before == snapshot(composed)
        run('composed-git-init', ['git', 'init', '.'], cwd=composed)
        run('composed-git-add', ['git', '-c', 'core.autocrlf=true', 'add', '.'], cwd=composed)
        run('composed-git-commit', ['git', '-c', 'user.name=Program Kit Fixture', '-c',
            'user.email=fixture@example.invalid', 'commit', '-m', 'Fictional composed baseline'], cwd=composed)
        composed_clone = record / 'composed clone'
        run('composed-cold-clone', ['git', '-c', 'core.autocrlf=true', 'clone', '--no-local', composed, composed_clone])
        assert not (composed_clone / 'eng').exists()
        cloned = run('consume-cold-composed-projection', [sys.executable, '-I', '-c',
            'import sys,json; from pathlib import Path; root=Path.cwd(); sys.path.insert(0,str(root/"scripts")); '
            'import composition_run; graph,contract,resolved=composition_run.selected(root); '
            'print(json.dumps(resolved))'], cwd=composed_clone)
        assert json.loads(cloned.stdout) == resolved
        assert (composed_clone / 'eng/web/compositions/application-shell.json').read_bytes() == (composed / 'eng/web/compositions/application-shell.json').read_bytes()
        (record / 'results.json').write_text(json.dumps({'status': 'passed', 'commands': commands,
            'elapsedSeconds': round(time.monotonic() - started, 3),
            'scope': 'Installed native skill, real standalone compilation, regeneration and preservation; no agent/service execution'}, indent=2) + '\n')
        print('Disposable eng contract passed; retained fixture: ' + str(record))
    except BaseException:
        print('Disposable eng contract failed; retained fixture: ' + str(record), file=sys.stderr)
        raise


if __name__ == '__main__':
    main()

"""Real offline NuGet lock closure using tiny disposable local packages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


def exercise(root, restore):
    sdk = json.loads((root / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json').read_text())['sdk']
    with tempfile.TemporaryDirectory(prefix='lock-closure-') as directory:
        repository = Path(directory).resolve()
        (repository / 'global.json').write_text(json.dumps({'sdk': sdk}))
        detected = subprocess.run(['dotnet', '--version'], cwd=repository, capture_output=True, text=True, timeout=30)
        assert detected.returncode == 0 and detected.stdout.strip() == sdk['version'], 'Exact SDK must be ready before lock fixture'
        feed = repository / 'feed'
        feed.mkdir()
        for version in ('1.0.0', '2.0.0'):
            with zipfile.ZipFile(feed / f'ProgramKit.ClosureFixture.{version}.nupkg', 'w') as package:
                package.writestr('ProgramKit.ClosureFixture.nuspec', f'<package><metadata><id>ProgramKit.ClosureFixture</id><version>{version}</version><authors>fixture</authors><description>Offline closure fixture</description></metadata></package>')
        config = repository / 'NuGet.config'
        config.write_text(f'<configuration><packageSources><clear/><add key="fixture" value="{feed.as_posix()}" /></packageSources></configuration>')
        projects = {}
        rows = []
        for name, dependencies, role in (('Owner', [], 'implementation'), ('Owner.Api', ['Owner'], 'api'),
                                         ('Owner.Tests', ['Owner.Api'], 'test'), ('Independent', [], 'core')):
            relative = f'{"tests" if role == "test" else "src"}/{name}/{name}.csproj'
            projects[name] = relative
            references = [projects[n] for n in dependencies]
            target = repository / relative
            target.parent.mkdir(parents=True)
            edges = ''.join(f'<ProjectReference Include="{os.path.relpath(repository / p, target.parent)}" />' for p in references)
            pin = '<PackageReference Include="ProgramKit.ClosureFixture" Version="1.0.0" />' if name == 'Owner' else ''
            target.write_text(f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup>{edges}{pin}</ItemGroup></Project>')
            rows.append({'path': relative, 'role': role, 'projectReferences': references})
        solution = repository / 'Closure.slnx'
        solution.write_text('<Solution>' + ''.join(f'<Project Path="{p}" />' for p in projects.values()) + '</Solution>')
        (repository / 'eng').mkdir()
        (repository / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': rows, 'bindings': []}}))
        profile = repository / '.program-kit/dependency-profile.json'
        profile.parent.mkdir()
        profile.write_text('{"profile":"retained-exact-profile","pins":{"Foundation":"0.3.2"}}')
        original_profile = profile.read_bytes()
        environment = restore.isolated_environment(repository)
        environment['MSBUILDDISABLENODEREUSE'] = '1'
        environment['DOTNET_ADD_GLOBAL_TOOLS_TO_PATH'] = '0'
        def native(arguments):
            return subprocess.run(arguments, cwd=repository, env=environment, capture_output=True, text=True, timeout=180)
        initial = native(['dotnet', 'restore', str(solution), '--configfile', str(config), '--use-lock-file'])
        assert initial.returncode == 0, initial.stdout + initial.stderr
        independent = repository / Path(projects['Independent']).parent / 'packages.lock.json'
        original_lock = independent.read_bytes()
        owner = repository / projects['Owner']
        owner.write_text(owner.read_text().replace('Version="1.0.0"', 'Version="2.0.0"'))
        lock = {'targets': [{'path': projects['Owner'], 'packages': [{'materializationKind': 'nuget-project'}]}]}
        plan = restore.restore_commands(repository, lock, 'renew')
        print('Renewal preview: ' + ', '.join(command['subject'] for command in plan))
        for command in plan:
            restored = native(command['args'])
            assert restored.returncode == 0, restored.stdout + restored.stderr
        locked = native(['dotnet', 'restore', str(solution), '--configfile', str(config), '--locked-mode'])
        assert locked.returncode == 0, 'Incomplete renewal caused whole-solution LockedMode failure:\n' + locked.stdout + locked.stderr
        assert {command['subject'] for command in plan} == {projects['Owner'], projects['Owner.Api'], projects['Owner.Tests']}
        assert independent.read_bytes() == original_lock
        assert profile.read_bytes() == original_profile
        (repository / projects['Owner.Api']).write_text('<Project><ItemGroup><ProjectReference Include="$(Unknown)" /></ItemGroup></Project>')
        try:
            restore.restore_commands(repository, lock, 'renew')
        except restore.RestoreError as error:
            assert 'evaluated' in str(error)
        else:
            raise AssertionError('Dynamic reverse graph was silently narrowed')
    print('Complete reverse-dependent lock batch and whole-solution LockedMode passed; unrelated lock/profile bytes preserved.')

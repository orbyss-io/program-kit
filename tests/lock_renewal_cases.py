"""Real offline NuGet lock closure using tiny disposable local packages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile
import shutil
import sys
import uuid
from datetime import datetime, timezone


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
        for name, dependencies, role in (('Dependency', [], 'core'), ('Owner', ['Dependency'], 'implementation'), ('Owner.Api', ['Owner'], 'api'),
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
        solution.write_text('<Solution>' + ''.join(f'<Project Path="{p}" />' for name,p in projects.items() if name != 'Dependency') + '</Solution>')
        (repository / 'eng').mkdir()
        (repository / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': rows, 'bindings': []}}))
        profile = repository / '.program-kit/dependency-profile.json'
        profile.parent.mkdir()
        profile.write_text('{"profile":"retained-exact-profile","pins":{"Foundation":"0.3.2"}}')
        original_profile = profile.read_bytes()
        environment = restore.isolated_environment(repository)
        environment['MSBUILDDISABLENODEREUSE'] = '1'
        environment['DOTNET_ADD_GLOBAL_TOOLS_TO_PATH'] = '0'
        executions = []
        def native(arguments):
            result = subprocess.run(arguments, cwd=repository, env=environment, capture_output=True, text=True, timeout=180)
            executions.append({'command': [str(arg).replace(str(repository), '<fixture>') for arg in arguments],
                               'exitCode': result.returncode, 'stdoutSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                               'stderrSha256': hashlib.sha256(result.stderr.encode()).hexdigest()})
            return result
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
        # The forward dependency is absent from solution membership and the
        # target list, yet real native restore produces its outputs.
        closure = restore.nuget_plan_closure(repository, lock)
        related = {projects[name] for name in ('Dependency', 'Owner', 'Owner.Api', 'Owner.Tests')}
        assert set(closure['projects']) == related
        solution_lock = {'targets': [{'path': projects['Owner'], 'lockRoot': 'Closure.slnx',
                                     'packages': [{'materializationKind': 'nuget-project'}]}]}
        solution_closure = restore.nuget_plan_closure(repository, solution_lock)
        assert set(solution_closure['projects']) == set(projects.values())
        dependency_path = repository / '.program-kit/sync/dependencies.json'
        dependency_path.parent.mkdir(parents=True)
        dependency_path.write_text(json.dumps(lock))
        toolchain_path = repository / 'artifacts/program-kit/toolchain.json'
        toolchain_path.parent.mkdir(parents=True)
        toolchain_path.write_text(json.dumps({'commands': {'dotnet': [shutil.which('dotnet')]},
            'required': {'dotnet': sdk['version']}, 'resolved': {'dotnet': sdk['version']}, 'satisfied': True}))
        # Execute the actual maintained CLI, not a synthetic successful receipt.
        for mode in ('renew', 'locked'):
            execution = native([sys.executable, restore.__file__, mode, '--target', str(repository),
                                '--lock', '.program-kit/sync/dependencies.json', '--approved'])
            assert execution.returncode == 0, execution.stdout + execution.stderr
        evidence_path = repository / 'artifacts/program-kit/building-block-restore.json'
        evidence = json.loads(evidence_path.read_text())
        restore.verify_evidence(repository, lock, evidence)
        expected_outputs = {closure['outputs'][project][kind] for project in related for kind in ('lock', 'assets')}
        actual_outputs = {path for outputs in evidence['nugetOutputs'].values() for path in outputs}
        assert expected_outputs == actual_outputs
        assert all((repository / path).is_file() for path in actual_outputs)
        sys.path.insert(0, str(root / 'scripts'))
        import upgrade_program_kit as upgrade
        affected = [repository / closure['outputs'][project]['lock'] for project in related]
        upgrade.write_lock_renewal(repository, {}, affected)
        assert upgrade.satisfy_lock_renewal(repository, {}, [], restore), 'Forward/reverse native owner was rejected'
        renewal = json.loads((repository / 'artifacts/program-kit/dotnet-lock-renewal.json').read_text())
        # A current lock snapshot is insufficient for an unrelated owner.
        upgrade.write_lock_renewal(repository, {}, [independent])
        assert not upgrade.satisfy_lock_renewal(repository, {}, [], restore)
        # The exact native output inventory must survive through verification.
        assets = repository / closure['outputs'][projects['Dependency']]['assets']
        original_assets = assets.read_bytes()
        assets.write_bytes(original_assets + b'\n ')
        try:
            restore.verify_evidence(repository, lock, evidence)
        except restore.RestoreError as error:
            assert 'output inventory' in str(error)
        else:
            raise AssertionError('Changed forward output was accepted')
        assets.write_bytes(original_assets)
        restore.verify_evidence(repository, lock, evidence)
        assert independent.read_bytes() == original_lock
        assert profile.read_bytes() == original_profile
        custom = repository / projects['Dependency']
        custom_original = custom.read_bytes()
        custom.write_text(custom.read_text().replace('<TargetFramework>', '<NuGetLockFilePath>locks/custom.json</NuGetLockFilePath><TargetFramework>'))
        try:
            restore.nuget_plan_closure(repository, lock)
        except restore.RestoreError as error:
            assert 'evaluated graph/output adapter' in str(error)
        else:
            raise AssertionError('Custom lock was silently attributed to a default path')
        custom.write_bytes(custom_original)
        (repository / projects['Owner.Api']).write_text('<Project><ItemGroup><ProjectReference Include="$(Unknown)" /></ItemGroup></Project>')
        try:
            restore.restore_commands(repository, lock, 'renew')
        except restore.RestoreError as error:
            assert 'evaluated' in str(error)
        else:
            raise AssertionError('Dynamic reverse graph was silently narrowed')
        run = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex
        output = root / 'artifacts/restore-closure' / run / 'results.json'
        output.parent.mkdir(parents=True)
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps({'status': 'passed', 'sdk': sdk, 'nativeExecutions': executions,
            'directClosure': closure, 'solutionClosure': solution_closure,
            'restoreEvidence': evidence, 'acceptedRenewal': renewal,
            'sourceSha256': {str(path.relative_to(root)).replace('\\','/'): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (Path(__file__), Path(restore.__file__), root / 'scripts/upgrade_program_kit.py')},
            'cases': {'actual-maintained-renew-and-locked': True, 'forward-nonmember-owner': True,
                      'reverse-dependent-owner': True, 'unrelated-owner-rejected': True,
                      'changed-assets-rejected': True, 'custom-output-refused': True, 'dynamic-graph-refused': True,
                      'unrelated-lock-and-retained-profile-unchanged': True}}, indent=2) + '\n')
        print('Native restore closure evidence: ' + output.relative_to(root).as_posix())
    print('Complete reverse-dependent lock batch and whole-solution LockedMode passed; unrelated lock/profile bytes preserved.')

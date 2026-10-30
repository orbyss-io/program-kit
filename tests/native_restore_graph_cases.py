"""Native offline evaluated restore ownership; no execution of retired source."""
import hashlib
from contextlib import nullcontext
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import zipfile


def exercise(root, restore):
    sdk = json.loads((root/'extensions/program-kit-dotnet/templates/dotnet/files/global.json').read_text())['sdk']
    evidence = root/'artifacts/restore-closure'/('evaluated-'+uuid.uuid4().hex)
    evidence.mkdir(parents=True)
    consumer = root/'artifacts/t'/('evaluated-'+uuid.uuid4().hex[:12])
    consumer.mkdir(parents=True)
    # Retain native graph commands/expanded inputs on failure as well as success.
    # This is an exact new owned fixture; no pre-existing checkout is reused.
    with nullcontext(str(consumer)) as temporary:
        repository = Path(temporary).resolve()
        (repository/'scripts').mkdir()
        (repository/'config/program-kit').mkdir(parents=True)
        (repository/'global.json').write_text(json.dumps({'sdk': sdk}))
        (repository/'config/program-kit/restore-graph.json').write_text(json.dumps({'schemaVersion': 1, 'adapter': 'native-msbuild',
            'configuration': 'Debug', 'sdkVersion': sdk['version']}))
        (repository/'Directory.Build.props').write_text('<Project><PropertyGroup><BaseIntermediateOutputPath>$(MSBuildThisFileDirectory)artifacts/obj/$(MSBuildProjectName)/</BaseIntermediateOutputPath><NuGetLockFilePath>$(MSBuildThisFileDirectory)locks/$(MSBuildProjectName).json</NuGetLockFilePath></PropertyGroup></Project>')
        feed = repository/'feed'; feed.mkdir()
        for version in ('1.0.0', '2.0.0'):
            with zipfile.ZipFile(feed/f'ProgramKit.EvaluatedFixture.{version}.nupkg', 'w') as archive:
                archive.writestr('ProgramKit.EvaluatedFixture.nuspec', f'<package><metadata><id>ProgramKit.EvaluatedFixture</id><version>{version}</version><authors>fixture</authors><description>Offline evaluated restore</description></metadata></package>')
        # The SDK's own F# library pack supplies the implicit public FSharp.Core.
        sdk_root = Path(shutil.which('dotnet')).resolve().parent/'sdk'/sdk['version']
        fsharp = sdk_root/'FSharp/library-packs'
        assert fsharp.is_dir(), 'Exact SDK F# library pack must be prepared'
        (repository/'NuGet.config').write_text(f'<configuration><packageSources><clear/><add key="fixture" value="{feed.as_posix()}"/><add key="sdk-fsharp" value="{fsharp.as_posix()}"/></packageSources></configuration>')
        projects = {'Dependency': 'src/Dependency/Dependency.fsproj', 'Owner': 'src/Shared/Owner.csproj',
                    'Peer': 'src/Shared/Peer.vbproj', 'Reverse': 'tests/Reverse/Reverse.vbproj',
                    'Independent': 'src/Independent/Independent.csproj'}
        for name, relative in projects.items():
            target = repository/relative; target.parent.mkdir(parents=True, exist_ok=True)
            reference = '<Import Project="../../scripts/owner-links.props" />' if name == 'Owner' else ''
            if name == 'Reverse':
                reference = '<ItemGroup><ProjectReference Include="../../src/Shared/Owner.csproj" /></ItemGroup>'
            package = '<ItemGroup><PackageReference Include="ProgramKit.EvaluatedFixture" Version="1.0.0" /></ItemGroup>' if name == 'Owner' else ''
            target.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>'+reference+package+'</Project>')
        (repository/'scripts/owner-links.props').write_text('<Project><ItemGroup><ProjectReference Include="$(MSBuildThisFileDirectory)../src/Dependency/Dependency.fsproj" /></ItemGroup></Project>')
        (repository/'Program.slnx').write_text('<Solution>'+''.join(f'<Project Path="{relative}" />' for name, relative in projects.items() if name != 'Dependency')+'</Solution>')
        profile = repository/'eng/retained-profile.json'; profile.write_text('{"retained":"original"}')
        original_profile = profile.read_bytes()
        toolchain = repository/'artifacts/program-kit/toolchain.json'; toolchain.parent.mkdir(parents=True)
        toolchain.write_text(json.dumps({'commands': {'dotnet': [shutil.which('dotnet')]},
            'required': {'dotnet': sdk['version']}, 'resolved': {'dotnet': sdk['version']}, 'satisfied': True}))
        env = restore.isolated_environment(repository)
        env['MSBUILDDISABLENODEREUSE'] = '1'; env['DOTNET_CLI_USE_MSBUILD_SERVER'] = '0'
        executions = []
        def native(command):
            index = len(executions)
            result = subprocess.run(command, cwd=repository, env=env, capture_output=True, text=True, timeout=900)
            (evidence/f'{index}.stdout.log').write_text(result.stdout, encoding='utf-8')
            (evidence/f'{index}.stderr.log').write_text(result.stderr, encoding='utf-8')
            executions.append({'command': list(map(str, command)), 'exitCode': result.returncode})
            assert result.returncode == 0, result.stdout+result.stderr
        native(['dotnet', 'restore', 'Program.slnx', '--configfile', 'NuGet.config', '--use-lock-file'])
        unrelated = {name: (repository/f'locks/{name}.json').read_bytes() for name in ('Independent', 'Peer')}
        owner = repository/projects['Owner']; owner.write_text(owner.read_text().replace('Version="1.0.0"', 'Version="2.0.0"'))
        lock = {'targets': [{'path': projects['Owner'], 'packages': [{'materializationKind': 'nuget-project'}]}]}
        closure = restore.nuget_plan_closure(repository, lock)
        assert set(closure['subjects']) == {projects['Owner'], projects['Reverse']}
        assert set(closure['projects']) == {projects[name] for name in ('Owner', 'Dependency', 'Reverse')}
        for name in ('Owner', 'Dependency', 'Reverse'):
            assert closure['outputs'][projects[name]] == {'lock': f'locks/{name}.json', 'assets': f'artifacts/obj/{name}/project.assets.json'}
        assert closure == restore.nuget_plan_closure(repository, lock), 'Equivalent native observations must be deterministic'
        context = repository/'.program-kit/sync/dependencies.json'; context.parent.mkdir(parents=True)
        context.write_text(json.dumps(lock))
        for mode in ('renew', 'locked'):
            native([sys.executable, restore.__file__, mode, '--target', str(repository), '--approved', '--lock', '.program-kit/sync/dependencies.json'])
        receipt = json.loads((repository/'artifacts/program-kit/building-block-restore.json').read_text())
        restore.verify_evidence(repository, lock, receipt)
        sys.path.insert(0, str(root/'scripts'))
        import upgrade_program_kit as upgrade
        affected = upgrade.stale_program_kit_locks(repository, {'ProgramKit.EvaluatedFixture': '2.0.0'}, restore)
        assert set(affected) == {repository/f'locks/{name}.json' for name in ('Owner', 'Reverse')}
        upgrade.write_lock_renewal(repository, {}, [repository/row['lock'] for row in closure['outputs'].values()])
        assert upgrade.satisfy_lock_renewal(repository, {}, [], restore)
        assert {row['path'] for row in receipt['nativeLocks']} >= {f'locks/{name}.json' for name in ('Owner', 'Dependency', 'Reverse')}
        for name, original in unrelated.items():
            assert (repository/f'locks/{name}.json').read_bytes() == original
        assert profile.read_bytes() == original_profile
        native(['dotnet', 'restore', 'Program.slnx', '--configfile', 'NuGet.config', '--locked-mode'])
        # Shared directory is safe only because native owners have distinct outputs.
        peer = repository/projects['Peer']; before = peer.read_bytes()
        peer.write_text(before.decode().replace('<TargetFramework>', '<NuGetLockFilePath>../../locks/Owner.json</NuGetLockFilePath><TargetFramework>'))
        try:
            restore.nuget_plan_closure(repository, lock)
        except restore.RestoreError as error:
            assert 'share a restore output' in str(error)
        else:
            raise AssertionError('Independent native owner shared a selected output without rejection')
        peer.write_bytes(before)
        assets = repository/closure['outputs'][projects['Owner']]['assets']; original = assets.read_bytes(); assets.write_bytes(original+b' ')
        try:
            restore.verify_evidence(repository, lock, receipt)
        except restore.RestoreError as error:
            assert 'output inventory' in str(error)
        else:
            raise AssertionError('Changed evaluated output was accepted')
        assets.write_bytes(original)
        # A metadata target must not become an escape hatch for executing old code.
        owner.write_text(owner.read_text().replace('</Project>', '<Target Name="Unsafe" BeforeTargets="GenerateRestoreGraphFile"><Error Text="must not execute"/></Target></Project>'))
        try:
            restore.nuget_plan_closure(repository, lock)
        except restore.RestoreError as error:
            assert 'restore-target override/hook' in str(error)
        else:
            raise AssertionError('Consumer restore hook was executed/admitted')
        (evidence/'results.json').write_text(json.dumps({'status': 'passed', 'sdk': sdk, 'scope': 'Actual native offline graph/renew/locked metadata and output ownership; no retired source execution or application acceptance',
            'retainedConsumer': str(repository),
            'closure': closure, 'restoreEvidence': receipt, 'nativeExecutions': executions,
            'sourceSha256': {str(path.relative_to(root)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(__file__), Path(restore.__file__), Path(restore.native_restore_graph.__file__))}}, indent=2)+'\n')
    print('Evaluated native restore graph evidence: '+evidence.relative_to(root).as_posix())

"""Execute pinned EF/Npgsql against a real disposable PostgreSQL, including database restart."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import persistence_selection
from live.v2.postgresql_service import PostgreSqlService, deploy_postgresql
from live.v2.supervisor import run_supervised
from live.v2.cli import supervisor_environment


def main():
    template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
    artifact = ROOT / 'artifacts/persistence-runtime'; artifact.mkdir(parents=True, exist_ok=True)
    env = supervisor_environment()
    env.update(DOTNET_CLI_HOME=str(ROOT / 'artifacts/dotnet-engineering/cli'),
               NUGET_PACKAGES=str(ROOT / 'artifacts/dotnet-engineering/packages'),
               DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_NOLOGO='1')
    contract = json.loads((ROOT / 'tests/live/scenarios/knowledge-application/v1/bootstrap-seed/fixture/acceptance/services.json').read_text())
    with tempfile.TemporaryDirectory(prefix='ef-', dir=artifact) as directory:
        project = Path(directory)
        shutil.copyfile(ROOT / 'tests/fixtures/persistence-runtime/Program.cs', project / 'Program.cs')
        (project / 'global.json').write_text(json.dumps({'sdk': json.loads((template / 'global.json').read_text())['sdk']}))
        pins = {n.attrib['Include']: n.attrib['Version'] for n in ET.parse(template / '.program-kit/eng/profiles/persistence/ProgramKit.Persistence.EfPostgreSql.props').iter('PackageVersion')}
        central = '<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup>' + ''.join(
            f'<PackageVersion Include="{name}" Version="{version}" />' for name, version in pins.items()) + '</ItemGroup></Project>'
        (project / 'Directory.Packages.props').write_text(central)
        references = ''.join(f'<PackageReference Include="{name}" PrivateAssets="all" />' for name in
                             ('Microsoft.EntityFrameworkCore', 'Microsoft.EntityFrameworkCore.Design', 'Npgsql.EntityFrameworkCore.PostgreSQL'))
        (project / 'Probe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup>' + references + '</ItemGroup></Project>')
        (project / 'NuGet.config').write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
        def operation(command, name, environment, secrets=()):
            result = run_supervised(command, cwd=project, environment=environment, evidence_directory=artifact / name,
                                    timeout_seconds=180, secrets=list(secrets))
            if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
                raise AssertionError(f'{name} failed; inspect {artifact / name}')
        operation(['dotnet', 'build', 'Probe.csproj', '--verbosity', 'quiet'], 'build', env)
        test_project = project / 'tests/ProviderTests.csproj'; test_project.parent.mkdir()
        test_project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><PackageReference Include="Microsoft.EntityFrameworkCore" /></ItemGroup></Project>')
        owner = {'owner': 'Reservations', 'profile': 'ef-postgresql', 'admissionComplete': True,
                 'providerProject': 'Probe.csproj', 'testProjects': ['tests/ProviderTests.csproj'], 'testProvisioning': 'supervisor'}
        selection = {'owners': [owner], 'blockers': []}
        def evaluated_graph():
            graph = {}
            for index, relative in enumerate([owner['providerProject'], *owner['testProjects']]):
                name = 'evaluated-' + str(index)
                operation(['dotnet', 'msbuild', relative, '-nologo', '-getProperty:ManagePackageVersionsCentrally',
                           '-getItem:PackageReference,PackageVersion'], name, env)
                graph[relative] = json.loads((artifact / name / 'workflow.stdout.log').read_text(encoding='utf-8'))
            return graph
        persistence_selection.validate_evaluated(selection, template, evaluated_graph())
        original = (project / 'Probe.csproj').read_text()
        (project / 'Probe.csproj').write_text(original.replace('Include="Npgsql.', 'Condition="false" Include="Npgsql.'))
        try:
            persistence_selection.validate_evaluated(selection, template, evaluated_graph())
        except ValueError as error:
            if 'assignment/pin' not in str(error):
                raise
        else:
            raise AssertionError('Actual conditional provider omission escaped the evaluated graph gate')
        (project / 'Probe.csproj').write_text(original)
        persistence_selection.validate_evaluated(selection, template, evaluated_graph())
        operation(['dotnet', 'tool', 'install', 'dotnet-ef', '--tool-path', '.tools', '--version', pins['Microsoft.EntityFrameworkCore.Design'],
                   '--configfile', 'NuGet.config'], 'migration-tool', env)
        executable = str(project / '.tools' / ('dotnet-ef.exe' if os.name == 'nt' else 'dotnet-ef'))
        operation([executable, 'migrations', 'add', 'Initial', '--project', 'Probe.csproj', '--no-build'], 'migration-authoring', env)
        shutil.copytree(project / 'Migrations', artifact / 'migrations', dirs_exist_ok=True)
        operation(['dotnet', 'build', 'Probe.csproj', '--no-restore', '--verbosity', 'quiet'], 'migration-build', env)
        # Consumer providers are libraries; the executable above is only the behavior test runner.
        provider = project / 'provider'; provider.mkdir()
        (provider / 'Provider.csproj').write_text(original.replace('<OutputType>Exe</OutputType>', ''))
        types = (project / 'Program.cs').read_text().split('public sealed class Store : DbContext', 1)[1]
        (provider / 'Store.cs').write_text('using Microsoft.EntityFrameworkCore;\npublic sealed class Store : DbContext' + types)
        shutil.copytree(project / 'Migrations', provider / 'Migrations')
        operation(['dotnet', 'build', 'provider/Provider.csproj', '--verbosity', 'quiet'], 'provider-library-build', env)
        manifest = project / '.program-kit/eng/.config/dotnet-tools.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'version': 1, 'isRoot': True, 'tools': {'dotnet-ef': {
            'version': pins['Microsoft.EntityFrameworkCore.Design'], 'commands': ['dotnet-ef']}}}))
        with PostgreSqlService(contract, project, artifact / 'database', env) as database:
            environment = {**env, **database.worker_environment()}
            def deployment_operation(command, name, *, cwd, environment=None, secrets=None):
                result = run_supervised(command, cwd=cwd, environment=environment or env, evidence_directory=artifact / name,
                                        timeout_seconds=180, secrets=secrets)
                if result.exitCode != 0 or not result.cleanupComplete or not result.logsDrained:
                    raise AssertionError(f'{name} failed; inspect {artifact / name}')
            deploy_postgresql(project, artifact, database, ['dotnet'], [{'owner': 'Reservations', 'profile': 'ef-postgresql',
                'admissionComplete': True, 'providerProject': 'provider/Provider.csproj'}], env, deployment_operation, 'shared-deployment')
            command = ['dotnet', str(project / 'bin/Debug/net10.0/Probe.dll')]
            operation(command + ['exercise', str(artifact / 'exercise.xml')], 'exercise', environment, [database.password])
            database.restart()
            environment.update(database.worker_environment())
            operation(command + ['restart', str(artifact / 'restart.xml')], 'restart', environment, [database.password])
        cases = [c for name in ('exercise', 'restart') for c in ET.parse(artifact / (name + '.xml')).iter('testcase')]
        if not cases or any(c.find('failure') is not None for c in cases):
            raise AssertionError('Database behavior cases did not pass')
        (artifact / 'verification.json').write_text(json.dumps({'image': contract['image'], 'pins': pins,
            'cases': [c.attrib['name'] for c in cases], 'evaluatedCentralGraph': 'passed-positive-and-conditional-negative',
            'sharedMigrationDeployment': 'passed-from-provider-class-library', 'cleanupComplete': True}, indent=2) + '\n')
        print(f'Real EF/Npgsql/PostgreSQL integration passed: {len(cases)} cases, database restart and cleanup.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

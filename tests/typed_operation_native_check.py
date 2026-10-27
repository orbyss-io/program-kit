"""Compile actual emitted owners with the selected native analyzer; exercise the native outer deadline.

This bounded fixture supplies no HTTP/database/semantic-agent acceptance claim.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def check():
    sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'),
                   str(ROOT / 'extensions/program-kit-governance/scripts')]
    import typed_operation
    directory = ROOT / 'artifacts/t' / ('typed-native-' + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True)
    (directory / 'Directory.Build.props').write_text('''<Project><PropertyGroup>
<TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>
<GenerateDocumentationFile>true</GenerateDocumentationFile><TreatWarningsAsErrors>true</TreatWarningsAsErrors>
<FoundationSourceReadability>true</FoundationSourceReadability><NuGetAudit>false</NuGetAudit>
</PropertyGroup><ItemGroup><PackageReference Include="Orbyss.Foundation.Analyzers" Version="0.3.7" PrivateAssets="all"/>
</ItemGroup></Project>''', encoding='utf-8')
    (directory / 'Directory.Build.targets').write_text('<Project/>', encoding='utf-8')
    (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear/></packageSources></configuration>', encoding='utf-8')
    shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig', directory / '.editorconfig')
    owners = {key: f'src/{key}/{key}.csproj' for key in ('core', 'runtime', 'api', 'provider', 'test')}
    owners.update(frontend='web/app', generatedTypes='tools/openapi/labels/generated/types.ts')
    for name, content in typed_operation.render(owners, ROOT / 'extensions').items():
        path = directory / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
    # Compile both actual upstream provider shapes: the base registration and
    # named multi-context specialization that the installed route consumes.
    import foundation_composition
    import composition_render
    contract = {'packages': ['Orbyss.Foundation.Execution']}
    for label in ('Base', 'Named'):
        project = {'path': f'src/provider/Scaffold/{label}/{label}.csproj',
                   'packageId': 'NativeFixture.' + label, 'featureIdentity': 'NativeFixture.' + label,
                   'role': 'provider', 'responsibility': 'persistence'}
        generated = (foundation_composition.scaffold_project(project, contract) if label == 'Base' else
            composition_render.provider_scaffold(project, [{'context': 'FirstDbContext', 'policy': 'first'},
                {'context': 'SecondDbContext', 'policy': 'second'}], contract))
        for name, content in generated.items():
            if name.endswith('.cs'):
                path = directory / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
    packages = {'core': [], 'runtime': ['Orbyss.Foundation.Execution'],
                'api': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'],
                'provider': ['Orbyss.Foundation.PostgreSql']}
    commands = []
    for owner, names in packages.items():
        project = directory / owners[owner]; project.parent.mkdir(parents=True, exist_ok=True)
        items = ''.join(f'<PackageReference Include="{name}" Version="0.3.7"/>' for name in names)
        if owner != 'core':
            items += '<ProjectReference Include="../core/core.csproj"/><FrameworkReference Include="Microsoft.AspNetCore.App"/>'
        if owner in ('api', 'provider'):
            items += '<PackageReference Include="CShells.Abstractions" Version="0.0.31"/>'
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><ItemGroup>' + items + '</ItemGroup></Project>', encoding='utf-8')
    test = directory / owners['test']; test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>
</PropertyGroup><ItemGroup><ProjectReference Include="../runtime/runtime.csproj"/>
<ProjectReference Include="../api/api.csproj"/><ProjectReference Include="../provider/provider.csproj"/>
<FrameworkReference Include="Microsoft.AspNetCore.App"/></ItemGroup></Project>''', encoding='utf-8')
    fixture = test.parent / 'Labels'; fixture.mkdir()
    for source in (ROOT / 'tests/fixtures/typed-operation-runtime').glob('*.cs'):
        shutil.copyfile(source, fixture / source.name)
    commands.append(['dotnet', 'build', str(test), '--configuration', 'Release', '--nologo', '-m:1', '--disable-build-servers'])
    commands.append(['dotnet', 'run', '--no-build', '--project', str(test), '--configuration', 'Release'])
    for index, command in enumerate(commands):
        run = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=90)
        (directory / f'{index}.stdout.txt').write_text(run.stdout, encoding='utf-8')
        (directory / f'{index}.stderr.txt').write_text(run.stderr, encoding='utf-8')
        print(run.stdout, end=''); print(run.stderr, end='')
        if run.returncode:
            print('Native source/check retained: ' + str(directory)); return run.returncode
    if 'NATIVE_OUTER_DEADLINE_FRESHNESS_CALLER_AND_CONFIG_PASSED' not in run.stdout:
        raise ValueError('Successful build did not execute the intended runtime behavior')
    # A representative real native diagnostic must reject the exact historical
    # inline collection shape. Successful fixture setup alone cannot satisfy it.
    source = directory / 'src/provider/Labels/PostgreSqlLabelStore.cs'
    original = source.read_text(encoding='utf-8')
    if original.count('            parameters,') != 1:
        raise ValueError('Native ORB1008 negative seam changed; preserve source for review')
    source.write_text(original.replace('            parameters,', '            [value],'), encoding='utf-8')
    command = ['dotnet', 'build', str(directory / owners['provider']), '--configuration', 'Release', '--nologo', '-m:1', '--disable-build-servers']
    negative = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=90)
    (directory / 'native-negative.stdout.txt').write_text(negative.stdout, encoding='utf-8')
    (directory / 'native-negative.stderr.txt').write_text(negative.stderr, encoding='utf-8')
    source.write_text(original, encoding='utf-8')
    if negative.returncode == 0 or 'error ORB1008:' not in negative.stdout + negative.stderr:
        raise ValueError('Expected native inline-argument rejection, inspect ' + str(directory))
    print('ACTUAL_NATIVE_ORB1008_NEGATIVE_PASSED')
    print('Native source/check retained: ' + str(directory))
    return 0


if __name__ == '__main__':
    raise SystemExit(check())

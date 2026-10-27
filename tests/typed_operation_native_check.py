"""Compile actual emitted owners with the selected native analyzer; exercise the native outer deadline.

This bounded fixture supplies no HTTP/database/semantic-agent acceptance claim.
"""
from pathlib import Path
import shutil
import re
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
    eng = directory / 'eng'; eng.mkdir()
    shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Build.props', eng / 'ProgramKit.Build.props')
    (directory / 'Directory.Build.props').write_text('''<Project><Import Project="eng/ProgramKit.Build.props"/><PropertyGroup>
<NuGetAudit>false</NuGetAudit>
</PropertyGroup><ItemGroup><PackageReference Update="Orbyss.Foundation.Analyzers" Version="0.3.7"/>
</ItemGroup></Project>''', encoding='utf-8')
    shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Build.targets', eng / 'ProgramKit.Build.targets')
    (directory / 'Directory.Build.targets').write_text('<Project><Import Project="eng/ProgramKit.Build.targets"/></Project>', encoding='utf-8')
    (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear/></packageSources></configuration>', encoding='utf-8')
    shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig', directory / '.editorconfig')
    shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json', directory / 'global.json')
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
    check_source_category(directory, directory / owners['core'])
    print('Native source/check retained: ' + str(directory))
    return 0


def check_source_category(directory, project):
    """Native positive and independent mutation controls for the whole mechanical category.

    This deliberately establishes no automated policy/Options/SOLID semantic review.
    Each mutation starts from the same compiled positive, so a setup error cannot pass it.
    """
    source = project.parent / 'SourceStyleControl.cs'
    positive = '''namespace NativeStyle;

/// <summary>Independent source-layout control compiled by the actual selected analyzers.</summary>
internal sealed class SourceStyleControl
{
    /// <summary>Immutable input used by both observation branches.</summary>
    private readonly string field;

    /// <summary>Prepares one immutable input.</summary>
    public SourceStyleControl(string value)
    {
        field = value;
    }

    /// <summary>Permits a next-line unbraced body, a standalone call and a correctly split chain.</summary>
    public string Read(bool enabled)
    {
        if (enabled)
            return field
                .Trim()
                .ToUpperInvariant();
        return Echo(field);
    }

    /// <summary>Leaves private helpers after the public behavior.</summary>
    private static string Echo(string value) => value;

    /// <summary>Executes an explicitly prepared deferred function.</summary>
    private static string From(Func<string> read) => read();
}
'''
    command = ['dotnet', 'build', str(project), '--configuration', 'Release', '--no-restore', '--nologo', '-m:1', '--disable-build-servers']

    def build(label, text, diagnostic=None, extra=()):
        source.write_text(text, encoding='utf-8')
        result = subprocess.run([*command, *extra], cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=90)
        (directory / f'style-{label}.stdout.txt').write_text(result.stdout, encoding='utf-8')
        (directory / f'style-{label}.stderr.txt').write_text(result.stderr, encoding='utf-8')
        output = result.stdout + result.stderr
        compiler_errors = re.findall(r'error\s+(?:CS\d+|AD0001)\b', output)
        marker = 'error : PKQ003 ' if diagnostic == 'PKQ003' else f'error {diagnostic}:'
        if compiler_errors or (diagnostic is None and result.returncode) or (diagnostic is not None and
                (result.returncode == 0 or marker not in output)):
            raise ValueError(f'Native source control {label} did not establish {diagnostic or "positive compilation"}; inspect {directory}')

    mutations = [
        ('embedded-body', 'IDE2001', 'if (enabled)\n            return', 'if (enabled) return'),
        ('chain-first', 'ORB1009', 'field\n                .Trim()', 'field.Trim()'),
        ('chain-combined', 'ORB1009', '.Trim()\n                .ToUpperInvariant()', '.Trim().ToUpperInvariant()'),
        ('nested-call', 'ORB1008', 'return Echo(field);', 'return Echo(field.Trim());'),
        ('constructed-argument', 'ORB1008', 'return Echo(field);', "return Echo(new string('x', 1));"),
        ('deferred-argument', 'ORB1008', 'return Echo(field);', 'return From(() => Echo(field));'),
        ('awaited-argument', 'ORB1008', 'return Echo(field);', 'return Echo(await Task.FromResult(field));'),
        ('parameter-layout', 'ORB1007', 'Echo(string value)', 'Echo(string value, string second = "", string third = "")'),
        ('constructor-layout', 'ORB1007', 'SourceStyleControl(string value)', 'SourceStyleControl(string value, string second = "", string third = "")'),
        ('argument-layout', 'ORB1007', 'return Echo(field);', 'return string.Concat(field, field, field);'),
        ('fields-first', 'ORB1010', '    private readonly string field;\n', ''),
        ('private-helper-last', 'ORB1004', '    public string Read', '    private string Read'),
        ('xml-presence', 'ORB1005', '    /// <summary>Prepares one immutable input.</summary>\n', ''),
        ('one-type', 'ORB1003', '\n}\n', '\n}\n/// <summary>Second declared owner.</summary>\ninternal sealed class Extra {}\n'),
        ('private-field-name', 'IDE1006', 'field', '_field'),
    ]
    try:
        build('positive', positive)
        build('disabled-code-style', positive, 'PKQ003', ['-p:EnforceCodeStyleInBuild=false'])
        for label, diagnostic, old, new in mutations:
            if old not in positive:
                raise ValueError('Native source mutation seam missing: ' + label)
            text = positive.replace(old, new)
            if label == 'awaited-argument':
                text = text.replace('public string Read', 'public async Task<string> Read')
            if label == 'fields-first':
                text = text.replace('    private static string From', '    private readonly string field;\n\n    /// <summary>Prepared deferred function.</summary>\n    private static string From')
            if label == 'private-helper-last':
                # An actual public member follows a private method; private-only types are valid.
                text = text.replace('    /// <summary>Leaves private helpers', '    /// <summary>Public observation follows a private helper.</summary>\n    public string Observe() => field;\n\n    /// <summary>Leaves private helpers')
            build(label, text, diagnostic)
        build('restored-positive', positive)
    finally:
        source.unlink(missing_ok=True)
    print('ACTUAL_NATIVE_SOURCE_CATEGORY_CONTROLS_PASSED: ' + ', '.join(row[0] for row in mutations))


if __name__ == '__main__':
    raise SystemExit(check())

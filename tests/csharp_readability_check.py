"""Check editable F4 C# output with the installed SDK parser; no package restore sources.

This is a fixture regression, not a shipped analyzer or general consumer acceptance.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def check(extra_paths=()):
    sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'),
                   str(ROOT / 'extensions/program-kit-governance/scripts')]
    import typed_operation
    directory = ROOT / 'artifacts/t' / ('style-' + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True)
    fixture = ROOT / 'tests/fixtures/csharp-readability'
    for path in fixture.iterdir():
        shutil.copyfile(path, directory / path.name)
    for name in ('Directory.Build.props', 'Directory.Build.targets'):
        (directory / name).write_text('<Project/>', encoding='utf-8')
    (directory / 'NuGet.Config').write_text(
        '<configuration><packageSources><clear/></packageSources></configuration>', encoding='utf-8')
    owners = {key: f'src/{key}/{key}.csproj' for key in ('core', 'runtime', 'api', 'provider', 'test')}
    owners.update(frontend='web/app', generatedTypes='tools/openapi/labels/generated/types.ts')
    output = typed_operation.render(owners, ROOT / 'extensions')
    paths = []
    for name, content in output.items():
        if not name.endswith('.cs'):
            continue
        path = directory / 'emitted' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        paths.append(str(path))
    # The parser project must not compile the emitted application as its own code.
    project = directory / 'Readability.csproj'
    text = project.read_text(encoding='utf-8').replace('<OutputType>',
        '<EnableDefaultCompileItems>false</EnableDefaultCompileItems><OutputType>')
    text = text.replace('<ItemGroup>', '<ItemGroup><Compile Include="Program.cs" />', 1)
    project.write_text(text, encoding='utf-8')
    paths.append(str(directory / 'Program.cs'))
    from coding_label_check import ORACLE
    oracle = directory / 'LabelBehavior.cs'
    oracle.write_text(ORACLE, encoding='utf-8')
    paths.append(str(oracle))
    paths.extend(str(path) for path in extra_paths)
    run = subprocess.run(['dotnet', 'run', '--project', str(project), '--configuration', 'Release', '--', *paths],
                         cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
    print(run.stdout, end='')
    print(run.stderr, end='')
    print('Readability parser and actual emitted source retained: ' + str(directory))
    return run.returncode


if __name__ == '__main__':
    raise SystemExit(check())

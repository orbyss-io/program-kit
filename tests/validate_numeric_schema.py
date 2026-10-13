"""Investigate truthful numeric schemas without changing parser or compatibility authority."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def main():
    evidence = ROOT / 'artifacts/tests/numeric-schema' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
    from dependency_profile import resolver
    blocks = resolver()
    catalog = blocks.new_project_catalog()
    version = catalog['packages']['nuget:Orbyss.Foundation.Json']['version']
    shutil.copyfile(TEMPLATE / 'global.json', evidence / 'global.json')
    shutil.copyfile(ROOT / 'tests/fixtures/composition-numeric/Program.cs', evidence / 'Program.cs')
    (evidence / 'Probe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
        '<TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><ImplicitUsings>enable</ImplicitUsings>'
        '<InterceptorsNamespaces>$(InterceptorsNamespaces);Microsoft.AspNetCore.OpenApi.Generated</InterceptorsNamespaces>'
        '<ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup>'
        '<PackageReference Include="Orbyss.Foundation.Json" Version="' + version + '" />'
        '<PackageReference Include="Orbyss.Foundation.Web.OpenApi" Version="' + catalog['packages']['nuget:Orbyss.Foundation.Web.OpenApi']['version'] + '" /></ItemGroup></Project>')
    (evidence / 'NuGet.config').write_text('<configuration><packageSources><clear />'
        '<add key="nuget.org" value="https://api.nuget.org/v3/index.json" /></packageSources></configuration>')
    for name, command in [('renew', ['dotnet', 'restore', 'Probe.csproj', '--use-lock-file', '--force-evaluate']),
                          ('locked', ['dotnet', 'restore', 'Probe.csproj', '--locked-mode']),
                          ('run', ['dotnet', 'run', '--project', 'Probe.csproj', '--no-restore'])]:
        result = subprocess.run(command, cwd=evidence, capture_output=True, text=True, timeout=240)
        (evidence / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise AssertionError('Numeric schema probe failed: ' + str(evidence / (name + '.log')))
    schemas = {key: json.loads((evidence / filename).read_text()) for key, filename in
               [('aspnet', 'aspnet-default.schema.json'), ('profile', 'foundation-profile.schema.json'), ('scoped', 'scoped-dto.schema.json')]}
    for field, numeric in [('amount', 'number'), ('count', 'integer')]:
        assert set(schemas['aspnet']['properties'][field]['type']) == {numeric, 'string'}
        assert schemas['profile']['properties'][field]['type'] == numeric
        assert schemas['scoped']['properties'][field]['type'] == numeric
    assert 'STRICT_NUMERIC_PROFILE_OK' in (evidence / 'run.log').read_text()
    produced = json.loads((evidence / 'producer.openapi.json').read_text())['components']['schemas']
    for field, numeric in [('amount', 'number'), ('count', 'integer')]:
        assert set(produced['NumericRequest']['properties'][field]['type']) == {numeric, 'string'}
        assert produced['StrictNumericRequest']['properties'][field]['type'] == numeric
    (evidence / 'result.json').write_text(json.dumps({'status': 'passed', 'foundationJson': version,
        'aspnetDefaultMismatchReproduced': True, 'profileMetadataTruthful': True, 'numericStringsRejected': True,
        'actualOpenApiProducerVerified': True,
        'scopedDtoCandidateVerified': True, 'contractApproval': 'pending-consumer-review',
        'scope': 'Profile schema investigation. No parser, baseline or consumer approval changed.'}, indent=2))
    print('Numeric profile investigation passed: ' + str(evidence))


if __name__ == '__main__':
    main()

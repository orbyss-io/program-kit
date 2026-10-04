"""Pack managed consumer features with the public Foundation-owned descriptor builder."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def main() -> int:
    with tempfile.TemporaryDirectory(prefix='pkfd-') as directory:
        root = Path(directory)
        for relative in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props',
                         'NuGet.config', 'global.json', '.program-kit/eng/ProgramKit.Build.props',
                         '.program-kit/eng/ProgramKit.Build.targets', '.program-kit/eng/ProgramKit.Packages.props'):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(TEMPLATE / relative, target)
        feature = root / 'Feature/Example.Feature.csproj'
        feature.parent.mkdir()
        feature.write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<IsPackable>true</IsPackable><Version>1.0.0</Version><PackageId>Example.Feature</PackageId>
<AssemblyName>Example.Feature</AssemblyName><FoundationFeatureIdentity>Example</FoundationFeatureIdentity>
<ProgramKitFeatureDependencies>FoundationTasks</ProgramKitFeatureDependencies>
<ProgramKitFeatureRoutes>/example</ProgramKitFeatureRoutes><ProgramKitFeatureDormant>true</ProgramKitFeatureDormant>
</PropertyGroup></Project>''', encoding='utf-8')
        (feature.parent / 'Feature.cs').write_text('namespace Example; /// <summary>Consumer feature.</summary>\npublic sealed class Feature {}', encoding='utf-8')
        output = root / 'packages'
        environment = dict(os.environ, MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0')

        def run(*arguments: str, success: bool = True) -> str:
            result = subprocess.run(['dotnet', *arguments], cwd=root, env=environment,
                                    capture_output=True, text=True, timeout=180)
            if success:
                assert result.returncode == 0, result.stdout + result.stderr
            else:
                assert result.returncode != 0, 'Invalid feature unexpectedly packed'
            return result.stdout + result.stderr

        # A fresh owned cache cannot reuse private qualification bytes under the public version.
        cache = root / 'nuget-cache'
        run('restore', str(feature), '--configfile', str(root / 'NuGet.config'), '--packages', str(cache))
        run('restore', str(feature), '--locked-mode', '--configfile', str(root / 'NuGet.config'), '--packages', str(cache))
        run('pack', str(feature), '--no-restore', '-c', 'Release', '--output', str(output))
        with zipfile.ZipFile(output / 'Example.Feature.1.0.0.nupkg') as archive:
            assert 'orbyss-foundation/feature.json' in archive.namelist()
            assert 'program-kit/feature.json' not in archive.namelist()
            descriptor = json.loads(archive.read('orbyss-foundation/feature.json'))
            assert descriptor['identity'] == 'Example' and descriptor['packageId'] == 'Example.Feature'
            assert descriptor['featureDependencies'] == ['FoundationTasks']
            assert descriptor['routes'] == ['/example'] and descriptor['dormant'] is True
            assert descriptor['composeForOpenApi'] is True
            nuspec = ET.fromstring(archive.read('Example.Feature.nuspec'))
            assert not any(item.attrib.get('id') in {'Orbyss.Foundation.Build', 'Orbyss.Foundation.Analyzers'}
                           for item in nuspec.iter())
        print('Canonical consumer descriptor and private engineering package boundary passed.')
        conflicting = run('pack', str(feature), '--no-restore', '-c', 'Release',
                          '-p:FoundationFeatureRoutes=/conflict', success=False)
        assert 'PKF104' in conflicting, conflicting
        for arguments, code in ((('-p:IsPackable=false',), 'PKF100'),
                                (('-p:AssemblyName=Different',), 'PKF101'),
                                (('-p:FoundationBuildTaskAssembly=missing.dll',), 'PKF103')):
            rejected = run('pack', str(feature), '--no-restore', '-c', 'Release', *arguments, success=False)
            assert code in rejected, rejected
        print('Conflicting declarations, non-packable features, assembly mismatch and missing builder reject.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

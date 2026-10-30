"""Offline native MSBuild regression under synthetic consumer imports; no agents."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from runtime_fixture import standalone_build_files


class FixtureIsolationTests(unittest.TestCase):
    def test_pickup_archives_authored_boundary_and_changes_only_new_draft(self):
        import fixture_readiness as readiness
        with tempfile.TemporaryDirectory(prefix='pk-boundary-') as directory:
            root = Path(directory).resolve()
            docs = root / 'docs'; docs.mkdir()
            original = b'<Project><!-- historical authored boundary --></Project>'
            (docs / 'boundary.props').write_bytes(original)
            (docs / 'Probe.csproj').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally></PropertyGroup></Project>')
            recipe = docs / 'historical.py'; recipe.write_text('# synthetic retained recipe')
            contract = {'fixtures': {'Directory.Build.props': 'docs/boundary.props', 'Probe.csproj': 'docs/Probe.csproj'},
                        'dependencyTargets': ['Probe.csproj']}
            recipe.with_suffix('.contract.json').write_text(json.dumps(contract))
            blocks = SimpleNamespace(effective_dependency_context=lambda _: {'sources': {}, 'sharedAbi': {'pins': {}}})
            with patch('compatibility_scope.catalog', return_value=(blocks, {'packages': {}}, None)), \
                 patch.object(readiness, 'native_pins', return_value=({}, {})):
                self.assertEqual(['docs/boundary.props'], readiness.stale_inputs(root, contract))
                preview, _ = readiness.preview(root, 'docs/historical.contract.json', 'current')
                readiness.apply(root, 'docs/historical.contract.json', 'current', preview['planDigest'])
            self.assertEqual(original, (docs / 'boundary.props').read_bytes())
            self.assertEqual(standalone_build_files()['Directory.Build.props'], (docs / 'current.fixtures/Directory.Build.props').read_bytes())
            record = json.loads((root / '.program-kit/fixture-pickup/current.json').read_text())
            self.assertIn('docs/boundary.props', record['archives'])

    def test_preparation_blocks_ancestor_items_and_targets_before_sdk_imports(self):
        with tempfile.TemporaryDirectory(prefix='pk-import-') as directory:
            root = Path(directory).resolve()
            (root / 'scripts').mkdir()
            (root / 'scripts/Consumer.props').write_bytes((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/config/program-kit/build/ProgramKit.Build.props').read_bytes())
            props = b'<Project><Import Project="scripts/Consumer.props" /></Project>'
            targets = b'<Project><PropertyGroup><SyntheticConsumerTargets>inherited</SyntheticConsumerTargets></PropertyGroup></Project>'
            (root / 'Directory.Build.props').write_bytes(props)
            (root / 'Directory.Build.targets').write_bytes(targets)
            (root / 'Directory.Packages.props').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup><PackageVersion Include="Synthetic.Consumer.Analyzers" Version="9.9.9" /></ItemGroup></Project>')
            source = root / 'probe.csproj'
            source.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><ImportDirectoryBuildProps>false</ImportDirectoryBuildProps><ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>')
            (root / 'Program.cs').write_text('System.Console.WriteLine("ISOLATION_OK");')
            scratch = root / 'proof/nested/scratch'; scratch.mkdir(parents=True)
            (scratch / 'Probe.csproj').write_bytes(source.read_bytes())
            (scratch / 'NuGet.config').write_text('<configuration><packageSources><clear /></packageSources></configuration>')
            evidence = ROOT / 'artifacts/fixture-isolation' / uuid.uuid4().hex[:12]
            evidence.mkdir(parents=True)
            operations = []
            def run(*args):
                result = subprocess.run(['dotnet', *args], cwd=scratch, capture_output=True, text=True, encoding='utf-8', timeout=90)
                operations.append({'command': ['dotnet', *args], 'exitCode': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
                (evidence / 'operations.json').write_text(json.dumps(operations, indent=2), encoding='utf-8')
                return result
            broken = run('restore', 'Probe.csproj', '--configfile', 'NuGet.config', '--verbosity', 'quiet')
            self.assertNotEqual(0, broken.returncode)
            self.assertIn('NU1015', broken.stdout + broken.stderr)
            offline = b'<configuration><packageSources><clear /></packageSources></configuration>'
            # Exercise the current standalone boundary directly. The retired
            # bootstrap proof runner is not part of consumer installation.
            scratch.mkdir(parents=True, exist_ok=True)
            (scratch / 'Probe.csproj').write_bytes(source.read_bytes())
            (scratch / 'Program.cs').write_bytes((root / 'Program.cs').read_bytes())
            (scratch / 'NuGet.config').write_bytes(offline)
            for name, payload in standalone_build_files().items():
                (scratch / name).write_bytes(payload)
                self.assertEqual(payload, (scratch / name).read_bytes())
            # Both root and nested targets must stop before ancestor imports.
            nested = scratch / 'Nested'; nested.mkdir()
            (nested / 'Pinned.csproj').write_text(source.read_text().replace('</Project>', '<ItemGroup><PackageReference Include="Synthetic.Direct" Version="2.3.4" /></ItemGroup></Project>'))
            for project in ('Probe.csproj', 'Nested/Pinned.csproj'):
                evaluated = run('msbuild', project, '-nologo', '-getItem:PackageReference', '-getProperty:ManagePackageVersionsCentrally,SyntheticConsumerTargets,ProgramKitStandaloneFixtureVersion')
                self.assertEqual(0, evaluated.returncode, evaluated.stdout + evaluated.stderr)
                value = json.loads(evaluated.stdout)
                self.assertEqual('false', value['Properties']['ManagePackageVersionsCentrally'])
                self.assertEqual('', value['Properties']['SyntheticConsumerTargets'])
                self.assertEqual('1', value['Properties']['ProgramKitStandaloneFixtureVersion'])
                references = value['Items']['PackageReference']
                self.assertEqual([] if project == 'Probe.csproj' else ['Synthetic.Direct'], [item['Identity'] for item in references])
                if references: self.assertEqual('2.3.4', references[0]['Version'])
            # Exclude the nested project from this tiny program's default glob.
            import shutil
            shutil.rmtree(nested)
            restored = run('restore', 'Probe.csproj', '--configfile', 'NuGet.config', '--verbosity', 'quiet')
            self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)
            executed = run('run', '--project', 'Probe.csproj', '--no-restore')
            self.assertEqual(0, executed.returncode, executed.stdout + executed.stderr)
            self.assertIn('ISOLATION_OK', executed.stdout)
            self.assertEqual(props, (root / 'Directory.Build.props').read_bytes())
            self.assertEqual(targets, (root / 'Directory.Build.targets').read_bytes())
            retained = run('msbuild', str(source), '-nologo', '-getItem:PackageReference')
            self.assertEqual(0, retained.returncode, retained.stdout + retained.stderr)
            self.assertIn('Orbyss.Foundation.Analyzers', retained.stdout)
            print('Retained offline native import diagnostics: ' + str(evidence))


if __name__ == '__main__':
    unittest.main()

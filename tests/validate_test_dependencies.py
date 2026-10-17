"""Responsibility-derived test scaffold and selected central-pin admission."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import repository_architecture as architecture
import test_project


class TestDependencies(unittest.TestCase):
    def test_exact_qualified_alias_preserves_selected_identity_and_normal_nuget_casing(self):
        for identity in ('xunit.v3', 'XUnit.V3', 'xunit.v3.mtp-v2'):
            with self.subTest(identity=identity):
                project = copy.deepcopy(self.project)
                project['packageReferences'] = [identity]
                payload = test_project.scaffold(project, {'xunit.v3': '4.0.2', 'xunit.v3.mtp-v2': '4.0.2',
                    'cshells.abstractions': '0.0.30'})
                references = [p.get('Include') for p in ET.fromstring(payload).iter('PackageReference')]
                self.assertIn(identity, references)
                self.assertNotIn('Microsoft.NET.Test.Sdk', references)
        for packages, pins in ((['xunit.v3'], {'xunit.v3': '3.2.2'}),
                               (['xunit.v3'], {'xunit.v3': '4.0.3'}),
                               (['xunit.v3'], {}),
                               (['xunit.v3', 'xunit.v3.mtp-v2'], {'xunit.v3': '4.0.2', 'xunit.v3.mtp-v2': '4.0.2'}),
                               ([], {})):
            with self.assertRaisesRegex(ValueError, 'PKA020'):
                test_project.runner_capability(packages, pins)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-dependencies-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'eng').mkdir()
        self.project = {'path': 'tests/Owned.Tests/Owned.Tests.csproj', 'role': 'test',
                        'projectReferences': [], 'packageReferences': ['xunit.v3.mtp-v2'],
                        'responsibilities': [{'name': 'owned lifecycle proof', 'kind': 'test',
                                              'effects': [], 'testSeams': ['shell-lifecycle']}]}
        self.manifest = {'runtimeComposition': {'projects': [self.project], 'bindings': []}}
        self.save()
        (self.root / 'Directory.Packages.props').write_text('<Project><Import Project="eng/selected.props" /></Project>')
        (self.root / 'eng/selected.props').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup>'
            '<PackageVersion Include="CShells.Abstractions" Version="0.0.30" />'
            '<PackageVersion Include="CShells.AspNetCore.Abstractions" Version="0.0.30" />'
            '<PackageVersion Include="xunit.v3.mtp-v2" Version="3.2.2" /></ItemGroup></Project>')

    def save(self):
        (self.root / 'eng/architecture.json').write_text(json.dumps(self.manifest))

    def test_planning_rejects_missing_direct_contract_and_unknown_or_absent_uses(self):
        with self.assertRaisesRegex(ValueError, 'missing direct.*CShells.Abstractions'):
            architecture.validate_manifest(self.root, self.manifest)
        for seams in (['unsupported-converter'], None):
            project = copy.deepcopy(self.project)
            project['packageReferences'].append('CShells.Abstractions')
            if seams is None:
                project['responsibilities'][0].pop('testSeams')
            else:
                project['responsibilities'][0]['testSeams'] = seams
            with self.subTest(seams=seams), self.assertRaisesRegex(ValueError, 'PKA020'):
                architecture.test_compile_contracts(project, required=True)

    def test_new_projects_derive_only_actual_contracts_and_keep_selected_pins(self):
        before = (self.root / 'eng/selected.props').read_bytes()
        for seam, expected in (('pure-core', set()), ('shell-lifecycle', {'CShells.Abstractions'}),
                               ('api-feature', {'CShells.Abstractions', 'CShells.AspNetCore.Abstractions'}),
                               ('activation', {'CShells.Abstractions', 'CShells.AspNetCore.Abstractions'})):
            self.project['responsibilities'][0]['testSeams'] = [seam]
            self.save()
            plan = test_project.preview(self.root, self.project['path'])
            generated = ET.fromstring(plan['changes'][self.project['path']])
            references = {p.get('Include'): p.attrib for p in generated.iter('PackageReference')}
            self.assertEqual(expected, set(references) - {'xunit.v3.mtp-v2'})
            for contract in expected:
                self.assertEqual('all', references[contract]['PrivateAssets'])
                self.assertNotIn('Version', references[contract])
                self.assertEqual('0.0.30', plan['compileContractPins'][contract])
            inventory = json.loads(plan['changes']['eng/architecture.json'])['runtimeComposition']['projects'][0]
            self.assertEqual(set(references), set(inventory['packageReferences']))
        self.assertEqual(before, (self.root / 'eng/selected.props').read_bytes())

    def test_apply_is_bound_to_selected_inputs_and_preserves_existing_authored_project(self):
        plan = test_project.preview(self.root, self.project['path'])
        original = (self.root / 'eng/architecture.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            test_project.apply(self.root, self.project['path'], 'wrong-digest')
        self.assertEqual(original, (self.root / 'eng/architecture.json').read_bytes())
        test_project.apply(self.root, self.project['path'], plan['planDigest'])
        target = self.root / self.project['path']; before = target.read_bytes()
        architecture.validate_manifest(self.root, json.loads((self.root / 'eng/architecture.json').read_text()))
        with self.assertRaisesRegex(ValueError, 'consumer-owned'):
            test_project.preview(self.root, self.project['path'])
        self.assertEqual(before, target.read_bytes())

    def test_missing_selected_pin_and_dynamic_pins_fail_without_partial_write(self):
        selected = self.root / 'eng/selected.props'
        for content in ('<Project><ItemGroup><PackageVersion Include="xunit.v3.mtp-v2" Version="3.2.2" /></ItemGroup></Project>',
                        '<Project><Import Project="$(OtherPins)" /></Project>'):
            selected.write_text(content)
            with self.assertRaises(ValueError):
                test_project.preview(self.root, self.project['path'])
            self.assertFalse((self.root / self.project['path']).exists())

    def test_after_plan_admission_checks_the_selected_contract_pin_before_source_exists(self):
        self.project['packageReferences'].append('CShells.Abstractions')
        self.save()
        self.assertEqual(1, len(architecture.validate_planned(self.root, self.manifest, require_responsibilities=True)))
        selected = self.root / 'eng/selected.props'
        selected.write_text(selected.read_text().replace('<PackageVersion Include="CShells.Abstractions" Version="0.0.30" />', ''))
        with self.assertRaisesRegex(ValueError, 'missing selected central.*Owned.Tests.*CShells.Abstractions'):
            architecture.validate_planned(self.root, self.manifest, require_responsibilities=True)
        self.assertFalse((self.root / self.project['path']).exists())


class NativeRunner(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='native-test-runner-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_qualified_runner_scaffolds_restore_build_and_execute_named_native_cases(self):
        for index, (identity, version) in enumerate(sorted(test_project.QUALIFIED_MTP_RUNNERS)):
            with self.subTest(identity=identity, version=version):
                root = self.root / ('native-' + str(index))
                (root / 'eng').mkdir(parents=True)
                project = {'path': 'tests/Proof/Proof.csproj', 'role': 'test', 'projectReferences': [],
                           'packageReferences': [identity], 'responsibilities': [
                               {'name': 'named native proof', 'kind': 'test', 'effects': [], 'testSeams': ['pure-core']}]}
                (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [project], 'bindings': []}}))
                (root / 'global.json').write_bytes((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json').read_bytes())
                (root / 'Directory.Build.props').write_text('<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>')
                (root / 'Directory.Packages.props').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup><PackageVersion Include="' + identity + '" Version="' + version + '" /></ItemGroup></Project>')
                (root / 'NuGet.config').write_text('<configuration><packageSources><clear/><add key="public" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
                proposal = test_project.preview(root, project['path'])
                test_project.apply(root, project['path'], proposal['planDigest'])
                (root / 'tests/Proof/Proof.cs').write_text('namespace RunnerProof; public class NativeCase { [Xunit.Fact] public void NamedNativeCase() { Xunit.Assert.Equal(4, 2 + 2); } }')
                for args in (['restore', project['path'], '--use-lock-file'],
                             ['build', project['path'], '-c', 'Release', '--no-restore'],
                             ['test', '--project', project['path'], '-c', 'Release', '--no-build', '--no-restore',
                              '--minimum-expected-tests', '1', '--fail-skips', 'on', '--report-xunit-trx',
                              '--report-xunit-trx-filename', 'named.trx', '--results-directory', str(root / 'results')]):
                    observed = subprocess.run(['dotnet', *args], cwd=root, capture_output=True, text=True, timeout=180)
                    self.assertEqual(0, observed.returncode, str(args) + '\n' + observed.stdout + observed.stderr)
                reports = list((root / 'results').rglob('*.trx'))
                self.assertTrue(reports, 'Native execution must retain its actual named report')
                cases = [row for report in reports for row in ET.parse(report).getroot().iter()
                         if row.tag.rsplit('}', 1)[-1] == 'UnitTestResult']
                self.assertEqual(1, len(cases))
                self.assertIn('NamedNativeCase', cases[0].get('testName', ''))
                self.assertEqual('Passed', cases[0].get('outcome'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', action='store_true', help='Restore, build and execute the qualified native runners')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeRunner if args.native else TestDependencies)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())

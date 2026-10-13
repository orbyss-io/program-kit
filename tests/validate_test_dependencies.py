"""Responsibility-derived test scaffold and selected central-pin admission."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import repository_architecture as architecture
import test_project


class TestDependencies(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()

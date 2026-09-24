"""Architecture recipe regression inputs, including evaluated/imported and compiled-only edges."""
import copy
import json
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from architecture_verify import validate_graph, execute


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='architecture-recipe-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifest = {'runtimeComposition': {'projects': [
            {'path': 'Core/Slots.Core.csproj', 'role': 'core', 'projectReferences': [], 'packageReferences': []},
            {'path': 'Provider/Slots.Provider.csproj', 'role': 'provider', 'projectReferences': ['Core/Slots.Core.csproj'], 'packageReferences': []}],
            'bindings': [{'capabilityProject': 'Core/Slots.Core.csproj', 'implementationProject': 'Provider/Slots.Provider.csproj',
                          'capability': 'Slots.ISlots', 'implementation': 'Slots.Provider', 'registration': 'Slots.Services.Register'}]}}
        self.evaluated = {p['path']: {'Properties': {'AssemblyName': Path(p['path']).stem}, 'Items': {
            'PackageReference': [], 'ProjectReference': [{'Identity': r, 'FullPath': str(self.root / r)} for r in p['projectReferences']]}}
                          for p in self.manifest['runtimeComposition']['projects']}
        self.compiled = [{'name': 'Slots.Core', 'references': ['System.Runtime'], 'types': [
            {'name': 'Slots.ISlots', 'isInterface': True, 'baseType': '', 'interfaces': [], 'methods': ['Reserve']}]},
            {'name': 'Slots.Provider', 'references': ['System.Runtime', 'Slots.Core'], 'types': [
                {'name': 'Slots.Provider', 'isInterface': False, 'baseType': 'System.Object', 'interfaces': ['Slots.ISlots'], 'methods': ['Reserve']},
                {'name': 'Slots.Services', 'isInterface': False, 'baseType': 'System.Object', 'interfaces': [], 'methods': ['Register']}]}]

    def check(self):
        return validate_graph(self.root, self.manifest, self.evaluated, self.compiled)

    def test_real_build_and_imported_forbidden_reference(self):
        self.assertIsNotNone(shutil.which('dotnet'), 'The architecture recipe requires the selected .NET SDK')
        (self.root / 'NuGet.Config').write_text('<configuration><packageSources><clear/></packageSources></configuration>', encoding='utf-8')
        for project in self.manifest['runtimeComposition']['projects']:
            path = self.root / project['path']
            path.parent.mkdir(parents=True)
            references = ''.join('<ProjectReference Include="' + str(self.root / ref) + '" />' for ref in project['projectReferences'])
            path.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
                            '<NuGetAudit>false</NuGetAudit></PropertyGroup><ItemGroup>' + references + '</ItemGroup>'
                            '<Import Project="Extra.props" Condition="Exists(&apos;Extra.props&apos;)" /></Project>', encoding='utf-8')
        (self.root / 'Core/Slots.cs').write_text('namespace Slots; public interface ISlots { int Reserve(string key); }', encoding='utf-8')
        (self.root / 'Provider/Provider.cs').write_text(
            'namespace Slots; public sealed class Provider : ISlots { public int Reserve(string key) => 1; } '
            'public static class Services { public static ISlots Register() => new Provider(); }', encoding='utf-8')
        def restore(path):
            result = subprocess.run(['dotnet', 'restore', str(path), '--configfile', str(self.root / 'NuGet.Config')],
                                    cwd=self.root, capture_output=True, text=True, timeout=180)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        restore(self.root / 'Provider/Slots.Provider.csproj')
        self.assertEqual(2, len(execute(self.root, self.manifest, 'Debug')))
        rogue = self.root / 'Rogue/Rogue.csproj'
        rogue.parent.mkdir()
        rogue.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>', encoding='utf-8')
        (self.root / 'Core/Extra.props').write_text('<Project><ItemGroup><ProjectReference Include="../Rogue/Rogue.csproj" /></ItemGroup></Project>', encoding='utf-8')
        restore(self.root / 'Provider/Slots.Provider.csproj')
        with self.assertRaisesRegex(ValueError, 'Evaluated references differ'):
            execute(self.root, self.manifest, 'Debug')

    def test_compiled_capability_and_evaluated_graph(self):
        self.assertEqual(2, len(self.check()))

    def test_imported_reference_is_not_hidden_by_raw_project_xml(self):
        self.evaluated['Core/Slots.Core.csproj']['Items']['ProjectReference'] = [
            {'Identity': '../Provider/Slots.Provider.csproj', 'FullPath': str(self.root / 'Provider/Slots.Provider.csproj')}]
        with self.assertRaisesRegex(ValueError, 'Evaluated references differ'):
            self.check()

    def test_compiled_dll_reference_is_guarded(self):
        self.compiled[0]['references'].append('Slots.Provider')
        with self.assertRaisesRegex(ValueError, 'Compiled project edge'):
            self.check()

    def test_core_serializer_leak_is_guarded(self):
        self.compiled[0]['references'].append('System.Text.Json')
        with self.assertRaisesRegex(ValueError, 'Core leaks'):
            self.check()

    def test_invented_interface_or_registration_fails(self):
        original = copy.deepcopy(self.manifest)
        for key in ('capability', 'registration'):
            self.manifest = copy.deepcopy(original)
            self.manifest['runtimeComposition']['bindings'][0][key] = 'Invented.Name'
            with self.assertRaises(ValueError):
                self.check()

    def test_real_class_without_interface_fails(self):
        self.compiled[1]['types'][0]['interfaces'] = []
        with self.assertRaisesRegex(ValueError, 'does not implement'):
            self.check()


if __name__ == '__main__':
    unittest.main()

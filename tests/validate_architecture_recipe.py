"""Architecture recipe regression inputs, including evaluated/imported and compiled-only edges."""
import copy
import json
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from architecture_verify import validate_graph, execute
import repository_architecture as recipe


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
        subprocess.run(['dotnet', 'new', 'sln', '--name', 'Consumer'], cwd=self.root,
                       capture_output=True, check=True, timeout=60)
        solution = next(self.root.glob('Consumer.sln*'))
        subprocess.run(['dotnet', 'sln', str(solution), 'add', *[str(self.root/p['path'])
                       for p in self.manifest['runtimeComposition']['projects']]], cwd=self.root,
                       capture_output=True, check=True, timeout=60)
        self.assertEqual(2, len(recipe.execute(self.root, self.manifest, 'Debug',
                               build_subject=solution.name, version='9.0.0')))
        subprocess.run(['dotnet', 'sln', str(solution), 'remove', str(self.root/'Provider/Slots.Provider.csproj')],
                       cwd=self.root, capture_output=True, check=True, timeout=60)
        with self.assertRaisesRegex(ValueError, 'include every declared'):
            recipe.execute(self.root, self.manifest, 'Debug', build_subject=solution.name)
        rogue = self.root / 'Rogue/Rogue.csproj'
        rogue.parent.mkdir()
        rogue.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>', encoding='utf-8')
        (self.root / 'Core/Extra.props').write_text('<Project><ItemGroup><ProjectReference Include="../Rogue/Rogue.csproj" /></ItemGroup></Project>', encoding='utf-8')
        restore(self.root / 'Provider/Slots.Provider.csproj')
        with self.assertRaisesRegex(ValueError, 'Evaluated references differ'):
            execute(self.root, self.manifest, 'Debug')

    def test_compiled_capability_and_evaluated_graph(self):
        self.assertEqual(2, len(self.check()))

    def test_binding_roles_and_physical_separation_are_mandatory(self):
        for index, role, message in ((0, 'composition', 'capability.*Core'),
                                     (1, 'composition', 'implementation.*role')):
            with self.subTest(role=role, index=index):
                original = self.manifest['runtimeComposition']['projects'][index]['role']
                self.manifest['runtimeComposition']['projects'][index]['role'] = role
                with self.assertRaisesRegex(ValueError, message): self.check()
                self.manifest['runtimeComposition']['projects'][index]['role'] = original
        binding = self.manifest['runtimeComposition']['bindings'][0]
        binding['implementationProject'] = binding['capabilityProject']
        with self.assertRaisesRegex(ValueError, 'distinct'): self.check()

    def test_omitted_active_capability_is_rejected(self):
        self.manifest['runtimeComposition']['bindings'] = []
        with self.assertRaisesRegex(ValueError, 'Unlisted active capability'): self.check()

    def test_core_role_relabel_and_namespace_waiver_are_rejected(self):
        self.manifest['runtimeComposition']['projects'][0]['role'] = 'provider'
        with self.assertRaisesRegex(ValueError, 'Core.*role'): self.check()
        self.manifest['runtimeComposition']['projects'][0]['role'] = 'core'
        self.manifest['runtimeComposition']['projects'][1]['persistenceOwnerNamespaces'] = ['Slots.Provider']
        with self.assertRaisesRegex(ValueError, 'namespace.*boundary'): self.check()

    def test_mixed_workbench_graph_is_rejected_even_without_bindings(self):
        self.manifest = {'runtimeComposition': {'projects': [{'path': 'Workbench/Workbench.csproj',
            'role': 'provider'}], 'bindings': []}}
        self.evaluated = {'Workbench/Workbench.csproj': {'Properties': {'AssemblyName': 'Workbench'},
            'Items': {'ProjectReference': [], 'PackageReference': [{'Identity': 'Microsoft.EntityFrameworkCore'}]}}}
        self.compiled = [{'name': 'Workbench', 'references': ['Microsoft.EntityFrameworkCore'], 'types': [
            {'name': 'Workbench.Core.INotes', 'isInterface': True, 'baseType': '', 'interfaces': [], 'methods': []}]}]
        with self.assertRaisesRegex(ValueError, 'Core types.*separate'): self.check()

    def test_compiled_persistence_dependency_cannot_hide_in_composition(self):
        self.manifest['runtimeComposition']['projects'][1]['role'] = 'composition'
        self.manifest['runtimeComposition']['bindings'] = []
        self.compiled[1]['references'].append('Microsoft.EntityFrameworkCore')
        with self.assertRaisesRegex(ValueError, 'Persistence.*provider'): self.check()

    def test_provider_cannot_relabel_api_types_or_unused_core_packages(self):
        self.compiled[1]['types'].append({'name': 'Slots.Api.Operations.Read.Endpoint', 'isInterface': False,
            'baseType': 'System.Object', 'interfaces': [], 'methods': []})
        with self.assertRaisesRegex(ValueError, 'API types.*separate'): self.check()
        self.compiled[1]['types'].pop()
        self.manifest['runtimeComposition']['projects'][0].pop('packageReferences')
        self.evaluated['Core/Slots.Core.csproj']['Items']['PackageReference'] = [{'Identity': 'System.Text.Json'}]
        with self.assertRaisesRegex(ValueError, 'Core leaks'): self.check()

    def test_planned_graph_checks_the_same_roles_without_building(self):
        validate = getattr(recipe, 'validate_manifest', None)
        self.assertIsNotNone(validate, 'Planned architecture validation must exist')
        validate(self.root, self.manifest)
        self.manifest['runtimeComposition']['projects'][1]['role'] = 'composition'
        with self.assertRaisesRegex(ValueError, 'implementation.*role'):
            validate(self.root, self.manifest)

    def test_empty_initial_and_pure_core_graphs_remain_valid(self):
        validate = getattr(recipe, 'validate_manifest', None)
        self.assertIsNotNone(validate, 'Planned architecture validation must exist')
        validate(self.root, {'runtimeComposition': {'projects': [], 'bindings': []}})
        self.manifest['runtimeComposition']['projects'] = self.manifest['runtimeComposition']['projects'][:1]
        self.manifest['runtimeComposition']['bindings'] = []
        self.evaluated = {key: value for key, value in self.evaluated.items() if key.startswith('Core/')}
        self.compiled = self.compiled[:1]
        self.compiled[0]['types'].append({'name': 'Slots.UnicodeText', 'isInterface': False,
            'baseType': 'System.Object', 'interfaces': [], 'methods': ['Admit']})
        self.assertEqual(2, len(self.check()))

    def test_empty_initial_verification_builds_nothing(self):
        with patch.object(recipe.subprocess, 'run', side_effect=AssertionError('No project exists to build')):
            self.assertEqual(2, len(execute(self.root, {'runtimeComposition': {'projects': [], 'bindings': []}}, 'Debug')))

    def test_frozen_original_workbench_graph_is_rejected_without_mutation(self):
        path = ROOT / 'tests/fixtures/foundation-consumer-contracts/baseline/mixed-workbench-architecture.json'
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'namespace.*boundary'):
            recipe.validate_manifest(self.root, json.loads(original))
        self.assertEqual(original, path.read_bytes())

    def test_planned_unassigned_source_project_is_rejected(self):
        path = self.root / 'src/Rogue/Rogue.csproj'; path.parent.mkdir(parents=True)
        path.write_text('<Project Sdk="Microsoft.NET.Sdk" />')
        with self.assertRaisesRegex(ValueError, 'Assign an architectural role'):
            recipe.validate_planned(self.root, self.manifest)

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

    def test_persistence_packages_stay_in_provider_tests_and_design_is_private(self):
        project = self.manifest['runtimeComposition']['projects'][1]
        project.pop('packageReferences')
        self.evaluated[project['path']]['Items']['PackageReference'] = [{'Identity':'Microsoft.EntityFrameworkCore'}]
        self.check()
        project['role']='implementation'
        with self.assertRaisesRegex(ValueError,'owning provider/tests'):self.check()
        project['role']='provider'
        self.evaluated[project['path']]['Items']['PackageReference'] = [{'Identity':'Microsoft.EntityFrameworkCore.Design'}]
        with self.assertRaisesRegex(ValueError,'private engineering'):self.check()
        self.evaluated[project['path']]['Items']['PackageReference'][0]['PrivateAssets']='all'
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

    def test_managed_private_analyzer_and_spoofed_origins(self):
        item = {'Identity': 'Orbyss.Foundation.Analyzers', 'PrivateAssets': 'all',
                'IncludeAssets': 'runtime;build;analyzers',
                'DefiningProjectFullPath': str(self.root / 'eng/ProgramKit.Build.props')}
        self.evaluated['Core/Slots.Core.csproj']['Items']['PackageReference'] = [item]
        self.check()
        for field, value in (('PrivateAssets', ''), ('IncludeAssets', 'all'),
                             ('IncludeAssets', ''), ('IncludeAssets', 'compile;analyzers'),
                             ('DefiningProjectFullPath', str(self.root / 'Fake.props'))):
            with self.subTest(field=field, value=value):
                changed = dict(item, **{field: value})
                self.evaluated['Core/Slots.Core.csproj']['Items']['PackageReference'] = [changed]
                with self.assertRaises(ValueError): self.check()

    def test_unused_duplicate_types_pass_but_capability_parent_ambiguity_fails(self):
        fixture = {'name': 'Tests.SharedFixture', 'isInterface': False,
                   'baseType': '', 'interfaces': [], 'methods': []}
        for assembly in self.compiled: assembly['types'].append(dict(fixture))
        self.check()
        parent = {'name': 'Slots.Parent', 'isInterface': True,
                  'baseType': '', 'interfaces': ['Slots.ISlots'], 'methods': []}
        for assembly in self.compiled: assembly['types'].append(dict(parent))
        self.compiled[1]['types'][0]['interfaces'] = ['Slots.Parent']
        with self.assertRaisesRegex(ValueError, 'Ambiguous capability'): self.check()

    def test_managed_private_descriptor_builder_rejects_runtime_assets_and_spoofing(self):
        item = {'Identity': 'Orbyss.Foundation.Build', 'PrivateAssets': 'all',
                'IncludeAssets': 'build;buildtransitive',
                'DefiningProjectFullPath': str(self.root / 'eng/ProgramKit.Build.targets')}
        self.evaluated['Provider/Slots.Provider.csproj']['Items']['PackageReference'] = [item]
        self.check()
        for field, value in (('PrivateAssets', ''), ('IncludeAssets', 'all'),
                             ('IncludeAssets', 'build;buildtransitive;compile'),
                             ('IncludeAssets', 'build;runtime'),
                             ('DefiningProjectFullPath', str(self.root / 'Fake.targets'))):
            with self.subTest(field=field, value=value):
                self.evaluated['Provider/Slots.Provider.csproj']['Items']['PackageReference'] = [dict(item, **{field: value})]
                with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main()

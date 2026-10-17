"""F2 independent negatives, extension seam and installed-command journey."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from coding_context import compose, validate_units, prepare, task_scope
from phase_obligations import catalog
from dotnet_adapter import bootstrap
bootstrap()
from repository_architecture import evaluate_project
from owned_fixture import FixtureDirectory, native_path


class CodingContextTests(unittest.TestCase):
    def test_added_declaration_selects_without_composer_changes_and_excludes_unrelated_scope(self):
        data = copy.deepcopy(catalog())
        data['codingUnits'] = [{'id': 'new-owned-query', 'ruleIds': ['principle.compilation-boundaries'],
            'when': {'all': ['persistence'], 'not': ['web']}, 'requiredContext': ['model-owner'], 'route': 'manual-edit'}]
        units, excluded, blockers = compose(data, [], {'persistence'}, {'model-owner': True}, ROOT / 'extensions')
        self.assertEqual(['new-owned-query'], [s['id'] for s in units])
        self.assertTrue(units[0]['rules'][0]['fingerprint'])
        self.assertFalse(units[0]['applicationObserved'])
        self.assertFalse(blockers)
        self.assertFalse(compose(data, [], {'web'}, {}, ROOT / 'extensions')[0])
        self.assertTrue(compose(data, [], {'persistence'}, {}, ROOT / 'extensions')[2])

    def test_unknown_duplicate_and_executable_extension_declarations_are_rejected(self):
        data = copy.deepcopy(catalog())
        original = data['codingUnits'][0]
        for alteration in ({'id': original['id']}, {'id': 'other', 'run': 'arbitrary.py'},
                           {'id': 'other', 'ruleIds': ['unknown-rule']}, {'id': 'other', 'requiredContext': ['invented-context']},
                           {'id': 'other', 'route': 'execute-submitted-code'}, {'id': 'other', 'when': {'unknown': []}}):
            current = copy.deepcopy(data)
            current['codingUnits'].append({**original, **alteration})
            with self.subTest(alteration=alteration), self.assertRaisesRegex(ValueError, 'PKC003'):
                validate_units(current)

    def test_missing_recipe_and_canonical_source_cannot_pass(self):
        data = copy.deepcopy(catalog())
        data['codingUnits'] = [{'id': 'recipe-only', 'ruleIds': ['principle.compilation-boundaries'], 'route': 'bound-recipes'}]
        self.assertTrue(compose(data, [], set(), {}, ROOT / 'extensions')[2])
        with patch('coding_context.resolve', side_effect=ValueError('missing canonical owner')):
            units, excluded, blockers = compose(data, [], set(), {}, ROOT / 'extensions')
            self.assertTrue(any(b['code'] == 'PKC019' and b['owner'] == 'program-kit-governance' for b in blockers))

    def test_publisher_binding_receives_selected_consumer_context(self):
        data = copy.deepcopy(catalog())
        data['codingUnits'] = [{'id': 'selected-publisher', 'ruleIds': ['publisher.domain-event-dispatcher'], 'route': 'manual-edit'}]
        def selected(catalog, identity, *, extensions, repository):
            self.assertEqual(ROOT, repository, 'A missing selected context must not become a default capture')
            return {'id': identity, 'text': 'Fictional resolver boundary; actual capture behavior is independently tested in F1.', 'fingerprint': 'fixture'}
        with patch('coding_context.resolve', side_effect=selected):
            units, excluded, blockers = compose(data, [], set(), {}, ROOT / 'extensions', repository=ROOT)
        self.assertTrue(units)
        self.assertFalse(blockers)

    def test_native_query_uses_actual_imports_and_runs_no_target_or_restore(self):
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            (root / 'settings.props').write_text('<Project><PropertyGroup><AssemblyName>ImportedName</AssemblyName></PropertyGroup><ItemGroup Condition="\'$(Configuration)\' == \'Debug\'"><PackageReference Include="Npgsql" Version="10.0.0" /></ItemGroup></Project>')
            (root / 'Test.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><Import Project="settings.props" /><Target Name="Build"><Error Text="must never build" /></Target></Project>')
            (root / 'File.cs').write_text('class File {}')
            original = subprocess.run
            commands = []
            def record(command, **kwargs):
                commands.append(command)
                return original(command, **kwargs)
            with patch('repository_architecture.subprocess.run', side_effect=record):
                value = evaluate_project(root, 'Test.csproj')
            self.assertEqual('ImportedName', value['Properties']['AssemblyName'])
            self.assertEqual('10.0.0', value['Items']['PackageReference'][0]['Version'])
            self.assertTrue(value['Items']['Compile'])
            self.assertFalse(any(arg.startswith(('-target:', '-t:')) or arg in ('build', 'restore') for command in commands for arg in command))
            self.assertFalse((root / 'bin').exists())
            self.assertFalse((root / 'obj').exists())
            with self.assertRaisesRegex(ValueError, 'target framework is not declared'):
                evaluate_project(root, 'Test.csproj', framework='net9.0')

    def test_operation_scope_is_explicit_and_baseline_is_not_reset(self):
        with FixtureDirectory(native=True) as folder:
            feature = Path(folder)
            (feature / 'tasks.md').write_text('- [ ] T001 Work\n')
            self.assertEqual('feature', task_scope(feature, None)['mode'])
            with self.assertRaises(ValueError):
                task_scope(feature, 'missing')

    def test_planned_project_does_not_supply_effective_source_context(self):
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            feature = root / 'specs/001-core'
            feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('C# policy with owned invariants.')
            (feature / 'plan.md').write_text('Use src/Core/Core.csproj.')
            (feature / 'tasks.md').write_text('- [ ] T001 Materialize src/Core/Core.csproj and implement src/Core/Policy.cs.\n')
            (root / 'eng').mkdir()
            (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [
                {'path': 'src/Core/Core.csproj', 'role': 'core', 'projectReferences': [],
                 'responsibilities': [{'name': 'Policy', 'kind': 'pure-policy', 'effects': []}]}], 'bindings': []}}))
            source = prepare(root, feature)
            self.assertFalse(source['coding']['canProceed'])
            self.assertTrue(any(b.get('context') == 'effective-projects' for b in source['coding']['blockers']))
            setup = prepare(root, feature, stage='setup')
            self.assertTrue(setup['coding']['canProceed'])
            self.assertFalse(setup['coding']['nativeContext']['sourceReady'])

    def test_installed_guided_fixture_and_actual_failures(self):
        from coding_review_fixture import scenario
        with FixtureDirectory(native=True) as folder:
            result = scenario(folder)
            self.assertEqual('passed', result['status'])
            self.assertTrue(result['workingInputsUnchanged'])
            self.assertGreaterEqual(sum(c['actualExit'] == 2 for c in result['commands']), 6)
            self.assertTrue((Path(folder) / 'index.md').is_file())


if __name__ == '__main__':
    unittest.main()

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
from knowledge_review_fixture import BRIEF_LIMITS, assert_complete_required_text


class CodingContextTests(unittest.TestCase):
    def test_profile_boolean_uses_the_same_case_semantics_as_msbuild(self):
        from coding_context import source_profile_qualified
        for value in ('true', 'True', 'TRUE'):
            self.assertTrue(source_profile_qualified({'FoundationSourceReadabilityContract': 'source-readability-v1',
                'FoundationSourceReadability': value}))
        self.assertFalse(source_profile_qualified({'FoundationSourceReadabilityContract': 'source-readability-v1',
            'FoundationSourceReadability': 'false'}))
        self.assertFalse(source_profile_qualified({'FoundationSourceReadabilityContract': 'unknown',
            'FoundationSourceReadability': 'True'}))

    def test_actual_native_core_task_does_not_inherit_neighbor_host_units_or_duties(self):
        with FixtureDirectory(native=True) as name:
            root = Path(name); feature = root / 'specs/001-owned'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('C# Core policy and a separately owned host.')
            (feature / 'plan.md').write_text('src/Core/Core.csproj and src/Host/Host.csproj')
            (feature / 'tasks.md').write_text('- [ ] T001 Implement src/Core/Policy.cs in src/Core/Core.csproj.\n- [ ] T002 Implement src/Host/Policy.cs in src/Host/Host.csproj.\n')
            declarations = []
            for owner, role, sdk, kind in [('Core', 'core', 'Microsoft.NET.Sdk', 'pure-policy'),
                    ('Host', 'implementation', 'Microsoft.NET.Sdk.Web', 'http')]:
                project = root / 'src' / owner / (owner + '.csproj'); project.parent.mkdir(parents=True)
                project.write_text('<Project Sdk="' + sdk + '"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
                project.with_name('Policy.cs').write_text('namespace Fixture; public sealed class Policy { public int Evaluate() => 1; }')
                declarations.append({'path': project.relative_to(root).as_posix(), 'role': role, 'projectReferences': [],
                    'responsibilities': [{'name': owner, 'kind': kind, 'effects': []}]})
            (root / 'eng').mkdir(); (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': declarations, 'bindings': []}}))
            value = prepare(root, feature, task_ids=['T001'])
            self.assertEqual([('src/Core/Core.csproj', 'evaluated', 'core')],
                [(p['path'], p['status'], p['role']) for p in value['coding']['projects']])
            self.assertIn('project-role:core', value['coding']['responsibilities'])
            ids = {d['rule'] for d in value['coding']['evaluation']['duties']}
            self.assertNotIn('principle.shell-feature-lifecycle-contract', ids)
            self.assertNotIn('principle.application-bundle-delivery', ids)
            self.assertIn('principle.method-coherence', ids)
            self.assertIn('principle.completed-result-integrity', ids)
            # Scope selection is not acceptance: no selected public analyzer was
            # restored in this structural fixture, and its blocker must remain.
            self.assertIn('PKC024', {b['code'] for b in value['coding']['blockers']})
            import phase_obligations as phase
            output = phase.render(value, 'implementation')
            self.assertLess(len(output.encode('utf-8')), BRIEF_LIMITS['core'])
            assert_complete_required_text(self, catalog(), value['requirements'], output, ROOT / 'extensions')

    def test_shared_domain_persistence_is_design_knowledge_not_core_source_effect(self):
        with FixtureDirectory(native=True) as name:
            root = Path(name); feature = root / 'specs/001-owned'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('- **Specification roadmap entry**: RM-01\nPure domain policy and its separately implemented provider.')
            (feature / 'plan.md').write_text('src/Core/Core.csproj and src/Provider/Provider.csproj')
            (feature / 'tasks.md').write_text('- [ ] T001 Implement src/Core/Policy.cs in src/Core/Core.csproj.\n- [ ] T002 Implement src/Provider/Policy.cs in src/Provider/Provider.csproj.\n')
            brief = root / '.program-kit/specification-intake/RM-01/brief.json'; brief.parent.mkdir(parents=True)
            brief.write_text(json.dumps({'architectureScope': ['domain']}))
            architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'architecture-map.json').write_text(json.dumps({'elements': [
                {'id': 'domain', 'type': 'component', 'technology': '.NET PostgreSQL'}], 'decisions': []}))
            (architecture / 'building-block-selection.json').write_text(json.dumps({'status': 'Accepted',
                'targets': [{'id': owner.lower(), 'kind': 'dotnet-project', 'path': 'src/' + owner + '/' + owner + '.csproj',
                    'placement': {'owner': 'domain'}} for owner in ('Core', 'Provider')], 'instances': []}))
            (architecture / 'bootstrap-decisions.json').write_text(json.dumps({'selected_profiles': ['dotnet'],
                'persistence': [{'owner': 'domain', 'profile': 'postgresql', 'providerProject': 'src/Provider/Provider.csproj', 'status': 'accepted'}]}))
            declarations = []
            for owner, role, kind in [('Core', 'core', 'pure-policy'), ('Provider', 'provider', 'persistence')]:
                project = root / 'src' / owner / (owner + '.csproj'); project.parent.mkdir(parents=True)
                project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
                project.with_name('Policy.cs').write_text('namespace Fixture; public sealed class Policy { public int Evaluate() => 1; }')
                declarations.append({'path': project.relative_to(root).as_posix(), 'role': role, 'projectReferences': [],
                    'responsibilities': [{'name': owner, 'kind': kind, 'effects': []}]})
            graph = root / 'eng/architecture.json'; graph.parent.mkdir()
            def save_graph():
                graph.write_text(json.dumps({'runtimeComposition': {'projects': declarations, 'bindings': []}}))
            save_graph()
            def snapshot(task):
                value = prepare(root, feature, task_ids=[task])
                return value, {b['code'] for b in value['coding']['blockers']}
            core, codes = snapshot('T001')
            self.assertNotIn('PKC012', codes)
            self.assertNotIn('persistence', core['coding']['responsibilities'])
            self.assertNotIn('persistence-adoption', {r['id'] for r in core['requirements']})
            self.assertNotIn('persistence-adoption', {u['id'] for u in core['coding']['skills']})
            persistence_rules = set(next(r['ruleIds'] for r in catalog()['requirements'] if r['id'] == 'persistence-adoption'))
            self.assertFalse(persistence_rules & {d['rule'] for d in core['coding']['evaluation']['duties']})
            self.assertIn('PKC024', codes)  # Scope proof supplies no analyzer acceptance.
            provider, codes = snapshot('T002')
            self.assertNotIn('PKC012', codes)
            self.assertIn('persistence', provider['coding']['responsibilities'])
            self.assertIn('persistence-adoption', {u['id'] for u in provider['coding']['skills']})
            self.assertTrue(persistence_rules & {d['rule'] for d in provider['coding']['evaluation']['duties']})
            declarations[0]['role'] = 'unresolved'; save_graph()
            unknown, codes = snapshot('T001')
            self.assertIn('persistence', unknown['coding']['responsibilities'])
            self.assertIn('persistence-adoption', {r['id'] for r in unknown['requirements']})
            declarations[0].pop('role'); save_graph()
            malformed, codes = snapshot('T001')
            self.assertIn('PKC015', codes)
            self.assertIn('persistence', malformed['coding']['responsibilities'])
            finding = next(row for row in malformed['lifecycleFindings'] if row['id'] == 'invalid-project-role')
            self.assertEqual('src/Core/Core.csproj', finding['project'])
            self.assertIn('architecture owner', finding['message'])
            self.assertIn('eng/architecture.json', finding['message'])
            for invalid_role in ([], {}):
                declarations[0]['role'] = invalid_role; save_graph()
                invalid, codes = snapshot('T001')
                self.assertIn('PKC015', codes)
                self.assertIn('persistence', invalid['coding']['responsibilities'])
                self.assertIn('invalid-project-role', {row['id'] for row in invalid['lifecycleFindings']})
            declarations[0]['role'] = 'core'; save_graph()
            core_source = root / 'src/Core/Policy.cs'
            core_source.write_text('using Microsoft.EntityFrameworkCore; namespace Fixture; public sealed class Policy {}')
            contaminated, codes = snapshot('T001')
            self.assertIn('PKC012', codes)
            self.assertIn('persistence', contaminated['coding']['responsibilities'])
            core_source.write_text('namespace Fixture; public sealed class Policy {}')
            (root / 'src/Core/imported.props').write_text('<Project><ItemGroup><PackageReference Include="Npgsql" Version="10.0.0" /></ItemGroup></Project>')
            (root / 'src/Core/Core.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><Import Project="imported.props" /></Project>')
            imported, codes = snapshot('T001')
            self.assertIn('PKC012', codes)
            self.assertIn('persistence', imported['coding']['projects'][0]['responsibilityTags'])

    def test_manual_module_keeps_complete_generic_guidance_within_measured_bound(self):
        with FixtureDirectory() as name:
            root = Path(name); feature = root / 'specs/001-module'; feature.mkdir(parents=True)
            source = root / 'src/policy.py'; source.parent.mkdir(); source.write_text('def evaluate(value):\n    return value + 1\n')
            (feature / 'spec.md').write_text('A finite pure domain transformation.')
            (feature / 'plan.md').write_text('The operation is implemented by src/policy.py.')
            (feature / 'tasks.md').write_text('- [ ] T001 Implement src/policy.py.\n')
            value = prepare(root, feature, task_ids=['T001'])
            self.assertFalse(value['coding']['nativeContext']['applicable'])
            self.assertNotIn('PKC024', {b['code'] for b in value['coding']['blockers']})
            import phase_obligations as phase
            output = phase.render(value, 'implementation')
            self.assertLess(len(output.encode('utf-8')), BRIEF_LIMITS['module'])
            assert_complete_required_text(self, catalog(), value['requirements'], output, ROOT / 'extensions')

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
        # F5 now legitimately supplies a recipe for this rule. Construct the
        # independent missing-binding control explicitly instead of assuming none.
        data['rules']['principle.compilation-boundaries']['bindings']['recipes'] = []
        self.assertTrue(compose(data, [], set(), {}, ROOT / 'extensions')[2])
        data['rules']['principle.compilation-boundaries']['bindings']['recipes'] = ['extensions/program-kit-dotnet/references/fictional-missing-recipe.md']
        self.assertTrue(any(b['code'] == 'PKC004' for b in compose(data, [], set(), {}, ROOT / 'extensions')[2]))
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

    def test_bound_recipe_uses_installed_packed_bytes_and_rejects_corruption(self):
        import asset_sources
        data = copy.deepcopy(catalog())
        identity = 'principle.compilation-boundaries'
        data['codingUnits'] = [{'id': 'packed-recipe', 'ruleIds': [identity], 'route': 'bound-recipes'}]
        relative = 'references/examples/recipe.md'
        data['rules'][identity]['bindings']['recipes'] = ['extensions/fixture/' + relative]
        with FixtureDirectory() as directory:
            extensions = Path(directory)
            component = extensions / 'fixture'; component.mkdir()
            (component / 'extension.yml').write_text('extension:\n  id: fixture\n')
            pack = component / asset_sources.PACK
            pack.write_bytes(asset_sources.encoded({relative: b'Exact original recipe.\n'}))
            with patch('coding_context.resolve', return_value={'id': identity, 'fingerprint': 'independent-rule'}):
                self.assertFalse(compose(data, [], set(), {}, extensions)[2])
                value = json.loads(pack.read_bytes())
                value['files'][relative]['sha256'] = '0' * 64
                pack.write_text(json.dumps(value))
                self.assertTrue(any(b['code'] == 'PKC004' for b in compose(data, [], set(), {}, extensions)[2]))

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
            (feature / 'plan.md').write_text('Use src/Example.Core/Example.Core.csproj.')
            (feature / 'tasks.md').write_text('- [ ] T001 Materialize src/Example.Core/Example.Core.csproj and implement src/Example.Core/Policy.cs.\n')
            (root / 'eng').mkdir()
            (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [
                {'path': 'src/Example.Core/Example.Core.csproj', 'role': 'core', 'projectReferences': [],
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

"""Behavioral regressions for decision-time routing and ordinary design handoffs."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
from owned_fixture import FixtureDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import phase_obligations as knowledge
from repository_architecture import validate_planned


class KnowledgeApplicationTests(unittest.TestCase):
    def setUp(self):
        temporary = FixtureDirectory(prefix='knowledge-application-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.feature = self.root / 'specs/001-notes'
        self.feature.mkdir(parents=True)
        (self.feature / 'spec.md').write_text(
            'Private named notes with durable saves.\n'
            '- **Specification roadmap entry**: RM-01\n', encoding='utf-8')

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def adopted(self):
        self.write('.program-kit/specification-intake/RM-01/brief.json', {
            'architectureScope': ['notes'], 'decisions': []})
        self.write('docs/architecture/architecture-map.json', {
            'elements': [{'id': 'notes', 'type': 'bounded-context', 'decision_refs': ['notes-runtime']},
                         {'id': 'future', 'type': 'bounded-context', 'decision_refs': ['future-runtime']}],
            'decisions': [{'id': 'notes-runtime', 'status': 'Accepted'},
                          {'id': 'future-runtime', 'status': 'Accepted'}],
            'strategic_model': {'bounded_contexts': [{'element': 'notes'}, {'element': 'future'}]}})
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'browser-web']})
        self.write('docs/architecture/building-block-selection.json', {
            'status': 'Accepted', 'targets': [
                {'id': 'notes-http', 'kind': 'dotnet-project', 'path': 'src/Notes.Http/Notes.Http.csproj',
                 'placement': {'owner': 'notes', 'decisionIds': ['notes-runtime']}},
                {'id': 'future-store', 'kind': 'dotnet-project', 'path': 'src/Future.Store/Future.Store.csproj',
                 'placement': {'owner': 'future', 'decisionIds': ['future-runtime']}}],
            'instances': [
                {'id': 'notes-api', 'composition': 'api_baseline', 'targetBindings': {'dotnet': 'notes-http'}},
                {'id': 'future-db', 'composition': 'persistence', 'targetBindings': {'dotnet': 'future-store'}}]})

    def ids(self, phase='planning'):
        return {r['id'] for r in knowledge.project(self.root, self.feature, phase)['requirements']}

    def graph(self):
        return {'runtimeComposition': {'projects': [
            {'path': 'src/Notes/Notes.csproj', 'role': 'core', 'projectReferences': [],
             'responsibilities': [{'name': 'NotesService', 'kind': 'runtime',
                                   'effects': ['persistence'], 'provides': ['Notes.INotes']}]},
            {'path': 'src/Notes.Postgres/Notes.Postgres.csproj', 'role': 'provider',
             'projectReferences': ['src/Notes/Notes.csproj']}],
            'bindings': []}}

    def test_adoption_reaches_design_before_plan_or_projects_exist(self):
        self.adopted()
        ids = self.ids()
        self.assertIn('dotnet-boundaries', ids)
        self.assertIn('http-operation-contracts', ids)
        self.assertNotIn('persistence-adoption', ids)  # Another owner's adopted provider.
        self.assertFalse((self.feature / 'plan.md').exists())
        self.assertFalse((self.root / 'src').exists())

    def test_frontend_only_feature_does_not_inherit_backend_from_global_sdk(self):
        self.adopted()
        (self.feature / 'spec.md').write_text('Frontend-only browser presentation.\n'
            '- **Specification roadmap entry**: RM-01\n', encoding='utf-8')
        self.write('global.json', {'sdk': {'version': '10.0.100'}})
        self.assertNotIn('dotnet-boundaries', self.ids())
        self.assertIn('browser-experience', self.ids())
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'typescript-web']})
        self.assertIn('typescript-boundaries', self.ids())
        self.assertNotIn('dotnet-boundaries', self.ids())

    def test_actual_backend_evidence_cannot_be_hidden_by_frontend_label(self):
        self.adopted()
        project = self.root / 'src/Notes.Http/Notes.Http.csproj'
        project.parent.mkdir(parents=True)
        project.write_text('<Project Sdk="Microsoft.NET.Sdk.Web" />', encoding='utf-8')
        (self.feature / 'plan.md').write_text('Frontend-only. Change src/Notes.Http/Notes.Http.csproj.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'frontend-only.*backend|backend.*frontend-only'):
            self.ids()

    def test_neighbor_decision_and_shared_parent_do_not_activate_a_private_provider(self):
        self.adopted()
        path = self.root / 'docs/architecture/architecture-map.json'
        model = json.loads(path.read_text())
        model['elements'].append({'id': 'app', 'type': 'software-system'})
        for element in model['elements'][:2]:
            element['parent'] = 'app'
        self.write('docs/architecture/architecture-map.json', model)
        selection = json.loads((self.root / 'docs/architecture/building-block-selection.json').read_text())
        selection['targets'][1]['placement']['decisionIds'] = ['notes-runtime']
        self.write('docs/architecture/building-block-selection.json', selection)
        result = knowledge.project(self.root, self.feature, 'planning')
        self.assertNotIn('persistence-adoption', {r['id'] for r in result['requirements']})
        self.assertTrue(any('another owner' in d for d in result['context']['diagnostics']))

    def test_selected_design_needs_metadata_without_reopening_unrelated_projects(self):
        (self.feature / 'plan.md').write_text('C# pure policy in src/Notes.Core/Notes.Core.csproj.', encoding='utf-8')
        graph = {'runtimeComposition': {'projects': [
            {'path': 'src/Notes.Core/Notes.Core.csproj', 'role': 'core'},
            {'path': 'src/Unrelated.Core/Unrelated.Core.csproj', 'role': 'core'}], 'bindings': []}}
        self.write('eng/architecture.json', graph)
        with self.assertRaisesRegex(ValueError, 'responsibilities.*Notes.Core'):
            knowledge.check(self.root, self.feature, 'after-plan')
        graph['runtimeComposition']['projects'][0]['responsibilities'] = [
            {'name': 'NamePolicy', 'kind': 'pure-policy', 'effects': []}]
        self.write('eng/architecture.json', graph)
        result = knowledge.check(self.root, self.feature, 'after-plan')
        self.assertTrue(result['validation']['declaredGraphPassed'])
        self.assertFalse(result['validation']['semanticReviewEstablished'])

    def test_installed_default_brief_and_graph_use_the_same_canonical_rules(self):
        self.adopted()
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(ROOT / 'extensions' / name, self.root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('__pycache__'))
        script = self.root / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py'
        command = [sys.executable, str(script), 'project', '--repository', str(self.root),
                   '--feature-dir', 'specs/001-notes', '--phase', 'planning']
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn('Core', result.stdout)
        self.assertIn('canonical permission', result.stdout)
        canonical = self.root / '.specify/extensions/program-kit-governance/references/modularity-and-contracts.md'
        canonical.write_text(canonical.read_text().replace(
            '<!-- program-kit:decision-rule compilation-responsibilities -->', '<!-- removed -->'), encoding='utf-8')
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(2, result.returncode)
        self.assertIn('Missing/ambiguous canonical decision rule', result.stdout)

    def test_original_mixed_core_is_rejected_by_declared_responsibilities(self):
        with self.assertRaisesRegex(ValueError, 'Core.*runtime|runtime.*Core'):
            validate_planned(self.root, self.graph())

    def test_absent_graph_cannot_be_reported_as_a_pass(self):
        result = knowledge.check(self.root, self.feature, 'after-plan')
        self.assertIsNone(result['validation']['declaredGraphPassed'])
        self.assertNotIn('Declared graph: PASS', knowledge.render(result, 'after-plan'))

    def test_runtime_capability_cannot_be_omitted_from_bindings(self):
        graph = self.graph()
        graph['runtimeComposition']['projects'][0]['role'] = 'implementation'
        graph['runtimeComposition']['projects'][1]['projectReferences'] = []
        with self.assertRaisesRegex(ValueError, 'binding'):
            validate_planned(self.root, graph)

    def test_pure_policy_and_minimal_core_remain_valid(self):
        graph = {'runtimeComposition': {'projects': [
            {'path': 'src/Notes.Core/Notes.Core.csproj', 'role': 'core',
             'responsibilities': [{'name': 'NamePolicy', 'kind': 'pure-policy', 'effects': []}]}],
            'bindings': []}}
        self.assertEqual(1, len(validate_planned(self.root, graph)))
        self.assertEqual({}, validate_planned(self.root, {'runtimeComposition': {'projects': [], 'bindings': []}}))

    def test_decisive_conditions_survive_default_phase_transitions(self):
        (self.feature / 'plan.md').write_text('C# HTTP API with database and authorization.', encoding='utf-8')
        for phase in ('planning', 'tasks', 'implementation', 'delivery'):
            brief = knowledge.render(knowledge.project(self.root, self.feature, phase), phase)
            self.assertIn('when those responsibilities exist', brief)
            self.assertIn('Core', brief)
            self.assertIn('canonical permission', brief)
            self.assertIn('resource/state/effect', brief)
            self.assertIn('semantic', brief.lower())
        self.assertIn('parser/schema/runtime', knowledge.render(
            knowledge.project(self.root, self.feature, 'planning'), 'planning'))


class ExactFoundationApplicabilityTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        from validate_effective_dependency_context import EffectiveContextTests
        EffectiveContextTests.setUp(self)
        EffectiveContextTests.selected(self, 'foundation-0.3.2-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2')
        self.feature = self.root / 'specs/001-web'; self.feature.mkdir(parents=True)
        (self.feature / 'spec.md').write_text('Private HTML pages and an owned API.')
        selection = json.loads(self.selection.read_text())
        selection['status'] = 'Accepted'
        self.selection.write_text(json.dumps(selection))
        self.targets = {row['id'] for row in selection['targets']}
        self.inherited = {'sources': [{'path': 'docs/architecture/building-block-selection.json',
                                     'targets': sorted(self.targets)}], 'diagnostics': []}

    def brief(self, tags={'api', 'web'}):
        from unittest.mock import patch
        with patch.object(knowledge, 'intent', return_value=tags), \
                patch.object(knowledge, 'adopted_context', return_value=self.inherited):
            return knowledge.project(self.root, self.feature, 'planning')

    def test_api_brief_uses_exact_captured_mechanisms(self):
        value = self.brief()['foundationApplicability']
        self.assertEqual('0.3.2', value['version'])
        self.assertEqual('8e3576d0b8dc25b820e56f4013d92137e410a440', value['sourceCommit'])
        rendered = knowledge.render(self.brief(), 'planning')
        for mechanism in ('Foundation:Web:ResponsePolicies', 'WebResponseMetadata',
                          'final header writer', 'permission:', 'typed configuration', 'owned constants'):
            self.assertIn(mechanism, rendered)

    def hosted(self, identity, purpose):
        selection = json.loads(self.selection.read_text())
        selection['instances'].append({'id': identity, 'composition': 'hosted_pages', 'purpose': purpose,
            'targetBindings': {'implementation': sorted(self.targets)}})
        self.selection.write_text(json.dumps(selection))

    def test_public_only_hosting_rejects_private_page_adoption(self):
        self.hosted('private-pages', 'Authenticated HTML and bootstrap')
        with self.assertRaisesRegex(ValueError, '0.3.2.*public-only|public-only.*0.3.2'):
            self.brief()

    def test_explicit_public_assets_remain_valid_with_private_api(self):
        self.hosted('public-assets', 'Explicitly public immutable code assets')
        self.assertIn('WebResponseMetadata', knowledge.render(self.brief(), 'planning'))

    def test_released_private_pages_use_the_exact_new_qualified_contract(self):
        from validate_effective_dependency_context import EffectiveContextTests
        EffectiveContextTests.selected(self, 'foundation-0.3.3-build-0.3.1-exporter-0.2.5-forms-0.2.1-localization-0.1.2')
        self.hosted('private-pages', 'Authenticated HTML and bootstrap')
        value = self.brief()['foundationApplicability']
        self.assertEqual('0.3.3', value['version'])
        self.assertEqual('0739892610a12f36673941dbe9718f45a38ae6cb', value['sourceCommit'])
        self.assertIn('typed HostedPages Routes', knowledge.render(self.brief(), 'planning'))

    def test_default_private_pages_use_independently_verified_selected_capture(self):
        from validate_effective_dependency_context import EffectiveContextTests
        EffectiveContextTests.selected(self)
        effective = self.blocks.effective_dependency_context(self.root)
        self.hosted('private-pages', 'Authenticated HTML and bootstrap')
        value = self.brief()['foundationApplicability']
        self.assertEqual(effective['catalog']['families']['foundation']['releaseVersion'], value['version'])
        self.assertEqual(effective['profile'], value['profile'])
        self.assertEqual(effective['publisherKnowledge']['sourceCommit'], value['sourceCommit'])
        options = next(row for row in effective['publisherKnowledge']['documents']
                       if row['publisherPath'] == 'src/Orbyss.Foundation.Web.HostedPages/HostedPageOptions.cs')
        source = self.blocks.publisher_document_bytes(Path(effective['registryPath']), options).decode('utf-8')
        self.assertIn('HostedPageRouteOptions', source)
        self.assertIn('Routes', source)
        rendered = knowledge.render(self.brief(), 'planning')
        self.assertIn('typed HostedPages Routes', rendered)
        self.assertIn(value['sourceCommit'], rendered)

    def test_unrelated_scope_does_not_read_foundation_knowledge(self):
        self.inherited = {'sources': [], 'diagnostics': []}
        self.assertIsNone(self.brief({'dotnet'}).get('foundationApplicability'))


if __name__ == '__main__':
    unittest.main()

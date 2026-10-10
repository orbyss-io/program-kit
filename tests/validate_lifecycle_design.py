"""Selected publisher knowledge and normal composition review regressions."""
import copy
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import repository_architecture as architecture


class LifecycleDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lifecycle-design-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.provider = 'src/Notes.PostgreSql/Notes.PostgreSql.csproj'
        self.application = 'src/Notes/Notes.csproj'
        self.preset = 'src/Notes.Bundle/Notes.Bundle.csproj'
        self.manifest = {'runtimeComposition': {'projects': [
            {'path': self.provider, 'role': 'provider'},
            {'path': self.application, 'role': 'implementation'},
            {'path': self.preset, 'role': 'composition', 'projectReferences': [self.provider, self.application],
             'responsibilities': [{'name': 'NotesPreset', 'kind': 'composition', 'effects': [],
                                   'rationale': 'Reusable Notes deployment selects a supported store and application feature.'}]}]}}

    def source(self, project, filename, content):
        path = self.root / Path(project).parent / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def test_genuine_selection_preset_and_feature_owned_lifecycle_are_valid(self):
        self.source(self.provider, 'Schema.cs', 'public class Schema : IShellInitializer { }')
        self.source(self.provider, 'Feature.cs', 'services.AddShellInitializer<Schema>(LifecyclePhase.Prepare);')
        self.source(self.application, 'Worker.cs', 'public class Worker : IBackgroundTask { }')
        self.source(self.application, 'Feature.cs', 'services.AddSingleton<IBackgroundTask, Worker>();')
        self.source(self.preset, 'Feature.cs', '[ShellFeature("NotesPreset", DependsOn = ["Notes", "Notes.PostgreSql"])] public class Preset : IShellFeature { }')
        self.assertEqual([], architecture.lifecycle_findings(self.root, self.manifest))

    def test_unjustified_catch_all_has_concrete_review_finding(self):
        self.manifest['runtimeComposition']['projects'][2]['responsibilities'][0].pop('rationale')
        findings = architecture.lifecycle_findings(self.root, self.manifest)
        self.assertTrue(any(row['id'] == 'composition-selection-responsibility' for row in findings))

    def test_concrete_provider_initialization_and_foreign_tasks_are_found_by_ownership(self):
        self.source(self.provider, 'Schema.cs', 'namespace Notes.PostgreSql; public class Schema : IShellInitializer { }')
        self.source(self.application, 'Worker.cs', 'namespace Notes; public class Worker : IBackgroundTask { }')
        self.source(self.preset, 'Bootstrap.cs', 'provider.GetRequiredService<Notes.PostgreSql.Schema>().InitializeAsync(token); services.AddSingleton<IBackgroundTask, Notes.Worker>();')
        findings = architecture.lifecycle_findings(self.root, self.manifest)
        self.assertEqual({'foreign-lifecycle-ownership'}, {row['id'] for row in findings})
        self.assertTrue(any('Schema.cs' in row['ownerSource'] for row in findings))
        self.assertTrue(any('Worker.cs' in row['ownerSource'] for row in findings))

    def test_names_alone_and_domain_events_are_not_lifecycle_violations(self):
        self.source(self.provider, 'Model.cs', 'public record SchemaInitializerReport(string Status);')
        self.source(self.application, 'Reaction.cs', 'public class Reaction : IDomainEventHandler<NoteSaved> { }')
        self.source(self.preset, 'Feature.cs', 'services.AddSingleton<IDomainEventHandler<NoteSaved>, Reaction>(); var report = new SchemaInitializerReport("ok");')
        self.assertEqual([], architecture.lifecycle_findings(self.root, self.manifest))

    def test_reported_plain_provider_helper_and_composition_startup_is_found(self):
        self.source(self.provider, 'Schema.cs', 'public class NotesSchemaInitializer { public Task InitializeAsync(CancellationToken token) => Task.CompletedTask; }')
        self.source(self.preset, 'Startup.cs', 'public class NotesStartup(NotesSchemaInitializer schema) : IStartupTask { public Task ExecuteAsync(CancellationToken token) => schema.InitializeAsync(token); }')
        findings = architecture.lifecycle_findings(self.root, self.manifest)
        self.assertTrue(any(row['id'] == 'composition-runtime-lifecycle' and row['source'].endswith('Startup.cs') for row in findings))

    def test_normal_phase_handoff_projects_scoped_findings_and_worked_publisher_route(self):
        sys.path.insert(0, str(ROOT/'extensions/program-kit-governance/scripts'))
        import phase_obligations as knowledge
        feature = self.root/'specs/001-notes'; feature.mkdir(parents=True)
        (feature/'spec.md').write_text('C# Notes application lifecycle.', encoding='utf-8')
        (feature/'plan.md').write_text('Change '+self.preset, encoding='utf-8')
        for row in self.manifest['runtimeComposition']['projects'][:2]:
            row['responsibilities'] = [{'name': 'OwnedRuntime', 'kind': 'runtime', 'effects': ['runtime']}]
        self.manifest['runtimeComposition']['projects'].append({'path': 'src/Unrelated/Unrelated.csproj', 'role': 'composition'})
        self.source(self.preset, 'Startup.cs', 'public class NotesStartup : IStartupTask { }')
        self.source('src/Unrelated/Unrelated.csproj', 'Startup.cs', 'public class OtherStartup : IStartupTask { }')
        manifest = self.root/'eng/architecture.json'; manifest.parent.mkdir()
        manifest.write_text(json.dumps(self.manifest), encoding='utf-8')
        for phase in ('planning', 'after-plan'):
            result = knowledge.project(self.root, feature, phase) if phase == 'planning' else knowledge.check(self.root, feature, phase)
            self.assertEqual({self.preset}, {row['project'] for row in result['lifecycleFindings']})
            brief = knowledge.render(result, phase)
            self.assertIn('composition-runtime-lifecycle', brief)
            self.assertIn('LifecyclePhase.Prepare', brief)
            self.assertIn('publisher_knowledge.py', brief)

    def test_versioned_route_supports_selected_cshells(self):
        command = [sys.executable, str(ROOT/'extensions/program-kit-building-blocks/scripts/publisher_knowledge.py')]
        result = subprocess.run(command+['--target', str(ROOT), '--package', 'CShells.Abstractions', '--fact', 'README.md'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('AddShellInitializer<T>()', result.stdout)
        self.assertIn('0.3.1', result.stdout)
        historical = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        result = subprocess.run(command+['--profile', historical, '--package', 'CShells.Abstractions'], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('repair of this selected profile', result.stderr)

    def test_installed_registry_and_captured_historical_scaffold_do_not_choose_new_default(self):
        installed = self.root/'.specify/extensions/program-kit-building-blocks'
        shutil.copytree(ROOT/'extensions/program-kit-building-blocks', installed)
        command = [sys.executable, str(installed/'scripts/publisher_knowledge.py'), '--target', str(self.root), '--package', 'CShells.Abstractions']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        # Use the actual installed resolver, including its anchored dynamic import.
        import importlib.util
        spec = importlib.util.spec_from_file_location('fixture_installed_blocks', installed/'scripts/building_blocks.py')
        blocks = importlib.util.module_from_spec(spec); sys.modules[spec.name] = blocks; spec.loader.exec_module(blocks)
        historical = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        registry = installed/'references/dependency-profiles'
        index = blocks.load_json(registry/'index.json')
        catalog, _ = blocks.qualified_dependency_profile(registry, historical, blocks.load_json(installed/'references/orbyss-building-blocks.json'))
        managed = self.root/'.program-kit/managed.json'; managed.parent.mkdir()
        managed.write_text(json.dumps({'newProjectDependencyProfile': {'profile': historical,
                           'entrySha256': blocks.canonical_sha256(index['profiles'][historical]),
                           'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog)}}), encoding='utf-8')
        selected = blocks.effective_dependency_context(self.root)
        self.assertEqual(historical, selected['profile'])
        self.assertIsNone(selected['lifecycleKnowledge'])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('repair of this selected profile', result.stderr)


if __name__ == '__main__': unittest.main()

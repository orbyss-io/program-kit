"""Selected publisher knowledge and normal composition review regressions."""
import copy
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
from owned_fixture import FixtureDirectory, filesystem_path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import repository_architecture as architecture


class LifecycleDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = FixtureDirectory(prefix='lifecycle-design-')
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

    def test_direct_selection_and_feature_owned_lifecycle_are_valid(self):
        self.manifest['runtimeComposition']['projects'].pop()
        self.source(self.provider, 'Schema.cs', 'public class Schema : IShellInitializer { }')
        self.source(self.provider, 'Feature.cs', 'services.AddShellInitializer<Schema>(LifecyclePhase.Prepare);')
        self.source(self.application, 'Worker.cs', 'public class Worker : IBackgroundTask { }')
        self.source(self.application, 'Feature.cs', 'services.AddSingleton<IBackgroundTask, Worker>();')
        shells = {'CShells': {'Shells': {'notes': {'Features': {'Notes': {}, 'Notes.PostgreSql': {}}}}}}
        (self.root / 'shells.json').write_text(json.dumps(shells))
        architecture.validate_manifest(self.root, self.manifest)
        self.assertEqual([], architecture.lifecycle_findings(self.root, self.manifest))
        self.assertFalse((self.root / Path(self.preset).parent).exists())

    def test_even_justified_retained_preset_is_diagnosed_without_mutation(self):
        original = copy.deepcopy(self.manifest)
        with self.assertRaisesRegex(ValueError, 'PKA022 retired C# composition project role'):
            architecture.validate_manifest(self.root, self.manifest)
        findings = architecture.lifecycle_findings(self.root, self.manifest)
        self.assertEqual(['retired-composition-project'], [row['id'] for row in findings])
        self.assertIn('do not merely relabel', findings[0]['message'])
        self.assertEqual(original, self.manifest)

    def test_foreign_tasks_are_found_after_preset_retirement(self):
        self.manifest['runtimeComposition']['projects'].pop()
        self.source(self.provider, 'Schema.cs', 'namespace Notes.PostgreSql; public class Schema : IShellInitializer { }')
        self.source(self.application, 'Bootstrap.cs', 'provider.GetRequiredService<Notes.PostgreSql.Schema>().InitializeAsync(token);')
        findings = architecture.lifecycle_findings(self.root, self.manifest)
        self.assertEqual({'foreign-lifecycle-ownership'}, {row['id'] for row in findings})
        self.assertTrue(any('Schema.cs' in row['ownerSource'] for row in findings))

    def test_names_alone_and_domain_events_are_not_lifecycle_violations(self):
        self.manifest['runtimeComposition']['projects'].pop()
        self.source(self.provider, 'Model.cs', 'public record SchemaInitializerReport(string Status);')
        self.source(self.application, 'Reaction.cs', 'public class Reaction : IDomainEventHandler<NoteSaved> { }')
        self.source(self.application, 'Feature.cs', 'services.AddSingleton<IDomainEventHandler<NoteSaved>, Reaction>(); var report = new SchemaInitializerReport("ok");')
        self.assertEqual([], architecture.lifecycle_findings(self.root, self.manifest))

    def test_normal_phase_scopes_retirement_and_blocks_retained_graph(self):
        sys.path.insert(0, str(ROOT/'extensions/program-kit-governance/scripts'))
        import phase_obligations as knowledge
        feature = self.root/'specs/001-notes'; feature.mkdir(parents=True)
        (feature/'spec.md').write_text('C# Notes application lifecycle.', encoding='utf-8')
        (feature/'plan.md').write_text('Change '+self.preset, encoding='utf-8')
        self.manifest['runtimeComposition']['projects'].append({'path': 'src/Unrelated/Unrelated.csproj', 'role': 'composition'})
        manifest = self.root/'eng/architecture.json'; manifest.parent.mkdir()
        manifest.write_text(json.dumps(self.manifest), encoding='utf-8')
        result = knowledge.project(self.root, feature, 'planning')
        self.assertEqual({self.preset}, {row['project'] for row in result['lifecycleFindings']})
        brief = knowledge.render(result, 'planning')
        self.assertIn('retired-composition-project', brief)
        self.assertIn('LifecyclePhase.Prepare', knowledge.render(result, 'planning', detailed=True))
        self.assertIn('publisher_knowledge.py', brief)
        for phase in ('after-plan', 'after-tasks', 'implementation'):
            with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, 'PKA022 retired C# composition project role'):
                knowledge.check(self.root, feature, phase)

    def test_versioned_route_supports_selected_cshells(self):
        from validate_building_blocks import load_module, RESOLVER
        blocks = load_module(RESOLVER)
        selected = blocks.effective_dependency_context(ROOT)
        registry = Path(selected['registryPath'])
        index = blocks.load_json(registry/'index.json')
        self.assertEqual(index['default'], selected['profile'])
        runtime_version = selected['catalog']['families']['foundation']['releaseVersion']
        self.assertEqual(runtime_version, selected['publisherKnowledge']['releaseVersion'])
        command = [sys.executable, str(ROOT/'extensions/program-kit-building-blocks/scripts/publisher_knowledge.py'), '--target', str(ROOT)]
        header = 'Publisher knowledge page 1/1; exact selected profile ' + selected['profile']

        # Runtime package metadata must follow runtime authority, even when an
        # independently versioned tool contributes another version to the profile ID.
        runtime_id = 'Orbyss.Foundation.Authentication'
        runtime_row = next(row for row in selected['publisherKnowledge']['packages'] if row['id'] == runtime_id)
        runtime_fact = blocks.publisher_package_fact(registry, runtime_row)
        result = subprocess.run(command+['--package', runtime_id], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        actual_header, payload = result.stdout.split('\n', 1)
        self.assertEqual(header, actual_header)
        metadata = json.loads(payload)
        self.assertEqual(runtime_version, metadata['version'])
        self.assertEqual(selected['publisherKnowledge']['sourceCommit'], metadata['repository']['commit'])
        self.assertEqual({key: runtime_fact[key] for key in ('id', 'version', 'license', 'repository')}
                         | {'facts': sorted(runtime_fact['facts'])}, metadata)

        # CShells lifecycle facts are selected by the qualified native lock,
        # rather than the Foundation runtime version or today's external pin.
        recipe = blocks.load_json(registry/index['profiles'][selected['profile']]['qualificationRecipe']['path'])
        lock_path = ROOT/recipe['nativeLock']['path']
        lock = blocks.load_json(lock_path)
        versions = {row['resolved'] for target in lock['dependencies'].values()
                    for name, row in target.items() if name == 'CShells.Abstractions'}
        self.assertEqual({selected['lifecycleKnowledge']['version']}, versions)
        lifecycle_row = next(row for row in selected['lifecycleKnowledge']['packages'] if row['id'] == 'CShells.Abstractions')
        lifecycle_fact = blocks.publisher_package_fact(registry, lifecycle_row)
        for source in (lock_path, registry/lifecycle_row['path']):
            self.assertEqual(blocks.raw_sha256(source), selected['sources'][str(source.resolve())])
        result = subprocess.run(command+['--package', 'CShells.Abstractions'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        actual_header, payload = result.stdout.split('\n', 1)
        self.assertEqual(header, actual_header)
        metadata = json.loads(payload)
        self.assertEqual(versions, {metadata['version']})
        self.assertEqual({key: lifecycle_fact[key] for key in ('id', 'version', 'license', 'repository')}
                         | {'facts': sorted(lifecycle_fact['facts'])}, metadata)
        result = subprocess.run(command+['--package', 'CShells.Abstractions', '--fact', 'README.md'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        actual_header, payload = result.stdout.split('\n', 1)
        self.assertEqual(header, actual_header)
        self.assertEqual(lifecycle_fact['facts']['README.md'], payload)
        self.assertIn('AddShellInitializer<T>()', payload)
        historical = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        result = subprocess.run(command+['--profile', historical, '--package', 'CShells.Abstractions'], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('repair of this selected profile', result.stderr)

    def test_installed_registry_and_captured_historical_scaffold_do_not_choose_new_default(self):
        installed = self.root/'.specify/extensions/program-kit-building-blocks'
        shutil.copytree(filesystem_path(ROOT/'extensions/program-kit-building-blocks'), installed)
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

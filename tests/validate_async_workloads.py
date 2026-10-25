"""Synthetic routing and explicit provider closure checks; no platform qualification."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from owned_fixture import FixtureDirectory
from validate_native_phases import snapshot

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import phase_obligations as phase
import provider_composition as model

EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/async-workload'


def composition(environment='Production'):
    # Fictional metadata/observations, not installed or qualified cloud providers.
    value = json.loads((EXAMPLE / 'composition.example.json').read_text(encoding='utf-8'))
    value['environment'] = environment
    value['scope'] = environment + '.tenant-a'
    for row in value['bindings']: row['scope'] = value['scope']
    for row in value['packages']: row['developmentOnly'] = environment == 'Development'
    return value


class Guidance(unittest.TestCase):
    def test_early_plain_language_routing_without_backend_or_toolkit_state(self):
        for text in ('Process background jobs.', 'Use durable dispatch with a transactional outbox.',
                     'Queue consumers process queued work.', 'Compare WebJobs and Kubernetes Jobs.',
                     'Use replaceable execution providers with Development Docker.'):
            with self.subTest(text=text), FixtureDirectory() as name:
                root = Path(name); feature = root / 'specs/001-batch'; feature.mkdir(parents=True)
                (feature / 'spec.md').write_text(text, encoding='utf-8')
                before = snapshot(root)
                for event in ('planning', 'after-plan', 'tasks'):
                    value = phase.check(root, feature, event)
                    rendered = phase.text_page(phase.render(value, event), 1)
                    self.assertIn('async-workload', value['responsibilities'])
                    self.assertIn('research the execution boundary', rendered)
                    self.assertIn('--only async-workload', rendered)
                    selected = deepcopy(value)
                    selected['requirements'] = [r for r in value['requirements'] if r['id'] == 'async-workload']
                    focused = phase.render(selected, event, True)
                    for phrase in ('App Service/WebJobs', 'Container Apps apps/jobs', 'Kubernetes Jobs',
                                   'Competing consumers', 'Semantic replacement contract', 'Ambiguous submission',
                                   'Provider retirement', 'platform qualification'):
                        self.assertIn(phrase, focused)
                self.assertEqual(before, snapshot(root))

    def test_unrelated_async_syntax_and_excluded_future_work_do_not_select_pattern(self):
        for text in ('An async HTTP handler awaits a query.', 'Edit a label.\n## Non-goals\nBackground jobs and queue consumers.'):
            with FixtureDirectory() as name:
                root = Path(name); feature = root / 'specs/001-label'; feature.mkdir(parents=True)
                (feature / 'spec.md').write_text(text, encoding='utf-8')
                self.assertNotIn('async-workload', phase.check(root, feature, 'planning')['responsibilities'])

    def test_installed_governance_has_source_map_without_dotnet_adapter(self):
        with FixtureDirectory() as name:
            root = Path(name); feature = root / 'specs/001-batch'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('Process background jobs with replaceable providers.', encoding='utf-8')
            source = ROOT / 'extensions/program-kit-governance'
            installed = root / '.specify/extensions/program-kit-governance'
            shutil.copytree(source, installed, ignore=shutil.ignore_patterns('__pycache__'))
            result = subprocess.run([sys.executable, str(installed / 'scripts/phase_obligations.py'), 'project',
                '--feature-dir', str(feature), '--phase', 'planning', '--only', 'async-workload'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn('learn.microsoft.com', result.stdout)
            self.assertFalse((root / '.specify/extensions/program-kit-dotnet').exists())


class Composition(unittest.TestCase):
    def reject(self, value, message):
        with self.assertRaisesRegex(ValueError, message):
            model.validate_provider_composition(value)

    def test_explicit_development_and_production_are_read_only(self):
        for env in ('Development', 'Production', 'Staging', 'Test'):
            value = composition(env); before = deepcopy(value)
            result = model.validate_provider_composition(value)
            self.assertEqual(env, result['environment'])
            self.assertIn('consistency-only', result['proof'])
            self.assertEqual(before, value)

    def test_missing_ambiguous_incompatible_bindings_and_no_fallback(self):
        for mutation, message in (
            (lambda v: v['bindings'].pop(), 'no Docker fallback'),
            (lambda v: v['bindings'].append(deepcopy(v['bindings'][0])), 'ambiguous'),
            (lambda v: v['bindings'][0].update(contractVersion='2'), 'scope or contract'),
            (lambda v: v['bindings'][0].update(scope='Development.tenant-b'), 'scope or contract'),
            (lambda v: v['bindings'][0].update(version='2.0.0'), 'package/version'),
            (lambda v: v['bindings'][0].update(feature='exchange'), 'feature is not active in its package'),
            (lambda v: v.update(compatiblePairs=[]), 'not explicitly compatible'),
        ):
            value = composition(); mutation(value)
            with self.subTest(message=message): self.reject(value, message)

    def test_development_packages_fixtures_and_engine_privileges_fail_outside_development(self):
        for env in ('Production', 'Staging', 'Test'):
            for mutation, message in (
                (lambda v: v['packages'][0].update(developmentOnly=True), 'Development-only package'),
                (lambda v: v['fixtures'].append({'id': 'Fixture.Engine', 'developmentOnly': True}), 'Development-only fixture'),
                (lambda v: v.update(privileges=['docker.socket']), 'privileges are Development-only'),
            ):
                value = composition(env); mutation(value)
                with self.subTest(env=env, message=message): self.reject(value, message)
        value = composition('Development')
        value['packages'][0]['privileges'] = ['docker.socket']; value['privileges'] = ['docker.socket']
        model.validate_provider_composition(value)
        value['privileges'] = []
        self.reject(value, 'provider privilege is missing')

    def test_transitive_packages_and_activations_cannot_reintroduce_development(self):
        for through_feature in (False, True):
            value = composition()
            value['packages'].append({'id': 'Recording.DevEngine', 'version': '1.0.0',
                'dependencies': [], 'developmentOnly': True, 'privileges': []})
            value['packaged'].append('Recording.DevEngine')
            if through_feature:
                value['features'].append({'id': 'Engine', 'package': 'Recording.DevEngine', 'dependencies': []})
                value['features'][0]['dependencies'] = ['Engine']; value['activated'].append('Engine')
            else:
                value['packages'][0]['dependencies'] = ['Recording.DevEngine']
            with self.subTest(through_feature=through_feature): self.reject(value, 'Development-only package')

    def test_observed_closure_extra_missing_dependency_and_cycle(self):
        for mutation, message in (
            (lambda v: v['packaged'].append('Unselected.Provider'), 'observed package closure'),
            (lambda v: v['packaged'].pop(), 'observed package closure'),
            (lambda v: v['activated'].append('Unselected.Feature'), 'observed activation closure'),
            (lambda v: v['features'][0].update(dependencies=['missing']), 'missing feature dependency'),
            (lambda v: v['packages'][0].update(dependencies=['missing']), 'missing package dependency'),
            (lambda v: v['features'][0].update(dependencies=['execution']), 'cyclic feature'),
            (lambda v: v['packages'][0].update(version='latest'), 'exact package version'),
            (lambda v: v.update(scope='Development.tenant-a'), 'selected environment'),
        ):
            value = composition(); mutation(value)
            with self.subTest(message=message): self.reject(value, message)

    def test_sample_environment_relabel_is_rejected(self):
        value = composition('Development')
        value['environment'] = 'Production'; value['scope'] = 'Production.tenant-a'
        for row in value['bindings']: row['scope'] = value['scope']
        self.reject(value, 'Development-only package')

    def test_installed_composition_entrypoint_does_not_require_materialized_graph(self):
        with FixtureDirectory() as name:
            root = Path(name); path = root / 'eng/providers.json'; path.parent.mkdir()
            path.write_text(json.dumps(composition()), encoding='utf-8')
            before = snapshot(root)
            result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/provider_composition.py'),
                '--repository', str(root), '--input', 'eng/providers.json'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual('Production', json.loads(result.stdout)['environment'])
            self.assertEqual(before, snapshot(root))
            value = composition(); value['bindings'] = []; path.write_text(json.dumps(value), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/provider_composition.py'),
                '--repository', str(root), '--input', 'eng/providers.json'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('no Docker fallback', result.stderr)


class Compiled(unittest.TestCase):
    def test_sdk_free_core_and_executed_workflow_fixture(self):
        with FixtureDirectory(native=True) as name:
            root = Path(name)
            shutil.copytree(EXAMPLE, root / 'example', ignore=shutil.ignore_patterns('bin', 'obj'))
            directory = root / 'example'
            build = subprocess.run(['dotnet', 'build', 'AsyncWorkloadProof.csproj', '--configuration', 'Release',
                '--nologo', '-m:1', '-p:UseSharedCompilation=false'], cwd=directory, capture_output=True,
                text=True, encoding='utf-8', timeout=60)
            self.assertEqual(0, build.returncode, build.stdout + build.stderr)
            print('BUILD_SUCCEEDED_BEFORE_BEHAVIOR', flush=True)
            deps = json.loads((directory / 'Core/obj/project.assets.json').read_text(encoding='utf-8'))
            self.assertEqual({}, deps['libraries'], 'Core must compile without package/project dependencies')
            run = subprocess.run(['dotnet', 'bin/Release/net10.0/AsyncWorkloadProof.dll'], cwd=directory,
                capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)
            for marker in ('lost-acknowledgement-remains-unknown', 'superseded-attempt-cannot-publish',
                           'stop-request-is-not-stop-confirmation-or-cleanup', 'outage-retains-cleanup-obligation',
                           'changed-default-preserves-original-run-binding', 'WORKFLOW_CONFORMANCE_ONLY'):
                self.assertIn(marker, run.stdout)
            print(run.stdout, end='')


if __name__ == '__main__':
    compiled = '--compiled' in sys.argv
    if compiled: sys.argv.remove('--compiled')
    suite = unittest.TestSuite()
    for cls in ((Compiled,) if compiled else (Guidance, Composition)):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    sys.exit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)

"""Provider handoff and source visibility regressions; no network or coding agents."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import bootstrap_provider_context as providers
import bootstrap_context as context
from validate_building_blocks import accepted_fixture, load_module, write_json, RESOLVER, CATALOG


class ProviderContextTests(unittest.TestCase):
    def test_shipped_probe_and_exporter_pins_match_managed_foundation(self):
        import xml.etree.ElementTree as ET
        version = json.loads(CATALOG.read_text())['families']['foundation']['releaseVersion']
        files = list((ROOT / 'extensions/program-kit-governance/examples').rglob('*.csproj'))
        files += list((ROOT / 'tests/fixtures/knowledge-application/components').rglob('*.csproj'))
        checked = 0
        for path in files:
            for reference in ET.parse(path).iter('PackageReference'):
                if reference.get('Include', '').startswith('Orbyss.Foundation.'):
                    self.assertEqual(version, reference.get('Version'), str(path))
                    checked += 1
        self.assertGreater(checked, 0)
        tools = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.program-kit/eng/.config/dotnet-tools.json'
        self.assertEqual(version, json.loads(tools.read_text())['tools']['orbyss.foundation.openapi.exporter']['version'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'extensions/program-kit-building-blocks', self.root / '.specify/extensions/program-kit-building-blocks')
        self.identity = '.specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/deploy/compose.identity.yml'
        destination = self.root / self.identity
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / self.identity.replace('.specify/', ''), destination)
        for relative in ('references/persistence-runtimes.json',
                         'templates/dotnet/files/.program-kit/eng/profiles/persistence/ProgramKit.Persistence.EfPostgreSql.props'):
            source = ROOT / 'extensions/program-kit-dotnet' / relative
            target = self.root / '.specify/extensions/program-kit-dotnet' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        self.decisions = {'selected_profiles': ['dotnet'], 'identity': {'provider': 'keycloak', 'scope': 'local-evaluation'}}
        resolver = load_module(RESOLVER)
        self.selection, _ = accepted_fixture(resolver, self.root, json.loads(CATALOG.read_text()), 'api_baseline')
        selection = json.loads(self.selection.read_text())
        selection['status'] = 'Draft'
        selection['targets'][0]['role'] = 'api'
        selection['targets'] += [
            {'id': 'repository', 'kind': 'repository', 'path': 'Directory.Build.props', 'role': 'repository', 'scope': 'application'},
            {'id': 'host', 'kind': 'host-image', 'path': 'runtime/hostsettings.json', 'role': 'runtime-host', 'scope': 'application'}]
        selection['instances'][0]['targetBindings'].update(repository='repository', host='host')
        selection['instances'][0]['options'] = {'host': ['foundation-host']}
        selection['scopes'].append({'id': 'browser', 'kind': 'browser-boundary', 'parent': 'application', 'environment': 'production'})
        selection['instances'].append({'id': 'bff', 'composition': 'browser_bff', 'scope': 'browser',
                                       'targetBindings': {'dotnet': 'feature', 'shell': 'shell'}, 'options': {'extensions': ['assurance']}})
        write_json(self.selection, selection)

    def test_selected_packages_identity_sources_and_activations_without_writes(self):
        def inventory():
            return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        before = inventory()
        value = providers.project(self.root, self.decisions)
        catalog = json.loads(CATALOG.read_text())
        for item in value['selected_packages']:
            self.assertEqual(catalog['packages'][item['packageKey']]['version'], item['version'])
        self.assertTrue(any('Bff' in item['packageId'] for item in value['selected_packages']))
        self.assertFalse(any(item['family'] == 'forms' for item in value['selected_packages']))
        self.assertTrue(value['activations'])
        self.assertIn('@sha256:', value['identity_runtime']['image'])
        self.assertEqual(before, inventory())
        self.assertFalse((self.root / '.program-kit/building-blocks.lock.json').exists())

    def test_missing_selection_and_unpinned_identity_fail_before_dispatch(self):
        self.selection.unlink()
        with self.assertRaisesRegex(ValueError, 'building-block selection'):
            providers.project(self.root, self.decisions)
        self.assertIn('@sha256:', providers.project(self.root, self.decisions, require_selection=False)['identity_runtime']['image'])
        (self.root / self.identity).write_text('services:\n  keycloak:\n    image: quay.io/keycloak/keycloak:latest\n')
        with self.assertRaisesRegex(ValueError, 'exact tag and digest'):
            providers.project(self.root, self.decisions, require_selection=False)

    def test_baseline_sources_precede_architecture_and_stale_release_fails(self):
        self.selection.unlink()
        value = providers.project(self.root, self.decisions, require_selection=False)
        evidence = value['managed_baseline_evidence']
        self.assertEqual('0.2.2', evidence['releaseVersion'])
        self.assertIn('dotnet-foundation', evidence['publisher'])
        self.assertTrue(evidence['metadataExceptions'])
        self.assertGreater(evidence['distributionNoticeCount'], 0)
        self.assertIn('No blanket', ' '.join(evidence['assessment']['limits']))
        path = self.root / evidence['source']
        document = json.loads(path.read_text()); document['releaseVersion'] = '0.2.0'
        write_json(path, document)
        with self.assertRaisesRegex(ValueError, 'reviewed for selected'):
            providers.project(self.root, self.decisions, require_selection=False)

    def test_persistence_runtime_available_before_selection_and_not_for_alternatives(self):
        self.selection.unlink()
        decisions = {**self.decisions, 'persistence': [{'owner': 'household', 'profile': 'ef-postgresql'}]}
        projected = providers.project(self.root, decisions, require_selection=False)
        postgres = projected['persistence_runtimes'][0]
        self.assertEqual(['household'], postgres['owners'])
        self.assertIn('@sha256:', postgres['image'])
        self.assertEqual('18.6', postgres['version'])
        self.assertEqual('10.0.3', postgres['packages']['Npgsql.EntityFrameworkCore.PostgreSQL'])
        decisions['persistence'][0]['profile'] = 'ef-sqlite'
        self.assertEqual([], providers.project(self.root, decisions, require_selection=False)['persistence_runtimes'])
        decisions['persistence'][0]['profile'] = 'ef-postgresql'
        path = self.root / '.specify/extensions/program-kit-dotnet/references/persistence-runtimes.json'
        value = json.loads(path.read_text()); value['profiles']['ef-postgresql']['image'] = 'postgres:latest'
        write_json(path, value)
        with self.assertRaisesRegex(ValueError, 'exact server version and digest'):
            providers.project(self.root, decisions, require_selection=False)

    def test_selected_catalog_drift_is_not_silently_rebound(self):
        selection = json.loads(self.selection.read_text())
        selection['catalog']['resolutionSha256'] = '0' * 64
        write_json(self.selection, selection)
        with self.assertRaises(ValueError):
            providers.project(self.root, self.decisions)

    def test_explicit_alternate_host_and_consumer_identity_do_not_inherit_local_runtime(self):
        self.selection.unlink()
        decisions = {'selected_profiles': ['dotnet'], 'dotnet': {'program_kit_host_opt_out': True},
                     'identity': {'provider': 'keycloak', 'scope': 'consumer-service'}}
        result = providers.project(self.root, decisions)
        self.assertEqual([], result['selected_packages'])
        self.assertIsNone(result['identity_runtime'])
        decisions['web'] = {'secure_profile': 'bff-cookie-v1'}
        with self.assertRaisesRegex(ValueError, 'building-block selection'):
            providers.project(self.root, decisions)

    def test_missing_managed_security_control_is_rejected_before_architecture_dispatch(self):
        relative = '.specify/extensions/program-kit-dotnet/references/web-security-evidence.json'
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        original = json.loads((ROOT / relative.replace('.specify/', '')).read_text(encoding='utf-8'))
        original['controls'] = [c for c in original['controls'] if c['id'] != 'WEB-C06']
        write_json(path, original)
        with self.assertRaisesRegex(context.ContextError, 'incomplete'):
            context.managed_web_control_projection(self.root, {'assessment_decisions': {'web': {'secure_profile': 'bff-cookie-v1'}}})

    def test_maintained_provider_recipes_bind_real_fixtures_and_exact_cases(self):
        import managed_provider_probes as probes
        from bootstrap_lifecycle import validate_recipe
        governance = self.root / '.specify/extensions/program-kit-governance'
        shutil.copytree(ROOT / 'extensions/program-kit-governance/examples', governance / 'examples')
        (governance / 'scripts').mkdir()
        shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/compatibility_process.py', governance / 'scripts/compatibility_process.py')
        templates = self.root / '.specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles'
        shutil.copytree(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles', templates, dirs_exist_ok=True)
        decisions = {**self.decisions, 'web': {'secure_profile': 'bff-cookie-v1'},
                     'persistence': [{'owner': 'household', 'profile': 'ef-postgresql'}],
                     'toolchain': {'pins': {'dotnet-sdk': '10.0.202'}}}
        write_json(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
        image = 'ghcr.io/orbyss-io/foundation-host@sha256:' + 'a' * 64
        with patch.object(probes, '__file__', str(governance / 'scripts/managed_provider_probes.py')):
            with self.assertRaisesRegex(ValueError, 'registry-verified'):
                probes.render(self.root, 'bff-keycloak', 'bad-image', 'ghcr.io/orbyss-io/foundation-host:latest')
            for kind in probes.CASES:
                plan = probes.render(self.root, kind, kind, image)
                _, _, contract, cases = validate_recipe(self.root, kind, plan['recipe'])
                self.assertEqual(probes.CASES[kind], cases)
                self.assertTrue(contract['dependencyTargets'])
                for source in contract['fixtures'].values():
                    self.assertTrue((self.root / source).is_file())
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    probes.render(self.root, kind, kind, image)
            decisions['identity']['scope'] = 'consumer-service'
            write_json(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
            with self.assertRaisesRegex(ValueError, 'managed local identity'):
                probes.render(self.root, 'bff-keycloak', 'wrong-provider-scope', image)

    def test_projected_sources_are_queryable_hash_bound_and_missing_sources_fail(self):
        provider = providers.project(self.root, self.decisions)
        payload = {'stage_plan': {'provider_inputs': provider}, 'reading_policy': {'allowed_sources': []}, 'evidence_index': {}}
        evidence = {'artifacts': []}
        paths = context.bind_projected_sources(self.root, payload, evidence)
        self.assertIn(self.identity, paths)
        self.assertIn('docs/architecture/building-block-selection.json', paths)
        self.assertNotIn('Directory.Build.props', paths)  # Planned targets are not evidence sources.
        self.assertEqual(set(paths), set(payload['reading_policy']['allowed_sources']))
        self.assertEqual({i['path'] for i in evidence['artifacts']}, set(paths))
        old = payload['evidence_index']['sha256']
        (self.root / self.identity).write_text((self.root / self.identity).read_text() + '\n# changed installed input\n')
        fresh = {'artifacts': []}
        context.bind_projected_sources(self.root, payload, fresh)
        self.assertNotEqual(old, payload['evidence_index']['sha256'])
        (self.root / self.identity).unlink()
        with self.assertRaisesRegex(context.ContextError, 'STAGE-INPUT-MISSING'):
            context.bind_projected_sources(self.root, payload, {'artifacts': []})


if __name__ == '__main__':
    unittest.main()

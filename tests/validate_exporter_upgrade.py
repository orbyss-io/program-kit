"""Bounded exporter catalog transitions preserve design and reject runtime changes."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import validate_building_blocks as fixtures
import validate_local_upgrade as upgrades

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import openapi_upgrade_reconciliation as reconciliation


class ExporterUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.blocks = fixtures.load_module(fixtures.RESOLVER)
        self.upgrader = upgrades.load_updater()
        self.catalog = self.blocks.load_json(fixtures.CATALOG)
        old = copy.deepcopy(self.catalog)
        old['resolutionRevision'] -= 1
        old['families']['foundation'].pop('toolVersions')
        old['packages'][reconciliation.EXPORTER_KEY]['version'] = '0.2.2'
        self.old_path = self.root / '.specify' / reconciliation.CATALOG_RELATIVE
        fixtures.write_json(self.old_path, old)
        self.selection, self.architecture = fixtures.accepted_fixture(self.blocks, self.root, old)
        version = self.root / '.specify/extensions/program-kit-governance/extension.yml'
        version.parent.mkdir(parents=True)
        version.write_text('extension:\n  version: "0.12.5"\n')
        plan = self.blocks.resolve(self.root, self.selection, self.old_path, '0.12.5')
        self.lock = self.root / '.program-kit/building-blocks.lock.json'
        self.blocks.apply_materialization(self.root, self.lock, plan, old)
        self.originals = {p: p.read_bytes() for p in (self.selection, self.architecture, self.lock)}

    def test_explicit_transition_preserves_choices_history_and_current_lock_checks(self):
        self.assertEqual('materialized', self.upgrader.building_block_upgrade_state(self.root, ROOT))
        plan = {}
        self.assertEqual('materialized', self.upgrader.building_block_upgrade_state(self.root, ROOT, plan))
        reconciliation.archive_catalog_transition(plan)
        reconciliation.apply_catalog_transition(self.root, ROOT, plan, self.blocks, '0.12.5')
        previous = json.loads(self.originals[self.selection])
        current = self.blocks.load_json(self.selection)
        for field in ('authority', 'scopes', 'targets', 'instances'):
            self.assertEqual(previous[field], current[field])
        self.assertEqual(previous['revision'] + 1, current['revision'])
        self.assertEqual('Accepted', current['status'])
        for name, data in plan['originals'].items():
            self.assertEqual(data, (plan['archive'] / name).read_bytes())
        self.assertEqual(self.originals[self.lock], self.lock.read_bytes())
        # Old materialization cannot become current by changing its input binding.
        fixtures.write_json(self.old_path, self.catalog)
        with self.assertRaisesRegex(self.upgrader.UpgradeError, 'stale or corrupt'):
            self.upgrader.building_block_upgrade_state(self.root, ROOT)
        new = self.blocks.resolve(self.root, self.selection, self.old_path, '0.12.5')
        self.blocks.apply_materialization(self.root, self.lock, new, self.catalog)
        fixtures.write_json(self.old_path, self.catalog)
        self.assertEqual('materialized', self.upgrader.building_block_upgrade_state(self.root, ROOT))

    def test_interrupted_install_uses_preserved_old_catalog(self):
        plan = reconciliation.catalog_transition(self.root, ROOT, self.blocks, self.blocks.load_json(self.selection))
        reconciliation.archive_catalog_transition(plan)
        fixtures.write_json(self.old_path, self.catalog)
        resumed = reconciliation.catalog_transition(self.root, ROOT, self.blocks, self.blocks.load_json(self.selection))
        self.assertEqual(plan['fromHash'], resumed['fromHash'])
        self.assertEqual(plan['originals'], resumed['originals'])
        version = self.root / '.specify/extensions/program-kit-governance/extension.yml'
        version.write_text('extension:\n  version: "0.12.6"\n')
        transition = {}
        self.assertEqual('materialized', self.upgrader.building_block_upgrade_state(self.root, ROOT, transition))
        self.assertEqual('0.12.5', transition['previousInstalledVersion'])

    def test_interrupted_install_rejects_missing_and_changed_originals(self):
        plan = reconciliation.catalog_transition(self.root, ROOT, self.blocks, self.blocks.load_json(self.selection))
        reconciliation.archive_catalog_transition(plan)
        fixtures.write_json(self.old_path, self.catalog)
        for name in ('governance-extension.yml', 'lock.json', 'originals.json'):
            path = plan['archive'] / name
            original = path.read_bytes()
            for mutation in (b'{}', None):
                if mutation is None: path.unlink()
                else: path.write_bytes(mutation)
                with self.subTest(name=name, mutation=mutation), self.assertRaises(reconciliation.ReconciliationError):
                    reconciliation.catalog_transition(self.root, ROOT, self.blocks, self.blocks.load_json(self.selection))
                path.write_bytes(original)

    def test_runtime_or_policy_changes_cannot_use_exporter_authorization(self):
        release = self.root / 'candidate'
        for change in ('runtime', 'source', 'activation', 'template', 'revision'):
            catalog = copy.deepcopy(self.catalog)
            if change == 'runtime':
                catalog['families']['foundation']['releaseVersion'] = '0.2.3'
                for package in catalog['packages'].values():
                    if package['family'] == 'foundation' and package['packageId'] != 'Orbyss.Foundation.OpenApi.Exporter': package['version'] = '0.2.3'
            elif change == 'source': catalog['sources']['nuget-org']['url'] = 'https://example.test/index.json'
            elif change == 'activation': catalog['packages']['nuget:Orbyss.Foundation.Web.OpenApi']['activations'][0]['featureIdentity'] = 'Changed'
            elif change == 'revision': catalog['resolutionRevision'] += 1
            fixtures.write_json(release / reconciliation.CATALOG_RELATIVE, catalog)
            tools = release / 'extensions/program-kit-dotnet/templates/dotnet/files/.program-kit/eng/.config/dotnet-tools.json'
            fixtures.write_json(tools, {'tools': {'orbyss.foundation.openapi.exporter': {'version': '0.2.5' if change == 'template' else self.catalog['packages'][reconciliation.EXPORTER_KEY]['version']}}})
            with self.subTest(change=change), self.assertRaises(reconciliation.ReconciliationError):
                reconciliation.catalog_transition(self.root, release, self.blocks, self.blocks.load_json(self.selection))
        for path, data in self.originals.items(): self.assertEqual(data, path.read_bytes())

    def test_tool_overrides_cannot_relax_runtime_or_unknown_package_pins(self):
        for identity in ('Orbyss.Foundation.Web.OpenApi', 'Unknown.Tool'):
            catalog = copy.deepcopy(self.catalog)
            catalog['families']['foundation']['toolVersions'][identity] = '0.2.3'
            with self.assertRaises(self.blocks.ResolverError): self.blocks.validate_catalog(catalog)
        changed = copy.deepcopy(self.catalog)
        changed['families']['foundation']['toolVersions']['Orbyss.Foundation.OpenApi.Exporter'] = '0.2.5'
        self.assertNotEqual(self.blocks.catalog_resolution_sha256(self.catalog), self.blocks.catalog_resolution_sha256(changed))

    def test_planning_updates_only_exporter_and_preserves_runtime_pins(self):
        text = 'Foundation Host 0.2.2; Orbyss.Foundation.OpenApi.Exporter 0.2.2; analyzer 0.2.2.\nexporter0.2.2\n'
        result = reconciliation.reconcile_planning_text(text, ['0.2.2'], '0.2.3')
        self.assertEqual('Foundation Host 0.2.2; Orbyss.Foundation.OpenApi.Exporter 0.2.3; analyzer 0.2.2.\nexporter0.2.3\n', result)
        self.assertEqual('Use exporter 0.2.3.', reconciliation.reconcile_planning_text('Use exporter 0.2.2.', ['0.2.2'], '0.2.3'))
        self.assertEqual('Use exporter 0.2.2-preview.1.', reconciliation.reconcile_planning_text('Use exporter 0.2.2-preview.1.', ['0.2.2'], '0.2.3'))

    def test_retained_profile_survives_new_default_without_changing_selection(self):
        before = self.selection.read_bytes()
        snapshot = self.blocks.preserve_dependency_profile(self.root, self.blocks.load_json(self.selection), self.old_path)
        fixtures.write_json(self.old_path, self.catalog)
        resolved = self.blocks.resolve(self.root, self.selection, self.old_path, '0.12.6')
        self.assertEqual('0.2.2', self.blocks.load_json(snapshot)['families']['foundation']['releaseVersion'])
        self.assertEqual('0.12.6', resolved['producer']['programKitVersion'])
        self.assertEqual(before, self.selection.read_bytes())
        snapshot.write_text('{}')
        with self.assertRaises(self.blocks.ResolverError):
            self.blocks.resolve(self.root, self.selection, self.old_path, '0.12.6')


if __name__ == '__main__':
    unittest.main()

"""Real materialization transitions and bounded retry admission; no workers."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import validate_building_blocks as fixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import upgrade_program_kit as upgrade


class UpgradeRetryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='upgrade-real-transition-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.blocks = fixture.load_module(fixture.RESOLVER)
        self.catalog = self.blocks.load_json(fixture.CATALOG)
        self.selection, self.architecture = fixture.accepted_fixture(self.blocks, self.root, self.catalog)
        self.version = (ROOT / 'VERSION').read_text().strip()
        self.manifest = self.root / '.specify/extensions/program-kit-governance/extension.yml'
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text('extension:\n  version: "0.12.6"\n')
        catalog_path = self.root / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
        catalog_path.parent.mkdir(parents=True)
        shutil.copyfile(fixture.CATALOG, catalog_path)
        self.lock_path = self.root / 'eng/building-blocks.lock.json'
        original = self.blocks.resolve(self.root, self.selection, fixture.CATALOG, '0.12.6')
        self.blocks.apply_materialization(self.root, self.lock_path, original, self.catalog)
        self.original = self.lock_path.read_bytes()
        self.attempt_path, self.attempt = upgrade.begin_attempt(self.root, ROOT, self.version, '0.12.6')
        self.attempt.update(status='incomplete', diagnostic='fixture: interruption after sequential component writes')
        upgrade.write_attempt(self.attempt_path, self.attempt)
        self.manifest.write_text('extension:\n  version: "' + self.version + '"\n')
        self.context = upgrade.upgrade_retry_context(self.root, ROOT, self.version)

    def apply_target(self):
        target = self.blocks.resolve(self.root, self.selection, fixture.CATALOG, self.version)
        self.blocks.apply_materialization(self.root, self.lock_path, target, self.catalog)
        return target

    def state(self, context=True):
        return upgrade.building_block_upgrade_state(self.root, ROOT, retry_context=self.context if context else None)

    def test_actual_original_then_complete_target_materialization_are_admitted_only_with_retry_context(self):
        self.assertEqual('materialized', self.state())
        selection = self.selection.read_bytes()
        architecture = self.architecture.read_bytes()
        first_attempt = self.attempt_path.read_bytes()
        target = self.apply_target()
        self.assertEqual(target, self.blocks.load_json(self.lock_path))
        self.assertEqual('materialized', self.state())
        with self.assertRaisesRegex(upgrade.UpgradeError, 'stale or corrupt'):
            self.state(context=False)
        self.assertEqual(selection, self.selection.read_bytes())
        self.assertEqual(architecture, self.architecture.read_bytes())
        self.assertEqual(first_attempt, self.attempt_path.read_bytes())
        archived = self.root / self.attempt['originals']['lock']['path']
        self.assertEqual(self.original, archived.read_bytes())

    def test_mixed_lock_and_changed_actual_materialization_remain_errors(self):
        target = self.apply_target()
        mixed = copy.deepcopy(target)
        mixed['planDigest'] = '0' * 64
        fixture.write_json(self.lock_path, mixed)
        with self.assertRaisesRegex(upgrade.UpgradeError, 'stale or corrupt'):
            self.state()
        fixture.write_json(self.lock_path, target)
        project = self.root / 'src/Test.Feature/Test.Feature.csproj'
        project.write_text(project.read_text().replace('Orbyss.Foundation.DomainEvents', 'Unknown.Package'))
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU116'):
            self.state()

    def test_even_complete_recomputed_target_cannot_borrow_a_changed_selection(self):
        self.apply_target()
        changed = self.blocks.load_json(self.selection)
        changed['revision'] += 1
        fixture.write_json(self.selection, changed)
        fixture.refresh_registration(self.selection, self.architecture)
        recomputed = self.blocks.resolve(self.root, self.selection, fixture.CATALOG, self.version)
        fixture.write_json(self.lock_path, recomputed)
        with self.assertRaisesRegex(upgrade.UpgradeError, 'retry selection differs'):
            self.state()

    def test_pending_transaction_and_changed_original_stay_blocked(self):
        self.apply_target()
        pending = self.blocks.transaction_root(self.root) / 'incomplete/journal.json'
        pending.parent.mkdir(parents=True)
        pending.write_text('{}')
        with self.assertRaisesRegex(upgrade.UpgradeError, 'unfinished'):
            self.state()
        archived = self.root / self.attempt['originals']['selection']['path']
        archived.write_bytes(archived.read_bytes() + b' ')
        with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU121'):
            upgrade.upgrade_retry_context(self.root, ROOT, self.version)

    def test_recomputed_target_cannot_borrow_changed_architecture_authority(self):
        self.apply_target()
        architecture = self.blocks.load_json(self.architecture)
        architecture['decisions'][0]['rationale'] = 'A different current decision basis'
        fixture.write_json(self.architecture, architecture)
        target = self.blocks.resolve(self.root, self.selection, fixture.CATALOG, self.version)
        fixture.write_json(self.lock_path, target)
        with self.assertRaisesRegex(upgrade.UpgradeError, 'architecture authority changed'):
            self.state()


if __name__ == '__main__':
    unittest.main()

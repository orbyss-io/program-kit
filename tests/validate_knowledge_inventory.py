"""Knowledge inventory coverage; this is bookkeeping, not semantic correctness proof."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root, inventory, obligations):
    extensions = root / 'extensions'
    actual = {p.relative_to(extensions).as_posix() for directory in extensions.glob('*/references') for p in directory.rglob('*.md')}
    records = inventory['sources']
    declared = {r['path'] for r in records}
    if len(declared) != len(records) or actual != declared:
        raise ValueError(f'Knowledge inventory mismatch: unmapped={sorted(actual-declared)}, stale={sorted(declared-actual)}')
    for record in records:
        if not record.get('phases') or not record.get('enforcement', '').strip():
            raise ValueError('Every source needs phase routing and an explicit enforcement disposition')
    ids = set()
    for obligation in obligations['requirements']:
        if obligation['id'] in ids or not set(obligation['sources']) <= declared:
            raise ValueError('Obligation source is unregistered or identity is duplicated')
        ids.add(obligation['id'])
    for path in root.glob('presets/*/templates/*governance.md'):
        if path.name in {'plan-governance.md', 'tasks-governance.md'}:
            content = path.read_text(encoding='utf-8')
            if 'phase-context.md' not in content or 'verification-plan.json' not in content:
                raise ValueError('Producer template lost phase obligations: ' + str(path))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        references = ROOT / 'extensions/program-kit-governance/references'
        self.inventory = json.loads((references / 'knowledge-inventory.json').read_text(encoding='utf-8'))
        self.obligations = json.loads((references / 'phase-obligations.json').read_text(encoding='utf-8'))

    def test_all_shipped_references_have_dispositions(self):
        validate(ROOT, self.inventory, self.obligations)

    def test_omitted_reference_is_visible(self):
        self.inventory['sources'].pop()
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            validate(ROOT, self.inventory, self.obligations)

    def test_missing_phase_route_is_visible(self):
        self.inventory['sources'][0]['phases'] = []
        with self.assertRaisesRegex(ValueError, 'phase routing'):
            validate(ROOT, self.inventory, self.obligations)

    def test_obligation_cannot_point_to_unregistered_knowledge(self):
        self.obligations['requirements'][0]['sources'].append('missing.md')
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            validate(ROOT, self.inventory, self.obligations)


if __name__ == '__main__':
    unittest.main()

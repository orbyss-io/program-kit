"""Knowledge inventory coverage; this is bookkeeping, not semantic correctness proof."""
import copy
import json
import tempfile
import sys
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from decision_knowledge import decision_rule


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
        route = record.get('route', {})
        if route.get('kind') not in {'phase', 'bootstrap', 'setup', 'manual', 'intake', 'maintainer', 'routing'}:
            raise ValueError('Every source needs an actual active or explicit non-feature route')
        if not route.get('via') or not route.get('review', '').strip():
            raise ValueError('Knowledge route needs a producer and its review scope')
        for relative in route['via']:
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError('Missing knowledge route: ' + relative)
            if route['kind'] == 'phase' and path.name in {'historical_phase_evidence.py', 'artifact_ownership.py'}:
                raise ValueError('Historical-only route cannot claim active feature enforcement')
        content = (extensions / record['path']).read_text(encoding='utf-8')
        headings = re.findall(r'^## (.+)$', content, re.M) or re.findall(r'^# (.+)$', content, re.M)
        if route.get('sections') != headings:
            raise ValueError('Canonical rule groups lack a disposition: ' + record['path'])
    ids = set()
    for obligation in obligations['requirements']:
        if obligation['id'] in ids or not set(obligation['sources']) <= declared:
            raise ValueError('Obligation source is unregistered or identity is duplicated')
        ids.add(obligation['id'])
    for record in records:
        expected = [r['id'] for r in obligations['requirements'] if record['path'] in r['sources']]
        if record['route'].get('requirements') != expected:
            raise ValueError('Knowledge source has stale requirement routes')
    used = {i for r in obligations['requirements'] for i in r.get('decisionRules', [])}
    if used != set(obligations.get('decisionRules', {})):
        raise ValueError('Decision constraints are unused or unregistered')
    for identity, record in obligations['decisionRules'].items():
        if record['source'] not in declared:
            raise ValueError('Decision constraint source is unregistered')
        decision_rule(extensions, record, identity)
    for path in root.glob('presets/*/templates/*governance.md'):
        if path.name in {'plan-governance.md', 'tasks-governance.md'}:
            content = path.read_text(encoding='utf-8').lower()
            if 'plan' not in content or 'test' not in content:
                raise ValueError('Producer template lost phase obligations: ' + str(path))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        references = ROOT / 'extensions/program-kit-governance/references'
        self.inventory = json.loads((references / 'phase-obligations.json').read_text(encoding='utf-8'))
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

    def test_invented_and_historical_routes_cannot_claim_active_enforcement(self):
        row = self.inventory['sources'][0]
        row['route']['via'] = ['missing-validator.py']
        with self.assertRaisesRegex(ValueError, 'Missing knowledge route'):
            validate(ROOT, self.inventory, self.obligations)
        row['route'].update(kind='phase', via=['extensions/program-kit-governance/scripts/historical_phase_evidence.py'])
        with self.assertRaisesRegex(ValueError, 'Historical-only'):
            validate(ROOT, self.inventory, self.obligations)

    def test_dropped_rule_group_and_unreferenced_constraint_are_visible(self):
        self.inventory['sources'][0]['route']['sections'] = []
        with self.assertRaisesRegex(ValueError, 'rule groups'):
            validate(ROOT, self.inventory, self.obligations)

    def test_obligation_cannot_point_to_unregistered_knowledge(self):
        self.obligations['requirements'][0]['sources'].append('missing.md')
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            validate(ROOT, self.inventory, self.obligations)

    def test_discovery_routes_resolve_to_registered_shipped_knowledge(self):
        extension = ROOT/'extensions/program-kit-governance'
        capabilities = json.loads((extension/'references/capability-index.json').read_text(encoding='utf-8'))['capabilities']
        by_id = {row['id']: row for row in capabilities}
        self.assertEqual('references/functional-discovery.md', by_id['functional-discovery']['reference'])
        registered = {r['path'] for r in self.inventory['sources']}
        for row in capabilities:
            path = extension/row['reference']
            self.assertTrue(path.is_file(), row['id'])
            self.assertIn(path.relative_to(ROOT/'extensions').as_posix(), registered)


if __name__ == '__main__':
    unittest.main()

"""Small domain maps drive optional generators without approval fingerprints."""
import copy
from pathlib import Path
import unittest
from owned_fixture import FixtureDirectory
import validate_building_blocks as fixtures

class MinimalMapSelection(unittest.TestCase):
    def setUp(self):
        self.temp = FixtureDirectory(prefix='minimal-selection-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tool = fixtures.load_module(fixtures.RESOLVER)
        self.catalog = self.tool.load_json(fixtures.CATALOG)
        self.selection_path, self.map_path = fixtures.accepted_fixture(self.tool, self.root, self.catalog)
        self.adr = self.root / 'docs/decision.md'
        self.adr.write_text('# Use domain events\n\nStatus: Accepted\n', encoding='utf-8')
        self.model = {'schema_version': '2.0', 'model_id': 'sample', 'title': 'Synthetic service',
            'elements': [{'id': 'service', 'type': 'container', 'name': 'Service', 'description': 'Owns events'}],
            'relationships': [], 'decisions': [{'id': 'use-building-blocks', 'status': 'Accepted', 'path': 'docs/decision.md'}]}
        fixtures.write_json(self.map_path, self.model)

    def resolve(self):
        return self.tool.resolve(self.root, self.selection_path, fixtures.CATALOG, '1.0.0-preview.1')

    def test_resolution_acceptance_and_readable_edits(self):
        self.assertTrue(self.resolve()['targets'][0]['packages'])
        original = self.map_path.read_bytes()
        selection = self.tool.load_json(self.selection_path); selection['status'] = 'Draft'
        fixtures.write_json(self.selection_path, selection)
        result = self.tool.accept_selection(self.root, self.selection_path, fixtures.CATALOG,
            'docs/architecture/architecture-map.json', ['use-building-blocks'], 'Choose domain events', '1.0.0-preview.1')
        self.assertTrue(result['targets'][0]['packages'])
        self.assertEqual(original, self.map_path.read_bytes())
        self.adr.write_text(self.adr.read_text() + '\nAdditional explanation.\n', encoding='utf-8')
        self.map_path.write_text(self.map_path.read_text() + '\n', encoding='utf-8')
        self.assertTrue(self.resolve()['targets'][0]['packages'])

    def test_selected_decisions_need_real_confined_documents(self):
        for changes, code in [({'status': 'Proposed'}, 'PKB113'), ({'path': 'docs/missing.md'}, 'PKB113'),
                              ({'path': '../outside.md'}, 'PKB300'), ({'id': 'unrelated'}, 'PKB113')]:
            with self.subTest(changes=changes):
                model = copy.deepcopy(self.model); model['decisions'][0].update(changes)
                fixtures.write_json(self.map_path, model)
                with self.assertRaisesRegex(self.tool.ResolverError, code): self.resolve()

    def test_placement_materialization_and_negative_checks(self):
        selection = self.tool.load_json(self.selection_path)
        for target in selection['targets']:
            target['placement'] = {'state': 'planned', 'owner': 'service',
                'decisionIds': ['use-building-blocks'], 'rationale': 'Use service boundary'}
        self.tool.validate_placements(self.root, selection, require_all=True)
        draft = copy.deepcopy(selection); draft['status'] = 'Draft'
        with self.assertRaisesRegex(self.tool.ResolverError, 'PKB306.*already observed'):
            self.tool.validate_placements(self.root, draft, require_all=True)
        for change, code in [(lambda t: t['placement'].update(owner='absent'), 'PKB306'),
                             (lambda t: t['placement'].update(decisionIds=['absent']), 'PKB306'),
                             (lambda t: t.update(path='missing.csproj', placement={**t['placement'], 'state': 'observed'}), 'PKB306'),
                             (lambda t: t.update(path='../outside.csproj'), 'PKB300')]:
            with self.subTest(code=code):
                bad = copy.deepcopy(selection); change(bad['targets'][0])
                with self.assertRaisesRegex(self.tool.ResolverError, code):
                    self.tool.validate_placements(self.root, bad, require_all=True)

if __name__ == '__main__': unittest.main()

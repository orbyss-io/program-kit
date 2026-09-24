"""Scoped canonical knowledge, ownership inheritance and lifecycle-view freshness."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from feature_knowledge import project, source_hash


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='feature-knowledge-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'docs/architecture/architecture-map.json'
        self.path.parent.mkdir(parents=True)
        self.model = {'elements': [{'id': 'reservations'}, {'id': 'reserve', 'parent': 'reservations'}, {'id': 'billing'}],
                      'relationships': [], 'constraints': [], 'decisions': [],
                      'strategic_model': {'bounded_contexts': [
                          {'element': 'reservations', 'invariants': ['Success requires capacity acknowledgement'], 'lifecycle': 'Requested -> Confirmed'},
                          {'element': 'billing', 'invariants': ['Invoice belongs to billing']}],
                          'modules': [{'element': 'reserve', 'context': 'reservations', 'responsibilities': ['Reserve equipment']} ]}}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.model), encoding='utf-8')

    def test_module_inherits_owning_context_semantics(self):
        result = project(self.root, ['reserve'])
        contexts = result['strategic_model']['bounded_contexts']
        self.assertEqual(['reservations'], [item['element'] for item in contexts])
        self.assertEqual(['Success requires capacity acknowledgement'], contexts[0]['invariants'])

    def test_unrelated_semantics_do_not_invalidate_selected_scope(self):
        before = project(self.root, ['reserve'])
        self.model['strategic_model']['bounded_contexts'][1]['invariants'].append('Other change')
        self.save()
        self.assertEqual(before, project(self.root, ['reserve']))
        self.model['strategic_model']['bounded_contexts'][0]['invariants'].append('One durable owner')
        self.save()
        self.assertNotEqual(before, project(self.root, ['reserve']))

    def test_new_boundary_contract_enters_the_projection(self):
        self.model['relationships'] = [{'id': 'reserve-billing', 'source': 'reservations', 'target': 'billing'}]
        self.model['strategic_model']['context_relationships'] = [
            {'upstream': 'reservations', 'downstream': 'billing', 'contract': 'charge', 'failure_owner': 'reservations'}]
        self.model['strategic_model']['contracts'] = [{'id': 'charge', 'owner': 'billing', 'version': 'v1'}]
        self.save()
        result = project(self.root, ['reserve'])
        self.assertEqual('charge', result['strategic_model']['contracts'][0]['id'])
        self.assertEqual('reservations', result['strategic_model']['context_relationships'][0]['failure_owner'])

    def test_unknown_scope_cannot_suppress_knowledge(self):
        for scope in ([], ['missing'], 'reserve', [{}]):
            with self.assertRaises(ValueError):
                project(self.root, scope)

    def test_generated_status_view_does_not_change_authored_authority(self):
        path = self.root / 'architecture.md'
        text = '# Architecture\n\nAccepted rule.\n\n<!-- PROGRAM-KIT:ROADMAP-VIEW:START -->\nActive\n<!-- PROGRAM-KIT:ROADMAP-VIEW:END -->\n'
        path.write_text(text, encoding='utf-8')
        before = source_hash(path)
        path.write_text(text.replace('Active', 'Delivered'), encoding='utf-8')
        self.assertEqual(before, source_hash(path))
        path.write_text(text.replace('Accepted rule.', 'A changed rule.'), encoding='utf-8')
        self.assertNotEqual(before, source_hash(path))


if __name__ == '__main__':
    unittest.main()

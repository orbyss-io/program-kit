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

    def test_feature_seed_and_discovery_neighbors_are_scoped(self):
        self.model['strategic_model']['candidate_slices'] = [
            {'id': 'reserve-feature', 'contexts': ['reservations'], 'journey': 'reserve-journey',
             'epic': 'RM01', 'commitment': 'intended', 'seed': {'details': 'Preserve rich reservation thought.'}},
            {'id': 'renew-feature', 'contexts': ['reservations'], 'journey': 'renew-journey',
             'epic': 'RM01', 'commitment': 'exploratory', 'outcome': 'Extend an existing reservation.',
             'seed': {'details': 'Detailed possible renewal behavior.'}},
            {'id': 'billing-feature', 'contexts': ['billing'], 'journey': 'billing-journey',
             'epic': 'RM02', 'seed': {'details': 'Unrelated billing details.'}}]
        self.model['strategic_model']['journeys'] = [
            {'id': identity, 'steps': [], 'discovery': ['clarify-policy']}
            for identity in ('reserve-journey', 'renew-journey', 'billing-journey')]
        self.save()
        projected = project(self.root, ['reserve'], feature_id='reserve-feature')
        candidates = projected['strategic_model']['candidate_slices']
        self.assertEqual(['reserve-feature', 'renew-feature'], [item['id'] for item in candidates])
        self.assertEqual('Preserve rich reservation thought.', candidates[0]['seed']['details'])
        self.assertNotIn('seed', candidates[1])
        self.assertEqual(['reserve-journey', 'renew-journey'], [item['id'] for item in projected['strategic_model']['journeys']])
        self.model['strategic_model']['candidate_slices'][1]['seed']['details'] = 'A later sibling refinement.'
        self.save()
        self.assertEqual(projected, project(self.root, ['reserve'], feature_id='reserve-feature'))
        self.model['strategic_model']['candidate_slices'][0]['seed']['details'] = 'Selected boundary changed.'
        self.save()
        self.assertNotEqual(projected, project(self.root, ['reserve'], feature_id='reserve-feature'))

    def test_feature_dependency_contract_is_retained_without_whole_neighbor_seed(self):
        self.model['strategic_model']['candidate_slices'] = [
            {'id': 'reserve-feature', 'contexts': ['reservations'], 'journey': 'reserve-journey',
             'dependencies': [{'feature': 'billing-feature', 'contract': 'charge', 'rationale': 'Requires charge terms.'}]},
            {'id': 'billing-feature', 'contexts': ['billing'], 'journey': 'billing-journey',
             'seed': {'details': 'Unselected implementation ideas.'}}]
        self.model['strategic_model']['contracts'] = [{'id': 'charge', 'owner': 'billing'}]
        self.save()
        result = project(self.root, ['reserve'], feature_id='reserve-feature')['strategic_model']
        self.assertEqual('charge', result['contracts'][0]['id'])
        self.assertEqual('billing-feature', result['candidate_slices'][1]['id'])
        self.assertNotIn('seed', result['candidate_slices'][1])

    def test_provider_retains_direct_future_consumer_boundary_and_contract(self):
        self.model = {
            'elements': [{'id': 'policies'}, {'id': 'claims'}, {'id': 'billing'}],
            'relationships': [{'id': 'claims-policy-terms', 'source': 'claims', 'target': 'policies'}],
            'constraints': [], 'decisions': [],
            'strategic_model': {
                'bounded_contexts': [{'element': 'policies'}, {'element': 'claims'}, {'element': 'billing'}],
                'contracts': [{'id': 'historical-terms', 'owner': 'claims', 'version': 'v1'}],
                'candidate_slices': [
                    {'id': 'policy-terms', 'contexts': ['policies'], 'journey': 'maintain-policies',
                     'seed': {'details': 'Maintain the original policy terms.'}},
                    {'id': 'calculate-claim', 'contexts': ['claims'], 'journey': 'claim-calculation',
                     'commitment': 'intended', 'outcome': 'Calculate against the applicable policy revision.',
                     'dependencies': [{'feature': 'policy-terms', 'contract': 'historical-terms',
                                       'rationale': 'Historical claims retain their applicable immutable revision.'}],
                     'seed': {'details': 'Detailed future claim calculation rules.'}},
                    {'id': 'invoice-policy', 'contexts': ['billing'], 'journey': 'invoice',
                     'seed': {'details': 'Unrelated billing details.'}}],
                'journeys': [{'id': identity, 'steps': [], 'discovery': ['clarify-policy']}
                             for identity in ('maintain-policies', 'claim-calculation', 'invoice')]}}
        self.save()
        result = project(self.root, ['policies'], feature_id='policy-terms')
        knowledge = result['strategic_model']
        self.assertEqual(['policy-terms', 'calculate-claim'], [item['id'] for item in knowledge['candidate_slices']])
        dependent = knowledge['candidate_slices'][1]
        self.assertEqual('Historical claims retain their applicable immutable revision.', dependent['dependencies'][0]['rationale'])
        self.assertNotIn('seed', dependent)
        self.assertEqual(['historical-terms'], [item['id'] for item in knowledge['contracts']])
        self.assertEqual(['maintain-policies', 'claim-calculation'], [item['id'] for item in knowledge['journeys']])
        self.model['strategic_model']['candidate_slices'][1]['seed']['details'] = 'A later future-feature refinement.'
        self.model['strategic_model']['candidate_slices'][2]['seed']['details'] = 'A later unrelated refinement.'
        self.save()
        self.assertEqual(result, project(self.root, ['policies'], feature_id='policy-terms'))

    def test_seed_decision_metadata_is_preserved_without_canonical_adr_interpretation(self):
        from architecture_map import validate_feature_seed
        seed = {'brief': {'decisions': [
            {'question': 'An unfinished source question', 'decision_refs': None},
            {'question': 'Another proposal', 'decision_refs': ['source-only']} ]}}
        validate_feature_seed(seed)
        self.model['strategic_model']['candidate_slices'] = [
            {'id': 'reserve-feature', 'contexts': ['reservations'], 'seed': copy.deepcopy(seed)}]
        self.model['decisions'] = [{'id': 'source-only'}]
        self.save()
        result = project(self.root, ['reserve'], feature_id='reserve-feature')
        self.assertEqual(seed, result['strategic_model']['candidate_slices'][0]['seed'])
        self.assertEqual([], result['decisions'])

    def test_legacy_projection_keeps_existing_shape(self):
        self.model['strategic_model']['candidate_slices'] = [
            {'id': 'legacy', 'contexts': ['reservations'], 'journey': 'legacy-journey'}]
        self.save()
        self.assertNotIn('candidate_slices', project(self.root, ['reserve'])['strategic_model'])
        self.assertEqual(['reserve'], project(self.root, ['reserve'], feature_id='new-feature')['scope'])

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

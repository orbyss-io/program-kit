"""Offline authoring regression tests; optional replay of a preserved human intake."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import intake_authoring as authoring
import contract_shapes as shapes
import architecture_map as architecture
import bootstrap_intake as intake

EXAMPLE = ROOT / 'extensions/program-kit-governance/references/intake-authoring-example.json'


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(authoring.encode(value), encoding='utf-8')


def make_source(model: dict, document: dict) -> dict:
    result = copy.deepcopy(document)
    result.pop('artifacts', None)
    result['domain_analysis'] = {'boundary_challenges': result['domain_analysis']['boundary_challenges']}
    result['capability_assessments'] = [{'id': item['id'], 'need': item['need']} for item in result['capability_assessments']]
    return {'map': copy.deepcopy(model), 'intake': result}


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='program-kit-authoring-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.intent = self.root / 'docs/architecture/project-intent.md'
        self.intent.parent.mkdir(parents=True)
        self.intent.write_text('# Purpose\nRequester registers a request. Révision – café 中文.\n', encoding='utf-8')
        self.source = json.loads(EXAMPLE.read_text(encoding='utf-8'))
        self.source_path = Path('docs/architecture/intake-authoring.json')

    def build(self):
        write_json(self.root / self.source_path, self.source)
        return authoring.build(self.root, self.source_path)

    def test_example_builds_valid_draft_preserving_unicode_and_references(self):
        self.build()
        document = intake.validate_intake(self.root, allowed_statuses={'draft'})
        self.assertEqual(document['status'], 'draft')
        self.assertIn('registration', document['domain_analysis']['founding_decision_candidates'][0]['affected_elements'])
        map_path = self.root / intake.CANONICAL_ARTIFACTS['architecture_map']
        self.assertIn('—', map_path.read_text(encoding='utf-8'))
        self.assertIn('中文', self.intent.read_text(encoding='utf-8'))
        before = {p.name: p.read_bytes() for p in self.intent.parent.iterdir()}
        self.build()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.intent.parent.iterdir()})

    def test_confirmed_intake_cannot_be_replaced(self):
        self.build()
        path = self.root / intake.CANONICAL_INTAKE
        document = intake.load_object(path)
        document['status'] = 'confirmed'
        write_json(path, document)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'confirmed intake'):
            self.build()
        self.assertEqual(before, path.read_bytes())

    def test_source_cannot_confirm(self):
        self.source['intake']['status'] = 'confirmed'
        with self.assertRaisesRegex(ValueError, 'cannot confirm'):
            self.build()

    def test_multiple_shape_errors_reported_together_without_writes(self):
        self.source['map']['strategic_model']['subdomains'][0]['classification'] = 'Core'
        del self.source['map']['strategic_model']['bounded_contexts'][0]['vision']
        self.source['map']['strategic_model']['modules'][0]['context_id'] = 'wrong-key'
        self.source['map']['sources'] = [None]
        self.source['map']['documentation'] = 'not-an-array'
        with self.assertRaises(ValueError) as error:
            self.build()
        self.assertIn('classification', str(error.exception))
        self.assertIn('vision', str(error.exception))
        self.assertIn('context_id', str(error.exception))
        self.assertIn('sources/0', str(error.exception))
        self.assertIn('documentation', str(error.exception))
        self.assertFalse((self.root / intake.CANONICAL_INTAKE).exists())

    def test_invalid_semantics_preserve_existing_draft(self):
        self.build()
        before = (self.root / intake.CANONICAL_INTAKE).read_bytes()
        self.source['map']['strategic_model']['founding_decisions'][0]['affected_elements'].append('missing-element')
        with self.assertRaises(architecture.ArchitectureMapError):
            self.build()
        self.assertEqual(before, (self.root / intake.CANONICAL_INTAKE).read_bytes())

    def test_unknown_evidence_is_not_invented(self):
        self.source['map']['strategic_model']['subdomains'][0]['evidence'] = ['unknown-evidence']
        with self.assertRaises(intake.IntakeError):
            self.build()

    def test_different_module_parent_not_silently_changed(self):
        self.source['map']['elements'][-1]['parent'] = 'another-context'
        with self.assertRaisesRegex(ValueError, 'conflicting parent'):
            self.build()

    def test_owned_schema_vocabulary_is_supported(self):
        from json_schema import engine
        for document in ('map', 'intake'):
            engine(shapes.schema_for(document))

    def test_descriptor_exposes_nested_exact_contract(self):
        descriptor = shapes.describe('map', 'bounded_context')
        self.assertIn('element', descriptor['required'])
        self.assertNotIn('id', descriptor['required'])
        self.assertEqual(descriptor['fields']['boundary_kind']['enum'], ['domain-model', 'cross-cutting-concern'])
        patterns = shapes.describe('map', 'context_relationship')['fields']['patterns']['items']['enum']
        self.assertIn('acl', patterns)
        self.assertNotIn('anti-corruption-layer', patterns)

    def test_descriptor_navigation_is_compact_and_inline_sections_are_discoverable(self):
        for document in ('map', 'intake'):
            root = shapes.describe(document, 'root')
            self.assertLess(len(json.dumps(root)), 6000)
            self.assertNotIn('properties', json.dumps(root['fields']))
            self.assertEqual(root['sections'], shapes.sections(document))
        for section in ('open_items', 'choices'):
            self.assertIn(section, shapes.sections('intake'))
            self.assertIn('id', shapes.describe('intake', section)['required'])
        with self.assertRaisesRegex(ValueError, 'Valid sections:.*open_items'):
            shapes.describe('intake', 'open_item')

    def test_descriptor_reports_real_owner_options_without_modifying_source(self):
        before = copy.deepcopy(self.source)
        result = authoring.describe_authoring('map', 'capability_binding', self.source)
        for field, literals in architecture.CAPABILITY_OWNER_LITERALS.items():
            self.assertEqual(result['ownerOptions'][field], sorted({'request-handling'} | literals))
            self.assertNotIn('registration', result['ownerOptions'][field])
            self.assertEqual(result['semanticRules'][field]['literals'], sorted(literals))
        self.assertEqual(self.source, before)

    def test_descriptor_cli_lists_sections_and_returns_actionable_invalid_section(self):
        command = [sys.executable, str(SCRIPTS / 'intake_authoring.py'), 'describe', '--document', 'intake']
        result = subprocess.run(command + ['--list-sections'], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('open_items', json.loads(result.stdout)['sections'])
        result = subprocess.run(command + ['--section', 'open_item'], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertIn('open_items', result.stderr)

    def semantic_fixture(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        import validate_bootstrap_semantics as fixture
        return fixture.semantic_model(self.intent)

    def test_owner_and_cross_context_errors_are_batched_without_changing_outputs(self):
        self.build()
        before = {p.name: p.read_bytes() for p in self.intent.parent.iterdir() if p.name != self.source_path.name}
        model = self.semantic_fixture()
        self.source['map'] = model
        bindings = model['strategic_model']['capability_bindings']
        bindings[0]['semantic_owner'] = 'The team owns semantics'
        bindings[0]['integration_owner'] = 'pk-forms-profile'
        bindings[1]['integration_owner'] = 'Not a context'
        records = model['strategic_model']['context_relationships']
        missing = records.pop()['relationship']
        duplicate = records[0]['relationship']
        records.append(copy.deepcopy(records[0]))
        with self.assertRaises(ValueError) as error:
            self.build()
        message = str(error.exception)
        for expected in ('/capability_bindings/0/semantic_owner', '/capability_bindings/0/integration_owner',
                         '/capability_bindings/1/integration_owner', missing, duplicate, 'calculator-forms'):
            self.assertIn(expected, message)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.intent.parent.iterdir()
                                  if p.name != self.source_path.name})

    def test_preflight_preserves_valid_owners_and_covers_module_edges_individually(self):
        model = self.semantic_fixture()
        self.assertEqual(authoring.authoring_semantic_errors(model), [])
        before = copy.deepcopy(model)
        for field, options in authoring.owner_options(model).items():
            for owner in options:
                model['strategic_model']['capability_bindings'][0][field] = owner
                self.assertEqual(authoring.authoring_semantic_errors(model), [])
        model = before
        edge = copy.deepcopy(model['relationships'][-1])
        edge.update(id='module-edge', source='calculation', target='quantity-engine')
        model['relationships'].append(edge)
        self.assertIn('module-edge', '\n'.join(authoring.authoring_semantic_errors(model)))
        record = copy.deepcopy(model['strategic_model']['context_relationships'][-1])
        record['relationship'] = 'module-edge'
        model['strategic_model']['context_relationships'].append(record)
        self.assertEqual(authoring.authoring_semantic_errors(model), [])

    def test_preflight_reports_non_cross_context_typed_records(self):
        model = self.semantic_fixture()
        model['strategic_model']['context_relationships'][0]['relationship'] = 'uses-calculator'
        message = '\n'.join(authoring.authoring_semantic_errors(model))
        self.assertIn("'uses-calculator' has 1 typed records; expected 0", message)
        self.assertIn("'forms-catalog' has 0 typed records; expected 1", message)

    def test_ambiguous_capability_is_exposed_for_semantic_review(self):
        model = {'strategic_model': {
            'context_relationships': [{'relationship': 'texts', 'contract': 'resolve-text', 'atomicity': 'read-only'}],
            'journeys': [{'id': 'edit-text', 'steps': [{'relationship': 'texts', 'contract': 'resolve-text',
                                                      'description': 'Resolve and manage translated text.'}]}]}}
        review = authoring.semantic_review(model)
        self.assertEqual(review[0]['atomicity'], 'read-only')
        self.assertEqual(review[0]['journey_steps'][0]['journey'], 'edit-text')
        self.assertIn('manage', review[0]['journey_steps'][0]['description'])

    def test_shared_contract_does_not_mix_relationship_journey_steps(self):
        model = {'strategic_model': {
            'context_relationships': [
                {'relationship': relation, 'contract': 'shared-query', 'atomicity': 'read-only'}
                for relation in ('catalog-texts', 'estimate-texts', 'unused-texts')],
            'journeys': [{'id': journey, 'steps': [{'relationship': relation, 'contract': 'shared-query',
                                                  'description': description}]}
                         for journey, relation, description in (
                             ('catalog', 'catalog-texts', 'Resolve catalog text.'),
                             ('estimate', 'estimate-texts', 'Resolve estimate text.'),
                             ('second-catalog', 'catalog-texts', 'Resolve another catalog label.'))]}}
        before = copy.deepcopy(model)
        review = authoring.semantic_review(model)
        self.assertEqual([s['journey'] for s in review[0]['journey_steps']], ['catalog', 'second-catalog'])
        self.assertEqual([s['journey'] for s in review[1]['journey_steps']], ['estimate'])
        self.assertEqual(review[2]['journey_steps'], [])
        self.assertEqual(before, model)

    def test_command_cannot_use_read_only_context_contract(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        import validate_bootstrap_semantics as fixture
        model = fixture.semantic_model(self.intent)
        model['strategic_model']['contracts'][0]['kind'] = 'command'
        with self.assertRaisesRegex(architecture.ArchitectureMapError, 'command contract cannot use read-only'):
            architecture.validate_model(model)

    def test_output_failure_rolls_back_all_replaced_artifacts(self):
        self.build()
        targets = [self.root / relative for relative in (*intake.CANONICAL_ARTIFACTS.values(), intake.CANONICAL_INTAKE)]
        before = {path: path.read_bytes() for path in targets}
        self.source['map']['title'] = 'Changed title'
        original = Path.replace
        def replace(path, target):
            if str(target).endswith('workspace.dsl'):
                raise OSError('simulated replace failure')
            return original(path, target)
        with patch.object(Path, 'replace', replace):
            with self.assertRaises(OSError):
                self.build()
        self.assertEqual(before, {path: path.read_bytes() for path in targets})


def replay_session(evidence: Path) -> None:
    """Read preserved evidence without changing it; compare semantic output, not model speed."""
    with tempfile.TemporaryDirectory(prefix='program-kit-intake-replay-') as directory:
        root = Path(directory)
        intent_relative = intake.CANONICAL_ARTIFACTS['project_intent']
        (root / intent_relative).parent.mkdir(parents=True)
        (root / intent_relative).write_bytes((evidence / intent_relative).read_bytes())
        if (evidence / 'product-idea.md').exists():
            (root / 'product-idea.md').write_bytes((evidence / 'product-idea.md').read_bytes())
        model = intake.load_object(evidence / intake.CANONICAL_ARTIFACTS['architecture_map'])
        document = intake.load_object(evidence / intake.CANONICAL_INTAKE)
        source = make_source(model, document)
        write_json(root / 'source.json', source)
        authoring.build(root, Path('source.json'))
        rebuilt = intake.load_object(root / intake.CANONICAL_ARTIFACTS['architecture_map'])
        assert rebuilt['strategic_model'] == model['strategic_model'], 'Replay changed semantic decisions'
        assert intake.validate_intake(root, allowed_statuses={'draft'})['journeys'] == document['journeys']
        print('Preserved intake replay passed in one deterministic build; semantic decisions and all source journeys retained.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-evidence', type=Path)
    args = parser.parse_args()
    if args.session_evidence:
        replay_session(args.session_evidence)
    unittest.main(argv=[sys.argv[0]])

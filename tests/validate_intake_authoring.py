"""Offline authoring regression tests; optional replay of a preserved human intake."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
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

    def test_ambiguous_capability_is_exposed_for_semantic_review(self):
        model = {'strategic_model': {
            'context_relationships': [{'relationship': 'texts', 'contract': 'resolve-text', 'atomicity': 'read-only'}],
            'journeys': [{'id': 'edit-text', 'steps': [{'relationship': 'texts', 'contract': 'resolve-text',
                                                      'description': 'Resolve and manage translated text.'}]}]}}
        review = authoring.semantic_review(model)
        self.assertEqual(review[0]['atomicity'], 'read-only')
        self.assertEqual(review[0]['journey_steps'][0]['journey'], 'edit-text')
        self.assertIn('manage', review[0]['journey_steps'][0]['description'])

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

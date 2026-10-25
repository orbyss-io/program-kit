"""Existing product questions remain context, never an all-items confirmation protocol."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import specification_intake as intake


class FrontierTests(unittest.TestCase):
    def test_existing_questions_are_context_without_hash_or_applicability_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / intake.governance.BOOTSTRAP_INTAKE
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'open_items': [
                {'id': 'retention', 'question': 'How long are requests retained?', 'owner': 'Retention feature'},
                {'id': 'reporting', 'question': 'Which reporting format?', 'owner': 'Future reporting feature'}]}))
            brief_path = intake.begin(root, 'FEATURE', 'Register a request', feature='registration')
            brief = intake.read(brief_path)
            brief.update({key: 'Registration ' + key for key in intake.FIELDS})
            brief['decisions'] = []
            intake.atomic_write(brief_path, brief)
            context = intake.context(root, 'FEATURE', feature='registration')
            self.assertEqual(['retention', 'reporting'], [item['id'] for item in context['productFrontier']])
            self.assertNotIn('sha256', context['productFrontier'][0])
            intake.review(root, 'FEATURE', feature='registration')
            self.assertFalse((brief_path.parent / 'confirmation.json').exists())

    def test_absent_frontier_is_normal_and_malformed_selected_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual([], intake.product_frontier(root))
            path = root / intake.governance.BOOTSTRAP_INTAKE
            path.parent.mkdir(parents=True)
            path.write_text('{"open_items": "not a list"}')
            with self.assertRaisesRegex(ValueError, 'objects'):
                intake.product_frontier(root)


if __name__ == '__main__':
    unittest.main()

"""Optional feature-input inspection without authoring receipts or native phase gates."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import specification_intake as intake


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.spec = self.root / 'specs/001-register/spec.md'
        self.spec.parent.mkdir(parents=True)

    def write(self, text):
        self.spec.write_text(text, encoding='utf-8')

    def complete_brief(self):
        path = intake.begin(self.root, 'FEATURE', 'Register a request', feature='register-request')
        value = intake.read(path)
        value.update({key: 'Actual synthetic ' + key for key in intake.FIELDS})
        value['decisions'] = []
        intake.atomic_write(path, value)
        return path, value

    def test_normal_spec_needs_no_roadmap_or_confirmation_metadata(self):
        self.write('# Register request\n\nA requester receives an identifier or visible rejection.\n')
        result = intake.check_spec(self.root, self.spec)
        self.assertEqual('specs/001-register/spec.md', result['spec'])
        self.assertIsNone(result['brief'])
        self.assertFalse((self.root / '.program-kit').exists())

    def test_selected_inspection_rejects_empty_or_untitled_spec(self):
        for text in ('', 'An untitled incomplete specification'):
            self.write(text)
            with self.assertRaises(ValueError):
                intake.check_spec(self.root, self.spec)

    def test_optional_readable_link_requires_actual_contained_document(self):
        note = self.root / 'docs/registration.md'
        note.parent.mkdir()
        note.write_text('# Registration\nHuman confirmation context: fictional example.\n')
        self.write('# Registration\n\n- **Intake brief**: docs/registration.md\n')
        self.assertEqual(note, intake.resolve_spec_brief(self.root, self.spec)[0])
        intake.check_spec(self.root, self.spec)
        for reference in ('../outside.md', 'docs/missing.md'):
            self.write('# Registration\n\n- **Intake brief**: ' + reference + '\n')
            with self.assertRaises(ValueError):
                intake.check_spec(self.root, self.spec)

    def test_optional_scope_checks_real_architecture_ids(self):
        model = json.loads((ROOT / 'extensions/program-kit-governance/references/architecture-map-minimal.json').read_text())
        path = self.root / 'docs/architecture/architecture-map.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(model))
        self.write('# Registration\n\n- **Architecture scope**: request-service\n')
        intake.check_spec(self.root, self.spec)
        self.write('# Registration\n\n- **Architecture scope**: invented-owner\n')
        with self.assertRaisesRegex(ValueError, 'existing canonical'):
            intake.check_spec(self.root, self.spec)

    def test_begin_preserves_answers_and_needs_no_existing_epic(self):
        path, value = self.complete_brief()
        self.assertTrue(path.is_relative_to(self.root / 'docs/architecture/feature-intake'))
        original = path.read_bytes()
        self.assertEqual(path, intake.begin(self.root, 'FEATURE', 'A changed request needs affected discussion', feature='register-request'))
        self.assertEqual(original, path.read_bytes())
        self.assertEqual([], value['decisions'])

    def test_review_is_read_only_and_not_confirmation(self):
        path, value = self.complete_brief()
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = intake.review(self.root, 'FEATURE', feature='register-request')
        self.assertIn('supplies no consent', result['review'])
        intake.check(self.root, 'FEATURE', feature='register-request')
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertNotIn('reviewHash', result)

    def test_structured_helper_still_rejects_incomplete_and_cyclic_decisions(self):
        path, value = self.complete_brief()
        value['outcome'] = ''
        with self.assertRaisesRegex(ValueError, 'outcome'):
            intake.validate_brief(value, 'FEATURE', 'register-request')
        value['outcome'] = 'A stable request identity'
        def decision(identity, dependency):
            return {'id': identity, 'question': 'Which policy?', 'answer': 'One named policy',
                    'provenance': 'Synthetic explicit decision', 'rationale': 'Ownership',
                    'disposition': 'answered', 'blocking': False, 'dependsOn': [dependency]}
        value['decisions'] = [decision('first', 'second'), decision('second', 'first')]
        with self.assertRaisesRegex(ValueError, 'cycle'):
            intake.validate_brief(value, 'FEATURE', 'register-request')

    def test_deferral_needs_owner_trigger_without_future_phase_receipt(self):
        path, value = self.complete_brief()
        decision = {'id': 'retention', 'question': 'How long?', 'answer': 'Settle with retention feature',
                    'provenance': 'Synthetic', 'rationale': 'Future policy', 'disposition': 'deferred',
                    'blocking': False, 'dependsOn': [], 'owner': 'Retention owner', 'trigger': 'When retention is selected'}
        value['decisions'] = [decision]
        intake.validate_brief(value, 'FEATURE', 'register-request')
        decision.pop('owner')
        with self.assertRaisesRegex(ValueError, 'owner'):
            intake.validate_brief(value, 'FEATURE', 'register-request')


if __name__ == '__main__':
    unittest.main()

"""Consumer quality authority and batched authoring diagnostics; no agents."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
import bootstrap_quality as quality
import bootstrap_context as context


class QualityHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pk-quality-handoff-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / quality.SOURCE).parent.mkdir(parents=True)
        (self.root / quality.SOURCE).write_text('# Scenarios\n\n- WEB-Q04 (WEB-C12): Private export contains no records.\n'
                                              '  Verify actual exported contents.\n- WEB-Q05 (WEB-C06): Device accessibility.\n', encoding='utf-8')
        (self.root / quality.TARGET).write_text('# Gates\n\nUse WEB-Q04 and WEB-Q05 at delivery.\n', encoding='utf-8')

    def test_exact_generated_mapping_preserves_every_case_and_user_prose(self):
        self.assertEqual(['WEB-Q04', 'WEB-Q05'], quality.synchronize(self.root))
        quality.validate(self.root)
        original = (self.root / quality.TARGET).read_bytes()
        quality.synchronize(self.root)
        self.assertEqual(original, (self.root / quality.TARGET).read_bytes())
        self.assertIn('Use WEB-Q04 and WEB-Q05 at delivery.', original.decode())

    def test_conflicting_or_duplicate_authored_case_is_not_silently_overwritten(self):
        path = self.root / quality.TARGET
        path.write_text('- WEB-Q04: readiness, locale and unrelated assertions\n', encoding='utf-8')
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'definitions belong only'):
            quality.synchronize(self.root)
        self.assertEqual(before, path.read_bytes())

    def test_changed_missing_and_stale_case_views_are_detected(self):
        with self.assertRaisesRegex(ValueError, 'Missing generated'):
            quality.validate(self.root)
        quality.synchronize(self.root)
        target = self.root / quality.TARGET
        target.write_text(target.read_text().replace('Device accessibility.', 'Different case.'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stale'):
            quality.validate(self.root)
        quality.synchronize(self.root)
        quality.validate(self.root)
        source = self.root / quality.SOURCE
        source.write_text('- WEB-Q04: Changed agreed scenario.\n', encoding='utf-8')
        quality.synchronize(self.root)
        quality.validate(self.root)
        self.assertNotIn('- WEB-Q05', target.read_text())

    def test_duplicate_source_ids_are_reported_before_projection(self):
        source = self.root / quality.SOURCE
        source.write_text('- WEB-Q04: one\n- WEB-Q04: another\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            quality.synchronize(self.root)

    def test_non_web_project_needs_no_web_case_artifact(self):
        (self.root / quality.SOURCE).write_text('# Local application quality\n')
        before = (self.root / quality.TARGET).read_bytes()
        quality.synchronize(self.root)
        quality.validate(self.root)
        self.assertEqual(before, (self.root / quality.TARGET).read_bytes())

    def test_all_oversized_and_missing_outputs_reported_together(self):
        for name, size in [('first.md', 12), ('second.md', 13)]:
            (self.root / name).write_text('x' * size)
        contract = {'artifact_byte_budgets': {'first.md': 10, 'second.md': 10, 'missing.md': 10},
                    'artifact_target_bytes': {'first.md': 8, 'second.md': 8, 'missing.md': 8}}
        with patch.object(context, 'governance_contract', return_value={'paths': {}}), \
                patch.object(context, 'resolved_output_contract', return_value=contract):
            with self.assertRaises(context.ContextError) as error:
                context.validate_stage_output(self.root, 'tooling')
        for name in ('first.md', 'second.md', 'missing.md'):
            self.assertIn(name, str(error.exception))


if __name__ == '__main__':
    unittest.main()

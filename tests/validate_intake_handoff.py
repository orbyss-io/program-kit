"""Synthetic handoff contract tests; no human session or paid acceptance is claimed."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from live.v2 import cli, intake_handoff, scenario, sync_stages
from live.v2.common import LiveContractError, atomic_write_json, load_object, sha256_file

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tests/live/scenarios/knowledge-application/v1/bootstrap-seed'


class IntakeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='intake-handoff-')
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)
        self.session = self.scratch / 'session'
        self.session.mkdir()
        self.output = self.scratch / 'captured'
        for name in ('speckit.program-kit-governance.bootstrap.md', 'speckit.program-kit-governance.grilling.md'):
            shutil.copyfile(ROOT / 'extensions/program-kit-governance/commands' / name, self.session / name)
        shutil.copyfile(ROOT / 'VERSION', self.session / 'VERSION')
        (self.session / 'conversation.md').write_text('Synthetic unit-test conversation, not human approval.')
        self.inputs = {p.relative_to(BASE / 'fixture').as_posix(): p.read_bytes()
                       for p in (BASE / 'fixture').rglob('*') if p.is_file()}
        self.inputs['product-idea.md'] = (BASE.parent / 'PROJECT_REQUEST.md').read_bytes()
        self.state = dict(id='12345678synthetic', status='needs-human-review', intakeStatus='valid-confirmed',
                          transcriptStatus='captured', sessionIds=['synthetic-test'], exitCode=0,
                          sourceChanges='', sourceCommit='a'*40)
        self.save_archive()
        self.git = patch.object(cli, 'git', side_effect=lambda root, *args: 'a'*40 if args == ('rev-parse', 'HEAD') else '')
        self.git.start()
        self.addCleanup(self.git.stop)

    def save_archive(self):
        with zipfile.ZipFile(self.session / 'consumer.zip', 'w') as archive:
            for name, payload in self.inputs.items():
                archive.writestr(name, payload)
        self.state['archiveSha256'] = sha256_file(self.session / 'consumer.zip')
        atomic_write_json(self.session / 'session.json', self.state)

    def capture(self):
        return intake_handoff.capture(ROOT, self.session, self.output)

    def test_native_validation_preserves_actual_bytes_and_dynamic_phase_binding(self):
        document = self.capture()
        fixture = self.output / 'fixture'
        for name in ['docs/architecture/bootstrap-intake.json', *load_object(fixture / 'docs/architecture/bootstrap-intake.json')['artifacts']]:
            if name.startswith('docs/'):
                self.assertEqual((fixture / name).read_bytes(), self.inputs[name])
        intake = load_object(fixture / 'docs/architecture/bootstrap-intake.json')
        for record in intake['artifacts'].values():
            self.assertEqual((fixture / record['path']).read_bytes(), self.inputs[record['path']])
        self.assertEqual(load_object(self.output / 'selection-template.json')['status'], 'Draft')
        self.assertFalse((fixture / '.program-kit').exists())
        self.assertIn('live-intake', document['id'])
        source = scenario.scenario_authority(self.output, ROOT / 'tests/live/schemas/v2')
        binding = sync_stages.authority(ROOT, 'fresh-candidate', self.output)
        parent = dict(phase='bootstrap-checkpoint', candidate='b'*64, scenario=source['digest'], scenarioRoot=str(self.output))
        sync_stages.validate_parent(parent, 'feature-intake', 'fresh-candidate', binding, 'b'*64, ROOT, self.output)
        with self.assertRaisesRegex(LiveContractError, 'PARENT_SCENARIO'):
            sync_stages.validate_parent(parent, 'feature-intake', 'fresh-candidate', binding, 'b'*64, ROOT)
        parent.update(phase='feature-confirmed', scenario=binding['digest'])
        sync_stages.validate_parent(parent, 'feature-planning', 'fresh-candidate', binding, 'b'*64, ROOT, self.output)
        original = fixture / 'docs/architecture/project-intent.md'
        original.write_bytes(original.read_bytes() + b'changed')
        with self.assertRaisesRegex(LiveContractError, 'COPIED_INPUT_CHANGED'):
            scenario.scenario_authority(self.output, ROOT / 'tests/live/schemas/v2')

    def test_draft_setup_failed_or_uncaptured_session_rejected_before_output(self):
        for change in (dict(status='setup-only'), dict(intakeStatus='valid-draft'), dict(exitCode=1),
                       dict(transcriptStatus='unavailable'), dict(sourceChanges=' M VERSION')):
            with self.subTest(change=change):
                atomic_write_json(self.session / 'session.json', {**self.state, **change})
                with self.assertRaises(LiveContractError):
                    self.capture()
                self.assertFalse(self.output.exists())

    def test_source_and_archive_changes_rejected(self):
        with patch.object(cli, 'git', return_value='different'):
            with self.assertRaisesRegex(LiveContractError, 'CANDIDATE'):
                self.capture()
        with (self.session / 'consumer.zip').open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(LiveContractError, 'ARCHIVE_CHANGED'):
            self.capture()

    def test_changed_product_and_fixed_contract_require_review(self):
        for name in ('product-idea.md', 'acceptance/README.md'):
            with self.subTest(name=name):
                original = self.inputs[name]
                self.inputs[name] += b'changed'
                self.save_archive()
                with self.assertRaisesRegex(LiveContractError, 'DIFFERENT_PRODUCT|ACCEPTANCE_CONTRACT'):
                    self.capture()
                self.inputs[name] = original

    def test_original_intake_hash_and_selected_decision_guard(self):
        with self.assertRaisesRegex(LiveContractError, 'SELECT_ACTUAL'):
            intake_handoff.capture(ROOT, self.session, self.output, ['invented-decision'])
        self.inputs['docs/architecture/project-intent.md'] += b'changed'
        self.save_archive()
        with self.assertRaisesRegex(LiveContractError, 'ORIGINAL_INPUT_CHANGED'):
            self.capture()

    def test_source_conversation_remains_bound_after_capture(self):
        self.capture()
        (self.session / 'conversation.md').write_text('changed')
        with self.assertRaisesRegex(LiveContractError, 'SOURCE_EVIDENCE_CHANGED'):
            intake_handoff.validate_provenance(self.output / 'fixture')


if __name__ == '__main__':
    unittest.main()

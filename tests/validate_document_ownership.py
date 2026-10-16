"""Actual reset witnesses and installed drafting preflight; synthetic consumer authority only."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / 'extensions/program-kit-governance'
sys.path.insert(0, str(GOVERNANCE / 'scripts'))
import task_draft
import retained_inputs
from owned_scratch import filesystem_path


class DocumentOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = FixtureDirectory(native=True)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.frozen = 'docs/architecture/compatibility/README.md'
        self.proposal = 'docs/architecture/compatibility/current-proposal.md'
        target = self.root / self.frozen
        target.parent.mkdir(parents=True); target.write_text('Original accepted context.\n')
        old = self.root / 'specs/old'; old.mkdir(parents=True)
        files = []
        for name in ('spec.md', 'plan.md', 'tasks.md'):
            file = old / name; file.write_text('Original unfinished ' + name)
            files.append(dict(path=file.relative_to(self.root).as_posix(), owner='specs/old', sha256=self.sha(file)))
        request = dict(feature='specs/old', reviewSource='Synthetic fixture review; no consumer authority',
                       selectionSource='Synthetic fixture selection', files=files, preserve=[self.frozen])
        original = task_draft.reset(self.root, request, apply=True)
        self.record = self.root / 'artifacts/reset/result.json'; self.record.parent.mkdir(parents=True)
        self.record.write_text(json.dumps(original, indent=2)+'\n')
        self.index = dict(schemaVersion=1, records=[dict(id='original-reset', path=self.record.relative_to(self.root).as_posix(), sha256=self.sha(self.record))],
                          protected=[dict(path=self.frozen, record='original-reset')],
                          activeDocuments=[dict(path=self.proposal, supersedes=[self.frozen])])
        self.write_index()
        self.feature = self.root / 'specs/current'; self.feature.mkdir()
        for name in ('spec.md', 'plan.md'):
            (self.feature / name).write_text('Current governed feature\n')

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_index(self):
        path = self.root / retained_inputs.INDEX; path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(self.index, indent=2)+'\n')

    def test_snapshot_binds_original_reset_and_proposal_without_modifying_either(self):
        before = {p: self.sha(self.root / p) for p in (self.frozen, 'artifacts/reset/result.json')}
        result = retained_inputs.snapshot(self.root)
        self.assertEqual(self.sha(self.root / self.frozen), result['frozen'][self.frozen]['sha256'])
        self.assertEqual([self.proposal], retained_inputs.summary(result)['activeProposals'])
        self.assertFalse(retained_inputs.summary(result)['freshProductAcceptance'])
        self.assertEqual(before, {p: self.sha(self.root / p) for p in before})

    def test_actual_drafting_rejects_frozen_output_before_saving_phase(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        tasks = self.feature / 'tasks.md'; before = tasks.read_bytes()
        body = f'## Current documentation\n- [ ] T001 Update `{self.frozen}`\n\n## Document outputs\n| Task | Path | Mode |\n| --- | --- | --- |\n| T001 | `{self.frozen}` | write |\n'
        with self.assertRaisesRegex(ValueError, 'frozen historical bytes'):
            task_draft.save_phase(self.root, self.feature, 'docs', body)
        self.assertEqual(before, tasks.read_bytes())

    def test_reference_requires_explicit_read_intent_and_new_active_target_is_allowed(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        body = f'## Current documentation\n- [ ] T001 Read `{self.frozen}` and write `{self.proposal}`\n'
        with self.assertRaisesRegex(ValueError, 'as read'):
            task_draft.save_phase(self.root, self.feature, 'docs', body)
        body += f'\n## Document outputs\n| Task | Path | Mode |\n| --- | --- | --- |\n| T001 | `{self.frozen}` | read |\n| T001 | `{self.proposal}` | write |\n'
        task_draft.save_phase(self.root, self.feature, 'docs', body)
        self.assertEqual(['docs'], task_draft.prepare(self.root, self.feature, None)['completedPhases'])
        self.assertFalse((self.root / self.proposal).exists(), 'Drafting must not implement the proposed output')

    def test_prior_completed_tasks_are_historical_not_new_mutation_authority(self):
        result = retained_inputs.validate_document_outputs(self.root, f'- [x] T001 Previously edited `{self.frozen}`\n')
        self.assertIn(self.frozen, result['frozen'])

    def test_plain_text_and_case_alias_cannot_hide_a_frozen_output(self):
        with self.assertRaisesRegex(ValueError, 'as read'):
            retained_inputs.validate_document_outputs(self.root, '- [ ] T001 Update ' + self.frozen.upper() + '\n')
        content = f'- [ ] T001 Update `{self.frozen.upper()}`\n\n## Document outputs\n| Task | Path | Mode |\n| --- | --- | --- |\n| T001 | {self.frozen.upper()} | write |\n'
        with self.assertRaisesRegex(ValueError, 'frozen historical bytes'):
            retained_inputs.validate_document_outputs(self.root, content)

    def test_changed_frozen_bytes_and_changed_original_record_fail(self):
        (self.root / self.frozen).write_text('Unexplained replacement')
        with self.assertRaisesRegex(ValueError, 'frozen historical input changed'):
            retained_inputs.snapshot(self.root)
        self.record.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'original preservation record changed'):
            retained_inputs.snapshot(self.root)

    def test_rehashed_anchor_and_payload_cannot_change_a_retained_drafting_basis(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        tasks = self.feature / 'tasks.md'; before = tasks.read_bytes()
        (self.root / self.frozen).write_text('Forged replacement')
        changed = json.loads(self.record.read_text()); changed['preserved'][self.frozen] = self.sha(self.root / self.frozen)
        self.record.write_text(json.dumps(changed)); self.index['records'][0]['sha256'] = self.sha(self.record); self.write_index()
        self.assertIn(self.frozen, retained_inputs.snapshot(self.root)['frozen'])  # A different declaration, never the old basis.
        with self.assertRaisesRegex(ValueError, 'anchor changed since drafting'):
            task_draft.acknowledge(self.root, self.feature)
        self.assertEqual(before, tasks.read_bytes())

    def test_removing_index_or_frozen_entry_does_not_unfreeze_the_prior_basis(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        self.index['protected'] = []; self.index['activeDocuments'] = []; self.write_index()
        with self.assertRaisesRegex(ValueError, 'ownership/anchor changed'):
            task_draft.acknowledge(self.root, self.feature)
        (self.root / retained_inputs.INDEX).unlink()
        with self.assertRaisesRegex(ValueError, 'ownership/anchor changed'):
            task_draft.prepare(self.root, self.feature, None)

    def test_standalone_preflight_reads_the_bound_draft_even_after_index_removal(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        content = (self.feature / 'tasks.md').read_text()
        (self.root / retained_inputs.INDEX).unlink()
        with self.assertRaisesRegex(ValueError, 'ownership/anchor changed'):
            retained_inputs.validate_document_outputs(self.root, content)

    def test_ownership_transition_uses_distinct_current_path_and_preserves_original(self):
        task_draft.prepare(self.root, self.feature, ['docs'])
        self.index['activeDocuments'].append(dict(path='docs/new-current.md', supersedes=[self.frozen])); self.write_index()
        task_draft.acknowledge(self.root, self.feature)
        self.assertIn('docs/new-current.md', task_draft.prepare(self.root, self.feature, None)['documentOwnership']['activeProposals'])
        self.index['activeDocuments'][0]['path'] = self.frozen; self.write_index()
        with self.assertRaisesRegex(ValueError, 'cannot become a mutable target'):
            retained_inputs.snapshot(self.root)

    def test_preview_and_missing_original_provenance_do_not_claim_frozen_authority(self):
        record = json.loads(self.record.read_text()); record['status'] = 'preview'; self.record.write_text(json.dumps(record))
        self.index['records'][0]['sha256'] = self.sha(self.record); self.write_index()
        with self.assertRaisesRegex(ValueError, 'executed supported'):
            retained_inputs.snapshot(self.root)

    def test_portable_aliases_traversal_duplicates_and_unknown_proposals_fail(self):
        for value in ('../outside.md', 'docs/../a.md', 'docs//a.md', 'docs\\a.md', 'docs/NUL.md', 'docs/a.md.', '/absolute.md', 'docs/*.md'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                retained_inputs.canonical(value)
        self.index['protected'].append(copy.deepcopy(self.index['protected'][0])); self.write_index()
        with self.assertRaisesRegex(ValueError, 'duplicate/aliased protected'):
            retained_inputs.snapshot(self.root)

    def test_installed_isolated_cli_inspects_and_rejects_before_phase_mutation(self):
        for name in ('program-kit-dotnet', 'program-kit-governance'):
            target = self.root / '.specify/extensions' / name
            shutil.copytree(filesystem_path(ROOT / 'extensions' / name), filesystem_path(target),
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        cli = self.root / '.specify/extensions/program-kit-governance/scripts/task_draft.py'
        # Ignore environment/user/site packages while retaining Python's normal
        # script-directory import contract for the shipped sibling loader.
        command = [sys.executable, '-E', '-s', '-S', str(cli)]
        result = subprocess.run([*command, 'prepare', '--repository', str(self.root), '--feature-dir', 'specs/current', '--phases', 'docs'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout+result.stderr)
        self.assertEqual(1, json.loads(result.stdout)['documentOwnership']['frozenInputs'])
        tasks = self.feature / 'tasks.md'; before = tasks.read_bytes()
        body = self.root / 'phase.md'; body.write_text(f'## Documentation\n- [ ] T001 Update `{self.frozen}`\n')
        result = subprocess.run([*command, 'save-phase', '--repository', str(self.root), '--feature-dir', 'specs/current',
                                 '--phase', 'docs', '--content-file', str(body)], capture_output=True, text=True, timeout=30)
        self.assertEqual(2, result.returncode, result.stdout+result.stderr)
        self.assertIn('as read', result.stdout); self.assertEqual(before, tasks.read_bytes())


if __name__ == '__main__':
    unittest.main()

"""Completed-bootstrap maintenance through real engine gates, with no coding agent."""
from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_workflow_resumption as fixture

g, life, workflow = fixture.g, fixture.life, fixture.workflow


class PostBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temp = tempfile.TemporaryDirectory(prefix='post-bootstrap-')
        self.root = Path(self.temp.name)
        os.chdir(self.root)
        self.addCleanup(self.cleanup)
        fixture.fixture.setup(self.root)
        fixture.fixture.ledger(self.root, [fixture.fixture.item()])
        self.recipe = self.root / 'docs/architecture/probe.py'
        self.recipe.write_text("import sqlite3\nfrom pathlib import Path\nc=sqlite3.connect('probe.db')\nc.execute('create table evidence(value integer)')\nc.execute('insert into evidence values(7)')\nc.commit()\nc.close()\nc=sqlite3.connect('probe.db')\nassert c.execute('select value from evidence').fetchone() == (7,)\nc.close()\nPath('compatibility-results.xml').write_text('<testsuite><testcase classname=\"Probe\" name=\"persist\"/></testsuite>')\n", encoding='utf-8')
        life.write(self.recipe.with_suffix('.contract.json'), {'schemaVersion': 1, 'checks': [
            {'id': 'persist', 'kind': 'runtime-compatibility', 'testCases': ['Probe.persist']}]})
        life.write(self.root / 'docs/architecture/bootstrap-proof-plan.json', {'schemaVersion': 1,
            'probes': [{'id': 'provider', 'recipe': 'docs/architecture/probe.py', 'timeout': 10}],
            'readyWhenProven': [{'id': 'SPEC-001', 'prerequisites': ['provider'], 'rationale': 'Complete architecture prerequisite inventory'}]})
        g.synchronize_roadmap_views()
        g.write_review('bootstrap')
        g.accept_bootstrap('approve')
        (self.root / g.READINESS_REPORT).write_text('**Status**: READY\n\nCurrent reviewed evidence agrees.\n', encoding='utf-8')
        original_shell = fixture.ShellStep.execute
        def execute(step, config, context):
            config = copy.deepcopy(config)
            config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
            return original_shell(step, config, context)
        self.shell = patch.object(fixture.ShellStep, 'execute', execute)
        self.shell.start()
        self.stdin = patch.object(sys.stdin, 'isatty', return_value=False)
        self.stdin.start()
        self.source = fixture.WorkflowEngine(self.root).execute(fixture.definition([
            fixture.shell('complete-bootstrap', fixture.FLOW + 'step complete --run-id {{ context.run_id }}')
        ]), run_id='completed-source')
        self.assertEqual(fixture.RunStatus.COMPLETED, self.source.status, self.source.error)

    def cleanup(self):
        os.chdir(self.previous)
        if hasattr(self, 'stdin'):
            self.stdin.stop()
        if hasattr(self, 'shell'):
            self.shell.stop()
        self.temp.cleanup()

    def test_completed_continuation_preserves_history_reviews_drift_and_keeps_active(self):
        run = workflow.run_directory(self.root, self.source.run_id)
        source_files = {p.relative_to(run): p.read_bytes() for p in run.rglob('*') if p.is_file()}
        old_approval = (self.root / g.BOOTSTRAP_APPROVAL).read_bytes()
        old_completion = (self.root / g.BOOTSTRAP_COMPLETION).read_bytes()
        roadmap = self.root / g.ROADMAP
        active = roadmap.read_text(encoding='utf-8').replace('**Status**: Ready', '**Status**: Active')
        oversized = '<!-- retained verbose draft ' + 'x' * 6600 + ' -->\n'
        roadmap.write_text(oversized + active, encoding='utf-8')
        receipt = life.run_proof(self.root, 'provider', 'docs/architecture/probe.py', 10)
        proof_bytes = (self.root / receipt['path']).read_bytes()
        from bootstrap_proof_plan import execute as execute_proofs
        with self.assertRaises((ValueError, OSError)):
            execute_proofs(self.root, recovery_source=self.source.run_id)
        self.assertFalse(life.phase_eligibility(self.root, g.roadmap_records(roadmap), 'SPEC-001', 'implementation')['eligible'])
        self.assertGreater(roadmap.stat().st_size, 6144)
        with self.assertRaisesRegex(ValueError, 'terminal failure'):
            workflow.recovery.prepare(self.root, self.source.run_id)
        with self.assertRaisesRegex(ValueError, 'cannot preapprove'):
            workflow.resume(self.root, self.source.run_id, {'recovery_verdict': 'approve'}, post_bootstrap=True)
        prepared = workflow.recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
        self.assertTrue(prepared['preserved'])
        directory, saved = workflow.recovery.manifest(self.root, self.source.run_id)
        self.assertTrue(saved['post_bootstrap'])
        self.assertEqual(old_completion, (directory / 'original' / saved['original'][g.BOOTSTRAP_COMPLETION.as_posix()]).read_bytes())
        self.assertFalse(workflow.source_ready(self.root, self.source.run_id))
        calls = []
        def dispatch(step, command, integration, model, args, context):
            calls.append(command)
            self.assertEqual('speckit.program-kit-governance.bootstrap-recovery', command)
            roadmap.write_text(active, encoding='utf-8')
            return {'exit_code': 0, 'stdout': 'bounded correction', 'stderr': ''}
        with patch.object(fixture.CommandStep, '_try_dispatch', dispatch):
            paused = workflow.resume(self.root, self.source.run_id, post_bootstrap=True)
            self.assertEqual(fixture.RunStatus.PAUSED, paused.status, (paused.current_step_id, paused.error))
            self.assertEqual('review-recovery', paused.current_step_id)
            self.assertEqual(old_approval, (self.root / g.BOOTSTRAP_APPROVAL).read_bytes())
            self.assertEqual(old_completion, (self.root / g.BOOTSTRAP_COMPLETION).read_bytes())
            review = life.load(directory / 'review.json')
            previous = life.load(directory / 'original' / saved['original'][g.BOOTSTRAP_APPROVAL.as_posix()])
            self.assertEqual(previous['artifacts'][g.ROADMAP.as_posix()], review['changed'][g.ROADMAP.as_posix()]['before'])
            packet = directory / 'review.md'
            original_packet = packet.read_bytes()
            packet.write_bytes(original_packet + b'\nstale edit')
            with self.assertRaisesRegex(ValueError, 'stale'):
                workflow.recovery.accept(self.root, self.source.run_id, 'approve')
            packet.write_bytes(original_packet)
            done = workflow.resume(self.root, self.source.run_id, {'recovery_verdict': 'approve'})
            self.assertEqual(fixture.RunStatus.COMPLETED, done.status, (done.current_step_id, done.error))
            self.assertEqual(1, len(calls))
        self.assertIn('**Status**: Active', roadmap.read_text(encoding='utf-8'))
        self.assertEqual(proof_bytes, (self.root / receipt['path']).read_bytes())
        self.assertEqual(1, len(list(self.root.rglob('proof.json'))))
        self.assertTrue(life.phase_eligibility(self.root, g.roadmap_records(roadmap), 'SPEC-001', 'implementation')['eligible'])
        workflow.validate_engine_completion(self.root)
        g.validate_completion()
        self.assertEqual(source_files, {p.relative_to(run): p.read_bytes() for p in run.rglob('*') if p.is_file()})
        self.assertEqual(old_approval, (directory / 'original' / saved['original'][g.BOOTSTRAP_APPROVAL.as_posix()]).read_bytes())
        self.assertEqual(old_completion, (directory / 'original' / saved['original'][g.BOOTSTRAP_COMPLETION.as_posix()]).read_bytes())
        self.assertEqual(done.run_id, workflow.resume(self.root, self.source.run_id).run_id)
        # A second linked review can renew changed executable inputs while
        # preserving the first receipt and the Active feature. Standalone renewal
        # must continue to reject mutation of accepted compatibility authority.
        self.recipe.write_bytes(self.recipe.read_bytes() + b'\n# reviewed recipe repair\n')
        with self.assertRaisesRegex(ValueError, 'reopen the architecture review'):
            execute_proofs(self.root)
        with patch.object(fixture.CommandStep, '_try_dispatch', dispatch):
            second = workflow.resume(self.root, done.run_id, post_bootstrap=True)
            self.assertEqual(fixture.RunStatus.PAUSED, second.status, (second.current_step_id, second.error))
            renewed = workflow.resume(self.root, done.run_id, {'recovery_verdict': 'approve'})
            self.assertEqual(fixture.RunStatus.COMPLETED, renewed.status, (renewed.current_step_id, renewed.error, renewed.step_results.get(renewed.current_step_id)))
        self.assertEqual(proof_bytes, (self.root / receipt['path']).read_bytes())
        self.assertEqual(2, len(list(self.root.rglob('proof.json'))))
        self.assertIn('**Status**: Active', roadmap.read_text(encoding='utf-8'))
        g.validate_completion()

    def test_completed_preparation_rejects_broken_completion_and_accepted_adr_drift(self):
        path = self.root / g.BOOTSTRAP_COMPLETION
        original = path.read_bytes()
        value = life.load(path)
        value['bootstrap_approval_sha256'] = '0' * 64
        life.write(path, value)
        with self.assertRaisesRegex(ValueError, 'intact bound completion'):
            workflow.recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
        path.write_bytes(original)
        approval = life.load(self.root / g.BOOTSTRAP_APPROVAL)
        adr = self.root / approval['accepted_founding_adrs'][0]['path']
        adr.write_bytes(adr.read_bytes() + b'\nunauthorized decision change')
        with self.assertRaisesRegex(ValueError, 'changed'):
            workflow.recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
        self.assertFalse(workflow.recovery.location(self.root, self.source.run_id).exists())


if __name__ == '__main__':
    unittest.main()

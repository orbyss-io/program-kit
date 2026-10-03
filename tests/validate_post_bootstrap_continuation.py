"""Completed-bootstrap maintenance through real engine gates, with no coding agent."""
from __future__ import annotations

import copy
import os
import subprocess
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

    def preserve_git_history(self):
        command = ['git', '-c', f'safe.directory={self.root}', '-c', 'core.excludesFile=',
                   '-c', 'core.autocrlf=false', '-c', 'core.attributesFile=',
                   '-c', 'user.name=Continuation fixture', '-c', 'user.email=fixture@example.invalid',
                   '-c', 'commit.gpgsign=false', '-c', f'core.hooksPath={self.root / "no-hooks"}']
        subprocess.run([*command, 'init', '--quiet'], cwd=self.root, check=True, capture_output=True)
        (self.root / '.gitattributes').write_text('* -text\n', encoding='utf-8')
        subprocess.run([*command, 'add', '--force', '--', '.gitattributes',
                        g.CONSTITUTION.as_posix(), g.READINESS_REPORT.as_posix()],
                       cwd=self.root, check=True, capture_output=True)
        subprocess.run([*command, 'commit', '--quiet', '-m', 'Preserve actual completed-bootstrap bytes'],
                       cwd=self.root, check=True, capture_output=True)

    def amend_constitution(self):
        g.begin()
        path = self.root / g.CONSTITUTION
        text = path.read_text(encoding='utf-8').replace('**Version**: 1.0.0', '**Version**: 2.0.0')
        text = text.replace('**Status**: Ratified', '**Status**: Draft')
        path.write_text(text + '\nRatified amendment: keep consumer decisions explicit.\n', encoding='utf-8', newline='\n')
        g.write_review('constitution')
        g.ratify('ratify')
        self.assertEqual('2.0.0', g.validate_ratification()['constitution']['version'])

    def test_legitimate_amendment_and_regenerated_report_complete_with_original_bindings(self):
        original_constitution = (self.root / g.CONSTITUTION).read_bytes()
        original_report = (self.root / g.READINESS_REPORT).read_bytes()
        self.preserve_git_history()
        self.amend_constitution()
        current_constitution = (self.root / g.CONSTITUTION).read_bytes()
        g.render_readiness()
        self.assertNotEqual(original_report, (self.root / g.READINESS_REPORT).read_bytes())
        self.test_completed_continuation_preserves_history_reviews_drift_and_keeps_active()
        directory, saved = workflow.recovery.manifest(self.root, self.source.run_id)
        for name, payload in (('constitution', original_constitution), ('readiness_report', original_report)):
            bound = saved['historical_completion'][name]
            self.assertEqual('git', bound['source']['kind'])
            self.assertEqual(payload, (directory / 'original' / bound['sha256']).read_bytes())
        self.assertEqual(current_constitution, (self.root / g.CONSTITUTION).read_bytes())
        completion = life.load(self.root / g.BOOTSTRAP_COMPLETION)
        self.assertEqual(life.digest(self.root / g.CONSTITUTION), completion['constitution_sha256'])
        self.assertEqual(life.digest(self.root / g.READINESS_REPORT), completion['readiness_report']['sha256'])
        review = life.load(directory / 'review.json')
        self.assertEqual(life.digest(self.root / g.CONSTITUTION), review['current_authority']['constitution'])
        historical = directory / 'original' / saved['historical_completion']['constitution']['sha256']
        historical.write_bytes(original_constitution + b'\nchanged historical evidence')
        with self.assertRaisesRegex(ValueError, 'Preserved recovery authority/evidence changed'):
            workflow.recovery.manifest(self.root, self.source.run_id)

    def test_evolution_requires_valid_current_ratification_and_recoverable_history(self):
        self.preserve_git_history()
        self.amend_constitution()
        g.render_readiness()
        constitution = self.root / g.CONSTITUTION
        ratified = constitution.read_bytes()
        constitution.write_bytes(ratified + b'\nunratified change')
        with self.assertRaisesRegex(ValueError, 'changed after ratification'):
            workflow.recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
        constitution.write_bytes(ratified)
        completion = self.root / g.BOOTSTRAP_COMPLETION
        preserved = completion.read_bytes()
        for name in ('constitution', 'readiness_report'):
            value = life.load(completion)
            if name == 'constitution':
                value['constitution_sha256'] = '0' * 64
            else:
                value['readiness_report']['sha256'] = '0' * 64
            life.write(completion, value)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Historical completion binding is not recoverable'):
                workflow.recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
            completion.write_bytes(preserved)
        self.assertFalse(workflow.recovery.location(self.root, self.source.run_id).exists())

    def test_archived_binding_requires_matching_bytes_and_no_git_history(self):
        relative = g.READINESS_REPORT.as_posix()
        expected = life.digest(self.root / g.READINESS_REPORT)
        payload = (self.root / g.READINESS_REPORT).read_bytes()
        archive = self.root / '.specify/governance/bootstrap-recovery/earlier/original' / expected
        archive.parent.mkdir(parents=True)
        archive.write_bytes(payload)
        (self.root / g.READINESS_REPORT).write_bytes(b'current generated output')
        with patch.object(workflow.recovery.subprocess, 'run', side_effect=AssertionError('Git must not be needed for valid archived bytes')):
            recovered, source = workflow.recovery.historical_binding(self.root, relative, expected)
        self.assertEqual(payload, recovered)
        self.assertEqual('recovery-archive', source['kind'])
        archive.write_bytes(b'false bytes under a true hash filename')
        with self.assertRaisesRegex(ValueError, 'not recoverable'):
            workflow.recovery.historical_binding(self.root, relative, expected)

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


    def producer_budget_retry(self, *, historical=False):
        import bootstrap_context
        architecture = self.root / 'docs/architecture/architecture.md'
        original = architecture.read_bytes()
        paths = bootstrap_context.governance_contract(self.root)['paths']
        sizes = bootstrap_context.artifact_sizes(self.root, architecture.relative_to(self.root).as_posix(), paths)
        # Physical UTF-8 bytes matter. Retain the real canonical generated blocks,
        # rather than inventing an exempt marker or a counter stub.
        padding = 11166 - sizes['authored_bytes'] - len(b'\n<!--  -->\n') - len('é'.encode('utf-8'))
        self.assertGreater(padding, 0)
        oversized = original + b'\n<!-- ' + 'é'.encode('utf-8') + b'x' * padding + b' -->\n'
        approval = (self.root / g.BOOTSTRAP_APPROVAL).read_bytes()
        ratification = (self.root / g.RATIFICATION).read_bytes()
        source_dir = workflow.run_directory(self.root, self.source.run_id)
        source_files = {p.relative_to(source_dir): p.read_bytes() for p in source_dir.rglob('*') if p.is_file()}
        definition = workflow.continuation_definition(self.root)
        if historical:
            data = copy.deepcopy(definition.data)
            for step in data['steps']:
                if step['id'] == 'route-recovery-synchronization':
                    step['cases'][False] = [s for s in step['cases'][False]
                                            if s['id'] != 'validate-recovery-producer-output']
            definition = fixture.WorkflowDefinition(data)
        calls, proof_steps = [], []
        original_execute = fixture.ShellStep.execute
        def execute(step, config, context):
            if config['id'] == 'recovery-execute-compatibility-proofs':
                proof_steps.append(config['id'])
            return original_execute(step, config, context)
        def dispatch(*args, **kwargs):
            calls.append('producer')
            architecture.write_bytes(oversized if len(calls) == 1 else original)
            return {'exit_code': 0, 'stdout': 'producer ended normally', 'stderr': ''}
        with patch.object(workflow, 'continuation_definition', return_value=definition), \
                patch.object(fixture.CommandStep, '_try_dispatch', dispatch), \
                patch.object(fixture.ShellStep, 'execute', execute):
            failed = workflow.resume(self.root, self.source.run_id, post_bootstrap=True)
            self.assertEqual(fixture.RunStatus.FAILED, failed.status)
            self.assertEqual('recovery-execute-compatibility-proofs' if historical else
                             'validate-recovery-producer-output', failed.current_step_id)
            diagnostics = str(failed.step_results[failed.current_step_id])
            for expected in ('RECOVERY_PRODUCER_OUTPUT', 'docs/architecture/architecture.md',
                             '11166 authored bytes', 'hard limit 10240',
                             f"{sizes['generated_bytes']} generated bytes"):
                self.assertIn(expected, diagnostics)
            self.assertEqual(oversized, architecture.read_bytes())
            self.assertEqual(0 if not historical else 1, len(proof_steps))
            self.assertFalse(list(self.root.rglob('proof.json')))
            self.assertNotIn('recovery-synchronize', failed.step_results)
            self.assertNotIn('review-recovery', failed.step_results)
            self.assertEqual(approval, (self.root / g.BOOTSTRAP_APPROVAL).read_bytes())
            child_dir = workflow.run_directory(self.root, failed.run_id)
            failed_state = (child_dir / 'state.json').read_bytes()
            saved_definition = (child_dir / 'workflow.yml').read_bytes()
            with self.assertRaisesRegex(ValueError, 'only at the actual paused review gate'):
                workflow.resume(self.root, failed.run_id, {'recovery_verdict': 'approve'})
            self.assertEqual(failed_state, (child_dir / 'state.json').read_bytes())
            repaired = workflow.resume(self.root, failed.run_id)
            self.assertEqual(fixture.RunStatus.PAUSED, repaired.status, repaired.error)
            self.assertEqual('review-recovery', repaired.current_step_id)
            self.assertEqual(2, len(calls))
            self.assertEqual(1 if not historical else 2, len(proof_steps))
            self.assertEqual(original, architecture.read_bytes())
            self.assertEqual(saved_definition, (child_dir / 'workflow.yml').read_bytes())
            archives = self.root / '.specify/workflows/resumption-history' / failed.run_id
            self.assertTrue(any(p.read_bytes() == failed_state for p in archives.glob('*/state.json')))
            self.assertTrue(any(p.read_bytes() == oversized for p in archives.glob('*/*') if p.is_file()))
            self.assertEqual(approval, (self.root / g.BOOTSTRAP_APPROVAL).read_bytes())
            self.assertEqual(ratification, (self.root / g.RATIFICATION).read_bytes())
            self.assertEqual(source_files, {p.relative_to(source_dir): p.read_bytes()
                                           for p in source_dir.rglob('*') if p.is_file()})

    def test_oversized_producer_stops_before_proofs_and_resumes_bounded_correction(self):
        self.producer_budget_retry()

    def test_saved_continuation_enforces_sizing_without_rewriting_definition(self):
        self.producer_budget_retry(historical=True)

    def test_current_handoff_budgets_and_generated_accounting_are_read_only(self):
        import bootstrap_context
        recovery = workflow.recovery
        recovery.prepare(self.root, self.source.run_id, post_bootstrap=True)
        handoff = (recovery.location(self.root, self.source.run_id) / 'handoff.md').read_text(encoding='utf-8')
        report = recovery.validate_output(self.root, self.source.run_id)
        self.assertEqual('Validated', report['status'])
        for item in report['artifacts']:
            self.assertIn(f"| {item['path']} | {item['target_bytes']} | {item['budget_bytes']} |", handoff)
        architecture = self.root / 'docs/architecture/architecture.md'
        original = architecture.read_bytes()
        paths = bootstrap_context.governance_contract(self.root)['paths']
        sizes = bootstrap_context.artifact_sizes(self.root, 'docs/architecture/architecture.md', paths)
        self.assertGreater(sizes['generated_bytes'], 0)
        start, end = b'<!-- PROGRAM-KIT:LIFECYCLE:START -->', b'<!-- PROGRAM-KIT:LIFECYCLE:END -->'
        block_start, block_end = original.index(start), original.index(end) + len(end)
        generated = original[block_start:block_end]
        architecture.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'required corrective output is missing or empty'):
            recovery.validate_output(self.root, self.source.run_id)
        self.assertEqual(b'', architecture.read_bytes())
        architecture.write_bytes(original[:block_start] + original[block_end:]
                                 + b'\n<!-- PROGRAM-KIT:LIFECYCLE:START -->\n' + b'x' * 12000
                                 + b'\n<!-- PROGRAM-KIT:LIFECYCLE:END -->')
        before = architecture.read_bytes()
        with self.assertRaisesRegex(ValueError, 'hard limit 10240'):
            recovery.validate_output(self.root, self.source.run_id)
        self.assertEqual(before, architecture.read_bytes())
        architecture.write_bytes(original)
        self.assertIn(generated, architecture.read_bytes())
        # Above-target output within the unchanged hard budget remains acceptable.
        target_size = 9569
        padding = target_size - sizes['authored_bytes'] - len(b'\n<!--  -->\n')
        architecture.write_bytes(original + b'\n<!-- ' + b'x' * padding + b' -->\n')
        item = next(i for i in recovery.validate_output(self.root, self.source.run_id)['artifacts']
                    if i['path'] == 'docs/architecture/architecture.md')
        self.assertEqual(target_size, item['authored_bytes'])
        self.assertEqual(sizes['generated_bytes'], item['generated_bytes'])
        self.assertIn(generated, architecture.read_bytes())
        constitution = self.root / g.CONSTITUTION
        constitution.write_bytes(constitution.read_bytes() + b'\nunratified edit')
        with self.assertRaisesRegex(ValueError, 'Preserved recovery authority/evidence changed'):
            recovery.validate_output(self.root, self.source.run_id)


if __name__ == '__main__':
    unittest.main()

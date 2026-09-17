"""Phase-local eligibility with incomplete knowledge; real validators, no coding agents."""
import copy
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import validate_bootstrap_lifecycle as fixture
import bootstrap_handoff as handoff
import bootstrap_proof_plan as proofs
import specification_intake as intake
import phase_obligations as phases
import workflow_lifecycle as workflow

G, L = fixture.governance, fixture.lifecycle

class PhaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd()
        self.temp = tempfile.TemporaryDirectory(prefix='pk-phase-readiness-')
        self.root = Path(self.temp.name)
        os.chdir(self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, self.old)
        with contextlib.redirect_stdout(io.StringIO()):
            fixture.setup(self.root)
        self.run = self.root / '.specify/workflows/runs/trial'
        L.write(self.run / 'inputs.json', {'inputs': {}})

    def baseline(self, items=(), status='Ready'):
        fixture.ledger(self.root, list(items))
        p = self.root / G.ROADMAP
        p.write_text(p.read_text().replace('**Status**: Ready', '**Status**: ' + status))
        with contextlib.redirect_stdout(io.StringIO()):
            G.synchronize_roadmap_views()
            G.write_review('bootstrap')
            G.accept_bootstrap('approve')
        result = G.render_readiness('trial')
        return result

    def eligibility(self, phase):
        return L.phase_eligibility(self.root, G.roadmap_records(self.root / G.ROADMAP), 'SPEC-001', phase)

    def test_missing_provider_proof_initializes_but_blocks_implementation(self):
        result = self.baseline([fixture.item()])
        self.assertEqual('INITIALIZED', result['status'])
        self.assertTrue(result['eligible'])
        self.assertTrue(self.eligibility('specification')['eligible'])
        self.assertTrue(self.eligibility('planning')['eligible'])
        self.assertFalse(self.eligibility('implementation')['eligible'])
        # An intake answer cannot waive a still-open proof obligation.
        L.write(self.root / '.specify/feature.json', {'roadmap_entry_id': 'SPEC-001'})
        L.write(self.root / '.program-kit/specification-intake/SPEC-001/brief.json', {'decisions': []})
        with self.assertRaisesRegex(ValueError, 'provider'):
            phases.deferred(self.root, 'implementation')

    def test_all_candidates_can_initialize_without_a_ready_slice(self):
        result = self.baseline([fixture.item(trigger='before-specification')], 'Candidate')
        self.assertTrue(result['eligible'])
        self.assertFalse(self.eligibility('specification')['eligible'])
        self.assertIn('needs resolution', (self.root / G.READINESS_REPORT).read_text())

    def test_incomplete_journey_remains_honest_discovery(self):
        model = L.load(self.root / G.ARCHITECTURE_MAP)
        journey = model['strategic_model']['journeys'][0]
        journey.update(status='proposed', discovery=['clarify-journey-boundary'], view='', steps=[])
        L.write(self.root / G.ARCHITECTURE_MAP, model)
        G.write_text(self.root / G.WORKSPACE_DSL, G._load_architecture_module().StructurizrDslExporter().export(model))
        result = self.baseline([fixture.item('clarify-journey-boundary', trigger='before-specification')], 'Candidate')
        self.assertTrue(result['eligible'])
        self.assertEqual([], L.load(self.root / G.ARCHITECTURE_MAP)['strategic_model']['journeys'][0]['steps'])
        self.assertFalse(self.eligibility('specification')['eligible'])

    def test_unknown_answer_is_preserved_and_carried_without_fabrication(self):
        q = {'id': 'retention', 'question': 'How long should history remain?', 'kind': 'user-answer',
             'owner': 'Consumer', 'due_stage': 'research', 'recommendation': 'Resolve before production'}
        L.write(self.run / 'decision-questions.json', {'questions': [q]})
        self.assertEqual('complete', handoff.check(self.root, 'trial', 'research', questions_only=True)['status'])
        handoff.defer(self.root, 'trial', 'retention', ['SPEC-001'], 'production', 'Not used by the first local journey')
        items = L.load(self.root / L.LEDGER)['prerequisites']
        result = self.baseline(items)
        self.assertTrue(result['eligible'])
        self.assertIsNone(handoff.projection(self.root, 'trial')[0]['answer'])
        self.assertTrue(self.eligibility('implementation')['eligible'])
        self.assertFalse(self.eligibility('production')['eligible'])

    def test_carry_forward_reuses_existing_compatibility_obligation(self):
        q = {'id': 'provider', 'question': 'Prove the provider', 'kind': 'design-decision',
             'owner': 'Architecture maintainer', 'due_stage': 'research'}
        L.write(self.run / 'decision-questions.json', {'questions': [q]})
        fixture.ledger(self.root, [fixture.item()])
        for _ in range(2):
            handoff.defer(self.root, 'trial', 'provider', ['SPEC-001'], 'implementation', 'Before dependent code')
        items = L.load(self.root / L.LEDGER)['prerequisites']
        self.assertEqual(1, len(items))
        self.assertEqual('architecture', items[0]['disposition'])
        self.assertNotEqual('decision', items[0].get('verification'))
        self.assertEqual([], handoff.untracked_questions(self.root, 'trial'))

    def test_changed_question_cannot_reuse_old_carry_forward(self):
        q = {'id': 'retention', 'question': 'Which retention?', 'kind': 'user-answer', 'owner': 'Consumer', 'due_stage': 'research'}
        L.write(self.run / 'decision-questions.json', {'questions': [q]})
        handoff.defer(self.root, 'trial', 'retention', ['SPEC-001'], 'production', 'Before operation')
        q['question'] = 'Changed consequential meaning'
        L.write(self.run / 'decision-questions.json', {'questions': [q]})
        self.assertEqual(['retention'], [q['id'] for q in handoff.untracked_questions(self.root, 'trial')])

    def test_conflicting_artifacts_cannot_be_deferred(self):
        q = {'id': 'conflict', 'question': 'Two meanings for WEB-Q01', 'kind': 'artifact-conflict',
             'owner': 'Tooling', 'due_stage': 'tooling', 'recommendation': 'Correct the conflicting mapping'}
        L.write(self.run / 'decision-questions.json', {'questions': [q]})
        with self.assertRaisesRegex(ValueError, 'needs-design-decision'):
            handoff.require(self.root, 'trial', 'closure', questions_only=True)
        with self.assertRaisesRegex(ValueError, 'repair artifact conflicts'):
            handoff.defer(self.root, 'trial', 'conflict', ['SPEC-001'], 'production', 'Not allowed')

    def test_empty_proof_plan_is_valid_with_owned_unknowns(self):
        fixture.ledger(self.root, [fixture.item()])
        L.write(self.root / proofs.PLAN, {'schemaVersion': 1, 'probes': [], 'readyWhenProven': []})
        self.assertEqual([], proofs.execute(self.root))
        self.assertEqual('open', L.load(self.root / L.LEDGER)['prerequisites'][0]['status'])

    def test_native_terminal_completes_with_no_ready_entry(self):
        self.baseline([fixture.item(trigger='before-specification')], 'Candidate')
        import yaml
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.steps.command import CommandStep
        from specify_cli.workflows.steps.shell import ShellStep
        import sys
        shipped = yaml.safe_load((fixture.ROOT / 'workflows/program-kit-bootstrap/workflow.yml').read_text())
        steps = [copy.deepcopy(s) for s in shipped['steps'] if s['id'] in {'readiness', 'require-readiness', 'complete-bootstrap'}]
        definition = WorkflowDefinition({'workflow': shipped['workflow'], 'steps': steps})
        original = ShellStep.execute
        def execute(instance, config, context):
            config = copy.deepcopy(config)
            config['run'] = config['run'].replace('python ', f'"{sys.executable}" ', 1)
            return original(instance, config, context)
        with patch.object(CommandStep, '_try_dispatch', side_effect=AssertionError('No agent dispatch')):
            with patch.object(ShellStep, 'execute', execute):
                state = WorkflowEngine(self.root).execute(definition, run_id='incomplete-terminal')
        self.assertEqual('completed', state.status.value, state.error)
        G.validate_completion()
        workflow.validate_engine_completion(self.root)
        self.assertFalse(self.eligibility('specification')['eligible'])

    def test_failed_compatibility_is_retained_without_claiming_proof(self):
        fixture.ledger(self.root, [fixture.item()])
        recipe = self.root / 'docs/architecture/compatibility/negative.py'
        recipe.parent.mkdir(parents=True)
        recipe.write_text("from pathlib import Path\nPath('compatibility-results.xml').write_text('<testsuite><testcase classname=\"Provider\" name=\"write\"><failure message=\"unsupported\"/></testcase></testsuite>')\nraise SystemExit(1)\n")
        L.write(recipe.with_suffix('.contract.json'), {'schemaVersion': 1, 'result': 'compatibility-results.xml',
                'checks': [{'id': 'write', 'kind': 'runtime-compatibility', 'testCases': ['Provider.write']}]})
        L.write(self.root / proofs.PLAN, {'schemaVersion': 1,
                'probes': [{'id': 'provider', 'recipe': recipe.relative_to(self.root).as_posix(), 'timeout': 10}], 'readyWhenProven': []})
        results = proofs.execute(self.root)
        self.assertEqual(1, results[0]['exit_code'])
        self.assertTrue((self.root / results[0]['path']).is_file())
        item = L.load(self.root / L.LEDGER)['prerequisites'][0]
        self.assertEqual('open', item['status'])
        self.assertEqual([], item['evidence'])
        self.assertTrue(self.baseline([item])['eligible'])
        self.assertFalse(self.eligibility('implementation')['eligible'])

    def test_native_handoff_pause_does_not_reclassify_a_script_crash(self):
        from types import SimpleNamespace
        q = {'id': 'conflict', 'kind': 'artifact-conflict'}
        L.write(self.run / 'handoff-closure.json', {'stage': 'closure', 'status': 'needs-design-decision', 'questions': [q]})
        events = []
        state = SimpleNamespace(run_id='trial', current_step_id='require-closure-answers',
                                status=workflow.RunStatus.FAILED, error='exit 1', append_log=events.append, save=lambda: None,
                                step_results={'require-closure-answers': {'output': {'stderr': 'needs-design-decision: closure output is incomplete'}}})
        workflow.normalize_handoff_pause(self.root, state)
        self.assertEqual(workflow.RunStatus.PAUSED, state.status)
        self.assertIsNone(state.error)
        state.status = workflow.RunStatus.FAILED
        state.current_step_id = 'execute-compatibility-proofs'
        workflow.normalize_handoff_pause(self.root, state)
        self.assertEqual(workflow.RunStatus.FAILED, state.status)

    def test_decision_closure_cannot_use_an_arbitrary_note(self):
        note = self.root / 'docs/architecture/unreviewed-note.md'
        note.write_text('Assume the decision is solved')
        item = fixture.item('consumer-provider')
        item.update(verification='decision', status='closed', evidence=[{
            'path': note.relative_to(self.root).as_posix(), 'sha256': L.source_digest(note), 'kind': 'decision'}])
        fixture.ledger(self.root, [item])
        with self.assertRaisesRegex(ValueError, 'governed ADR evidence'):
            self.eligibility('implementation')

    def test_real_integrity_failure_is_not_initialized(self):
        self.baseline()
        (self.root / G.CONSTITUTION).write_text('Changed without ratification')
        result = G.render_readiness('trial')
        self.assertFalse(result['eligible'])
        self.assertFalse(result['authority_valid'])

    def test_delivery_execution_does_not_gate_planning_or_accept_an_answer(self):
        item = fixture.item('device-proof', disposition='feature', trigger='delivery')
        self.baseline([item])
        self.assertTrue(self.eligibility('planning')['eligible'])
        self.assertTrue(self.eligibility('implementation')['eligible'])
        self.assertFalse(self.eligibility('delivery')['eligible'])
        L.write(self.root / '.program-kit/specification-intake/SPEC-001/brief.json',
                {'decisions': [{'bootstrapPrerequisite': 'device-proof', 'disposition': 'answered'}]})
        with patch.object(intake, 'check', return_value={}):
            self.assertFalse(self.eligibility('delivery')['eligible'])
        with self.assertRaisesRegex(ValueError, 'executed evidence'):
            intake.require_bootstrap_carryover({'decisions': [
                {'bootstrapPrerequisite': 'device-proof', 'disposition': 'answered'}]},
                intake.bootstrap_obligations(self.root, 'SPEC-001'))

    def test_execution_cannot_be_assigned_to_planning(self):
        item = fixture.item('delivery', disposition='feature', trigger='feature-plan')
        item['verification'] = 'compatibility'
        fixture.ledger(self.root, [item])
        with self.assertRaisesRegex(ValueError, 'not executed proof'):
            self.eligibility('planning')

    def test_explicit_late_consumer_decision_remains_a_valid_deferral(self):
        item = fixture.item('release-choice', disposition='feature', trigger='delivery')
        item.update(verification='decision', task='Consumer chooses the release audience')
        self.assertTrue(self.baseline([item])['eligible'])
        self.assertTrue(self.eligibility('implementation')['eligible'])
        self.assertFalse(self.eligibility('delivery')['eligible'])

    def test_native_delivery_receipt_satisfies_gate_without_mutating_approved_ledger(self):
        item = fixture.item('device-proof', disposition='feature', trigger='delivery')
        self.baseline([item])
        ledger = (self.root / L.LEDGER).read_bytes()
        approval = (self.root / G.BOOTSTRAP_APPROVAL).read_bytes()
        recipe = self.root / 'docs/architecture/delivery-test.py'
        recipe.write_text("from pathlib import Path\nPath('compatibility-results.xml').write_text('<testsuite><testcase classname=\"Delivery\" name=\"behavior\"/></testsuite>')\n")
        L.write(recipe.with_suffix('.contract.json'), {'schemaVersion': 1, 'result': 'compatibility-results.xml',
                'checks': [{'id': 'behavior', 'kind': 'runtime-compatibility', 'testCases': ['Delivery.behavior']}]})
        result = L.run_proof(self.root, item['id'], recipe.relative_to(self.root).as_posix(), 10)
        self.assertEqual(0, result['exit_code'])
        self.assertTrue(self.eligibility('delivery')['eligible'])
        # A still-deferred brief does not block again after valid native proof.
        L.write(self.root / '.specify/feature.json', {'roadmap_entry_id': 'SPEC-001'})
        L.write(self.root / '.program-kit/specification-intake/SPEC-001/brief.json', {'decisions': [
            {'id': 'device', 'bootstrapPrerequisite': 'device-proof', 'disposition': 'deferred', 'duePhase': 'delivery'}]})
        phases.deferred(self.root, 'delivery')
        self.assertEqual(ledger, (self.root / L.LEDGER).read_bytes())
        self.assertEqual(approval, (self.root / G.BOOTSTRAP_APPROVAL).read_bytes())
        # Changed source revokes the receipt; a later failed attempt cannot reuse it.
        recipe.write_text(recipe.read_text() + '\nraise SystemExit(1)\n')
        self.assertFalse(self.eligibility('delivery')['eligible'])
        L.run_proof(self.root, item['id'], recipe.relative_to(self.root).as_posix(), 10)
        self.assertFalse(self.eligibility('delivery')['eligible'])

if __name__ == '__main__':
    unittest.main()

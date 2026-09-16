"""Deterministic default/decision/maintained-recipe integration; no coding agents."""
import copy
import json
import sys
import tempfile
import unittest
import importlib.util
import os
import shutil
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from bootstrap_defaults import resolve
import bootstrap_handoff as handoff
import managed_compatibility as managed
import architecture_map as architecture
from bootstrap_lifecycle import validate_recipe, load, write


class DefaultAndHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.intake = {'routing': {'languages': [], 'capabilities': ['authenticated-browser-bff']},
                       'journeys': [{'id': 'shopping'}, {'id': 'history'}]}
        self.register = resolve(self.intake, {'first_slice': {'journey_ids': ['shopping'], 'outcome': 'Remember needed items', 'rationale': 'Useful before purchase history'}})
        write(self.root / 'docs/architecture/bootstrap-intake.json', self.intake)
        write(self.root / handoff.REGISTER, self.register)
        self.directory = self.root / '.specify/workflows/runs/trial'
        write(self.directory / 'inputs.json', {'inputs': {}})

    def test_no_selection_closes_language_host_auth_and_persistence_defaults(self):
        original = copy.deepcopy(self.intake)
        value = resolve(self.intake, {'web': {'browser_ui': True}, 'persistence': [{'owner': 'list', 'storage': 'server-relational', 'profile': 'auto', 'status': 'proposed'}]})
        self.assertEqual('Orbyss.Foundation.Host', value['dotnet']['host_runtime'])
        self.assertEqual('bff-cookie-v1', value['web']['secure_profile'])
        self.assertEqual('keycloak', value['identity']['provider'])
        self.assertEqual('ef-postgresql', value['persistence'][0]['profile'])
        self.assertEqual('proposed', value['persistence'][0]['status'])
        self.assertEqual(value, resolve(self.intake, value))
        self.assertEqual(original, self.intake)

    def test_explicit_anonymous_and_provider_survive(self):
        explicit = {'web': {'browser_ui': True, 'secure_profile': 'none-v1', 'profile_source': 'explicit-intake'}, 'selected_profiles': ['browser-web']}
        value = resolve(self.intake, explicit)
        self.assertNotIn('dotnet', value['selected_profiles'])
        self.assertNotIn('identity', value)
        original = copy.deepcopy(self.register)
        original['identity'] = {'provider': 'consumer-oidc', 'source': 'explicit-intake', 'scope': 'consumer-service', 'production_trigger': 'already-owned'}
        original['persistence'] = [{'owner': 'list', 'storage': 'custom', 'profile': 'custom', 'status': 'proposed'}]
        self.assertEqual(original, resolve(self.intake, original))

    def test_explicit_stack_conflict_is_preserved_and_early(self):
        self.intake['routing']['languages'] = ['Python']
        with self.assertRaisesRegex(ValueError, 'DEFAULT-CONFLICT'):
            resolve(self.intake, {'web': {'browser_ui': True}})
        self.assertEqual(['Python'], self.intake['routing']['languages'])

    def test_default_does_not_mask_unsupported_host(self):
        self.register['dotnet']['program_kit_host_opt_out'] = True
        write(self.root / handoff.REGISTER, self.register)
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED-ADAPTER'):
            handoff.check(self.root, 'trial', 'research')

    def test_required_answer_blocks_but_future_question_does_not(self):
        question = {'id': 'region', 'question': 'Which required hosting region?', 'blocks': 'provider choice',
                    'kind': 'user-answer', 'owner': 'consumer', 'due_stage': 'research', 'recommendation': 'Use the existing region constraint'}
        self.register['unresolved'] = [question]
        write(self.root / handoff.REGISTER, self.register)
        with self.assertRaisesRegex(ValueError, 'needs-user-answer'):
            handoff.require(self.root, 'trial', 'research')
        write(self.directory / 'decision-responses.json', {'region': {'question_sha256': handoff.fingerprint(question), 'answer': 'EU'}})
        self.assertEqual('complete', handoff.require(self.root, 'trial', 'research')['status'])
        question['question'] = 'Changed question must invalidate the old answer'
        write(self.root / handoff.REGISTER, self.register)
        self.assertEqual('needs-user-answer', handoff.check(self.root, 'trial', 'research')['status'])
        question['due_stage'] = 'production'
        write(self.root / handoff.REGISTER, self.register)
        self.assertEqual('complete', handoff.check(self.root, 'trial', 'research')['status'])

    def test_design_owner_gets_its_stage_before_exit_is_enforced(self):
        self.register['unresolved'] = [{'id': 'provider', 'question': 'Research the constrained provider', 'blocks': 'architecture', 'kind': 'design-decision', 'owner': 'research', 'due_stage': 'research'}]
        write(self.root / handoff.REGISTER, self.register)
        self.assertEqual('complete', handoff.check(self.root, 'trial', 'research')['status'])
        self.assertEqual('needs-design-decision', handoff.check(self.root, 'trial', 'architecture')['status'])
        self.assertEqual('needs-design-decision', handoff.check(self.root, 'trial', 'research', questions_only=True)['status'])

    def design_fixture(self):
        question = {'id': 'design-boundary', 'question': 'Realize the context, contracts and UI placement',
                    'blocks': 'tooling', 'kind': 'design-decision', 'owner': 'architecture', 'due_stage': 'architecture'}
        self.register['unresolved'] = [question]
        write(self.root / handoff.REGISTER, self.register)
        relative = 'docs/architecture/decisions/household.md'
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        marker = handoff.projection(self.root, 'trial')[0]['resolution_marker']
        path.write_text('# Household ownership\n\n- **Status**: Proposed\n' + marker + '\n\nOne household context owns list contracts; the Web adapter owns initial rendering.\n', encoding='utf-8')
        import hashlib
        model = {'decisions': [{'id': 'household', 'path': relative, 'status': 'Proposed',
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}
        write(self.root / 'docs/architecture/architecture-map.json', model)
        return question, path, model

    def test_approved_question_resolves_through_existing_proposed_adr(self):
        question, path, model = self.design_fixture()
        before = (self.root / handoff.REGISTER).read_bytes()
        write(self.root / '.specify/governance/bootstrap-assessment-approval.json', {'approved': True})
        self.assertEqual('complete', handoff.require(self.root, 'trial', 'architecture', questions_only=True)['status'])
        self.assertEqual('complete', handoff.require(self.root, 'trial', 'tooling')['status'])
        self.assertEqual(before, (self.root / handoff.REGISTER).read_bytes())
        self.assertEqual('Proposed', handoff.projection(self.root, 'trial')[0]['resolution_evidence'][0]['status'])
        # Earlier failure metadata cannot force another paid architecture dispatch.
        write(self.directory / 'handoff-tooling.json', {'status': 'needs-design-decision', 'retry_stage': 'architecture'})
        self.assertIsNone(handoff.retry_stage(self.root, 'trial', 'tooling'))
        question['question'] = 'A changed requirement needs new design evidence'
        write(self.root / handoff.REGISTER, self.register)
        self.assertEqual('architecture', handoff.retry_stage(self.root, 'trial', 'tooling'))

    def test_stale_unreferenced_or_rejected_adr_cannot_close_design(self):
        question, path, model = self.design_fixture()
        original = path.read_bytes()
        path.write_bytes(original + b'Unbound edit\n')
        self.assertEqual('needs-design-decision', handoff.check(self.root, 'trial', 'tooling')['status'])
        path.write_bytes(original)
        model['decisions'][0]['status'] = 'Rejected'
        write(self.root / 'docs/architecture/architecture-map.json', model)
        self.assertEqual('needs-design-decision', handoff.check(self.root, 'trial', 'tooling')['status'])
        write(self.root / 'docs/architecture/architecture-map.json', {'decisions': []})
        self.assertEqual('needs-design-decision', handoff.check(self.root, 'trial', 'tooling')['status'])

    def test_design_failure_does_not_request_user_answer_and_retries_owner(self):
        question, path, model = self.design_fixture()
        path.unlink()
        with self.assertRaises(ValueError) as caught:
            handoff.require(self.root, 'trial', 'architecture', questions_only=True)
        self.assertNotIn('--answer', str(caught.exception))
        self.assertIn('design owner', str(caught.exception))
        self.assertEqual('architecture', handoff.retry_stage(self.root, 'trial', 'architecture', completing=True))
        question['kind'] = 'user-answer'
        write(self.root / handoff.REGISTER, self.register)
        with self.assertRaisesRegex(ValueError, 'needs-user-answer'):
            handoff.retry_stage(self.root, 'trial', 'tooling')

    def test_first_feature_is_bounded_and_future_blockers_do_not_expand_it(self):
        from validate_governance_state import roadmap
        model = {'elements': [{'id': 'list', 'type': 'domain-capability'}], 'relationships': [], 'strategic_model': {
            'journeys': [{'id': 'j-first', 'source_journey': 'shopping', 'steps': []}, {'id': 'j-later', 'source_journey': 'history', 'steps': []}],
            'candidate_slices': [{'id': 'slice-first', 'journey': 'j-first', 'contexts': ['list']}, {'id': 'slice-later', 'journey': 'j-later', 'contexts': ['list']}]}}
        write(self.root / 'docs/architecture/architecture-map.json', model)
        path = self.root / 'docs/architecture/specification-roadmap.md'
        import re
        content = re.sub(r'(?m)^- \*\*Scope\*\*:.*$', '- **Scope**: slice-first', roadmap())
        path.write_text(content, encoding='utf-8')
        value = handoff.first_feature(self.root, require_ready=True)
        self.assertEqual(['list'], value['architectureScope'])
        self.assertEqual(['shopping'], value['journeyIds'])
        path.write_text(content.replace('slice-first', 'slice-first and slice-later'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'future candidate journeys'):
            handoff.first_feature(self.root)
        path.write_text(content.replace('**Status**: Ready', '**Status**: Blocked'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'before asking for final acceptance'):
            handoff.first_feature(self.root, require_ready=True)

    def test_late_question_stops_before_output_validation(self):
        write(self.directory / 'state.json', {'status': 'running', 'current_step_id': 'architecture-dispatch'})
        handoff.ask(self.root, 'trial', 'legal-region', 'Which mandated region applies?', 'consumer', 'architecture', 'Use the stated contractual region', kind='user-answer')
        with self.assertRaisesRegex(ValueError, 'needs-user-answer'):
            handoff.require(self.root, 'trial', 'architecture', questions_only=True)

    def test_technical_question_requires_explicit_kind_and_routes_to_design_owner(self):
        write(self.directory / 'state.json', {'status': 'running', 'current_step_id': 'architecture-prerequisite-closure'})
        args = (self.root, 'trial', 'provider-input', 'Resolve exact provider bindings', 'Architecture/research owner', 'closure', 'Use selected provider evidence')
        with self.assertRaisesRegex(ValueError, 'explicit question kind'):
            handoff.ask(*args)
        self.assertFalse((self.directory / 'decision-questions.json').exists())
        handoff.ask(*args, kind='design-decision')
        with self.assertRaisesRegex(ValueError, 'needs-design-decision') as caught:
            handoff.require(self.root, 'trial', 'closure', questions_only=True)
        self.assertNotIn('--answer', str(caught.exception))
        self.assertEqual('closure', handoff.retry_stage(self.root, 'trial', 'closure', completing=True))

    def test_recipe_uses_sync_resolved_tool_not_path(self):
        write(self.root / '.program-kit/evidence/toolchain.json', {'satisfied': True, 'commands': {'node': ['exact-managed-node']}})
        with patch.object(managed, 'run', return_value=0) as execute, patch.object(managed.shutil, 'which', side_effect=AssertionError('PATH discovery is forbidden after sync')):
            managed.command(self.root, ['node', '--version'])
        self.assertEqual(['exact-managed-node', '--version'], execute.call_args.args[0])

    def test_new_register_fields_pass_the_actual_governance_validator(self):
        import governance_state as governance
        from contextlib import chdir
        from validate_governance_state import write_installation, decisions
        write_installation(self.root, '0.3.1')
        value = decisions()
        value.update(first_slice=self.register['first_slice'], identity=self.register['identity'])
        value['unresolved'] = [{'id': 'future', 'question': 'Production region?', 'blocks': 'deployment', 'owner': 'consumer', 'kind': 'user-answer', 'due_stage': 'production'}]
        write(self.root / handoff.REGISTER, value)
        with chdir(self.root):
            governance.configure_paths()
            self.assertEqual(value, governance.validate_bootstrap_decisions())

    def test_maintained_recipes_bind_inputs_and_preserve_failure_case(self):
        self.register['toolchain'] = {'pins': {'dotnet-sdk': '10.0.202', 'node': '24.20.0'}}
        write(self.root / handoff.REGISTER, self.register)
        for kind in ('dotnet-runtime', 'browser-runtime', 'foundation-host'):
            result = managed.render(self.root, kind, kind)
            recipe, _, contract, cases = validate_recipe(self.root, kind, result['recipe'])
            self.assertTrue(recipe.is_file())
            self.assertEqual([managed.catalog()[kind]['case']], cases)
            for target, source in contract['fixtures'].items():
                destination = self.root / target
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((self.root / source).read_bytes())
            with patch.object(managed, 'command', side_effect=ValueError('exact seeded underlying failure')):
                self.assertEqual(1, managed.probe(self.root))
            self.assertIn('exact seeded underlying failure', (self.root / 'compatibility-results.xml').read_text())
            with self.assertRaisesRegex(ValueError, 'already exists'):
                managed.render(self.root, kind, kind)

    def test_refinement_requires_exact_proposal_adr_and_preserved_consumer_evidence(self):
        old = {'id': 'list-context', 'status': 'proposed', 'evidence': ['consumer-1'], 'responsibilities': ['Initial interpretation']}
        new = {**old, 'responsibilities': ['Refined list ownership']}
        model = {'decisions': [{'id': 'ownership', 'status': 'Proposed'}], 'refinements': [{
            'collection': 'candidate_contexts', 'id': old['id'],
            'before_sha256': architecture.refinement_hash(old), 'after_sha256': architecture.refinement_hash(new),
            'decision_refs': ['ownership'], 'rationale': 'Domain research clarified the boundary'}]}
        self.assertEqual([new], architecture.refined_records(model, 'candidate_contexts', [old], [new]))
        promoted = {**new, 'status': 'accepted'}
        self.assertEqual([promoted], architecture.refined_records(model, 'candidate_contexts', [old], [promoted]))
        with self.assertRaisesRegex(architecture.ArchitectureMapError, 'Explicit consumer'):
            architecture.refined_records(model, 'candidate_contexts', [{**old, 'status': 'explicit'}], [new])
        with self.assertRaisesRegex(architecture.ArchitectureMapError, 'stale'):
            architecture.refined_records(model, 'candidate_contexts', [old], [{**new, 'responsibilities': ['Unreviewed change']}])
        changed = {**new, 'evidence': ['invented-evidence']}
        model['refinements'][0]['after_sha256'] = architecture.refinement_hash(changed)
        with self.assertRaisesRegex(architecture.ArchitectureMapError, 'preserve original consumer evidence'):
            architecture.refined_records(model, 'candidate_contexts', [old], [changed])

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Native engine tests use the installed Spec Kit interpreter')
    def test_native_approved_design_handoff_reaches_review_without_rewriting_register(self):
        from contextlib import chdir
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
        from specify_cli.workflows.base import RunStatus
        question, path, model = self.design_fixture()
        original = path.read_bytes()
        approved = (self.root / handoff.REGISTER).read_bytes()
        path.write_text('# Household ownership\n\n- **Status**: Proposed\n\nDesign exists but its resolution link is absent.\n', encoding='utf-8')
        import hashlib
        model['decisions'][0]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        write(self.root / 'docs/architecture/architecture-map.json', model)
        write(self.root / '.specify/governance/bootstrap-assessment-approval.json', {'register': hashlib.sha256(approved).hexdigest()})
        shutil.copytree(ROOT / 'extensions/program-kit-governance/scripts', self.root / '.specify/extensions/program-kit-governance/scripts')
        shutil.copytree(ROOT / 'extensions/program-kit-dotnet/scripts', self.root / '.specify/extensions/program-kit-dotnet/scripts')
        definition = WorkflowDefinition({'schema_version': '1.0', 'workflow': {'id': 'program-kit-bootstrap', 'name': 'Approved design handoff regression', 'version': '0.12.0'},
            'inputs': {'bootstrap_verdict': {'type': 'string', 'default': ''}}, 'steps': [
                {'id': 'require-architecture-answers', 'type': 'shell', 'run': '"' + sys.executable + '" .specify/extensions/program-kit-governance/scripts/bootstrap_handoff.py questions --run-id {{ context.run_id }} --stage architecture', 'output_format': 'json'},
                {'id': 'require-tooling-handoff', 'type': 'shell', 'run': '"' + sys.executable + '" .specify/extensions/program-kit-governance/scripts/bootstrap_handoff.py require --run-id {{ context.run_id }} --stage tooling', 'output_format': 'json'},
                {'id': 'review', 'type': 'gate', 'message': 'Human architecture acceptance remains required', 'options': ['approve', 'reject'], 'on_reject': 'retry', 'verdict_input': 'bootstrap_verdict'}]})
        with chdir(self.root), patch.object(sys.stdin, 'isatty', return_value=False):
            engine = WorkflowEngine(self.root)
            state = engine.execute(definition, run_id='design')
            self.assertEqual(RunStatus.FAILED, state.status)
            self.assertEqual('require-architecture-answers', state.current_step_id)
            self.assertNotIn('require-tooling-handoff', state.step_results)
            path.write_bytes(original)
            model['decisions'][0]['sha256'] = hashlib.sha256(original).hexdigest()
            write(self.root / 'docs/architecture/architecture-map.json', model)
            state = engine.resume('design')
            self.assertEqual(RunStatus.PAUSED, state.status)
            self.assertEqual('review', state.current_step_id)
            self.assertEqual(approved, (self.root / handoff.REGISTER).read_bytes())

    @unittest.skipUnless(importlib.util.find_spec('specify_cli'), 'Native engine tests use the installed Spec Kit interpreter')
    def test_native_question_answer_gate_and_explicit_reopen(self):
        from contextlib import chdir
        from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine, RunState, validate_workflow
        from specify_cli.workflows.base import RunStatus
        import workflow_lifecycle as lifecycle
        scripts = self.root / '.specify/extensions/program-kit-governance/scripts'
        shutil.copytree(ROOT / 'extensions/program-kit-governance/scripts', scripts)
        shutil.copytree(ROOT / 'extensions/program-kit-dotnet/scripts', self.root / '.specify/extensions/program-kit-dotnet/scripts')
        self.register['unresolved'] = [{'id': 'region', 'question': 'Required region?', 'blocks': 'provider', 'kind': 'user-answer', 'owner': 'consumer', 'due_stage': 'research'}]
        write(self.root / handoff.REGISTER, self.register)
        definition = WorkflowDefinition({'schema_version': '1.0', 'workflow': {'id': 'program-kit-bootstrap', 'name': 'Deterministic handoff transport', 'version': '0.12.0'},
            'inputs': {'bootstrap_verdict': {'type': 'string', 'default': ''}}, 'steps': [
                {'id': 'require-research-handoff', 'type': 'shell', 'run': '"' + sys.executable + '" .specify/extensions/program-kit-governance/scripts/bootstrap_handoff.py require --run-id {{ context.run_id }} --stage research', 'output_format': 'json'},
                {'id': 'review', 'type': 'gate', 'message': 'Independent baseline acceptance', 'options': ['approve', 'reject'], 'on_reject': 'retry', 'verdict_input': 'bootstrap_verdict'}]})
        self.assertEqual([], validate_workflow(definition))
        with chdir(self.root), patch.object(sys.stdin, 'isatty', return_value=False):
            engine = WorkflowEngine(self.root)
            state = engine.execute(definition, run_id='native')
            self.assertEqual(RunStatus.FAILED, state.status)
            self.assertNotIn('review', state.step_results)
            handoff.answer(self.root, 'native', 'region', 'EU')
            state = engine.resume('native')
            self.assertEqual(RunStatus.PAUSED, state.status)
            self.assertEqual('review', state.current_step_id)
            state = engine.resume('native', inputs={'bootstrap_verdict': 'approve'})
            self.assertEqual(RunStatus.COMPLETED, state.status)
            write(self.root / '.specify/governance/bootstrap-assessment-approval.json', {'fixture': 'old approval'})
            lifecycle.reopen(self.root, 'native', 'research')
            self.assertFalse((self.root / '.specify/governance/bootstrap-assessment-approval.json').exists())
            self.assertFalse((self.root / '.specify/workflows/runs/native/decision-responses.json').exists())
            self.assertTrue(list((self.root / '.specify/workflows/resumption-history/native').rglob('decision-responses.json')))
            self.assertFalse(RunState.load('native', self.root).inputs['auto_approve_and_ratify'])
            handoff.answer(self.root, 'native', 'region', 'A corrected operator answer')


if __name__ == '__main__':
    unittest.main()

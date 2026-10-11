"""Ordinary Spec Kit work needs knowledge and code checks, not governance dossiers."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import phase_obligations as knowledge
import implementation_preflight
import execution_history
import upgrade_remediation


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='ordinary-development-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.feature = self.root / 'specs/001-slots'
        self.feature.mkdir(parents=True)
        for name, text in [('spec.md','Reserve slots with idempotent admission.'),
                           ('plan.md','Pure domain policy; no database or browser required.'),
                           ('tasks.md','Implement and test reservation outcomes.')]:
            (self.feature / name).write_text(text)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}

    def test_normal_flow_creates_no_dossiers_or_approvals(self):
        before = self.snapshot()
        started = time.perf_counter()
        for phase in ('planning','after-plan','after-tasks','implementation'):
            value = knowledge.check(self.root, self.feature, phase)
            self.assertIn('domain-semantics', {r['id'] for r in value['requirements']})
        with contextlib.redirect_stdout(io.StringIO()), patch.object(sys,'argv',
                ['preflight','--repository',str(self.root),'--feature-dir','specs/001-slots']):
            self.assertEqual(0, implementation_preflight.main())
        self.assertEqual(before, self.snapshot())
        print(f'Four phases + implementation guidance: {time.perf_counter()-started:.3f}s; 0 maintained artifacts, 0 approvals')

    def test_planned_roles_gate_after_plan_tasks_and_source_without_builds(self):
        eng = self.root / 'eng'; eng.mkdir()
        graph = {'runtimeComposition': {'projects': [
            {'path': 'src/Notes.Core/Notes.Core.csproj', 'role': 'core',
             'responsibilities': [{'name': 'Notes.INotes', 'kind': 'contract', 'effects': []}]},
            {'path': 'src/Notes/Notes.csproj', 'role': 'composition',
             'responsibilities': [{'name': 'Notes.Notes', 'kind': 'runtime', 'effects': [], 'provides': ['Notes.INotes']}]}],
            'bindings': [{'capabilityProject': 'src/Notes.Core/Notes.Core.csproj',
                'implementationProject': 'src/Notes/Notes.csproj', 'capability': 'Notes.INotes',
                'implementation': 'Notes.Notes', 'registration': 'Notes.Feature.ConfigureServices'}]}}
        path = eng / 'architecture.json'; path.write_text(json.dumps(graph))
        before = self.snapshot()
        with patch.object(subprocess, 'run', side_effect=AssertionError('Planned validation must not build')):
            for phase in ('after-plan', 'after-tasks', 'implementation'):
                with self.assertRaisesRegex(ValueError, 'implementation.*role'):
                    knowledge.check(self.root, self.feature, phase)
            with contextlib.redirect_stdout(io.StringIO()), patch.object(sys, 'argv',
                    ['preflight', '--repository', str(self.root), '--feature-dir', 'specs/001-slots']):
                self.assertEqual(2, implementation_preflight.main())
        self.assertEqual(before, self.snapshot())
        graph['runtimeComposition']['projects'][1]['role'] = 'implementation'
        path.write_text(json.dumps(graph))
        for phase in ('after-plan', 'after-tasks', 'implementation'):
            knowledge.check(self.root, self.feature, phase)

    def test_planned_source_requires_manifest_but_empty_repository_is_valid(self):
        (self.feature / 'plan.md').write_text('Implement src/Notes.Core/Notes.Core.csproj in C#.')
        with self.assertRaisesRegex(ValueError, 'eng/architecture.json'):
            knowledge.check(self.root, self.feature, 'after-plan')
        eng = self.root / 'eng'; eng.mkdir()
        (eng / 'architecture.json').write_text('{"runtimeComposition":{"projects":[],"bindings":[]}}')
        knowledge.check(self.root, self.feature, 'after-plan')

    def test_constitution_amendment_is_independent_and_preserves_previous_approval(self):
        import os
        import governance_state as governance
        from validate_governance_state import constitution
        path = self.root / '.specify/memory/constitution.md'
        path.parent.mkdir(parents=True)
        path.write_text(constitution(pending=False).replace('1.0.0', '1.1.0'))
        # Historical approval/model bytes may be absent or stale after a toolkit upgrade.
        stale = self.root / governance.ASSESSMENT_APPROVAL
        stale.parent.mkdir(parents=True)
        stale.write_text('{"status":"obsolete","version":"0.12.3"}')
        marker = self.root / '.specify/memory/constitution-ratification.json'
        previous = {'schema_version':'1.0', 'status':'Ratified',
                    'constitution':{'version':'1.0.0','sha256':'historical'}}
        marker.write_text(json.dumps(previous))
        original = os.getcwd()
        try:
            os.chdir(self.root)
            governance.configure_paths()
            governance.begin()
            governance.begin()  # Interrupted/repeated drafting preserves the last approval.
            governance.validate_constitution_draft()
            governance.write_review('constitution')
            review = self.root / governance.CONSTITUTION_REVIEW
            reviewed = path.read_bytes()
            path.write_bytes(reviewed + b'\nChanged principle.\n')
            with self.assertRaisesRegex(governance.GovernanceStateError, 'stale|changed'):
                governance.ratify('ratify')
            path.write_bytes(reviewed)
            governance.ratify('ratify')
            governance.validate_ratification()
            self.assertEqual(previous, json.loads(marker.read_text())['previous_ratification'])
            self.assertEqual('{"status":"obsolete","version":"0.12.3"}', stale.read_text())
            self.assertNotIn('assessment approval still matches', review.read_text())
        finally:
            os.chdir(original)
            governance.configure_paths()

    def test_changed_tooling_and_stale_receipts_do_not_block_drafting(self):
        folder = self.root / '.specify/governance'
        folder.mkdir(parents=True)
        (folder/'bootstrap-completion.json').write_text('{"status":"Completed","obsolete":true}')
        (self.feature/'obligation-review.json').write_text('{"basis":"old"}')
        (self.feature/'verification-results.json').write_text('{"status":"failed"}')
        before = self.snapshot()
        knowledge.check(self.root, self.feature, 'implementation')
        result = upgrade_remediation.assess(self.root)
        self.assertTrue(result['migrationVerificationEstablished'])
        self.assertIsNone(result['applicationReady'])
        self.assertFalse(result['applicationChecksPerformed'])
        self.assertFalse(result['features'][0]['migrationVerificationRequired'])
        self.assertEqual(before, self.snapshot())

    def test_unrelated_project_does_not_activate_feature_guidance(self):
        other = self.root / 'src/Future.Api'
        other.mkdir(parents=True)
        (other/'Future.Api.csproj').write_text('<Project><PackageReference Include="Microsoft.EntityFrameworkCore" /></Project>')
        (self.feature/'plan.md').write_text('Pure domain policy only.')
        ids = {r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('persistence-adoption',ids)
        self.assertNotIn('http-operation-contracts',ids)

    def test_guidance_arrives_before_source_and_has_real_enforcement_routes(self):
        (self.feature/'plan.md').write_text('dotnet API using async cancellation and an owned database provider.')
        value = knowledge.project(self.root,self.feature,'planning')
        rules = {r['id']:r for r in value['requirements']}
        self.assertIn('http-operation-contracts',rules)
        self.assertIn('persistence-adoption',rules)
        self.assertEqual(['CA2012','CA2016'],rules['dotnet-async']['enforcement']['diagnostics'])
        for r in rules.values():
            self.assertTrue(r['sources'])
            for test in r['enforcement']['coverage']:
                self.assertTrue((ROOT/test).is_file(), test)

    def test_conditional_guidance_and_csharp_intent_are_scoped_before_source(self):
        ids={r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('persistence-adoption',ids)
        self.assertNotIn('browser-experience',ids)
        (self.root/'package.json').write_text('{"devDependencies":{"vite":"1.0.0"}}')
        ids={r['id'] for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertNotIn('browser-experience',ids)
        (self.feature/'plan.md').write_text('C# immutable value semantics for a small identifier.')
        rules={r['id']:r for r in knowledge.project(self.root,self.feature,'planning')['requirements']}
        self.assertIn('dotnet-source-quality',rules)
        self.assertIn('not a blanket replacement',rules['dotnet-source-quality']['example'])

    def test_excluded_capabilities_do_not_activate_guidance(self):
        (self.feature/'plan.md').write_text('C# policy only. No database. API and browser are future out of scope.')
        ids = {r['id'] for r in knowledge.project(self.root, self.feature, 'planning')['requirements']}
        self.assertNotIn('persistence-adoption', ids)
        self.assertNotIn('browser-experience', ids)
        self.assertNotIn('http-operation-contracts', ids)
        self.assertNotIn('dotnet-concurrency', ids)

    def test_identity_styling_intent_routes_provider_theme_guidance_before_frontend_source(self):
        (self.feature / 'spec.md').write_text('Style the Notes sign-in and recovery screens with accessible brand presentation.')
        before = self.snapshot()
        for phase in ('planning', 'tasks', 'implementation', 'delivery'):
            with self.subTest(phase=phase):
                value = knowledge.project(self.root, self.feature, phase)
                self.assertIn('browser-experience', {rule['id'] for rule in value['requirements']})
                rendered = knowledge.render(value, phase)
                self.assertIn('Keycloak', rendered)
                self.assertIn('active realm/client theme binding', rendered)
                self.assertIn('omitted implementation term', rendered)
                self.assertIn('existing intake, bootstrap decisions and UI inputs', rendered)
        self.assertEqual(before, self.snapshot())

    def test_identity_backend_and_explicitly_excluded_screens_do_not_invent_ui_scope(self):
        for prose in ('A command-line login operation returns a token.',
                      'An API login endpoint validates authentication.',
                      'Pure domain policy.\n## Non-goals\nSign-in and account recovery screens.'):
            with self.subTest(prose=prose):
                (self.feature / 'plan.md').write_text(prose)
                ids = {rule['id'] for rule in knowledge.project(self.root, self.feature, 'planning')['requirements']}
                self.assertNotIn('browser-experience', ids)

    def test_selected_ef_package_supplies_planning_knowledge_even_without_keywords(self):
        store = self.root/'src/Slots.Store'; store.mkdir(parents=True)
        (store/'Slots.Store.csproj').write_text('<Project><PackageReference Include="Microsoft.EntityFrameworkCore" /></Project>')
        (self.feature/'plan.md').write_text('Use C# source at src/Slots.Store/Slots.Store.csproj.')
        ids = {r['id'] for r in knowledge.project(self.root, self.feature, 'planning')['requirements']}
        self.assertIn('persistence-adoption', ids)
        self.assertIn('dotnet-queries', ids)

    def test_positive_api_prefix_and_nested_non_goals_are_scoped_separately(self):
        (self.feature/'plan.md').write_text('C# API without database.\n## Non-goals\n### Later\nBrowser frontend\n## Design\nPure policy.')
        ids = {r['id'] for r in knowledge.project(self.root, self.feature, 'planning')['requirements']}
        self.assertIn('http-operation-contracts', ids)
        self.assertNotIn('persistence-adoption', ids)
        self.assertNotIn('browser-experience', ids)

    def test_phase_projection_is_concise_and_changes_the_immediate_action(self):
        (self.feature/'plan.md').write_text('dotnet API with database persistence and async cancellation.')
        outputs = {p: knowledge.render(knowledge.project(self.root, self.feature, p), p)
                   for p in ('planning','tasks','implementation','delivery')}
        # Brevity cannot erase decisive canonical constraints; full references stay focused.
        self.assertTrue(all(len(o.split()) < 1600 for o in outputs.values()))
        self.assertTrue(all('canonical permission' in o and 'when those responsibilities exist' in o
                            for o in outputs.values()))
        self.assertIn('decisions', outputs['planning'])
        self.assertIn('test tasks', outputs['tasks'])
        self.assertIn('focused', outputs['implementation'])
        self.assertIn('acceptance', outputs['delivery'])
        self.assertNotIn('Focused lookup:', outputs['implementation'])

    def test_historical_cli_is_read_only_and_keeps_original_results(self):
        receipt=self.feature/'verification-results.json'
        receipt.write_text('{"status":"failed","basis":"original old source"}')
        before=self.snapshot()
        result=subprocess.run([sys.executable,str(ROOT/'extensions/program-kit-governance/scripts/historical_phase_evidence.py'),
                               'inspect','--repository',str(self.root),'--feature-dir','specs/001-slots'],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        value=json.loads(result.stdout)
        self.assertTrue(value['historicalOnly'])
        self.assertEqual('failed',value['records']['verification-results.json']['status'])
        self.assertEqual(before,self.snapshot())
        retired = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-governance/scripts/lifecycle_state.py'),
                                 '--repository', str(self.root), '--feature-dir', 'specs/001-slots', 'verify-delivery'],
                                capture_output=True, text=True)
        self.assertEqual(2, retired.returncode)
        self.assertIn('retired', retired.stderr)
        self.assertEqual(before, self.snapshot())

    def test_completion_cannot_claim_success_without_an_engineering_command(self):
        with self.assertRaisesRegex(ValueError,'no completion claim'):
            knowledge.check(self.root,self.feature,'delivery')

    def test_successful_engineering_command_does_not_certify_semantic_or_human_acceptance(self):
        eng = self.root / 'eng'
        eng.mkdir(exist_ok=True)
        (eng / 'Invoke-RepositoryVerification.ps1').write_text(
            "Write-Output 'Fixture engineering oracle ran'\nexit 0\n", encoding='utf-8')
        result = knowledge.execute(self.root, self.feature)
        self.assertTrue(result['engineeringAcceptanceEstablished'])
        self.assertFalse(result['acceptanceEstablished'])
        self.assertFalse(result['semanticReviewEstablished'])
        self.assertFalse(result['releaseReadinessEstablished'])
        logs = list((self.root / 'artifacts/program-kit/runs').glob('*/stdout.log'))
        self.assertEqual(1, len(logs))
        self.assertIn('Fixture engineering oracle ran', logs[0].read_text())

    def test_partial_checkpoint_never_runs_full_acceptance_but_explicit_handoff_does(self):
        (self.feature/'tasks.md').write_text('- [X] T001 Test the operation\n- [ ] T002 Finish the story\n')
        with patch.object(knowledge, 'execute') as execute:
            result = knowledge.finish(self.root, self.feature)
            self.assertEqual('in-progress', result['status'])
            self.assertFalse(result['acceptanceEstablished'])
            execute.assert_not_called()
            knowledge.finish(self.root, self.feature, handoff=True)
            execute.assert_called_once_with(self.root, self.feature)
        (self.feature/'tasks.md').write_text('> Draft: incomplete\n- [X] T001 A saved phase\n')
        with patch.object(knowledge, 'execute') as execute:
            self.assertFalse(knowledge.finish(self.root, self.feature)['acceptanceEstablished'])
            execute.assert_not_called()
        (self.feature/'tasks.md').write_text('- [X] T001 A saved phase\n<!-- program-kit:tasks-draft {"status":"draft"} -->\n')
        with patch.object(knowledge, 'execute') as execute:
            self.assertFalse(knowledge.finish(self.root, self.feature)['acceptanceEstablished'])
            execute.assert_not_called()

    def test_feature_closure_runs_acceptance_once_and_forwards_affected_scope(self):
        (self.feature/'tasks.md').write_text('- [X] T001 Delivered behavior\n')
        with patch.object(knowledge, 'execute', return_value={'acceptanceEstablished': True}) as execute:
            self.assertTrue(knowledge.finish(self.root, self.feature)['acceptanceEstablished'])
            execute.assert_called_once_with(self.root, self.feature)

    def test_coarse_parent_with_delivered_operation_substep_is_still_progress(self):
        (self.feature/'tasks.md').write_text(
            '- [ ] T040 Deliver policy operations\n'
            '  - [X] T040.create Create owned policy; auth/storage regressions passed\n'
            '  - [ ] T040.process Process uploaded evidence; OCR lease gate pending\n')
        with patch.object(knowledge, 'execute') as execute:
            result = knowledge.finish(self.root, self.feature)
            self.assertEqual('in-progress', result['status'])
            self.assertEqual(2, result['pendingTasks'])
            execute.assert_not_called()

    def test_operation_graph_never_defers_retained_feature_authority_gate(self):
        (self.feature/'spec.md').write_text(
            '- **Specification roadmap entry**: RM-01\nCreate owned policy then process evidence.\n')
        ledger = self.root/'docs/architecture/bootstrap-prerequisites.json'
        ledger.parent.mkdir(parents=True)
        items = [{'id': 'OCR-PROOF', 'owner': 'Evidence', 'task': 'Prove selected OCR admission',
                  'affected_slices': ['RM-01'], 'status': 'open', 'disposition': 'feature',
                  'verification': 'compatibility', 'trigger': 'before-implementation'}]
        ledger.write_text(json.dumps({'prerequisites': items}))
        # Task-level independence cannot change previously approved feature-scope authority.
        with patch('bootstrap_lifecycle.current_compatibility_evidence', return_value=None):
            proofs = knowledge.retained_proofs(self.root, self.feature, 'implementation')
            self.assertTrue(proofs[0]['requiredNow'])
            with self.assertRaisesRegex(ValueError, 'OCR-PROOF'):
                knowledge.require_due_proofs(self.root, self.feature, 'implementation')
            items[0]['trigger'] = 'delivery'
            ledger.write_text(json.dumps({'prerequisites': items}))
            knowledge.require_due_proofs(self.root, self.feature, 'implementation')
            with self.assertRaisesRegex(ValueError, 'OCR-PROOF'):
                knowledge.require_due_proofs(self.root, self.feature, 'delivery')
        self.assertEqual('delivery', json.loads(ledger.read_text())['prerequisites'][0]['trigger'])

    def test_closure_does_not_reuse_prior_scoped_pass_as_acceptance(self):
        eng = self.root/'eng'; eng.mkdir()
        (eng/'Invoke-RepositoryVerification.ps1').write_text('exit 0')
        prior = self.root/'artifacts/tests/runs/old'; prior.mkdir(parents=True)
        scoped = {'schemaVersion': 1, 'scope': 'Focused', 'status': 'completed',
                  'projects': ['tests/Policies.Tests/Policies.Tests.csproj'],
                  'testArguments': ['--filter', 'CreateOwnedPolicy']}
        (prior/'result.json').write_text(json.dumps(scoped))
        (self.feature/'tasks.md').write_text('- [X] T001 Delivered operation\n')
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            result = knowledge.finish(self.root, self.feature)
        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertNotIn('-Scope', command)
        self.assertNotIn('-Plan', command)
        self.assertTrue(result['engineeringAcceptanceEstablished'])
        self.assertEqual(scoped, json.loads((prior/'result.json').read_text()))
        self.assertEqual(1, len(list((self.root/'artifacts/program-kit/runs').glob('*/run.json'))))

    def test_failed_engineering_remains_failed_and_preserves_diagnostics(self):
        eng = self.root/'eng';eng.mkdir()
        (eng/'Invoke-RepositoryVerification.ps1').write_text('Write-Error "actual application failure"; exit 7')
        with self.assertRaisesRegex(ValueError,'Application verification failed'):
            knowledge.execute(self.root,self.feature)
        logs = list((self.root/'artifacts/program-kit/runs').glob('*/run.json'))
        self.assertEqual(1,len(logs))
        self.assertEqual('failed',json.loads(logs[0].read_text())['status'])
        self.assertIn('actual application failure',' '.join((logs[0].parent/'stderr.log').read_text().split()))

    def test_history_preview_is_bounded_and_protects_failed_interrupted_and_unowned(self):
        for n in range(9):
            folder=self.root/f'artifacts/program-kit/runs/{n}';folder.mkdir(parents=True)
            (folder/'run.json').write_text(json.dumps({'schemaVersion':1,'owner':'program-kit',
                'status':'completed' if n<7 else ('failed' if n==7 else 'running'),
                'finishedAtUtc':str(n)}))
        unowned=self.root/'artifacts/program-kit/runs/application';unowned.mkdir()
        (unowned/'important.log').write_text('Keep application evidence')
        before=self.snapshot()
        self.assertEqual(['artifacts/program-kit/runs/1','artifacts/program-kit/runs/0'],execution_history.preview(self.root))
        self.assertEqual(before,self.snapshot())
        execution_history.cleanup(self.root)
        self.assertEqual([],execution_history.preview(self.root))
        self.assertTrue((self.root/'artifacts/program-kit/runs/7/run.json').exists())
        self.assertTrue((self.root/'artifacts/program-kit/runs/8/run.json').exists())
        self.assertTrue((unowned/'important.log').exists())


if __name__ == '__main__':
    unittest.main()

"""Registered existing-source repair preserves state and blocks product continuation."""
from pathlib import Path
import copy
import json
import sys
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import conformance_repair as repair
import task_draft as tasks
from owned_fixture import FixtureDirectory
from validate_story_delivery import seed, fictional_evaluation, accepted_fixture


class RepairTests(unittest.TestCase):
    def test_nondefault_browser_recovery_uses_only_authored_source_and_exact_target(self):
        from coding_context import prepare
        package = self.root / 'client'
        package.mkdir()
        (package / 'package.json').write_text(json.dumps({'devDependencies': {'typescript': '5.9.3'}}))
        (package / 'source.ts').write_text('export const title = "Policy";')
        (package / '.specify').mkdir()
        (package / '.specify/managed.ts').write_text('export async function managed() { await Promise.resolve(); }')
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('src/Create.txt', 'client/source.ts'))
        value = prepare(self.root, self.feature, task_ids=['T001'], configuration='Release', framework='fictional-target')['coding']
        blocker = next(row for row in value['blockers'] if row['code'] == 'PKC025')
        request = blocker['request']
        self.assertEqual(['client/source.ts'], request['findings'][0]['sourcePaths'])
        self.assertEqual(('Release', 'fictional-target'), (request['configuration'], request['framework']))
        before = repair.operation_policies(self.root, self.feature, ['create'], configuration='Release', framework='fictional-target')
        tasks.transition(self.root, self.feature, request, now=0)
        after = tasks.load_delivery(self.feature)
        self.assertEqual(before, after['conformanceRepairs'][0]['policyCells'])
        self.assertEqual(before, repair.operation_policies(self.root, self.feature, ['create'], configuration='Release', framework='fictional-target'))
        original_hash = repair.policy_basis(self.root, value)
        changed = copy.deepcopy(value)
        next(row for row in changed['evaluation']['duties'] if row['required'])['fingerprint'] = 'changed-applicable-policy'
        self.assertNotEqual(original_hash, repair.policy_basis(self.root, changed))
        unchanged = copy.deepcopy(value)
        unchanged['evaluation']['duties'].append({'rule': 'unselected.recommendation', 'fingerprint': 'unrelated', 'required': False})
        self.assertEqual(original_hash, repair.policy_basis(self.root, unchanged))

    def test_explicit_python_owner_requires_registered_current_repair_without_dotnet(self):
        from coding_context import prepare, require_ready
        from coding_evaluation_fixture import fictional_claims
        policy = self.root / 'src/policy.py'
        policy.write_text('def evaluate(value):\n    if value < 0:\n        raise ValueError("negative value")\n    return value + 1\n')
        unrelated = self.root / 'src/unrelated.py'; unrelated.write_text('raise RuntimeError("Unrelated file must not execute or become an owner")\n')
        target = self.feature / 'tasks.md'; target.write_text(target.read_text().replace('src/Create.txt', 'src/policy.py'))
        script = self.root / 'checks/story.py'
        script.write_text('import runpy\nevaluate = runpy.run_path("src/policy.py")["evaluate"]\nassert evaluate(2) == 3\ntry:\n    evaluate(-1)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("negative value was admitted")\n')
        declaration = {'schemaVersion': 1, 'toolkitChecks': [{'id': 'story-state', 'script': 'checks/story.py',
            'arguments': [], 'inputs': ['checks/story.py', 'src/policy.py'], 'timeoutSeconds': 10}]}
        (self.root / 'config/program-kit/verification.json').parent.mkdir(parents=True, exist_ok=True)
        (self.root / 'config/program-kit/verification.json').write_text(json.dumps(declaration))
        # Establish the initial fictional consumer's real Git baseline before
        # registration. Every repair assertion below preserves that exact ID.
        for command in (['git', 'init', '-q'], ['git', 'add', '.'], ['git', '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Program Kit fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Initial fictional Python owner']):
            subprocess.run(command, cwd=self.root, check=True, capture_output=True, text=True)
        baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
        saved = tasks.current(self.feature); saved['baseline'] = baseline; tasks.save_current(self.feature, saved)
        before = tasks.current(self.feature)
        original_tasks = [line for line in target.read_text().splitlines() if line.startswith('- [')]
        coding = prepare(self.root, self.feature, task_ids=['T001'])['coding']
        self.assertFalse(coding['nativeContext']['applicable'])
        self.assertNotIn('PKC024', {b['code'] for b in coding['blockers']})
        request = next(b['request'] for b in coding['blockers'] if b['code'] == 'PKC025')
        self.assertEqual(['src/policy.py'], request['findings'][0]['sourcePaths'])
        self.assertNotIn('Foundation', request['findings'][0]['checks'])
        invalid = copy.deepcopy(request); invalid['findings'][0]['sourcePaths'] = ['src/unrelated.py']
        with self.assertRaisesRegex(ValueError, 'owned source'):
            repair.register(self.root, self.feature, tasks.load_delivery(self.feature), invalid)
        result = tasks.transition(self.root, self.feature, request, now=0)
        finding = result['delivery']['conformanceRepairs'][-1]
        self.assertEqual(before['baseline'], tasks.current(self.feature)['baseline'])
        self.assertTrue(all(line in target.read_text() for line in original_tasks))
        tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'create', 'purpose': 'conformance'}, now=0)
        for identity in finding['taskIds']:
            target.write_text(target.read_text().replace('- [ ] ' + identity, '- [X] ' + identity))
        import toolkit_verification as toolkit
        toolkit.execute(self.root, ['story-state'], toolkit.declarations(self.root, declaration))
        checks = [p.relative_to(self.root).as_posix() for p in (self.root / 'artifacts/tests/toolkit-runs').glob('*/result.json') if p.parent.name != 'story-fixture']
        self.assertEqual(1, len(checks))
        current = prepare(self.root, self.feature, task_ids=finding['taskIds'])
        require_ready(current)
        claims = fictional_claims(current['coding'], 'src/policy.py', [{'kind': 'toolkit', 'id': 'story-state'}])
        # Real source/check identity is required even though review attribution
        # and product-outcome authority remain explicitly fictional.
        stale = copy.deepcopy(claims); stale[0]['inspections'][0]['sources'][0]['path'] = 'src/unrelated.py'
        with self.assertRaisesRegex(ValueError, 'outside the affected'):
            from coding_context import bind_evaluation
            bind_evaluation(self.root, self.feature, current['coding'], stale, checks)
        tasks.transition(self.root, self.feature, {'action': 'conformance-complete', 'findings': [finding['id']],
            'checks': checks, 'evaluation': claims, 'outcomeAssessment': {'review': 'review.md',
                'reviewer': 'fictional-independent-reviewer', 'conclusion': 'Fictional source review; actual finite Python positive/adverse controls passed with preserved outcome.',
                'materialEffects': {finding['id']: 'preserving'}}}, now=0)
        self.assertEqual('complete', tasks.load_delivery(self.feature)['conformanceRepairs'][-1]['status'])
        resumed = prepare(self.root, self.feature, task_ids=['T001'])
        self.assertNotIn('PKC025', {b['code'] for b in resumed['coding']['blockers']})
        self.assertEqual(baseline, tasks.current(self.feature)['baseline'])
        self.assertIn('Unrelated file', unrelated.read_text())

    def setUp(self):
        self.owner = FixtureDirectory(native=True)
        self.addCleanup(self.owner.cleanup)
        self.root = Path(self.owner.name)
        self.feature = self.root / 'specs/001-repair'
        self.feature.mkdir(parents=True)
        seed(self.root, self.feature)

    def finding(self, **change):
        return {'id': 'source-conformance', 'rule': 'principle.source-file-context',
                'sourcePaths': ['src/Create.txt'], 'operations': ['create', 'export'],
                'repair': 'Repair existing source layout and retain behavior', 'checks': 'story-state plus affected native checks',
                'materialEffect': 'preserving', **change}

    def test_insert_preserves_all_existing_identity_state_and_shared_dependencies(self):
        before = tasks.current(self.feature)
        value = tasks.load_delivery(self.feature)
        value['stories']['US1']['effort']['create']['seconds'] = 42
        value['checkpoints']['US1']['human'] = 'accepted'
        value['checkpoints']['US1']['decisions'] = [{'fictional': 'exact retained original'}]
        for human in ('pending', 'ready for review', 'accepted', 'deferred'):
            snapshot = copy.deepcopy(value)
            snapshot['checkpoints']['US2']['human'] = human
            # Registration is source-local and works independently of story disposition.
            updated, content = repair.register(self.root, self.feature, snapshot, {'findings': [self.finding(id='repair-' + human.replace(' ', '-'))]})
            self.assertEqual(snapshot['roles'], updated['roles'])
            self.assertEqual(42, updated['stories']['US1']['effort']['create']['seconds'])
            self.assertEqual(snapshot['checkpoints']['US1']['decisions'], updated['checkpoints']['US1']['decisions'])
            self.assertEqual(human, updated['checkpoints']['US2']['human'])
            self.assertEqual(before['baseline'], tasks.current(self.feature)['baseline'])
            self.assertEqual(1, len(repair.pending(updated, 'create')))
            self.assertEqual(1, len(repair.pending(updated, 'export')))
            with self.assertRaisesRegex(ValueError, 'PKC023'):
                repair.require_clear(updated, 'create')
            self.assertFalse(repair.require_clear(updated, 'integrate'))
            self.assertTrue(repair.require_clear(updated, 'export', repair=True))
            tasks.validate_operation_graph(content, required=True, root=self.root)

    def test_invalid_new_source_toolkit_or_unknown_operation_preserves_tasks(self):
        prior = (self.feature / 'tasks.md').read_bytes()
        value = tasks.load_delivery(self.feature)
        for change in ({'operations': ['invent-product']}, {'sourcePaths': ['src/New.txt']},
                       {'sourcePaths': ['.specify/private.json']}, {'sourcePaths': ['../private.txt']},
                       {'repair': 'Implement a new feature\n- [ ] T999 Hidden task'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                repair.register(self.root, self.feature, value, {'findings': [self.finding(**change)]})
            self.assertEqual(prior, (self.feature / 'tasks.md').read_bytes())

    def test_registered_cli_transition_blocks_product_and_scopes_conformance_start(self):
        result = tasks.transition(self.root, self.feature, {'action': 'conformance-register', 'findings': [self.finding()]}, now=0)
        value = result['delivery']
        self.assertEqual('T004', value['conformanceRepairs'][0]['taskIds'][0])
        with self.assertRaisesRegex(ValueError, 'PKC023'):
            tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'create'}, now=1)
        for purpose in ('repair', 'diagnose'):
            with self.assertRaisesRegex(ValueError, 'PKC023'):
                tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'create', 'purpose': purpose}, now=1)
        tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'export', 'purpose': 'conformance'}, now=2)
        import coding_context
        scope = coding_context.task_scope(self.feature, None)
        self.assertEqual(['T004'], scope['taskIds'])
        self.assertTrue(all('Conformance' in line for line in scope['tasks']))

    def test_atomic_amendment_and_repeated_registration_preserve_prior_bytes(self):
        before = (self.feature / 'tasks.md').read_bytes()
        original = tasks.atomic_write
        def fail_amendment(path, content):
            if 'T004' in content:
                raise OSError('injected atomic replacement failure')
            original(path, content)
        with patch.object(tasks, 'atomic_write', side_effect=fail_amendment), self.assertRaisesRegex(OSError, 'injected'):
            tasks.transition(self.root, self.feature, {'action': 'conformance-register', 'findings': [self.finding()]}, now=0)
        self.assertEqual(before, (self.feature / 'tasks.md').read_bytes())
        for identity in ('first-layout', 'second-lifetime'):
            tasks.transition(self.root, self.feature, {'action': 'conformance-register', 'findings': [self.finding(id=identity)]}, now=0)
        content = (self.feature / 'tasks.md').read_text()
        self.assertEqual(1, content.count('## Conformance repair tasks'))
        self.assertEqual(1, content.count('## Conformance prerequisite map'))
        value = tasks.load_delivery(self.feature)
        self.assertEqual(['T004', 'T005'], [r['taskIds'][0] for r in value['conformanceRepairs']])
        self.assertTrue({'T004', 'T005'} <= set(value['stories']['US1']['taskIds']))

    def test_changed_outcome_amendment_and_completion_require_independent_impact(self):
        tasks.transition(self.root, self.feature, {'action': 'conformance-register', 'findings': [self.finding(operations=['create'])]}, now=0)
        tasks.transition(self.root, self.feature, {'action': 'conformance-amend', 'finding': 'source-conformance',
                        'materialEffect': 'changed', 'rationale': 'The corrected admission now rejects previously accepted invalid state.'}, now=0)
        value = tasks.load_delivery(self.feature)
        self.assertEqual('preserving', value['conformanceRepairs'][0]['amendments'][0]['before'])
        self.assertEqual('pending', value['checkpoints']['US1']['human'])
        self.complete_changed_outcome()

    def complete_changed_outcome(self):
        with self.assertRaisesRegex(ValueError, 'never downgrade'):
            tasks.transition(self.root, self.feature, {'action': 'conformance-amend', 'finding': 'source-conformance',
                            'materialEffect': 'preserving', 'rationale': 'Do not reopen acceptance'}, now=0)
        tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'create', 'purpose': 'conformance'}, now=0)
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('- [ ] T004', '- [X] T004'))
        request = {'action': 'conformance-complete', 'findings': ['source-conformance'],
                   'checks': ['artifacts/tests/toolkit-runs/story-fixture/result.json'],
                   'evaluation': fictional_evaluation(self.root, self.feature, ['T004'])}
        with self.assertRaisesRegex(ValueError, 'outcome assessment'):
            tasks.transition(self.root, self.feature, request, now=0)
        request['outcomeAssessment'] = {'review': 'review.md', 'reviewer': 'fictional-independent-reviewer',
            'conclusion': 'Fictional corrected admission materially changes outcome; original accepted decisions stay in history.',
            'materialEffects': {'source-conformance': 'changed'}}
        tasks.transition(self.root, self.feature, request, now=0)
        value = tasks.load_delivery(self.feature)
        self.assertEqual('complete', value['conformanceRepairs'][0]['status'])
        self.assertEqual('pending', value['checkpoints']['US1']['human'])

    def test_actual_accepted_story_registers_without_rewriting_human_provenance(self):
        # Use real present/decision transitions, not a hand-constructed accepted flag.
        other = self.root / 'specs/002-accepted'
        other.mkdir()
        accepted_fixture(self.root, other)
        before = tasks.load_delivery(other)
        tasks.transition(self.root, other, {'action': 'conformance-register', 'findings': [self.finding()]}, now=0)
        after = tasks.load_delivery(other)
        for story in ('US1', 'US2'):
            self.assertEqual(before['checkpoints'][story]['decisions'], after['checkpoints'][story]['decisions'])
            self.assertEqual('accepted', after['checkpoints'][story]['human'])
            self.assertEqual('pending', after['checkpoints'][story]['engineering'])

    def test_shared_pending_repairs_block_transitive_operation_in_both_owner_orders(self):
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('- [ ] T001', '- [X] T001'))
        for index, operations in enumerate((['export', 'create'], ['create', 'export'])):
            tasks.transition(self.root, self.feature, {'action': 'conformance-register',
                'findings': [self.finding(id='shared-' + str(index), operations=operations)]}, now=0)
            with self.assertRaisesRegex(ValueError, 'PKC023'):
                tasks.transition(self.root, self.feature, {'action': 'start', 'operation': 'integrate'}, now=0)


if __name__ == '__main__':
    unittest.main()

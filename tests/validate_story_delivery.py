"""Bounded story progression, provenance, freshness and clock controls.

All people/decisions are fictional deterministic fixtures; no coding agents or
real human acceptance, posting, monitoring or consumer resets occur.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import task_draft as delivery
import task_draft as draft
import phase_obligations as phases
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
from composition_fixture import two_apps
import task_draft as reset


def story_tasks():
    return '''# Fictional runnable stories
<!-- program-kit:story-delivery-v1 -->
- [ ] T001 [US1] Materialize src/Create.txt
- [ ] T002 [US1] Integrate src/Create.txt and tests/Create.txt
- [ ] T003 [US2] Export through src/Export.txt

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| create | none |
| integrate | create |
| export | integrate |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | create | none | none | scaffold |
| T002 | integrate | T001 | scaffold | none |
| T003 | export | T002 | none | none |

## Story delivery map
| Story | Operations | Useful outcome | Independent walkthrough | Active minutes to review | Larger-story rationale |
|-------|------------|----------------|-------------------------|--------------------------|------------------------|
| US1 | create, integrate | Create owned record | Open UI, create and reopen record | 90 | none |
| US2 | export | Export record | Export and inspect durable result | 45 | none |
'''


def seed(root, feature):
    """Initialize fictional state for focused controls; installed reset exercises ratification."""
    for name in ('spec.md', 'plan.md'):
        (feature / name).write_text(delivery.POLICY + '\nFictional fresh specification.', encoding='utf-8')
    (feature / 'tasks.md').write_text(story_tasks(), encoding='utf-8')
    for name in ('src/Create.txt', 'src/Export.txt', 'artifacts/passing.json'):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({'status': 'completed', 'exitCode': 0, 'fixture': 'simulated; no human acceptance'}) if name.endswith('.json')
                          else 'Fictional fixture; no human acceptance.', encoding='utf-8')
    with patch.object(delivery, 'require_policy'):
        delivery.transition(root, feature, {'action': 'initialize', 'baseline': 'original-commit',
                                           'source': 'simulated requesting-human conversation'}, now=0)


def accepted_fixture(root, feature):
    seed(root, feature)
    target = feature / 'tasks.md'
    target.write_text(target.read_text().replace('- [ ]', '- [X]'))
    for key in ('US1', 'US2'):
        delivery.transition(root, feature, {'action': 'present', 'checkpoint': key,
            'checks': ['artifacts/passing.json'], 'basisPaths': ['src/Create.txt' if key == 'US1' else 'src/Export.txt'],
            'entryPoint': 'fixture supported interface', 'preparedData': 'fictional account/data',
            'walkthrough': 'exercise fictional integrated outcome', 'expected': 'owned useful outcome',
            'limitations': 'Simulated decisions only; no real human acceptance'}, now=0)
        delivery.transition(root, feature, {'action': 'decision', 'checkpoint': key, 'actor': 'requester',
            'verdict': 'accepted', 'source': 'simulated explicit fixture reviewer decision'}, now=0)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='story-review-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.feature = self.root / 'specs/001-record'
        self.feature.mkdir(parents=True)
        seed(self.root, self.feature)
        self.now = 0

    def act(self, action, **fields):
        return delivery.transition(self.root, self.feature, {'action': action, **fields}, self.now)

    def complete(self, *ids):
        target = self.feature / 'tasks.md'
        text = target.read_text()
        for identifier in ids:
            text = text.replace('- [ ] ' + identifier, '- [X] ' + identifier)
        target.write_text(text)

    def present(self, key='US1'):
        self.complete(*delivery.load_delivery(self.feature)['stories'][key]['taskIds'])
        return self.act('present', checkpoint=key, checks=['artifacts/passing.json'],
                        basisPaths=['src/Create.txt' if key == 'US1' else 'src/Export.txt'],
                        entryPoint='http://localhost/records', preparedData='fixture owner account',
                        walkthrough='Create, reopen, exercise failure', expected='Owned persistent result',
                        limitations='Simulated external responses; no real human acceptance')

    def accept(self, key='US1'):
        return self.act('decision', checkpoint=key, verdict='accepted', actor='requester', source='simulated explicit acceptance')

    def scoped_presentation(self):
        self.complete('T001', 'T002')
        (self.root / 'eng').mkdir(exist_ok=True)
        self.graph = two_apps(ROOT)
        self.composition = self.root / 'eng/foundation-composition.json'
        self.composition.write_text(json.dumps(self.graph))
        self.scope = {'schemaVersion': 1, 'inputs': [
            {'path': 'src/Create.txt', 'kind': 'file'},
            {'path': 'eng/foundation-composition.json', 'kind': 'foundation-composition', 'version': 1,
             'hosts': ['application-host'], 'environments': ['development']}]}
        self.act('present', checkpoint='US1', checks=['artifacts/passing.json'],
            basisPaths=['src/Create.txt', 'eng/foundation-composition.json'], materialScope=self.scope,
            entryPoint='fixture', preparedData='fixture', walkthrough='fixture', expected='fixture', limitations='fixture')
        self.accept()

    def large_presentation(self):
        self.complete('T001', 'T002')
        paths = []
        for index in range(121):
            name = 'src/review/' + str(index).zfill(3) + '-' + 'owned-' * 7 + '.txt'
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('Fictional original source ' + str(index))
            paths.append(name)
        self.act('present', checkpoint='US1', checks=['artifacts/passing.json'], basisPaths=paths,
                 entryPoint='fixture', preparedData='fixture', walkthrough='fixture', expected='fixture', limitations='fixture')
        return paths

    def stored_checkpoint(self):
        return json.loads(delivery.CURRENT.search((self.feature / 'tasks.md').read_text())[1])

    def replace_stored_checkpoint(self, saved):
        path = self.feature / 'tasks.md'
        path.write_text(delivery.CURRENT.sub(lambda _: '<!-- program-kit:current-checkpoint '
                       + json.dumps(saved, separators=(',', ':')) + ' -->', path.read_text(), count=1))

    def test_repeated_large_bases_are_interned_without_losing_human_provenance(self):
        paths = self.large_presentation()
        for index in range(60):
            self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'],
                     source='simulated explicit owner continuation ' + str(index))
        expanded = delivery.current(self.feature)
        original = copy.deepcopy(expanded['delivery']['checkpoints']['US1']['decisions'])
        stored = self.stored_checkpoint()
        self.assertEqual(3, stored['version'])
        self.assertLess(len(json.dumps(stored).encode()), 65536)
        self.assertGreater(len(json.dumps(expanded).encode()), 65536)
        self.assertEqual(2, len(stored['delivery']['basisStorage']['values']))
        self.assertEqual(60, len(original))
        self.assertEqual(121, len(original[0]['basis']))
        (self.root / paths[0]).write_text('changed material fixture')
        self.act('present', checkpoint='US1', checks=['artifacts/passing.json'], basisPaths=paths,
                 entryPoint='fixture', preparedData='fixture', walkthrough='fixture', expected='fixture', limitations='fixture')
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated changed review')
        self.assertEqual(original, delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions'][:60])
        self.assertEqual(3, len(self.stored_checkpoint()['delivery']['basisStorage']['values']))
        self.assertEqual('original-commit', delivery.current(self.feature)['baseline'])

    def test_expanded_bases_are_independent_and_legacy_state_migrates_atomically(self):
        self.large_presentation()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated owner')
        saved = delivery.current(self.feature)
        review = saved['delivery']['checkpoints']['US1']
        review['decisions'] *= 8
        saved['delivery']['clock']['accountingCorrections'] = [{'identity': 'retained-fixture-correction', 'seconds': 936.331586}]
        self.replace_stored_checkpoint(saved)  # Legacy inline state larger than the old limit.
        before = (self.feature / 'tasks.md').read_bytes()
        self.assertGreater(len(before), 65536)
        state = delivery.load_delivery(self.feature)
        with patch.object(delivery.os, 'replace', side_effect=OSError('fixture interrupted atomic migration')):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                delivery.persist(self.feature, state)
        self.assertEqual(before, (self.feature / 'tasks.md').read_bytes())
        delivery.persist(self.feature, state)
        self.assertEqual(state, delivery.load_delivery(self.feature))
        independently_expanded = delivery.load_delivery(self.feature)
        basis = independently_expanded['checkpoints']['US1']['presentation']['basis']
        basis[next(iter(basis))] = 'fixture changed copy'
        self.assertNotEqual(basis, independently_expanded['checkpoints']['US1']['decisions'][0]['basis'])

    def test_missing_tampered_or_mixed_stored_bases_are_refused_without_writes(self):
        self.present(); self.accept()
        original = self.stored_checkpoint()
        for corruption in ('missing', 'tampered', 'mixed'):
            with self.subTest(corruption=corruption):
                saved = copy.deepcopy(original)
                site = saved['delivery']['checkpoints']['US1']['presentation']
                if corruption == 'missing':
                    site['basisRef'] = '0' * 64
                elif corruption == 'tampered':
                    saved['delivery']['basisStorage']['values'][site['basisRef']]['src/Create.txt'] = 'changed hash'
                else:
                    site['basis'] = {'src/Create.txt': 'ambiguous inline basis'}
                self.replace_stored_checkpoint(saved)
                before = (self.feature / 'tasks.md').read_bytes()
                with self.assertRaisesRegex(ValueError, 'retained basis|inline/reference'):
                    delivery.current(self.feature)
                self.assertEqual(before, (self.feature / 'tasks.md').read_bytes())

    def test_summary_and_retained_history_limits_refuse_without_discarding_state(self):
        before = (self.feature / 'tasks.md').read_bytes()
        saved = delivery.current(self.feature)
        saved['outcome'] = 'x' * 8192
        with self.assertRaisesRegex(ValueError, '8192'):
            delivery.save_current(self.feature, saved)
        state = delivery.load_delivery(self.feature)
        state['clock']['retainedFixtureHistory'] = 'x' * delivery.RETAINED_LIMIT
        with self.assertRaisesRegex(ValueError, '1048576'):
            delivery.persist(self.feature, state)
        self.assertEqual(before, (self.feature / 'tasks.md').read_bytes())

    def test_basis_expansion_is_bounded_even_when_stored_state_is_small(self):
        self.present(); self.accept()
        saved = delivery.current(self.feature)
        review = saved['delivery']['checkpoints']['US1']
        huge = {'fixture': 'x' * 500000}
        review['presentation']['basis'] = huge
        review['decisions'] = [dict(review['decisions'][0], basis=huge) for _ in range(40)]
        stored = delivery._store_bases(saved)
        self.assertLess(len(json.dumps(stored).encode()), delivery.RETAINED_LIMIT)
        self.replace_stored_checkpoint(stored)
        with self.assertRaisesRegex(ValueError, 'expansion exceeds'):
            delivery.current(self.feature)

    def test_owner_named_continuation_survives_material_changes_but_not_acceptance(self):
        self.present()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated owner continue export')
        decisions = copy.deepcopy(delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions'])
        (self.root / 'src/Create.txt').write_text('changed shared implementation')
        self.act('status')
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual(('deferred', 'pending', True), (review['human'], review['engineering'], review['stale']))
        self.assertEqual(decisions, review['decisions'])
        self.act('start', operation='export')
        for operation in ('integrate', 'unknown-operation'):
            with self.assertRaises(ValueError):
                self.act('start', operation=operation)
        with self.assertRaisesRegex(ValueError, 'remain due'):
            delivery.guard(self.root, self.feature, closure=True)
        with self.assertRaisesRegex(ValueError, 'fresh checkpoint'):
            self.accept()

    def test_owner_can_defer_an_existing_stale_review_but_requester_cannot(self):
        self.present(); self.accept()
        (self.root / 'src/Create.txt').write_text('changed original basis')
        self.act('status')
        with self.assertRaisesRegex(ValueError, 'fresh checkpoint'):
            self.act('decision', checkpoint='US1', verdict='deferred', actor='requester', permits=['export'], source='simulated requester')
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated explicit stale owner deferral')
        self.act('start', operation='export')

    def test_requester_deferral_loses_fresh_authority_after_source_changes(self):
        self.present()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='requester', permits=['export'], source='simulated requester')
        (self.root / 'src/Create.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Pause'):
            self.act('start', operation='export')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_owner_continuation_preserves_scoped_raw_freshness_and_rejects_failed_checks(self):
        self.scoped_presentation()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated owner')
        self.graph['resources']['assessment-shell']['name'] = 'changed sibling'
        self.composition.write_text(json.dumps(self.graph))
        self.act('start', operation='export')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['engineering'])
        (self.root / 'artifacts/passing.json').write_text('{"status":"failed","exitCode":1}')
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            self.act('start', operation='export')

    def test_changed_operation_meaning_revokes_only_relevant_active_permits(self):
        self.present()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['export'], source='simulated owner')
        self.act('start', operation='export'); self.now = 10; self.act('status')
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('Export record |', 'Export a changed approved record |', 1))
        with self.assertRaisesRegex(ValueError, 'scope decision'):
            self.act('start', operation='export')
        self.act('scope', actor='owner', source='simulated changed operation meaning', stories=['US2'])
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual([], review['permits'])
        self.assertEqual(['export'], review['decisions'][-1]['permits'])
        self.assertTrue(delivery.load_delivery(self.feature)['clock']['waiting'])
        self.now = 70; self.act('status')
        self.assertEqual(10, delivery.load_delivery(self.feature)['stories']['US2']['seconds'])
        with self.assertRaisesRegex(ValueError, 'Pause'):
            self.act('start', operation='export')

    def test_permitted_active_work_counts_once_and_explicit_wait_and_suspend_do_not(self):
        self.act('start', operation='create'); self.complete('T001'); self.act('start', operation='integrate')
        self.now = 10; self.present()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['integrate'], source='simulated owner continue active work')
        self.assertFalse(delivery.load_delivery(self.feature)['clock']['waiting'])
        self.now = 70; self.act('status'); self.act('status')
        self.assertEqual(70, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])
        self.act('wait'); self.now = 170; self.act('resume')
        self.now = 200; self.act('suspend'); self.now = 400; self.act('resume')
        self.assertEqual(100, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])
        (self.root / 'src/Create.txt').write_text('changed while still permitted')
        self.now = 410; self.act('status')
        self.assertEqual(110, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])

    def test_other_due_checkpoint_still_blocks_active_work_and_clock(self):
        self.act('start', operation='create'); self.complete('T001'); self.act('start', operation='integrate'); self.present()
        self.act('early-checkpoint', actor='owner', source='simulated owner early review', checkpoint='early', story='US1', taskIds=['T001'])
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner', permits=['integrate'], source='simulated owner')
        self.assertTrue(delivery.load_delivery(self.feature)['clock']['waiting'])
        self.now = 60; self.act('resume'); self.now = 120; self.act('status')
        self.assertEqual(0, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])
        with self.assertRaisesRegex(ValueError, 'early'):
            self.act('start', operation='integrate')

    def test_scoped_sibling_host_change_retains_human_decision_but_blocks_stale_engineering(self):
        self.scoped_presentation()
        decision = copy.deepcopy(delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions'])
        self.graph['resources']['assessment-shell']['name'] = 'changed-assessment'
        self.composition.write_text(json.dumps(self.graph, indent=2))
        self.act('status')
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual('accepted', review['human']); self.assertEqual('pending', review['engineering'])
        self.assertEqual(decision, review['decisions'])
        with self.assertRaisesRegex(ValueError, 'engineering checks remain due'):
            self.act('start', operation='export')
        self.act('engineering', checkpoint='US1', checks=['artifacts/passing.json'])
        self.act('start', operation='export')
        self.assertEqual(decision, delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions'])

    def test_canonical_formatting_change_retains_acceptance_without_rewriting_approval(self):
        self.scoped_presentation()
        prior = copy.deepcopy(delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions'])
        self.composition.write_text(json.dumps(self.graph, indent=4))
        self.act('engineering', checkpoint='US1', checks=['artifacts/passing.json'])
        self.act('present', checkpoint='US1', checks=['artifacts/passing.json'],
            basisPaths=['src/Create.txt', 'eng/foundation-composition.json'], materialScope=self.scope,
            entryPoint='fixture', preparedData='fixture', walkthrough='fixture', expected='fixture', limitations='fixture')
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual('accepted', review['human']); self.assertEqual(prior, review['decisions'])

    def test_material_shared_host_authentication_change_reopens_only_affected_review(self):
        self.scoped_presentation()
        self.graph['resources']['product-identity']['session'] = {'idleMinutes': 25, 'absoluteMinutes': 480}
        self.composition.write_text(json.dumps(self.graph))
        self.act('status')
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual('pending', review['human']); self.assertTrue(review['stale'])
        self.assertEqual('accepted', review['decisions'][-1]['verdict'])

    def test_unknown_duplicate_or_deleted_shared_input_cannot_claim_unchanged(self):
        for content in ('{"schemaVersion":2,"schemaVersion":2}', '{"schemaVersion":999}', None):
            with self.subTest(content=content):
                self.scoped_presentation()
                if content is None:
                    self.composition.unlink()
                else:
                    self.composition.write_text(content)
                self.act('status')
                self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_changed_scope_does_not_promote_historical_acceptance(self):
        self.scoped_presentation()
        value = delivery.load_delivery(self.feature)
        value['checkpoints']['US1']['materialScope']['inputs'][1]['hosts'] = ['assessment-host']
        delivery.persist(self.feature, value)
        self.act('status')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_shared_private_mount_is_material_even_without_business_source_change(self):
        self.scoped_presentation()
        self.graph['authority'] = {'architectureMap': 'docs/architecture/map.json', 'decisionIds': ['fixture']}
        self.graph['resources']['private-store'] = {'kind': 'privateFiles', 'ownerRef': 'application'}
        self.graph['environments']['development']['resources']['private-store'] = {'directory': 'artifacts/private-evidence/policies'}
        self.graph['bindings'].append({'kind': 'privateFiles', 'filesRef': 'private-store', 'hostRef': 'application-host',
            'shellRef': 'application-shell', 'featureRef': 'feature-0', 'setting': 'Root'})
        self.composition.write_text(json.dumps(self.graph))
        self.act('status')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_verification_sibling_group_requires_current_checks_without_new_human_decision(self):
        import review_material
        file = self.root / 'eng/verification.json'; file.parent.mkdir(exist_ok=True)
        value = {'schemaVersion': 1, 'testGroups': [{'id': 'create', 'projects': ['tests/Create.csproj'], 'inputs': ['src/Create/**']}]}
        file.write_text(json.dumps(value))
        scope = {'schemaVersion': 1, 'inputs': [{'path': 'eng/verification.json', 'kind': 'verification', 'version': 1,
                                               'projects': ['tests/Create.csproj']}]}
        original = review_material.basis(self.root, scope, ['eng/verification.json'])
        value['testGroups'].append({'id': 'export', 'projects': ['tests/Export.csproj'], 'inputs': ['src/Export/**']})
        file.write_text(json.dumps(value))
        self.assertEqual(original, review_material.basis(self.root, scope, ['eng/verification.json']))
        value['testGroups'][0]['reuse'] = False; file.write_text(json.dumps(value))
        self.assertNotEqual(original, review_material.basis(self.root, scope, ['eng/verification.json']))
        value['unknownFutureBehavior'] = True; file.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'unknown verification'):
            review_material.basis(self.root, scope, ['eng/verification.json'])

    def test_failed_checks_cannot_renew_scoped_engineering(self):
        self.scoped_presentation()
        self.composition.write_text(json.dumps(self.graph, indent=2))
        (self.root / 'artifacts/passing.json').write_text('{"status":"failed","exitCode":1}')
        with self.assertRaisesRegex(ValueError, 'Failed/incomplete'):
            self.act('engineering', checkpoint='US1', checks=['artifacts/passing.json'])
        self.act('status')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['engineering'])

    def test_projection_implementation_change_reopens_review(self):
        self.scoped_presentation()
        import review_material
        prior = review_material.basis
        def changed(*arguments):
            result = prior(*arguments); result['implementationSha256'] = 'changed-fixture'; return result
        with patch.object(review_material, 'basis', side_effect=changed):
            self.act('status')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_active_environment_switch_cannot_hide_behind_old_environment_projection(self):
        self.scoped_presentation()
        self.graph['environments']['test'] = copy.deepcopy(self.graph['environments']['development'])
        self.graph['defaultEnvironment'] = 'test'
        self.composition.write_text(json.dumps(self.graph))
        self.act('status')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_operations_progress_without_review_and_actual_dependencies_remain(self):
        self.act('start', operation='create')
        with self.assertRaisesRegex(ValueError, 'enabling prerequisites'):
            self.act('start', operation='integrate')
        self.complete('T001')
        self.act('start', operation='integrate')
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])
        with self.assertRaisesRegex(ValueError, 'enabling prerequisites|current story'):
            self.act('start', operation='export')

    def test_completed_boxes_and_engineering_do_not_manufacture_human_acceptance(self):
        self.act('start', operation='create'); self.complete('T001', 'T002')
        with self.assertRaisesRegex(ValueError, 'Pause'):
            self.act('start', operation='export')
        self.act('engineering', checkpoint='US1', checks=['artifacts/passing.json'])
        with self.assertRaisesRegex(ValueError, 'remain due'):
            delivery.guard(self.root, self.feature, closure=True)
        self.assertEqual('pending', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_pause_acceptance_and_repair_scope(self):
        self.act('start', operation='create'); self.complete('T001')
        self.act('start', operation='integrate'); self.present()
        for operation in ('create', 'export'):
            with self.assertRaisesRegex(ValueError, 'Pause'):
                self.act('start', operation=operation)
        self.act('start', operation='integrate', purpose='repair')
        self.act('decision', checkpoint='US1', verdict='changes requested', actor='requester', source='simulated corrections')
        with self.assertRaisesRegex(ValueError, 'Pause'):
            delivery.guard(self.root, self.feature)
        self.accept(); self.act('start', operation='export')
        self.assertEqual('accepted', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_bounded_deferral_permits_only_named_work_and_remains_due_at_handoff(self):
        self.present()
        self.act('decision', checkpoint='US1', verdict='deferred', actor='requester',
                 source='simulated defer this checkpoint for export', permits=['export'])
        self.act('start', operation='export')
        with self.assertRaisesRegex(ValueError, 'Pause'):
            self.act('start', operation='create')
        self.complete('T003')
        with patch.object(phases, 'execute', side_effect=AssertionError('Must not bypass review')):
            for handoff in (False, True):
                with self.assertRaisesRegex(ValueError, 'remain due'):
                    phases.finish(self.root, self.feature, handoff)
        with self.assertRaisesRegex(ValueError, 'Broader batch'):
            self.act('decision', checkpoint='US1', verdict='deferred', actor='requester',
                     source='simulated', permits=['export', 'integrate'])
        self.act('decision', checkpoint='US1', verdict='deferred', actor='owner',
                 source='simulated owner bounded batch', permits=['export', 'integrate'])
        self.act('start', operation='integrate', purpose='repair')
        self.assertEqual('US1', delivery.load_delivery(self.feature)['active']['story'])

    def test_early_checkpoint_requires_agreement_and_stops_next_operation(self):
        with self.assertRaisesRegex(ValueError, 'agreement'):
            self.act('early-checkpoint', checkpoint='early', story='US1', taskIds=['T001'])
        self.act('early-checkpoint', actor='owner', source='simulated agreed early product question',
                 checkpoint='early', story='US1', taskIds=['T001'])
        self.act('start', operation='create'); self.complete('T001')
        with self.assertRaisesRegex(ValueError, 'Pause'):
            self.act('start', operation='integrate')

    def test_progress_replacement_retains_all_reviews_roles_baseline_and_failures(self):
        self.present(); self.accept()
        draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Export', 'next': 'Verify', 'failures': ['required provider failure']})
        saved = delivery.load_delivery(self.feature)
        for _ in range(5):
            draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Export', 'next': 'Repair'})
        self.assertEqual(saved, delivery.load_delivery(self.feature))
        self.assertEqual(['required provider failure'], draft.current(self.feature)['failures'])
        self.assertEqual(1, (self.feature / 'tasks.md').read_text().count('program-kit:current-checkpoint'))
        with self.assertRaisesRegex(ValueError, 'technical failures'):
            self.present('US2')

    def test_material_changes_reopen_only_affected_story_unrelated_tests_preserve_acceptance(self):
        self.present(); self.accept(); self.present('US2'); self.accept('US2')
        (self.root / 'tests').mkdir(); (self.root / 'tests/Unrelated.txt').write_text('test correction')
        delivery.guard(self.root, self.feature, closure=True)
        (self.root / 'src/Create.txt').write_text('changed ownership/persistence')
        with self.assertRaisesRegex(ValueError, 'US1'):
            delivery.guard(self.root, self.feature, closure=True)
        reviews = delivery.load_delivery(self.feature)['checkpoints']
        self.assertEqual('pending', reviews['US1']['human'])
        self.assertEqual('accepted', reviews['US2']['human'])
        self.assertEqual(1, len(reviews['US1']['decisions']))
        with self.assertRaisesRegex(ValueError, 'fresh checkpoint'):
            self.accept()

    def test_unchanged_represented_story_preserves_original_human_source(self):
        self.present(); self.accept()
        prior = delivery.load_delivery(self.feature)['checkpoints']['US1']['decisions']
        self.present()
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        self.assertEqual('accepted', review['human'])
        self.assertEqual(prior, review['decisions'])

    def test_early_review_reuse_requires_complete_unchanged_story_coverage(self):
        self.act('early-checkpoint', actor='owner', source='simulated agreed early review',
                 checkpoint='early', story='US1', taskIds=['T001'])
        self.complete('T001')
        self.act('present', checkpoint='early', checks=['artifacts/passing.json'], basisPaths=['src/Create.txt'],
                 entryPoint='fixture runnable interface', preparedData='fixture account', walkthrough='create',
                 expected='owned result', limitations='simulation')
        self.act('decision', checkpoint='early', actor='requester', source='simulated explicit review', verdict='accepted')
        with self.assertRaisesRegex(ValueError, 'complete story'):
            self.act('reuse-review', **{'from': 'early'}, checkpoint='US1')
        self.complete('T002')
        self.act('early-checkpoint', actor='owner', source='simulated agreed full-story review',
                 checkpoint='early-full', story='US1', taskIds=['T001', 'T002'])
        self.act('present', checkpoint='early-full', checks=['artifacts/passing.json'], basisPaths=['src/Create.txt'],
                 entryPoint='fixture runnable interface', preparedData='fixture account', walkthrough='create/reopen',
                 expected='complete owned result', limitations='simulation')
        self.act('decision', checkpoint='early-full', actor='requester', source='simulated full-story review', verdict='accepted')
        result = self.act('reuse-review', **{'from': 'early-full'}, checkpoint='US1')
        self.assertEqual('accepted', result['delivery']['checkpoints']['US1']['human'])
        self.assertEqual('early-full', result['delivery']['checkpoints']['US1']['reusedFrom'])

    def test_failed_or_changed_check_artifacts_cannot_be_waived(self):
        target = self.root / 'artifacts/passing.json'
        target.write_text('{"status":"failed","exitCode":1}')
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            self.present()
        target.write_text('{"status":"completed","exitCode":0}')
        self.present()
        target.write_text('{"status":"interrupted","exitCode":130}')
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            self.accept()

    def test_suspension_retains_active_effort_without_charging_stopped_session(self):
        self.act('start', operation='create'); self.now = 90; self.act('suspend')
        self.now += 86400; self.act('resume'); self.now += 30; self.act('status')
        self.assertEqual(120, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])

    def test_malformed_state_and_clock_are_rejected_without_loss(self):
        state = delivery.load_delivery(self.feature)
        invalid = copy.deepcopy(state); invalid['clock']['at'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'clock'):
            delivery.persist(self.feature, invalid)
        self.assertEqual(state, delivery.load_delivery(self.feature))
        self.now = -1
        with self.assertRaisesRegex(ValueError, 'Clock moved backwards'):
            self.act('status')

    def test_explicit_owner_scope_update_reopens_only_affected_meaning_preserves_effort(self):
        self.act('early-checkpoint', actor='owner', source='simulated agreed early checkpoint',
                 checkpoint='early', story='US1', taskIds=['T001'])
        self.present(); self.accept()
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('Create owned record', 'Create approved owned record', 1))
        with self.assertRaisesRegex(ValueError, 'scope decision'):
            delivery.guard(self.root, self.feature)
        with self.assertRaisesRegex(ValueError, 'owner decision'):
            self.act('scope', stories=['US1'])
        self.act('scope', actor='owner', source='simulated new scope decision', stories=['US1'])
        self.assertTrue(delivery.load_delivery(self.feature)['checkpoints']['US1']['stale'])
        self.assertTrue(delivery.load_delivery(self.feature)['checkpoints']['early']['stale'])

    def test_clock_survives_resume_wait_and_repairs_warns_once_never_blocks_due_to_time(self):
        self.act('start', operation='create')
        self.now = 3601
        first = self.act('status')
        self.assertEqual(['create'], [warning['work'] for warning in first['warnings']])
        self.act('wait'); self.now += 86400; self.act('resume')
        self.assertEqual(3601, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])
        self.complete('T001'); self.act('start', operation='integrate')
        self.now += 3600
        second = self.act('status')
        self.assertEqual({'US1', 'integrate'}, {warning['work'] for warning in second['warnings']})
        self.assertEqual([], self.act('status')['warnings'])
        self.present(); self.now += 86400
        self.act('start', operation='integrate', purpose='repair'); self.now += 60; self.act('status')
        self.assertEqual(7261, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])
        with self.assertRaisesRegex(ValueError, 'owner'):
            self.act('budget', story='US1', minutes=180)
        self.act('budget', actor='owner', source='simulated budget revision', story='US1', minutes=180)
        self.assertEqual(7261, delivery.load_delivery(self.feature)['stories']['US1']['seconds'])

    def test_no_hook_preflight_finish_and_formal_handoff_consume_same_state(self):
        self.present()
        with self.assertRaisesRegex(ValueError, 'Pause'):
            phases.check(self.root, self.feature, 'implementation')
        progress = phases.finish(self.root, self.feature)
        self.assertFalse(progress['canProceed'])
        self.assertFalse(progress['acceptanceEstablished'])
        self.accept(); self.present('US2'); self.accept('US2')
        with patch.object(phases, 'execute', return_value={'acceptanceEstablished': False}) as execute:
            result = phases.finish(self.root, self.feature)
            self.assertTrue(result['humanReviewsPassed'])
            execute.assert_called_once()
        self.assertFalse(result['acceptanceEstablished'], 'Simulated reviews establish no real acceptance')

    def test_old_partial_feature_cannot_initialize_and_scaffold_first_graph_is_valid(self):
        draft.validate_operation_graph(story_tasks(), required=True)
        (self.feature / 'tasks.md').write_text(story_tasks().replace('- [ ] T001', '- [X] T001'))
        with patch.object(delivery, 'require_policy'), self.assertRaisesRegex(ValueError, 'old implementation'):
            self.act('initialize', baseline='new', source='simulated')

    def github(self, verdict='accepted'):
        self.present()
        user = {'id': 42, 'login': 'fixture-reviewer', 'type': 'User', 'html_url': 'https://github.com/fixture-reviewer'}
        with patch.object(delivery, 'github_read', return_value=user):
            # Explicit reader ensures mocked responses cannot become CLI decision evidence.
            verified = delivery.transition(self.root, self.feature, {'action': 'verify-reviewer', 'actor': 'owner',
                'source': 'simulated nomination', 'login': 'fixture-reviewer'}, self.now, reader=lambda host, endpoint: user)
            self.assertTrue(verified['assignmentPending'])
            delivery.transition(self.root, self.feature, {'action': 'assign', 'actor': 'owner', 'source': 'simulated nomination',
                'checkpoint': 'US1', 'role': 'reviewer', 'login': 'fixture-reviewer', 'confirmedId': 42, 'confirmation': 'simulated confirmed assignment'}, self.now,
                reader=lambda host, endpoint: user)
        reference = 'https://github.com/fixture/repo/issues/1#issuecomment-7'
        review = delivery.load_delivery(self.feature)['checkpoints']['US1']
        marker = {'feature': 'specs/001-record', 'checkpoint': 'US1', 'basis': delivery.review_digest(review['presentation']), 'verdict': verdict}
        return reference, {'user': user, 'html_url': reference, 'body': '<!-- program-kit:story-decision ' + json.dumps(marker) + ' -->'}

    def test_authenticated_exact_github_author_scope_and_outage(self):
        reference, record = self.github()
        request = {'action': 'decision', 'checkpoint': 'US1', 'verdict': 'accepted', 'reference': reference}
        for response in (dict(record, user={'id': 99}), dict(record, body='Approved'),
                         dict(record, body=record['body'].replace('US1', 'US2')), dict(record, body=record['body'] * 2)):
            result = delivery.transition(self.root, self.feature, request, self.now, reader=lambda host, endpoint: response)
            self.assertEqual('pending', result['status'])
            self.assertEqual('ready for review', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])
        result = delivery.transition(self.root, self.feature, request, self.now, reader=lambda host, endpoint: record)
        self.assertFalse(result['acceptanceEstablished'])
        self.assertEqual('accepted', result['delivery']['checkpoints']['US1']['human'])
        with patch.object(delivery, 'github_read', side_effect=OSError('offline')):
            self.act('status')
        self.assertEqual('accepted', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_github_outage_wrong_reviewer_and_explicit_owner_reassignment(self):
        reference, record = self.github()
        with self.assertRaisesRegex(ValueError, 'Wrong reviewer'):
            self.accept()
        request = {'action': 'decision', 'checkpoint': 'US1', 'verdict': 'accepted', 'reference': reference}
        def unavailable(host, endpoint):
            raise OSError('offline')
        self.assertEqual('pending', delivery.transition(self.root, self.feature, request, self.now, reader=unavailable)['status'])
        self.act('assign', actor='owner', source='simulated reassignment', checkpoint='US1', role='requester')
        self.accept()

    def test_github_stable_account_confirmation_and_deferral_scope_cannot_be_impersonated(self):
        reference, record = self.github(verdict='deferred')
        user = record['user']
        for role, confirmed in (('requester', 42), ('another-reviewer', 99)):
            with self.assertRaisesRegex(ValueError, 'conversation requester|stable account ID'):
                delivery.transition(self.root, self.feature, {'action': 'assign', 'actor': 'owner',
                    'source': 'simulated owner assignment', 'checkpoint': 'US1', 'role': role,
                    'login': user['login'], 'confirmation': 'simulated', 'confirmedId': confirmed}, self.now,
                    reader=lambda host, endpoint: user)
        request = {'action': 'decision', 'checkpoint': 'US1', 'verdict': 'deferred', 'reference': reference,
                   'actor': 'owner', 'permits': ['integrate', 'export']}
        # Even an authenticated delegated reviewer cannot claim owner powers by a request field.
        marker = json.loads(record['body'].split(' ', 2)[2].rsplit(' -->', 1)[0]); marker['permits'] = request['permits']
        record['body'] = '<!-- program-kit:story-decision ' + json.dumps(marker) + ' -->'
        with self.assertRaisesRegex(ValueError, 'Broader batch'):
            delivery.transition(self.root, self.feature, request, self.now, reader=lambda host, endpoint: record)

    def test_same_code_new_user_meaning_cannot_replay_old_authenticated_acceptance(self):
        reference, record = self.github()
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('Create owned record', 'Create approved owned record', 1))
        self.act('scope', actor='owner', source='simulated consequential outcome decision', stories=['US1'])
        self.present()
        result = delivery.transition(self.root, self.feature, {'action': 'decision', 'checkpoint': 'US1',
            'verdict': 'accepted', 'reference': reference}, self.now, reader=lambda host, endpoint: record)
        self.assertEqual('pending', result['status'])
        self.assertEqual('ready for review', delivery.load_delivery(self.feature)['checkpoints']['US1']['human'])

    def test_github_reference_reader_is_read_only_and_exact_url(self):
        reference, record = self.github()
        for fragment, resource in (('issuecomment-7', 'issues/comments/7'), ('pullrequestreview-7', 'pulls/1/reviews/7'), ('discussion_r7', 'pulls/comments/7')):
            url = reference.replace('issues', 'pull').split('#')[0] + '#' + fragment
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(dict(record, html_url=url)), '')) as run:
                delivery.github_reference(url)
                self.assertEqual(['gh', 'api', '--hostname', 'github.com', 'repos/fixture/repo/' + resource], run.call_args.args[0])

    def test_reset_preview_rejects_changed_ownership_shared_data_and_unselected_apply(self):
        files = ['specs/001-record/' + name for name in ('spec.md', 'plan.md', 'tasks.md')]
        request = {'feature': 'specs/001-record', 'reviewSource': 'simulated inventory review',
            'files': [{'path': name, 'owner': 'specs/001-record', 'sha256': hashlib.sha256((self.root / name).read_bytes()).hexdigest()} for name in files],
            'preserve': ['src/Export.txt']}
        self.assertEqual('preview', reset.reset(self.root, request)['status'])
        with self.assertRaisesRegex(ValueError, 'human selection'):
            reset.reset(self.root, request, True)
        damaged = copy.deepcopy(request); damaged['files'][0]['sha256'] = 'old'
        with self.assertRaisesRegex(ValueError, 'changed'):
            reset.reset(self.root, damaged)
        damaged = copy.deepcopy(request); damaged['files'][0]['owner'] = 'shared'
        with self.assertRaisesRegex(ValueError, 'exclusive'):
            reset.reset(self.root, damaged)

    def delete_request(self):
        intake = self.root / '.program-kit/specification-intake/DS01/brief.json'
        intake.parent.mkdir(parents=True); intake.write_text('{"request":"retained confirmed intent"}')
        (self.feature / 'contracts').mkdir()
        (self.feature / 'contracts/api.json').write_text('{"old":"phase output"}')
        files = [*self.feature.rglob('*'), self.root / 'src/Create.txt', self.root / 'src/Export.txt']
        return {'method': 'fresh-feature-delete-v1', 'feature': 'specs/001-record',
            'reviewSource': 'simulated complete owned inventory', 'selectionSource': 'simulated user delete entire unfinished attempt',
            'files': [{'path': target.relative_to(self.root).as_posix(), 'owner': 'specs/001-record',
                       'sha256': hashlib.sha256(target.read_bytes()).hexdigest()} for target in files if target.is_file()],
            'preserve': ['.program-kit/specification-intake/DS01/brief.json']}

    def test_delete_only_restart_removes_entire_spec_and_owned_code_without_content_archive(self):
        request = self.delete_request()
        for name in ('web/record/ui.ts', 'tests/record/lifecycle.test.ts'):
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('old exclusively owned generated work')
            request['files'].append({'path': name, 'owner': request['feature'],
                                     'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        intake = self.root / request['preserve'][0]; before = intake.read_bytes()
        shared = self.root / 'src/Shared.txt'; shared.write_text('shared owner')
        preview = reset.reset(self.root, request)
        self.assertEqual('preview', preview['status']); self.assertTrue(self.feature.is_dir())
        with patch.object(reset.shutil, 'copyfile', side_effect=AssertionError('Must not retain old content')):
            result = reset.reset(self.root, request, True)
        self.assertEqual('deleted', result['status']); self.assertNotIn('archive', result)
        self.assertFalse(self.feature.exists())
        self.assertTrue(all(not (self.root / row['path']).exists() for row in request['files']))
        self.assertFalse((self.root / '.program-kit/abandoned-features').exists())
        self.assertEqual(before, intake.read_bytes()); self.assertEqual('shared owner', shared.read_text())
        self.assertIn('execute specify itself', result['instruction'])
        self.assertIn('Do not consult or reuse', result['instruction'])

    def test_delete_only_restart_requires_complete_spec_inventory_and_unchanged_inputs(self):
        request = self.delete_request()
        alias = copy.deepcopy(request)
        alias['files'].append({'path': 'specs/001-record/../001-record/spec.md', 'owner': 'specs/001-record',
                              'sha256': hashlib.sha256((self.feature / 'spec.md').read_bytes()).hexdigest()})
        with self.assertRaisesRegex(ValueError, 'canonical'):
            reset.reset(self.root, alias, True)
        omitted = copy.deepcopy(request); omitted['files'] = [row for row in request['files'] if not row['path'].endswith('api.json')]
        with self.assertRaisesRegex(ValueError, 'every file'):
            reset.reset(self.root, omitted, True)
        self.assertTrue(self.feature.is_dir())
        (self.root / 'src/Create.txt').write_text('changed after selection')
        with self.assertRaisesRegex(ValueError, 'changed'):
            reset.reset(self.root, request, True)
        self.assertTrue((self.feature / 'spec.md').is_file())
        self.assertFalse((self.root / '.program-kit/abandoned-features').exists())

    def test_delete_only_cli_removes_attempt_without_an_archive(self):
        request = self.delete_request()
        content = self.root / 'delete-request.json'; content.write_text(json.dumps(request))
        result = subprocess.run([sys.executable, str(Path(delivery.__file__).resolve()), 'reset',
            '--repository', str(self.root), '--feature-dir', 'specs/001-record', '--content-file', str(content), '--apply'],
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('deleted', json.loads(result.stdout)['status'])
        self.assertFalse(self.feature.exists())
        self.assertFalse((self.root / '.program-kit/abandoned-features').exists())

    def test_historical_archive_recipe_retains_its_original_behavior(self):
        request = self.delete_request(); request['method'] = 'fresh-story-delivery-v1'
        result = reset.reset(self.root, request, True)
        self.assertEqual('abandoned', result['status'])
        archive = self.root / result['archive']
        self.assertTrue(all(hashlib.sha256((archive / row['path']).read_bytes()).hexdigest() == row['sha256']
                            for row in request['files']))


if __name__ == '__main__':
    unittest.main()

"""History, scoped revision, attributable review and recoverable authority transitions."""
from copy import deepcopy, copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from validate_delivery_azure import FakeProvider, OWNER, REPO
import validate_delivery_azure as fixtures
import azure_history as history
import azure_reconcile as reconcile
import azure_revision as revision
import azure_transitions as transitions
import azure_planning as planning
import azure_activation as activation
from azure_transport import AzureError
from delivery_contract import authority


class ReconciliationTests(unittest.TestCase):
    graph = fixtures.AzurePlanningTests.graph
    configured_repository = fixtures.AzurePlanningTests.configured_repository

    def setUp(self):
        self.provider = FakeProvider()
        proposal = planning.prepare(self.provider, self.graph())
        planning.approve(self.provider, proposal, authority.digest(proposal), 'approved synthetic graph')
        planning.apply(self.provider, proposal['id'])
        self.original_proposal = proposal

    def decisions(self, report, classification='baseline'):
        return [{'nativeId': f['nativeId'], 'classification': classification, 'reason': 'Explicit fixture review',
            'affectedKeys': f['provisionalImpact'], 'technicalRevisionRequired': classification in ('business', 'technical')}
            for f in report['findings']]

    def accept(self, report, decisions=None):
        proposal = reconcile.propose_review(self.provider, report['id'], decisions or self.decisions(report))
        for role in proposal['requiredRoles']:
            reconcile.approve_review(self.provider, proposal, authority.digest(proposal), 'approved fixture decision', role)
        reconcile.apply_review(self.provider, proposal['id'])
        return proposal

    def baseline(self):
        self.accept(reconcile.sync(self.provider, ['E1']))

    def change(self, identity=1, text='Changed human scope'):
        current = self.provider.item(identity)
        self.provider.update(identity, current['rev'], {'System.Description': text}, [])

    def test_observation_does_not_accept_new_business_basis(self):
        report = reconcile.sync(self.provider, ['E1'])
        self.assertEqual(len(report['findings']), 4)
        self.assertEqual(reconcile.ledger(self.provider.state)['accepted'], {})
        with self.assertRaisesRegex(AzureError, 'initial history basis'):
            reconcile.check_scoped(self.provider, self.provider.state, 'R1')

    def test_legacy_unfinished_proposal_cannot_bypass_history_review(self):
        proposal = planning.prepare(self.provider, [{'key': 'E2', 'kind': 'epic', 'fields': self.graph()[0]['fields']}])
        planning.approve(self.provider, proposal, authority.digest(proposal), 'accepted Phase 2 fixture')
        stored = self.provider.state['proposals'][proposal['id']]
        stored['proposal'].pop('historyBasis')
        stored['digest'] = authority.digest(stored['proposal'])
        before = self.provider.created
        with self.assertRaisesRegex(AzureError, 'legacy proposal'):
            planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.created, before)

    def test_business_revision_needs_both_roles_and_stays_technically_pending(self):
        self.baseline()
        self.change()
        report = reconcile.sync(self.provider, ['E1'])
        review = reconcile.propose_review(self.provider, report['id'], self.decisions(report, 'business'))
        reconcile.approve_review(self.provider, review, authority.digest(review), 'business approved', 'business')
        with self.assertRaisesRegex(AzureError, 'all exact role approvals'):
            reconcile.apply_review(self.provider, review['id'])
        reconcile.approve_review(self.provider, review, authority.digest(review), 'technical assessed', 'technical')
        reconcile.apply_review(self.provider, review['id'])
        self.assertEqual(reconcile.check_scoped(self.provider, self.provider.state, 'R1'), [review['id']])
        self.assertEqual(self.provider.items[1]['fields']['System.Description'], 'Changed human scope')

    def test_no_impact_review_requires_reason_and_cannot_drop_changed_work(self):
        report = reconcile.sync(self.provider, ['E1'])
        decisions = self.decisions(report)
        decisions[0]['reason'] = ''
        with self.assertRaises(AzureError):
            reconcile.propose_review(self.provider, report['id'], decisions)
        decisions[0]['reason'] = 'Explained'
        decisions[0]['affectedKeys'] = []
        with self.assertRaisesRegex(AzureError, 'omit the changed work'):
            reconcile.propose_review(self.provider, report['id'], decisions)

    def test_edit_then_revert_remains_a_finding_and_invalidates_plan(self):
        self.baseline()
        entries = [{'key': 'E1', 'kind': 'epic', 'nativeId': 1, 'fields': {'System.Title': 'Reviewed rename'}}]
        proposal = planning.prepare(self.provider, entries)
        original = self.provider.items[1]['fields']['System.Description']
        self.change(text='Temporary changed requirement')
        self.change(text=original)
        report = reconcile.sync(self.provider, ['E1'])
        self.assertIn(1, [f['nativeId'] for f in report['findings']])
        with self.assertRaises(AzureError):
            planning.approve(self.provider, proposal, authority.digest(proposal), 'stale approval')

    def test_comment_edit_or_deletion_invalidates_review(self):
        self.baseline()
        self.provider.comments[1] = [{'comment': {'id': 10, 'version': 1, 'text': 'Question'}, 'versions': [{'version': 1, 'text': 'Question'}]}]
        report = reconcile.sync(self.provider, ['E1'])
        review = reconcile.propose_review(self.provider, report['id'], self.decisions(report, 'feedback'))
        self.provider.comments[1][0]['comment'].update(version=2, isDeleted=True)
        with self.assertRaisesRegex(AzureError, 'history changed'):
            reconcile.approve_review(self.provider, review, authority.digest(review), 'old comment approved', 'technical')

    def test_incomplete_history_stays_unknown_and_never_becomes_ready(self):
        self.baseline()
        original = self.provider.evidence
        def incomplete(identity):
            result = original(identity)
            if identity == 3:
                result['coverage']['comments'], result['status'] = False, 'incomplete'
            return result
        with patch.object(self.provider, 'evidence', side_effect=incomplete):
            report = reconcile.sync(self.provider, ['R1'])
            with self.assertRaises(AzureError):
                self.accept(report)
            with self.assertRaisesRegex(AzureError, 'unavailable history'):
                reconcile.check_scoped(self.provider, self.provider.state, 'R1')
        self.assertTrue(reconcile.ledger(self.provider.state)['accepted']['3']['snapshot']['coverage']['comments'])

    def test_changed_requirement_does_not_block_unrelated_sibling(self):
        proposal = planning.prepare(self.provider, [{'key': 'R2', 'kind': 'requirement', 'parent': 'F1', 'fields': self.graph()[2]['fields']}])
        planning.approve(self.provider, proposal, authority.digest(proposal), 'another accepted requirement')
        planning.apply(self.provider, proposal['id'])
        self.baseline()
        self.change(3)
        with self.assertRaises(AzureError):
            reconcile.check_scoped(self.provider, self.provider.state, 'R1')
        self.assertEqual(reconcile.check_scoped(self.provider, self.provider.state, 'R2'), [])

    def test_repeated_apply_preserves_review_and_pending_revision(self):
        self.baseline()
        self.change(3)
        report = reconcile.sync(self.provider, ['R1'])
        review = self.accept(report, self.decisions(report, 'business'))
        generation = self.provider.generation
        reconcile.apply_review(self.provider, review['id'])
        self.assertEqual(self.provider.generation, generation)

    def test_history_offset_paging_continues_after_short_page(self):
        rows = [{'id': identity} for identity in range(1, 4)]
        api = SimpleNamespace(call=lambda method, path, **kwargs: {'value': rows[kwargs['query']['$skip']:kwargs['query']['$skip'] + 1]})
        self.assertEqual(history.offset_pages(api, '/history'), rows)
        api.call = lambda *args, **kwargs: {'value': [{'id': 1}]}
        with self.assertRaisesRegex(AzureError, 'repeated an identity'):
            history.offset_pages(api, '/history')

    def test_missing_coverage_stream_cannot_claim_complete(self):
        self.assertFalse(history.complete({'status': 'observed', 'coverage': {}}))
        self.assertFalse(history.complete({'status': 'observed', 'coverage': {'item': True, 'updates': True}}))

    def test_comment_body_pagination_and_all_versions(self):
        seen = []
        def call(method, path, **kwargs):
            seen.append(kwargs)
            if path.endswith('/versions'):
                return [{'version': 1, 'text': 'Original'}, {'version': 2, 'text': 'Edited'}]
            if kwargs['query'].get('continuationToken'):
                return {'comments': [], 'totalCount': 1}
            return {'comments': [{'id': 1, 'version': 2, 'isDeleted': True}], 'continuationToken': 'next', 'totalCount': 1}
        self.provider.api.call = call
        result = history.comments(self.provider, 1)
        self.assertTrue(result[0]['comment']['isDeleted'])
        self.assertEqual(len(result[0]['versions']), 2)
        self.assertEqual(seen[0]['query']['includeDeleted'], 'true')
        self.assertEqual(seen[-1]['query']['continuationToken'], 'next')

    def test_comment_version_gap_is_not_complete_history(self):
        self.provider.api.call = lambda method, path, **kwargs: ([{'version': 2}] if path.endswith('/versions') else
            {'comments': [{'id': 1, 'version': 2}]})
        with self.assertRaisesRegex(AzureError, 'version history has a gap'):
            history.comments(self.provider, 1)

    def test_missing_item_is_unknown_without_positive_deletion_provenance(self):
        with patch.object(self.provider, 'item', side_effect=AzureError('missing', 404)):
            self.provider.api.call = lambda *args, **kwargs: {'id': 99}
            self.assertEqual(history.read(self.provider, 99)['status'], 'unknown')
            self.provider.api.call = lambda *args, **kwargs: {'id': 99, 'deletedDate': '2026-09-12', 'deletedBy': {'id': OWNER}}
            self.assertEqual(history.read(self.provider, 99)['status'], 'deleted')

    def active(self):
        root, binding = self.configured_repository()
        decision = activation.prepare(self.provider, root, binding)
        activation.apply(self.provider, root, decision, authority.digest(decision), 'fixture activation')
        return root, authority.read(root / authority.BINDING)

    def test_disconnect_requires_obligations_and_all_roles(self):
        root, binding = self.active()
        roots = {binding['repositoryId']: str(root)}
        with self.assertRaises(AzureError):
            transitions.prepare_disconnect(self.provider, binding['repositoryId'], roots, [])
        obligations = [{'key': 'R1', 'disposition': 'retired', 'recipientRepositoryId': None, 'reason': 'Synthetic work explicitly retired'}]
        proposal = transitions.prepare_disconnect(self.provider, binding['repositoryId'], roots, obligations)
        transitions.approve(self.provider, proposal, authority.digest(proposal), 'accepted handoff', 'business', roots)
        with self.assertRaises(AzureError):
            transitions.apply(self.provider, proposal['id'], roots)
        for role in ('technical', 'coordinator'):
            transitions.approve(self.provider, proposal, authority.digest(proposal), 'accepted handoff', role, roots)
        transitions.apply(self.provider, proposal['id'], roots)
        disconnected = authority.read(root / authority.BINDING)
        local_history = authority.read(root / authority.HISTORY)
        self.assertEqual(transitions.verify_disconnected(self.provider, root, disconnected, local_history)['authority'], 'local')
        self.assertEqual(local_history['records'][-1]['previousDigest'], authority.digest(local_history['records'][0]))

    def test_disconnect_recovers_between_binding_and_history_writes(self):
        root, binding = self.active()
        roots = {binding['repositoryId']: str(root)}
        proposal = transitions.prepare_disconnect(self.provider, binding['repositoryId'], roots,
            [{'key': 'R1', 'disposition': 'retired', 'recipientRepositoryId': None, 'reason': 'Retired synthetic obligation'}])
        for role in proposal['requiredRoles']:
            transitions.approve(self.provider, proposal, authority.digest(proposal), 'accepted', role, roots)
        original = transitions.write
        def interrupted(path, value):
            if path == root / authority.HISTORY:
                raise OSError('Interrupted before history persistence')
            return original(path, value)
        with patch.object(transitions, 'write', side_effect=interrupted):
            with self.assertRaises(OSError):
                transitions.apply(self.provider, proposal['id'], roots)
        self.assertEqual(self.provider.state['transitions'][proposal['id']]['state'], 'applying')
        transitions.apply(self.provider, proposal['id'], roots)
        saved = (root / authority.HISTORY).read_bytes()
        transitions.apply(self.provider, proposal['id'], roots)
        self.assertEqual((root / authority.HISTORY).read_bytes(), saved)

    def test_unknown_operations_prevent_disconnect(self):
        root, binding = self.active()
        self.provider.state['operations']['unknown'] = {'state': 'dispatched'}
        with self.assertRaisesRegex(AzureError, 'uncertain operations'):
            transitions.prepare_disconnect(self.provider, binding['repositoryId'], {binding['repositoryId']: str(root)}, [])

    def test_migration_preserves_old_policy_until_all_handoffs_approved(self):
        root, binding = self.active()
        roots = {binding['repositoryId']: str(root)}
        new_profile = deepcopy(self.provider.profile)
        new_profile['tagNamespace'] = 'reviewed'
        content = json.dumps(new_profile)
        source = {'repositoryId': REPO, 'commit': 'b' * 40, 'path': 'next.json', 'sha256': hashlib.sha256(content.encode()).hexdigest()}
        self.provider.files[(source['commit'], source['path'])] = content
        candidate = copy(self.provider)
        candidate.profile, candidate.settings = new_profile, new_profile['azure']
        with patch.object(transitions, 'AzureProvider', return_value=candidate):
            proposal = transitions.prepare_migration(self.provider, new_profile, source, roots)
            self.assertEqual(authority.read(root / authority.BINDING), binding)
            for role in proposal['requiredRoles']:
                transitions.approve(self.provider, proposal, authority.digest(proposal), 'accepted migration', role, roots)
            transitions.apply(self.provider, proposal['id'], roots)
        current = authority.read(root / authority.BINDING)
        self.assertEqual(current['profile']['sha256'], source['sha256'])
        self.assertEqual(self.provider.state['profileDigest'], authority.digest(new_profile))
        self.assertEqual(reconcile.ledger(self.provider.state)['accepted'], {})
        self.assertTrue(reconcile.ledger(self.provider.state)['profileHistory'])
        self.assertEqual((root / current['profile']['snapshot']).read_bytes(), content.encode())

    def test_recovery_preserves_edited_native_item_and_retires_stale_remaining_plan(self):
        entries = [{'key': 'E2', 'kind': 'epic', 'fields': self.graph()[0]['fields']}]
        proposal = planning.prepare(self.provider, entries)
        planning.approve(self.provider, proposal, authority.digest(proposal), 'approved')
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        native = self.provider.created
        self.change(native, 'Human-edited outcome preserved')
        review = revision.recovery_plan(self.provider, proposal['id'] + ':E2', native, 'Retain observed human revision')
        for role in ('business', 'technical'):
            revision.approve_recovery(self.provider, review, authority.digest(review), 'accepted recovery', role)
        revision.recover(self.provider, review, authority.digest(review), 'apply accepted recovery')
        self.assertEqual(self.provider.items[native]['fields']['System.Description'], 'Human-edited outcome preserved')
        self.assertEqual(self.provider.state['works']['E2']['nativeId'], native)
        with self.assertRaisesRegex(AzureError, 'prepare a new proposal'):
            planning.apply(self.provider, proposal['id'])

    def test_technical_completion_checks_actual_git_and_later_working_changes(self):
        root, binding = self.active()
        roots = {binding['repositoryId']: str(root)}
        self.change(3)
        report = reconcile.sync(self.provider, ['R1'])
        self.accept(report, self.decisions(report, 'business'))
        prefix = ['git', '-c', 'safe.directory=' + root.as_posix(), '-c', 'core.excludesFile=',
                  '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                  '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false']
        def git(*args):
            result = subprocess.run(prefix + list(args), cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git('init')
        artifact = root / 'docs/revised-plan.md'
        artifact.write_bytes(b'Accepted revised pilot contract.\n')
        git('add', '.')
        git('commit', '-m', 'Record actual reviewed technical basis')
        commit = git('rev-parse', 'HEAD')
        artifacts = [{'repositoryId': binding['repositoryId'], 'commit': commit, 'path': 'docs/revised-plan.md',
                      'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
        proposal = revision.technical_plan(self.provider, ['R1'], artifacts, roots)
        wrong = deepcopy(proposal)
        wrong['artifacts'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(AzureError, 'artifact hash mismatch'):
            revision.complete_technical(self.provider, wrong, authority.digest(wrong), 'approved bad fixture', roots)
        revision.complete_technical(self.provider, proposal, authority.digest(proposal), 'approved actual technical revision', roots)
        self.assertEqual(reconcile.check_scoped(self.provider, self.provider.state, 'R1'), [])
        revision.check_artifact_freshness(self.provider.state, 'R1', roots)
        artifact.write_bytes(b'Unreviewed later change.\n')
        with self.assertRaisesRegex(AzureError, 'differs from current repository evidence'):
            revision.check_artifact_freshness(self.provider.state, 'R1', roots)

    def test_recovery_cannot_adopt_an_uncorrelated_native_item(self):
        proposal = planning.prepare(self.provider, [{'key': 'E2', 'kind': 'epic', 'fields': self.graph()[0]['fields']}])
        planning.approve(self.provider, proposal, authority.digest(proposal), 'approved')
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        wrong = self.provider.create('epic', self.graph()[0]['fields'], [])
        with self.assertRaisesRegex(AzureError, 'initial native history'):
            revision.recovery_plan(self.provider, proposal['id'] + ':E2', wrong['id'], 'Wrong identity fixture')


if __name__ == '__main__':
    unittest.main()

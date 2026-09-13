"""Phase 4 authority, real Git scope, generation and evidence regressions."""
from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import io
import json
import zipfile
import shutil
import tempfile

import validate_delivery_azure as fixtures
from validate_delivery_azure import FakeProvider, OWNER
from delivery_contract import authority, validate_profile
from azure_transport import AzureError
import azure_activation as activation
import azure_planning as planning
import azure_execution as execution
import azure_execution_evidence as evidence
import delivery_execution_contract as contract
import azure_execution_views as views
import azure_reconcile as reconcile
import azure_execution_ci as ci


class ExecutionTests(unittest.TestCase):
    configured_repository = fixtures.AzurePlanningTests.configured_repository

    def graph(self):
        entries = fixtures.AzurePlanningTests.graph(self)
        second = deepcopy(entries[2])
        second['key'] = 'R2'
        second['fields']['System.Title'] = 'Independent second slice'
        return entries + [second]

    def setUp(self):
        self.provider = FakeProvider()
        self.provider.profile['execution'] = {'schemaVersion': 1,
            'teams': {'team': {'repositories': ['consumer-repo'], 'executors': [OWNER], 'workInProgressWarning': 3}},
            'pipelines': {}, 'tagCategories': {'area:sample': self.provider.profile['tagNamespace'] + ':area:sample'}}
        self.provider.state = planning.empty_state(self.provider.profile)
        proposal = planning.prepare(self.provider, self.graph())
        planning.approve(self.provider, proposal, authority.digest(proposal), 'fixture business approval')
        planning.apply(self.provider, proposal['id'])
        self.root, binding = self.configured_repository()
        binding['workBindings']['SPC-002'] = {'requirementId': 'R2', 'executionMode': 'direct', 'taskId': None}
        roadmap = self.root / binding['artifactPaths']['roadmap']
        roadmap.write_text(roadmap.read_text() + '\n' + roadmap.read_text().replace('SPC-001', 'SPC-002'))
        from delivery import write
        write(self.root / authority.BINDING, binding)
        report = reconcile.sync(self.provider, ['R2'])
        decisions = [{'nativeId': f['nativeId'], 'classification': 'baseline', 'reason': 'Reviewed second independent slice',
            'affectedKeys': f['provisionalImpact'], 'technicalRevisionRequired': False} for f in report['findings']]
        review = reconcile.propose_review(self.provider, report['id'], decisions)
        for role in review['requiredRoles']:
            reconcile.approve_review(self.provider, review, authority.digest(review), 'fixture baseline approval', role)
        reconcile.apply_review(self.provider, review['id'])
        activation_proposal = activation.prepare(self.provider, self.root, binding)
        activation.apply(self.provider, self.root, activation_proposal, authority.digest(activation_proposal), 'fixture activation approval')
        (self.root / 'docs/plan.md').write_bytes(b'Accepted contract and technical plan.\n')
        (self.root / 'src').mkdir()
        (self.root / 'src/feature.py').write_bytes(b'pass\n')
        self.git('init', '-b', 'main')
        self.git('add', '.')
        self.git('commit', '-m', 'Accepted initial plan')
        self.commit = self.git('rev-parse', 'HEAD')
        self.roots = {'consumer-repo': str(self.root)}
        self.value = {'workId': 'R1', 'repositoryId': 'consumer-repo', 'teamId': 'team', 'executorId': OWNER,
            'targetBranch': 'main', 'baseCommit': self.commit,
            'technicalArtifacts': [{'repositoryId': 'consumer-repo', 'commit': self.commit, 'path': 'docs/plan.md',
                'sha256': hashlib.sha256((self.root / 'docs/plan.md').read_bytes()).hexdigest()}],
            'footprint': {'writePaths': ['src'], 'resources': [], 'categories': ['area:sample'], 'generatedSources': {}},
            'checks': [{'id': 'manual-observation', 'kind': 'manual', 'acceptanceIds': ['AC-1'], 'pipeline': None,
                       'description': 'A reviewer confirms the visible result'}],
            'dependencies': [], 'schedule': {'plannedStart': None, 'targetFinish': None, 'committedDeadline': None},
            'priority': None, 'milestones': []}

    def git(self, *args):
        p = ['git', '-c', 'safe.directory=' + self.root.as_posix(), '-c', 'core.excludesFile=',
             '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false']
        result = subprocess.run(p + list(args), cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def planned(self):
        proposal = execution.propose(self.provider, self.value, self.roots)
        for role in ('business', 'technical'):
            execution.approve(self.provider, proposal, authority.digest(proposal), 'explicit fixture execution approval', role, self.roots)
        execution.apply(self.provider, proposal['id'], self.roots)
        return proposal

    def claimed(self):
        self.planned()
        execution.claim(self.provider, 'R1', 'session-one', self.roots)
        return authority.read(self.root / execution.RECEIPT)

    def test_profile_execution_configuration_remains_explicit(self):
        validate_profile(self.provider.profile)
        wrong = deepcopy(self.provider.profile)
        wrong['execution']['teams']['team']['executors'] = ['unverified-person']
        with self.assertRaises(AzureError):
            validate_profile(wrong)

    def test_initial_implementation_plan_checks_actual_git_artifacts(self):
        self.value['technicalArtifacts'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(AzureError, 'hash mismatch'):
            self.planned()

    def test_only_one_current_session_and_idempotent_claim(self):
        receipt = self.claimed()
        generation = self.provider.generation
        execution.claim(self.provider, 'R1', 'session-one', self.roots)
        self.assertEqual(generation, self.provider.generation)
        with self.assertRaisesRegex(AzureError, 'already has an authorized claim'):
            execution.claim(self.provider, 'R1', 'session-two', self.roots)
        self.assertEqual(receipt, authority.read(self.root / execution.RECEIPT))

    def test_claim_race_cannot_write_local_receipt(self):
        self.planned()
        with patch.object(self.provider, 'commit', side_effect=AzureError('stale head', 409)):
            with self.assertRaises(AzureError):
                execution.claim(self.provider, 'R1', 'session-one', self.roots)
        self.assertFalse((self.root / execution.RECEIPT).exists())

    def test_one_person_can_hold_independent_sessions_in_distinct_checkouts(self):
        self.value['footprint']['writePaths'] = ['src/feature.py']
        first = self.claimed()
        self.value['workId'] = 'R2'
        self.value['footprint']['writePaths'] = ['src/second.py']
        self.planned()
        directory = tempfile.TemporaryDirectory(prefix='delivery-second-checkout-')
        self.addCleanup(directory.cleanup)
        second = Path(directory.name) / 'repo'
        shutil.copytree(self.root, second)
        (second / execution.RECEIPT).unlink()
        execution.claim(self.provider, 'R2', 'independent-session', {'consumer-repo': str(second)})
        self.assertEqual(set(execution.current_claims(self.provider.state)), {'R1', 'R2'})
        self.assertEqual(authority.read(self.root / execution.RECEIPT), first)
        self.assertEqual(authority.read(second / execution.RECEIPT)['workId'], 'R2')

    def test_parent_and_child_claims_cannot_coexist(self):
        self.claimed()
        with self.assertRaisesRegex(AzureError, 'parent-wide and child'):
            execution.conflicts(self.provider.state, 'T1', self.value)

    def test_receiving_dependency_blocks_only_its_named_activity(self):
        self.planned()
        self.value['workId'] = 'R2'
        self.value['dependencies'] = [{'id': 'receiving', 'predecessor': 'R1', 'blockedActivity': 'delivery',
            'condition': 'integration', 'checkIds': ['manual-observation'], 'reason': 'Explicit receiving proof', 'externalReference': None}]
        self.planned()
        execution.dependency_gate(self.provider, self.provider.state, 'R2', 'implementation', self.roots)
        with self.assertRaisesRegex(AzureError, 'required execution evidence'):
            execution.dependency_gate(self.provider, self.provider.state, 'R2', 'delivery', self.roots)

    def test_takeover_fences_old_session_and_requires_resume(self):
        old = self.claimed()
        execution.change_claim(self.provider, 'R1', 1, 'takeover', 'Explicit recovery', session='session-two', executor=OWNER)
        with self.assertRaisesRegex(AzureError, 'no longer authorized'):
            execution.checkpoint(self.provider, old, 'implementation', self.roots)
        execution.resume(self.provider, 'R1', 'session-two', self.roots)
        current = authority.read(self.root / execution.RECEIPT)
        self.assertEqual(current['generation'], 2)
        execution.checkpoint(self.provider, current, 'implementation', self.roots)

    def test_claim_does_not_invent_actual_start(self):
        receipt = self.claimed()
        self.assertNotIn('actualStart', execution.book(self.provider.state)['progress']['R1'])
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        self.assertIn('actualStart', execution.book(self.provider.state)['progress']['R1'])

    def test_review_retains_claim_and_return_to_implementation_updates_activity(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'review', self.roots)
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'awaiting-review')
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'active')

    def test_deleted_work_is_unknown_without_hiding_other_readiness_rows(self):
        self.planned()
        original = self.provider.item
        def item(identity):
            if identity == 3:
                raise AzureError('work unavailable', 404)
            return original(identity)
        with patch.object(self.provider, 'item', side_effect=item):
            rows = views.ready(self.provider, self.roots)['work']
        self.assertFalse(next(r for r in rows if r['workId'] == 'R1')['readyToImplement'])
        self.assertIn('unavailable', next(r for r in rows if r['workId'] == 'R1')['blocker'])

    def test_milestone_dates_and_membership_do_not_imply_outcome_acceptance(self):
        proposal = views.milestone_plan(self.provider, {'id': 'pilot', 'title': 'Pilot', 'outcome': 'Pilot serves users',
            'ownerId': OWNER, 'workIds': ['R1'], 'schedule': self.value['schedule']})
        views.milestone_apply(self.provider, proposal, authority.digest(proposal), 'fixture milestone approval')
        generation = self.provider.generation
        views.milestone_apply(self.provider, proposal, authority.digest(proposal), 'same approval retried')
        self.assertEqual(generation, self.provider.generation)
        status = views.milestone_status(self.provider, self.provider.state, 'pilot', self.roots)
        self.assertFalse(status['outcomeAccepted'])
        with self.assertRaises(AzureError):
            views.milestone_acceptance_plan(self.provider, 'pilot', {'explanation': 'Items look closed',
                'artifacts': self.value['technicalArtifacts']}, self.roots)

    def test_material_scope_expansion_blocks_checkpoint(self):
        receipt = self.claimed()
        (self.root / 'outside.py').write_text('unreviewed')
        with self.assertRaisesRegex(AzureError, 'scope expansion'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)

    def test_human_closed_status_does_not_release_or_complete(self):
        receipt = self.claimed()
        item = self.provider.item(3)
        self.provider.update(3, item['rev'], {'System.State': 'Closed'}, [])
        with self.assertRaisesRegex(AzureError, 'unreviewed'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'active')
        self.assertIsNone(execution.book(self.provider.state)['progress']['R1']['delivery'])

    def test_changed_plan_file_blocks_current_claim(self):
        receipt = self.claimed()
        (self.root / 'docs/plan.md').write_text('Changed technical direction')
        with self.assertRaisesRegex(AzureError, 'differs from current repository evidence'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)

    def test_outage_preserves_current_work_but_blocks_the_next_checkpoint(self):
        receipt = self.claimed()
        path = self.root / 'src/feature.py'
        path.write_text('print("current local work")\n')
        generation = self.provider.generation
        with patch.object(self.provider, 'evidence', side_effect=AzureError('service unavailable', 503)):
            with self.assertRaisesRegex(AzureError, 'service unavailable'):
                execution.checkpoint(self.provider, receipt, 'publish', self.roots)
        self.assertEqual(self.provider.generation, generation)
        self.assertIn('current local work', path.read_text())
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)

    def test_completion_releases_claim_but_not_delivery(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        with patch.object(evidence, 'branch', return_value=self.commit):
            proposal = evidence.progress_plan(self.provider, 'R1', 'implementation', self.roots)
            evidence.complete(self.provider, proposal, authority.digest(proposal), 'Accept integrated implementation fixture', self.roots)
            self.assertEqual(self.provider.state['claims']['R1']['state'], 'released')
            with self.assertRaisesRegex(AzureError, 'required execution evidence'):
                evidence.progress_plan(self.provider, 'R1', 'delivery', self.roots)

    def test_integrated_ci_allows_released_parent_with_active_receiving_task(self):
        receipt = self.claimed()
        with patch.object(evidence, 'branch', return_value=self.commit):
            proposal = evidence.progress_plan(self.provider, 'R1', 'implementation', self.roots)
            evidence.complete(self.provider, proposal, authority.digest(proposal), 'Integrated fixture parent', self.roots)
        state = deepcopy(self.provider.state)
        task = deepcopy(self.value)
        task['workId'] = 'T1'
        execution.book(state)['plans']['T1'] = {'proposal': {'id': 'task-plan', 'plan': task}}
        state['claims']['T1'] = {**deepcopy(state['claims']['R1']), 'workId': 'T1', 'state': 'active', 'planId': 'task-plan'}
        yaml = 'jobs:\n- job: Verify\n'
        rule = {'projectId': self.provider.project, 'definitionId': 7, 'repositoryId': 'consumer-repo',
            'finalYamlSha256': evidence.yaml_digest(yaml), 'repositoryAliases': {'self': 'consumer-repo'},
            'targetBranches': {'consumer-repo': 'main'}, 'requiredJobs': ['Verify'], 'artifactName': 'delivery', 'manifestPath': 'manifest.json'}
        self.provider.profile['execution']['pipelines']['check'] = rule
        build = {'id': 123, 'project': {'id': self.provider.project}, 'definition': {'id': 7},
            'repository': {'id': 'consumer-repo'}, 'sourceVersion': self.commit, 'reason': 'manual'}
        self.provider.api.call = lambda method, path, **kwargs: {'finalYaml': yaml} if '/runs/' in path else build
        with patch.object(planning, 'state_for', return_value=('head', state)), \
                patch.object(execution, 'current_plan', side_effect=lambda p, s, key, *a: task if key == 'T1' else self.value), \
                patch.object(evidence, 'branch_policy', return_value=[{'id': 1}]), \
                patch.object(evidence, 'published_artifacts', return_value=self.value['technicalArtifacts']), \
                patch.object(evidence, 'branch', return_value=self.commit):
            binding = authority.read(self.root / authority.BINDING)
            result = ci.check(self.provider, self.root, 123, binding=binding)
            with self.assertRaisesRegex(AzureError, 'binding differs'):
                ci.check(self.provider, self.root, 123, binding={**binding, 'repositoryId': 'another-repository'})
        self.assertEqual(set(result['workIds']), {'R1', 'T1'})
        self.assertFalse(result['completionRecorded'])

    def test_dependency_cycle_detects_activity_cycle(self):
        def value(predecessor):
            return {'dependencies': [{'predecessor': predecessor, 'condition': 'integration', 'blockedActivity': 'integration'}]}
        with self.assertRaisesRegex(AzureError, 'circular'):
            execution.cycles({'A': value('B'), 'B': value('A')})
        execution.cycles({'A': {'dependencies': [{'predecessor': 'B', 'condition': 'contract', 'blockedActivity': 'implementation'}]}, 'B': {'dependencies': []}})

    def test_category_overlap_is_not_resource_exclusion(self):
        other = deepcopy(self.value)
        other['footprint']['writePaths'] = ['other']
        self.assertEqual(contract.compare(self.value, other)['assessment'], 'no-known-conflict')
        other['footprint']['writePaths'] = ['src']
        self.assertEqual(contract.compare(self.value, other)['assessment'], 'advisory')
        self.value['footprint']['resources'] = [{'id': 'shared-api', 'mode': 'change', 'contractRevision': 'v2'}]
        other['repositoryId'] = 'other-repo'
        other['footprint']['resources'] = [{'id': 'shared-api', 'mode': 'read', 'contractRevision': 'v1'}]
        self.assertEqual(contract.compare(self.value, other)['assessment'], 'coordinate')

    def test_native_projection_preserves_human_tag_and_claim_basis(self):
        current = self.provider.item(3)
        self.provider.update(3, current['rev'], {'System.Tags': 'Human pilot'}, [])
        report = reconcile.sync(self.provider, ['R1'])
        decisions = [{'nativeId': f['nativeId'], 'classification': 'cosmetic', 'reason': 'Human category accepted',
            'affectedKeys': [f['key']], 'technicalRevisionRequired': False} for f in report['findings']]
        review = reconcile.propose_review(self.provider, report['id'], decisions)
        reconcile.approve_review(self.provider, review, authority.digest(review), 'accepted human tag', 'technical')
        reconcile.apply_review(self.provider, review['id'])
        receipt = self.claimed()
        published = views.publish(self.provider, 'R1', self.roots)
        self.assertEqual(published['state'], 'applied')
        tags = self.provider.item(3)['fields']['System.Tags']
        self.assertIn('Human pilot', tags)
        self.assertIn(self.provider.profile['tagNamespace'] + ':area:sample', tags)
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        generation = self.provider.generation
        views.resume_projection(self.provider, published['id'])
        self.assertEqual(generation, self.provider.generation)

    def test_projection_lost_response_recovers_without_replaying_native_write(self):
        self.planned()
        update = self.provider.update
        def lost(*args, **kwargs):
            update(*args, **kwargs)
            raise AzureError('lost response', 503)
        with patch.object(self.provider, 'update', side_effect=lost):
            with self.assertRaisesRegex(AzureError, 'lost response'):
                views.publish(self.provider, 'R1', self.roots)
        identity = next(iter(execution.book(self.provider.state)['projections']))
        revision = self.provider.item(3)['rev']
        views.resume_projection(self.provider, identity)
        self.assertEqual(self.provider.item(3)['rev'], revision)
        self.assertEqual(execution.book(self.provider.state)['projections'][identity]['state'], 'applied')

    def test_projection_accepts_only_observed_audit_expiry_and_empty_tag_backfill(self):
        self.planned()
        before = self.provider.evidence(3)
        before['updates'][-1]['rev'] = before['item']['rev']
        before['updates'][-1]['revisedDate'] = '9999-01-01T00:00:00Z'
        before['updates'][-1].setdefault('fields', {})['System.RevisedDate'] = {'newValue': '9999-01-01T00:00:00Z'}
        after = deepcopy(before)
        timestamp = '2026-09-13T14:03:08.72Z'
        after['item']['fields']['System.Tags'] = 'pk:area:sample'
        after['updates'][-1]['revisedDate'] = timestamp
        after['updates'][-1]['fields']['System.RevisedDate']['newValue'] = timestamp
        after['updates'][0]['fields']['System.Tags'] = {'newValue': ''}
        after['updates'].append({'id': len(after['updates']) + 1, 'fields': {
            'System.ChangedDate': {'newValue': timestamp}, 'System.Tags': {'oldValue': '', 'newValue': 'pk:area:sample'}}})
        self.assertTrue(views.projection_compatible(before, after, [], {'System.Tags': 'pk:area:sample'}))
        after['updates'][0]['fields']['System.Tags']['newValue'] = 'erased human tag'
        self.assertFalse(views.projection_compatible(before, after, [], {'System.Tags': 'pk:area:sample'}))
        after['updates'][0]['fields']['System.Tags']['newValue'] = ''
        after['updates'][-2]['revisedDate'] = '2026-09-12T00:00:00Z'
        self.assertFalse(views.projection_compatible(before, after, [], {'System.Tags': 'pk:area:sample'}))

    def test_projection_recovery_requires_review_and_fences_its_conditional_revision(self):
        self.planned()
        with patch.object(self.provider, 'update', side_effect=AzureError('outcome unknown', 503)):
            with self.assertRaises(AzureError):
                views.publish(self.provider, 'R1', self.roots)
        identity = next(iter(execution.book(self.provider.state)['projections']))
        with self.assertRaisesRegex(AzureError, 'has not been fenced'):
            views.abandon_projection(self.provider, identity, 'Attempt before proving the outcome')
        item = self.provider.item(3)
        self.provider.update(3, item['rev'], {'System.Tags': 'Human recovery tag'}, [])
        with self.assertRaisesRegex(AzureError, 'review all intervening'):
            views.abandon_projection(self.provider, identity, 'Human edited while the operation was uncertain')
        report = reconcile.sync(self.provider, ['R1'])
        decisions = [{'nativeId': f['nativeId'], 'classification': 'cosmetic', 'reason': 'Reviewed human tag',
            'affectedKeys': [f['key']], 'technicalRevisionRequired': False} for f in report['findings']]
        review = reconcile.propose_review(self.provider, report['id'], decisions)
        for role in review['requiredRoles']:
            reconcile.approve_review(self.provider, review, authority.digest(review), 'explicit fixture recovery review', role)
        reconcile.apply_review(self.provider, review['id'])
        result = views.abandon_projection(self.provider, identity, 'New accepted revision fences the old conditional PATCH')
        self.assertEqual(result['state'], 'abandoned')
        self.assertEqual(self.provider.item(3)['fields']['System.Tags'], 'Human recovery tag')

    def test_manual_evidence_cannot_replace_a_required_pipeline(self):
        self.planned()
        inputs = {'checkIds': ['manual-observation'], 'buildId': 12, 'manualArtifacts': self.value['technicalArtifacts'],
                  'explanation': 'A human saw the result'}
        with self.assertRaisesRegex(AzureError, 'manual evidence'):
            evidence.evidence_plan(self.provider, 'R1', inputs, self.roots)

    def test_successful_manual_delivery_and_separate_acceptance(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        with patch.object(evidence, 'branch', return_value=self.commit):
            p = evidence.progress_plan(self.provider, 'R1', 'implementation', self.roots)
            evidence.complete(self.provider, p, authority.digest(p), 'accepted integrated implementation', self.roots)
            inputs = {'checkIds': ['manual-observation'], 'buildId': None,
                      'manualArtifacts': self.value['technicalArtifacts'], 'explanation': 'Verified visible fixture outcome'}
            p = evidence.evidence_plan(self.provider, 'R1', inputs, self.roots)
            evidence.record_evidence(self.provider, p, authority.digest(p), 'Human observed acceptance criterion', self.roots)
            p = evidence.progress_plan(self.provider, 'R1', 'delivery', self.roots)
            evidence.complete(self.provider, p, authority.digest(p), 'Approve evidence-backed delivery', self.roots)
            self.assertIsNone(execution.book(self.provider.state)['progress']['R1']['acceptance'])
            # A later checkout session cannot redirect an explicitly selected completed entry.
            (self.root / execution.RECEIPT).write_text('{"workId":"R2"}')
            from delivery_contract import admit_execution
            with patch('azure_provider.AzureProvider', return_value=self.provider), patch('azure_transport.AzureTransport', return_value=None):
                admission = admit_execution(self.root, 'delivery', 'SPC-001')
                self.assertEqual(admission['workId'], 'R1')
                self.assertFalse(admission['completionRecorded'])
            p = evidence.progress_plan(self.provider, 'R1', 'acceptance', self.roots)
            evidence.complete(self.provider, p, authority.digest(p), 'Accept the business outcome', self.roots)
            self.assertIsNotNone(execution.book(self.provider.state)['progress']['R1']['acceptance'])


class PipelineEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeProvider()
        self.repo = 'consumer-repo'
        self.source = 'a' * 40
        self.yaml = 'jobs:\n- job: Verify\n'
        self.rule = {'projectId': self.provider.project, 'definitionId': 7, 'repositoryId': self.repo,
            'finalYamlSha256': evidence.yaml_digest(self.yaml), 'repositoryAliases': {'self': self.repo},
            'targetBranches': {self.repo: 'main'}, 'requiredJobs': ['Verify'], 'artifactName': 'delivery', 'manifestPath': 'manifest.json'}
        self.provider.profile['execution'] = {'schemaVersion': 1,
            'teams': {'team': {'repositories': [self.repo], 'executors': [OWNER], 'workInProgressWarning': None}},
            'pipelines': {'checks': self.rule}, 'tagCategories': {}}
        self.build = {'id': 123, 'project': {'id': self.provider.project}, 'definition': {'id': 7, 'revision': 1},
            'repository': {'id': self.repo}, 'status': 'completed', 'result': 'succeeded', 'sourceVersion': self.source, 'reason': 'manual'}
        self.run = {'id': 123, 'pipeline': {'id': 7, 'revision': 1}, 'state': 'completed', 'result': 'succeeded',
            'finalYaml': self.yaml, 'resources': {'repositories': {'self': {'repository': {'id': self.repo}, 'version': self.source}}}}
        self.job = {'type': 'Job', 'name': 'Verify', 'state': 'completed', 'result': 'succeeded'}
        self.payload = {'id': 1, 'name': 'delivery', 'manifest': {'sources': {self.repo: self.source}, 'checks': {'check': 'passed'}}}
        def call(method, path, **kwargs):
            if path.endswith('/timeline'):
                return {'records': [self.job]}
            return self.run if '/runs/' in path else self.build
        self.provider.api.call = call
        self.addCleanup(patch.stopall)
        patch.object(evidence, 'branch', return_value=self.source).start()
        patch.object(evidence, 'artifact', side_effect=lambda *args: deepcopy(self.payload)).start()

    def verify(self):
        return evidence.pipeline(self.provider, 'checks', 123, ['check'])

    def test_exact_provider_pipeline_evidence(self):
        self.assertEqual(self.verify()['sources'], {self.repo: self.source})

    def test_partially_successful_or_skipped_job_cannot_pass(self):
        self.build['result'] = 'partiallySucceeded'
        with self.assertRaises(AzureError):
            self.verify()
        self.build['result'] = 'succeeded'
        self.job['result'] = 'skipped'
        with self.assertRaisesRegex(AzureError, 'required job'):
            self.verify()

    def test_changed_yaml_does_not_pass_but_line_endings_match(self):
        self.run['finalYaml'] = self.yaml.replace('\n', '\r\n')
        self.verify()
        self.run['finalYaml'] += 'malicious: true\n'
        with self.assertRaisesRegex(AzureError, 'YAML differs'):
            self.verify()

    def test_missing_consumed_repository_identity_is_unknown(self):
        self.run['resources']['repositories']['self']['repository'].pop('id')
        with self.assertRaisesRegex(AzureError, 'identity/version'):
            self.verify()

    def test_manifest_cannot_lie_about_tested_revision_or_result(self):
        self.payload['manifest']['sources'][self.repo] = 'b' * 40
        with self.assertRaisesRegex(AzureError, 'manifest'):
            self.verify()
        self.payload['manifest']['sources'][self.repo] = self.source
        self.payload['manifest']['checks']['check'] = 'failed'
        with self.assertRaisesRegex(AzureError, 'manifest'):
            self.verify()

    def test_pr_validation_is_not_integrated_delivery(self):
        self.build['reason'] = 'pullRequest'
        with self.assertRaisesRegex(AzureError, 'PR candidate'):
            self.verify()

    def test_target_advance_invalidates_old_evidence(self):
        with patch.object(evidence, 'branch', return_value='b' * 40):
            with self.assertRaisesRegex(AzureError, 'current integrated target'):
                self.verify()


class ArtifactTests(unittest.TestCase):
    def test_duplicate_evidence_properties_are_rejected(self):
        with self.assertRaisesRegex(AzureError, 'duplicate'):
            json.loads('{"sources":{},"sources":{"unexpected":"revision"}}', object_pairs_hook=evidence.unique_object)

    def test_remote_ancestry_requires_exact_common_commit(self):
        ancestor, target = 'a' * 40, 'b' * 40
        value = {'baseCommit': ancestor, 'targetCommit': target, 'commonCommit': ancestor}
        provider = SimpleNamespace(project='project', api=SimpleNamespace(call=lambda *a, **k: value))
        evidence.contains_commit(provider, 'repo', ancestor, target)
        value['commonCommit'] = 'c' * 40
        with self.assertRaisesRegex(AzureError, 'target history'):
            evidence.contains_commit(provider, 'repo', ancestor, target)

    def test_job_transport_and_provider_cannot_mutate_or_approve_business(self):
        transport = object.__new__(ci.JobReadTransport)
        transport.organization = 'example'
        with self.assertRaisesRegex(AzureError, 'prohibits mutations'):
            transport.request('POST', '/_apis/anything', {})
        provider = ci.JobReadProvider(transport, fixtures.FakeProvider().profile)
        for method in ('commit', 'create', 'update'):
            with self.assertRaises(AzureError):
                getattr(provider, method)()
        for role in ('business', 'acceptance', 'coordinator'):
            with self.assertRaisesRegex(AzureError, 'cannot approve'):
                provider.authorize(role)

    def test_corrupted_or_unmanifested_artifact_files_cannot_pass(self):
        provider = SimpleNamespace(project='project', api=SimpleNamespace(call=lambda *a, **k:
            {'id': 1, 'name': 'delivery', 'resource': {'downloadUrl': 'https://unused.invalid'}}))
        rule = {'artifactName': 'delivery', 'manifestPath': 'manifest.json'}
        manifest = {'schemaVersion': 1, 'sources': {}, 'checks': {}, 'artifacts': {'payload': hashlib.sha256(b'expected').hexdigest()}}
        def archive(payload, extra=False):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as output:
                output.writestr('manifest.json', json.dumps(manifest))
                output.writestr('payload', payload)
                if extra:
                    output.writestr('unreviewed', 'extra payload')
            return stream.getvalue()
        with patch.object(evidence, 'download', return_value=archive(b'expected')):
            self.assertEqual(evidence.artifact(provider, 1, rule)['manifest'], manifest)
        with patch.object(evidence, 'download', return_value=archive(b'corrupted')):
            with self.assertRaisesRegex(AzureError, 'hash mismatch'):
                evidence.artifact(provider, 1, rule)
        with patch.object(evidence, 'download', return_value=archive(b'expected', True)):
            with self.assertRaisesRegex(AzureError, 'outside its exact content manifest'):
                evidence.artifact(provider, 1, rule)

    def test_artifact_credentials_do_not_follow_arbitrary_hosts(self):
        provider = SimpleNamespace(project='project', api=SimpleNamespace(organization='example'))
        with self.assertRaisesRegex(AzureError, 'unsupported artifact download origin'):
            evidence.download(provider, 'https://attacker.invalid/steal')


class BoardTests(unittest.TestCase):
    configured_repository = ExecutionTests.configured_repository
    graph = ExecutionTests.graph
    git = ExecutionTests.git
    planned = ExecutionTests.planned
    claimed = ExecutionTests.claimed

    def setUp(self):
        ExecutionTests.setUp(self)
        import azure_execution_board as board
        self.board = board
        self.mapping = json.loads((fixtures.SCRIPTS.parent / 'references/azure-board-default.json').read_text())
        self.mapping['boards'] = [{'teamId': 'native-team', 'boardId': k, 'kind': k} for k in ('epic', 'feature', 'requirement')]
        capabilities = self.provider.discover_capabilities
        def discover():
            result = capabilities()
            for kind, value in result['types'].items():
                value['states'] = [{'name': n, 'category': c} for n, c in
                    [('New', 'Proposed'), ('Active', 'InProgress'), ('Closed', 'Completed')]
                    + ([] if kind == 'task' else [('Resolved', 'InProgress')])]
            return result
        self.provider.discover_capabilities = discover
        self.columns = {}
        for kind in ('epic', 'feature', 'requirement'):
            self.columns[kind] = {'id': kind, 'fields': {}, 'columns': [
                {'id': name, 'name': name, 'columnType': 'incoming' if name == 'New' else 'outgoing' if name == 'Closed' else 'inProgress',
                 'stateMappings': {self.provider.profile['workTypes'][kind]: name}} for name in ('New', 'Active', 'Resolved', 'Closed')]}
        self.provider.api.call = lambda method, path, **kwargs: deepcopy(self.columns[path.rsplit('/', 1)[-1]])
        update = self.provider.update
        def native_update(identity, revision, fields, relations):
            fields = deepcopy(fields)
            fields['System.ChangedBy'] = {'id': OWNER}
            fields['System.ChangedDate'] = '2026-09-13T12:00:00Z'
            if 'System.State' in fields:
                fields['System.Reason'] = 'Native workflow transition'
                fields['Microsoft.VSTS.Common.StateChangeDate'] = fields['System.ChangedDate']
            return update(identity, revision, fields, relations)
        self.provider.update = native_update
        proposal = board.plan(self.provider, self.mapping)
        for role in ('business', 'technical'):
            board.approve(self.provider, proposal, authority.digest(proposal), 'Approved native board fixture', role)
        board.apply(self.provider, proposal['id'])

    def test_claim_is_not_start_and_checkpoint_publishes_active_parents(self):
        receipt = self.claimed()
        self.assertEqual(self.provider.item(3)['fields']['System.State'], 'New')
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        for native in (1, 2, 3):
            self.assertEqual(self.provider.item(native)['fields']['System.State'], 'Active')
        self.assertIsNone(self.provider.state['execution']['progress']['R1']['acceptance'])
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'active')

    def test_implementation_resolves_and_only_verified_acceptance_closes(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        with patch.object(evidence, 'branch', return_value=self.commit):
            p = evidence.progress_plan(self.provider, 'R1', 'implementation', self.roots)
            evidence.complete(self.provider, p, authority.digest(p), 'Integrated implementation', self.roots)
            self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Resolved')
            with self.assertRaisesRegex(AzureError, 'required execution evidence'):
                evidence.progress_plan(self.provider, 'R1', 'delivery', self.roots)
            p = evidence.evidence_plan(self.provider, 'R1', {'checkIds': ['manual-observation'], 'buildId': None,
                'manualArtifacts': self.value['technicalArtifacts'], 'explanation': 'Actual visible manual criterion'}, self.roots)
            evidence.record_evidence(self.provider, p, authority.digest(p), 'Reviewed manual observation', self.roots)
            for stage in ('delivery', 'acceptance'):
                p = evidence.progress_plan(self.provider, 'R1', stage, self.roots)
                evidence.complete(self.provider, p, authority.digest(p), 'Reviewed ' + stage, self.roots)
                self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Closed' if stage == 'acceptance' else 'Resolved')
        self.assertEqual(self.provider.item(2)['fields']['System.State'], 'Active')
        with patch.object(evidence, 'branch', return_value=self.commit):
            with self.assertRaises(AzureError):
                self.board.parent_plan(self.provider, 'F1', {'explanation': 'Parent not established by a closed child',
                    'artifacts': self.value['technicalArtifacts']}, self.roots)

    def test_parent_closure_needs_its_own_outcome_even_after_all_requirements_accept(self):
        with patch.object(evidence, 'branch', return_value=self.commit):
            for key in ('R1', 'R2'):
                self.value['workId'] = key
                self.planned()
                execution.claim(self.provider, key, 'session-' + key, self.roots)
                receipt = authority.read(self.root / execution.RECEIPT)
                execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
                p = evidence.evidence_plan(self.provider, key, {'checkIds': ['manual-observation'], 'buildId': None,
                    'manualArtifacts': self.value['technicalArtifacts'], 'explanation': 'Observed explicit manual criterion'}, self.roots)
                evidence.record_evidence(self.provider, p, authority.digest(p), 'Reviewed observation', self.roots)
                for stage in ('implementation', 'delivery', 'acceptance'):
                    p = evidence.progress_plan(self.provider, key, stage, self.roots)
                    evidence.complete(self.provider, p, authority.digest(p), 'Reviewed ' + stage, self.roots)
            self.assertEqual(self.provider.item(2)['fields']['System.State'], 'Active')
            p = self.board.parent_plan(self.provider, 'F1', {'explanation': 'Feature outcome explicitly observed',
                'artifacts': self.value['technicalArtifacts']}, self.roots)
            self.board.accept_parent(self.provider, p, authority.digest(p), 'Business accepted the Feature outcome', self.roots)
            self.assertEqual(self.provider.item(2)['fields']['System.State'], 'Closed')
            self.assertEqual(self.provider.item(1)['fields']['System.State'], 'Active')

    def test_failed_write_is_atomic_pending_and_lost_response_is_not_replayed(self):
        receipt = self.claimed()
        native_update = self.provider.update
        calls = []
        def lost(identity, revision, fields, relations):
            calls.append(identity)
            native_update(identity, revision, fields, relations)
            raise AzureError('lost native response')
        with patch.object(self.provider, 'update', side_effect=lost):
            with self.assertRaisesRegex(AzureError, 'lost native response'):
                execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        self.assertIsNotNone(self.provider.state['execution']['progress']['R1']['actualStart'])
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'active')
        with self.assertRaisesRegex(AzureError, 'board synchronization pending'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        operation = self.board.pending(self.provider.state)[0]['id']
        with patch.object(self.provider, 'update', wraps=native_update) as written:
            result = self.board.flush(self.provider, operation)
            self.assertNotIn(calls[0], [call.args[0] for call in written.call_args_list])
        self.assertEqual(result['state'], 'applied')
        self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Active')

    def test_human_closure_and_tag_require_reconciliation_and_grant_nothing(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        original_claim = deepcopy(self.provider.state['claims']['R1'])
        original_progress = deepcopy(self.provider.state['execution']['progress']['R1'])
        original_plan = deepcopy(self.provider.state['execution']['plans']['R1'])
        item = self.provider.item(3)
        self.provider.update(3, item['rev'], {'System.State': 'Closed', 'System.Tags': 'Human portal check'}, [])
        with self.assertRaisesRegex(AzureError, 'unreviewed'):
            self.board.sync(self.provider, 'R1', self.roots)
        with self.assertRaisesRegex(AzureError, 'unreviewed'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        report = reconcile.sync(self.provider, ['R1'])
        self.assertTrue(report['findings'])
        self.assertEqual(self.provider.item(3)['fields']['System.Tags'], 'Human portal check')
        self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Closed')
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'active')
        self.assertTrue(all(self.provider.state['execution']['progress']['R1'][k] is None for k in ('implementation', 'delivery', 'acceptance')))
        decisions = [{'nativeId': 3, 'classification': 'feedback', 'reason': 'Reviewed false closure: no outcome or design change; restore verified activity and preserve tag',
                      'affectedKeys': ['R1'], 'technicalRevisionRequired': False}]
        review = reconcile.propose_review(self.provider, report['id'], decisions)
        reconcile.approve_review(self.provider, review, authority.digest(review), 'Approved closure correction', 'technical')
        reconcile.apply_review(self.provider, review['id'])
        self.board.sync(self.provider, 'R1', self.roots)
        self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Active')
        self.assertIn('Human portal check', self.provider.item(3)['fields']['System.Tags'])
        self.assertEqual(self.provider.state['claims']['R1'], original_claim)
        self.assertEqual(self.provider.state['execution']['progress']['R1'], original_progress)
        self.assertEqual(self.provider.state['execution']['plans']['R1'], original_plan)
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots, record=False)

    def test_mapping_rejects_premature_completed_category_and_column_drift(self):
        wrong = deepcopy(self.mapping)
        wrong['types']['task']['implemented'] = 'Closed'
        with self.assertRaisesRegex(AzureError, 'misrepresent'):
            self.board.plan(self.provider, wrong)
        self.assertEqual(self.mapping['types']['task']['implemented'], 'Active')
        receipt = self.claimed()
        self.columns['requirement']['columns'][1]['columnType'] = 'outgoing'
        with self.assertRaisesRegex(AzureError, 'unfinished work'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        self.assertNotIn('actualStart', self.provider.state['execution']['progress']['R1'])

    def test_explicit_stop_survives_unreviewed_change_without_overwriting_the_board(self):
        receipt = self.claimed()
        execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        progress = deepcopy(self.provider.state['execution']['progress']['R1'])
        item = self.provider.item(3)
        self.provider.update(3, item['rev'], {'System.Description': 'Human request requiring assessment'}, [])
        human = self.provider.evidence(3)
        for action in ('pause', 'withdraw'):
            with patch.object(self.provider, 'update', wraps=self.provider.update) as writes:
                stopped = execution.change_claim(self.provider, 'R1', receipt['generation'], action, 'Stop pending human-change review')
                writes.assert_not_called()
            self.assertIn('unreviewed', stopped['boardPublicationDeferred']['reason'])
            self.assertEqual(self.provider.state['claims']['R1']['state'], 'paused' if action == 'pause' else 'withdrawn')
            self.assertEqual(self.provider.state['execution']['progress']['R1'], progress)
            self.assertEqual(self.provider.evidence(3), human)
        self.assertIn('R1', views.ready(self.provider, self.roots)['deferredBoardPublications'])
        with self.assertRaisesRegex(AzureError, 'no longer authorized'):
            execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        report = reconcile.sync(self.provider, ['R1'])
        review = reconcile.propose_review(self.provider, report['id'], [{'nativeId': 3, 'classification': 'feedback',
            'reason': 'Reviewed request; retain current scope', 'affectedKeys': ['R1'], 'technicalRevisionRequired': False}])
        reconcile.approve_review(self.provider, review, authority.digest(review), 'Explicit fixture review', 'technical')
        reconcile.apply_review(self.provider, review['id'])
        self.board.sync(self.provider, 'R1', self.roots)
        self.assertNotIn('R1', self.board.book(self.provider.state)['deferred'])
        self.assertEqual(self.provider.item(3)['fields']['System.State'], 'Active')
        self.assertEqual(self.provider.state['claims']['R1']['state'], 'withdrawn')

    def test_another_human_edit_after_write_is_not_absorbed_as_native_side_effect(self):
        receipt = self.claimed()
        native_update = self.provider.update
        def human_race(identity, revision, fields, relations):
            native_update(identity, revision, fields, relations)
            native_update(identity, revision + 1, {'System.Title': 'Human decision during publication'}, [])
        with patch.object(self.provider, 'update', side_effect=human_race):
            with self.assertRaisesRegex(AzureError, 'intervening human changes'):
                execution.checkpoint(self.provider, receipt, 'implementation', self.roots)
        op = self.board.pending(self.provider.state)[0]
        identity = next(iter(op['items'].values()))['nativeId']
        self.assertEqual(self.provider.item(identity)['fields']['System.Title'], 'Human decision during publication')
        self.assertEqual(op['state'], 'pending')

    def test_initial_board_materialization_is_narrow_and_preserves_human_edits(self):
        before = self.provider.evidence(3)
        policy = deepcopy(self.board.book(self.provider.state)['policy'])
        for selected in policy['proposal']['capabilities']['boards']:
            if selected['kind'] == 'requirement':
                selected['fields'] = {'columnField': {'referenceName': 'WEF_FIXTURE_Kanban.Column'},
                                      'doneField': {'referenceName': 'WEF_FIXTURE_Kanban.Column.Done'}}
        fields = {'System.AuthorizedAs': {'id': self.board.AZURE_WORKFLOW_SERVICE}, 'System.PersonId': 100,
                  'System.BoardColumn': 'New', 'System.BoardColumnDone': False,
                  'WEF_FIXTURE_Kanban.Column': 'New', 'WEF_FIXTURE_Kanban.Column.Done': False,
                  'WEF_FIXTURE_System.ExtensionMarker': True}
        after = deepcopy(before)
        after['item']['rev'] += 1
        after['item']['fields'].update({k: v for k, v in fields.items() if k not in
            ('System.AuthorizedAs', 'System.PersonId', 'WEF_FIXTURE_System.ExtensionMarker')})
        after['updates'].append({'id': len(after['updates']) + 1, 'rev': after['item']['rev'],
                                'fields': {k: {'newValue': v} for k, v in fields.items()}})
        self.assertTrue(self.board.initialization_compatible(before, after, 'requirement', policy))
        for field, value in [('System.State', 'Closed'), ('System.Tags', 'Human tag'), ('System.Title', 'Human scope')]:
            changed = deepcopy(after)
            changed['item']['fields'][field] = value
            changed['updates'][-1]['fields'][field] = {'newValue': value}
            self.assertFalse(self.board.initialization_compatible(before, changed, 'requirement', policy))
        changed = deepcopy(after)
        changed['comments'].append({'id': 1, 'text': 'Human feedback'})
        self.assertFalse(self.board.initialization_compatible(before, changed, 'requirement', policy))

    def test_native_unchanged_actor_and_hidden_audit_fields_are_verified(self):
        before = self.provider.evidence(3)
        self.provider.update(3, before['item']['rev'], {'System.State': 'Active'}, [])
        after = self.provider.evidence(3)
        update = after['updates'][-1]
        del update['fields']['System.ChangedBy']
        update['revisedBy'] = {'id': OWNER}
        update['fields']['System.AuthorizedAs'] = {'newValue': {'id': OWNER}}
        update['fields']['System.PersonId'] = {'newValue': 42}
        entry = {'before': {**before, 'canonicalKind': 'requirement'}, 'fields': {'System.State': 'Active'}}
        policy = self.board.book(self.provider.state)['policy']
        self.assertTrue(self.board.compatible({'actorId': OWNER}, entry, after, policy))
        update['fields']['System.AuthorizedAs']['newValue']['id'] = 'unexpected-actor'
        self.assertFalse(self.board.compatible({'actorId': OWNER}, entry, after, policy))


if __name__ == '__main__':
    unittest.main()

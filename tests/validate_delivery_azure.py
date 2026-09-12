"""Bounded deterministic Azure planning, mutation recovery and admission regressions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-delivery/scripts'
sys.path.insert(0, str(SCRIPTS))
import azure_planning as planning
import azure_activation as activation
import azure
from azure_provider import AzureProvider, AzureError, GIT_SECURITY
from azure_transport import AzureTransport, NoRedirect
from delivery_contract import authority, validate_profile

OWNER = '11111111-1111-1111-1111-111111111111'
PROJECT = '22222222-2222-2222-2222-222222222222'
REPO = '33333333-3333-3333-3333-333333333333'
AREA = '44444444-4444-4444-4444-444444444444'


def profile():
    value = json.loads((SCRIPTS.parent / 'references/azure-default.json').read_text())
    value['roles'] = {k: [OWNER] for k in value['roles']}
    value['coordination']['repositoryId'] = REPO
    value['azure'] = {'organization': 'example', 'projectId': PROJECT,
        'areaRoots': [{'id': AREA, 'path': 'Example', 'includeDescendants': True}],
        'types': {k: {'initialState': 'New', 'fields': {'title': 'System.Title', 'outcome': 'System.Description',
            'owner': 'System.AssignedTo', 'acceptance': 'Microsoft.VSTS.Common.AcceptanceCriteria'}} for k in value['workTypes']}}
    return value


class FakeProvider:
    def __init__(self):
        self.profile = profile()
        self.settings = self.profile['azure']
        self.coord = self.profile['coordination']
        self.api = SimpleNamespace(organization='example')
        self.project = PROJECT
        self.state_path = 'state.json'
        self.state = planning.empty_state(self.profile)
        self.generation = 0
        self.items, self.files = {}, {}
        self.updates, self.comments = {}, {}
        self.created, self.validated = 0, 0
        self.fail_create = self.fail_record = False
        self.authorized = self.protected = True

    def authorize(self, role):
        if not self.authorized:
            raise AzureError('unauthorized')
        return {'id': OWNER}

    def assignment_value(self, identity):
        return identity

    def verify_protection(self):
        if not self.protected:
            raise AzureError('unprotected')
        return {'aclDigest': 'f' * 64}

    def areas(self):
        return {AREA: 'Example'}

    def discover_capabilities(self):
        fields = ['System.Title', 'System.Description', 'System.AssignedTo', 'System.AreaPath', 'System.State',
                  'Microsoft.VSTS.Common.AcceptanceCriteria']
        return {'types': {k: {'fields': [{'referenceName': f} for f in fields]} for k in self.profile['workTypes']},
                'identities': {OWNER: {}}}

    def read(self):
        return f'{self.generation:040x}', deepcopy(self.state)

    def commit(self, expected, state, **kwargs):
        if expected != f'{self.generation:040x}':
            raise AzureError('stale head', 409)
        if self.fail_record and any(op['state'] == 'applied' for op in state['operations'].values()):
            self.fail_record = False
            raise AzureError('lost recording commit')
        self.generation += 1
        self.state = deepcopy(state)
        self.files[(f'{self.generation:040x}', self.state_path)] = json.dumps(state)
        return f'{self.generation:040x}'

    def item(self, identity):
        if identity not in self.items:
            raise AzureError('inaccessible', 404)
        return deepcopy(self.items[identity])

    def evidence(self, identity):
        return {'id': identity, 'available': True, 'coverage': {'item': True, 'updates': True, 'comments': True},
                'status': 'observed', 'inScope': self.in_scope(self.items[identity]), 'item': self.item(identity),
                'updates': deepcopy(self.updates[identity]), 'comments': deepcopy(self.comments[identity])}

    def in_scope(self, item):
        return item['fields'].get('System.AreaPath', 'Example').startswith('Example')

    def create(self, kind, fields, relations, validate_only=False):
        if validate_only:
            self.validated += 1
            return {}
        self.created += 1
        identity = self.created
        value = {'id': identity, 'rev': 1, 'fields': {**deepcopy(fields), 'System.WorkItemType': self.profile['workTypes'][kind]},
                 'relations': deepcopy(relations)}
        if 'System.AssignedTo' in value['fields']:
            value['fields']['System.AssignedTo'] = {'id': value['fields']['System.AssignedTo']}
        self.items[identity] = value
        self.updates[identity] = [{'id': 1, 'rev': 1, 'fields': {k: {'newValue': v} for k, v in value['fields'].items()}}]
        self.comments[identity] = []
        for relation in relations:
            parent = self.items[int(relation['url'].rsplit('/', 1)[-1])]
            parent['relations'].append({'rel': 'System.LinkTypes.Hierarchy-Forward', 'url': 'https://example/items/' + str(identity)})
            parent['rev'] += 1
            self.updates[parent['id']].append({'id': len(self.updates[parent['id']]) + 1, 'rev': parent['rev'],
                'relations': {'added': [deepcopy(parent['relations'][-1])]}})
        if self.fail_create:
            self.fail_create = False
            raise AzureError('lost create response')
        return deepcopy(value)

    def update(self, identity, revision, fields, relations):
        item = self.items[identity]
        if item['rev'] != revision:
            raise AzureError('stale work-item revision', 412)
        item['fields'].update(fields)
        item['relations'].extend(relations)
        item['rev'] += 1
        self.updates[identity].append({'id': len(self.updates[identity]) + 1, 'rev': item['rev'],
            'fields': {k: {'newValue': deepcopy(v)} for k, v in fields.items()}, 'relations': {'added': deepcopy(relations)}})
        return deepcopy(item)

    def find_operation(self, operation_id):
        return [i for i, v in self.items.items() if 'Program Kit operation: ' + operation_id in v['fields'].get('System.Description', '')]

    def file(self, commit, path, repository=None):
        return self.files[(commit, path)]


class AzurePlanningTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeProvider()

    def graph(self):
        return [{'key': key, 'kind': kind, 'parent': parent, 'fields': {'System.Title': title,
            'System.Description': '<p>Scope and outcome</p>', 'System.AssignedTo': OWNER,
            'Microsoft.VSTS.Common.AcceptanceCriteria': 'AC-1 Observable result'}} for key, kind, parent, title in (
                ('E1', 'epic', None, 'Business outcome'), ('F1', 'feature', 'E1', 'Capability'),
                ('R1', 'requirement', 'F1', 'Observable slice'), ('T1', 'task', 'R1', 'Receiving integration'))]

    def approve(self, entries=None):
        proposal = planning.prepare(self.provider, entries or self.graph())
        planning.approve(self.provider, proposal, authority.digest(proposal), 'User accepted exact fixture proposal')
        return proposal

    def test_profile_schema_resolves_offline(self):
        self.assertEqual(validate_profile(profile())['provider'], 'azure')

    def test_continuation_pages_and_repeated_token_fail_closed(self):
        transport = object.__new__(AzureTransport)
        with patch.object(transport, 'request', side_effect=[
            ({'value': [1]}, {'X-MS-ContinuationToken': 'next'}), ({'value': [2]}, {})]) as request:
            self.assertEqual(transport.list('/_apis/projects'), [1, 2])
            self.assertEqual(request.call_args.kwargs['query']['continuationToken'], 'next')
        with patch.object(transport, 'request', return_value=({'value': [1]}, {'x-ms-continuationtoken': 'same'})):
            with self.assertRaisesRegex(AzureError, 'repeated pagination'):
                transport.list('/_apis/projects')

    def test_competing_proposal_cannot_redispatch_same_logical_work(self):
        first = self.approve([self.graph()[0]])
        second = self.approve([self.graph()[0]])
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, first['id'])
        with self.assertRaisesRegex(AzureError, 'unresolved operation'):
            planning.apply(self.provider, second['id'])
        self.assertEqual(self.provider.created, 1)

    def test_stale_coordinator_commit_prevents_external_dispatch(self):
        proposal = self.approve([self.graph()[0]])
        with patch.object(self.provider, 'commit', side_effect=AzureError('stale head', 409)):
            with self.assertRaises(AzureError):
                planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.created, 0)

    def test_recovery_rejects_unreviewed_fields_on_existing_item(self):
        item = self.provider.create('epic', self.graph()[0]['fields'], [])
        proposal = self.approve([{'key': 'E1', 'kind': 'epic', 'nativeId': item['id'],
                                 'fields': {'System.Title': 'Reviewed title'}}])
        self.provider.fail_record = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.provider.items[item['id']]['fields']['System.Description'] = 'Unreviewed human scope'
        self.provider.items[item['id']]['rev'] += 1
        with self.assertRaisesRegex(AzureError, 'outside the approved payload'):
            planning.recover(self.provider, proposal['id'] + ':E1', [])
        self.assertEqual(self.provider.state['operations'][proposal['id'] + ':E1']['state'], 'dispatched')

    def test_parent_automatic_revision_does_not_hide_link_comment_edit(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        parent = self.provider.items[2]
        parent['relations'][0]['attributes'] = {'comment': 'Changed by human'}
        parent['rev'] += 1
        with self.assertRaisesRegex(AzureError, 'planning basis changed'):
            planning.apply(self.provider, proposal['id'])

    def test_parent_comment_only_revision_is_not_an_automatic_child_change(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['rev'] += 1
        with self.assertRaisesRegex(AzureError, 'planning basis changed'):
            planning.apply(self.provider, proposal['id'])

    def test_links_are_checked_even_when_parent_revision_does_not_advance(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['rev'] = 1  # Azure can expose child links without a parent revision.
        planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['relations'].append({'rel': 'System.LinkTypes.Related', 'url': 'https://example/items/99'})
        with self.assertRaisesRegex(AzureError, 'planning basis changed'):
            planning.apply(self.provider, proposal['id'])

    def test_new_child_link_comment_is_not_treated_as_automatic(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['relations'][0]['attributes'] = {'comment': 'Human coordination decision'}
        with self.assertRaisesRegex(AzureError, 'planning basis changed'):
            planning.apply(self.provider, proposal['id'])

    def test_setup_unknown_outcome_is_never_replayed(self):
        import azure_setup
        api = SimpleNamespace(organization='example')
        api.call = lambda *a, **k: {'authenticatedUser': {'id': OWNER, 'descriptor': 'human'}}
        decision = {'organization': 'example', 'actor': {'id': OWNER}, 'id': 'setup',
                    'existingProjectId': None, 'projectName': 'Example'}
        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder) / 'journal.json'
            journal.write_text(json.dumps({'proposalDigest': authority.digest(decision),
                'operations': {'project': {'state': 'dispatched'}}}))
            with self.assertRaisesRegex(AzureError, 'outcome unknown'):
                azure_setup.apply(api, decision, journal, authority.digest(decision), 'accepted fixture')
            self.assertEqual(json.loads(journal.read_text())['operations']['project']['state'], 'dispatched')

    def test_protection_checks_actual_acl_and_effective_permissions(self):
        provider = AzureProvider(SimpleNamespace(organization='example'), profile())
        plan = {'token': 'exact-branch/', 'accessControlEntries': [{'descriptor': 'human', 'allow': 6, 'deny': 10248}]}
        provider.api.list = lambda *a, **k: [{'token': 'exact-branch', 'acesDictionary': {'human': plan['accessControlEntries'][0]}}]
        provider.api.call = lambda method, path, **k: {'value': [path.endswith('/6')]}
        with patch.object(provider, 'protection_plan', return_value=plan):
            self.assertTrue(provider.verify_protection()['administratorOverridePossible'])
            provider.api.call = lambda *a, **k: {'value': [True]}
            with self.assertRaisesRegex(AzureError, 'effective coordination permission'):
                provider.verify_protection()

    def test_full_graph_and_repeat_apply(self):
        proposal = self.approve()
        self.assertFalse(planning.apply(self.provider, proposal['id'])['implementationAdmission'])
        self.assertEqual(self.provider.created, 4)
        planning.apply(self.provider, proposal['id'])
        planning.approve(self.provider, proposal, authority.digest(proposal), 'same accepted proposal')
        self.assertEqual(self.provider.created, 4)
        self.assertEqual(self.provider.state['works']['T1']['parent'], 'R1')

    def test_human_epic_adoption_does_not_rewrite_description(self):
        fields = {'System.Title': 'Human entry', 'System.Description': 'Original human narrative', 'System.AssignedTo': OWNER}
        item = self.provider.create('epic', fields, [])
        entries = self.graph()
        entries[0] = {'key': 'E1', 'kind': 'epic', 'nativeId': item['id'], 'fields': {}}
        proposal = self.approve(entries)
        planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.items[item['id']]['fields']['System.Description'], fields['System.Description'])
        self.assertEqual(self.provider.created, 4)

    def test_parent_first_and_type_hierarchy_required(self):
        entries = self.graph()
        entries[1]['parent'] = None
        with self.assertRaises(AzureError):
            planning.prepare(self.provider, entries)
        with self.assertRaises(AzureError):
            planning.prepare(self.provider, list(reversed(self.graph())))

    def test_unknown_fields_and_state_changes_rejected(self):
        for key in ('System.State', 'Unknown.Field'):
            entries = self.graph()
            entries[0]['fields'][key] = 'Closed'
            with self.assertRaises(AzureError):
                planning.prepare(self.provider, entries)

    def test_approval_is_exact_and_role_bound(self):
        proposal = planning.prepare(self.provider, self.graph())
        with self.assertRaises(AzureError):
            planning.approve(self.provider, proposal, 'a' * 64, 'approved')
        self.provider.authorized = False
        with self.assertRaises(AzureError):
            planning.approve(self.provider, proposal, authority.digest(proposal), 'approved')

    def test_unprotected_store_cannot_approve(self):
        proposal = planning.prepare(self.provider, self.graph())
        self.provider.protected = False
        with self.assertRaises(AzureError):
            planning.approve(self.provider, proposal, authority.digest(proposal), 'approved')

    def test_changed_native_basis_invalidates_proposal(self):
        item = self.provider.create('epic', self.graph()[0]['fields'], [])
        entries = [{'key': 'E1', 'kind': 'epic', 'nativeId': item['id'], 'fields': {}}]
        proposal = planning.prepare(self.provider, entries)
        self.provider.items[item['id']]['rev'] += 1
        self.provider.items[item['id']]['fields']['System.Description'] = 'Changed business direction'
        with self.assertRaises(AzureError):
            planning.approve(self.provider, proposal, authority.digest(proposal), 'approved')

    def test_human_edit_after_approval_is_preserved(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['rev'] += 1
        self.provider.items[1]['fields']['System.Description'] = 'Human changed scope'
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.items[1]['fields']['System.Description'], 'Human changed scope')

    def test_lost_create_response_recovers_without_duplicate(self):
        proposal = self.approve()
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.created, 1)
        result = planning.recover(self.provider, proposal['id'] + ':E1', [])
        self.assertEqual(result['state'], 'applied')
        planning.apply(self.provider, proposal['id'])
        self.assertEqual(self.provider.created, 4)

    def test_lost_identity_record_recovers_without_duplicate(self):
        proposal = self.approve([self.graph()[0]])
        self.provider.fail_record = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.assertEqual(planning.recover(self.provider, proposal['id'] + ':E1', [])['state'], 'applied')
        self.assertEqual(self.provider.created, 1)

    def test_empty_recovery_never_redispatches(self):
        proposal = self.approve([self.graph()[0]])
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.provider.items = {}
        self.assertFalse(planning.recover(self.provider, proposal['id'] + ':E1', [])['retryAllowed'])
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])

    def test_duplicate_correlation_requires_review(self):
        proposal = self.approve([self.graph()[0]])
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.provider.items[2] = {**deepcopy(self.provider.items[1]), 'id': 2}
        with self.assertRaises(AzureError):
            planning.recover(self.provider, proposal['id'] + ':E1', [])

    def test_changed_recovery_payload_requires_review(self):
        proposal = self.approve([self.graph()[0]])
        self.provider.fail_create = True
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])
        self.provider.items[1]['fields']['System.Title'] = 'Human update'
        with self.assertRaises(AzureError):
            planning.recover(self.provider, proposal['id'] + ':E1', [])

    def test_only_observed_html_paragraph_whitespace_is_normalized(self):
        operation = {'fields': {'System.Description': '<p><a href="/one">Scope</a></p>'},
                     'entry': {'fields': {}}, 'relations': []}
        item = {'fields': {'System.Description': '<p><a href="/one">Scope</a> </p>'}}
        self.assertTrue(planning.matches(operation, item))
        item['fields']['System.Description'] = '<p><a href="/two">Scope</a> </p>'
        self.assertFalse(planning.matches(operation, item))

    def test_milestone_stays_on_business_item(self):
        entries = self.graph()
        entries[0]['milestones'] = [{'id': 'M1', 'name': 'Pilot accepted', 'ownerId': OWNER,
            'conditions': 'Receiving integration verified', 'requirementIds': ['R1'], 'targetDate': None}]
        proposal = self.approve(entries)
        planning.apply(self.provider, proposal['id'])
        self.assertIn('Pilot accepted', self.provider.items[1]['fields']['System.Description'])
        self.assertEqual(self.provider.state['works']['E1']['milestones'][0]['targetDate'], None)

    def test_profile_change_stops_operations(self):
        proposal = self.approve()
        self.provider.profile['space'] = 'different'
        with self.assertRaises(AzureError):
            planning.apply(self.provider, proposal['id'])

    def test_native_identity_cannot_be_adopted_twice(self):
        proposal = self.approve([self.graph()[0]])
        planning.apply(self.provider, proposal['id'])
        with self.assertRaises(AzureError):
            planning.prepare(self.provider, [{'key': 'OTHER', 'kind': 'epic', 'nativeId': 1}])

    def test_concurrent_native_adoption_is_rechecked_at_dispatch(self):
        item = self.provider.create('epic', self.graph()[0]['fields'], [])
        first = self.approve([{'key': 'FIRST', 'kind': 'epic', 'nativeId': item['id']}])
        second = self.approve([{'key': 'SECOND', 'kind': 'epic', 'nativeId': item['id']}])
        planning.apply(self.provider, first['id'])
        with self.assertRaisesRegex(AzureError, 'native identity adopted concurrently'):
            planning.apply(self.provider, second['id'])

    def test_individual_identity_accepts_omitted_container_flag_but_rejects_group(self):
        provider = AzureProvider(SimpleNamespace(organization='example'), profile())
        person = {'id': OWNER, 'descriptor': 'human', 'isActive': True,
                  'properties': {'SchemaClassName': {'$value': 'User'}}}
        provider.api.call = lambda *a, **k: {'value': [person]}
        self.assertIn(OWNER, provider.identities())
        person['isContainer'] = True
        with self.assertRaisesRegex(AzureError, 'group identity'):
            provider.identities()

    def test_azure_branch_token_and_transport_paths(self):
        provider = AzureProvider(SimpleNamespace(organization='example'), profile())
        self.assertEqual(GIT_SECURITY, '2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87')
        self.assertTrue(provider.security_token().endswith('/63006f006f007200640069006e006100740069006f006e00/'))
        transport = object.__new__(AzureTransport)  # Path rejection precedes TLS/credential setup.
        with patch.object(transport, 'authenticate', side_effect=AssertionError('must not authenticate')):
            for value in ('https://evil.test', '//evil.test', '/../other', '/%2e%2e/other', '/api?url=other'):
                with self.assertRaises(AzureError):
                    transport.call('GET', value)
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other'))

    def configured_repository(self):
        temporary = tempfile.TemporaryDirectory(prefix='delivery-azure-activation-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        import governance_state
        roadmap = root / 'docs/architecture/specification-roadmap.md'
        roadmap.parent.mkdir(parents=True)
        roadmap.write_text('### SPC-001: Existing slice\n' + ''.join(
            f'- **{key}**: {"Ready" if key == "Status" else "none"}\n' for key in sorted(governance_state.REQUIRED_RECORD_FIELDS)))
        directory = root / '.program-kit/delivery'
        directory.mkdir(parents=True)
        content = json.dumps(self.provider.profile, indent=2) + '\n'
        (directory / 'profile.json').write_bytes(content.encode())
        self.provider.files[('a' * 40, 'profile.json')] = content
        binding = {'schemaVersion': 1, 'recordType': 'binding', 'state': 'prepared', 'space': self.provider.profile['space'],
            'repositoryId': 'consumer-repo', 'teamId': 'team', 'provider': 'azure', 'activationId': None,
            'profile': {'repositoryId': REPO, 'commit': 'a' * 40, 'path': 'profile.json',
                'sha256': hashlib.sha256(content.encode()).hexdigest(), 'snapshot': '.program-kit/delivery/profile.json'},
            'artifactPaths': {'roadmap': 'docs/architecture/specification-roadmap.md'},
            'teamDefaults': {'area': None, 'iteration': None},
            'workBindings': {'SPC-001': {'requirementId': 'R1', 'executionMode': 'direct', 'taskId': None}}}
        (root / authority.BINDING).write_text(json.dumps(binding))
        (root / authority.HISTORY).write_text(json.dumps({'schemaVersion': 1, 'recordType': 'history', 'records': []}))
        import azure_reconcile as reconcile
        report = reconcile.sync(self.provider, ['R1'])
        decisions = [{'nativeId': finding['nativeId'], 'classification': 'baseline', 'reason': 'Accepted deterministic fixture basis',
                      'affectedKeys': finding['provisionalImpact'], 'technicalRevisionRequired': False} for finding in report['findings']]
        if decisions:
            review = reconcile.propose_review(self.provider, report['id'], decisions)
            for role in ('business', 'technical'):
                reconcile.approve_review(self.provider, review, authority.digest(review), 'accepted fixture', role)
            reconcile.apply_review(self.provider, review['id'])
        return root, binding

    def test_activation_and_repeat_are_verified_and_planning_only(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        root, binding = self.configured_repository()
        decision = activation.prepare(self.provider, root, binding)
        digest = authority.digest(decision)
        self.assertTrue(activation.apply(self.provider, root, decision, digest, 'accepted')['planningOnly'])
        original = (root / authority.HISTORY).read_bytes()
        activation.apply(self.provider, root, decision, digest, 'accepted')
        self.assertEqual(original, (root / authority.HISTORY).read_bytes())
        enabled = authority.read(root / authority.BINDING)
        self.assertEqual(activation.admit(self.provider, root, enabled, 'SPC-001')['admission'], 'refinement-only')
        with self.assertRaises(AzureError):
            activation.admit(self.provider, root, enabled, 'SPC-002')

    def test_active_repository_cannot_switch_authority(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        root, binding = self.configured_repository()
        roadmap = root / binding['artifactPaths']['roadmap']
        roadmap.write_text(roadmap.read_text().replace('**Status**: Ready', '**Status**: Active'))
        with self.assertRaisesRegex(AzureError, 'active implementation'):
            activation.prepare(self.provider, root, binding)

    def test_activation_rejects_changed_handoff_and_remote_profile(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        root, binding = self.configured_repository()
        decision = activation.prepare(self.provider, root, binding)
        roadmap = root / binding['artifactPaths']['roadmap']
        roadmap.write_text(roadmap.read_text() + '\nChanged roadmap\n')
        with self.assertRaises(AzureError):
            activation.apply(self.provider, root, decision, authority.digest(decision), 'accepted')
        self.provider.files[('a' * 40, 'profile.json')] += ' '
        with self.assertRaises(AzureError):
            activation.prepare(self.provider, root, binding)

    def test_forged_local_activation_has_no_provider_admission(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        root, binding = self.configured_repository()
        binding.update(state='enabled', activationId='fake')
        with self.assertRaisesRegex(AzureError, 'not confirmed'):
            activation.admit(self.provider, root, binding)

    def test_changed_business_scope_blocks_refinement_after_activation(self):
        proposal = self.approve()
        planning.apply(self.provider, proposal['id'])
        root, binding = self.configured_repository()
        decision = activation.prepare(self.provider, root, binding)
        activation.apply(self.provider, root, decision, authority.digest(decision), 'accepted')
        self.provider.items[3]['rev'] += 1
        self.provider.items[3]['fields']['System.Description'] = 'Changed by business owner'
        with self.assertRaisesRegex(AzureError, 'unreviewed or unavailable history'):
            activation.admit(self.provider, root, authority.read(root / authority.BINDING), 'SPC-001')


if __name__ == '__main__':
    unittest.main()

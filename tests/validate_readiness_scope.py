"""Enforce accepted slice scope without treating proposal prose as lifecycle state."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import validate_bootstrap_lifecycle as fixture

g, life = fixture.governance, fixture.lifecycle


class ReadinessScopeTests(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.directory = tempfile.TemporaryDirectory(prefix='pk-ready-scope-')
        self.root = Path(self.directory.name)
        os.chdir(self.root)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(os.chdir, self.previous)
        fixture.setup(self.root)
        self.model = life.load(self.root / g.ARCHITECTURE_MAP)
        self.scope = life.load(self.root / life.SCOPE)
        self.candidate = self.model['strategic_model']['candidate_slices'][0]
        journey = next(j for j in self.model['strategic_model']['journeys'] if j['id'] == self.candidate['journey'])
        self.edge = next(e for e in self.model['relationships'] if e['id'] == journey['steps'][0]['relationship'])
        self.owner = next(iter(self.scope['decisions']))
        self.records = g.roadmap_records(self.root / g.ROADMAP)
        self.records[0]['Scope'] += ' Canonical candidate: ' + self.candidate['id']
        self.records[0]['Status'] = 'Ready'
        for step in journey['steps']:
            edge = next(e for e in self.model['relationships'] if e['id'] == step['relationship'])
            edge['status'] = 'accepted'
            for key in ('source', 'target'):
                next(e for e in self.model['elements'] if e['id'] == edge[key])['status'] = 'accepted'

    def save(self):
        life.write(self.root / g.ARCHITECTURE_MAP, self.model)
        life.write(self.root / life.SCOPE, self.scope)

    def follow_on(self, *, scoped=True, status='Proposed'):
        self.model = life.load(self.root / g.ARCHITECTURE_MAP)
        decision = copy.deepcopy(self.model['decisions'][0])
        decision.update(id='bootstrap-proof-assignment',
                        path='docs/architecture/decisions/bootstrap-proof-assignment.md',
                        status=status)
        (self.root / decision['path']).write_text(
            '# Bootstrap proof assignment\n\nStatus: ' + status + '\n', encoding='utf-8')
        decision['sha256'] = life.digest(self.root / decision['path'])
        self.model['decisions'].append(decision)
        if scoped:
            self.scope['decisions'][decision['id']] = {'elements': [], 'relationships': []}
        self.save()
        (self.root / g.ROADMAP).write_text(
            fixture.fixture.roadmap('`bootstrap-proof-assignment`'), encoding='utf-8')
        fixture.ledger(self.root, [])
        return decision

    def test_fresh_scoped_follow_on_reaches_review_without_premature_acceptance(self):
        decision = self.follow_on()
        g.synchronize_lifecycle()
        g.synchronize_roadmap_views()
        g.validate_roadmap(True)
        reviewed = {r['candidate_id'] for r in g.reviewed_adr_records()}
        self.assertIn(decision['id'], reviewed)
        self.assertFalse(g.accepted_adr(decision['id']))
        self.assertFalse((self.root / g.BOOTSTRAP_APPROVAL).exists())
        g.write_review('bootstrap')
        g.accept_bootstrap('approve')  # Simulated review in this disposable fixture only.
        self.assertTrue(g.accepted_adr(decision['id']))
        g.validate_bootstrap(True, True)
        self.assertTrue(g.render_readiness()['eligible'])
        g.complete_bootstrap()
        g.validate_completion()

    def test_unscoped_follow_on_cannot_reach_review(self):
        self.follow_on(scoped=False)
        with self.assertRaisesRegex(g.GovernanceStateError, 'unresolved ADRs: bootstrap-proof-assignment'):
            g.validate_roadmap(True)

    def test_rejected_follow_on_is_not_pending_review_authority(self):
        self.follow_on(status='Rejected')
        with self.assertRaisesRegex(g.GovernanceStateError, 'unresolved ADRs: bootstrap-proof-assignment'):
            g.validate_roadmap(True)

    def test_pending_follow_on_requires_recovery_review_after_bootstrap_approval(self):
        self.follow_on()
        life.write(self.root / g.BOOTSTRAP_APPROVAL, {'status': 'Approved'})
        with self.assertRaisesRegex(g.GovernanceStateError, 'unresolved ADRs: bootstrap-proof-assignment'):
            g.validate_roadmap(True)
        with patch.object(g, 'PENDING_RECOVERY_REVIEW', True):
            g.validate_roadmap(True)

    def test_stale_follow_on_cannot_be_synchronized(self):
        decision = self.follow_on()
        with (self.root / decision['path']).open('a', encoding='utf-8') as stream:
            stream.write('\nUnreviewed change.\n')
        with self.assertRaisesRegex(g.GovernanceStateError, 'inventory is stale'):
            g.synchronize_roadmap_views()

    def test_missing_edge_requires_scope_then_actual_acceptance(self):
        self.edge['status'] = 'proposed'
        for item in self.scope['decisions'].values():
            item['relationships'] = [x for x in item['relationships'] if x != self.edge['id']]
        self.save()
        with self.assertRaisesRegex(g.GovernanceStateError, 'outside accepted or pending review scope'):
            g.validate_roadmap_architecture_scope(self.records)
        self.edge['decision_refs'].append(self.owner) if self.owner not in self.edge['decision_refs'] else None
        self.scope['decisions'][self.owner]['relationships'].append(self.edge['id'])
        self.save()
        g.validate_roadmap_architecture_scope(self.records)
        life.write(self.root / g.BOOTSTRAP_APPROVAL, {'status': 'Approved'})
        with self.assertRaisesRegex(g.GovernanceStateError, 'outside accepted'):
            g.validate_roadmap_architecture_scope(self.records)
        self.edge['status'] = 'accepted'
        self.save()
        g.validate_roadmap_architecture_scope(self.records)

    def test_required_endpoint_is_checked_but_unrelated_proposals_are_allowed(self):
        self.save()
        g.validate_roadmap_architecture_scope(self.records)
        endpoint = next(e for e in self.model['elements'] if e['id'] == self.edge['target'])
        endpoint['status'] = 'proposed'
        for item in self.scope['decisions'].values():
            item['elements'] = [x for x in item['elements'] if x != endpoint['id']]
        self.save()
        with self.assertRaisesRegex(g.GovernanceStateError, endpoint['id']):
            g.validate_roadmap_architecture_scope(self.records)

    def test_explicit_actor_is_a_confirmed_fact_not_a_pending_component(self):
        endpoint = next(e for e in self.model['elements'] if e['id'] == self.edge['source'])
        endpoint.update(type='person', status='explicit')
        for item in self.scope['decisions'].values():
            item['elements'] = [x for x in item['elements'] if x != endpoint['id']]
        self.save()
        g.validate_roadmap_architecture_scope(self.records)

    def test_proposal_history_does_not_need_a_successor_after_approval(self):
        new = self.follow_on()
        path = self.root / new['path']
        with path.open('a', encoding='utf-8') as stream:
            stream.write('\nThe founding ADRs remain Proposed. SPEC-001 remains Blocked.\n'
                         'Final architecture review remains mandatory. No runtime success is asserted.\n')
        new['sha256'] = life.digest(path)
        self.save()
        fixture.ledger(self.root, [])
        g.synchronize_lifecycle()
        g.synchronize_roadmap_views()
        g.validate_bootstrap_consistency()
        g.write_review('bootstrap')
        g.accept_bootstrap('approve')
        self.assertTrue(g.render_readiness()['eligible'])
        self.assertIn('founding ADRs remain Proposed', path.read_text(encoding='utf-8'))
        # A substantive unreviewed change still fails the accepted source hashes.
        with path.open('a', encoding='utf-8') as stream:
            stream.write('\nSwitch the selected provider.\n')
        self.assertFalse(g.render_readiness()['eligible'])


if __name__ == '__main__':
    unittest.main()

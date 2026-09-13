"""Reject incomplete slice acceptance and live ADR status contradictions before readiness."""
import copy
import os
from pathlib import Path
import tempfile
import unittest

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

    def test_stale_adr_needs_reviewed_supersession_not_unscoped_proposal(self):
        old = self.model['decisions'][0]
        with (self.root / old['path']).open('a', encoding='utf-8') as stream:
            stream.write('\n' + self.records[0]['id'] + ' remains Blocked.\n')
        self.save()
        with self.assertRaisesRegex(g.GovernanceStateError, 'contradicts authoritative status'):
            g.validate_adr_roadmap_claims(self.records)
        new = copy.deepcopy(old)
        new.update(id='reviewed-correction', path='docs/architecture/decisions/reviewed-correction.md',
                   status='Proposed', supersedes=[old['id']])
        (self.root / new['path']).write_text('# Scoped correction\nStatus: Proposed\n', encoding='utf-8')
        new['sha256'] = life.digest(self.root / new['path'])
        self.model['decisions'].append(new)
        self.save()
        with self.assertRaisesRegex(g.GovernanceStateError, 'contradicts authoritative status'):
            g.validate_adr_roadmap_claims(self.records)
        self.scope['decisions'][new['id']] = {'elements': [], 'relationships': []}
        self.save()
        g.validate_adr_roadmap_claims(self.records)
        life.write(self.root / g.BOOTSTRAP_APPROVAL, {'status': 'Approved'})
        with self.assertRaisesRegex(g.GovernanceStateError, 'contradicts authoritative status'):
            g.validate_adr_roadmap_claims(self.records)
        new['status'] = 'Accepted'
        self.save()
        g.validate_adr_roadmap_claims(self.records)


if __name__ == '__main__':
    unittest.main()

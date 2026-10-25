"""Offline fictional product-question handoff; no agents, runtime proof or new ledger."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import specification_intake as intake
import phase_obligations as phases


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureDirectory(prefix='product-frontier-', native=True)
        self.addCleanup(self.fixture.cleanup)
        self.root = Path(self.fixture.name).resolve()
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.items = [
            {'id': 'retention-policy', 'question': 'How long are requests retained?',
             'classification': 'deferred', 'disposition': 'Feature owner will settle the policy',
             'blocks': '', 'trigger': 'An intentionally free-text later trigger', 'evidence': ['fictional-intent']},
            {'id': 'future-reporting', 'question': 'Which future reporting format?',
             'classification': 'deferred', 'disposition': 'Reporting owner, when reporting is selected',
             'blocks': '', 'trigger': 'Reporting selection', 'evidence': ['fictional-intent']},
        ]
        self.write_frontier()
        self.path = intake.begin(self.root, 'SPEC-001', 'Record a request', feature='register-request')
        self.brief = intake.read(self.path)
        self.brief.update({name: 'Fictional reviewed ' + name for name in intake.FIELDS})
        self.brief['decisions'] = [self.decision(item) for item in self.items]
        self.brief['decisions'][1].update(disposition='excluded', answer='Reporting is unrelated to registration',
                                          rationale='The selected feature records requests and exposes no reports')
        self.save()
        self.feature = self.root / 'specs/001-register'
        self.feature.mkdir(parents=True)

    def write_frontier(self):
        intake.atomic_write(self.root / intake.governance.BOOTSTRAP_INTAKE, {'open_items': self.items})

    def decision(self, item):
        return {'id': 'decision-' + item['id'], 'question': item['question'], 'answer': 'Resolve with the actual feature owner',
                'disposition': 'deferred', 'blocking': False, 'dependsOn': [],
                'owner': 'Registration feature owner', 'trigger': 'Before implementing retention', 'duePhase': 'implementation',
                'provenance': 'Fictional source and applicability review', 'rationale': 'Registration owns its retention policy',
                'productOpenItem': item['id'], 'productOpenItemSha256': intake.digest(item)}

    def save(self):
        intake.atomic_write(self.path, self.brief)

    def confirm(self):
        review = intake.review(self.root, 'SPEC-001', feature='register-request')
        intake.confirm(self.root, 'SPEC-001', review['reviewHash'], 'Fictional deterministic fixture',
                       'Simulated explicit feature review; no real human acceptance claim', feature='register-request')
        result = intake.check(self.root, 'SPEC-001', feature='register-request')
        (self.feature / 'spec.md').write_text(
            '- **Specification roadmap entry**: SPEC-001\n'
            '- **Specification feature ID**: register-request\n'
            f"- **Confirmed intake brief**: {result['brief']}\n"
            f"- **Confirmed intake SHA256**: {result['briefHash']}\n", encoding='utf-8')

    def test_frontier_is_visible_and_applicability_is_explicit(self):
        frontier = intake.context(self.root, 'SPEC-001', feature='register-request')['productFrontier']
        self.assertEqual([item['id'] for item in self.items], [item['id'] for item in frontier])
        missing = self.brief['decisions'].pop()
        self.save()
        with self.assertRaisesRegex(ValueError, 'Review each product frontier'):
            intake.review(self.root, 'SPEC-001', feature='register-request')
        self.brief['decisions'].append(missing)
        self.save()
        self.confirm()
        review = self.path.with_name('review.md').read_text(encoding='utf-8')
        self.assertIn('Reporting is unrelated', review)
        self.assertIn('retention-policy', review)
        self.assertFalse((self.root / 'docs/architecture/bootstrap-prerequisites.json').exists())

    def test_relevant_deferral_blocks_only_its_explicit_due_phase(self):
        self.confirm()
        phases.require_due_product_decisions(self.root, self.feature, 'after-plan')
        rows = phases.product_decisions(self.root, self.feature, 'implementation')
        self.assertEqual(['retention-policy'], [row['id'] for row in rows if row['requiredNow']])
        with self.assertRaisesRegex(ValueError, 'retention-policy'):
            phases.require_due_product_decisions(self.root, self.feature, 'implementation')
        # The normal phase command rejects before invoking engineering/runtime work.
        with patch.object(phases, 'intent', side_effect=AssertionError('Engineering ran before due decision')):
            with self.assertRaisesRegex(ValueError, 'retention-policy'):
                phases.check(self.root, self.feature, 'implementation')
        self.brief['decisions'][0].update(disposition='answered', answer='Retain requests for 30 days',
                                          provenance='Fictional feature owner answer')
        self.save()
        with self.assertRaisesRegex(ValueError, 'Feature intent changed'):
            phases.require_due_product_decisions(self.root, self.feature, 'implementation')
        self.confirm()
        phases.require_due_product_decisions(self.root, self.feature, 'implementation')

    def test_source_drift_is_scoped_and_new_unrelated_frontier_does_not_reconfirm(self):
        self.confirm()
        original_confirmation = self.path.with_name('confirmation.json').read_bytes()
        self.items.append({**copy.deepcopy(self.items[1]), 'id': 'future-billing'})
        self.write_frontier()
        intake.check_spec(self.root, self.feature / 'spec.md')
        self.assertEqual(original_confirmation, self.path.with_name('confirmation.json').read_bytes())
        self.items[0]['question'] = 'Changed actual retention condition?'
        self.write_frontier()
        with self.assertRaisesRegex(ValueError, 'changed; review'):
            intake.check_spec(self.root, self.feature / 'spec.md')

    def test_unknown_duplicate_stale_and_runtime_proof_links_are_rejected(self):
        for change in ({'productOpenItem': 'unknown'}, {'productOpenItemSha256': '0' * 64},
                       {'verification': 'compatibility'}):
            with self.subTest(change=change):
                candidate = copy.deepcopy(self.brief)
                candidate['decisions'][0].update(change)
                with self.assertRaises(ValueError):
                    intake.require_product_carryover(candidate, intake.product_frontier(self.root))
        candidate = copy.deepcopy(self.brief)
        candidate['decisions'].append(copy.deepcopy(candidate['decisions'][0]))
        with self.assertRaisesRegex(ValueError, 'unique stable IDs'):
            intake.require_product_carryover(candidate, intake.product_frontier(self.root))


if __name__ == '__main__':
    unittest.main()

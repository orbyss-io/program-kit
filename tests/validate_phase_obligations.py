"""Offline negative controls for missing, stale and incomplete knowledge evidence."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import phase_obligations as obligations
from semantic_contract import validate_contract


class ObligationTests(unittest.TestCase):
    def test_future_owner_evidence_does_not_block_scoped_inventory(self):
        self.write('docs/architecture/bootstrap-decisions.json', {'persistence': [
            {'owner': 'Future', 'admission': {'atomicity': ['docs/not-yet-written.md']}},
            {'owner': 'Reservations', 'admission': {'atomicity': ['specs/001-reservation/plan.md']}}]})
        self.write('specs/001-reservation/artifact-ownership.json', {'persistenceOwners': ['Reservations']})
        inventory = obligations.inventory(self.root, self.feature)
        self.assertIn('specs/001-reservation/plan.md', inventory)
        self.write('specs/001-reservation/artifact-ownership.json', {'persistenceOwners': ['Future']})
        with self.assertRaisesRegex(ValueError, 'Missing declared verification input'):
            obligations.inventory(self.root, self.feature)

    def setUp(self):
        # Unit scope: intake's native integration is exercised by validate_specification_intake.
        authority = patch.object(obligations, 'require_confirmed_intake')
        authority.start()
        self.addCleanup(authority.stop)
        self.temp = tempfile.TemporaryDirectory(prefix='phase-obligations-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.feature = self.root / 'specs/001-reservation'
        self.feature.mkdir(parents=True)
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': []})
        (self.feature / 'plan.md').write_text('Reserve an equipment slot; duplicate admission returns the original reservation.')
        self.semantic = {'schemaVersion': 1, 'scope': 'Equipment slot reservation',
                         'subjects': [], 'policies': [], 'effects': [], 'admissions': [],
                         'outcomes': [{'id': 'accepted', 'kind': 'success', 'owner': 'Reservations', 'checkIds': ['reservation']} ]}
        self.write('specs/001-reservation/semantic-contract.json', self.semantic)
        self.expected = obligations.project(self.root, self.feature, 'planning')
        records = [{'id': r['id'], 'owner': 'Reservations', 'applicability': 'applicable',
                    'rationale': 'A reservation has explicit outcomes and owned behavior',
                    'designRefs': ['specs/001-reservation/plan.md'],
                    'checkIds': ['reservation'] if r['proof'] == 'behavior' else []}
                   for r in self.expected['requirements']]
        self.write('specs/001-reservation/obligation-design.json', {'schemaVersion': 1, 'requirements': records})
        runner = self.root / 'run_tests.py'
        runner.write_text('''import pathlib, unittest, xml.etree.ElementTree as E
class Reservation(unittest.TestCase):
 def test_idempotency(self):
  slots = {}
  def reserve(key): return slots.setdefault(key, len(slots) + 1)
  self.assertEqual(reserve('same'), reserve('same'))
  self.assertEqual(1, len(slots))
result = unittest.TestResult()
unittest.defaultTestLoader.loadTestsFromTestCase(Reservation).run(result)
suite = E.Element('testsuite')
case = E.SubElement(suite, 'testcase', classname='Reservation', name='test_idempotency')
if not result.wasSuccessful(): E.SubElement(case, 'failure')
pathlib.Path('artifacts').mkdir(exist_ok=True)
E.ElementTree(suite).write('artifacts/reservation.xml')
raise SystemExit(not result.wasSuccessful())
''', encoding='utf-8')
        self.plan = {'schemaVersion': 1, 'suites': [{'command': [sys.executable, 'run_tests.py'],
                       'result': 'artifacts/reservation.xml', 'format': 'junit',
                       'checks': {'reservation': ['Reservation.test_idempotency']}}]}
        self.write('specs/001-reservation/verification-plan.json', self.plan)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def review(self, stage='design'):
        self.write('specs/001-reservation/obligation-review.json', {
            'basis': obligations.digest(obligations.review_basis(self.root, self.feature, stage)),
            'stage': stage, 'verdict': 'accepted', 'reviewer': 'fixture reviewer', 'source': 'deterministic fixture',
            'findings': [], 'requirements': {r['id']: 'Reviewed reservation behavior and mapped tests'
                                            for r in self.expected['requirements']}})

    def test_project_before_plan_then_current_delivery(self):
        obligations.check(self.root, self.feature, 'planning')
        self.review()
        obligations.check(self.root, self.feature, 'after-plan')
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        obligations.check(self.root, self.feature, 'delivery')

    def test_dotnet_intent_projects_engineering_before_source_exists(self):
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet']})
        projected = obligations.project(self.root, self.feature, 'planning')
        ids = {r['id'] for r in projected['requirements']}
        self.assertTrue({'dotnet-async', 'dotnet-concurrency', 'dotnet-lifetime', 'dotnet-construction',
                         'dotnet-queries', 'dotnet-runtime-io', 'dotnet-runtime-security',
                         'dotnet-source-quality'} <= ids)
        self.assertTrue(any(key.endswith('#Deferred initialization') for key in projected['knowledgeHashes']))
        self.assertIn('Deferred initialization', (self.feature / 'phase-context.md').read_text())
        with self.assertRaisesRegex(ValueError, 'every applicable requirement'):
            obligations.design(self.root, self.feature, projected)

    def test_scoped_knowledge_changes_revoke_only_affected_hashes(self):
        path = self.root / 'knowledge.md'
        path.write_text('# Profile\n\n## Async\nObserve work.\n\n## Memory\nOwn buffers.\n')
        rules = [{'sources': ['knowledge.md'], 'sections': {'knowledge.md': ['Async']}}]
        original = obligations.knowledge_hashes(rules, self.root)
        path.write_text(path.read_text().replace('Own buffers.', 'Return buffers.'))
        self.assertEqual(original, obligations.knowledge_hashes(rules, self.root))
        path.write_text(path.read_text().replace('Observe work.', 'Observe all work.'))
        self.assertNotEqual(original, obligations.knowledge_hashes(rules, self.root))
        path.write_text(path.read_text().replace('## Async', '## Missing'))
        with self.assertRaisesRegex(ValueError, 'Missing/ambiguous'):
            obligations.knowledge_hashes(rules, self.root)

    def test_ambiguous_knowledge_section_fails_closed(self):
        path = self.root / 'knowledge.md'
        path.write_text('## Async\nOne.\n## Async\nTwo.\n')
        with self.assertRaisesRegex(ValueError, 'Missing/ambiguous'):
            obligations.knowledge_section(path, 'Async')

    def test_delivered_roadmap_requires_current_executed_proof(self):
        import os
        import governance_state as governance
        from validate_governance_state import roadmap
        (self.feature / 'spec.md').write_text('- **Specification roadmap entry**: SPEC-001\n', encoding='utf-8')
        roadmap_path = self.root / 'docs/architecture/specification-roadmap.md'
        roadmap_path.write_text(roadmap(status='Delivered'), encoding='utf-8')
        obligations.project(self.root, self.feature, 'planning')
        previous = Path.cwd()
        os.chdir(self.root)
        try:
            with self.assertRaisesRegex(ValueError, 'lacks current required evidence'):
                governance.validate_roadmap(False)
            obligations.execute(self.root, self.feature)
            self.review('delivery')
            governance.validate_roadmap(False)
            # The active pointer is navigation; changing it cannot revoke another
            # feature's proof or force unrelated feature revalidation.
            self.write('.specify/feature.json', {'feature_directory': 'specs/002-other'})
            governance.validate_roadmap(False)
            (self.root / 'run_tests.py').write_text('raise Exception("changed behavior")', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'lacks current required evidence'):
                governance.validate_roadmap(False)
        finally:
            os.chdir(previous)

    def test_deleted_requirement_cannot_disable_itself(self):
        altered = copy.deepcopy(self.expected)
        altered['requirements'].pop()
        self.write('specs/001-reservation/phase-obligations.json', altered)
        with self.assertRaisesRegex(ValueError, 'projection'):
            obligations.check(self.root, self.feature, 'planning')

    def test_green_command_cannot_reuse_prior_test_output(self):
        obligations.execute(self.root, self.feature)
        self.plan['suites'][0]['command'] = [sys.executable, '-c', 'pass']
        self.write('specs/001-reservation/verification-plan.json', self.plan)
        with self.assertRaises(FileNotFoundError):
            obligations.execute(self.root, self.feature)
        self.assertEqual('failed', obligations.read(self.feature / 'verification-results.json')['status'])

    def test_absent_named_case_fails(self):
        self.plan['suites'][0]['checks']['reservation'] = ['Reservation.missing']
        self.write('specs/001-reservation/verification-plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'Missing, failed or skipped'):
            obligations.execute(self.root, self.feature)

    def test_missing_suite_mapping_fails(self):
        self.plan['suites'][0]['checks'] = {}
        self.write('specs/001-reservation/verification-plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'cover each required'):
            obligations.execute(self.root, self.feature)

    def test_source_change_revokes_review_and_results(self):
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        (self.root / 'reservation.py').write_text('raise RuntimeError("changed")')
        with self.assertRaisesRegex(ValueError, 'review is stale'):
            obligations.check(self.root, self.feature, 'delivery')
        self.review('delivery')
        with self.assertRaisesRegex(ValueError, 'results are stale'):
            obligations.check(self.root, self.feature, 'delivery')

    def test_tampered_result_file_fails(self):
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        (self.root / 'artifacts/reservation.xml').write_text('<testsuite/>')
        with self.assertRaisesRegex(ValueError, 'result changed'):
            obligations.check(self.root, self.feature, 'delivery')

    def test_receipt_cannot_omit_result_hashes(self):
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        receipt = obligations.read(self.feature / 'verification-results.json')
        receipt['outputs'] = {}
        self.write('specs/001-reservation/verification-results.json', receipt)
        with self.assertRaisesRegex(ValueError, 'result hashes'):
            obligations.check(self.root, self.feature, 'delivery')

    def test_receipt_cannot_change_test_identity(self):
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        receipt = obligations.read(self.feature / 'verification-results.json')
        receipt['checks']['reservation']['tests'] = ['invented']
        self.write('specs/001-reservation/verification-results.json', receipt)
        with self.assertRaisesRegex(ValueError, 'No passing executed tests'):
            obligations.check(self.root, self.feature, 'delivery')

    def test_explicit_managed_adapter_change_revokes_proof(self):
        self.write('.program-kit/custom-adapter.json', {'value': 1})
        design = obligations.read(self.feature / 'obligation-design.json')
        design['inputPaths'] = ['.program-kit/custom-adapter.json']
        self.write('specs/001-reservation/obligation-design.json', design)
        obligations.execute(self.root, self.feature)
        self.review('delivery')
        self.write('.program-kit/custom-adapter.json', {'value': 2})
        with self.assertRaisesRegex(ValueError, 'stale'):
            obligations.check(self.root, self.feature, 'delivery')

    def test_domain_description_is_not_a_state_model(self):
        value = copy.deepcopy(self.semantic)
        value['subjects'] = [{'id': 'slot', 'identity': 'slot id', 'stateful': True,
                              'lifecycle': 'Versioned independently when rules change'}]
        with self.assertRaisesRegex(ValueError, 'states'):
            validate_contract(value)

    def test_required_handover_cannot_be_fire_and_forget(self):
        value = copy.deepcopy(self.semantic)
        value['outcomes'].append({'id': 'failed', 'kind': 'failure', 'owner': 'Reservations', 'checkIds': ['failed']})
        value['admissions'] = [{'id': 'save', 'requirement': 'required', 'checkIds': ['save'],
                                 **{k: 'defined' for k in ('owner', 'consistency', 'acknowledgement', 'idempotency', 'retry', 'ordering', 'timeout')},
                                 'failureOutcome': 'failed', 'successAfterAcknowledgement': False}]
        with self.assertRaisesRegex(ValueError, 'acknowledge'):
            validate_contract(value)

    def test_due_deferral_cannot_hide_in_prose(self):
        from validate_governance_state import roadmap
        path = self.root / 'docs/architecture/specification-roadmap.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(roadmap().replace('SPEC-001', 'SPC-001'))
        self.write('.specify/feature.json', {'roadmap_entry_id': 'SPC-001'})
        brief = {'decisions': [{'id': 'storage', 'disposition': 'deferred', 'trigger': 'Before plan approval'}]}
        self.write('.program-kit/specification-intake/SPC-001/brief.json', brief)
        with self.assertRaisesRegex(ValueError, 'structured duePhase'):
            obligations.check(self.root, self.feature, 'planning')
        brief['decisions'][0]['duePhase'] = 'after-plan'
        self.write('.program-kit/specification-intake/SPC-001/brief.json', brief)
        obligations.check(self.root, self.feature, 'planning')
        with self.assertRaisesRegex(ValueError, 'is due'):
            obligations.check(self.root, self.feature, 'after-plan')

    def test_missing_web_sources_do_not_disable_requirements(self):
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'typescript-web']})
        ids = {r['id'] for r in obligations.model(self.root, self.feature)['requirements']}
        self.assertTrue({'api-contracts', 'browser-experience', 'dotnet-boundaries'} <= ids)

    def test_review_cannot_self_waive_an_exception(self):
        value = obligations.read(self.feature / 'obligation-design.json')
        value['requirements'][0]['applicability'] = 'exception'
        self.write('specs/001-reservation/obligation-design.json', value)
        self.review()
        with self.assertRaises(FileNotFoundError):
            obligations.check(self.root, self.feature, 'after-plan')


if __name__ == '__main__':
    unittest.main()

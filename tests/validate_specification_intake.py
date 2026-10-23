"""Bounded offline feature-grilling gate regressions; no coding agent is started."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
import specify_cli
from specify_cli.extensions import ExtensionManager

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "extensions/program-kit-governance/scripts"
sys.path.insert(0, str(SCRIPTS))
import specification_intake as intake


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature-intake-")
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name).resolve()
        previous = Path.cwd()
        os.chdir(self.repository)
        self.addCleanup(os.chdir, previous)
        for name in ("validate_installation", "validate_ratification", "configure_paths"):
            mocked = patch.object(intake.governance, name)
            mocked.start()
            self.addCleanup(mocked.stop)
        self.records = [{"id": "SPC-001", "title": "Invoice export", "Status": "Ready",
                         "Scope": "Own invoices", "Required Accepted ADRs": "none"}]
        mocked = patch.object(intake.governance, "validate_roadmap", side_effect=lambda ready, **kwargs: self.records)
        mocked.start()
        self.addCleanup(mocked.stop)
        for path in (intake.governance.CONSTITUTION, intake.governance.ARCHITECTURE):
            full = self.repository / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text("Accepted source", encoding="utf-8")
        self.path = intake.begin(self.repository, "SPC-001", "Export my invoices")
        self.brief = intake.read(self.path)
        self.brief.update({key: "Reviewed " + key for key in intake.FIELDS})
        self.brief["decisions"] = [{"id": "Q1", "question": "Whose invoices?", "answer": "Own account",
                                    "provenance": "User turn 2", "rationale": "Ownership boundary",
                                    "dependsOn": [], "disposition": "answered", "blocking": True}]
        self.save()

    def save(self):
        intake.atomic_write(self.path, self.brief)

    def confirm(self):
        review = intake.review(self.repository, "SPC-001")
        intake.confirm(self.repository, "SPC-001", review["reviewHash"], "User turn 4", "I confirm this brief")
        return intake.check(self.repository, "SPC-001")

    def test_confirmation_and_resume_without_setup_side_effects(self):
        original = self.path.read_bytes()
        self.assertEqual(intake.begin(self.repository, "SPC-001", "New request must be compared"), self.path)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(OSError):
            intake.check(self.repository, "SPC-001")
        review = intake.review(self.repository, "SPC-001")
        with self.assertRaises(OSError):
            intake.check(self.repository, "SPC-001")
        with self.assertRaises(ValueError):
            intake.confirm(self.repository, "SPC-001", "0" * 64, "turn 4", "yes")
        with self.assertRaises(ValueError):
            intake.confirm(self.repository, "SPC-001", review["reviewHash"], "", "")
        self.confirm()
        for path in ("specs", ".git", ".specify/feature.json"):
            self.assertFalse((self.repository / path).exists())

    def test_upgrade_assessment_is_read_only_and_independent_of_product_confirmation(self):
        import upgrade_remediation as remediation
        self.confirm()
        caller=self.repository/'unrelated-caller';caller.mkdir()
        os.chdir(caller)
        before=self.path.with_name('confirmation.json').read_bytes()
        result=remediation.assess(self.repository)
        self.assertTrue(remediation.migration_phase_ready(result))
        self.assertIsNone(result['applicationReady'])
        self.assertEqual(caller,Path.cwd())
        self.brief['scope']='Changed product scope'
        self.save()
        self.assertTrue(remediation.migration_phase_ready(remediation.assess(self.repository)))
        with self.assertRaises(ValueError):intake.check(self.repository,'SPC-001')
        self.assertEqual(before,self.path.with_name('confirmation.json').read_bytes())

    def test_bootstrap_bookkeeping_does_not_reopen_product_confirmation(self):
        self.confirm()
        ledger=self.repository/'docs/architecture/bootstrap-prerequisites.json'
        intake.atomic_write(ledger,{'prerequisites':[{'id':'stale','status':'open','evidence':[{'sha256':'obsolete'}]}]})
        self.assertEqual([],intake.context(self.repository,'SPC-001')['bootstrapObligations'])
        before=self.path.with_name('confirmation.json').read_bytes()
        intake.check(self.repository,'SPC-001')
        self.assertEqual(before,self.path.with_name('confirmation.json').read_bytes())

    def test_bootstrap_carryover_rejects_duplicate_unknown_and_excluded_links(self):
        obligation = {'id': 'retained'}
        for decisions in ([{'bootstrapPrerequisite': 'retained', 'disposition': 'excluded'}],
                          [{'bootstrapPrerequisite': 'retained', 'disposition': 'answered'}] * 2,
                          [{'bootstrapPrerequisite': 'retained', 'disposition': 'answered'},
                           {'bootstrapPrerequisite': 'unknown', 'disposition': 'answered'}]):
            with self.subTest(decisions=decisions), self.assertRaises(ValueError):
                intake.require_bootstrap_carryover({'decisions': decisions}, [obligation])

    def test_mutation_invalidates_confirmation_and_can_be_reconfirmed(self):
        self.confirm()
        self.brief["scope"] = "Include archived invoices"
        self.save()
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        intake.review(self.repository, "SPC-001")
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.confirm()

    def test_tampered_review_and_copied_receipt_block(self):
        self.confirm()
        review = self.path.with_name("review.md")
        review.write_text("Different synthesis", encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.confirm()
        receipt = intake.read(self.path.with_name("confirmation.json"))
        receipt["roadmapEntry"] = "SPC-002"
        intake.atomic_write(self.path.with_name("confirmation.json"), receipt)
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")

    def test_unrelated_governance_changes_preserve_product_confirmation(self):
        self.confirm()
        before=self.path.with_name('confirmation.json').read_bytes()
        self.records.append({'id':'SPC-002','Status':'Ready'})
        self.records[0].update(Status='Blocked',Scope='Changed planning context')
        (self.repository/intake.governance.CONSTITUTION).write_text('Amended formatting')
        intake.check(self.repository,'SPC-001')
        self.assertEqual(before,self.path.with_name('confirmation.json').read_bytes())
        self.brief['scope']='Actual changed product scope'
        self.save()
        with self.assertRaises(ValueError):intake.check(self.repository,'SPC-001')

    def test_incomplete_and_blocking_decisions_cannot_be_reviewed(self):
        for modification in ({"disposition": "open"}, {"disposition": "deferred", "owner": "team", "trigger": "plan"},
                             {"dependsOn": ["missing"]}, {"dependsOn": ["Q1"]}, {"provenance": ""}):
            with self.subTest(modification=modification):
                brief = copy.deepcopy(self.brief)
                brief["decisions"][0].update(modification)
                with self.assertRaises(ValueError):
                    intake.validate_brief(brief, "SPC-001")
        self.brief["decisions"][0].update(disposition="deferred", blocking=False, owner="Planning owner", trigger="Before plan approval", duePhase="after-plan")
        self.save()
        self.confirm()
        self.brief["decisions"].append({**self.brief["decisions"][0], "id": "Q2", "disposition": "answered", "dependsOn": ["Q1"]})
        with self.assertRaises(ValueError):
            intake.validate_brief(self.brief, "SPC-001")

    def test_spec_reference_cannot_bypass_confirmation(self):
        result = self.confirm()
        spec = self.repository / "specs/001-export/spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("Existing spec with no intake", encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check_spec(self.repository, spec)
        text = ("- **Specification roadmap entry**: SPC-001 Invoice export\n"
                f"- **Confirmed intake brief**: {result['brief']}\n"
                f"- **Confirmed intake SHA256**: {result['briefHash']}\n")
        spec.write_text(text, encoding="utf-8")
        intake.check_spec(self.repository, spec)
        spec.write_text(text.replace(result["briefHash"], "0" * 64), encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check_spec(self.repository, spec)

    def test_path_escape_rejected(self):
        for entry in ("../escape", "A/../../escape", "", "SPC-001/child"):
            with self.assertRaises(ValueError):
                intake.directory(self.repository, entry)

    def test_context_does_not_require_installation_ratification_or_roadmap_receipts(self):
        for operation in ('validate_installation','validate_ratification','validate_roadmap'):
            with patch.object(intake.governance,operation,side_effect=ValueError('obsolete bookkeeping')) as gate:
                intake.begin(self.repository,'SPC-001','Resume')
                gate.assert_not_called()

    def test_dependency_cycles_and_missing_review_fields(self):
        self.brief["decisions"][0]["dependsOn"] = ["Q2"]
        self.brief["decisions"].append({**self.brief["decisions"][0], "id": "Q2", "dependsOn": ["Q1"]})
        with self.assertRaisesRegex(ValueError, "cycle"):
            intake.validate_brief(self.brief, "SPC-001")
        self.brief["acceptanceCriteria"] = ""
        with self.assertRaisesRegex(ValueError, "acceptanceCriteria"):
            intake.validate_brief(self.brief, "SPC-001")

    def test_preflight_cannot_continue_without_intake(self):
        feature = self.repository / "specs/001-export"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("Old spec", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "implementation_preflight.py"),
                                 "--repository", str(self.repository), "--feature-dir", str(feature)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("old progress grants no authority", result.stdout)

    def feature_seed(self, feature='renew-policy', **changes):
        candidate = {'id': feature, 'epic': 'SPC-001', 'commitment': 'intended',
                     'name': 'Renew a policy', 'outcome': 'Keep cover and historical terms',
                     'contexts': ['policies'], 'journey': 'manage-policies',
                     'seed': {'details': 'Keep old revisions for historical claims.\nPreserve the supplied examples.',
                              'boundaryRationale': 'Renewal is useful without evidence automation.',
                              'openQuestions': ['Which renewal exceptions apply?'],
                              'brief': {'scope': 'Renew one policy with a new immutable revision',
                                        'nonGoals': 'Evidence analysis and deletion',
                                        'decisions': copy.deepcopy(self.brief['decisions'])}}, **changes}
        model_path = self.repository / 'docs/architecture/architecture-map.json'
        model = intake.read(model_path) if model_path.is_file() else {
            'elements': [{'id': 'policies'}, {'id': 'claims'}], 'relationships': [],
            'constraints': [], 'decisions': [], 'strategic_model': {'candidate_slices': []}}
        model['strategic_model']['candidate_slices'].append(candidate)
        intake.atomic_write(model_path, model)
        return candidate

    def feature_confirm(self, feature):
        path = intake.begin(self.repository, 'SPC-001', '', feature=feature)
        brief = intake.read(path)
        brief.update({key: brief.get(key) or 'Reviewed ' + key for key in intake.FIELDS})
        intake.atomic_write(path, brief)
        reviewed = intake.review(self.repository, 'SPC-001', feature=feature)
        intake.confirm(self.repository, 'SPC-001', reviewed['reviewHash'], 'User feature review',
                       'Confirm this feature only', feature=feature)
        return intake.check(self.repository, 'SPC-001', feature=feature)

    def feature_spec(self, result, name='renew'):
        path = self.repository / f'specs/001-{name}/spec.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"- **Specification roadmap entry**: {result['roadmapEntry']}\n"
                        f"- **Specification feature ID**: {result['featureId']}\n"
                        f"- **Confirmed intake brief**: {result['brief']}\n"
                        f"- **Confirmed intake SHA256**: {result['briefHash']}\n", encoding='utf-8')
        return path

    def test_features_share_epic_without_overwriting_or_reopening_sibling(self):
        legacy = self.path.read_bytes()
        self.feature_seed()
        self.feature_seed('retire-policy')
        first = self.feature_confirm('renew-policy')
        first_path = self.repository / first['brief']
        confirmation = first_path.with_name('confirmation.json').read_bytes()
        second = self.feature_confirm('retire-policy')
        self.assertNotEqual(first['brief'], second['brief'])
        self.assertEqual(first['roadmapEntry'], second['roadmapEntry'])
        second_path = self.repository / second['brief']
        changed = intake.read(second_path)
        changed['scope'] = 'Changed retirement product boundary'
        intake.atomic_write(second_path, changed)
        with self.assertRaisesRegex(ValueError, 'intent changed'):
            intake.check(self.repository, 'SPC-001', feature='retire-policy')
        self.assertEqual(first, intake.check(self.repository, 'SPC-001', feature='renew-policy'))
        self.assertEqual(confirmation, first_path.with_name('confirmation.json').read_bytes())
        self.assertEqual(legacy, self.path.read_bytes())

    def test_seed_preserved_partial_answers_reused_and_resume_is_non_destructive(self):
        candidate = self.feature_seed()
        path = intake.begin(self.repository, 'SPC-001', '', feature='renew-policy')
        draft = intake.read(path)
        self.assertEqual(candidate, draft['bootstrapSeed'])
        self.assertEqual(candidate['seed']['brief']['scope'], draft['scope'])
        self.assertEqual(candidate['outcome'], draft['request'])
        self.assertEqual('', draft['failureCases'])
        self.assertFalse(path.with_name('confirmation.json').exists())
        draft['failureCases'] = 'A human answer supplied after bootstrap'
        intake.atomic_write(path, draft)
        before = path.read_bytes()
        model_path = self.repository / 'docs/architecture/architecture-map.json'
        model = intake.read(model_path)
        model['strategic_model']['candidate_slices'][0]['seed']['details'] = 'Later source edit'
        intake.atomic_write(model_path, model)
        self.assertEqual(path, intake.begin(self.repository, 'SPC-001', 'New request', feature='renew-policy'))
        self.assertEqual(before, path.read_bytes())

    def test_feature_and_epic_mismatches_and_unsafe_ids_rejected(self):
        self.feature_seed()
        with self.assertRaisesRegex(ValueError, 'different roadmap epic'):
            intake.begin(self.repository, 'SPC-002', 'Wrong parent', feature='renew-policy')
        result = self.feature_confirm('renew-policy')
        with self.assertRaisesRegex(ValueError, 'identity'):
            intake.begin(self.repository, 'SPC-002', 'Move existing feature', feature='renew-policy')
        for feature in ('../escape', 'A', 'x/y', '', 'a' * 65):
            with self.subTest(feature=feature), self.assertRaises(ValueError):
                intake.directory(self.repository, 'SPC-001', feature)
        receipt_path = (self.repository / result['brief']).with_name('confirmation.json')
        receipt = intake.read(receipt_path)
        receipt['featureId'] = 'retire-policy'
        intake.atomic_write(receipt_path, receipt)
        with self.assertRaisesRegex(ValueError, 'another feature'):
            intake.check(self.repository, 'SPC-001', feature='renew-policy')

    def test_explicit_exploratory_selection_preserves_classification_without_source_promotion(self):
        self.feature_seed(commitment='exploratory')
        source = self.repository / 'docs/architecture/architecture-map.json'
        before = source.read_bytes()
        result = self.feature_confirm('renew-policy')
        review = (self.repository / result['brief']).with_name('review.md').read_text(encoding='utf-8')
        self.assertIn('"commitment": "exploratory"', review)
        self.assertEqual(before, source.read_bytes())

    def test_new_feature_request_does_not_require_prior_canonical_candidate(self):
        self.feature_seed()
        path = intake.begin(self.repository, 'SPC-001', 'A newly requested useful feature', feature='new-feature')
        draft = intake.read(path)
        self.assertEqual(2, draft['schemaVersion'])
        self.assertNotIn('bootstrapSeed', draft)

    def test_direct_feature_reference_used_by_context_upgrade_and_phase_callers(self):
        self.feature_seed()
        result = self.feature_confirm('renew-policy')
        spec = self.feature_spec(result)
        self.assertEqual(result, intake.check_spec(self.repository, spec))
        import feature_context
        from consumer_upgrade import request_scope
        import phase_obligations
        resolved = feature_context.feature_scope(self.repository, spec.parent)
        self.assertEqual('renew-policy', resolved['featureId'])
        self.assertEqual(['policies'], resolved['brief']['architectureScope'])
        self.assertEqual(self.repository / result['brief'], resolved['briefPath'])
        self.assertEqual(['policies'], request_scope(self.repository, feature=spec.parent)['owners'])
        obligation = {'id': 'policy-meaning', 'affected_slices': ['SPC-001'], 'status': 'open',
                      'disposition': 'feature', 'trigger': 'before-implementation', 'verification': 'decision',
                      'owner': 'Policy owner', 'task': 'Clarify historical meaning'}
        intake.atomic_write(self.repository / 'docs/architecture/bootstrap-prerequisites.json',
                            {'prerequisites': [obligation]})
        brief_path = self.repository / result['brief']
        brief = intake.read(brief_path)
        brief['decisions'][0]['bootstrapPrerequisite'] = obligation['id']
        intake.atomic_write(brief_path, brief)
        # Exercise the caller's exact feature routing independently of the retired
        # bootstrap-decision confirmation mechanism (ordinary context has no ledger).
        with patch.object(intake, 'check', return_value=result) as confirmed:
            self.assertEqual('satisfied', phase_obligations.retained_proofs(self.repository, spec.parent, 'implementation')[0]['status'])
            confirmed.assert_called_once_with(self.repository, 'SPC-001', later=True, feature='renew-policy')

    def test_spec_cannot_substitute_sibling_parent_or_legacy_reference(self):
        self.feature_seed()
        self.feature_seed('retire-policy')
        first, second = self.feature_confirm('renew-policy'), self.feature_confirm('retire-policy')
        spec = self.feature_spec(first)
        text = spec.read_text(encoding='utf-8')
        variants = (text.replace(first['brief'], second['brief']),
                    text.replace('SPC-001', 'SPC-002'),
                    text.replace('- **Specification feature ID**: renew-policy\n', ''),
                    text.replace(first['brief'], '../outside/brief.json'),
                    text.replace(first['briefHash'], second['briefHash']))
        for content in variants:
            with self.subTest(content=content), self.assertRaises(ValueError):
                spec.write_text(content, encoding='utf-8')
                intake.check_spec(self.repository, spec)

    def test_plan_prerequisite_resolution_selects_child_within_shared_epic(self):
        self.feature_seed()
        self.feature_seed('retire-policy')
        first, second = self.feature_confirm('renew-policy'), self.feature_confirm('retire-policy')
        first_spec = self.feature_spec(first)
        self.feature_spec(second, 'retire')
        import feature_plan_decisions
        items = [{'id': 'terms', 'disposition': 'feature', 'trigger': 'feature-plan'}]
        with patch.object(feature_plan_decisions, 'project', return_value=[{'id': 'terms', 'status': 'resolved'}]) as projected:
            self.assertEqual({'terms'}, feature_plan_decisions.satisfied(self.repository, 'SPC-001', items,
                                                                       feature_id='renew-policy'))
            projected.assert_called_once_with(self.repository, first_spec.parent)
        self.assertEqual(set(), feature_plan_decisions.satisfied(self.repository, 'SPC-001', items))

    def retained_conditions(self, items):
        import bootstrap_lifecycle
        decisions = self.repository / 'docs/architecture/bootstrap-decisions.json'
        intake.atomic_write(decisions, {'unresolved': [], 'deferred': []})
        intake.atomic_write(self.repository / bootstrap_lifecycle.LEDGER,
                            {'schema_version': '1.0', 'sources': [{
                                'path': 'docs/architecture/bootstrap-decisions.json',
                                'sha256': bootstrap_lifecycle.source_digest(decisions),
                                'prerequisites': [item['id'] for item in items]}], 'prerequisites': items})
        return bootstrap_lifecycle

    def test_retained_feature_condition_does_not_gate_sibling_but_aggregate_is_conservative(self):
        self.feature_seed()
        self.feature_seed('maintain-policy')
        renewal = self.feature_spec(self.feature_confirm('renew-policy'))
        maintenance = self.feature_spec(self.feature_confirm('maintain-policy'), 'maintain')
        condition = {'id': 'renewal-policy', 'source_ids': ['renewal-policy'],
                     'affected_slices': ['SPC-001'], 'affected_features': ['renew-policy'],
                     'disposition': 'architecture', 'trigger': 'before-specification',
                     'owner': 'Policy owner', 'task': 'Resolve renewal terms compatibility',
                     'rationale': 'Renewal depends on historical terms', 'status': 'open', 'evidence': []}
        lifecycle = self.retained_conditions([condition])
        records = [{'id': 'SPC-001', 'Status': 'Ready'}]
        self.assertEqual([condition], lifecycle.validate_prerequisites(self.repository, records))
        self.assertFalse(lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'specification',
                                                   feature='renew-policy')['eligible'])
        self.assertTrue(lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'specification',
                                                  feature='maintain-policy')['eligible'])
        self.assertFalse(lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'specification')['eligible'])
        # A caller cannot evade the renewal blocker by selecting an invented
        # feature or a real feature belonging to another epic.
        with self.assertRaisesRegex(lifecycle.LifecycleError, 'unknown affected feature'):
            lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'specification',
                                        feature='unknown-feature')
        self.feature_seed('claims-only', epic='SPC-002')
        with self.assertRaisesRegex(lifecycle.LifecycleError, 'another epic'):
            lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'specification',
                                        feature='claims-only')
        import phase_obligations
        self.assertEqual(['renewal-policy'], [p['id'] for p in phase_obligations.retained_proofs(
            self.repository, renewal.parent, 'implementation')])
        self.assertEqual([], phase_obligations.retained_proofs(self.repository, maintenance.parent, 'implementation'))
        shared = {**condition, 'id': 'shared-terms', 'source_ids': ['shared-terms'],
                  'trigger': 'before-implementation'}
        shared.pop('affected_features')
        self.retained_conditions([condition, shared])
        for feature in ('renew-policy', 'maintain-policy'):
            state = lifecycle.phase_eligibility(self.repository, records, 'SPC-001', 'implementation', feature=feature)
            self.assertIn('shared-terms', [b['id'] for b in state['blockers']])
        self.assertEqual(['shared-terms'], [p['id'] for p in phase_obligations.retained_proofs(
            self.repository, maintenance.parent, 'implementation')])

    def test_scoped_plan_conditions_and_feature_reference_validation(self):
        self.feature_seed()
        self.feature_seed('maintain-policy')
        renewal = self.feature_spec(self.feature_confirm('renew-policy'))
        maintenance = self.feature_spec(self.feature_confirm('maintain-policy'), 'maintain')
        condition = {'id': 'renewal-rules', 'source_ids': ['renewal-rules'],
                     'affected_slices': ['SPC-001'], 'affected_features': ['renew-policy'],
                     'disposition': 'feature', 'trigger': 'feature-plan', 'owner': 'Policy owner',
                     'task': 'Define renewal exceptions', 'rationale': 'Feature-specific rules',
                     'status': 'open', 'evidence': []}
        lifecycle = self.retained_conditions([condition])
        lifecycle.validate_prerequisites(self.repository, [{'id': 'SPC-001', 'Status': 'Ready'}])
        import feature_plan_decisions
        self.assertEqual([condition], feature_plan_decisions.rows(self.repository, renewal.parent))
        self.assertEqual([], feature_plan_decisions.rows(self.repository, maintenance.parent))
        for scope in ([], ['renew-policy', 'renew-policy'], ['UNKNOWN'], ['unknown-feature']):
            with self.subTest(scope=scope), self.assertRaises(lifecycle.LifecycleError):
                lifecycle.validate_feature_scope(self.repository, {**condition, 'affected_features': scope})
        self.feature_seed('claims-only', epic='SPC-002')
        with self.assertRaisesRegex(lifecycle.LifecycleError, 'another epic'):
            lifecycle.validate_feature_scope(self.repository, {**condition, 'affected_features': ['claims-only']})
        self.feature_seed('unparented', epic=None)
        with self.assertRaisesRegex(lifecycle.LifecycleError, 'explicit parent epic'):
            lifecycle.validate_feature_scope(self.repository, {**condition, 'affected_features': ['unparented']})


class HookContractTests(unittest.TestCase):
    def test_installed_cli_keeps_seeded_features_independent_within_one_epic(self):
        """Exercise shipped commands, not imported helpers, in a fresh consumer."""
        with tempfile.TemporaryDirectory(prefix="feature-intake-cli-") as value:
            repository = Path(value).resolve()
            (repository / ".specify").mkdir()
            intake.atomic_write(repository / ".specify/init-options.json", {"ai": "codex", "ai_skills": True})
            (repository / ".agents/skills").mkdir(parents=True)
            ExtensionManager(repository).install_from_directory(SCRIPTS.parent, "1.1.1")
            installed = repository / ".specify/extensions/program-kit-governance/scripts/specification_intake.py"

            def command(*arguments, succeeds=True):
                result = subprocess.run([sys.executable, str(installed), "--repository", str(repository),
                                         *arguments], cwd=repository, capture_output=True, text=True,
                                        encoding="utf-8", timeout=30)
                self.assertEqual(result.returncode, 0 if succeeds else 1, result.stdout + result.stderr)
                if succeeds:
                    return json.loads(result.stdout)
                self.assertIn("Specification intake blocked:", result.stderr)
                return result.stderr

            seeds = [
                {"id": "renew-policy", "epic": "SPC-001", "name": "Renew policy",
                 "journey": "manage-policies", "commitment": "intended", "contexts": ["policies"],
                 "outcome": "Renew cover while retaining the terms used by historical claims",
                 "seed": {"details": "A renewal makes a new immutable revision.\n"
                                     "Example: a claim dated before renewal still uses the earlier terms.",
                          "boundaryRationale": "Renewal is useful before evidence analysis is automated.",
                          "openQuestions": ["How should a conflicting effective date be handled?"],
                          "brief": {"scope": "Renew one policy with a new immutable revision",
                                    "nonGoals": "Evidence automation and policy retirement"}}},
                {"id": "retire-policy", "epic": "SPC-001", "name": "Retire policy",
                 "journey": "manage-policies", "commitment": "intended", "contexts": ["policies"],
                 "outcome": "Retire a policy without erasing required historical claim meaning",
                 "seed": {"details": "Retirement prevents new use.\n"
                                     "Example: existing claims retain their original policy revision.",
                          "boundaryRationale": "Retirement can ship independently of renewal.",
                          "openQuestions": ["Which historical references prevent physical deletion?"],
                          "brief": {"scope": "Retire one policy while preserving referenced revisions",
                                    "nonGoals": "Renewal and automated evidence analysis"}}},
            ]
            model_path = repository / "docs/architecture/architecture-map.json"
            intake.atomic_write(model_path, {"elements": [{"id": "policies"}], "relationships": [],
                                            "constraints": [], "decisions": [],
                                            "strategic_model": {"candidate_slices": seeds}})
            source_bytes = model_path.read_bytes()
            results, paths = [], []
            for seed in seeds:
                feature = seed["id"]
                path = Path(command("begin", "--entry", "SPC-001", "--feature", feature))
                paths.append(path)
                brief = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(seed, brief["bootstrapSeed"])
                self.assertEqual(seed["seed"]["brief"]["scope"], brief["scope"])
                self.assertEqual(seed["outcome"], brief["request"])
                self.assertEqual("", brief["failureCases"])
                self.assertFalse(path.with_name("confirmation.json").exists())
                brief.update({"problem": "Staff need a reliable policy lifecycle",
                              "users": "Authorized policy administrators",
                              "outcome": seed["outcome"],
                              "journeys": "Select a policy, review the proposed change, and commit it",
                              "failureCases": "Reject conflicting changes without losing the current revision",
                              "dependencies": "Stable policy identity and immutable revision references",
                              "acceptanceCriteria": "Historical claims resolve their original policy terms",
                              "decisions": [{"id": "Q1", "question": seed["seed"]["openQuestions"][0],
                                             "answer": "Reject changes that invalidate historical references",
                                             "provenance": "Fictional offline fixture answer",
                                             "rationale": "Retain historical claim meaning", "dependsOn": [],
                                             "disposition": "answered", "blocking": True}]})
                intake.atomic_write(path, brief)
                authored = path.read_bytes()
                self.assertEqual(str(path), command("begin", "--entry", "SPC-001", "--feature", feature,
                                                   "--request", "A later prompt must preserve supplied answers"))
                self.assertEqual(authored, path.read_bytes())
                reviewed = command("review", "--entry", "SPC-001", "--feature", feature)
                self.assertIn(seed["seed"]["boundaryRationale"],
                              path.with_name("review.md").read_text(encoding="utf-8"))
                command("confirm", "--entry", "SPC-001", "--feature", feature,
                        "--review-sha256", reviewed["reviewHash"],
                        "--confirmation-source", "Fictional offline review",
                        "--confirmation-text", "Simulated confirmation of this feature only")
                confirmed = command("check", "--entry", "SPC-001", "--feature", feature)
                results.append(confirmed)
                spec = repository / "specs" / feature / "spec.md"
                spec.parent.mkdir(parents=True)
                spec.write_text(f"- **Specification roadmap entry**: SPC-001\n"
                                f"- **Specification feature ID**: {feature}\n"
                                f"- **Confirmed intake brief**: {confirmed['brief']}\n"
                                f"- **Confirmed intake SHA256**: {confirmed['briefHash']}\n", encoding="utf-8")
                self.assertEqual(confirmed, command("check-spec", "--spec", str(spec)))

            self.assertNotEqual(results[0]["brief"], results[1]["brief"])
            self.assertEqual("SPC-001", results[0]["roadmapEntry"])
            self.assertEqual("SPC-001", results[1]["roadmapEntry"])
            self.assertEqual(source_bytes, model_path.read_bytes())
            first_confirmation = paths[0].with_name("confirmation.json").read_bytes()
            sibling = json.loads(paths[1].read_text(encoding="utf-8"))
            sibling["scope"] = "A changed retirement boundary requires its own fresh confirmation"
            intake.atomic_write(paths[1], sibling)
            self.assertIn("intent changed", command("check", "--entry", "SPC-001", "--feature",
                                                   "retire-policy", succeeds=False))
            self.assertEqual(results[0], command("check", "--entry", "SPC-001", "--feature", "renew-policy"))
            self.assertEqual(first_confirmation, paths[0].with_name("confirmation.json").read_bytes())

            preserved = {path: path.read_bytes() for folder in paths for path in folder.parent.iterdir() if path.is_file()}
            self.assertIn("identity", command("begin", "--entry", "SPC-002", "--feature", "renew-policy",
                                              "--request", "Attempt to move this feature", succeeds=False))
            spec = repository / "specs/renew-policy/spec.md"
            correct_spec = spec.read_text(encoding="utf-8")
            for invalid_spec, expected_error in (
                    (correct_spec.replace(results[0]["brief"], results[1]["brief"]), "path differs"),
                    (correct_spec.replace("SPC-001", "SPC-002"), "identity does not match")):
                spec.write_text(invalid_spec, encoding="utf-8")
                rejected_bytes = spec.read_bytes()
                self.assertIn(expected_error, command("check-spec", "--spec", str(spec), succeeds=False))
                self.assertEqual(rejected_bytes, spec.read_bytes())
            self.assertEqual(preserved, {path: path.read_bytes() for path in preserved})
            spec.write_text(correct_spec, encoding="utf-8")
            self.assertEqual(results[0], command("check-spec", "--spec", str(spec)))

    def test_installed_and_reinstalled_hooks_and_skill(self):
        with tempfile.TemporaryDirectory(prefix="feature-intake-install-") as value:
            repository = Path(value)
            (repository / ".specify").mkdir()
            intake.atomic_write(repository / ".specify/init-options.json", {"ai": "codex", "ai_skills": True})
            (repository / ".agents/skills").mkdir(parents=True)
            config = repository / ".specify/extensions.yml"
            config.write_text(yaml.safe_dump({"settings": {"auto_execute_hooks": True}, "hooks": {"before_specify": [
                {"extension": "consumer", "command": "consumer.branch", "priority": 50, "enabled": True, "optional": False},
            ]}}), encoding="utf-8")
            manager = ExtensionManager(repository)
            for force in (False, True):
                manager.install_from_directory(SCRIPTS.parent, "1.1.1", force=force)
                hooks = yaml.safe_load(config.read_text(encoding="utf-8"))["hooks"]["before_specify"]
                owned = [h for h in hooks if h["extension"] == "program-kit-governance"]
                self.assertEqual([h["command"] for h in owned], ["speckit.program-kit-governance.architecture-check",
                                                                 "speckit.program-kit-governance.specification-intake"])
                self.assertEqual(len([h for h in hooks if h["extension"] == "consumer"]), 1)
                for hook in owned:
                    self.assertIs(hook["optional"], False)
                    self.assertIs(hook["enabled"], True)
                    self.assertIsNone(hook["condition"])
            skill = repository / ".agents/skills/speckit-program-kit-governance-specification-intake/SKILL.md"
            content = skill.read_text(encoding="utf-8")
            self.assertIn(".specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md", content)
            self.assertTrue((repository / ".specify/extensions/program-kit-governance/scripts/specification_intake.py").is_file())

    def test_mandatory_order_and_core_execution_boundary(self):
        manifest = yaml.safe_load((SCRIPTS.parent / "extension.yml").read_text(encoding="utf-8"))
        hooks = manifest["hooks"]["before_specify"]
        self.assertEqual([h["command"] for h in hooks], ["speckit.program-kit-governance.architecture-check",
                                                       "speckit.program-kit-governance.specification-intake"])
        self.assertEqual([h["priority"] for h in hooks], [5, 10])
        for hook in hooks:
            self.assertIs(hook["enabled"], True)
            self.assertIs(hook["optional"], False)
            self.assertIsNone(hook["condition"])
        core = Path(specify_cli.__file__).parent / "core_pack/commands/specify.md"
        text = core.read_text(encoding="utf-8")
        self.assertLess(text.index("hooks.before_specify"), text.index("## Outline"))
        self.assertLess(text.index("MUST actually invoke the hook and wait"), text.index("## Outline"))
        self.assertLess(text.index("## Outline"), text.index("mkdir -p SPECIFY_FEATURE_DIRECTORY"))


if __name__ == "__main__":
    unittest.main()

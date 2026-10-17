"""Bounded operational journeys; no agent, database, native build or browser runs.

Each family has a deliberately narrow claim. Cheap regression cases remain in
their focused modules; this entrypoint selects only the representative journeys.
Phase, bootstrap and upgrade journeys need the prepared Specify interpreter and
exact project-local schema dependencies. Upgrade also consumes the built archive
and the actual local v0.13.1 Git tag; knowledge and scaffold use Python only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPROVALS = ('--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved')


def sync(root: Path, *arguments: str, environment=None):
    return subprocess.run([sys.executable,
        str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
        '--target', str(root), *arguments], cwd=ROOT, env=environment,
        capture_output=True, text=True, encoding='utf-8', timeout=45)


def snapshot(root: Path):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class ScaffoldJourney(unittest.TestCase):
    def test_generation_validation_and_rejected_selection_preserve_authored_files(self):
        with tempfile.TemporaryDirectory(prefix='pk scaffold space ') as directory:
            root = Path(directory)
            authored = root / 'consumer-notes.txt'
            authored.write_bytes(b'Consumer-owned design decisions.\n')
            before = snapshot(root)
            rejected = sync(root)
            self.assertEqual(3, rejected.returncode, rejected.stdout + rejected.stderr)
            self.assertEqual(before, snapshot(root))
            installed = sync(root, *APPROVALS, '--web-profile', 'none')
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            state = json.loads((root / '.program-kit/managed.json').read_text())
            self.assertEqual('none', state['selections']['web'])
            self.assertTrue((root / 'eng/Build.ps1').is_file())
            self.assertTrue((root / 'Directory.Build.props').is_file())
            self.assertEqual(b'Consumer-owned design decisions.\n', authored.read_bytes())
            # Execute the emitted lightweight drift contract, without claiming
            # that the generated composition compiles or starts successfully.
            checked = sync(root, '--profile-selected', '--web-profile', 'none', '--check')
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            shell = json.loads((root / 'eng/web-profile.shells.json').read_text())
            self.assertEqual({}, shell['CShells']['Shells']['default']['Features'])
            emitted = subprocess.run([sys.executable, '-I', '-c',
                'import sys,json; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/"eng")); '
                'import shell_composition; print(json.dumps(shell_composition.compose(Path.cwd())))'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(0, emitted.returncode, emitted.stdout + emitted.stderr)
            self.assertEqual({}, json.loads(emitted.stdout)['CShells']['Shells']['default']['Features'])


class UpgradeJourney(unittest.TestCase):
    def test_profile_upgrade_rollback_retry_and_managed_conflict(self):
        with tempfile.TemporaryDirectory(prefix='pk upgrade space ') as directory:
            root = Path(directory)
            authored = root / 'consumer-notes.txt'
            authored.write_bytes(b'Keep consumer-authored content.\n')
            result = sync(root, *APPROVALS, '--web-profile', 'bff-cookie')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            before = snapshot(root)
            environment = dict(os.environ, PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION='2')
            interrupted = sync(root, *APPROVALS, '--web-profile', 'spa-pkce', environment=environment)
            self.assertEqual(2, interrupted.returncode, interrupted.stdout + interrupted.stderr)
            self.assertIn('rolled back', interrupted.stderr)
            self.assertEqual(before, snapshot(root))
            retry = sync(root, *APPROVALS, '--web-profile', 'spa-pkce')
            self.assertEqual(0, retry.returncode, retry.stdout + retry.stderr)
            self.assertFalse((root / 'eng/web/bff-session.ts').exists())
            self.assertTrue((root / 'eng/web/spa-session.ts').is_file())
            self.assertEqual(b'Keep consumer-authored content.\n', authored.read_bytes())
            managed = root / 'eng/spa-pkce.json'
            managed.write_bytes(managed.read_bytes() + b'\nConsumer customization\n')
            before = snapshot(root)
            conflict = sync(root, *APPROVALS, '--web-profile', 'bff-cookie')
            self.assertEqual(2, conflict.returncode, conflict.stdout + conflict.stderr)
            self.assertEqual(before, snapshot(root))


def phase_journey():
    """Run confirmed specification, plan, task and implementation gate mechanics."""
    from validate_phase_readiness import PhaseReadinessTests, fixture, intake
    from validate_story_delivery import seed
    import phase_obligations as phases
    import feature_plan_decisions as decisions

    class Journey(PhaseReadinessTests):
        def runTest(self):
            # A plan decision is genuinely due. Failed admission must not mutate
            # the approved bootstrap or silently waive that missing prerequisite.
            item = fixture.item('owned-design', disposition='feature', trigger='feature-plan')
            item.update(verification='decision', task='Define the owned first outcome')
            self.baseline([item])
            feature = self.root / 'specs/001-feature'
            feature.mkdir(parents=True)
            brief_path = intake.begin(self.root, 'SPEC-001', 'Define the owned first outcome')
            brief = intake.read(brief_path)
            brief.update({key: 'Reviewed ' + key for key in intake.FIELDS})
            brief['decisions'] = [{'id': 'Q1', 'question': 'Whose outcome?', 'answer': 'Named user',
                'provenance': 'Fictional mechanical fixture', 'rationale': 'Owned first outcome',
                'disposition': 'answered', 'blocking': False, 'dependsOn': []}]
            intake.atomic_write(brief_path, brief)
            review = intake.review(self.root, 'SPEC-001')
            intake.confirm(self.root, 'SPEC-001', review['reviewHash'], 'Fictional fixture reviewer', 'Fixture only')
            identity = intake.check(self.root, 'SPEC-001')
            # Seed the actual task-delivery state, then restore the real confirmed
            # intake binding before the phase gates read these authored artifacts.
            seed(self.root, feature)
            (feature / 'spec.md').write_text('# Feature\n- **Specification roadmap entry**: SPEC-001\n'
                '- **Confirmed intake SHA256**: ' + identity['briefHash'] + '\n'
                '- **Confirmed intake brief**: ' + identity['brief'] + '\n', encoding='utf-8')
            plan = feature / 'plan.md'
            plan.write_text('# Plan\n## Ownership\nOwned text operation; no runtime dependency.\n', encoding='utf-8')
            self.assertTrue(self.eligibility('specification')['eligible'])
            self.assertFalse(self.eligibility('planning')['eligible'])
            before = plan.read_bytes()
            with self.assertRaisesRegex(ValueError, 'owned-design'):
                phases.check(self.root, feature, 'implementation')
            self.assertEqual(before, plan.read_bytes())
            decisions.record(self.root, feature, item['id'], 'specs/001-feature/plan.md#Ownership',
                'Fictional fixture reviewer', 'Mechanical fixture; no actual human approval claim')
            before = plan.read_bytes()  # Includes the explicitly recorded review marker.
            for phase in ('planning', 'after-plan', 'tasks', 'after-tasks', 'implementation'):
                phases.check(self.root, feature, phase)
            self.assertTrue(self.eligibility('implementation')['eligible'])
            self.assertEqual(before, plan.read_bytes())

    return unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Journey()])).wasSuccessful()


CASES = {
    'phases': [
        'validate_task_generation.TaskTests.test_interrupted_draft_resumes_without_rewriting_or_duplicate_tasks',
        'validate_task_generation.TaskTests.test_changed_inputs_require_scoped_review_and_preserve_completed_work',
        'validate_task_generation.TaskTests.test_operation_graph_rejects_cycles_unknown_rows_and_missing_tasks',
        'validate_task_generation.TaskTests.test_new_operation_draft_finalization_checks_graph_without_claiming_execution',
    ],
    'knowledge': [
        'validate_knowledge_application.KnowledgeApplicationTests.test_adoption_reaches_design_before_plan_or_projects_exist',
        'validate_knowledge_application.KnowledgeApplicationTests.test_frontend_only_feature_does_not_inherit_backend_from_global_sdk',
        'validate_knowledge_application.KnowledgeApplicationTests.test_neighbor_decision_and_shared_parent_do_not_activate_a_private_provider',
        'validate_knowledge_application.KnowledgeApplicationTests.test_selected_design_needs_metadata_without_reopening_unrelated_projects',
        'validate_knowledge_application.KnowledgeApplicationTests.test_installed_default_brief_and_graph_use_the_same_canonical_rules',
    ],
    'upgrade': [
        'validate_mechanical_fixtures.UpgradeJourney',
        'validate_upgrade_retry.UpgradeRetryTests.test_actual_original_then_complete_target_materialization_are_admitted_only_with_retry_context',
    ],
    'scaffold': ['validate_mechanical_fixtures.ScaffoldJourney'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True, choices=[*CASES, 'bootstrap'])
    args = parser.parse_args()
    # Keep every disposable input in the owned ignored workspace. Some Windows
    # worker sandboxes expose a process TEMP that descendants cannot write.
    scratch = ROOT / 'artifacts/t'
    scratch.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(scratch)
    started = time.monotonic()
    try:
        if args.family in ('bootstrap', 'phases', 'upgrade'):
            sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
            import schema_runtime
            if not (schema_runtime.runtime_path(ROOT) / '.ready').is_file():
                raise RuntimeError('SCHEMA_RUNTIME_MISSING: prepare the exact locked project dependency once: '
                    + f'"{sys.executable}" "{ROOT / "extensions/program-kit-governance/scripts/schema_runtime.py"}" setup')
        if args.family == 'bootstrap':
            # Executes the shipped installed definition and real shell validators.
            # Its author/review adapter cannot dispatch a coding agent.
            from validate_installed_bootstrap_flow import scenario
            scenario('resume', source_payload=True)
            success = True
        else:
            suite = unittest.defaultTestLoader.loadTestsFromNames(CASES[args.family])
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            success = result.wasSuccessful()
            if args.family == 'phases' and success:
                success = phase_journey()
            if args.family == 'upgrade' and success:
                from validate_packaged_upgrade import scenario
                scenario()
    finally:
        print(json.dumps({'family': args.family, 'elapsedSeconds': round(time.monotonic() - started, 3),
            'scope': 'Representative mechanics; no application or agent acceptance claim.'}), flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())

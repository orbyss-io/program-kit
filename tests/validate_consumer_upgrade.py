"""Disposable consumer behavior/recovery checks; no agents, registries or real consumers."""
from __future__ import annotations
import copy
import hashlib
import uuid
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'extensions/program-kit-governance/scripts')]
import consumer_upgrade as flow
import consumer_upgrade_workspace as workspace
from build_release_guidance import build
from release_guidance import semantic_changes


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content) if isinstance(content, (dict, list)) else content, encoding='utf-8')
    return path


def commit(root, message='fixture'):
    flow.git(root, 'add', '.')
    flow.git(root, '-c', 'user.name=Upgrade Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', message)


def scope(owner='notes', paths=None, shared=False):
    return {'owners': [owner] if owner else [], 'contracts': [], 'paths': paths or [], 'features': [], 'shared': shared}


def record(root, source='0.12.5'):
    return flow.save(root, {'schemaVersion': 1, 'sourceVersion': source, 'targetVersion': '0.12.9',
                           'sourceCommit': flow.git(root, 'rev-parse', 'HEAD'), 'stage': 'prepare',
                           'findings': [], 'migrations': [], 'events': [], 'assessedInputs': flow.inputs(root)}, 'fixture')


def brief(identity='notes-repair', due='implementation', shared=False):
    return {'id': identity, 'origin': 'declared-responsibilities', 'reason': 'Actual notes contract needs a correction',
            'evidence': ['src/Notes/contract.txt'], 'scope': scope(paths=['src/Notes', 'specs/001-notes'], shared=shared),
            'outcome': 'Preserve notes output and isolate the provider effect', 'invariants': ['Named note output remains stable'],
            'trigger': 'Before extending the notes implementation', 'duePhase': due, 'dependencies': [],
            'method': 'selective-feature-repair-v1', 'uncertainties': ['Inspect current actual effects at pickup'],
            'nextAction': 'Pick up focused analysis', 'status': 'planned'}


class ConsumerUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='consumer-upgrade-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'consumer'
        self.root.mkdir()
        flow.git(self.root, 'init')
        write(self.root, '.gitignore', '.specify/\n.agents/\nartifacts/\n')
        write(self.root, 'src/Notes/contract.txt', 'named output\n')
        write(self.root, 'src/Other/contract.txt', 'unrelated output\n')
        write(self.root, 'specs/001-notes/spec.md', 'Keep valid note requirements\n- **Specification roadmap entry**: RM-01\n')
        write(self.root, 'specs/001-notes/plan.md', 'Use src/Notes/contract.txt; preserve named output\n')
        write(self.root, 'specs/001-notes/tasks.md', '- [x] T001 completed work\n- [ ] T002 verify output\n')
        write(self.root, 'docs/architecture/architecture-map.json', {
            'elements': [{'id': 'notes'}, {'id': 'other'}], 'decisions': [], 'strategic_model': {}})
        write(self.root, '.program-kit/specification-intake/RM-01/brief.json', {'architectureScope': ['notes']})
        write(self.root, 'docs/architecture/bootstrap-decisions.json', {'original': 'accepted historical decisions'})
        commit(self.root)
        record(self.root)
        self.guidance = build(ROOT, Path(self.temp.name) / 'guidance', '0.12.9')

    def test_cumulative_target_semantics_supersede_intermediate_default_and_bind_metadata(self):
        result = semantic_changes(self.guidance, '0.12.5', '0.12.9')
        ids = [c['id'] for c in result['changes']]
        self.assertIn('current-qualified-profile', ids)
        self.assertNotIn('retained-dependency-profile', ids)
        index = flow.read(self.guidance / 'migration-index.json')
        metadata = self.guidance / index['consumerChanges']['file']
        metadata.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            semantic_changes(self.guidance, '0.12.5', '0.12.9')

    def test_optional_defaults_preserve_selected_dependencies_and_confirmation(self):
        selection = write(self.root, 'docs/architecture/building-block-selection.json', {'status': 'Accepted', 'catalog': {'resolutionSha256': 'exact-old'}, 'targets': []})
        confirmation = write(self.root, '.program-kit/specification-intake/RM-01/confirmation.json', {'confirmed': 'unchanged intent'})
        before = {p: p.read_bytes() for p in (selection, confirmation, self.root/'docs/architecture/bootstrap-decisions.json')}
        result = flow.assess(self.root, self.guidance)
        default = next(f for f in result['findings'] if f['changeId'] == 'current-qualified-profile')
        self.assertEqual('optional', default['disposition'])
        self.assertNotIn('retained-dependency-profile', {f['changeId'] for f in result['findings']})
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        with self.assertRaisesRegex(ValueError, 'exact reviewed transition'):
            flow.decision(self.root, default['changeId'], {'disposition': 'retained', 'rationale': 'retained', 'scope': default['scope'],
                'evidence': ['docs/architecture/building-block-selection.json'], 'retainedCompatibility': 'supported profile', 'adoptDependencyProfile': 'new'})

    def test_tasks_repair_is_selective_and_does_not_restart_product_or_tasks(self):
        before = {p: p.read_bytes() for p in (self.root/'specs/001-notes/spec.md', self.root/'specs/001-notes/tasks.md')}
        flow.add_migration(self.root, brief(due='planning'))
        result = flow.reconcile(self.root)
        self.assertEqual('planning', result['actions'][0]['resumeFrom'])
        self.assertFalse(result['bootstrapRestartRequired'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse((self.root/'specs/001-notes/phase-context.json').exists())

    def test_shared_work_is_one_brief_with_due_phase_and_unaffected_work_available(self):
        shared = brief(shared=True)
        shared['scope']['features'] = ['specs/001-notes', 'specs/002-search']
        flow.add_migration(self.root, shared)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            flow.add_migration(self.root, shared)
        self.assertTrue(flow.scan(self.root, scope('other'), 'specification')['canProceed'])
        self.assertFalse(flow.scan(self.root, scope('other'), 'implementation')['canProceed'])
        self.assertEqual(1, len(flow.load(self.root)['migrations']))
        record(self.root)
        flow.add_migration(self.root, brief())
        self.assertTrue(flow.scan(self.root, scope('other'), 'implementation')['canProceed'])

    def test_conditional_activation_reuses_identity_and_keeps_prior_discovery(self):
        item = brief()
        item.update(status='conditional', trigger='Before a new feature extends the notes contract')
        flow.add_migration(self.root, item)
        self.assertTrue(flow.scan(self.root, scope(), 'specification')['canProceed'])
        result = flow.scan(self.root, scope(), 'implementation')
        self.assertFalse(result['canProceed'])
        self.assertTrue(result['migrations'][0]['conditionAssessmentRequired'])
        flow.revise_migration(self.root, item['id'], {
            'status': 'planned', 'evidence': ['src/Notes/contract.txt'],
            'discoveryEvidence': 'The requested feature now extends the existing contract',
            'recovery': 'Pick up the scoped retained adapter correction'}, 'activated-condition')
        value = flow.load(self.root)
        self.assertEqual(1, len(value['migrations']))
        self.assertEqual('conditional', value['migrationHistory'][0]['status'])
        self.assertEqual('activated-condition', value['migrations'][0]['cause'])

    def test_actual_installed_customization_requires_scoped_assessment_without_overwrite(self):
        skill = write(self.root, '.agents/skills/speckit-specify/SKILL.md', 'original installed prompt')
        write(self.root, '.specify/integrations/codex.manifest.json', {'files': {skill.relative_to(self.root).as_posix(): flow.sha(skill)}})
        skill.write_text('consumer customized prompt')
        result = flow.assess(self.root, self.guidance)
        finding = next(f for f in result['findings'] if f['changeId'] == 'installed-customization')
        self.assertEqual('unresolved', finding['disposition'])
        self.assertEqual('upgrade', finding['duePhase'])
        self.assertEqual('consumer customized prompt', skill.read_text())

    def test_concurrent_record_edits_are_rejected_instead_of_losing_a_decision(self):
        first, second = flow.load(self.root), flow.load(self.root)
        first['recoveryOutcome'] = 'first observed result'
        flow.save(self.root, first, 'first')
        second['recoveryOutcome'] = 'stale result'
        with self.assertRaisesRegex(ValueError, 'changed concurrently'):
            flow.save(self.root, second, 'stale')
        self.assertEqual('first observed result', flow.load(self.root)['recoveryOutcome'])

    def test_pre_directory_scan_and_planning_refinement_find_contract_scope(self):
        item = brief()
        item['scope']['contracts'] = ['notes-contract']
        flow.add_migration(self.root, item)
        request = {'architectureScope': ['notes'], 'contracts': ['notes-contract']}
        projected = flow.request_scope(self.root, request)
        self.assertEqual(['notes-repair'], [m['id'] for m in flow.scan(self.root, projected, 'specification')['migrations']])
        self.assertFalse((self.root/'specs/002-new').exists())
        self.assertFalse(flow.scan(self.root, projected, 'implementation')['canProceed'])
        self.assertTrue(flow.scan(self.root, scope('other'), 'implementation')['canProceed'])
        unknown = flow.scan(self.root, scope(None), 'specification')
        self.assertIn('Scope is unknown', unknown['limitations'][0])

    def test_deferred_retention_allows_spec_but_shared_upgrade_incompatibility_blocks_success(self):
        item = brief()
        item.update(status='deferred', retainedCompatibility='Existing provider contract is supported until extension')
        flow.add_migration(self.root, item)
        self.assertTrue(flow.scan(self.root, scope(), 'specification')['canProceed'])
        immediate = brief('shared-correction', 'upgrade', True)
        immediate['status'] = 'deferred'
        with self.assertRaisesRegex(ValueError, 'cannot be deferred'):
            flow.add_migration(self.root, immediate)
        immediate['status'] = 'blocked'
        flow.add_migration(self.root, immediate)
        self.assertFalse(flow.readiness(self.root)['upgradePrepared'])
        self.assertFalse(flow.scan(self.root, scope(), 'upgrade')['canProceed'])

    def test_pickup_defers_detail_reopens_current_inputs_and_completion_needs_execution(self):
        flow.add_migration(self.root, brief())
        self.assertNotIn('plan', flow.load(self.root)['migrations'][0])
        picked = flow.pickup(self.root, 'notes-repair', 'specs/001-notes/plan.md')
        self.assertEqual('analysis', picked['status'])
        with self.assertRaisesRegex(ValueError, 'Executed current'):
            flow.complete(self.root, 'notes-repair', {})
        checks = [{'id': 'notes-behavior', 'command': [sys.executable, '-c',
                   "from pathlib import Path; assert Path('src/Notes/contract.txt').read_text() == 'named output\\n'"]}]
        flow.verify(self.root, checks, 'notes-repair')
        flow.complete(self.root, 'notes-repair', {'outcome': 'Stable named output observed', 'invariantsVerified': ['named output'],
                                               'provenance': 'Deterministic fixture normal review', 'evidence': ['specs/001-notes/plan.md']})
        self.assertTrue(flow.scan(self.root, scope(), 'implementation')['canProceed'])
        write(self.root, 'src/Other/contract.txt', 'unrelated edit')
        self.assertTrue(flow.scan(self.root, scope(), 'implementation')['canProceed'])
        write(self.root, 'src/Notes/contract.txt', 'changed input')
        self.assertFalse(flow.scan(self.root, scope(), 'implementation')['canProceed'])
        self.assertEqual('analysis', flow.pickup(self.root, 'notes-repair')['status'])

    def test_discovery_appends_local_recovery_and_omission_needs_regression(self):
        item = brief()
        item.update(discoveryEvidence='The original scan missed a visible shared owner', recovery='Inspect and correct the local notes adapter')
        before = flow.load(self.root)['events']
        flow.add_migration(self.root, item, 'detectable-omission')
        current = flow.load(self.root)
        self.assertEqual(before, current['events'][:len(before)])
        self.assertTrue(current['migrations'][0]['regressionRequired'])
        self.assertTrue(flow.scan(self.root, scope('other'), 'implementation')['canProceed'])
        self.assertEqual('discovery', current['events'][-1]['action'])
        regression = write(self.root, 'tests/regression_notes.py',
            "from pathlib import Path\nassert Path('src/Notes/contract.txt').read_text() == 'named output\\n'\n")
        flow.revise_migration(self.root, item['id'], {'status': 'planned', 'evidence': ['src/Notes/contract.txt'],
            'scope': {**item['scope'], 'paths': item['scope']['paths'] + ['tests/regression_notes.py']},
            'discoveryEvidence': item['discoveryEvidence'], 'recovery': item['recovery']}, 'detectable-omission')
        flow.pickup(self.root, item['id'], 'specs/001-notes/plan.md')
        flow.verify(self.root, [{'id': 'omission-regression', 'command': [sys.executable, str(regression)]}], item['id'])
        review = {'outcome': 'Named output preserved by regression', 'invariantsVerified': ['named output'],
                  'provenance': 'Disposable fixture review', 'evidence': ['src/Notes/contract.txt']}
        with self.assertRaisesRegex(ValueError, 'regression path'):
            flow.complete(self.root, item['id'], review)
        review['regression'] = {'path': 'tests/regression_notes.py', 'checkId': 'not-executed'}
        with self.assertRaisesRegex(ValueError, 'not executed'):
            flow.complete(self.root, item['id'], review)
        review['regression']['checkId'] = 'omission-regression'
        flow.complete(self.root, item['id'], review)
        self.assertTrue(flow.scan(self.root, scope(), 'implementation')['canProceed'])

    def test_minimal_export_preserves_originals_redacts_and_survives_run_retention(self):
        raw = write(self.root, 'artifacts/run/raw.log', 'Authorization: Bearer fixture-secret\nfull private architecture')
        original = raw.read_bytes()
        value = flow.load(self.root)
        value.update(reproduction='password=fixture-secret api_key=privatekey at C:\\Users\\private\\repo', recoveryOutcome='local correction completed')
        flow.save(self.root, value, 'recovery-summary')
        before = (self.root / flow.RECORD).read_bytes()
        report = flow.export_report(self.root, self.root/'artifacts/report.json')
        safe = json.dumps(report)
        self.assertNotIn('fixture-secret', safe)
        self.assertNotIn('privatekey', safe)
        self.assertNotIn('full private architecture', safe)
        self.assertTrue(report['provenance']['redacted'])
        self.assertFalse(report['provenance']['sent'])
        self.assertEqual(original, raw.read_bytes())
        self.assertEqual(before, (self.root / flow.RECORD).read_bytes())
        raw.unlink()
        self.assertEqual('local correction completed', flow.read(self.root/'artifacts/report.json')['report']['recoveryOutcome'])

    def test_report_is_bounded_and_quoted_secrets_remain_valid_json(self):
        value = flow.load(self.root)
        value['reproduction'] = 'token="quoted-secret" ' + 'x' * 10000
        value['migrations'] = [{**brief('repair-' + str(i)), 'reason': 'private detail ' * 5000} for i in range(200)]
        flow.save(self.root, value, 'large-local-evidence')
        path = self.root/'artifacts/bounded.json'
        report = flow.export_report(self.root, path)
        self.assertLessEqual(path.stat().st_size, 65536)
        self.assertNotIn('quoted-secret', path.read_text())
        self.assertTrue(report['provenance']['truncated'])
        self.assertEqual('0.12.5', flow.read(path)['report']['sourceVersion'])

    def test_immediate_shared_incompatibility_cannot_hide_as_conditional(self):
        item = brief(due='upgrade', shared=True)
        item['status'] = 'conditional'
        with self.assertRaisesRegex(ValueError, 'immediate incompatibility'):
            flow.add_migration(self.root, item)

    def test_git_newline_conversion_of_immutable_originals_is_exact_and_conflict_checked(self):
        import hashlib
        original = b'original installation\n'
        identity = hashlib.sha256(original).hexdigest()
        relative = '.program-kit/installation/originals/' + identity + '.original'
        target = Path(self.temp.name)/'candidate'
        (target/relative).parent.mkdir(parents=True)
        (target/relative).write_bytes(original)
        path = write(self.root, relative, original.decode())
        flow.git(self.root, '-c', 'core.autocrlf=true', 'add', relative)
        flow.git(self.root, '-c', 'user.name=Upgrade Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Reviewed original')
        path.write_bytes(original.replace(b'\n', b'\r\n'))
        self.assertEqual([relative], workspace.reconcile_originals(target, self.root))
        self.assertEqual(original, path.read_bytes())
        path.write_bytes(b'consumer conflict\n')
        with self.assertRaisesRegex(ValueError, 'conflicts with reviewed'):
            workspace.reconcile_originals(target, self.root)
        self.assertEqual(b'consumer conflict\n', path.read_bytes())

    def test_baseline_vs_introduced_and_required_affected_failure(self):
        checks = [{'id': 'unrelated-existing', 'command': [sys.executable, '-c', 'raise SystemExit(7)'], 'affected': False}]
        flow.verify(self.root, checks, baseline=True)
        value = flow.verify(self.root, checks)
        self.assertEqual('pre-existing', value['checks'][0]['classification'])
        value = flow.verify(self.root, [{'id': 'new', 'command': [sys.executable, '-c', 'raise SystemExit(8)']}])
        self.assertEqual('introduced-or-unresolved', value['checks'][0]['classification'])
        self.assertFalse(flow.readiness(self.root)['requiredChecksCurrent'])

    def test_legacy_coverage_is_honest_and_does_not_create_age_only_gate(self):
        record(self.root, '0.9.0')
        value = flow.assess(self.root, self.guidance)
        self.assertIn('predates structured history', value['historyLimitations'][0])
        self.assertFalse(any(f['duePhase'] == 'upgrade' for f in value['findings']))

    def test_effective_targeting_is_scoped_and_direct_updater_rejects_sibling_override(self):
        with patch.dict(os.environ, {'SPECIFY_INIT_DIR': str(self.root.parent/'sibling')}):
            environment, targeting = workspace.effective_environment(self.root)
            self.assertEqual(str(self.root), environment['SPECIFY_INIT_DIR'])
            self.assertTrue(targeting['inheritedOverridePresent'])
            result = subprocess.run([sys.executable, str(ROOT/'scripts/upgrade_program_kit.py'), '--target', str(self.root)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn('PKU133', result.stderr)
            self.assertFalse((self.root/'.specify').exists())
            self.assertEqual(str(self.root.parent/'sibling'), os.environ['SPECIFY_INIT_DIR'])

    def test_snapshot_reproduction_conflicts_and_restore_protect_consumer_edits(self):
        archive = self.root.parent/'original'
        before = workspace.snapshot(self.root, archive, ['src/Notes/contract.txt'])
        target = self.root.parent/'empty'
        target.mkdir()
        workspace.reproduce(archive, target, before)
        self.assertEqual('named output\n', (target/'src/Notes/contract.txt').read_text())
        write(target, 'src/Notes/contract.txt', 'consumer customization')
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            workspace.reproduce(archive, target, before)
        changed = write(self.root, 'src/Notes/contract.txt', 'partial updater edit')
        after = {'src/Notes/contract.txt': flow.sha(changed)}
        write(self.root, 'src/Notes/contract.txt', 'concurrent consumer edit')
        with self.assertRaisesRegex(ValueError, 'consumer edit'):
            workspace.restore(self.root, archive, before, after)
        self.assertEqual('concurrent consumer edit', changed.read_text())
        changed.write_text('partial updater edit')
        workspace.restore(self.root, archive, before, after)
        self.assertEqual('named output\n', changed.read_text())


class InstalledUpgradeTests(unittest.TestCase):
    def test_packaged_command_scan_recipe_and_ignored_installation_are_real_installed_assets(self):
        from specify_cli.extensions import ExtensionManager
        from build_release import deterministic_zip
        import zipfile
        version = (ROOT / 'VERSION').read_text().strip()
        with tempfile.TemporaryDirectory(prefix='consumer-upgrade-installed-') as name:
            root = Path(name).resolve()
            source = root/'consumer'
            source.mkdir()
            flow.git(source, 'init')
            write(source, '.gitignore', '.specify/\n.agents/\nartifacts/\n')
            write(source, '.specify/init-options.json', {'ai': 'codex', 'ai_skills': True})
            (source/'.agents/skills').mkdir(parents=True)
            stage = root/'governance'
            shutil.copytree(ROOT/'extensions/program-kit-governance', stage, ignore=shutil.ignore_patterns('__pycache__'))
            build(ROOT, stage/'references/release-guidance', version)
            archive = root/'governance.zip'
            deterministic_zip(stage, archive)
            extracted = root/'extracted'
            with zipfile.ZipFile(archive) as package:
                package.extractall(extracted)
            ExtensionManager(source).install_from_directory(extracted, '1.1.2')
            skill = source/'.agents/skills/speckit-program-kit-governance-upgrade/SKILL.md'
            self.assertTrue(skill.is_file())
            self.assertIn('consumer_upgrade_workspace.py prepare', skill.read_text())
            installed = source/'.specify/extensions/program-kit-governance'
            result = subprocess.run([sys.executable, str(installed/'scripts/consumer_upgrade.py'), 'scan', '--repository', str(source)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertFalse(json.loads(result.stdout)['recordPresent'])
            self.assertTrue((installed/'references/consumer-migration-recipes.json').is_file())
            self.assertTrue((installed/'references/release-guidance'/f'consumer-changes-{version}.json').is_file())
            # Qualification source installation uses the existing synthetic installation metadata fixture;
            # the command payload and skill above were installed by the real public core manager.
            import validate_governance_state as fixture
            fixture.write_installation(source, version)
            # Retain actual governance payload and version-coherent fixture registries for the other components.
            shutil.copy2(extracted/'extension.yml', installed/'extension.yml')
            write(source, '.specify/integrations/codex.manifest.json', {'files': {
                '.agents/skills/speckit-specify/SKILL.md': {}, '.agents/skills/speckit-plan/SKILL.md': {}}})
            write(source, '.agents/skills/speckit-specify/SKILL.md', 'core specify fixture')
            write(source, '.agents/skills/speckit-plan/SKILL.md', 'core plan fixture')
            write(source, '.program-kit/dependency-profile.json', {'selected': 'unchanged exact fixture profile'})
            write(source, 'artifacts/cache/private-cache/secret', 'must never be copied')
            write(source, 'note.txt', 'retained output')
            commit(source)
            originals = {p: p.read_bytes() for p in (installed/'scripts/consumer_upgrade.py', skill)}
            target = root/'upgrade'
            value = workspace.prepare(source, target, ROOT, 'consumer-upgrade-fixture')
            self.assertEqual('prepare', value['stage'])
            self.assertFalse((target/'artifacts/cache/private-cache/secret').exists())
            self.assertEqual(originals, {p: p.read_bytes() for p in originals})
            self.assertTrue((target/'.specify/bundle-records.json').is_file())
            self.assertTrue((target/'.program-kit/dependency-profile.json').is_file())
            self.assertTrue((target/'.agents/skills/speckit-program-kit-governance-upgrade/SKILL.md').is_file())
            # Model coherent toolkit convergence separately from actual application checks.
            from release_guidance import completion, plan
            write(target, '.program-kit/installation/migration.json', completion(plan(extracted/'references/release-guidance', version, version), {}))
            checks = [{'id': 'retained-consumer-output', 'command': [sys.executable, '-c',
                       "from pathlib import Path; assert Path('note.txt').read_text() == 'retained output'"]}]
            flow.verify(target, checks)
            self.assertFalse(flow.readiness(target)['assessmentPerformed'])
            flow.assess(target, extracted/'references/release-guidance')
            value = flow.load(target)
            value['releaseInputsSha256'] = workspace.updater.release_fingerprint(ROOT)
            value['installedInputs'] = flow.capture(target, flow.installation_inputs(target))
            flow.save(target, value, 'exact-release')
            # Concurrent development is merged into the isolated branch and verified there.
            write(source, 'other.txt', 'intervening consumer development')
            commit(source, 'concurrent old-version development')
            review = workspace.integration_review(target, source)
            self.assertFalse(review['combinedCandidate'])
            self.assertIn('other.txt', review['changedSinceBaseline'])
            flow.git(target, 'merge', '--ff-only', flow.git(source, 'rev-parse', 'HEAD'))
            self.assertFalse(flow.readiness(target)['requiredChecksCurrent'])
            flow.verify(target, checks)
            workspace.integration_review(target, source)
            commit(target, 'reviewed upgrade source')
            flow.git(source, 'merge', '--ff-only', flow.git(target, 'rev-parse', 'HEAD'))
            before_activation = {p: p.read_bytes() for p in originals}
            # Observed interruption after partial installation must restore original owned setup,
            # preserve diagnostics and remove only files created by this attempt.
            def interrupted(destination, release):
                script = destination/'.specify/extensions/program-kit-governance/scripts/consumer_upgrade.py'
                script.write_bytes(script.read_bytes() + b'\n# partial installer mutation\n')
                write(destination, '.specify/partial-new-asset.json', {'partial': True})
                write(destination, 'note.txt', 'consumer edit during activation')
                raise KeyboardInterrupt('fixture operator interruption')
            with self.assertRaises(KeyboardInterrupt):
                workspace.activation(target, source, ROOT, checks, runner=interrupted)
            self.assertEqual(before_activation, {p: p.read_bytes() for p in originals})
            self.assertFalse((source/'.specify/partial-new-asset.json').exists())
            self.assertEqual('consumer edit during activation', (source/'note.txt').read_text())
            ledger_path = next((source/'artifacts/program-kit/consumer-activation').glob('*/activation.json'))
            self.assertEqual('recovered', flow.read(ledger_path)['status'])
            self.assertEqual('intervening consumer development', (source/'other.txt').read_text())
            with self.assertRaisesRegex(ValueError, 'differs from the combined'):
                workspace.activation(target, source, ROOT, checks, runner=lambda *_: None)
            write(source, 'note.txt', 'retained output')  # Explicit fixture restoration after reviewing the edit.
            def fixture_convergence(destination, release):
                write(destination, '.program-kit/installation/migration.json', flow.read(target/'.program-kit/installation/migration.json'))
                state = flow.load(destination)
                state['installedInputs'] = flow.capture(destination, flow.installation_inputs(destination))
                flow.save(destination, state, 'fixture-coherent-installation')
            result = workspace.activation(target, source, ROOT, checks, runner=fixture_convergence)
            self.assertTrue(result['activated'])
            self.assertFalse(result['applicationAcceptanceEstablished'])
            # Installed export remains local and does not expose full original setup.
            exported = source/'artifacts/local-maintenance.json'
            result = subprocess.run([sys.executable, str(installed/'scripts/consumer_upgrade.py'), 'export',
                '--repository', str(source), '--output', 'artifacts/local-maintenance.json'], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertFalse(flow.read(exported)['provenance']['rawLogsIncluded'])


class NativePresetBaselineTests(unittest.TestCase):
    """Actual maintained native install/resolution, not a mocked rendered baseline."""
    def setUp(self):
        from specify_cli.presets import PresetManager
        self.run = ROOT / 'artifacts/tests/consumer-upgrade-native' / uuid.uuid4().hex
        self.root = self.run / 'consumer'
        self.root.mkdir(parents=True)
        flow.git(self.root, 'init')
        write(self.root, '.gitignore', '.specify/\n.agents/\nartifacts/\n')
        write(self.root, '.specify/init-options.json', {'ai': 'codex', 'script': 'py', 'ai_skills': True})
        self.relative = '.agents/skills/speckit-analyze/SKILL.md'
        write(self.root, self.relative, 'Initial core integration content')
        self.initial = flow.sha(self.root / self.relative)
        write(self.root, '.specify/integrations/codex.manifest.json', {'files': {self.relative: self.initial}})
        # Native installation creates its own rendered skill and composed cache.
        self.manager = PresetManager(self.root)
        self.manager.install_from_directory(ROOT / 'presets/program-kit-governance-preset', '1.1.3')
        self.preset = self.root / '.specify/presets/program-kit-governance-preset'
        self.cache = self.preset / '.composed/speckit.analyze.md'
        self.assertTrue(self.cache.is_file())
        self.skill = self.root / self.relative
        self.assertIn('Program Kit operation dependency analysis', self.skill.read_text(encoding='utf-8'))
        commit(self.root)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}

    def inspect(self, customized=False):
        before = self.snapshot()
        observed = flow.inventory(self.root)
        after = self.snapshot()
        self.assertEqual(before, after, 'Native baseline inspection changed the consumer')
        self.assertEqual(customized, self.relative in observed['customizations'])
        flow.atomic(self.run / 'result.json', {'case': self.id(), 'before': before, 'after': after,
            'customizations': observed['customizations'], 'ownedInstallation': observed['ownedInstallation']})
        return observed

    def test_actual_append_install_is_baseline_and_preserves_every_consumer_file(self):
        observed = self.inspect()
        item = observed['ownedInstallation'][self.relative]
        self.assertEqual('active-native-preset', item['baselineOwner'])
        self.assertEqual(flow.sha(self.skill), item['baselineSha256'])
        self.assertNotEqual(self.initial, item['baselineSha256'])

    def test_edited_skill_and_matching_tampered_cache_remain_customization(self):
        pristine = self.skill.read_bytes()
        self.skill.write_bytes(pristine + b'\nConsumer-owned manual instruction\n')
        self.inspect(customized=True)
        # Generate a real native matching skill from a tampered installed cache.
        self.cache.write_text(self.cache.read_text(encoding='utf-8') + '\nConsumer-owned manual instruction\n', encoding='utf-8')
        from specify_cli.presets import PresetManifest
        self.manager._register_skills(PresetManifest(self.preset / 'preset.yml'), self.preset)
        self.assertIn('Consumer-owned manual instruction', self.skill.read_text(encoding='utf-8'))
        self.inspect(customized=True)

    def test_stale_cache_is_ignored_but_stale_skill_is_customization(self):
        self.cache.write_text('stale or malicious cache content', encoding='utf-8')
        self.inspect()
        self.skill.write_text('stale skill content', encoding='utf-8')
        self.inspect(customized=True)

    def test_replace_baseline_ignores_cache_and_preserves_real_edits(self):
        self.relative = '.agents/skills/speckit-tasks/SKILL.md'
        self.skill = self.root / self.relative
        write(self.root, '.specify/integrations/codex.manifest.json', {'files': {self.relative: self.initial}})
        write(self.preset, '.composed/speckit.tasks.md', 'tampered replace cache')
        self.inspect()
        self.skill.write_bytes(self.skill.read_bytes() + b'\nReal consumer task instruction\n')
        self.inspect(customized=True)

    def test_missing_unsupported_escaping_and_colliding_declarations_stay_unresolved(self):
        import yaml
        manifest = self.preset / 'preset.yml'
        original = manifest.read_bytes()
        for change in ('missing', 'unsupported', 'escaping', 'collision'):
            with self.subTest(change=change):
                data = yaml.safe_load(original)
                entry = next(t for t in data['provides']['templates'] if t['name'] == 'speckit.analyze')
                if change == 'missing':
                    entry['file'] = 'commands/missing.md'
                elif change == 'unsupported':
                    entry['strategy'] = 'prepend'
                elif change == 'escaping':
                    entry['file'] = '../../templates/commands/analyze.md'
                else:
                    data['provides']['templates'].append(copy.deepcopy(entry))
                manifest.write_text(yaml.safe_dump(data), encoding='utf-8')
                self.assertIsNone(flow.preset_baseline(self.root, self.relative, 'codex'))
                self.inspect(customized=True)
                manifest.write_bytes(original)

    def test_winning_replace_does_not_validate_irrelevant_lower_declarations(self):
        from specify_cli.presets import PresetManifest, PresetRegistry, PresetResolver
        import yaml
        top = self.root / '.specify/presets/top-replacement'
        top.mkdir()
        data = yaml.safe_load((self.preset / 'preset.yml').read_text(encoding='utf-8'))
        data['preset']['id'] = 'top-replacement'
        entry = next(t for t in data['provides']['templates'] if t['name'] == 'speckit.analyze')
        entry['strategy'] = 'replace'
        data['provides']['templates'] = [entry]
        write(top, 'preset.yml', yaml.safe_dump(data))
        write(top, entry['file'], '---\ndescription: Upper replacement\n---\nIndependent winning source\n')
        PresetRegistry(self.root / '.specify/presets').add('top-replacement', {'priority': 1, 'version': '0.12.11'})
        self.manager._register_skills(PresetManifest(top / 'preset.yml'), top)
        self.assertIn('Independent winning source', self.skill.read_text(encoding='utf-8'))
        manifest = self.preset / 'preset.yml'
        original = manifest.read_bytes()
        for problem in ('missing', 'unsupported', 'escaping'):
            with self.subTest(problem=problem):
                lower = yaml.safe_load(original)
                ignored = next(t for t in lower['provides']['templates'] if t['name'] == 'speckit.analyze')
                if problem == 'missing':
                    ignored['file'] = 'commands/missing.md'
                elif problem == 'unsupported':
                    ignored['strategy'] = 'prepend'
                else:
                    ignored['file'] = '../../escaped-source.md'
                manifest.write_text(yaml.safe_dump(lower), encoding='utf-8')
                observed = self.inspect()
                self.assertEqual(flow.sha(self.skill), observed['ownedInstallation'][self.relative]['baselineSha256'])
                manifest.write_bytes(original)

    def test_absolute_drive_unc_and_parent_sources_cannot_write_through_live_paths(self):
        import yaml
        manifest = self.preset / 'preset.yml'
        original = manifest.read_bytes()
        real_write = Path.write_bytes
        for unsafe in (str(self.preset / 'commands/speckit.analyze.md'),
                       '../program-kit-governance-preset/commands/speckit.analyze.md',
                       'C:/consumer-escape.md', '//server/share/consumer-escape.md',
                       'commands/../../consumer-escape.md'):
            with self.subTest(unsafe=unsafe):
                data = yaml.safe_load(original)
                entry = next(t for t in data['provides']['templates'] if t['name'] == 'speckit.analyze')
                entry['file'] = unsafe
                manifest.write_text(yaml.safe_dump(data), encoding='utf-8')
                before = self.snapshot()
                times = {p.relative_to(self.root).as_posix(): p.stat().st_mtime_ns
                         for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}
                def forbid_consumer_write(destination, payload):
                    self.assertFalse(destination.is_relative_to(self.root), 'Baseline rewrote a live consumer source')
                    return real_write(destination, payload)
                with patch.object(Path, 'write_bytes', forbid_consumer_write):
                    self.assertIsNone(flow.preset_baseline(self.root, self.relative, 'codex'))
                self.assertEqual(before, self.snapshot())
                self.assertEqual(times, {p.relative_to(self.root).as_posix(): p.stat().st_mtime_ns
                         for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts})
                self.inspect(customized=True)
                manifest.write_bytes(original)

    def test_missing_composition_base_and_changed_core_stay_unresolved_or_customized(self):
        from specify_cli.presets import PresetResolver
        import yaml
        manifest = self.preset / 'preset.yml'
        original = manifest.read_bytes()
        data = yaml.safe_load(original)
        entry = next(t for t in data['provides']['templates'] if t['name'] == 'speckit.analyze')
        entry['name'] = 'speckit.unavailable-base'
        manifest.write_text(yaml.safe_dump(data), encoding='utf-8')
        absent = '.agents/skills/speckit-unavailable-base/SKILL.md'
        write(self.root, absent, 'Consumer fragment with no base')
        before = self.snapshot()
        self.assertIsNone(flow.preset_baseline(self.root, absent, 'codex'))
        self.assertEqual(before, self.snapshot())
        manifest.write_bytes(original)
        # Fresh native core resolution must notice current source changes rather
        # than treating an older installed cache as authority for stale skills.
        upstream = PresetResolver(self.run).resolve_content('speckit.analyze', 'command')
        write(self.root, '.specify/templates/commands/analyze.md', upstream + '\nFresh maintained core source\n')
        observed = self.inspect(customized=True)
        self.assertNotEqual(flow.sha(self.skill), observed['ownedInstallation'][self.relative]['baselineSha256'])

    def test_linked_contributing_source_is_rejected_without_consumer_mutation(self):
        # Windows directory junctions need no administrator symlink privilege.
        source = self.preset / 'commands'
        target = self.run / 'linked-command-sources'
        shutil.copytree(source, target)
        backup = self.preset / 'original-commands'
        source.rename(backup)
        if os.name == 'nt':
            result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(source), str(target)],
                                    capture_output=True, text=True, check=True)
        else:
            source.symlink_to(target, target_is_directory=True)
        self.assertTrue(source.is_symlink() or getattr(source, 'is_junction', lambda: False)())
        before = self.snapshot()
        self.assertIsNone(flow.preset_baseline(self.root, self.relative, 'codex'))
        self.assertEqual(before, self.snapshot())
        # Inventory is fail-closed; it cannot silently grant preset ownership.
        observed = flow.inventory(self.root)
        self.assertIn(self.relative, observed['customizations'])
        flow.atomic(self.run / 'result.json', {'case': self.id(), 'before': before, 'after': self.snapshot(),
                                             'customizations': observed['customizations']})


if __name__ == '__main__':
    unittest.main()

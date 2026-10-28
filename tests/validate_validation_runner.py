"""Selection, input identity and failure semantics of local validation."""
import copy
import contextlib
import io
import json
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from owned_fixture import FixtureDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_validation as runner


class SelectionTests(unittest.TestCase):
    def test_explicit_checks_keep_command_budgets_without_inheriting_an_unselected_suite(self):
        import live.v2.supervisor as supervisor
        for suite, explicit, elapsed, command_limit, expected, aggregate in (
            ('Integrity', True, 70, 300, 0, None),
            ('Integrity', True, 310, 300, 1, None),
            ('Integrity', False, 70, 300, 1, 60),
            ('Baseline', False, 610, 1000, 1, 600),
        ):
            with self.subTest(suite=suite, explicit=explicit, elapsed=elapsed), FixtureDirectory() as directory:
                root = Path(directory)
                check = dict(id='synthetic-upgrade', kind='integration', needs=[],
                             budgetSeconds=command_limit, timeoutSeconds=1200)
                definition = {'checks': [check], 'suiteBudgetsSeconds': {'Integrity': 60, 'Baseline': 600}}
                argv = ['run_validation.py', '--suite', suite]
                if explicit:
                    argv += ['--check', check['id'], '--reason', 'synthetic selected upgrade budget']
                with patch.object(runner, 'ROOT', root), \
                        patch.object(runner, 'load_definition', return_value=definition), \
                        patch.object(runner, 'selected', return_value=[check]), \
                        patch.object(runner, 'git', return_value='synthetic'), \
                        patch.object(runner, 'input_snapshot', return_value={'digest': 'fixed'}), \
                        patch.object(runner, 'missing_prerequisites', return_value=[]), \
                        patch.object(runner, 'prerequisite_versions', return_value={}), \
                        patch.object(runner, 'command', return_value=['synthetic-no-process']), \
                        patch.object(runner.sys, 'argv', argv), \
                        patch.object(supervisor, 'run_supervised', return_value=SimpleNamespace(
                            exitCode=0, timedOut=False, cleanupComplete=True, logsDrained=True)), \
                        patch.object(runner.time, 'monotonic', side_effect=[0, 0, 0, 0, elapsed, elapsed]), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(expected, runner.main())
                journal = json.loads(next((root / 'artifacts/validation-runs').glob('*/results.json')).read_text())
                self.assertEqual(aggregate, journal['suiteBudgetSeconds'])
                self.assertEqual(elapsed > command_limit, journal['steps'][0]['overBudget'])
                self.assertEqual(bool(aggregate and elapsed > aggregate), journal['overBudget'])

    def test_known_device_admission_is_scoped_to_selected_requirements(self):
        policy = runner.device_policy()
        with patch.object(runner, 'device_policy', return_value=policy), \
                patch.object(policy, 'require_tool') as admit:
            self.assertEqual([], runner.missing_prerequisites({'id': 'git-only', 'prerequisites': ['tool:git']}))
            admit.assert_called_once_with(runner.ROOT, 'git', authority='Selected check git-only')
        with patch.object(runner, 'device_policy', return_value=policy), \
                patch.object(policy, 'require_tool') as admit:
            runner.missing_prerequisites({'id': 'library-only', 'prerequisites': ['module:json']})
            admit.assert_not_called()

    def definition(self):
        return {'capabilities': {
            'producer': {'inputs': ['producer/**'], 'dependsOn': []},
            'client': {'inputs': ['client/**'], 'dependsOn': ['producer']},
            'unrelated': {'inputs': ['other/**'], 'dependsOn': []}},
            'checks': [dict(id='unit', capabilities=['producer'], inputs=['tests/unit.py'], needs=[], suites=['Integrity']),
                       dict(id='client', capabilities=['client'], inputs=['tests/client.py'], needs=[], suites=[]),
                       dict(id='other', capabilities=['unrelated'], inputs=[], needs=[], suites=[]),
                       dict(id='broad', capabilities=['producer'], inputs=['tests/broad.py'], needs=[], suites=[], manualOnly=True)]}

    def test_reverse_transitive_dependencies_select_consumers_but_not_unrelated_checks(self):
        checks, gaps, reasons = runner.select_affected(self.definition(), ['producer/export.py'])
        self.assertEqual(['unit', 'client'], [c['id'] for c in checks])
        self.assertFalse(gaps)
        self.assertEqual(['depends on: producer'], reasons['client'])

    def test_unknown_input_does_not_select_everything(self):
        checks, gaps, _ = runner.select_affected(self.definition(), ['new/subsystem.py'])
        self.assertEqual(['unit'], [c['id'] for c in checks])
        self.assertEqual(['new/subsystem.py'], gaps)

    def test_source_policy_templates_select_released_native_controls(self):
        definition = runner.load_definition()
        for name in ('.editorconfig', 'eng/ProgramKit.Build.props', 'eng/ProgramKit.Build.targets'):
            with self.subTest(template=name):
                checks, gaps, _ = runner.select_affected(definition,
                    ['extensions/program-kit-dotnet/templates/dotnet/files/' + name])
                ids = {check['id'] for check in checks}
                self.assertFalse(gaps)
                self.assertIn('validate_coding_scaffolding', ids)
                self.assertIn('validate_native_source_scope', ids)
                self.assertNotIn('validate_source_readability_native', ids, 'Candidate qualification remains explicitly selected')

    def test_known_capability_without_runnable_coverage_is_still_a_gap(self):
        definition = self.definition()
        definition['capabilities']['uncovered'] = {'inputs': ['uncovered/**'], 'dependsOn': []}
        checks, gaps, _ = runner.select_affected(definition, ['uncovered/runtime.py'])
        self.assertEqual(['unit'], [c['id'] for c in checks])
        self.assertTrue(any('capability uncovered' in gap for gap in gaps))

    def test_check_change_selects_itself(self):
        checks, gaps, reasons = runner.select_affected(self.definition(), ['tests/client.py'])
        self.assertEqual(['unit', 'client'], [c['id'] for c in checks])
        self.assertFalse(gaps)
        self.assertIn('changed check input: tests/client.py', reasons['client'])

    def test_changed_manual_check_cannot_disappear_behind_integrity(self):
        definition = self.definition()
        manual = definition['checks'][-1]
        manual['command'] = ['{python}', 'tests/broad.py']
        deferred = runner.deferred_checks(definition, ['tests/broad.py'])
        self.assertEqual([{'id': 'broad', 'changedInputs': ['tests/broad.py']}], deferred)
        self.assertEqual([], runner.deferred_checks(definition, ['other/change.py']))

    def test_prerequisite_closure_is_ordered_and_rejects_cycles(self):
        checks = [dict(id='consumer', needs=['producer']), dict(id='producer', needs=[])]
        self.assertEqual(['producer', 'consumer'], [c['id'] for c in runner.closure(checks, ['consumer'])])
        checks[1]['needs'] = ['consumer']
        with self.assertRaisesRegex(ValueError, 'cycle'):
            runner.closure(checks, ['consumer'])
        with self.assertRaisesRegex(ValueError, 'Unknown checks'):
            runner.closure(checks, ['missing'])

    def test_snapshot_binds_dirty_untracked_and_deleted_contents(self):
        with FixtureDirectory(prefix='validation-input-') as directory:
            root = Path(directory)
            (root / 'tracked').write_text('old')
            (root / 'new').write_text('untracked')
            with patch.object(runner, 'ROOT', root), patch.object(runner, 'git', return_value='tracked\0new\0deleted\0'):
                before = runner.input_snapshot()
                (root / 'tracked').write_text('dirty')
                after = runner.input_snapshot()
            self.assertNotEqual(before['digest'], after['digest'])
            self.assertIn('new', before['files'])
            self.assertIsNone(before['files']['deleted'])

    def test_missing_prerequisites_are_per_check(self):
        check = dict(platforms=[runner.platform.system()], prerequisites=[])
        self.assertEqual([], runner.missing_prerequisites(check))
        check['prerequisites'] = ['tool:program-kit-nonexistent-tool']
        self.assertEqual(check['prerequisites'], runner.missing_prerequisites(check))

    def test_previous_release_prerequisite_follows_history_and_reports_missing_tag(self):
        # Historical fixtures can explicitly request their own declared prior
        # tag; the preview re-onboarding boundary does not invent a 0.x edge.
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'VERSION').write_text('0.9.2\n')
            (root / 'releases').mkdir()
            (root / 'releases/history.json').write_text(json.dumps({'entries':[{'version':'0.9.2','previous':'0.9.1'}]}))
            with patch.object(runner, 'ROOT', root):
                reference = runner.prerequisite_git_ref('previous-release')
                self.assertEqual('refs/tags/v0.9.1', reference)
                self.assertEqual('refs/tags/fixture', runner.prerequisite_git_ref('refs/tags/fixture'))
                check = dict(platforms=[runner.platform.system()], prerequisites=['git-ref:previous-release'])
                with patch.object(runner, 'git', side_effect=ValueError('missing tag')) as git:
                    missing = runner.missing_prerequisites(check)
                    self.assertIn('make the supported historical fixture tag available', missing[0])
                    self.assertEqual(reference + '^{commit}', git.call_args.args[-1])
        preview = next(c for c in runner.load_definition()['checks'] if c['id'] == 'mechanics-upgrade')
        self.assertNotIn('git-ref:previous-release', preview.get('prerequisites', []))

    def test_active_definition_is_valid_and_integrity_has_no_integration(self):
        definition = runner.load_definition()
        self.assertTrue(definition['capabilities'])
        self.assertTrue(runner.selected('Integrity'))
        self.assertTrue(all(c['kind'] == 'unit' for c in runner.selected('Integrity')))
        self.assertTrue(all(not c.get('manualOnly') for c in runner.selected('Baseline')))
        self.assertEqual(6, len(runner.selected('Baseline')))

    def test_preview_toolkit_replacement_selects_owned_upgrade_coverage(self):
        checks, gaps, _ = runner.select_affected(runner.load_definition(), [
            'scripts/upgrade_program_kit.py'])
        self.assertEqual([], gaps)
        ids = {c['id'] for c in checks}
        self.assertIn('mechanics-upgrade', ids)
        self.assertIn('validate_preview_distribution', ids)
        self.assertIn('validate_coding_installation_contracts', ids)
        self.assertFalse(any(c.get('manualOnly') for c in checks))
        self.assertNotIn('mechanics-founding', ids)

    def test_feature_phase_change_does_not_select_founding(self):
        checks, gaps, _ = runner.select_affected(runner.load_definition(), [
            'extensions/program-kit-governance/scripts/phase_obligations.py'])
        ids = {c['id'] for c in checks}
        self.assertFalse(gaps)
        self.assertIn('mechanics-phases', ids)
        self.assertNotIn('mechanics-founding', ids)
        self.assertIn('validate_native_phases', ids)
        self.assertFalse(any(c.get('manualOnly') for c in checks))
        self.assertFalse({'validate_coding_evaluation_journey', 'validate_coding_adverse_boundary',
                          'validate_story_delivery'} & ids)

    def test_native_evidence_owners_have_focused_affected_coverage(self):
        checks, gaps, _ = runner.select_affected(runner.load_definition(), [
            'extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py',
            'extensions/program-kit-dotnet/templates/dotnet/files/eng/toolkit_verification.py'])
        self.assertFalse(gaps)
        ids = {c['id'] for c in checks}
        self.assertIn('validate_native_phases', ids)
        self.assertIn('validate_test_dependencies', ids)
        self.assertNotIn('mechanics-founding', ids)

    def test_shared_governance_change_selects_both_consumers(self):
        checks, gaps, _ = runner.select_affected(runner.load_definition(), [
            'extensions/program-kit-governance/scripts/governance_state.py'])
        ids = {c['id'] for c in checks}
        self.assertFalse(gaps)
        self.assertTrue({'mechanics-phases', 'mechanics-founding'} <= ids)

    def test_shared_foundation_contract_selects_narrow_native_consumers(self):
        checks, gaps, reasons = runner.select_affected(runner.load_definition(), [
            'extensions/program-kit-dotnet/scripts/foundation_composition.py'])
        ids = {c['id'] for c in checks}
        self.assertFalse(gaps)
        self.assertTrue({'validate_postgresql_lifecycle', 'validate_openapi_export_client'} <= ids)
        self.assertIn('depends on: dotnet-runtime', reasons['validate_postgresql_lifecycle'])
        self.assertIn('depends on: dotnet-runtime', reasons['validate_openapi_export_client'])
        self.assertNotIn('qualify_composition_start', ids)
        self.assertNotIn('validate_typed_operation', ids)

    def test_active_maintenance_pins_have_focused_coverage(self):
        import dependency_maintenance as maintenance
        inventory = maintenance.inventory(runner.ROOT, maintenance.read_json(runner.ROOT / 'maintenance-policy.json'))
        paths = sorted({path for pin in inventory['pins'] for path in pin['paths']})
        checks, gaps, _ = runner.select_affected(runner.load_definition(), paths)
        self.assertEqual([], gaps)
        ids = {c['id'] for c in checks}
        self.assertTrue({'validate_dependency_updates', 'validate_dependency_workflows',
                         'validate_guardian_workflow', 'mechanics-scaffold',
                         'validate_composition_tooling', 'validate_openapi_export_client'} <= ids)
        self.assertFalse(any(c.get('manualOnly') for c in checks))
        self.assertFalse({'qualify_composition_start', 'validate_typed_operation', 'validate_emitted_ci'} & ids)

    def test_generic_phases_need_no_schema_history_but_selected_schema_checks_declare_their_own_runtime(self):
        check = next(c for c in runner.load_definition()['checks'] if c['id'] == 'validate_native_phases')
        self.assertNotIn('runtime:json-schema', check.get('prerequisites', []))
        selected_schema = {'prerequisites': ['runtime:json-schema']}
        with patch.object(runner, 'schema_runtime_ready', return_value=False):
            missing = runner.missing_prerequisites(selected_schema)
        self.assertEqual(1, len(missing))
        self.assertIn('runtime:json-schema; prepare with ', missing[0])
        self.assertIn('schema_runtime.py setup', missing[0])

    def test_guardian_pin_change_selects_its_small_source_contract(self):
        checks, gaps, _ = runner.select_affected(runner.load_definition(), [
            'evidence-repository/.github/workflows/guardian.yml'])
        self.assertEqual([], gaps)
        ids = {c['id'] for c in checks}
        self.assertIn('validate_guardian_workflow', ids)
        self.assertNotIn('validate_repair_feedback', ids)
        self.assertFalse(any(c['kind'] == 'integration' for c in checks))


if __name__ == '__main__':
    unittest.main(verbosity=2)

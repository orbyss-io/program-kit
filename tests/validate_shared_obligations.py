"""Portable old shared obligations against current contracts, with fictional state only."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'extensions/program-kit-governance/scripts'),
               str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng')]
from owned_fixture import FixtureDirectory
from validate_story_delivery import seed
import task_draft as draft
from test_project import scaffold


class TaskScopedFailures(unittest.TestCase):
    def setUp(self):
        self.scratch = FixtureDirectory(prefix='required-failure-'); self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name); self.feature = self.root / 'specs/synthetic'
        self.feature.mkdir(parents=True); seed(self.root, self.feature)
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('- [ ]', '- [X]'))
        self.failure = 'Synthetic required qualification remains unimplemented.'
        draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Synthetic',
                         'next': 'Repair required failure', 'failures': [self.failure]})

    def write_hint(self, scope):
        # Historical undeclared fields remain inert. Never invent a scope waiver
        # or use a retired product specification to supply current authority.
        target = self.feature / 'tasks.md'; value = draft.current(self.feature)
        value['failureScopes'] = {hashlib.sha256(self.failure.encode()).hexdigest(): scope}
        target.write_text(draft.CURRENT.sub('', target.read_text()).rstrip() +
                          '\n<!-- program-kit:current-checkpoint ' + json.dumps(value) + ' -->\n')

    def engineering(self):
        before = copy.deepcopy(draft.load_failures(self.feature))
        with self.assertRaisesRegex(ValueError, 'Resolve required technical failures'):
            draft.transition(self.root, self.feature, {'action': 'engineering', 'checkpoint': 'US1',
                'checks': ['artifacts/passing.json']}, now=0)
        self.assertEqual(before, draft.load_failures(self.feature))

    def test_later_task_hint_cannot_waive_a_retained_required_failure(self):
        self.write_hint(['T003']); self.engineering()

    def test_unscoped_failure_still_blocks_current_story(self): self.engineering()

    def test_current_task_failure_still_blocks_current_story(self):
        self.write_hint(['T001']); self.engineering()

    def test_unknown_task_scope_cannot_suppress_retained_failure(self):
        self.write_hint(['T999']); self.engineering()

    def test_mixed_current_and_later_failure_scope_still_blocks_current_story(self):
        self.write_hint(['T001', 'T003']); self.engineering()

    def test_unsupported_failure_scope_is_rejected_and_failure_is_preserved(self):
        before = (self.feature / 'tasks.md').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Checkpoint accepts only'):
            draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Synthetic',
                'next': 'Repair', 'failureScopes': {self.failure: ['T003']}})
        self.assertEqual(before, (self.feature / 'tasks.md').read_bytes())
        self.assertEqual([self.failure], draft.load_failures(self.feature))

    def test_resolved_failure_removes_only_its_obsolete_scope(self):
        self.write_hint(['T003'])
        draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Synthetic',
            'next': 'Continue', 'resolvedFailures': [self.failure], 'checks': ['artifacts/passing.json']})
        self.assertEqual([], draft.load_failures(self.feature))
        self.assertNotIn('failureScopes', draft.current(self.feature))
        self.assertIn(self.failure, json.dumps(draft.progress_history(self.feature)))


class TestProjectAliasTests(unittest.TestCase):
    def project(self, package):
        return {'path': 'tests/Synthetic.Tests/Synthetic.Tests.csproj', 'role': 'test',
                'packageReferences': [package], 'projectReferences': [],
                'responsibilities': [{'name': 'Synthetic.Tests', 'kind': 'test',
                                      'effects': [], 'testSeams': ['pure-core']}]}

    def test_selected_alias_preserves_direct_identity_and_mtp(self):
        document = ET.fromstring(scaffold(self.project('xunit.v3'), {'xunit.v3': '4.0.2'}))
        self.assertEqual(['xunit.v3'], [p.get('Include') for p in document.findall('.//PackageReference')])
        self.assertEqual('true', document.findtext('.//UseMicrosoftTestingPlatformRunner'))

    def test_explicit_mtp_package_still_supported(self):
        scaffold(self.project('xunit.v3.mtp-v2'), {'xunit.v3.mtp-v2': '4.0.2'})

    def test_unqualified_alias_versions_rejected(self):
        for version in ('3.2.2', '5.0.0', '4.0.1'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                scaffold(self.project('xunit.v3'), {'xunit.v3': version})

    def test_missing_pin_and_other_framework_remain_rejected(self):
        for package, pins in (('xunit.v3', {}), ('NUnit', {'nunit': '4.0.2'})):
            with self.subTest(package=package), self.assertRaises(ValueError): scaffold(self.project(package), pins)


# Append to the maintained test module after the committed suite finishes.
import os
import shutil
import subprocess
from handoff_contract import source_inputs


class PackSourceInputTests(unittest.TestCase):
    def setUp(self):
        self.scratch = FixtureDirectory(prefix='pack-source-'); self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def write(self, name, text):
        target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def test_generated_engineering_props_do_not_invalidate_authored_source(self):
        self.write('eng/inspection/Rules.props', '<Project />'); before = source_inputs(self.root)
        for name in ('eng/inspection/obj/Tool.csproj.nuget.g.props',
                     'eng/inspection/obj/Tool.csproj.nuget.g.targets', 'eng/inspection/bin/generated.py'):
            self.write(name, 'derived')
        self.assertEqual(before, source_inputs(self.root))

    def test_actual_engineering_source_changes_still_invalidate_pack(self):
        self.write('eng/inspection/Rules.props', 'before'); before = source_inputs(self.root)
        self.write('eng/inspection/Rules.props', 'after'); self.assertNotEqual(before, source_inputs(self.root))

    def test_native_application_assets_and_locks_remain_observed(self):
        self.write('src/Owner/Owner.csproj', '<Project />')
        self.write('src/Owner/obj/project.assets.json', '{}'); self.write('src/Owner/packages.lock.json', '{}')
        before = source_inputs(self.root); self.assertIn('src/Owner/obj/project.assets.json', before)
        self.write('src/Owner/obj/project.assets.json', '{"changed":true}')
        self.assertNotEqual(before, source_inputs(self.root)); before = source_inputs(self.root)
        self.write('src/Owner/packages.lock.json', '{"changed":true}'); self.assertNotEqual(before, source_inputs(self.root))


class VerificationCommandTests(unittest.TestCase):
    def setUp(self):
        self.scratch = FixtureDirectory(prefix='typed-wrapper-', native=True); self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name); (self.root / 'eng').mkdir()
        source = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
        for path in (source / 'eng').iterdir():
            if path.is_file() and path.suffix in ('.py', '.ps1', '.psm1', '.json'):
                shutil.copyfile(path, self.root / 'eng' / path.name)
        for name in ('.nvmrc', '.npm-version', 'global.json'): shutil.copyfile(source / name, self.root / name)
        shutil.copyfile(ROOT / '.python-version', self.root / '.python-version')
        (self.root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [], 'bindings': []}}))
        self.shell = os.environ.get('PROGRAM_KIT_POWERSHELL_EXECUTABLE') or shutil.which('pwsh')
        self.assertTrue(self.shell, 'Prepare the selected PowerShell before the emitted command contract')
        self.environment = dict(os.environ, SPECKIT_PYTHON=sys.executable, PYTHONUTF8='1')

    def invoke(self, *arguments):
        return subprocess.run([self.shell, '-NoProfile', '-File', str(self.root / 'eng/Invoke-RepositoryVerification.ps1'),
            *arguments], cwd=self.root, env=self.environment, capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_formal_boundaries_refuse_development_narrowing(self):
        for mode in ('CI', 'Release'):
            with self.subTest(mode=mode):
                result = self.invoke('-Mode', mode, '-Scope', 'Acceptance', '-Projects', 'tests/Synthetic.Tests/Synthetic.Tests.csproj')
                self.assertNotEqual(0, result.returncode); self.assertIn('Acceptance cannot be narrowed', result.stdout + result.stderr)

    def test_release_refuses_scoped_development_even_with_release_configuration(self):
        result = self.invoke('-Mode', 'Release', '-Scope', 'Focused', '-Projects', 'tests/Synthetic.Tests/Synthetic.Tests.csproj',
                             '-Configuration', 'Release', '-Reason', 'Synthetic command contract', '-Plan')
        self.assertNotEqual(0, result.returncode); self.assertIn('cannot claim Release acceptance', result.stdout + result.stderr)

    def test_valid_named_owner_plan_and_unknown_owner_keep_scoped_diagnostics_without_execution(self):
        (self.root / 'docs').mkdir(); (self.root / 'docs/input.json').write_text('{}')
        (self.root / 'eng/required.py').write_text('raise AssertionError("Plan must not execute a test")\n')
        declaration = {'id': 'required-current', 'script': 'eng/required.py', 'arguments': [],
                       'inputs': ['docs/input.json'], 'timeoutSeconds': 10}
        (self.root / 'eng/verification.json').write_text(json.dumps({'schemaVersion': 1, 'toolkitChecks': [declaration]}))
        result = self.invoke('-Scope', 'Focused', '-Checks', 'required-current', '-Plan')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        value = json.loads(result.stdout); self.assertEqual(['required-current'], value['toolkitChecks'])
        self.assertEqual([], value['projects']); self.assertFalse(value['acceptanceEstablished'])
        self.assertFalse((self.root / 'artifacts/tests/toolkit-runs').exists())
        result = self.invoke('-Scope', 'Focused', '-Checks', 'unknown-owner', '-Plan')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('PKV003 unknown named toolkit check', result.stdout + result.stderr)
        self.assertFalse((self.root / 'artifacts/tests/toolkit-runs').exists())


if __name__ == '__main__': unittest.main()

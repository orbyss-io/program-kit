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


if __name__ == '__main__': unittest.main()

"""F7 duty completeness and maintained evidence admission; no agents/providers."""
from pathlib import Path
import copy
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from dotnet_adapter import bootstrap
bootstrap()
import coding_context as coding
import coding_patterns as patterns
import task_draft
import toolkit_verification as toolkit
from owned_fixture import FixtureDirectory


class EvaluationTests(unittest.TestCase):
    def test_task_control_labels_are_not_async_but_real_source_remains_visible(self):
        from feature_context import affirmative, MECHANISMS
        import re
        prose = affirmative('# Fictional task plan\n## Task dependency map\n| Task | Operation |\n- [ ] T001 Read immutable rows\n')
        self.assertFalse(re.search(MECHANISMS['async'], prose, re.I))
        self.assertTrue(re.search(MECHANISMS['async'], 'public Task<int> ReadAsync()', re.I))

    def setUp(self):
        self.owner = FixtureDirectory(native=True)
        self.addCleanup(self.owner.cleanup)
        self.root = Path(self.owner.name)
        self.feature = self.root / 'specs/001-proof'
        self.feature.mkdir(parents=True)
        (self.feature / 'tasks.md').write_text('- [ ] T001 Apply owned behavior\n')
        (self.root / 'review.md').write_text('Scoped fictional review: inspect ownership, effects and source style. No human acceptance claim.')
        (self.root / 'check.py').write_text('print("Independent executed finite check")\n')
        (self.root / 'Owner.cs').write_text('internal sealed class Owner {}\n')
        (self.root / 'eng').mkdir()
        self.config = {'schemaVersion': 1, 'toolkitChecks': [{'id': 'proof', 'script': 'check.py', 'arguments': [],
                       'inputs': ['check.py'], 'timeoutSeconds': 5}]}
        (self.root / 'eng/verification.json').write_text(json.dumps(self.config))
        self.rows = toolkit.declarations(self.root, self.config)
        self.execute()
        self.value = {'scope': {'taskIds': ['T001']}, 'inputs': [coding.source(self.root, self.feature / 'tasks.md'), coding.source(self.root, self.root / 'Owner.cs')],
                      'projects': [], 'frontendProjects': [], 'profiles': [], 'patternsContext': {}, 'architecture': {},
                      'nativeContext': {'applicable': True, 'configuration': 'Debug', 'framework': None},
                      'evaluation': {'duties': [{'rule': 'owned', 'fingerprint': 'one', 'required': True,
                                                 'technicalRequired': True, 'owner': 'actual behavior owner'},
                                                {'rule': 'semantic', 'fingerprint': 'two', 'required': True,
                                                 'technicalRequired': False, 'owner': 'semantic reviewer'}]}}

    def execute(self):
        return toolkit.execute(self.root, ['proof'], self.rows)

    def claim(self, **change):
        rules = change.get('rules', ['owned', 'semantic'])
        return {'rules': ['owned', 'semantic'], 'checks': [{'kind': 'toolkit', 'id': 'proof'}], 'review': 'review.md',
                'authorship': {'implementationAuthors': ['fictional-implementer'], 'reviewer': 'fictional-reviewer', 'kind': 'agent'},
                'inspections': [{'rules': [rule], 'sources': [{'path': 'Owner.cs', 'start': 1, 'end': 1}],
                                 'boundary': 'Fictional Owner declaration and caller capability',
                                 'findings': ['No effectful behavior is claimed by this empty declaration.'],
                                 'assessment': 'Inspected ' + rule + ' against the finite source declaration.'} for rule in rules],
                'conclusion': 'Finite behavior and scoped source responsibilities inspected independently.',
                'limits': 'Fictional authored review; actual check is finite Python behavior only.', **change}

    def bind(self, **change):
        return coding.bind_evaluation(self.root, self.feature, self.value, [self.claim(**change)])

    def test_required_rule_without_unit_or_check_is_still_visible(self):
        (self.root / 'rule.md').write_text('Canonical semantic duty with no registered mechanical check.')
        catalog = {'sources': [{'id': 'local', 'locator': {'kind': 'repository', 'path': 'rule.md'}}],
                   'rules': {'unlisted': {'source': 'local', 'selector': {'kind': 'document'}, 'owner': 'semantic owner',
                                          'level': 'mandatory', 'bindings': {}, 'limits': 'Source review only'}}}
        blockers = []
        duties = coding.evaluation_duties(catalog, [{'ruleIds': ['unlisted'], 'proof': 'review'}], [],
                                          self.root, ROOT / 'extensions', blockers)
        self.assertFalse(blockers)
        self.assertEqual(['unlisted'], [d['rule'] for d in duties])
        self.assertTrue(duties[0]['required'])
        self.assertFalse(duties[0]['technicalRequired'])

    def test_complete_claims_pass_but_omission_and_checked_boxes_do_not(self):
        records = self.bind()
        coding.require_evaluated(self.root, self.feature, self.value, records)
        partial = self.bind(rules=['owned'])
        (self.feature / 'tasks.md').write_text('- [X] T001 Apply owned behavior\n')
        with self.assertRaisesRegex(ValueError, 'semantic.*semantic reviewer'):
            coding.require_evaluated(self.root, self.feature, self.value, partial)
        coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_completion_combines_current_scopes_without_omitting_a_task(self):
        first = self.bind()
        second_value = copy.deepcopy(self.value)
        second_value['scope']['taskIds'] = ['T002']
        second = coding.bind_evaluation(self.root, self.feature, second_value, [self.claim()])
        whole = copy.deepcopy(self.value)
        whole['scope']['taskIds'] = ['T001', 'T002']
        coding.require_evaluated(self.root, self.feature, whole, first + second)
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, whole, first)

    def test_distinct_project_package_contexts_combine_without_repeating_correct_handoffs(self):
        def context(name, task):
            value = copy.deepcopy(self.value)
            relative = 'src/' + name + '/' + name + '.csproj'
            target = self.root / relative
            target.parent.mkdir(parents=True)
            target.write_text('<Project/>')
            value['scope']['taskIds'] = [task]
            value['projects'] = [{'path': relative, 'status': 'evaluated', 'properties': {'TargetFramework': 'net10.0'},
                                  'packages': [{'id': name, 'version': '1.0.0'}]}]
            value['patternsContext'] = {'packages': [[name, '1.0.0']], 'runtimeInventory': ['fictional runtime identity']}
            return value
        first = context('First', 'T001')
        second = context('Second', 'T002')
        records = [*coding.bind_evaluation(self.root, self.feature, first, [self.claim()]),
                   *coding.bind_evaluation(self.root, self.feature, second, [self.claim()])]
        whole = copy.deepcopy(first)
        whole['scope']['taskIds'] = ['T001', 'T002']
        whole['projects'] += second['projects']
        whole['patternsContext']['packages'] += second['patternsContext']['packages']
        coding.require_evaluated(self.root, self.feature, whole, records)
        whole['projects'][1]['packages'][0]['version'] = '2.0.0'
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, whole, records)
        coding.require_evaluated(self.root, self.feature, first, records)

    def test_source_review_is_distinct_from_mandatory_actual_behavior(self):
        with self.assertRaisesRegex(ValueError, 'behavior checks remain due'):
            self.bind(checks=[])
        records = self.bind(rules=['semantic'], checks=[])
        self.value['evaluation']['duties'] = self.value['evaluation']['duties'][1:]
        coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_canonical_source_review_scope_and_configuration_stale_old_claims(self):
        records = self.bind()
        for mutate in (lambda v: v['evaluation']['duties'][0].update(fingerprint='changed'),
                       lambda v: v['scope'].update(taskIds=['T999']),
                       lambda v: v['nativeContext'].update(configuration='Release')):
            value = copy.deepcopy(self.value)
            mutate(value)
            with self.assertRaisesRegex(ValueError, 'PKC020'):
                coding.require_evaluated(self.root, self.feature, value, records)
        (self.root / 'review.md').write_text('Changed authored conclusions')
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_status_only_copied_and_tampered_execution_cannot_be_admitted(self):
        (self.root / 'fake.json').write_text('{"status":"completed"}')
        with self.assertRaisesRegex(ValueError, 'maintained.*owner'):
            task_draft.check_artifacts(self.root, ['fake.json'])
        actual = patterns.current_check(self.root, {'kind': 'toolkit', 'id': 'proof'})
        reference = actual['run']
        task_draft.check_artifacts(self.root, [reference])
        (self.root / 'replay.json').write_bytes((self.root / reference).read_bytes())
        with self.assertRaisesRegex(ValueError, 'maintained.*owner'):
            task_draft.check_artifacts(self.root, ['replay.json'])
        result = json.loads((self.root / reference).read_text())
        stream = next(iter(result['outcomes'][0]['evidence']))
        (self.root / stream).write_text('altered retained execution')
        with self.assertRaisesRegex(ValueError, 'Stale/corrupt'):
            task_draft.check_artifacts(self.root, [reference])

    def test_native_admission_calls_current_reader_beyond_report_integrity(self):
        import repository_verification as native
        directory = self.root / 'artifacts/tests/runs/synthetic'
        directory.mkdir(parents=True)
        log = directory / 'native.log'
        log.write_text('Synthetic reader-boundary input; no native execution claim.')
        reference = 'artifacts/tests/runs/synthetic/result.json'
        outcome = {'project': 'tests/Example.csproj', 'status': 'completed', 'executedTests': 1, 'fingerprint': 'synthetic',
                   'evidence': {log.relative_to(self.root).as_posix(): native.digest(log.read_bytes())}}
        (self.root / reference).write_text(json.dumps({'schemaVersion': 2, 'status': 'completed', 'testArguments': [],
                                                      'configuration': 'Debug', 'outcomes': [outcome]}))
        self.assertTrue(native.evidence_valid(self.root, self.root / reference, outcome))
        with patch.object(patterns, 'current_check', side_effect=ValueError('native current plan rejects stale source')) as reader:
            with self.assertRaisesRegex(ValueError, 'stale source'):
                task_draft.check_artifacts(self.root, [reference])
            reader.assert_called_once_with(self.root, {'kind': 'native', 'project': 'tests/Example.csproj',
                'arguments': [], 'configuration': 'Debug'}, reference, handoff=True)
        self.assertFalse(native.evidence_valid(self.root, self.root / reference, {**outcome, 'executedTests': True}))

    def test_stale_source_and_later_failed_execution_cannot_replay_qualification(self):
        records = self.bind()
        previous = patterns.current_check(self.root, {'kind': 'toolkit', 'id': 'proof'})
        (self.root / 'check.py').write_text('raise SystemExit(7)\n')
        with self.assertRaises(ValueError):
            self.execute()
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)
        with self.assertRaises(ValueError):
            task_draft.check_artifacts(self.root, [previous['run']])
        # Historical integrity remains inspectable independently of current reuse.
        task_draft.check_artifacts(self.root, [previous['run']], freshness=False)

    def test_unsupported_mechanism_and_unknown_rule_do_not_bind(self):
        for change in ({'checks': [{'kind': 'invented', 'command': 'never execute'}]}, {'rules': ['unknown']},
                       {'review': '../outside.md'}, {'review': 'missing.md'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.bind(**change)

    def test_native_configuration_cannot_be_substituted(self):
        declaration = {'kind': 'native', 'project': 'tests/Example.csproj', 'arguments': [], 'configuration': 'Release'}
        with self.assertRaisesRegex(ValueError, 'configuration differs'):
            self.bind(checks=[declaration])

    def test_crossed_incomplete_duties_do_not_combine_into_complete_tasks(self):
        first = self.bind(rules=['owned'])
        other = copy.deepcopy(self.value)
        other['scope']['taskIds'] = ['T002']
        second = coding.bind_evaluation(self.root, self.feature, other, [self.claim(rules=['semantic'])])
        whole = copy.deepcopy(self.value)
        whole['scope']['taskIds'] = ['T001', 'T002']
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, whole, first + second)
        # Heterogeneous applicability is valid; unrelated duties are not imposed.
        whole['evaluation']['duties'][0]['taskIds'] = ['T001']
        whole['evaluation']['duties'][1]['taskIds'] = ['T002']
        coding.require_evaluated(self.root, self.feature, whole, first + second)

    def test_generic_duplicate_outside_and_malformed_inspections_reject(self):
        (self.root / 'private.txt').write_text('Unrelated source must not be read as task evidence.')
        for change in ({'inspections': []}, {'inspections': [self.claim()['inspections'][0]] * 2},
                       {'inspections': [{**row, 'sources': [{'path': 'private.txt', 'start': 1, 'end': 1}]}
                                        for row in self.claim()['inspections']]},
                       {'inspections': [{**row, 'sources': [{'path': 'Owner.cs', 'start': True, 'end': 200}]}
                                        for row in self.claim()['inspections']]}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'PKC020'):
                self.bind(**change)
        # An actual scoped design/configuration source remains legitimate.
        (self.root / 'design.md').write_text('Accepted finite owner design.')
        self.value['inputs'].append(coding.source(self.root, self.root / 'design.md'))
        self.bind(inspections=[{**row, 'sources': [{'path': 'design.md', 'start': 1, 'end': 1}]}
                               for row in self.claim()['inspections']])

    def test_related_family_groups_are_useful_but_bulk_unrelated_groups_reject(self):
        inspections = [{**self.claim()['inspections'][0], 'rules': ['owned', 'semantic']}]
        with self.assertRaisesRegex(ValueError, 'unrelated canonical families'):
            self.bind(inspections=inspections)
        for duty in self.value['evaluation']['duties']:
            duty.update(reviewFamily='same-canonical-family', owner='actual owner')
        records = self.bind(inspections=inspections)
        coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_explicit_manual_task_source_is_current_but_affected_hint_is_not_ownership(self):
        (self.root / 'src').mkdir()
        (self.root / 'src/Record.txt').write_text('Existing manual owner result.')
        (self.root / 'src/Unrelated.txt').write_text('Unrelated source.')
        self.value['scope']['tasks'] = ['- [ ] T001 Repair existing src/Record.txt']
        self.value['affectedPaths'] = ['src/Unrelated.txt']
        inspections = [{**row, 'sources': [{'path': 'src/Record.txt', 'start': 1, 'end': 1}]}
                       for row in self.claim()['inspections']]
        records = self.bind(inspections=inspections)
        coding.require_evaluated(self.root, self.feature, self.value, records)
        with self.assertRaisesRegex(ValueError, 'outside the affected/evaluated'):
            self.bind(inspections=[{**row, 'sources': [{'path': 'src/Unrelated.txt', 'start': 1, 'end': 1}]} for row in inspections])
        (self.root / 'src/Record.txt').write_text('Changed manual owner result.')
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_independent_effect_coverage_accepts_self_authored_mechanical_evidence(self):
        self.value['evaluation']['duties'][1]['independentReviewRequired'] = True
        self_authorship = {'implementationAuthors': [' Writer '], 'reviewer': 'writer', 'kind': 'agent'}
        mechanical = self.bind(rules=['owned'], authorship=self_authorship)
        semantic_self = self.bind(rules=['semantic'], checks=[], authorship=self_authorship)
        coding.require_evaluated(self.root, self.feature, self.value, mechanical + semantic_self)
        with self.assertRaisesRegex(ValueError, 'PKC022'):
            coding.require_independent_review(self.value, mechanical + semantic_self)
        semantic_independent = self.bind(rules=['semantic'], checks=[])
        coding.require_evaluated(self.root, self.feature, self.value, mechanical + semantic_independent)
        coding.require_independent_review(self.value, mechanical + semantic_independent)
        unrelated = copy.deepcopy(semantic_self)
        unrelated[0]['taskIds'] = ['T999']
        coding.require_evaluated(self.root, self.feature, self.value, mechanical + semantic_independent + unrelated)
        coding.require_independent_review(self.value, mechanical + semantic_independent + unrelated)
        self.value['evaluation']['duties'][1]['fingerprint'] = 'new-canonical-policy'
        semantic_current_self = self.bind(rules=['semantic'], checks=[], authorship=self_authorship)
        coding.require_evaluated(self.root, self.feature, self.value, mechanical + semantic_current_self + semantic_independent)
        with self.assertRaisesRegex(ValueError, 'PKC022'):
            coding.require_independent_review(self.value, mechanical + semantic_current_self + semantic_independent)
        fresh_independent = self.bind(rules=['semantic'], checks=[])
        coding.require_evaluated(self.root, self.feature, self.value, mechanical + semantic_current_self + fresh_independent)
        coding.require_independent_review(self.value, mechanical + semantic_current_self + fresh_independent)


if __name__ == '__main__':
    unittest.main()

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
        (self.root / 'scripts').mkdir()
        self.config = {'schemaVersion': 1, 'toolkitChecks': [{'id': 'proof', 'script': 'check.py', 'arguments': [],
                       'inputs': ['check.py'], 'timeoutSeconds': 5}]}
        (self.root / 'config/program-kit/verification.json').parent.mkdir(parents=True, exist_ok=True)
        (self.root / 'config/program-kit/verification.json').write_text(json.dumps(self.config))
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

    def limits_context(self, identity='caption-length'):
        self.value['scope']['tasks'] = ['- [ ] T001 Maintain Owner.cs']
        self.value['evaluation']['duties'] = [{
            'rule': 'principle.operational-setting-lifecycle', 'fingerprint': 'per-limit-v1',
            'required': True, 'technicalRequired': True, 'owner': 'policy source reviewer'}]
        self.value['operationBrief'] = {'operations': [{
            'operation': 'caption', 'taskIds': ['T001'], 'decisions': [],
            'limits': {'inventory': [identity] if identity is not None else [], 'items': []}}]}

    def limit_claim(self, **change):
        rule = 'principle.operational-setting-lifecycle'
        return self.claim(rules=[rule], inspections=[{
            'rules': [rule], 'sources': [{'path': 'Owner.cs', 'start': 1, 'end': 1}],
            'boundary': 'Actual caption policy/configuration consumer boundary',
            'findings': ['Configured owner/source and actual source consumer reconciled by this fictional author.'],
            'assessment': 'Finite authored review, not universal semantic inference.',
            'limitReconciliation': [{'operation': 'caption', 'limit': 'caption-length',
                'disposition': 'compliant', 'assessment': 'Configured caption admission and consumer agree with the current policy decision.'}]}], **change)

    def test_limit_reconciliation_rejects_missing_foreign_duplicates_and_findings_at_bind_and_reuse(self):
        self.limits_context()
        claim = self.limit_claim()
        records = coding.bind_evaluation(self.root, self.feature, self.value, [claim])
        coding.require_evaluated(self.root, self.feature, self.value, records)
        entry = claim['inspections'][0]['limitReconciliation'][0]
        for bad in (None, [], [entry, entry], [{**entry, 'operation': 'foreign'}],
                    [{**entry, 'limit': 'new-invented-policy'}], [{**entry, 'disposition': 'finding'}],
                    [{**entry, 'assessment': 'TBD'}], [{**entry, 'assessment': 'compliant'}]):
            with self.subTest(reconciliation=bad):
                malformed = copy.deepcopy(claim)
                if bad is None:
                    malformed['inspections'][0].pop('limitReconciliation')
                else:
                    malformed['inspections'][0]['limitReconciliation'] = bad
                with self.assertRaisesRegex(ValueError, 'PKC020'):
                    coding.bind_evaluation(self.root, self.feature, self.value, [malformed])
                retained = copy.deepcopy(records)
                if bad is None:
                    retained[0]['inspections'][0].pop('limitReconciliation')
                else:
                    retained[0]['inspections'][0]['limitReconciliation'] = bad
                with self.assertRaisesRegex(ValueError, 'PKC020'):
                    coding.require_evaluated(self.root, self.feature, self.value, retained)
        malformed = copy.deepcopy(claim)
        malformed['inspections'][0]['sources'] = [{'unexpected': 'Owner.cs'}]
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.bind_evaluation(self.root, self.feature, self.value, [malformed])
        # Nested malformed JSON must retain actionable PKC020, never membership TypeError.
        for invalid_rules in (None, 3, 'principle.operational-setting-lifecycle', [], [{}], 'missing'):
            malformed = copy.deepcopy(claim)
            if invalid_rules == 'missing':
                malformed['inspections'][0].pop('rules')
            else:
                malformed['inspections'][0]['rules'] = invalid_rules
            if invalid_rules == [{}]:
                malformed['inspections'][0].pop('limitReconciliation')  # Reach existing set validation, not an unrelated extra-field rejection.
            with self.subTest(rules=invalid_rules), self.assertRaisesRegex(ValueError, 'PKC020'):
                coding.bind_evaluation(self.root, self.feature, self.value, [malformed])
            retained = copy.deepcopy(records)
            if invalid_rules == 'missing':
                retained[0]['inspections'][0].pop('rules')
            else:
                retained[0]['inspections'][0]['rules'] = invalid_rules
            with self.assertRaisesRegex(ValueError, 'PKC020'):
                coding.require_evaluated(self.root, self.feature, self.value, retained)
        # Discovering a previously omitted limit is an actual review finding, not numeric inference.
        self.value['operationBrief']['operations'][0]['limits']['inventory'].append('new-discovered-policy')
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)
        self.limits_context(None)
        no_limits = copy.deepcopy(claim)
        no_limits['inspections'][0]['limitReconciliation'][0].update(limit=None,
            assessment='This pure representation changes no behavioral/resource limit; existing exact identity invariant is retained.')
        record = coding.bind_evaluation(self.root, self.feature, self.value, [no_limits])
        coding.require_evaluated(self.root, self.feature, self.value, record)

    def test_non_source_work_with_exact_empty_targets_can_complete_without_fabricated_limits(self):
        self.limits_context()
        self.value['operationBrief']['operations'] = []
        self.value['scope']['tasks'] = ['- [ ] T001 Update README.md wording']
        (self.root / 'README.md').write_text('Fictional documentation-only wording; no implementation work.')
        claim = self.limit_claim()
        claim['inspections'][0]['sources'] = [{'path': 'README.md', 'start': 1, 'end': 1}]
        claim['inspections'][0]['limitReconciliation'] = []
        records = coding.bind_evaluation(self.root, self.feature, self.value, [claim])
        coding.require_evaluated(self.root, self.feature, self.value, records)
        self.limits_context()
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.bind_evaluation(self.root, self.feature, self.value, [claim])

    def test_cited_limit_policy_changes_stale_only_affected_review(self):
        authority = self.root / 'accepted-policy.md'
        authority.write_text('# Caption policy\nConfigured maximum defaults to 48 code points.\n')
        self.limits_context()
        operation = self.value['operationBrief']['operations'][0]
        operation['limits']['items'] = [{'id': 'caption-length', 'source': coding.source(self.root, authority)}]
        unrelated = self.root / 'other-policy.md'
        unrelated.write_text('Unrelated operation policy; not selected by this operation brief.')
        records = coding.bind_evaluation(self.root, self.feature, self.value, [self.limit_claim()])
        coding.require_evaluated(self.root, self.feature, self.value, records)
        self.assertIn('source:accepted-policy.md', records[0]['basis'])
        self.assertNotIn('source:other-policy.md', records[0]['basis'])
        unrelated.write_text('Unrelated revised policy does not stale this selected operation.')
        coding.require_evaluated(self.root, self.feature, self.value, records)
        authority.write_text('# Caption policy\nConfigured maximum defaults to 60 code points.\n')
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_named_limit_policy_only_review_cannot_establish_actual_implementation(self):
        self.limits_context()
        authority = self.root / 'accepted-policy.md'
        authority.write_text('Fictional accepted caption policy, independent from implementation.')
        self.value['operationBrief']['operations'][0]['limits']['items'] = [
            {'id': 'caption-length', 'source': coding.source(self.root, authority)}]
        claim = self.limit_claim()
        # Configuration-only work can explicitly inspect an unchanged existing consumer.
        (self.root / 'settings.json').write_text('{"maximum": 48}')
        self.value['scope']['tasks'] = ['- [ ] T001 Update settings.json; inspect existing Owner.cs consumer without editing it']
        records = coding.bind_evaluation(self.root, self.feature, self.value, [claim])
        coding.require_evaluated(self.root, self.feature, self.value, records)
        foreign = self.root / 'unrelated.py'
        foreign.write_text('UNRELATED = 48\n')
        self.value['operationBrief']['operations'][0]['limits']['items'].append(
            {'id': 'caption-length', 'source': coding.source(self.root, foreign)})
        outside = copy.deepcopy(claim)
        outside['inspections'][0]['sources'] = [{'path': 'unrelated.py', 'start': 1, 'end': 1}]
        with self.assertRaisesRegex(ValueError, 'actual owned implementation'):
            coding.bind_evaluation(self.root, self.feature, self.value, [outside])
        self.value['operationBrief']['operations'][0]['limits']['items'].pop()
        claim['inspections'][0]['sources'] = [{'path': 'accepted-policy.md', 'start': 1, 'end': 1}]
        with self.assertRaisesRegex(ValueError, 'actual owned implementation'):
            coding.bind_evaluation(self.root, self.feature, self.value, [claim])
        records[0]['inspections'][0]['sources'] = [{**claim['inspections'][0]['sources'][0],
            'sha256': coding.source(self.root, authority)['sha256']}]
        with self.assertRaisesRegex(ValueError, 'PKC020'):
            coding.require_evaluated(self.root, self.feature, self.value, records)

    def test_actual_configured_limit_behavior_rejects_hardcoded_bypass_without_changing_identity_invariant(self):
        # Fictional portable application, actual maintained process/activation/default/consumer checks.
        pure_source = ('def admit(value, maximum):\n'
            '    if len(value) > maximum: raise ValueError("caption-too-long")\n'
            '    return value\n'
            'def cite(original, quote):\n'
            '    if quote != original: raise ValueError("exact-quote-invariant")\n'
            '    return quote\n')
        application_source = ('from typing import NamedTuple\nfrom caption import admit\n'
            'class Policy(NamedTuple): maximum: int\n'
            'def activate(settings):\n'
            '    maximum = settings.get("maximum", 48)\n'
            '    if type(maximum) is not int or not 1 <= maximum <= 64: raise ValueError("invalid-policy")\n'
            '    return Policy(maximum)\n'
            'def admit_request(value, policy): return admit(value, policy.maximum)\n'
            'def execute(value, policy): return admit(value, policy.maximum)\n')
        (self.root / 'caption.py').write_text(pure_source)
        (self.root / 'application.py').write_text(application_source)
        (self.root / 'settings.json').write_text('{"maximum": 3}')
        (self.root / 'accepted-policy.md').write_text('Fictional accepted caption policy: configurable default 48 Unicode code points; nondefault overrides validated at activation; fixed wire ceiling 64. Pure Core receives admitted values. Both request admission and execution consume one immutable snapshot. This is test authoring, not real human approval.')
        (self.root / 'check.py').write_text('import json\nfrom caption import cite\nfrom application import activate, admit_request, execute\n'
            'policy = activate(json.load(open("settings.json")))\n'
            'assert policy.maximum == 3\n'
            'for consume, marker in ((admit_request, "configured-limit-bypass"), (execute, "execution-policy-bypass")):\n'
            '    assert consume("abc", policy) == "abc"\n'
            '    try: consume("abcd", policy)\n'
            '    except ValueError as error: assert str(error) == "caption-too-long"\n'
            '    else: raise AssertionError(marker)\n'
            'default = activate({})\n'
            'assert default.maximum == 48\n'
            'assert admit_request("x" * 48, default) == "x" * 48\n'
            'try: admit_request("x" * 49, default)\n'
            'except ValueError as error: assert str(error) == "caption-too-long"\n'
            'else: raise AssertionError("omitted-default-bypass")\n'
            'for invalid in (0, -1, True, 65):\n'
            '    try: activate({"maximum": invalid})\n'
            '    except ValueError as error: assert str(error) == "invalid-policy"\n'
            '    else: raise AssertionError("invalid-setting-activated")\n'
            'assert cite("exact", "exact") == "exact"\n'
            'try: cite("exact", "changed")\n'
            'except ValueError as error: assert str(error) == "exact-quote-invariant"\n'
            'else: raise AssertionError("identity-invariant-bypass")\n'
            'print("configured-boundary-invalid-default-consumers-and-fixed-invariant-passed")\n')
        self.config['toolkitChecks'][0]['inputs'] = ['check.py', 'caption.py', 'application.py', 'settings.json']
        (self.root / 'config/program-kit/verification.json').parent.mkdir(parents=True, exist_ok=True)
        (self.root / 'config/program-kit/verification.json').write_text(json.dumps(self.config))
        self.rows = toolkit.declarations(self.root, self.config)
        self.execute()  # A successful process precedes each intended behavioral negative.
        self.limits_context()
        self.value['scope']['tasks'] = ['- [ ] T001 Maintain caption.py, application.py and settings.json']
        self.value['operationBrief']['operations'][0]['limits']['inventory'].append('wire-caption-ceiling')
        self.value['operationBrief']['operations'][0]['limits']['items'] = [
            {'id': identity, 'classification': classification, 'source': coding.source(self.root, self.root / 'accepted-policy.md')}
            for identity, classification in [('caption-length', 'configurable-policy'), ('wire-caption-ceiling', 'fixed-contract')]]
        claim = self.limit_claim()
        claim['inspections'][0]['sources'] = [{'path': name, 'start': 1, 'end': len((self.root / name).read_text().splitlines())}
                                             for name in ('caption.py', 'application.py', 'settings.json')]
        claim['inspections'][0]['limitReconciliation'].append({
            'operation': 'caption', 'limit': 'wire-caption-ceiling', 'disposition': 'compliant',
            'assessment': 'Fictional fixed wire ceiling 64 from accepted policy bounds validated configuration; it remains separate from configurable default48 and override3.'})
        claim['inspections'][0]['assessment'] = 'Fictional reviewer inspects actual activation/default/settings and both pure-policy consumers; the real check process exercises each finite boundary.'
        records = coding.bind_evaluation(self.root, self.feature, self.value, [claim])
        coding.require_evaluated(self.root, self.feature, self.value, records)
        for name, mutated, marker in (
                ('caption.py', pure_source.replace('len(value) > maximum', 'len(value) > 48'), 'configured-limit-bypass'),
                ('application.py', application_source.replace('def execute(value, policy): return admit(value, policy.maximum)',
                    'def execute(value, policy): return admit(value, 48)'), 'execution-policy-bypass')):
            (self.root / name).write_text(mutated)
            with self.assertRaises(ValueError):
                self.execute()
            logs = [path.read_text(encoding='utf-8') for path in (self.root / 'artifacts').rglob('*') if path.is_file() and path.suffix in ('.log', '.txt')]
            self.assertTrue(any(marker in text for text in logs), 'The intended behavioral oracle must fail, not setup/import.')
            with self.assertRaisesRegex(ValueError, 'PKC020'):
                coding.require_evaluated(self.root, self.feature, self.value, records)
            with self.assertRaises(ValueError):
                coding.bind_evaluation(self.root, self.feature, self.value, [claim])
            (self.root / 'caption.py').write_text(pure_source)
            (self.root / 'application.py').write_text(application_source)
            self.execute()
            repaired = coding.bind_evaluation(self.root, self.feature, self.value, [claim])
            coding.require_evaluated(self.root, self.feature, self.value, repaired)

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

"""F3 independent admission, evidence invalidation and canonical producer tests."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import coding_patterns as patterns
from coding_context import compose, validate_units
from phase_obligations import catalog, canonical_rules, render
from pattern_review_fixture import declaration, ref
from owned_fixture import FixtureDirectory


class PatternTests(unittest.TestCase):
    def setUp(self):
        self.catalog = copy.deepcopy(catalog())
        self.catalog['codingUnits'] = [declaration('one', 'principle.compilation-boundaries')]
        self.observed = patterns.context(['dotnet'], [{'status': 'evaluated', 'properties': {'TargetFramework': 'net10.0'}, 'packages': [{'id': 'Npgsql', 'version': '10.0.0'}]}])

    def test_unknown_executable_and_version_fields_cannot_be_silent_extensions(self):
        for change in ({'run': 'private-secret-command'}, {'schemaVersion': 2}, {'schemaVersion': True},
                       {'version': 'latest'}, {'owner': ''}, {'review': {'root': 'outside', 'path': 'secret'}},
                       {'checks': [{'kind': 'shell', 'command': 'anything'}]}, {'evidence': [None]}):
            data = copy.deepcopy(self.catalog)
            data['codingUnits'][0]['pattern'].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'PKP001') as error:
                patterns.validate(data)
            self.assertNotIn('private-secret', str(error.exception))

    def test_local_input_cannot_shadow_rules_or_escape_through_sources(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            path = root / patterns.LOCAL
            path.parent.mkdir(parents=True)
            value = {'schemaVersion': 1, 'sources': [], 'rules': {'principle.compilation-boundaries': {}}, 'codingUnits': []}
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'shadow'):
                patterns.merge(self.catalog, root)
            value['rules'] = {}
            value['sources'] = [{'id': 'local.escape', 'locator': {'kind': 'repository', 'path': '../outside.md'}}]
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                patterns.merge(self.catalog, root)
            path.write_text('{"schemaVersion":1,"schemaVersion":1}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                patterns.merge(self.catalog, root)

    def test_replacement_cannot_erase_invariants_or_mandatory_rules(self):
        base = self.catalog['codingUnits'][0]
        local = declaration('two', 'guidance.component-adoption.foundation-web-and-json', replaces=['one'])
        self.catalog['codingUnits'].append(local)
        patterns.validate(self.catalog)
        local['pattern']['invariantRuleIds'] = []
        with self.assertRaisesRegex(ValueError, 'invariant'):
            patterns.validate(self.catalog)
        local['pattern']['invariantRuleIds'] = ['principle.compilation-boundaries']
        base['ruleIds'].append('principle.authorization-ownership')
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            patterns.validate(self.catalog)
        local['pattern']['invariantRuleIds'].append('principle.authorization-ownership')
        patterns.validate(self.catalog)
        local['pattern']['replaces'] = ['story-delivery']
        with self.assertRaisesRegex(ValueError, 'owner'):
            patterns.validate(self.catalog)

    def test_compatibility_uses_observed_profiles_frameworks_and_exact_package(self):
        unit = self.catalog['codingUnits'][0]
        self.assertFalse(patterns.compatibility(unit['pattern'], self.observed))
        for key, change in [('profiles', []), ('frameworks', ['net9.0']), ('packages', [('Npgsql', '11.0.0')])]:
            observed = {**self.observed, key: change}
            self.assertTrue(patterns.compatibility(unit['pattern'], observed))

    def test_qualification_is_separate_from_ambiguity_and_no_fallback(self):
        units, excluded, _ = compose(self.catalog, [], {'persistence'}, {'request': True, 'contract-owner': True}, ROOT / 'extensions')
        qualified = {'status': 'qualified', 'fingerprint': 'x'}
        with patch.object(patterns, 'qualify', return_value=qualified):
            selected, reports, blockers = patterns.apply(self.catalog, units, excluded, ROOT, ROOT / 'extensions', self.observed, {})
            self.assertEqual(['one'], [u['id'] for u in selected])
            self.assertFalse(blockers)
        self.catalog['codingUnits'].append(declaration('two', 'principle.compilation-boundaries', replaces=['one']))
        units, excluded, _ = compose(self.catalog, [], {'persistence'}, {'request': True, 'contract-owner': True}, ROOT / 'extensions')
        with patch.object(patterns, 'qualify', side_effect=[qualified, {'status': 'missing-proof', 'repair': 'normal proof needed'}]):
            selected, reports, blockers = patterns.apply(self.catalog, units, excluded, ROOT, ROOT / 'extensions', self.observed,
                {'notes-owner-query': {'id': 'two', 'version': '1.0.0', 'reason': 'local context'}})
            self.assertFalse(selected)
            self.assertTrue(any(b['code'] == 'PKP005' for b in blockers))
            self.assertFalse(any(r['selected'] for r in reports))

    def test_native_evidence_uses_current_plan_not_just_a_completed_result(self):
        from dotnet_adapter import bootstrap
        bootstrap()
        import repository_verification as native
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'Tests.csproj').write_text('<Project/>')
            run = root / 'artifacts/tests/runs/one/result.json'
            run.parent.mkdir(parents=True)
            run.write_text('{"status":"completed"}')
            check = {'kind': 'native', 'project': 'Tests.csproj', 'arguments': [], 'configuration': 'Release'}
            with patch.object(native, 'plan', return_value={'reusable': [{'run': run.relative_to(root).as_posix()}], 'needed': []}) as planned:
                proof = patterns.current_check(root, check)
                self.assertEqual('Release', planned.call_args.args[3])
                self.assertEqual(patterns.sha(run.read_bytes()), proof['sha256'])
            with patch.object(native, 'plan', return_value={'reusable': [], 'needed': [{'reason': 'stale native inputs'}]}):
                with self.assertRaisesRegex(ValueError, 'stale'):
                    patterns.current_check(root, check)

    def test_bindings_invalidate_rules_source_context_and_preserve_unrelated_text(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            for name in ('code.py', 'bad.py', 'review.md'):
                (root / name).write_text('bounded proof\n')
            unit = self.catalog['codingUnits'][0]
            p = unit['pattern']
            p['inputs'], p['examples'], p['review'] = [ref('code.py')], {'positive': [ref('code.py')], 'negative': [ref('bad.py')]}, ref('review.md')
            rules = [{'id': 'canonical', 'fingerprint': 'original'}]
            before = patterns.binding(unit, rules, root, ROOT / 'extensions', self.observed)
            (root / 'unrelated.md').write_text('unrelated private note')
            self.assertEqual(before, patterns.binding(unit, rules, root, ROOT / 'extensions', self.observed))
            for name in ('code.py', 'bad.py', 'review.md'):
                original = (root / name).read_bytes()
                (root / name).write_text('changed')
                self.assertNotEqual(before, patterns.binding(unit, rules, root, ROOT / 'extensions', self.observed))
                (root / name).write_bytes(original)
            self.assertNotEqual(before, patterns.binding(unit, [{'id': 'canonical', 'fingerprint': 'changed'}], root, ROOT / 'extensions', self.observed))
            self.assertNotEqual(before, patterns.binding(unit, rules, root, ROOT / 'extensions', {**self.observed, 'configuration': 'Release'}))

    def test_unbound_or_expired_evidence_is_not_a_pass(self):
        unit = self.catalog['codingUnits'][0]
        proof = {'check': unit['pattern']['checks'][0], 'run': 'artifacts/tests/toolkit-runs/one/result.json', 'sha256': 'a' * 64}
        unit['pattern']['evidence'] = [{'fingerprint': 'f' * 64, 'checks': [proof], 'boundAtUtc': '2026-01-01T00:00:00Z', 'expiresAt': '2020-01-01T00:00:00Z'}]
        with patch.object(patterns, 'binding', return_value='f' * 64), patch.object(patterns, 'current_check', return_value=proof):
            self.assertEqual('stale-or-unbound', patterns.qualify(unit, [], ROOT, ROOT / 'extensions', self.observed)['status'])
            del unit['pattern']['evidence'][0]['expiresAt']
            self.assertEqual('qualified', patterns.qualify(unit, [], ROOT, ROOT / 'extensions', self.observed)['status'])

    def test_real_named_check_rejects_changed_logs_source_and_later_failure(self):
        from dotnet_adapter import bootstrap
        bootstrap()
        import toolkit_verification as toolkit
        with FixtureDirectory(native=True) as directory:
            root = Path(directory)
            script = root / 'check.py'
            script.write_text('print("actual bounded check")\n')
            (root / 'eng').mkdir()
            config = {'schemaVersion': 1, 'toolkitChecks': [{'id': 'pattern-proof', 'script': 'check.py', 'arguments': [], 'inputs': ['check.py'], 'timeoutSeconds': 10}]}
            (root / 'eng/verification.json').write_text(json.dumps(config))
            row = toolkit.declarations(root, config)
            proof = toolkit.execute(root, ['pattern-proof'], row)
            check = {'kind': 'toolkit', 'id': 'pattern-proof'}
            self.assertEqual(proof['run'], patterns.current_check(root, check)['run'])
            toolkit.execute(root, ['pattern-proof'], row)
            self.assertEqual(proof['run'], patterns.current_check(root, check, proof['run'])['run'], 'An identical successful rerun must preserve valid earlier evidence')
            log = root / next(iter(proof['result']['outcomes'][0]['evidence']))
            original = log.read_bytes()
            log.write_text('tampered')
            with self.assertRaises(ValueError):
                patterns.current_check(root, check, proof['run'])
            log.write_bytes(original)
            script.write_text('raise SystemExit(2)\n')
            with self.assertRaises(ValueError):
                patterns.current_check(root, check)
            with self.assertRaises(ValueError):
                toolkit.execute(root, ['pattern-proof'], row)
            script.write_text('print("actual bounded check")\n')
            with self.assertRaisesRegex(ValueError, 'unresolved'):
                patterns.current_check(root, check)

    def test_malformed_private_rule_source_becomes_a_bounded_finding(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'private.py').write_text('def private():\n    PRIVATE_CANARY no valid syntax\n')
            data = copy.deepcopy(self.catalog)
            data['sources'].append({'id': 'local.invalid', 'locator': {'kind': 'repository', 'path': 'private.py'}})
            data['rules']['local.invalid'] = {'source': 'local.invalid', 'selector': {'kind': 'python-symbol', 'name': 'private'}, 'owner': 'consumer', 'level': 'recommended'}
            data['codingUnits'] = [{'id': 'local-invalid', 'ruleIds': ['local.invalid'], 'route': 'manual-edit'}]
            _, _, blockers = compose(data, [], set(), {}, ROOT / 'extensions', repository=root)
            self.assertEqual('PKC019', blockers[0]['code'])
            self.assertNotIn('PRIVATE_CANARY', json.dumps(blockers))

    def test_adapter_policy_resolves_from_canonical_source_and_native_stays_independent(self):
        from dotnet_adapter import bootstrap
        bootstrap()
        import source_quality
        with FixtureDirectory() as directory:
            root = Path(directory)
            self.assertFalse(source_quality.guidance(root)['guidance'])
            self.assertEqual(['principle.source-file-context'], source_quality.guidance(root)['canonicalRuleIds'])
            source = ROOT / 'extensions/program-kit-governance/references/phase-evidence.md'
            original = source.read_text()
            # Mutate only the resolver's read in memory, preserving the actual checkout.
            read = Path.read_bytes
            def changed(path):
                value = read(path)
                return value.replace(b'Make design decisions', b'Changed canonical decisions') if path == source else value
            before = canonical_rules(['phase-action.planning'])[0]
            with patch.object(Path, 'read_bytes', changed):
                after = canonical_rules(['phase-action.planning'])[0]
            self.assertNotEqual(before['fingerprint'], after['fingerprint'])
            self.assertIn('Changed canonical decisions', after['text'])
            self.assertEqual(original, source.read_text())

    def test_installed_review_fixture(self):
        from pattern_review_fixture import scenario
        with FixtureDirectory(native=True) as directory:
            result = scenario(directory)
            self.assertEqual('passed', result['status'])
            self.assertTrue(result['workingInputsUnchanged'])
            if result.get('sourceCompletion') == 'blocked-publication-dependency':
                self.assertTrue(any(b['code'] == 'PKC024' for b in result['sourceBlockers']))
                self.assertTrue(any(c['name'] == '04-independent-invalid-implementation' and c['actualExit'] == 2 for c in result['commands']))
                self.assertTrue(any(c['name'] == '04c-independent-browser-remains-available' and c['actualExit'] == 0 for c in result['commands']))
            else:
                self.assertTrue(any(c['name'] == '23-restored-qualified-context' and c['actualExit'] == 0 for c in result['commands']))


if __name__ == '__main__':
    unittest.main()

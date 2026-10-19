"""Independent teaching/promotion boundary regressions; execution lives in F6 fixture."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import coding_patterns as patterns
from coding_context import validate_units
from feature_context import responsibility_tags
from phase_obligations import catalog
from owned_fixture import FixtureDirectory
from learning_review_fixture import declaration, ref


class TeachingTests(unittest.TestCase):
    def test_actual_owned_csharp_preserves_invocation_readability(self):
        from csharp_readability_check import check
        paths = list((ROOT / 'extensions/program-kit-dotnet/references/examples/snapshot-query').glob('*.cs'))
        self.assertEqual(0, check(paths))

    def test_known_gap_prepares_one_draft_without_running_or_registering(self):
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            request = {'schemaVersion': 1, 'id': 'new-lesson', 'intent': 'new', 'problem': 'An explicit known gap, without supplied implementation.',
                       'changes': {k: [] for k in ('guidance', 'scaffolds', 'checks', 'examples', 'acceptedArtifacts')}}
            (root / 'request.json').write_text(json.dumps(request))
            with patch.object(patterns.subprocess, 'run', side_effect=AssertionError('submission execution forbidden')):
                value = patterns.teach(root, 'request.json', catalog())
            self.assertFalse(value['executionAuthorized'])
            self.assertFalse((root / patterns.LOCAL).exists())
            self.assertEqual('draft', value['proposal']['codingUnits'][0]['pattern']['status'])
            self.assertTrue(value['missingProof'])

    def test_prior_version_and_retirement_identity_are_exact(self):
        registry = copy.deepcopy(catalog())
        unit = declaration('prior')
        registry['codingUnits'].append(unit)
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            request = {'schemaVersion': 1, 'id': 'next', 'intent': 'refine', 'problem': 'Explicit refinement',
                       'basedOn': {'id': 'prior', 'version': '9.9.9'},
                       'changes': {k: [] for k in ('guidance', 'scaffolds', 'checks', 'examples', 'acceptedArtifacts')}}
            for intent, identity, version in [('refine', 'next', '9.9.9'), ('refine', 'prior', '1.0.0'), ('retire', 'next', '1.0.0')]:
                request.update(intent=intent, id=identity, basedOn={'id': 'prior', 'version': version})
                (root / 'request.json').write_text(json.dumps(request))
                with self.subTest(intent=intent, identity=identity), self.assertRaises(ValueError):
                    patterns.teach(root, 'request.json', registry)
            self.assertEqual('active', unit['pattern']['status'])
            self.assertEqual('1.0.0', unit['pattern']['version'])
            unit['pattern']['evidence'] = [{'fingerprint': 'a' * 64, 'checks': [], 'boundAtUtc': '2026-10-18T00:00:00Z'}]
            request.update(intent='retire', id='prior', basedOn={'id': 'prior', 'version': '1.0.0'})
            (root / 'request.json').write_text(json.dumps(request))
            proposed = patterns.teach(root, 'request.json', registry)['proposal']['codingUnits'][0]
            self.assertEqual(unit['pattern']['evidence'], proposed['pattern']['evidence'])
            self.assertEqual('retired', proposed['pattern']['status'])

    def test_unknown_applicability_is_a_missing_adapter_not_silent_exclusion(self):
        registry = copy.deepcopy(catalog())
        unit = copy.deepcopy(registry['codingUnits'][0])
        registry['codingUnits'] = [unit]
        unit['when'] = {'all': ['unknown-language']}
        with self.assertRaisesRegex(ValueError, 'unknown applicability adapter'):
            validate_units(registry)
        self.assertIn('snapshot-query', responsibility_tags())

    def test_selected_stale_pattern_preserves_missing_source_owner_diagnostic(self):
        registry = copy.deepcopy(catalog())
        unit = declaration('selected')
        unit['ruleIds'] = ['principle.compilation-boundaries']
        registry['codingUnits'] = [unit]
        missing_source = {'code': 'PKC019', 'owner': 'canonical source owner', 'repair': 'Restore source.'}
        selected = [{**unit, 'rules': [], 'blockers': [missing_source]}]
        choice = {'snapshot-owner-query': {'id': 'selected', 'version': '1.0.0', 'reason': 'Explicit reviewed scope'}}
        with patch.object(patterns, 'qualify', return_value={'status': 'missing-proof', 'repair': 'Rerun proof.'}):
            units, reports, blockers = patterns.apply(registry, selected, [], ROOT, ROOT / 'extensions', {'profiles': ['dotnet'], 'frameworks': ['net10.0'], 'packages': []}, choice)
        self.assertFalse(units)
        self.assertIn(missing_source, blockers)
        self.assertTrue(any(b['code'] == 'PKP005' for b in blockers))

    def test_changed_detector_and_runtime_are_qualification_inputs(self):
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            for name in ('code', 'invalid', 'review'):
                (root / name).write_text('Independent bounded content')
            unit = declaration('one')
            unit['pattern'].update(inputs=[ref('code')], examples={'positive': [ref('code')], 'negative': [ref('invalid')]}, review=ref('review'))
            observed = {'runtimeInventory': ['runtime-one']}
            before = patterns.binding(unit, [], root, ROOT / 'extensions', observed)
            self.assertNotEqual(before, patterns.binding(unit, [], root, ROOT / 'extensions', {'runtimeInventory': ['runtime-two']}))
            read_bytes = Path.read_bytes
            def mutated(path):
                value = read_bytes(path)
                return value + b'\n# changed detector' if path.name == 'feature_context.py' else value
            with patch.object(Path, 'read_bytes', mutated):
                self.assertNotEqual(before, patterns.binding(unit, [], root, ROOT / 'extensions', observed))

    def test_promotion_requires_selected_dependencies_and_cannot_transfer_evidence(self):
        with FixtureDirectory(native=True) as folder:
            root = Path(folder)
            (root / 'lesson.md').write_text('Explicit publishable lesson')
            (root / 'private.md').write_text('UNSELECTED_PRIVATE_CANARY')
            unit = declaration('shared-example')
            unit['ruleIds'] = ['new.shared-rule']
            unit['pattern'].update(status='draft', inputs=[ref('new/lesson.md', 'extensions')],
                examples={'positive': [ref('new/lesson.md', 'extensions')], 'negative': [ref('new/lesson.md', 'extensions')]},
                review=ref('new/lesson.md', 'extensions'), evidence=[])
            additions = {'schemaVersion': 1, 'sources': [{'id': 'new.shared-source', 'locator': {'kind': 'extension', 'path': 'new/lesson.md'}}],
                         'rules': {'new.shared-rule': {'source': 'new.shared-source', 'selector': {'kind': 'document'}, 'owner': 'fixture', 'level': 'recommended', 'limits': 'No proof.'}},
                         'codingUnits': [unit]}
            selection = {'schemaVersion': 1, 'declaration': 'additions.json', 'files': [{'source': 'lesson.md', 'target': 'extensions/new/lesson.md'}]}
            def save():
                (root / 'additions.json').write_text(json.dumps(additions))
                (root / 'selection.json').write_text(json.dumps(selection))
            save()
            output = root / 'contribution'
            patterns.prepare_shared(root, 'selection.json', output, catalog())
            contents = b''.join(p.read_bytes() for p in output.rglob('*') if p.is_file())
            self.assertNotIn(b'UNSELECTED_PRIVATE_CANARY', contents)
            with self.assertRaisesRegex(ValueError, 'output exists'):
                patterns.prepare_shared(root, 'selection.json', output, catalog())
            for mutate in ('evidence', 'missing-input', 'escape', 'history'):
                with self.subTest(mutate=mutate):
                    original_additions, original_selection = copy.deepcopy(additions), copy.deepcopy(selection)
                    if mutate == 'evidence':
                        additions['codingUnits'][0]['pattern']['evidence'] = [{'fingerprint': '0' * 64}]
                    elif mutate == 'missing-input':
                        additions['codingUnits'][0]['pattern']['inputs'] = [ref('private.md')]
                    elif mutate == 'escape':
                        selection['files'][0]['target'] = 'extensions/../../escape'
                    else:
                        (root / 'artifacts').mkdir(exist_ok=True)
                        (root / 'artifacts/raw.log').write_text('PRIVATE_HISTORY')
                        selection['files'][0]['source'] = 'artifacts/raw.log'
                    save()
                    with self.assertRaises(ValueError):
                        patterns.prepare_shared(root, 'selection.json', root / ('invalid-' + mutate), catalog())
                    self.assertFalse((root / ('invalid-' + mutate)).exists())
                    additions, selection = original_additions, original_selection


if __name__ == '__main__':
    unittest.main()

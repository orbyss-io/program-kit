"""Consumer quality authority and batched authoring diagnostics; no agents."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
import bootstrap_quality as quality
import bootstrap_context as context


class QualityHandoffTests(unittest.TestCase):
    def test_source_bundle_is_complete_compact_and_aggregate_bounded(self):
        from bounded_read import read_bundle, read_page, PAGE_BYTES
        value = {'data': [{'name': 'é漢🙂', 'count': n} for n in range(800)]}
        raw = json.dumps(value, ensure_ascii=False, indent=4)
        (self.root / 'data.json').write_text(raw, encoding='utf-8')
        (self.root / 'rules.md').write_text('Required rule.\n' * 300, encoding='utf-8')
        first = read_bundle(self.root, ['data.json', 'rules.md', 'data.json'])
        pages = [read_bundle(self.root, ['data.json', 'rules.md', 'data.json'], n)
                 for n in range(1, first['pages'] + 1)]
        content = ''.join(p['text'] for p in pages)
        compact = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        self.assertIn(compact, content)
        self.assertIn((self.root / 'rules.md').read_bytes().decode('utf-8'), content)
        self.assertEqual(1, content.count('SOURCE data.json'))
        self.assertTrue(all(len(p['text'].encode('utf-8')) <= PAGE_BYTES for p in pages))
        self.assertLess(len(content.encode('utf-8')), len(raw.encode('utf-8')))
        self.assertEqual(['data'], json.loads(read_page(self.root, 'data.json', keys=True)['text'])['keys'])
        with self.assertRaisesRegex(ValueError, 'available keys: data'):
            read_page(self.root, 'data.json', pointer='/assurance_levels')
        with self.assertRaisesRegex(ValueError, 'Omit --pointer for the root'):
            read_page(self.root, 'data.json', pointer='/')

    def test_required_source_reader_excludes_optional_evidence(self):
        path = context.context_path(context.safe_run_directory(self.root, 'trial'), 'closure')
        path.parent.mkdir(parents=True)
        (self.root / 'required.md').write_text('Required fact', encoding='utf-8')
        (self.root / 'optional.md').write_text('Optional unrelated fact', encoding='utf-8')
        path.write_text(json.dumps({'reading_policy': {'required_full_reads': ['required.md'],
            'allowed_sources': ['optional.md']}}), encoding='utf-8')
        result = context.read_sources(self.root, 'trial', 'closure', 1)
        self.assertIn('Required fact', result['text'])
        self.assertNotIn('Optional unrelated fact', result['text'])
        with self.assertRaisesRegex(context.ContextError, 'Page must be between'):
            context.read_sources(self.root, 'trial', 'closure', 2)

    def test_canonical_binding_status_distinguishes_acceptance_from_design_change(self):
        from bootstrap_lifecycle import source_binding_status, source_digest, LEDGER
        docs = self.root / 'docs/architecture'
        adr = docs / 'decision.md'
        adr.write_text('- **Status**: Proposed\n\nKeep consumer semantics.\n', encoding='utf-8')
        (docs / 'bootstrap-decisions.json').write_text('{}', encoding='utf-8')
        (docs / 'architecture-map.json').write_text(json.dumps({'decisions': [{'path': 'docs/architecture/decision.md'}]}), encoding='utf-8')
        (self.root / LEDGER).write_text(json.dumps({'sources': [{'path': 'docs/architecture/decision.md',
            'sha256': source_digest(adr)}]}), encoding='utf-8')
        adr.write_text(adr.read_text(encoding='utf-8').replace('Proposed', 'Accepted'), encoding='utf-8')
        self.assertEqual('matched', source_binding_status(self.root)['sources'][-1]['status'])
        adr.write_text(adr.read_text(encoding='utf-8') + 'Changed condition.\n', encoding='utf-8')
        self.assertEqual('changed', source_binding_status(self.root)['sources'][-1]['status'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pk-quality-handoff-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / quality.SOURCE).parent.mkdir(parents=True)
        (self.root / quality.SOURCE).write_text('# Scenarios\n\n- WEB-Q04 (WEB-C12): Private export contains no records.\n'
                                              '  Verify actual exported contents.\n- WEB-Q05 (WEB-C06): Device accessibility.\n', encoding='utf-8')
        (self.root / quality.TARGET).write_text('# Gates\n\nUse WEB-Q04 and WEB-Q05 at delivery.\n', encoding='utf-8')

    def test_exact_generated_mapping_preserves_every_case_and_user_prose(self):
        self.assertEqual(['WEB-Q04', 'WEB-Q05'], quality.synchronize(self.root))
        quality.validate(self.root)
        original = (self.root / quality.TARGET).read_bytes()
        quality.synchronize(self.root)
        self.assertEqual(original, (self.root / quality.TARGET).read_bytes())
        self.assertIn('Use WEB-Q04 and WEB-Q05 at delivery.', original.decode())

    def test_conflicting_or_duplicate_authored_case_is_not_silently_overwritten(self):
        path = self.root / quality.TARGET
        path.write_text('- WEB-Q04: readiness, locale and unrelated assertions\n', encoding='utf-8')
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'definitions belong only'):
            quality.synchronize(self.root)
        self.assertEqual(before, path.read_bytes())

    def test_changed_missing_and_stale_case_views_are_detected(self):
        with self.assertRaisesRegex(ValueError, 'Missing generated'):
            quality.validate(self.root)
        quality.synchronize(self.root)
        target = self.root / quality.TARGET
        target.write_text(target.read_text().replace('Device accessibility.', 'Different case.'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stale'):
            quality.validate(self.root)
        quality.synchronize(self.root)
        quality.validate(self.root)
        source = self.root / quality.SOURCE
        source.write_text('- WEB-Q04: Changed agreed scenario.\n', encoding='utf-8')
        quality.synchronize(self.root)
        quality.validate(self.root)
        self.assertNotIn('- WEB-Q05', target.read_text())

    def test_duplicate_source_ids_are_reported_before_projection(self):
        source = self.root / quality.SOURCE
        source.write_text('- WEB-Q04: one\n- WEB-Q04: another\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            quality.synchronize(self.root)

    def test_non_web_project_needs_no_web_case_artifact(self):
        (self.root / quality.SOURCE).write_text('# Local application quality\n')
        before = (self.root / quality.TARGET).read_bytes()
        quality.synchronize(self.root)
        quality.validate(self.root)
        self.assertEqual(before, (self.root / quality.TARGET).read_bytes())

    def test_all_oversized_and_missing_outputs_reported_together(self):
        for name, size in [('first.md', 12), ('second.md', 13)]:
            (self.root / name).write_text('x' * size)
        contract = {'artifact_byte_budgets': {'first.md': 10, 'second.md': 10, 'missing.md': 10},
                    'artifact_target_bytes': {'first.md': 8, 'second.md': 8, 'missing.md': 8}}
        with patch.object(context, 'governance_contract', return_value={'paths': {}}), \
                patch.object(context, 'resolved_output_contract', return_value=contract):
            with self.assertRaises(context.ContextError) as error:
                context.validate_stage_output(self.root, 'tooling')
        for name in ('first.md', 'second.md', 'missing.md'):
            self.assertIn(name, str(error.exception))

    def test_advisory_sizing_preserves_files_and_reports_headroom_without_acceptance(self):
        path = self.root / 'draft.md'
        path.write_bytes(b'x' * 12)
        contract = {'artifact_byte_budgets': {'draft.md': 10, 'missing.md': 10},
                    'artifact_target_bytes': {'draft.md': 8, 'missing.md': 8}}
        with patch.object(context, 'governance_contract', return_value={'paths': {}}), \
                patch.object(context, 'resolved_output_contract', return_value=contract):
            result = context.inspect_stage_output(self.root, 'research')
        self.assertTrue(result['advisory_only'])
        self.assertEqual(-2, result['artifacts'][0]['headroom_bytes'])
        self.assertEqual(4, result['artifacts'][0]['above_target_bytes'])
        self.assertIsNone(result['artifacts'][1]['bytes'])
        self.assertEqual(b'x' * 12, path.read_bytes())

    def test_generated_growth_preserves_authored_budget_and_cannot_hide_prose(self):
        from bootstrap_lifecycle import lifecycle_view
        model = {'decisions': [], 'elements': [{'id': f'element-{n}', 'status': 'proposed'} for n in range(200)],
                 'relationships': []}
        model_path = self.root / 'docs/architecture/architecture-map.json'
        model_path.write_text(json.dumps(model), encoding='utf-8')
        path = self.root / 'docs/architecture/architecture.md'
        body = '# Design\n\n' + 'é' * 4000 + '\n\n'
        path.write_bytes((body + lifecycle_view(model)).replace('\n', '\r\n').encode('utf-8'))
        before = path.read_bytes()
        sizes = context.artifact_sizes(self.root, 'docs/architecture/architecture.md', {})
        self.assertGreater(sizes['bytes'], 10240)
        self.assertLess(sizes['authored_bytes'], 10240)
        with patch.object(context, 'governance_contract', return_value={'paths': {'specification_roadmap': 'docs/architecture/specification-roadmap.md', 'constitution_document': '.specify/memory/constitution.md', 'constitution_ratification': '.specify/memory/constitution-ratification.json'}}):
            context.validate_final_narrative_sizes(self.root)
        self.assertEqual(before, path.read_bytes())
        # Extra author prose inside a marker is not a canonical generated view.
        path.write_text(body + lifecycle_view(model).replace('## Current lifecycle authority',
                        '## Current lifecycle authority\n' + 'hidden ' * 1000), encoding='utf-8')
        sizes = context.artifact_sizes(self.root, 'docs/architecture/architecture.md', {})
        self.assertEqual(0, sizes['generated_bytes'])
        with patch.object(context, 'governance_contract', return_value={'paths': {'specification_roadmap': 'docs/architecture/specification-roadmap.md', 'constitution_document': '.specify/memory/constitution.md', 'constitution_ratification': '.specify/memory/constitution-ratification.json'}}):
            with self.assertRaisesRegex(context.ContextError, 'hard byte budget'):
                context.validate_final_narrative_sizes(self.root)
        path.write_text(body + '<!-- PROGRAM-KIT:LIFECYCLE:START -->', encoding='utf-8')
        with self.assertRaisesRegex(context.ContextError, 'Malformed'):
            context.artifact_sizes(self.root, 'docs/architecture/architecture.md', {})

    def test_quality_view_counts_separately_without_dropping_any_case(self):
        quality.synchronize(self.root)
        sizes = context.artifact_sizes(self.root, quality.TARGET.as_posix(), {})
        raw = (self.root / quality.TARGET).read_bytes().decode('utf-8')
        block = raw[raw.index(quality.START):raw.index(quality.END) + len(quality.END)]
        self.assertEqual(len(block.encode('utf-8')), sizes['generated_bytes'])
        quality.validate(self.root)

    def test_final_validation_includes_roadmap_physical_bytes(self):
        path = self.root / 'docs/architecture/specification-roadmap.md'
        path.write_bytes(b'x' * 6144)
        paths = {'specification_roadmap': 'docs/architecture/specification-roadmap.md',
                 'constitution_document': '.specify/memory/constitution.md',
                 'constitution_ratification': '.specify/memory/constitution-ratification.json'}
        with patch.object(context, 'governance_contract', return_value={'paths': paths}):
            context.validate_final_narrative_sizes(self.root)
            path.write_bytes(b'x' * 6145)
            with self.assertRaisesRegex(context.ContextError, 'specification-roadmap.md'):
                context.validate_final_narrative_sizes(self.root)

    def test_brief_pages_are_lossless_bounded_and_do_not_rebuild_sources(self):
        path = context.context_path(context.safe_run_directory(self.root, 'trial'), 'closure')
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'run_id': 'trial', 'stage': 'closure', 'facts': ['é漢🙂' * 12000],
                   'last_required_fact': 'must not disappear'}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        before = path.read_bytes()
        first = context.read_brief(self.root, 'trial', 'closure', 1)
        pages = [context.read_brief(self.root, 'trial', 'closure', n)
                 for n in range(1, first['pages'] + 1)]
        self.assertEqual(payload, json.loads(''.join(p['text'] for p in pages)))
        self.assertTrue(all(len(p['text']) <= 8000 for p in pages))
        self.assertEqual(1, len({p['sha256'] for p in pages}))
        self.assertIsNone(pages[-1]['next_page'])
        for invalid in (0, first['pages'] + 1):
            with self.assertRaises(context.ContextError):
                context.read_brief(self.root, 'trial', 'closure', invalid)
        self.assertEqual(before, path.read_bytes())

    def test_repository_reader_pages_unicode_and_selects_json_without_mutation(self):
        from bounded_read import read_page, PAGE_BYTES
        path = self.root / 'large.json'
        payload = {'one/key': {'~value': ['é漢🙂' * 7000]}, 'other': 'not requested'}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        before = path.read_bytes()
        first = read_page(self.root, 'large.json', pointer='/one~1key/~0value/0')
        pages = [read_page(self.root, 'large.json', n, '/one~1key/~0value/0')
                 for n in range(1, first['pages'] + 1)]
        self.assertEqual(payload['one/key']['~value'][0], json.loads(''.join(p['text'] for p in pages)))
        self.assertTrue(all(len(p['text'].encode('utf-8')) <= PAGE_BYTES for p in pages))
        self.assertEqual(1, len({p['sha256'] for p in pages}))
        for page in (0, first['pages'] + 1):
            with self.assertRaises(ValueError):
                read_page(self.root, 'large.json', page, '/one~1key/~0value/0')
        with self.assertRaises(ValueError):
            read_page(self.root, '../outside.txt')
        with self.assertRaises(ValueError):
            read_page(self.root, 'large.json', pointer='/one~1key/~0value/-1')
        self.assertEqual(before, path.read_bytes())

    def test_later_stage_preserves_approved_research_and_allows_separate_successor(self):
        research = self.root / 'docs/architecture/tooling-evaluation.md'
        research.write_text('Original proposal: all provider cases before closure.\n', encoding='utf-8')
        receipt = self.root / '.specify/governance/bootstrap-assessment-approval.json'
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({'status': 'Approved', 'artifacts': {
            'docs/architecture/tooling-evaluation.md': context.sha256_file(research)}}), encoding='utf-8')
        protected = context.approved_assessment_inputs(self.root)
        brief = context.context_path(context.safe_run_directory(self.root, 'trial'), 'closure')
        brief.parent.mkdir(parents=True)
        brief.write_text(json.dumps({'stage_plan': {'approved_inputs': protected}}), encoding='utf-8')
        # A successor resolves the research proposal without rewriting its authority.
        (research.parent / 'successor.md').write_text('Mechanism now; consumer behavior at delivery.')
        context.validate_approved_inputs(self.root, protected)
        original = research.read_bytes()
        research.write_text('Edited proposal: consumer behavior later.', encoding='utf-8')
        with patch.object(context, 'validate_stage_output') as downstream:
            with self.assertRaisesRegex(context.ContextError, 'tooling-evaluation.md'):
                context.validate_stage_batch(self.root, 'trial', 'closure')
            downstream.assert_not_called()
        # Rewriting the approval receipt must not bypass the captured boundary.
        receipt.write_text(json.dumps({'status': 'Approved', 'artifacts': {
            'docs/architecture/tooling-evaluation.md': context.sha256_file(research)}}), encoding='utf-8')
        with self.assertRaisesRegex(context.ContextError, 'approval.json'):
            context.validate_stage_batch(self.root, 'trial', 'closure')
        research.write_bytes(original)
        self.assertTrue((research.parent / 'successor.md').exists())


if __name__ == '__main__':
    unittest.main()

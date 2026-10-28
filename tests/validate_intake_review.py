"""Inspectable review agenda and shipped instruction regression, not AI/human acceptance."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from owned_fixture import FixtureDirectory
from validate_native_phases import snapshot

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import product_intake as intake


class IntakeReview(unittest.TestCase):
    def test_constitution_criteria_remain_human_review_prompts_for_substantive_and_vacuous_drafts(self):
        with FixtureDirectory() as name:
            root = Path(name); intent = root / 'docs/architecture/project-intent.md'; intent.parent.mkdir(parents=True)
            intent.write_text('# Synthetic reporting service\n', encoding='utf-8')
            constitution = root / '.specify/memory/constitution.md'; constitution.parent.mkdir(parents=True)
            examples = (
                '# Constitution\n**Status**: Draft\nBuild a modern reporting app with a dashboard and export.\n',
                '# Constitution\n**Status**: Ratified\nDomain contracts must not reference provider implementations. '
                'Check dependency direction; review consequential exceptions with the owner.\n',
            )
            for text in examples:
                constitution.write_text(text, encoding='utf-8')
                before = snapshot(root)
                value = intake.review(root)
                criteria = value['constitution_review']
                self.assertEqual('.specify/memory/constitution.md', criteria['path'])
                self.assertIn('product-founding.md#constitution-and-consequential-decisions', criteria['reference'])
                questions = '\n'.join(criteria['questions'])
                for meaning in ('design/code decision', 'native framework reuse', 'service lifetimes/disposal',
                                'failure semantics', 'concrete source', 'proposed defaults', 'consequential exceptions'):
                    self.assertIn(meaning, questions)
                self.assertIn('No semantic quality', criteria['authority'])
                self.assertIn('Ratified label', criteria['authority'])
                self.assertEqual(before, snapshot(root), 'Review prompts must not grade, rewrite or ratify either draft')
                self.assertNotIn('score', criteria)
                self.assertNotIn('passed', criteria)

    def test_missing_projection_has_preparation_and_view_offer_without_review_writes(self):
        with FixtureDirectory() as name:
            root = Path(name); architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'project-intent.md').write_text('# Synthetic request service\n', encoding='utf-8')
            map_path = architecture / 'architecture-map.json'
            map_path.write_bytes((SCRIPTS.parent / 'references/architecture-map-minimal.json').read_bytes())
            before = snapshot(root)
            from c4_view import C4ViewError, validate_projection
            with self.assertRaisesRegex(C4ViewError, 'projection is missing'):
                validate_projection(root)
            value = intake.review(root)
            c4 = next(row for row in value['review_agenda'] if row['topic'] == 'C4 views')
            self.assertIn('projection missing', c4['availability'])
            preparation = value['c4_preparation']
            self.assertIn('architecture_map.py validate', preparation['validate_command'])
            self.assertIn('architecture_map.py export', preparation['export_command'])
            self.assertIn('--output docs/architecture/workspace.dsl', preparation['export_command'])
            self.assertIn('View C4', preparation['offer_after_export'])
            self.assertIn('$speckit-program-kit-governance-view-c4', preparation['offer_after_export'])
            self.assertEqual(before, snapshot(root), 'A read-only review must not export or invent decisions')
            # The existing exporter, not a new review writer or viewer runtime,
            # prepares the actual projection used by the local viewer.
            result = subprocess.run([sys.executable, str(SCRIPTS / 'architecture_map.py'), 'export',
                '--map', str(map_path), '--output', str(architecture / 'workspace.dsl')], cwd=root,
                capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue(validate_projection(root)['projection_current'])
            after_export = snapshot(root)
            ready = intake.review(root)
            self.assertIn('docs/architecture/workspace.dsl', next(
                row for row in ready['review_agenda'] if row['topic'] == 'C4 views')['paths'])
            self.assertIn('freshness', ready['c4_preparation']['availability'])
            self.assertEqual(after_export, snapshot(root))

    def test_review_requests_constitution_and_named_adr_decisions_without_accepting_them(self):
        with FixtureDirectory() as name:
            root = Path(name); architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'project-intent.md').write_text('# Synthetic service\nEarlier unscoped answer: confirm.\n', encoding='utf-8')
            constitution = root / '.specify/memory/constitution.md'; constitution.parent.mkdir(parents=True)
            constitution.write_text('# Constitution\n**Status**: Draft\nSynthetic draft.\n', encoding='utf-8')
            decisions = architecture / 'decisions'; decisions.mkdir()
            for name in ('identity', 'retention'):
                (decisions / f'{name}.md').write_text(f'# {name}\n**Status**: Proposed\n', encoding='utf-8')
            before = snapshot(root)
            value = intake.review(root)
            requests = value['decision_requests']
            self.assertEqual(['Product confirmation', 'Constitution ratification', 'ADR disposition', 'ADR disposition'],
                             [row['topic'] for row in requests])
            self.assertEqual(['docs/architecture/project-intent.md', '.specify/memory/constitution.md',
                              'docs/architecture/decisions/identity.md', 'docs/architecture/decisions/retention.md'],
                             [row['record_in'] for row in requests])
            self.assertIn('ratify', requests[1]['question'])
            self.assertIn('identity.md', requests[2]['question'])
            self.assertIn('retention.md', requests[3]['question'])
            self.assertIn('named', value['confirmation_scope'])
            self.assertIn('reuse', value['decision_guidance'].lower())
            self.assertEqual(before, snapshot(root), 'Drafts and proposals must not become human approval')

    def test_complete_review_links_actual_roadmap_domain_c4_and_distinct_decisions(self):
        with FixtureDirectory() as name:
            root = Path(name); architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'project-intent.md').write_text('# Synthetic request service\nEarlier answer: confirm.\n', encoding='utf-8')
            (architecture / 'specification-roadmap.md').write_text('# Roadmap\n1. Submit request\n2. Resolve request\n', encoding='utf-8')
            (architecture / 'technology-radar.md').write_text('# Technology\nPython, selected by fictional designer.\n', encoding='utf-8')
            (architecture / 'architecture-map.json').write_bytes((SCRIPTS.parent / 'references/architecture-map-minimal.json').read_bytes())
            import architecture_map
            model = architecture_map.load_object(architecture / 'architecture-map.json')
            (architecture / 'workspace.dsl').write_text(architecture_map.StructurizrDslExporter().export(model), encoding='utf-8')
            constitution = root / '.specify/memory/constitution.md'; constitution.parent.mkdir(parents=True)
            constitution.write_text('# Constitution\nStatus: Draft\nSynthetic proposal.\n', encoding='utf-8')
            decisions = architecture / 'decisions'; decisions.mkdir()
            adr = decisions / 'identity.md'; adr.write_text('# Identity\nStatus: Proposed\n', encoding='utf-8')
            before = snapshot(root)
            value = intake.review(root)
            topics = {row['topic']: row for row in value['review_agenda']}
            self.assertEqual({'Product and journeys', 'Roadmap', 'Domain map', 'C4 views',
                              'Technology and environments', 'Constitution', 'ADRs', 'Open decisions and handoff'}, set(topics))
            self.assertIn('docs/architecture/specification-roadmap.md', topics['Roadmap']['paths'])
            self.assertIn('docs/architecture/architecture-map.json', topics['Domain map']['paths'])
            self.assertIn('docs/architecture/workspace.dsl', topics['C4 views']['paths'])
            self.assertIn('Raw JSON/DSL links alone are not a walkthrough', topics['C4 views']['focus'])
            self.assertIn('human review not established', topics['C4 views']['availability'])
            self.assertIn('distinct human decision', topics['Constitution']['focus'])
            self.assertIn('docs/architecture/decisions/identity.md', topics['ADRs']['paths'])
            self.assertIn('unscoped confirm does not approve unseen models', value['confirmation_scope'])
            self.assertEqual(before, snapshot(root), 'Review changed documents or manufactured consent')
            self.assertNotIn('acceptance', value)

    def test_sparse_existing_product_remains_reviewable_without_required_new_files(self):
        with FixtureDirectory() as name:
            root = Path(name); intent = root / 'docs/architecture/project-intent.md'; intent.parent.mkdir(parents=True)
            intent.write_text('# Synthetic product\nRoadmap and domain are described here.\n', encoding='utf-8')
            before = snapshot(root)
            result = subprocess.run([sys.executable, str(SCRIPTS / 'product_intake.py'), 'review'], cwd=root,
                capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            value = json.loads(result.stdout)
            c4 = next(row for row in value['review_agenda'] if row['topic'] == 'C4 views')
            self.assertEqual([], c4['paths'])
            self.assertIn('gap/deferral', c4['availability'])
            self.assertIn('wait for the scoped decision', value['next_action'])
            self.assertEqual(before, snapshot(root))

    def test_intake_instructions_present_overview_before_confirmation_and_handoff(self):
        path = SCRIPTS.parent / 'commands/speckit.program-kit-governance.product-intake.md'
        text = path.read_text(encoding='utf-8')
        section = text.split('## Confirm meaning and continue', 1)[1]
        self.assertLess(section.index('**Review overview**'), section.index('Then ask for'))
        self.assertLess(section.index('**pause before specification intake**'), section.index('Continue directly'))
        for phrase in ('The outcome roadmap', 'The domain map', 'C4 system-context and container views',
                       'Constitution principles', 'Technology choices', 'unanswered questions',
                       'same response that requests confirmation', 'new mandatory files', 'explicit deferral'):
            self.assertIn(phrase, section)
        for phrase in ('architecture_map.py export', 'offer **View C4**',
                       '$speckit-program-kit-governance-view-c4', 'ratify the linked constitution draft',
                       'each named', '`**Status**: Ratified`', 'Leave unanswered items Draft/Proposed'):
            self.assertIn(phrase, section)
        self.assertLess(section.index('architecture_map.py export'), section.index('**Review overview**'))
        handoff = (SCRIPTS.parent / 'commands/speckit.program-kit-governance.specification-intake.md').read_text(encoding='utf-8')
        self.assertIn('missing review and pause for a scoped decision', handoff)
        self.assertIn('independent feature request does not require', handoff)
        self.assertIn('ratification or named ADR acceptance was', handoff)
        self.assertIn('ask for the missing explicit decisions now', handoff)
        for phrase in ('durable decision-guiding', 'rationale, applicability and concrete verification',
                       'No fixed principle count', 'not semantic certification', 'later design/code decision'):
            self.assertIn(phrase, text)
        reference = (SCRIPTS.parent / 'references/product-founding.md').read_text(encoding='utf-8')
        for phrase in ('compiled dependency direction', 'quality scenarios', 'configuration admission',
                       'do not invent SLOs', 'existing ADR process', 'architecture descriptions',
                       'does not prescribe a Program Kit constitution format'):
            self.assertIn(phrase, reference)


if __name__ == '__main__':
    unittest.main(verbosity=2)

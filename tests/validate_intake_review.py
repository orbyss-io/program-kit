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
        handoff = (SCRIPTS.parent / 'commands/speckit.program-kit-governance.specification-intake.md').read_text(encoding='utf-8')
        self.assertIn('missing review and pause for a scoped decision', handoff)
        self.assertIn('independent feature request does not require', handoff)


if __name__ == '__main__':
    unittest.main(verbosity=2)

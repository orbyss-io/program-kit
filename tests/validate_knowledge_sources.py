"""Independent failures and real source/producer consumption for F1 discovery."""
from pathlib import Path
import copy
import json
import sys
import unittest
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from knowledge_sources import resolve, select, confined
from knowledge_discovery import load, validate, discover, selected, inspect_declarations, validate_group
from decision_knowledge import constraints


class CanonicalSourcesTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load()

    def test_actual_native_roles_and_prose_are_complementary(self):
        native = resolve(self.catalog, 'native.allowed-role-references', extensions=ROOT / 'extensions')
        self.assertIn('"core": {"core"}', native['text'])
        self.assertIn('RUNTIME_PROJECT_ROLES', native['text'])
        # Independent forbidden boundary oracle, not a comparison against a
        # value copied out of the registry or generated from the same source.
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
        from repository_architecture import validate_planned
        graph = {'runtimeComposition': {'projects': [
            {'path': 'src/Orders.Core/Orders.Core.csproj', 'role': 'core',
             'projectReferences': ['src/Orders.Store/Orders.Store.csproj']},
            {'path': 'src/Orders.Store/Orders.Store.csproj', 'role': 'provider', 'projectReferences': []}], 'bindings': []}}
        with self.assertRaises(ValueError):
            validate_planned(ROOT, graph)

    def test_python_selectors_never_execute_source_and_follow_table_dependencies(self):
        source = 'raise RuntimeError("must not execute")\nBASE = {"core"}\nTABLE = {"test": BASE}\n'
        result = select(source, {'kind': 'python-symbol', 'name': 'TABLE'})
        self.assertIn('BASE = {"core"}', result)
        self.assertNotIn('RuntimeError', result)
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            select(source + 'TABLE = {}\n', {'kind': 'python-symbol', 'name': 'TABLE'})
        with self.assertRaisesRegex(ValueError, 'Missing'):
            select(source, {'kind': 'python-symbol', 'name': 'MISSING'})

    def test_discovery_inspects_candidates_without_promoting_or_emitting_literal_values(self):
        with FixtureDirectory() as directory:
            path = Path(directory) / 'carrier.py'
            path.write_text('raise RuntimeError("not executed")\nRULES = {"core"}\ndef guidance():\n    return "must NEVER_EXPOSE_SECRET"\n')
            result = inspect_declarations(path)
            self.assertTrue(any(row.get('symbol') == 'RULES' for row in result['candidates']))
            self.assertTrue(any(row.get('symbol') == 'guidance' for row in result['candidates']))
            self.assertNotIn('NEVER_EXPOSE_SECRET', json.dumps(result))
            self.assertNotIn('active', result)

    def test_expected_upgrade_failure_preserves_deep_diagnostics(self):
        from unittest.mock import patch
        import validate_consumer_upgrade_install as fixture
        from owned_fixture import filesystem_path
        with FixtureDirectory(native=True) as directory:
            root = Path(directory)
            relative = Path('artifacts/program-kit/consumer-upgrade') / ('nested-baseline-' * 7) / ('retained-input-' * 5) / 'witness.txt'
            original = Path(filesystem_path(root / relative))
            original.parent.mkdir(parents=True)
            original.write_text('Retain expected failure evidence.', encoding='utf-8')
            destination = root / 'review-diagnostics'
            with patch.object(fixture, 'RUN', destination):
                fixture.run([sys.executable, '-c', 'raise SystemExit(2)'], root, expected_exit=2)
            copied = Path(filesystem_path(destination / '0-local-state/consumer-upgrade' / relative.relative_to('artifacts/program-kit/consumer-upgrade')))
            self.assertEqual('Retain expected failure evidence.', copied.read_text(encoding='utf-8'))

    def test_json_schema_references_remain_part_of_selected_declaration(self):
        source = {'rule': {'$ref': '#/$defs/value'}, '$defs': {'value': {'minimum': 3}}, 'unrelated': 1}
        selector = {'kind': 'json-pointer', 'pointer': '/rule'}
        before = select(json.dumps(source), selector)
        source['unrelated'] = 2
        self.assertEqual(before, select(json.dumps(source), selector))
        source['$defs']['value']['minimum'] = 4
        self.assertNotEqual(before, select(json.dumps(source), selector))
        with self.assertRaisesRegex(ValueError, 'Missing'):
            select('{}', selector)

    def test_msbuild_and_editorconfig_retain_conditional_context(self):
        source = '<Project><Import Project="consumer.props"/><PropertyGroup Condition="x"><Warnings>true</Warnings></PropertyGroup></Project>'
        result = select(source, {'kind': 'xml-elements', 'element': 'Warnings'})
        self.assertIn('consumer.props', result)
        self.assertIn('Condition', result)
        config = 'root = true\n[*]\nkey = warning\n[*.cs]\nkey = error\n'
        result = select(config, {'kind': 'editorconfig-key', 'section': '[*.cs]', 'key': 'key'})
        self.assertIn('warning', result)
        self.assertIn('error', result)
        self.assertFalse(json.loads(result)['effectiveConfiguration'])

    def test_ambiguous_markers_and_fake_headings_fail(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            select('<!-- program-kit:decision-rule x -->a<!-- /program-kit:decision-rule -->' * 2,
                   {'kind': 'markdown-marker', 'id': 'x'})
        source = '# Header\n```\n## Actual\n```\n## Actual\nCanonical text.\n'
        self.assertEqual('Canonical text.', select(source, {'kind': 'markdown-section', 'heading': 'Actual'}))

    def test_new_canonical_duty_cannot_hide_outside_registered_leaves(self):
        content = ('<!-- program-kit:decision-rule group -->\n'
                   '<!-- program-kit:knowledge-rule leaf -->Existing duty.<!-- /program-kit:knowledge-rule -->\n'
                   'New mandatory duty without an identity.\n<!-- /program-kit:decision-rule -->')
        with self.assertRaisesRegex(ValueError, 'Unmapped'):
            validate_group(content, 'group', ['leaf'])
        altered = copy.deepcopy(self.catalog)
        requirement = next(row for row in altered['requirements'] if row['id'] == 'dotnet-boundaries')
        requirement['ruleIds'].remove('principle.compilation-boundaries')
        with self.assertRaisesRegex(ValueError, 'Omitted canonical duty'):
            validate(altered, ROOT / 'extensions', ROOT)

    def test_source_fingerprint_tracks_selected_rules_not_other_text(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'source.md').write_text('## Selected\nKeep this rule.\n## Other\nOne.\n')
            catalog = {'sources': [{'id': 's', 'locator': {'kind': 'extension', 'path': 'source.md'}}],
                       'rules': {'r': {'source': 's', 'selector': {'kind': 'markdown-section', 'heading': 'Selected'}, 'owner': 'owner', 'limits': 'fixture'}}}
            before = resolve(catalog, 'r', extensions=root)
            (root / 'source.md').write_text('## Selected\nKeep this rule.\n## Other\nTwo.\n')
            after = resolve(catalog, 'r', extensions=root)
            self.assertEqual(before['fingerprint'], after['fingerprint'])
            self.assertNotEqual(before['sourceSha256'], after['sourceSha256'])
            (root / 'source.md').write_text('## Selected\nChanged rule.\n## Other\nTwo.\n')
            self.assertNotEqual(before['fingerprint'], resolve(catalog, 'r', extensions=root)['fingerprint'])

    def test_root_escape_and_repository_only_sources_are_not_substituted(self):
        with self.assertRaisesRegex(ValueError, 'escapes'):
            confined(ROOT, '../outside')
        with self.assertRaisesRegex(ValueError, 'Repository-only'):
            resolve(self.catalog, 'decision.0007', extensions=ROOT / 'extensions')
        with self.assertRaisesRegex(ValueError, 'Unknown responsibility'):
            selected(self.catalog, ['invented-responsibility'])

    def test_actual_producer_ignores_retired_summary_policy(self):
        requirements = copy.deepcopy(self.catalog['requirements'])
        for requirement in requirements:
            requirement['requirement'] = 'FORGED RETIRED POLICY'
            requirement['guidance'] = {'planning': 'FORGED RETIRED POLICY'}
        import phase_obligations
        output = phase_obligations.render({'requirements': requirements}, 'planning')
        self.assertNotIn('FORGED RETIRED POLICY', output)
        self.assertIn('canonical permission', output)
        self.assertIn('ALLOWED_ROLE_REFERENCES', output)

    def test_bootstrap_keeps_its_canonical_group_adapter(self):
        from unittest.mock import patch
        import bootstrap_context
        with patch.object(bootstrap_context, 'routed_references', return_value=(
                '.specify/extensions/program-kit-dotnet/references/technology-profiles/dotnet.md',)):
            rows = bootstrap_context.decision_constraints({}, 'architecture')
        result = next(row for row in rows if row['id'] == 'compilation-responsibilities')
        self.assertIn('Core owns stable contracts', result['constraint'])
        self.assertNotIn('<!-- program-kit:knowledge-rule', result['constraint'])

    def test_changed_canonical_producer_selects_its_real_consumers(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import run_validation
        definition = run_validation.load_definition()
        checks, gaps, _ = run_validation.select_affected(definition, [
            'extensions/program-kit-governance/scripts/knowledge_sources.py'])
        identities = {row['id'] for row in checks}
        self.assertIn('validate_knowledge_sources', identities)
        self.assertIn('validate_task_generation', identities)
        self.assertFalse(gaps)
        unrelated, _, _ = run_validation.select_affected(definition, ['docs/knowledge-discovery.md'])
        self.assertNotIn('validate_knowledge_sources', {row['id'] for row in unrelated})

    def test_sources_routes_and_rule_owners_resolve(self):
        validate(self.catalog, ROOT / 'extensions', ROOT)
        duplicate = copy.deepcopy(self.catalog)
        duplicate['rules']['duplicate'] = duplicate['rules']['native.allowed-role-references']
        with self.assertRaisesRegex(ValueError, 'Duplicate canonical'):
            validate(duplicate, ROOT / 'extensions', ROOT)

    def test_discovery_covers_non_markdown_and_history_without_promoting_them(self):
        records = discover(ROOT, self.catalog)
        paths = {row['path'] for row in records}
        for path in ('maintenance-policy.json', 'tests/validate_knowledge_application.py',
                     'extensions/program-kit-dotnet/templates/dotnet/files/eng/architecture_rules.py',
                     'extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig',
                     'docs/decisions/0007-separate-domain-and-integration-events.md'):
            self.assertIn(path, paths)
        self.assertTrue(all(row['observedConsultation'] == 'unknown' for row in records))
        history = next(row for row in self.catalog['sources'] if row['locator']['kind'] == 'git-history')
        self.assertEqual('history', history['disposition'])
        self.assertFalse(any(rule['source'] == history['id'] for rule in self.catalog['rules'].values()))
        browser = selected(self.catalog, ['browser-experience'])
        self.assertNotIn('native.allowed-role-references', browser)


class ReviewFixtureTests(unittest.TestCase):
    def test_installed_canonical_walkthrough_and_failures(self):
        from knowledge_review_fixture import scenario
        with FixtureDirectory() as directory:
            result = scenario(directory)
            self.assertEqual('passed', result['status'])


if __name__ == '__main__':
    unittest.main()

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
from knowledge_discovery import load, validate, discover, selected, inspect_declarations, validate_group, display_coverage, validate_section_routes, source_partition, validate_source_partition
from decision_knowledge import constraints
from knowledge_review_fixture import BRIEF_LIMITS, assert_complete_required_text


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

    def test_dotnet_precode_atoms_survive_bounded_ordinary_brief(self):
        # The former 180-character preview lost the invocation restrictions and
        # async completion/lifetime clauses. Assert complete canonical atoms,
        # rather than accepting a link/reading claim or a giant document dump.
        duties = {
            'dotnet-source-quality': ['method-coherence', 'source-documentation', 'invocation-layout', 'source-enforcement'],
            'dotnet-async': ['async-completion'],
            'dotnet-concurrency': ['synchronization-contract'],
            'dotnet-lifetime': ['resource-retention'],
            'dotnet-construction': ['construction-invariants', 'deferred-initialization'],
            'dotnet-queries': ['query-execution'],
            'dotnet-runtime-io': ['runtime-time-and-io'],
            'dotnet-runtime-security': ['runtime-security'],
        }
        selected_requirements = [r for r in self.catalog['requirements'] if r['id'] in duties]
        brief = constraints(self.catalog, selected_requirements, ROOT / 'extensions')
        for requirement, names in duties.items():
            text = '\n'.join(brief[requirement])
            for name in names:
                rule = resolve(self.catalog, 'principle.' + name, extensions=ROOT / 'extensions')
                self.assertIn(rule['text'], text, name)
        source = '\n'.join(brief['dotnet-source-quality'])
        self.assertIn('Never invoke a method inside an argument', source)
        self.assertIn('Preserve evaluation order, cancellation, disposal and deferred activation', source)
        self.assertIn('a green build does not waive that review', source)
        self.assertLess(len(source.encode('utf-8')), BRIEF_LIMITS['source-quality'])
        all_brief = '\n'.join('\n'.join(rows) for rows in constraints(
            self.catalog, self.catalog['requirements'], ROOT / 'extensions').values())
        self.assertLess(len(all_brief.encode('utf-8')), BRIEF_LIMITS['union'])
        assert_complete_required_text(self, self.catalog, self.catalog['requirements'], all_brief, ROOT / 'extensions')

    def test_focused_dotnet_detail_retains_the_full_source(self):
        requirements = [r for r in self.catalog['requirements'] if r['id'] == 'dotnet-source-quality']
        brief = '\n'.join(constraints(self.catalog, requirements, ROOT / 'extensions', detailed=True)['dotnet-source-quality'])
        self.assertIn('Cyclomatic complexity is a warning signal', brief)
        self.assertIn('Public parameter renames remain a source-compatibility concern', brief)

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

    def test_required_guidance_prefix_never_truncates_a_complete_constraint(self):
        with FixtureDirectory() as name:
            root = Path(name)
            text = 'Carry the one owned deadline through every bounded stage. ' * 8 + 'Never restart it after an asynchronous wait.'
            (root / 'rules.md').write_text('<!-- program-kit:knowledge-rule guidance.complete -->\n' + text + '\n<!-- /program-kit:knowledge-rule -->')
            rules = {'sources': [{'id': 'owner', 'locator': {'kind': 'extension', 'path': 'rules.md'}}],
                'ruleDefaults': {'owner': 'owner', 'limits': 'Fictional selector behavior only'},
                'rules': {'guidance.complete': {'source': 'owner', 'level': 'conditional',
                    'selector': {'kind': 'markdown-marker', 'marker': 'knowledge-rule', 'id': 'guidance.complete'}}}}
            rendered = '\n'.join(constraints(rules, [{'id': 'scope', 'ruleIds': ['guidance.complete']}], root)['scope'])
            self.assertIn(text, rendered)
            self.assertNotIn('[excerpt]', rendered)

    def test_focused_sections_require_full_source_leaf_coverage_and_keep_advice_explicit(self):
        with FixtureDirectory() as name:
            root = Path(name)
            source = root / 'rules.md'
            source.write_text('## Policy\n<!-- program-kit:knowledge-rule principle.required -->\n'
                'Preserve the original operation identity after uncertain completion.\n<!-- /program-kit:knowledge-rule -->\n'
                '<!-- program-kit:knowledge-rule context.example -->\nAn illustrative fictional example.\n<!-- /program-kit:knowledge-rule -->\n')
            catalog = {'sources': [{'id': 'owner', 'locator': {'kind': 'extension', 'path': 'rules.md'},
                'route': {'kind': 'phase'}, 'sections': {'Policy': {'disposition': 'active', 'route': 'phase'}}}],
                'ruleDefaults': {'owner': 'owner', 'limits': 'Fictional source routing only'}, 'rules': {}}
            for identity, level in [('principle.required', 'conditional'), ('context.example', 'recommended')]:
                catalog['rules'][identity] = {'source': 'owner', 'level': level, 'status': 'active', 'requirements': ['scope'],
                    'selector': {'kind': 'markdown-marker', 'marker': 'knowledge-rule', 'id': identity}}
            catalog['rules']['context.example'].update(display='focused-detail',
                contextDisposition={'kind': 'context', 'owner': 'owner', 'reason': 'Illustration remains advice, not a required source decision.'})
            catalog['rules']['guidance.whole'] = {'source': 'owner', 'level': 'conditional', 'status': 'active',
                'requirements': ['scope'], 'selector': {'kind': 'markdown-section', 'heading': 'Policy'},
                'display': 'focused-detail', 'coveredBy': ['principle.required', 'context.example'],
                'contextDisposition': {'kind': 'context', 'owner': 'owner', 'reason': 'Exact required atoms appear in the ordinary brief; context remains focused.'}}
            requirement = {'id': 'scope', 'ruleIds': list(catalog['rules'])}
            output = '\n'.join(constraints(catalog, [requirement], root)['scope'])
            self.assertIn('Preserve the original operation identity', output)
            self.assertNotIn('An illustrative fictional example.', output)
            detailed = '\n'.join(constraints(catalog, [requirement], root, detailed=True)['scope'])
            self.assertIn('An illustrative fictional example.', detailed)
            self.assertEqual('recommended', catalog['rules']['context.example']['level'])
            display_coverage(catalog, 'guidance.whole', root)
            broken = copy.deepcopy(catalog)
            broken['rules']['guidance.whole']['coveredBy'].remove('principle.required')
            with self.assertRaisesRegex(ValueError, 'Incomplete canonical focused coverage'):
                display_coverage(broken, 'guidance.whole', root)
            misrouted = copy.deepcopy(catalog)
            misrouted['rules']['principle.required']['requirements'] = ['unrelated-scope']
            with self.assertRaisesRegex(ValueError, 'Incomplete focused responsibility coverage'):
                display_coverage(misrouted, 'guidance.whole', root)
            with self.assertRaisesRegex(ValueError, 'Omitted applicable focused canonical duty'):
                constraints(catalog, [{'id': 'scope', 'ruleIds': ['guidance.whole', 'context.example']}], root)
            source.write_text(source.read_text() + 'New mandatory cleanup responsibility outside every registered leaf.\n')
            with self.assertRaisesRegex(ValueError, 'Unmapped canonical section content'):
                display_coverage(catalog, 'guidance.whole', root)
            catalog['rules'].pop('guidance.whole')
            with self.assertRaisesRegex(ValueError, 'Unmapped canonical section content'):
                validate_section_routes(catalog, root)

    def test_phase_route_metadata_alone_cannot_claim_canonical_selection(self):
        with FixtureDirectory() as name:
            root = Path(name)
            (root / 'rules.md').write_text('## Recovery\nRetain the established identity; do not redispatch an uncertain operation.\n')
            catalog = {'sources': [{'id': 'owner', 'locator': {'kind': 'extension', 'path': 'rules.md'},
                'route': {'kind': 'phase', 'via': ['existing-owner.py']}, 'sections': {
                    'Recovery': {'disposition': 'active', 'route': 'phase'}}}], 'rules': {}}
            with self.assertRaisesRegex(ValueError, 'Unrouted active canonical section'):
                validate_section_routes(catalog, root)
            catalog['sources'][0]['sections']['Recovery']['codingDisposition'] = {
                'kind': 'native', 'owner': 'existing native fixture lifecycle',
                'reason': 'Fictional specialized native owner; disposition itself establishes no consumer behavior.'}
            validate_section_routes(catalog, root)

    def test_raw_source_partition_rejects_preamble_heading_marker_and_identical_prose_drift(self):
        with FixtureDirectory() as name:
            root = Path(name)
            path = root / 'source.md'
            original = '# Rules\nPreserve the original identity.\n## Selected\nPreserve the original identity.\n## Context\nIllustrative context.\n```text\n# Example heading\n```\n'
            path.write_text(original)
            source = {'id': 'owner', 'locator': {'kind': 'extension', 'path': 'source.md'}}
            catalog = {'sources': [source], 'rules': {'full': {'source': 'owner', 'status': 'active',
                'selector': {'kind': 'markdown-section', 'heading': 'Selected'}}}}
            headings, remaining = source_partition(catalog, source, root)
            source['contentCoverage'] = {'headings': headings, 'remaining': {'sha256': remaining,
                'kind': 'context', 'owner': 'source owner', 'reason': 'Exact fictional context remains classified.'}}
            validate_source_partition(catalog, source, root)
            for changed in (original + 'Preserve the original identity.\n', 'New raw preamble.\n' + original,
                    original + '## Undeclared new rule\nNew responsibility.\n',
                    original.replace('# Example heading', '# Newly authored fenced content')):
                path.write_text(changed)
                with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'source (structure|remainder)|source.*preamble'):
                    validate_source_partition(catalog, source, root)
            for identity in ('unregistered', 'foreign'):
                path.write_text(original + '<!-- program-kit:knowledge-rule ' + identity + ' -->\nNew duty.\n<!-- /program-kit:knowledge-rule -->\n')
                catalog['rules']['foreign'] = {'source': 'another-source', 'status': 'active',
                    'selector': {'kind': 'markdown-marker', 'marker': 'knowledge-rule', 'id': 'foreign'}}
                with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'Unregistered|foreign'):
                    validate_source_partition(catalog, source, root)

    def test_facet_typos_cannot_silently_remove_a_canonical_duty(self):
        for fields in ({'when': {'all': ['sourc-production']}}, {'when': {'unknown': []}},
                {'when': {'all': [None]}}, {'profileScope': {'secure-weeb': ['bff-cookie-v1']}},
                {'profileScope': {'secure-web': ['unknown-profile']}}, {'profileScope': {'secure-web': [None]}}):
            broken = copy.deepcopy(self.catalog)
            broken['rules']['principle.method-coherence'].update(fields)
            with self.subTest(fields=fields), self.assertRaisesRegex(ValueError, 'Unknown canonical.*(adapter|facet)'):
                validate(broken, ROOT / 'extensions', ROOT)

    def test_actual_owned_profile_facts_keep_brief_duties_and_units_in_one_scope(self):
        from feature_context import context, applicable_requirements
        from coding_context import compose, evaluation_duties
        with FixtureDirectory() as name:
            root = Path(name)
            feature = root / 'specs/001-scope'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('- **Specification roadmap entry**: RM-01\nHTTP browser in web/package.json.\n')
            (feature / 'plan.md').write_text('HTTP browser in web/package.json.')
            brief = root / '.program-kit/specification-intake/RM-01/brief.json'; brief.parent.mkdir(parents=True)
            brief.write_text(json.dumps({'architectureScope': ['owner']}))
            web = root / 'web'; web.mkdir(); (web / 'package.json').write_text('{"devDependencies":{"typescript":"5.9.0"}}')
            (web / 'policy.ts').write_text('export const result = 1;')
            architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'architecture-map.json').write_text(json.dumps({'elements': [
                {'id': 'owner', 'type': 'component', 'technology': '.NET browser'},
                {'id': 'neighbor', 'type': 'component'}], 'decisions': []}))
            selection = {'status': 'Accepted', 'targets': [{'id': 'owned', 'kind': 'dotnet-project', 'placement': {'owner': 'owner'}}],
                'instances': [{'composition': 'browser_bff', 'targetBindings': {'runtime': 'owned'}}]}
            path = architecture / 'building-block-selection.json'
            decisions = architecture / 'bootstrap-decisions.json'
            data = copy.deepcopy(self.catalog)
            bff, spa = 'principle.bff-selected-browser-contract', 'principle.spa-selected-browser-contract'
            host = 'principle.shell-feature-lifecycle-contract'
            data['codingUnits'] = [{'id': 'explicit-profile-unit', 'ruleIds': [bff, spa, host], 'route': 'manual-edit'}]
            for profile, composition, expected in (
                    ('bff-cookie-v1', 'browser_bff', {bff}), ('spa-pkce-v1', 'browser_spa_pkce', {spa}),
                    ('none-v1', None, set())):
                selection['instances'] = [{'composition': composition, 'targetBindings': {'runtime': 'owned'}}] if composition else []
                path.write_text(json.dumps(selection))
                decisions.write_text(json.dumps({'selected_profiles': ['dotnet', 'typescript-web'],
                    'web': {'secure_profile': profile}, 'dotnet': {'program_kit_host_opt_out': True,
                    'opt_out_reason': 'Fictional explicit conventional-host fixture', 'host_runtime': 'conventional'}}))
                tags = context(root, feature, 'implementation')
                requirements = applicable_requirements(data, tags)
                ids = {i for r in requirements for i in r['ruleIds']}
                self.assertEqual(expected, ids & {bff, spa})
                self.assertNotIn(host, ids)
                auth = {'principle.secure-shell-configuration', 'principle.secure-shell-settings',
                    'principle.canonical-auth-permission-contract', 'principle.authentication-presentation-contract',
                    'principle.auth-human-interaction-budget', 'principle.logout-publisher-compatibility'}
                if profile == 'none-v1':
                    self.assertFalse(auth & ids)
                    self.assertIn('principle.http-telemetry-contract', ids)
                else:
                    self.assertTrue(auth <= ids)
                output = '\n'.join(v for rows in constraints(data, requirements, ROOT / 'extensions').values() for v in rows)
                self.assertTrue(all(('Canonical ' + i) in output for i in expected))
                self.assertLess(len(output.encode('utf-8')), BRIEF_LIMITS['mixed'])
                assert_complete_required_text(self, data, requirements, output, ROOT / 'extensions')
                units, _, blockers = compose(data, requirements, tags, {}, ROOT / 'extensions')
                self.assertFalse(blockers)
                actual = {r['id'] for unit in units for r in unit['rules']}
                self.assertEqual(expected, actual)
                duties = evaluation_duties(data, requirements, units, root, ROOT / 'extensions', [])
                self.assertEqual(expected, {d['rule'] for d in duties} & {bff, spa, host})
            # A separately selected machine/outbound contract survives a
            # browser's explicit anonymous profile.
            selection['instances'] = [{'composition': 'service_to_service', 'targetBindings': {'runtime': 'owned'}}]
            path.write_text(json.dumps(selection))
            tags = context(root, feature, 'implementation')
            ids = {i for r in applicable_requirements(data, tags) for i in r['ruleIds']}
            self.assertIn('principle.neutral-auth-capabilities', ids)
            self.assertFalse({bff, spa} & ids)
            # An unrelated accepted target and a malformed/unknown profile cannot
            # turn repository-wide facts into an exemption for the owned scope.
            selection['targets'][0]['placement']['owner'] = 'neighbor'
            selection['instances'] = [{'composition': 'browser_bff', 'targetBindings': {'runtime': 'owned'}}]
            path.write_text(json.dumps(selection))
            tags = context(root, feature, 'implementation')
            self.assertFalse(any(t.startswith('secure-web:') for t in tags))
            ids = {i for r in applicable_requirements(data, tags) for i in r['ruleIds']}
            self.assertTrue({bff, spa} <= ids)
            selection['targets'][0]['placement']['owner'] = 'owner'; selection['instances'] = []
            path.write_text(json.dumps(selection)); decisions.write_text(json.dumps({'web': {'secure_profile': 'unrecognized'}, 'dotnet': {'program_kit_host_opt_out': True, 'opt_out_reason': 7}}))
            tags = context(root, feature, 'implementation')
            ids = {i for r in applicable_requirements(data, tags) for i in r['ruleIds']}
            self.assertTrue({bff, spa, host} <= ids)
            # Technology-neutral clauses remain selected for a real TS-only owner.
            tags = {'all', 'typescript', 'web'}
            ids = {i for r in applicable_requirements(data, tags) for i in r['ruleIds']}
            self.assertTrue({'principle.proportional-context-design', 'principle.cross-context-admissibility',
                'principle.consumer-meaning-ownership', 'principle.domain-integration-delivery'} <= ids)

    def test_two_owned_profile_targets_narrow_to_actual_task_project_paths(self):
        from feature_context import context, applicable_requirements
        with FixtureDirectory() as name:
            root = Path(name); feature = root / 'specs/001-owners'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('- **Specification roadmap entry**: RM-01\n')
            brief = root / '.program-kit/specification-intake/RM-01/brief.json'; brief.parent.mkdir(parents=True)
            brief.write_text(json.dumps({'architectureScope': ['bff', 'spa']}))
            architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'architecture-map.json').write_text(json.dumps({'elements': [
                {'id': 'bff', 'type': 'component', 'technology': '.NET HTTP browser'},
                {'id': 'spa', 'type': 'component', 'technology': '.NET HTTP browser'}], 'decisions': []}))
            targets, instances = [], []
            for owner, composition in [('bff', 'browser_bff'), ('spa', 'browser_spa_pkce')]:
                project = root / 'src' / owner / 'Owner.csproj'; project.parent.mkdir(parents=True)
                project.write_text('<Project Sdk="Microsoft.NET.Sdk.Web" />')
                targets.append({'id': owner, 'path': project.relative_to(root).as_posix(),
                    'kind': 'dotnet-project', 'placement': {'owner': owner}})
                instances.append({'composition': composition, 'targetBindings': {'runtime': owner}})
            (architecture / 'building-block-selection.json').write_text(json.dumps({'status': 'Accepted', 'targets': targets, 'instances': instances}))
            (architecture / 'bootstrap-decisions.json').write_text(json.dumps({'selected_profiles': ['dotnet'], 'web': {'secure_profile': 'bff-cookie-v1'}}))
            for owner, selected, excluded in [('bff', 'principle.bff-selected-browser-contract', 'principle.spa-selected-browser-contract'),
                    ('spa', 'principle.spa-selected-browser-contract', 'principle.bff-selected-browser-contract')]:
                path = 'src/' + owner + '/Owner.csproj'
                tags = context(root, feature, 'implementation', [path], prose_override='Implement ' + path)
                ids = {i for r in applicable_requirements(self.catalog, tags) for i in r['ruleIds']}
                self.assertIn(selected, ids)
                self.assertNotIn(excluded, ids, 'Neighboring accepted instances and root defaults cannot override actual task ownership')
            # A genuinely shared operation keeps both selected owner branches.
            tags = context(root, feature, 'implementation', [t['path'] for t in targets],
                prose_override=' '.join(t['path'] for t in targets))
            ids = {i for r in applicable_requirements(self.catalog, tags) for i in r['ruleIds']}
            self.assertTrue({'principle.bff-selected-browser-contract', 'principle.spa-selected-browser-contract'} <= ids)

    def test_unknown_dotnet_scope_preserves_complete_conditional_guidance_within_reviewed_bound(self):
        import phase_obligations as phase
        with FixtureDirectory() as name:
            root = Path(name); feature = root / 'specs/001-unknown'; feature.mkdir(parents=True)
            (feature / 'spec.md').write_text('C# pure policy in src/Core/Core.csproj.')
            (feature / 'plan.md').write_text('Use src/Core/Core.csproj; runtime ownership is not yet resolved.')
            project = root / 'src/Core/Core.csproj'; project.parent.mkdir(parents=True)
            project.write_text('<Project Sdk="Microsoft.NET.Sdk" />')
            value = phase.project(root, feature, 'planning')
            output = phase.render(value, 'planning')
            self.assertLess(len(output.encode('utf-8')), BRIEF_LIMITS['unknown-dotnet'])
            assert_complete_required_text(self, self.catalog, value['requirements'], output, ROOT / 'extensions')

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

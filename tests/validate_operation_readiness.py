"""Pre-code scoped blockers/recovery and current design references; no coding agent."""
from pathlib import Path
import shutil
import json
import sys
import unittest
from unittest.mock import patch

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import operation_readiness as readiness


class OperationReadinessTests(unittest.TestCase):
    def mixed_frontend_fixture(self, root):
        """Fictional authoring; actual package/source ownership is discovered."""
        import task_draft as tasks
        feature = root / 'specs/001-mixed'
        feature.mkdir(parents=True)
        for name, content in (
                ('static', 'export const title = "Policy";'),
                ('preview', 'export async function preview(file: File) { const bytes = await file.arrayBuffer(); const loading = getDocument(bytes); return await loading.promise; }')):
            owner = root / 'apps' / name
            owner.mkdir(parents=True)
            (owner / 'package.json').write_text(json.dumps({'name': name, 'devDependencies': {'typescript': '1.0.0-fictional'}}), encoding='utf-8')
            (owner / 'source.ts').write_text(content, encoding='utf-8')
        (feature / 'spec.md').write_text(tasks.POLICY + '\n# Two isolated views\nStatic title presentation and independently owned asynchronous document preview.\n', encoding='utf-8')
        rows = []
        for operation in ('static', 'preview'):
            rows.extend([
                (operation, 'ownership', 'The ' + operation + ' package owns its isolated view and public seam.'),
                (operation, 'results', 'Only the admitted view value is observable; failures retain the appropriate view state.'),
                (operation, 'limits', 'No applicable limits: this target-free synthetic routing fixture changes no actual behavioral ceiling.'),
                (operation, 'admission', 'The isolated view accepts the typed local contract and admits untrusted values at its entry.'),
            ])
        rows.extend([
            ('preview', 'cancellation-deadline', 'One preview deadline spans loading/rendering; cancellation signals the owned work and stale completions are discarded.'),
            ('preview', 'cleanup-uncertainty', 'The preview generation owns document loading/destruction from first acquisition through failure and uncertain completion.'),
            ('preview', 'bounds', 'The preview owner admits configured file/page work bounds before dispatch.'),
        ])
        (feature / 'plan.md').write_text(tasks.POLICY + '\n# Mixed plan\n\n## Design\nDistinct packages own distinct view effects.\n\n'
            '## Operation implementation map\n| Operation | Decision | Resolution | Source |\n|---|---|---|---|\n'
            + '\n'.join('| ' + ' | '.join((*row, 'plan.md#Design')) + ' |' for row in rows) + '\n', encoding='utf-8')
        (feature / 'tasks.md').write_text(tasks.POLICY + '''
# Mixed tasks
- [ ] T001 [US1] Update apps/static/source.ts
- [ ] T002 [US1] Update apps/preview/source.ts

## Operation dependency map
| Operation | Depends on operations |
|---|---|
| static | none |
| preview | none |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|---|---|---|---|---|
| T001 | static | none | none | none |
| T002 | preview | none | none | none |

## Story delivery map
| Story | Operations | Useful outcome | Independent walkthrough | Active minutes to review | Larger-story rationale |
|---|---|---|---|---|---|
| US1 | static, preview | Preserve isolated title and owned preview | Read title and operate preview separately | 60 | none |

## Operation implementation map
| Operation | Pattern / example | Compatibility / alternative | First adverse cases | Test owner / command | First coherent check |
|---|---|---|---|---|---|
| static | Pure title projection | Existing TypeScript package manual route | invalid input and immutable title | static package focused check owner | static compiler and view checks before expansion |
| preview | Owned document preview generation | Existing TypeScript package manual route | cancel during loading; late completion after disposal | preview package focused check owner | preview compiler and lifetime checks before expansion |
''', encoding='utf-8')
        return feature

    def test_mixed_frontend_decisions_and_independent_review_stay_with_actual_owner(self):
        from coding_context import prepare
        with FixtureDirectory(native=True) as directory:
            root = Path(directory)
            feature = self.mixed_frontend_fixture(root)
            static_expected = {'ownership', 'results', 'limits', 'admission'}
            preview_expected = static_expected | {'cancellation-deadline', 'cleanup-uncertainty', 'bounds'}
            expected = {'static': static_expected, 'preview': preview_expected}
            for label, scope, selected in (
                    ('static', {'task_ids': ['T001']}, {'static'}),
                    ('preview', {'task_ids': ['T002']}, {'preview'}),
                    ('mixed', {'task_ids': ['T001', 'T002']}, {'static', 'preview'}),
                    ('feature', {'feature_wide': True}, {'static', 'preview'})):
                with self.subTest(scope=label):
                    coding = prepare(root, feature, check_adoption=False, **scope)['coding']
                    self.assertTrue(coding['canProceed'], coding['blockers'])
                    brief = coding['operationBrief']
                    self.assertEqual('ready', brief['status'])
                    self.assertEqual(selected, {op['operation'] for op in brief['operations']})
                    for op in brief['operations']:
                        self.assertEqual(expected[op['operation']], set(op['requiredDecisions']))
                    if len(selected) == 2:
                        duties = {d['rule']: d for d in coding['evaluation']['duties']}
                        for rule in ('guidance.programming-guardrails.review-of-effects-and-test-boundaries', 'principle.ui-state-recovery'):
                            self.assertEqual(['T001', 'T002'], duties[rule]['taskIds'])
                            self.assertEqual(['T002'], duties[rule]['independentTaskIds'])
                        normal_ui = duties['guidance.ui-experience-v1.quality-and-evidence']
                        self.assertEqual(['T001', 'T002'], normal_ui['taskIds'])
                        self.assertEqual([], normal_ui['independentTaskIds'])
            plan = feature / 'plan.md'
            original = plan.read_bytes()
            plan.write_bytes(b'\n'.join(line for line in original.split(b'\n') if not line.startswith(b'| preview | cleanup-uncertainty |')))
            for scope in ({'task_ids': ['T001', 'T002']}, {'feature_wide': True}):
                brief = prepare(root, feature, check_adoption=False, **scope)['coding']['operationBrief']
                self.assertEqual('blocked', brief['status'])
                self.assertEqual({('preview', 'cleanup-uncertainty')}, {(b['operation'], b['decision']) for b in brief['blockers']})
                self.assertFalse(next(op for op in brief['operations'] if op['operation'] == 'static')['blockers'])
            self.assertTrue(prepare(root, feature, task_ids=['T001'], check_adoption=False)['coding']['canProceed'])

    def test_shared_frontend_repair_reuses_both_original_maps_in_either_owner_order(self):
        import task_draft as tasks
        import conformance_repair
        from coding_context import prepare
        expected = {'static': {'ownership', 'results', 'limits', 'admission'},
                    'preview': {'ownership', 'results', 'limits', 'admission', 'cancellation-deadline', 'cleanup-uncertainty', 'bounds'}}
        for operations in (['static', 'preview'], ['preview', 'static']):
            with self.subTest(first_owner=operations[0]), FixtureDirectory(native=True) as directory:
                root = Path(directory)
                feature = self.mixed_frontend_fixture(root)
                with patch.object(tasks, 'require_policy'):
                    tasks.transition(root, feature, {'action': 'initialize', 'baseline': 'fictional-original-baseline',
                        'source': 'Fictional mixed-source repair authoring; no real consumer or human acceptance'}, now=0)
                before = conformance_repair.operation_policies(root, feature, ['static', 'preview'])
                finding = {'id': 'shared-view-repair', 'rule': 'principle.ui-state-recovery',
                    'sourcePaths': ['apps/static/source.ts', 'apps/preview/source.ts'], 'operations': operations,
                    'repair': 'Repair existing isolated views while preserving original public results and owned preview lifetime',
                    'checks': 'focused static value and preview cancellation/lifetime checks', 'materialEffect': 'preserving'}
                tasks.transition(root, feature, {'action': 'conformance-register', 'findings': [finding]}, now=0)
                tasks.transition(root, feature, {'action': 'start', 'operation': operations[0], 'purpose': 'conformance'}, now=0)
                coding = prepare(root, feature, operation=operations[0], check_adoption=False)['coding']
                self.assertEqual(['T003'], coding['scope']['taskIds'])
                self.assertTrue(coding['canProceed'], coding['blockers'])
                self.assertEqual('ready', coding['operationBrief']['status'])
                self.assertEqual({'static', 'preview'}, {op['operation'] for op in coding['operationBrief']['operations']})
                for op in coding['operationBrief']['operations']:
                    self.assertEqual(expected[op['operation']], set(op['requiredDecisions']))
                self.assertEqual(before, conformance_repair.operation_policies(root, feature, ['static', 'preview']))
                plan = feature / 'plan.md'
                original = plan.read_bytes()
                plan.write_bytes(b'\n'.join(line for line in original.split(b'\n') if not line.startswith(b'| preview | cleanup-uncertainty |')))
                brief = prepare(root, feature, operation=operations[0], check_adoption=False)['coding']['operationBrief']
                self.assertEqual('blocked', brief['status'])
                self.assertEqual({('preview', 'cleanup-uncertainty')}, {(b['operation'], b['decision']) for b in brief['blockers']})
                self.assertFalse(next(op for op in brief['operations'] if op['operation'] == 'static')['blockers'])
                plan.write_bytes(original)

    def test_root_package_ownership_stops_at_nested_packages_and_ignores_unrelated_docs(self):
        from coding_context import prepare
        (self.root / 'package.json').write_text(json.dumps({'devDependencies': {'typescript': '5.9.3'}}))
        (self.root / 'client.ts').write_text('export const title = "Policy";')
        nested = self.root / 'packages/independent'
        nested.mkdir(parents=True)
        (nested / 'package.json').write_text(json.dumps({'devDependencies': {'typescript': '5.9.3'}}))
        (nested / 'effect.ts').write_text('export async function work() { await Promise.resolve(); }')
        target = self.feature / 'tasks.md'
        original = target.read_text()
        target.write_text(original.replace('Implement async provider upload in src/Upload.cs', 'Update client.ts'))
        value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
        self.assertEqual('package.json', value['frontendProjects'][0]['package']['path'])
        self.assertEqual(['client.ts'], value['frontendProjects'][0]['sources'])
        self.assertNotIn('browser-effects', value['responsibilities'])
        target.write_text(original.replace('Implement async provider upload in src/Upload.cs', 'Update README.md'))
        value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
        self.assertFalse(value['frontendProjects'])

    def test_actual_frontend_effects_in_nondefault_owner_cannot_shed_lifetime_decisions(self):
        from coding_context import prepare
        package = self.root / 'apps/client'
        package.mkdir(parents=True)
        (package / 'package.json').write_text(json.dumps({'devDependencies': {'typescript': '5.9.3'}}))
        (package / 'source.ts').write_text('export async function preview(file: File) { const bytes = await file.arrayBuffer(); return getDocument(bytes).promise; }')
        target = self.feature / 'tasks.md'
        target.write_text(target.read_text().replace('Implement async provider upload in src/Upload.cs', 'Implement preview in apps/client/source.ts'))
        self.plan_rows = [row for row in self.plan_rows if row[0] != 'upload' or row[1] in ('ownership', 'results', 'limits')]
        self.write_plan()
        value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
        self.assertIn('browser-effects', value['responsibilities'])
        missing = {row['decision'] for row in value['operationBrief']['blockers']}
        self.assertTrue({'cancellation-deadline', 'cleanup-uncertainty', 'bounds'} <= missing)
        self.assertTrue(any(row['independentReviewRequired'] for row in value['evaluation']['duties']))
        # A static view with no effectful source or intent retains its smaller scope.
        (package / 'source.ts').write_text('export const title = "Policy";')
        value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
        self.assertNotIn('browser-effects', value['responsibilities'])
        required = set(value['operationBrief']['operations'][0]['requiredDecisions'])
        self.assertFalse({'cancellation-deadline', 'cleanup-uncertainty', 'bounds'} & required)
        for relative in ('.specify/managed.ts', 'vendor/library.ts', 'source.generated.ts'):
            generated = package / relative
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_text('export async function generated() { await Promise.resolve(); }')
        value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
        self.assertNotIn('browser-effects', value['responsibilities'])
        self.assertEqual(['apps/client/source.ts'], value['frontendProjects'][0]['sources'])
        for source in ('export function work() { return Promise.resolve().then(x => x); }',
                       'export function work() { return setTimeout(() => 1, 100); }'):
            (package / 'source.ts').write_text(source)
            value = prepare(self.root, self.feature, task_ids=['T001'], check_adoption=False)['coding']
            self.assertIn('browser-effects', value['responsibilities'])

    def setUp(self):
        fixture = FixtureDirectory(prefix='operation-readiness-')
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name).resolve()
        self.feature = self.root / 'specs/001-documents'
        self.feature.mkdir(parents=True)
        self.plan_rows = [
            ('upload', 'ownership', 'Document application owns dispatch identity before the accounting await.'),
            ('upload', 'results', 'Completed requires admitted immutable observations; failures retain the remote locator.'),
            ('upload', 'limits', 'No applicable limits: this target-free ownership-edge fixture does not implement or alter a behavioral/resource ceiling.'),
            ('upload', 'cancellation-deadline', 'Caller token and shared operation deadline span dispatch, accounting and polling; stale results are discarded.'),
            ('upload', 'cleanup-uncertainty', 'Cleanup owner records the operation ID before accounting; accounting failure or cancellation triggers bounded cleanup and retains uncertain outcome.'),
            ('list', 'ownership', 'Catalog pure policy owns the in-memory title projection.'),
            ('list', 'results', 'An immutable ordered title list preserves existing public meaning.'),
            ('list', 'limits', 'No applicable limits: this pure representation repair introduces no policy or work ceiling.'),
        ]
        self.write_plan()
        self.write_tasks()

    def write_plan(self):
        (self.feature / 'plan.md').write_text('# Document plan\n\n## Design\nCurrent agreed design.\n\n'
            '## Operation implementation map\n\n| ' + ' | '.join(readiness.PLAN_COLUMNS) + ' |\n'
            '|---|---|---|---|\n' + '\n'.join('| ' + ' | '.join((*row, 'plan.md#Design')) + ' |' for row in self.plan_rows)
            + '\n', encoding='utf-8')

    def write_tasks(self):
        (self.feature / 'tasks.md').write_text(
            '# Tasks\n- [ ] T001 [US1] Implement async provider upload in src/Upload.cs\n'
            '- [ ] T002 [US2] Implement pure title projection in src/Titles.cs\n\n'
            '## Task dependency map\n| Task | Operation | Depends on tasks | Requires | Provides |\n'
            '|---|---|---|---|---|\n| T001 | upload | none | none | none |\n| T002 | list | none | none | none |\n\n'
            '## Operation implementation map\n| ' + ' | '.join(readiness.TASK_COLUMNS) + ' |\n'
            '|---|---|---|---|---|---|\n'
            '| upload | owned-provider example | selected profile with recording transport; preserve cleanup around accounting | cancel during accounting; accounting failure after dispatch | tests/Document.Tests.csproj with dotnet test --filter Upload | dotnet build src/Documents.csproj with selected analyzers, then focused Upload tests before expansion |\n'
            '| list | manual-edit pure projection | immutable Core pattern; no runtime effects | mutation attempt and empty list | tests/Core.Tests.csproj with dotnet test --filter Titles | dotnet build src/Core.csproj with analyzers, then focused Titles tests before expansion |\n', encoding='utf-8')

    def scope(self, operation='upload'):
        task = 'T001' if operation == 'upload' else 'T002'
        lines = [line for line in (self.feature / 'tasks.md').read_text(encoding='utf-8').splitlines()
                 if line.startswith('- [ ] ' + task)]
        return {'operation': operation, 'taskIds': [task], 'tasks': lines}

    def inspect(self, operation='upload', stage='source'):
        tags = {'dotnet', 'source-production', 'dotnet-async', 'dotnet-lifetime'} if operation == 'upload' else {'dotnet', 'source-production'}
        return readiness.inspect(self.root, self.feature, self.scope(operation), tags, stage)

    def test_concrete_ocr_edge_is_in_the_brief_before_editing(self):
        result = self.inspect()
        self.assertEqual('ready', result['status'])
        operation = result['operations'][0]
        self.assertEqual({'ownership', 'results', 'limits', 'cancellation-deadline', 'cleanup-uncertainty'}, set(operation['requiredDecisions']))
        cleanup = next(d for d in operation['decisions'] if d['decision'] == 'cleanup-uncertainty')
        self.assertIn('accounting failure', cleanup['resolution'])
        self.assertIn('cancel during accounting', operation['implementation']['adverseCases'])
        self.assertEqual('specs/001-documents/plan.md', operation['decisions'][0]['source']['path'])
        self.assertIn('semantic review', result['limits'])

    def test_missing_cleanup_blocks_only_affected_operation_and_has_recovery(self):
        self.plan_rows = [row for row in self.plan_rows if row[1] != 'cleanup-uncertainty']
        self.write_plan()
        result = self.inspect()
        self.assertEqual('blocked', result['status'])
        blocker = next(b for b in result['blockers'] if b['decision'] == 'cleanup-uncertainty')
        self.assertEqual('upload', blocker['operation'])
        for key in ('owner', 'condition', 'missingFact', 'consequence', 'repair', 'askUserWhen', 'artifactUpdates', 'retry'):
            self.assertTrue(blocker[key], key)
        self.assertEqual({'accessible-fact', 'human-decision', 'stale-input', 'engine-gap', 'environment'}, set(result['recovery']))
        self.assertEqual('ready', self.inspect('list')['status'])
        self.assertEqual('setup-only', self.inspect(stage='setup')['status'])

    def test_placeholder_and_stale_or_escaping_source_do_not_establish_readiness(self):
        path = self.feature / 'plan.md'
        original = path.read_text(encoding='utf-8')
        for replacement in ('TBD', 'Not applicable: none'):
            path.write_text(original.replace(self.plan_rows[0][2], replacement), encoding='utf-8')
            self.assertEqual('blocked', self.inspect()['status'])
        for reference in ('plan.md#Missing', '../outside.md', 'https://example.test/design'):
            path.write_text(original.replace('plan.md#Design', reference), encoding='utf-8')
            self.assertEqual('blocked', self.inspect()['status'])
        path.write_text(original, encoding='utf-8')
        before = self.inspect()['operations'][0]['decisions'][0]['source']['sha256']
        path.write_text(original.replace('Current agreed design.', 'Current revised design.'), encoding='utf-8')
        self.assertNotEqual(before, self.inspect()['operations'][0]['decisions'][0]['source']['sha256'])

    def test_duplicate_or_generic_implementation_row_rejected_without_source_mutation(self):
        path = self.feature / 'tasks.md'
        original = path.read_bytes()
        path.write_bytes(original.replace(b'cancel during accounting; accounting failure after dispatch', b'follow guidance'))
        self.assertEqual('blocked', self.inspect()['status'])
        self.assertEqual(original.replace(b'cancel during accounting; accounting failure after dispatch', b'follow guidance'), path.read_bytes())
        path.write_bytes(original + original[original.index(b'| upload | owned-provider'):].splitlines()[0] + b'\n')
        self.assertEqual('blocked', self.inspect()['status'])

    def test_feature_scope_cannot_shed_actual_source_lifetime_on_vague_tasks(self):
        from feature_context import context
        project = self.root / 'src/Documents/Documents.csproj'
        project.parent.mkdir(parents=True)
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"/>', encoding='utf-8')
        source = project.parent / 'DocumentParser.cs'
        source.write_text('class DocumentParser : System.IDisposable { async System.Threading.Tasks.Task Parse() { await ParsePdfPig(); } }', encoding='utf-8')
        tasks = (self.feature / 'tasks.md').read_text(encoding='utf-8')
        (self.feature / 'tasks.md').write_text(tasks.replace('Implement async provider upload', 'Implement change'), encoding='utf-8')
        scope = {'operation': None, 'taskIds': ['T001', 'T002'], 'tasks': self.scope()['tasks'] + self.scope('list')['tasks']}
        tags = context(self.root, self.feature, 'implementation',
                       ['src/Documents/DocumentParser.cs'], prose_override='src/Documents/Documents.csproj')
        self.assertIn('dotnet-lifetime', tags)
        result = readiness.inspect(self.root, self.feature, scope, tags | {'source-production'}, 'source')
        self.assertEqual('blocked', result['status'])
        pure = next(row for row in result['operations'] if row['operation'] == 'list')
        self.assertIn('cleanup-uncertainty', pure['requiredDecisions'])
        self.assertIn('cancellation-deadline', pure['requiredDecisions'])
        # Explicit unrelated operation preparation retains its own actual tags;
        # a feature union never supplies a reason to drop observed source duties.
        self.assertEqual('ready', self.inspect('list')['status'])

    def test_decisions_use_the_same_requirement_selection_as_guidance(self):
        from feature_context import applicable_requirements
        from phase_obligations import catalog
        tags = {'dotnet', 'source-production', 'dotnet-async', 'dotnet-lifetime'}
        obligations = applicable_requirements(catalog(), tags, 'implementation')
        expected = {decision for row in obligations for decision in row.get('operationDecisions', [])}
        self.assertEqual(expected, set(self.inspect()['operations'][0]['requiredDecisions']))

    def test_small_formatting_repair_uses_existing_decisions_without_human_approval(self):
        result = self.inspect('list')
        self.assertEqual('ready', result['status'])
        self.assertFalse(result['blockers'])
        self.assertEqual(['limits', 'ownership', 'results'], result['operations'][0]['requiredDecisions'])

    def test_legacy_missing_maps_cannot_silently_pass_source_entry(self):
        (self.feature / 'plan.md').write_text('Existing plan.', encoding='utf-8')
        (self.feature / 'tasks.md').write_text('- [ ] T001 Implement src/Core.cs', encoding='utf-8')
        result = readiness.inspect(self.root, self.feature,
                                   {'operation': None, 'taskIds': ['T001'], 'tasks': ['- [ ] T001 Implement src/Core.cs']},
                                   {'dotnet', 'source-production'}, 'source')
        self.assertEqual('blocked', result['status'])
        self.assertIn('exactly one Operation implementation map', result['blockers'][0]['missingFact'])

    def test_legacy_preparation_preserves_unknown_source_duties_and_setup(self):
        from coding_context import prepare
        package = self.root / 'apps/legacy'
        package.mkdir(parents=True)
        (package / 'package.json').write_text(json.dumps({'devDependencies': {'typescript': '5.9.3'}}))
        (package / 'source.ts').write_text('export async function preview(file: File) { return await file.arrayBuffer(); }')
        (self.feature / 'tasks.md').write_text('- [ ] T001 Update apps/legacy/source.ts\n', encoding='utf-8')
        (self.feature / 'plan.md').write_text('Legacy plan without current operation maps.\n', encoding='utf-8')
        source = prepare(self.root, self.feature, check_adoption=False)['coding']
        self.assertIn('browser-effects', source['responsibilities'])
        self.assertEqual('blocked', source['operationBrief']['status'])
        operation = source['operationBrief']['operations'][0]
        self.assertEqual('feature', operation['operation'])
        self.assertTrue({'cancellation-deadline', 'cleanup-uncertainty', 'bounds'} <= set(operation['requiredDecisions']))
        self.assertTrue(any(d['independentTaskIds'] == ['T001'] for d in source['evaluation']['duties']))
        setup = prepare(self.root, self.feature, stage='setup', check_adoption=False)['coding']
        self.assertEqual('setup-only', setup['operationBrief']['status'])

    def test_conditional_nonapplicability_is_visible_for_review(self):
        self.plan_rows.append(('upload', 'bounds', 'Not applicable: this operation transports already admitted immutable observations and performs no parsing or enumeration.'))
        self.write_plan()
        result = self.inspect()
        self.assertEqual('ready', result['status'])
        self.assertTrue(next(d for d in result['operations'][0]['decisions'] if d['decision'] == 'bounds')['nonapplicableClaim'])

    def limit_policy(self, classification='configurable-policy'):
        fields = {
            'meaning': 'maximum admitted caption length', 'units': 'Unicode code points',
            'owner': 'Caption application owner', 'classification': classification,
            'value': '48 default' if classification == 'configurable-policy' else '64 fixed ceiling',
            'basis': 'existing caption policy in Design', 'enforcement': 'typed admission and pure validation',
            'validation': 'invalid/default/nondefault and exact-boundary cases',
        }
        if classification == 'configurable-policy':
            fields.update(setting='Caption.MaxLength', **{'default-basis': 'existing policy default of 48'},
                          lifecycle='validated immutable activation snapshot', consumers='API admission, pure Core and client contract')
        return fields

    def add_limit(self, operation='upload', classification='configurable-policy'):
        self.plan_rows = [row for row in self.plan_rows if not (row[0] == operation and row[1] == 'limits')]
        self.plan_rows.extend([(operation, 'limits', 'Limits: caption-length'),
                              (operation, 'limit:caption-length', '; '.join(key + '=' + value for key, value in self.limit_policy(classification).items()))])
        self.write_plan()
        plan = self.feature / 'plan.md'
        plan.write_text(plan.read_text(encoding='utf-8').replace('Current agreed design.',
            'Current agreed design. Fictional accepted caption policy: the application owner uses a configurable maximum of 48 Unicode code points by default, validated at activation and enforced at all consumers. The independent fixed wire ceiling is 64 code points; the fictional engineering owner also chooses a 64-item work cap for bounded memory. These are simulated test decisions, not inferred from source or human acceptance.'), encoding='utf-8')

    def test_each_limit_needs_classified_authority_and_configured_consumption_before_coding(self):
        for classification in readiness.LIMIT_CLASSES:
            with self.subTest(classification=classification):
                self.add_limit(classification=classification)
                result = self.inspect()
                self.assertEqual('ready', result['status'], result['blockers'])
                limit = result['operations'][0]['limits']['items'][0]
                self.assertEqual(classification, limit['classification'])
                self.assertEqual('caption-length', limit['id'])
                self.assertEqual('Design', limit['source']['heading'])
                self.plan_rows = [row for row in self.plan_rows if not row[1].startswith('limit:')]
        # The same local id in another operation has a distinct policy and scope.
        self.add_limit('list', 'engineering-safeguard')
        self.add_limit()
        self.assertEqual('configurable-policy', self.inspect()['operations'][0]['limits']['items'][0]['classification'])
        self.assertEqual('engineering-safeguard', self.inspect('list')['operations'][0]['limits']['items'][0]['classification'])

    def test_generic_bounds_cannot_replace_inventory_and_every_limit_field_is_due(self):
        self.plan_rows = [row for row in self.plan_rows if row[:2] != ('upload', 'limits')]
        self.plan_rows.append(('upload', 'bounds', 'The operation owner chooses sensible configured bounds.'))
        self.write_plan()
        result = self.inspect()
        self.assertEqual('blocked', result['status'])
        self.assertIn('limits', {finding['decision'] for finding in result['blockers']})
        self.assertEqual('ready', self.inspect('list')['status'])
        self.add_limit()
        original = (self.feature / 'plan.md').read_text(encoding='utf-8')
        fields = self.limit_policy()
        for field, value in fields.items():
            with self.subTest(field=field):
                text = original.replace(field + '=' + value, field + '=TBD')
                (self.feature / 'plan.md').write_text(text, encoding='utf-8')
                self.assertEqual('blocked', self.inspect()['status'])
        for replacement in ('Limits: caption-length, caption-length', 'Limits: missing-id', 'No applicable limits: none', 'No applicable limits: not applicable', 'No applicable limits: no applicable limits'):
            (self.feature / 'plan.md').write_text(original.replace('Limits: caption-length', replacement), encoding='utf-8')
            self.assertEqual('blocked', self.inspect()['status'])
        for observed in ('existing implementation', 'current constant'):
            (self.feature / 'plan.md').write_text(original.replace(fields['default-basis'], observed), encoding='utf-8')
            self.assertEqual('blocked', self.inspect()['status'])
        for reference in ('plan.md', 'plan.md#Operation implementation map', 'plan.md#Absent', 'https://example.test/policy'):
            text = original.replace('| limit:caption-length | ' + '; '.join(key + '=' + value for key, value in fields.items()) + ' | plan.md#Design |',
                                    '| limit:caption-length | ' + '; '.join(key + '=' + value for key, value in fields.items()) + ' | ' + reference + ' |')
            (self.feature / 'plan.md').write_text(text, encoding='utf-8')
            self.assertEqual('blocked', self.inspect()['status'], reference)
        (self.feature / 'plan.md').write_text(original, encoding='utf-8')
        with (self.feature / 'plan.md').open('a', encoding='utf-8') as stream:
            stream.write(next(line for line in original.splitlines() if '| limit:caption-length |' in line) + '\n')
        self.assertEqual('blocked', self.inspect()['status'])

    def test_pure_manual_non_dotnet_operation_has_same_inventory_requirement(self):
        tags = {'source-production'}
        good = readiness.inspect(self.root, self.feature, self.scope('list'), tags)
        self.assertEqual('ready', good['status'])
        self.assertEqual([], good['operations'][0]['limits']['inventory'])
        self.plan_rows = [row for row in self.plan_rows if row[:2] != ('list', 'limits')]
        self.write_plan()
        blocked = readiness.inspect(self.root, self.feature, self.scope('list'), tags)
        self.assertEqual('blocked', blocked['status'])
        self.assertEqual('PKC020', blocked['blockers'][0]['code'])
        self.assertIn('spec.md/clarifications only when product meaning changes', blocked['blockers'][0]['artifactUpdates'])
        self.assertEqual('setup-only', readiness.inspect(self.root, self.feature, self.scope('list'), tags, 'setup')['status'])

    def test_installed_helper_uses_existing_local_artifacts(self):
        installed = self.root / '.specify/extensions/program-kit-governance/scripts'
        installed.mkdir(parents=True)
        shutil.copy(ROOT / 'extensions/program-kit-governance/scripts/operation_readiness.py', installed)
        import importlib.util
        module = importlib.util.spec_from_file_location('installed_operation_readiness', installed / 'operation_readiness.py')
        loaded = importlib.util.module_from_spec(module)
        module.loader.exec_module(loaded)
        self.assertEqual('ready', loaded.inspect(self.root, self.feature, self.scope(),
                                               {'dotnet', 'source-production', 'dotnet-async', 'dotnet-lifetime'}, 'source')['status'])


if __name__ == '__main__':
    unittest.main()

"""Task drafting contracts and negative controls; never starts a coding agent."""
from pathlib import Path
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import phase_obligations as context
import task_draft as draft


def validate_sections(catalog):
    for rule in catalog['requirements']:
        if set(rule['sources']) != set(rule.get('sections', {})):
            raise ValueError('Every source needs a focused section: ' + rule['id'])
        for source, sections in rule['sections'].items():
            text = (ROOT / 'extensions' / source).read_text(encoding='utf-8')
            headings = set(re.findall(r'^#{1,2} (.+)$', text, re.M))
            if not sections or not set(sections) <= headings:
                raise ValueError('Missing focused heading: ' + source)


def validate_installed_workflow(project):
    """Called by the real archive-install validator, using its disposable consumer."""
    import yaml
    hooks = yaml.safe_load((project / '.specify/extensions.yml').read_text(encoding='utf-8'))['hooks']
    for event, commands in {'before_tasks': ['speckit.program-kit-governance.phase-context'],
                            'after_tasks': ['speckit.program-kit-governance.architecture-check', 'speckit.analyze'],
                            'before_implement': ['speckit.program-kit-governance.implementation-check']}.items():
        selected = [h for h in hooks[event] if h.get('extension') == 'program-kit-governance']
        if [h['command'] for h in selected] != commands or any(h.get('optional') is not False or
                h.get('enabled') is not True or h.get('condition') is not None for h in selected):
            raise AssertionError('Installed tasks hooks must be mandatory and ordered: ' + event)
    skills = project / '.agents/skills'
    phase = (skills / 'speckit-program-kit-governance-phase-context/SKILL.md').read_text(encoding='utf-8')
    tasks = (skills / 'speckit-tasks/SKILL.md').read_text(encoding='utf-8')
    analyze = (skills / 'speckit-analyze/SKILL.md').read_text(encoding='utf-8')
    for marker in ('--phase tasks', 'task_draft.py prepare', 'task_draft.py save-phase',
                   'task_draft.py finalize', 'Do not invoke analyze on an incomplete draft'):
        if marker not in phase:
            raise AssertionError('Installed phase-context lost draft protocol: ' + marker)
    for marker in ('hooks.before_tasks', 'hooks.after_tasks', 'MUST actually invoke the hook'):
        if marker not in tasks:
            raise AssertionError('Installed tasks command lost hook dispatch: ' + marker)
    for marker in ('operation-sized', 'task_draft.py', 'exact prerequisite', 'STRICTLY READ-ONLY'):
        if marker.lower() not in tasks.lower():
            raise AssertionError('Installed tasks command lost operation planning: ' + marker)
    for obsolete in ('Tests → Models → Services → Endpoints → Integration',
                     'Foundational tasks (blocking prerequisites for all user stories)'):
        if obsolete in tasks:
            raise AssertionError('Installed tasks retained conflicting layer-first instructions')
    if 'STRICTLY READ-ONLY' not in analyze or 'complete `tasks.md`' not in analyze:
        raise AssertionError('Installed analyze must wait for complete tasks and remain read-only')
    implement = (skills / 'speckit-implement/SKILL.md').read_text(encoding='utf-8')
    for marker in ('hooks.before_implement', 'hooks.after_implement', 'MUST actually invoke the hook',
                   '-Scope Focused', '-Scope Affected', 'finish --handoff', 'reuse', 'not full acceptance'):
        if marker.lower() not in implement.lower():
            raise AssertionError('Installed implement lost focused execution/handoff semantics: ' + marker)
    if 'Common Patterns by Technology' in implement or 'Read research.md for technical decisions' in implement:
        raise AssertionError('The installed command appended to the broad core body instead of replacing it')
    spec_root = project / 'specs'
    spec_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='999-task-resume-', dir=spec_root) as directory:
        feature = Path(directory)
        for name in ('spec.md', 'plan.md'):
            (feature / name).write_text('Owned cut-list calculation with one user story.', encoding='utf-8')
        environment = {**os.environ, 'SPECIFY_FEATURE_DIRECTORY': feature.relative_to(project).as_posix()}
        def run(script, *arguments):
            result = subprocess.run([sys.executable, '-X', 'utf8', str(script), *arguments], cwd=project,
                                    env=environment, capture_output=True, text=True, encoding='utf-8')
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            return result.stdout
        setup = json.loads(run(project / '.specify/scripts/python/setup_tasks.py', '--json'))
        if Path(setup['FEATURE_DIR']).resolve() != feature.resolve():
            raise AssertionError('Installed setup_tasks selected the wrong feature')
        if '## Incremental task generation' not in setup['TASKS_TEMPLATE_CONTENT']:
            raise AssertionError('Installed setup_tasks omitted the composed drafting guidance')
        template = setup['TASKS_TEMPLATE_CONTENT']
        for marker in ('## Operation dependency map', '## Task dependency map', 'first operation',
                       'authorization', 'real-provider'):
            if marker not in template:
                raise AssertionError('Installed tasks template lost scoped graph: ' + marker)
        for obsolete in ('BLOCKS all user stories', 'Foundational (Blocking Prerequisites)',
                         'User story work can only begin after'):
            if obsolete in template:
                raise AssertionError('Installed resolver appended rather than replaced tasks template')
        guidance = run(project / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py',
                       'project', '--feature-dir', feature.relative_to(project).as_posix(), '--phase', 'tasks')
        if len(guidance.encode('utf-8')) >= 24000 or 'not a reading checklist' not in guidance:
            raise AssertionError('Installed before_tasks context lost bounded guidance')
        helper = project / '.specify/extensions/program-kit-governance/scripts/task_draft.py'
        arguments = ('--feature-dir', feature.relative_to(project).as_posix())
        run(helper, 'prepare', *arguments, '--phases', 'setup', 'US1')
        body = project / 'artifacts/task-resume-phase.md'
        body.parent.mkdir(exist_ok=True)
        body.write_text('## Setup\n- [ ] T001 Preserve exact profile in eng/Directory.Packages.props\n', encoding='utf-8')
        run(helper, 'save-phase', *arguments, '--phase', 'setup', '--content-file', str(body))
        saved = (feature / 'tasks.md').read_bytes()
        resumed = json.loads(run(helper, 'prepare', *arguments))
        if resumed['remainingPhases'] != ['US1'] or (feature / 'tasks.md').read_bytes() != saved:
            raise AssertionError('Installed helper lost or rewrote interrupted drafting progress')
        progress = json.loads(run(project / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py',
                                  'finish', *arguments))
        if progress['status'] != 'in-progress' or progress['acceptanceEstablished']:
            raise AssertionError('A partial installed implementation checkpoint claimed acceptance')
        state_file = project / 'artifacts/task-current.json'
        state_file.write_text(json.dumps({'baseline': 'initial-commit', 'outcome': 'Create cut list',
                                         'next': 'Implement owned persistence', 'taskIds': ['T001'],
                                         'failures': ['provider test failing: artifacts/provider.trx']}), encoding='utf-8')
        run(helper, 'checkpoint', *arguments, '--content-file', str(state_file))
        for _ in range(4):
            run(helper, 'prepare', *arguments)
            run(helper, 'checkpoint', *arguments, '--content-file', str(state_file))
        retained = json.loads(run(helper, 'current', *arguments))
        if retained['failures'] != ['provider test failing: artifacts/provider.trx']:
            raise AssertionError('Installed checkpoint lost the unresolved provider failure on resume')
        if (feature / 'tasks.md').read_text(encoding='utf-8').count('program-kit:current-checkpoint') != 1:
            raise AssertionError('Installed current checkpoint accumulated a journal')
        body.write_text('''## US1 create
- [ ] T002 [US1] Test owned creation in tests/Create.cs

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| create | none |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | create | none | none | exact-profile |
| T002 | create | T001 | exact-profile | none |
''', encoding='utf-8')
        run(helper, 'save-phase', *arguments, '--phase', 'US1', '--content-file', str(body))
        finalized = json.loads(run(helper, 'finalize', *arguments))
        if finalized['status'] != 'complete' or finalized['implementationExecuted']:
            raise AssertionError('Installed operation graph finalization claimed execution')


def operation_fixture():
    """RM-01-like: independent owned create/list, upload storage and later admitted OCR."""
    return '''# Tasks: Owned policies
- [ ] T001 [US1] Prove authorization in tests/Authorization.cs
- [ ] T002 [US1] Test create policy in tests/Create.cs
- [ ] T003 [US1] Implement create policy in src/Create.cs
- [ ] T004 [US1] Test owned list in tests/List.cs
- [ ] T005 [US1] Implement list in src/List.cs
- [ ] T006 [US2] Prove upload storage/provider in tests/Storage.cs
- [ ] T007 [US2] Test upload in tests/Upload.cs
- [ ] T008 [US2] Implement upload in src/Upload.cs
- [ ] T009 [US2] Admit OCR provider in tests/OcrAdmission.cs
- [ ] T010 [US2] Test processing in tests/Processing.cs
- [ ] T011 [US2] Implement processing in src/Processing.cs

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| create | none |
| list | create |
| upload | create |
| process | upload |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | create | none | none | authorization, ownership |
| T002 | create | T001 | authorization, ownership | none |
| T003 | create | T002 | authorization, ownership | none |
| T004 | list | T003 | authorization, ownership | none |
| T005 | list | T004 | authorization, ownership | none |
| T006 | upload | T003 | authorization, ownership | storage, real-provider |
| T007 | upload | T006 | authorization, ownership, storage, real-provider | none |
| T008 | upload | T007 | authorization, ownership, storage, real-provider | none |
| T009 | process | T008 | storage, real-provider | ocr-admission |
| T010 | process | T009 | authorization, ownership, storage, real-provider, ocr-admission | none |
| T011 | process | T010 | authorization, ownership, storage, real-provider, ocr-admission | none |
'''


class TaskTests(unittest.TestCase):
    def test_draft_inputs_track_latest_actual_foundation_outcome_without_execution(self):
        runs = self.root/'artifacts/tests/runs'
        ready=runs/'foundation-z/result.json'; ready.parent.mkdir(parents=True)
        failed=runs/'foundation-a/result.json'; failed.parent.mkdir(parents=True)
        ready.write_text(json.dumps({'startedAtUtc':'2026-10-10T01:00:00Z','status':'ready'}))
        failed.write_text(json.dumps({'startedAtUtc':'2026-10-10T02:00:00Z','status':'failed'}))
        with patch.object(subprocess, 'run', side_effect=AssertionError('Draft snapshot may not run setup')):
            observed=draft.inputs(self.root,self.feature)
        self.assertIn(failed.relative_to(self.root).as_posix(),observed)
        self.assertNotIn(ready.relative_to(self.root).as_posix(),observed)
        previous=observed[failed.relative_to(self.root).as_posix()]
        failed.write_text(json.dumps({'startedAtUtc':'2026-10-10T02:00:00Z','status':'interrupted'}))
        self.assertNotEqual(previous,draft.inputs(self.root,self.feature)[failed.relative_to(self.root).as_posix()])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='task-drafting-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.feature = self.root / 'specs/002-cut-list'
        self.feature.mkdir(parents=True)
        (self.feature / 'spec.md').write_text('US1: generate cut lists. US2: export results.', encoding='utf-8')
        (self.feature / 'plan.md').write_text('C# API browser with owned PostgreSQL persistence and Foundation capability.', encoding='utf-8')
        self.phases = ['setup', 'foundation', 'US1', 'US2', 'polish', 'dependencies']

    def test_every_context_source_has_valid_focused_sections(self):
        validate_sections(context.catalog())
        invalid = copy.deepcopy(context.catalog())
        invalid['requirements'][0]['sections'].clear()
        with self.assertRaisesRegex(ValueError, 'focused section'):
            validate_sections(invalid)
        invalid = copy.deepcopy(context.catalog())
        source = invalid['requirements'][0]['sources'][0]
        invalid['requirements'][0]['sections'][source] = ['Nonexistent heading']
        with self.assertRaisesRegex(ValueError, 'Missing focused heading'):
            validate_sections(invalid)

    def test_scoped_graph_preserves_gates_and_rejects_unrelated_future_prerequisites(self):
        body = operation_fixture()
        self.assertTrue(draft.validate_operation_graph(body))
        for dependency in ('T008', 'T009', 'T011'):
            with self.subTest(dependency=dependency), self.assertRaisesRegex(ValueError, 'cross-operation|Cyclic'):
                draft.validate_operation_graph(body.replace('| T002 | create | T001 |',
                                                           f'| T002 | create | T001, {dependency} |'))
        for gate in ('authorization', 'ownership', 'storage', 'real-provider', 'ocr-admission'):
            # Removing its establishing task declaration cannot unblock its consumers.
            lines = body.splitlines()
            for n, line in enumerate(lines):
                if line.startswith('| T'):
                    cells = line.split('|')
                    provides = [v.strip() for v in cells[5].split(',') if v.strip() != gate]
                    cells[5] = ' ' + (', '.join(provides) or 'none') + ' '
                    lines[n] = '|'.join(cells)
            with self.subTest(gate=gate), self.assertRaisesRegex(ValueError, 'Missing prerequisite gates'):
                draft.validate_operation_graph('\n'.join(lines))

    def test_operation_graph_rejects_cycles_unknown_rows_and_missing_tasks(self):
        body = operation_fixture()
        for damaged, error in (
                (body.replace('| create | none |', '| create | process |'), 'Cyclic'),
                (body.replace('| T003 | create | T002 |', '| T003 | create | T099 |'), 'Unknown'),
                (body.replace('- [ ] T005', '- [ ] T095'), 'exactly one'),
                (body.replace('| T009 | process | T008 |', '| T009 | invented | T008 |'), 'Invalid task')):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                draft.validate_operation_graph(damaged)
        self.assertFalse(draft.validate_operation_graph('# Existing approved graph\n- [X] T001 Keep src/Owned.cs'))

    def test_new_operation_draft_finalization_checks_graph_without_claiming_execution(self):
        draft.prepare(self.root, self.feature, ['operations'])
        draft.save_phase(self.root, self.feature, 'operations', operation_fixture())
        self.assertFalse(draft.finalize(self.root, self.feature)['implementationExecuted'])

    def test_new_draft_requires_maps_while_legacy_drafts_remain_read_only_compatible(self):
        draft.prepare(self.root, self.feature, ['US1_create'])
        draft.save_phase(self.root, self.feature, 'US1_create', '## Create\n- [ ] T001 Create src/Policy.cs')
        saved = (self.feature / 'tasks.md').read_bytes()
        with self.assertRaisesRegex(ValueError, 'requires Operation dependency map'):
            draft.finalize(self.root, self.feature)
        self.assertEqual(saved, (self.feature / 'tasks.md').read_bytes())
        content, state = draft.load(self.feature / 'tasks.md')
        state['version'] = 1
        state.pop('format')
        draft.store(self.feature / 'tasks.md', content, state)
        retained = (self.feature / 'tasks.md').read_bytes()
        self.assertEqual('draft', draft.prepare(self.root, self.feature, None)['status'])
        self.assertEqual(retained, (self.feature / 'tasks.md').read_bytes())
        self.assertFalse(draft.finalize(self.root, self.feature)['implementationExecuted'])

    def test_checkpoint_many_resumes_replace_current_state_preserve_failures_and_task_plan(self):
        path = self.feature / 'tasks.md'
        plan = operation_fixture().replace('- [ ] T001', '- [X] T001') + '\nConsumer decision: keep ownership boundary.\n'
        path.write_text(plan, encoding='utf-8')
        initial = {'baseline': 'original-commit', 'outcome': 'Create policy', 'next': 'Implement create',
                   'taskIds': ['T002', 'T003'], 'checks': ['red: artifacts/create.trx'],
                   'decisions': ['plan.md#Ownership'], 'failures': ['owned-create failing: artifacts/create.trx']}
        draft.checkpoint(self.feature, initial)
        first_size = path.stat().st_size
        for n in range(60):
            draft.prepare(self.root, self.feature, None)
            draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Create policy',
                                           'next': f'Repair owned create case {n}'})
        current = draft.current(self.feature)
        self.assertEqual(initial['failures'], current['failures'])
        self.assertEqual(initial['checks'], current['checks'])
        self.assertEqual(initial['decisions'], current['decisions'])
        self.assertEqual(initial['taskIds'], current['taskIds'])
        content = path.read_text(encoding='utf-8')
        self.assertTrue(content.startswith(plan.rstrip()))
        self.assertEqual(1, content.count('program-kit:current-checkpoint'))
        self.assertLess(path.stat().st_size, first_size + 80)
        progress = context.finish(self.root, self.feature)
        self.assertFalse(progress['acceptanceEstablished'])
        self.assertEqual(current, progress['currentCheckpoint'])
        fixed = draft.checkpoint(self.feature, {'baseline': 'original-commit', 'outcome': 'Create policy',
            'next': 'Owned list', 'checks': ['green: artifacts/create-fixed.trx'],
            'resolvedFailures': initial['failures']})
        self.assertEqual([], fixed['failures'])
        self.assertEqual(['green: artifacts/create-fixed.trx'], fixed['checks'])

    def test_checkpoint_rejects_lossy_invalid_or_failed_updates_atomically(self):
        path = self.feature / 'tasks.md'
        path.write_text(operation_fixture(), encoding='utf-8')
        valid = {'baseline': 'original', 'outcome': 'Create', 'next': 'Fix', 'failures': ['create failed']}
        draft.checkpoint(self.feature, valid)
        saved = path.read_bytes()
        for invalid, error in (({**valid, 'baseline': 'new'}, 'baseline'),
                               ({**valid, 'taskIds': ['T999']}, 'existing task'),
                               ({**valid, 'next': 'x' * 9000}, '8192'),
                               ({**valid, 'resolvedFailures': ['other']}, 'retained failure'),
                               ({**valid, 'resolvedFailures': ['create failed']}, 'successful check'),
                               ({**valid, 'outcome': 'bad --> marker'}, '8192')):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                draft.checkpoint(self.feature, invalid)
            self.assertEqual(saved, path.read_bytes())
        with patch.object(draft.os, 'replace', side_effect=OSError('Interrupted checkpoint')):
            with self.assertRaisesRegex(OSError, 'Interrupted checkpoint'):
                draft.checkpoint(self.feature, {**valid, 'next': 'Continue'})
        self.assertEqual(saved, path.read_bytes())
        self.assertEqual([], list(self.feature.glob('.tasks-*.tmp')))

    def test_duplicate_or_malformed_checkpoint_preserves_retained_state(self):
        path = self.feature / 'tasks.md'
        valid = {'baseline': 'original', 'outcome': 'Create', 'next': 'Fix', 'failures': ['create failed']}
        for marker in ('<!-- program-kit:current-checkpoint {"version":1} -->',
                       '<!-- program-kit:current-checkpoint malformed',
                       '<!-- program-kit:current-checkpoint [] -->'):
            path.write_text(operation_fixture() + '\n' + marker + '\n', encoding='utf-8')
            saved = path.read_bytes()
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError, 'checkpoint'):
                draft.checkpoint(self.feature, valid)
            self.assertEqual(saved, path.read_bytes())
    def test_context_is_bounded_phase_scoped_and_keeps_required_checks(self):
        value = context.project(self.root, self.feature, 'after-plan')
        output = context.render(value, 'after-plan')
        self.assertLess(len(output.encode('utf-8')), 24000)
        self.assertNotIn('Guidance: ', output)
        self.assertIn('not a reading checklist', output)
        ids = {r['id'] for r in value['requirements']}
        self.assertTrue({'architecture-authority', 'persistence-adoption', 'dotnet-runtime-security',
                         'capability-adoption', 'http-operation-contracts'} <= ids)
        self.assertIn('real-provider tests', output)
        self.assertNotIn('ui-evaluation-v1.md', output)  # Optional paid experiments are not browser acceptance.
        catalog = copy.deepcopy(context.catalog())
        catalog['requirements'][0]['phases'] = ['delivery']
        with patch.object(context, 'catalog', return_value=catalog):
            self.assertNotIn('domain-semantics', {r['id'] for r in context.project(self.root, self.feature, 'after-plan')['requirements']})

    def test_generated_draft_and_unrelated_source_cannot_expand_context(self):
        (self.feature / 'plan.md').write_text('Pure domain calculation; no database or browser required.', encoding='utf-8')
        before = context.project(self.root, self.feature, 'after-plan')
        (self.feature / 'tasks.md').write_text('Future dotnet browser API database capability guidance', encoding='utf-8')
        (self.feature / 'phase-context.md').write_text('PostgreSQL HTTP React capability', encoding='utf-8')
        self.assertEqual(before, context.project(self.root, self.feature, 'after-plan'))

    def test_project_delivery_is_read_only_and_only_is_focused(self):
        script = ROOT / 'extensions/program-kit-governance/scripts/phase_obligations.py'
        result = subprocess.run([sys.executable, str(script), 'project', '--repository', str(self.root),
                                 '--feature-dir', 'specs/002-cut-list', '--phase', 'delivery', '--only', 'persistence-adoption'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn('## persistence-adoption', result.stdout)
        self.assertNotIn('## dotnet-async', result.stdout)
        self.assertFalse((self.feature / 'tasks.md').exists())
        self.assertFalse((self.root / 'artifacts').exists())

    def test_interrupted_draft_resumes_without_rewriting_or_duplicate_tasks(self):
        first = draft.prepare(self.root, self.feature, self.phases)
        self.assertEqual(self.phases, first['remainingPhases'])
        draft.save_phase(self.root, self.feature, 'setup', '## Setup\n- [ ] T001 Retain exact pins in eng/Directory.Packages.props')
        tasks = self.feature / 'tasks.md'
        tasks.write_text(tasks.read_text(encoding='utf-8').replace('- [ ] T001', '- [X] T001') + '\nConsumer note: preserve this.\n', encoding='utf-8')
        saved = tasks.read_bytes()
        resumed = draft.prepare(self.root, self.feature, None)
        self.assertEqual(['setup'], resumed['completedPhases'])
        self.assertEqual([], resumed['changedInputs'])
        self.assertEqual(saved, tasks.read_bytes())
        with self.assertRaisesRegex(ValueError, 'already saved'):
            draft.save_phase(self.root, self.feature, 'setup', '## Setup\n- [ ] T002 Start over')
        with self.assertRaisesRegex(ValueError, 'Duplicate task IDs'):
            draft.save_phase(self.root, self.feature, 'foundation', '## Foundation\n- [ ] T001 Duplicate')
        self.assertEqual(saved, tasks.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Incomplete draft'):
            draft.finalize(self.root, self.feature)
        for n, phase in enumerate(self.phases[1:], 2):
            body = f'## {phase}\n- [ ] T{n:03} Verify owned behavior in tests/{phase}.cs'
            if phase == 'dependencies':
                body += '\n\n## Operation dependency map\n| Operation | Depends on operations |\n|-----------|-----------------------|\n| cutlist | none |\n'
                body += '\n## Task dependency map\n| Task | Operation | Depends on tasks | Requires | Provides |\n|------|-----------|------------------|----------|----------|\n'
                body += ''.join(f'| T{i:03} | cutlist | none | none | none |\n' for i in range(1, n + 1))
            draft.save_phase(self.root, self.feature, phase, body)
        self.assertFalse(draft.finalize(self.root, self.feature)['implementationExecuted'])
        content = tasks.read_text(encoding='utf-8')
        self.assertIn('- [X] T001', content)
        self.assertIn('Consumer note: preserve this.', content)
        self.assertNotIn('> Draft:', content)
        self.assertEqual('complete', draft.prepare(self.root, self.feature, None)['status'])
        self.assertEqual({'spec.md', 'plan.md', 'tasks.md'}, {p.name for p in self.feature.iterdir()})

    def test_changed_inputs_require_scoped_review_and_preserve_completed_work(self):
        draft.prepare(self.root, self.feature, self.phases)
        draft.save_phase(self.root, self.feature, 'setup', '## Setup\n- [ ] T001 Set up src/Feature.csproj')
        (self.feature / 'plan.md').write_text('Changed capability ownership.', encoding='utf-8')
        saved = (self.feature / 'tasks.md').read_bytes()
        state = draft.prepare(self.root, self.feature, None)
        self.assertEqual(['specs/002-cut-list/plan.md'], state['changedInputs'])
        with self.assertRaisesRegex(ValueError, 'Design inputs changed'):
            draft.save_phase(self.root, self.feature, 'foundation', '## Foundation\n- [ ] T002 Test tests/Feature.cs')
        self.assertEqual(saved, (self.feature / 'tasks.md').read_bytes())
        draft.acknowledge(self.root, self.feature)
        self.assertEqual(['setup'], draft.prepare(self.root, self.feature, None)['completedPhases'])
        self.assertEqual([], draft.prepare(self.root, self.feature, None)['changedInputs'])

    def test_failed_checkpoint_preserves_last_saved_phase(self):
        draft.prepare(self.root, self.feature, self.phases)
        saved = (self.feature / 'tasks.md').read_bytes()
        with patch.object(draft.os, 'replace', side_effect=OSError('Interrupted replacement')):
            with self.assertRaisesRegex(OSError, 'Interrupted replacement'):
                draft.save_phase(self.root, self.feature, 'setup', '## Setup\n- [ ] T001 Create src/Feature.cs')
        self.assertEqual(saved, (self.feature / 'tasks.md').read_bytes())
        self.assertEqual([], draft.prepare(self.root, self.feature, None)['completedPhases'])
        self.assertEqual([], list(self.feature.glob('.tasks-*.tmp')))

    def test_unmarked_consumer_tasks_are_preserved(self):
        tasks = self.feature / 'tasks.md'
        tasks.write_text('# Existing tasks\n- [X] T009 Keep src/Consumer.cs\n', encoding='utf-8')
        saved = tasks.read_bytes()
        self.assertEqual('existing', draft.prepare(self.root, self.feature, self.phases)['status'])
        self.assertEqual(saved, tasks.read_bytes())

    def test_final_review_rejects_invalid_or_duplicate_saved_tasks(self):
        draft.prepare(self.root, self.feature, ['US1'])
        draft.save_phase(self.root, self.feature, 'US1', '## US1\n- [ ] Missing task ID')
        with self.assertRaisesRegex(ValueError, 'task ID and description'):
            draft.finalize(self.root, self.feature)
        path = self.feature / 'tasks.md'
        content = path.read_text(encoding='utf-8').replace('Missing task ID', 'T001 Test tests/Feature.cs')
        path.write_text(content + '\n- [ ] T001 Duplicate tests/Other.cs\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate task IDs'):
            draft.finalize(self.root, self.feature)

    def test_reference_instructions_use_ordinary_artifacts_and_preserve_gates(self):
        component = (ROOT / 'extensions/program-kit-governance/references/component-adoption.md').read_text(encoding='utf-8')
        persistence = (ROOT / 'extensions/program-kit-dotnet/references/persistence-profiles.md').read_text(encoding='utf-8')
        dotnet = (ROOT / 'extensions/program-kit-dotnet/references/technology-profiles/dotnet.md').read_text(encoding='utf-8')
        self.assertNotIn('`capability-adoption.json` dispositions', component)
        self.assertNotIn('Unresolved answers block tasks', persistence)
        self.assertNotIn('identity in `artifact-ownership.json.runtimeComposition`', dotnet)
        self.assertIn('actual executed behavior', component)
        self.assertIn('authorization', persistence)
        self.assertIn('SQLite/InMemory cannot substitute', persistence)
        self.assertIn('No new artifact-ownership', persistence)
        modularity = (ROOT / 'extensions/program-kit-governance/references/modularity-and-contracts.md').read_text(encoding='utf-8')
        self.assertNotIn('`api-proof.json` binds', modularity)
        self.assertIn('No api-proof dossier', modularity)
        hook = (ROOT / 'extensions/program-kit-governance/commands/speckit.program-kit-governance.phase-context.md').read_text(encoding='utf-8')
        for text in ('constitution-required tests', 'security, ownership and real-provider',
                     'Do not invoke analyze on an incomplete draft', 'task_draft.py save-phase'):
            self.assertIn(text, hook)


if __name__ == '__main__':
    unittest.main()

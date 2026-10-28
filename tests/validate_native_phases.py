"""Native appended phases and read-only knowledge, without a delivery state engine."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from uuid import uuid4
from unittest.mock import patch

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'


def snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


def run(root, command, expected=0):
    result = subprocess.run([str(arg) for arg in command], cwd=root, capture_output=True,
                            text=True, encoding='utf-8', timeout=90)
    if result.returncode != expected:
        raise AssertionError(result.stdout + result.stderr)
    return result


def feature(root):
    path = root / 'specs/001-request'
    path.mkdir(parents=True)
    (path / 'spec.md').write_text('# Register a request\nA requester registers through an HTTP API.\n', encoding='utf-8')
    (path / 'plan.md').write_text('# Plan\nLocal choice: Rust with Axum; no curated generator.\n'
        'Use normal cargo checks and request behavior tests.\nReview: requester reviews registration before dependent work.\n', encoding='utf-8')
    (path / 'tasks.md').write_text('# Tasks\n- [x] T001 Preserve the request contract in src/request.rs\n'
        '- [ ] T002 Implement request registration in src/request.rs\n\n'
        'Review: pending requester walkthrough; pause dependent product work.\n'
        'Existing local notes and failure: request identity regression remains open.\n', encoding='utf-8')
    return path


def retain_installed_review(root):
    """Keep only synthetic instruction output before the owned consumer is removed."""
    from specify_cli.presets import PresetResolver
    target = ROOT / 'artifacts/tests/native-phase-review' / uuid4().hex
    target.mkdir(parents=True)
    names = ('plan', 'tasks', 'implement', 'analyze',
             'program-kit-governance-architecture-check',
             'program-kit-governance-implementation-check',
             'program-kit-governance-phase-context')
    for name in names:
        shutil.copyfile(root / f'.agents/skills/speckit-{name}/SKILL.md', target / f'{name}.md')
    shutil.copyfile(root / '.specify/extensions/program-kit-governance/references/engineering-feedback.md',
                    target / 'engineering-feedback.md')
    # Templates are composed by the native resolver, not rewritten in core storage.
    (target / 'tasks-template.md').write_text(
        PresetResolver(root).resolve_content('tasks-template', 'template'), encoding='utf-8')
    index = ('# Installed native phase guidance\n\n'
             'Synthetic disposable consumer; installation and deterministic instruction inspection only.\n'
             'No coding agent ran. These files do not demonstrate semantic judgment, agent obedience,\n'
             'human acceptance or platform compatibility. Native hook lookups were exercised separately.\n\n')
    index += ''.join(f'- [{name}]({name}.md)\n' for name in (*names, 'tasks-template', 'engineering-feedback'))
    (target / 'index.md').write_text(index, encoding='utf-8')
    print('Retained installed instruction review: ' + str(target / 'index.md'))


class NativePhaseTests(unittest.TestCase):
    def test_native_commands_survive_preset_and_plain_tasks_resume(self):
        from specify_cli._assets import get_speckit_version
        from specify_cli.events import refresh_integration_events
        from specify_cli.extensions import ExtensionManager
        from specify_cli.presets import PresetManager, PresetResolver
        with FixtureDirectory() as directory:
            root = Path(directory)
            site = Path(__import__('specify_cli').__file__).parent.parent
            bridge = [sys.executable, '-B', ROOT / 'scripts/invoke_specify.py', '--site-packages', site, '--']
            run(root, [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                       '--script', 'py', '--ignore-agent-tools'])
            skills = root / '.agents/skills'
            original = {name: (skills / f'speckit-{name}/SKILL.md').read_text(encoding='utf-8').split('---', 2)[2].strip()
                        for name in ('plan', 'tasks', 'implement', 'analyze')}
            manager = ExtensionManager(root)
            manager.install_from_directory(ROOT / 'extensions/program-kit-governance', get_speckit_version())
            refresh_integration_events(root)
            manager.scaffold_config('program-kit-governance')
            PresetManager(root).install_from_directory(ROOT / 'presets/program-kit-governance-preset', get_speckit_version())
            # Inspect the actual native registration/dispatch boundary, not only
            # our source manifest. This does not execute an AI hook command.
            import yaml
            from specify_cli.extensions import HookExecutor
            manifest = yaml.safe_load((ROOT / 'extensions/program-kit-governance/extension.yml').read_text(encoding='utf-8'))
            executor = HookExecutor(root)
            registered = executor.get_project_config()['hooks']
            self.assertEqual(set(manifest['hooks']), set(registered))
            for event, declarations in manifest['hooks'].items():
                expected = declarations if isinstance(declarations, list) else [declarations]
                expected = sorted(expected, key=lambda row: row.get('priority', 10))
                actual = executor.check_hooks_for_event(event)['hooks']
                self.assertEqual([row['command'] for row in expected], [row['command'] for row in actual], event)
                for row in actual:
                    self.assertIs(row['optional'], False)
                    self.assertIs(row['enabled'], True)
                    command = row['command'].replace('.', '-')
                    self.assertTrue((skills / command / 'SKILL.md').is_file(), row['command'])
                native = (skills / ('speckit-' + event.split('_', 1)[1]) / 'SKILL.md').read_text(encoding='utf-8')
                self.assertIn('hooks.' + event, native, event)
            after = executor.check_hooks_for_event('after_tasks')['hooks']
            self.assertEqual(['speckit.program-kit-governance.architecture-check', 'speckit.analyze'],
                             [row['command'] for row in after])
            self.assertEqual('$speckit-analyze', executor.execute_hook(after[1])['invocation'])
            after_plan = executor.check_hooks_for_event('after_plan')['hooks']
            self.assertEqual(['speckit.program-kit-governance.architecture-check'],
                             [row['command'] for row in after_plan])
            self.assertEqual('$speckit-program-kit-governance-architecture-check',
                             executor.execute_hook(after_plan[0])['invocation'])
            for name, native in original.items():
                installed = (skills / f'speckit-{name}/SKILL.md').read_text(encoding='utf-8')
                self.assertIn(native, installed, 'Preset replaced the native command: ' + name)
                if name == 'plan':
                    self.assertEqual(native, installed.split('---', 2)[2].strip(),
                                     'Planning must retain the upstream command without another append')
                    for wording in ('hooks.after_plan', 'actually invoke the hook and wait',
                                    'Emitting the block alone does not run the hook'):
                        self.assertIn(wording, installed)
                    continue
                marker = {'tasks': '## Program Kit task guidance', 'implement': '## Program Kit implementation guidance',
                          'analyze': '## Program Kit operation review'}[name]
                self.assertEqual(1, installed.count(marker))
                self.assertNotIn('task_draft.py', installed)
            implementation = (skills / 'speckit-implement/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('Pause dependent product work until actual acceptance', implementation)
            self.assertIn('silence', implementation.lower())
            # The append must clarify upstream test-first/halt wording without
            # replacing the native command or inventing another review boundary.
            method = ' '.join(implementation.split())
            self.assertIn('expected behavioral red test is followed by its implementation', method)
            self.assertIn('Finishing an internal task or saving progress alone is not a new pause boundary', method)
            tasks = (skills / 'speckit-tasks/SKILL.md').read_text(encoding='utf-8')
            for wording in ('finish the native `hooks.after_tasks` dispatch', '$speckit-analyze',
                            'not execution', 'Returning from architecture-check',
                            'do not force-enable', 'hooks actually invoked'):
                self.assertIn(wording, tasks)
            self.assertIn('Emitting the block alone does not run the hook', tasks)
            task_method = ' '.join(tasks.split())
            self.assertIn('a bounded setup increment', task_method)
            self.assertIn('It adds no approval receipt', task_method)
            template = ' '.join(PresetResolver(root).resolve_content('tasks-template', 'template').split())
            self.assertIn('preserving IDs, checkmarks and linked history', template)
            # These are instruction/packaging assertions, not simulated agent
            # decisions. The native helper below remains mechanically read-only.
            for wording in ('semantic commitments', 'local adaptation', 'first coherent',
                            'Keep Analyze read-only', 'preserving unrelated decisions'):
                self.assertIn(wording, tasks)
            architecture = (skills / 'speckit-program-kit-governance-architecture-check/SKILL.md').read_text(encoding='utf-8')
            for wording in ('actual spec, research, plan, contracts/data model', 'Alternatives',
                            'selected-version facts', 'genuinely unsettled', 'resume this review',
                            'An agent recommendation or Proposed ADR does not supply human acceptance',
                            'not execution'):
                self.assertIn(wording, architecture)
            preflight = (skills / 'speckit-program-kit-governance-implementation-check/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('](.specify/extensions/program-kit-dotnet/references/examples/postgresql-lifecycle/README.md#fast-provider-test-composition)', preflight)
            recipe = 'references/examples/cshells-initializer-ownership/'
            self.assertIn('](.specify/extensions/program-kit-dotnet/' + recipe + 'README.md)', preflight)
            for body in (implementation, preflight):
                for wording in ('existing source', 'semantic commitments', 'local adaptation',
                                'smallest coherent case', 'before replicating', 'engineering-feedback.md'):
                    self.assertIn(wording, ' '.join(body.split()))
            feedback_path = '.specify/extensions/program-kit-governance/references/engineering-feedback.md'
            for name in ('tasks', 'implement', 'analyze', 'program-kit-governance-architecture-check',
                         'program-kit-governance-implementation-check', 'program-kit-governance-phase-context'):
                body = (skills / f'speckit-{name}/SKILL.md').read_text(encoding='utf-8')
                self.assertIn('](' + feedback_path + ')', body, name)
            analyze = (skills / 'speckit-analyze/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('separate explicit correction step outside Analyze', analyze)
            feedback = (root / feedback_path).read_text(encoding='utf-8')
            for wording in ('strictly read-only', 'report its findings first', 'completed task IDs',
                            'do not silently amend the plan', 'continue independent ready work'):
                self.assertIn(wording, feedback)
            config = executor.get_project_config()
            config['hooks']['after_tasks'][1]['enabled'] = False
            executor.save_project_config(config)
            self.assertEqual(['speckit.program-kit-governance.architecture-check'],
                             [row['command'] for row in executor.check_hooks_for_event('after_tasks')['hooks']])
            config['hooks']['after_tasks'][1]['enabled'] = True
            executor.save_project_config(config)
            default_config = executor.get_project_config()
            config = executor.get_project_config()
            config['hooks']['after_plan'][0]['enabled'] = False
            executor.save_project_config(config)
            self.assertEqual([], executor.check_hooks_for_event('after_plan')['hooks'])
            config['hooks']['after_plan'][0]['enabled'] = True
            config['hooks']['after_plan'][0]['condition'] = "env.PROGRAM_KIT_SYNTHETIC_REVIEW == 'enabled'"
            executor.save_project_config(config)
            with patch.dict(os.environ, {'PROGRAM_KIT_SYNTHETIC_REVIEW': 'disabled'}):
                self.assertEqual([], executor.check_hooks_for_event('after_plan')['hooks'])
            with patch.dict(os.environ, {'PROGRAM_KIT_SYNTHETIC_REVIEW': 'enabled'}):
                self.assertEqual(1, len(executor.check_hooks_for_event('after_plan')['hooks']))
            del config['hooks']['after_plan']
            executor.save_project_config(config)
            removed = snapshot(root)
            self.assertEqual([], executor.check_hooks_for_event('after_plan')['hooks'])
            self.assertNotIn('after_plan', executor.get_project_config()['hooks'])
            self.assertEqual(removed, snapshot(root), 'Hook lookup recreated a removed hook')
            executor.save_project_config(default_config)
            retain_installed_review(root)
            chosen = feature(root)
            (chosen / 'research.md').write_text('# Research\nSelected local request approach; verify its contract.\n', encoding='utf-8')
            (chosen / 'data-model.md').write_text('# Request identity\nThe request owner controls identity assignment.\n', encoding='utf-8')
            # Existing poisoned 0.x history is preserved and never parsed as
            # current authority. No .NET extension or engineering adapter exists.
            old = root / 'docs/architecture/bootstrap-prerequisites.json'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'\xff preserved historical state, intentionally unreadable JSON')
            (root / 'docs/architecture/bootstrap-decisions.json').write_bytes(b'\xff old selected profile receipt')
            self.assertFalse((root / '.specify/extensions/program-kit-dotnet').exists())
            before = snapshot(root)
            installed = root / '.specify/extensions/program-kit-governance/scripts'
            for script, arguments in (
                ('phase_obligations.py', ['project', '--feature-dir', chosen.relative_to(root), '--phase', 'tasks', '--format', 'json']),
                ('implementation_preflight.py', ['--feature-dir', chosen.relative_to(root)]),
                ('phase_obligations.py', ['check', '--feature-dir', chosen.relative_to(root), '--phase', 'after-tasks']),
            ):
                run(root, [sys.executable, '-B', installed / script, *arguments])
                self.assertEqual(before, snapshot(root), 'Guidance changed normal tasks/history')
            data = json.loads(run(root, [sys.executable, '-B', installed / 'phase_obligations.py', 'project',
                '--feature-dir', chosen.relative_to(root), '--phase', 'implementation', '--format', 'json']).stdout)
            self.assertNotIn('dotnet', data['responsibilities'])
            for name in ('spec.md', 'research.md', 'plan.md', 'data-model.md', 'tasks.md'):
                self.assertIn('specs/001-request/' + name, data['localGuidance'])


class KnowledgeTests(unittest.TestCase):
    def test_cshells_workaround_is_in_selected_lifetime_guidance_and_lookup_is_read_only(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            (chosen / 'plan.md').write_text('# Plan\n.NET with CShells 0.0.31; a generation-owned resource needs admission.\n')
            before = snapshot(root)
            value = phase.check(root, chosen, 'implementation')
            selected = [row for row in value['requirements'] if row['id'] == 'dotnet-lifetime']
            self.assertEqual(1, len(selected))
            focused = phase.render({**value, 'requirements': selected}, 'implementation', True)
            self.assertIn('CShells 0.0.31', focused)
            self.assertIn('examples/cshells-initializer-ownership/README.md', focused)
            self.assertIn('one DI owner', focused)
            self.assertEqual(before, snapshot(root))
            (chosen / 'plan.md').write_text('# Plan\nRust with Axum; an independent runtime.\n')
            value = phase.check(root, chosen, 'implementation')
            self.assertNotIn('dotnet-lifetime', [row['id'] for row in value['requirements']])

    def test_packed_reference_availability_uses_the_existing_logical_source_reader(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        import asset_sources
        from knowledge_sources import resolve
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            extensions = root / '.specify/extensions'
            component = extensions / 'program-kit-dotnet'; component.mkdir(parents=True)
            (component / 'extension.yml').write_text('extension:\n  id: program-kit-dotnet\n')
            relative = 'references/examples/manual/README.md'
            original = b'An inspectable optional recipe; selected project contracts still apply.\n'
            (component / asset_sources.PACK).write_bytes(asset_sources.encoded({relative:original}))
            source = 'program-kit-dotnet/' + relative
            registry = {'sources':[{'id':source,'locator':{'kind':'extension','path':source}}],
                'rules':{'manual-example':{'source':source,'owner':'fixture','limits':'Source availability only',
                    'selector':{'kind':'document'}}},
                'requirements':[{'id':'example','when':'all','phases':['planning'],
                    'sources':[source],'ruleIds':['manual-example']}]}
            before = snapshot(root)
            fake_installed_script = extensions / 'program-kit-governance/scripts/phase_obligations.py'
            with patch.object(phase, '__file__', str(fake_installed_script)), patch.object(phase, 'catalog', return_value=registry):
                value = phase.model(root, chosen, 'planning', selected_tags={'all'})
            self.assertEqual([], value['requirements'][0]['unavailableReferences'])
            self.assertEqual(['manual-example'], value['requirements'][0]['ruleIds'])
            self.assertEqual(original.decode().strip(), resolve(registry,'manual-example',extensions=extensions)['text'])
            self.assertEqual(before, snapshot(root))

    def test_accepted_owned_targets_supply_only_their_explicit_technology_facets(self):
        sys.path.insert(0, str(SCRIPTS))
        import feature_context
        with FixtureDirectory() as directory:
            root = Path(directory)
            chosen = feature(root)
            architecture = root / 'docs/architecture'; architecture.mkdir(parents=True)
            (architecture / 'building-block-selection.json').write_text(json.dumps({
                'status':'Accepted', 'targets':[{'id':'request-api', 'kind':'dotnet-project',
                    'path':'src/Request/Request.csproj', 'placement':{'owner':'request-service'}}],
                'instances':[{'id':'request-bff', 'composition':'browser_bff', 'targetBindings':{'api':'request-api'}}]}))
            old = architecture / 'bootstrap-decisions.json'; old.write_bytes(b'\xff unavailable old profile receipt')
            projection = {'scope':['request-service'], 'elements':[{'id':'request-service', 'type':'container', 'technology':'.NET'}],
                          'decisions':[]}
            before = snapshot(root)
            original = Path.open
            def guarded(path, *args, **kwargs):
                if path == old:
                    raise AssertionError('Read retired profile register')
                return original(path, *args, **kwargs)
            with patch.object(feature_context, 'feature_scope', return_value={'projection':projection}), patch.object(Path, 'open', guarded):
                value = feature_context.adopted_context(root, chosen)
            self.assertIn('secure-web:bff-cookie-v1', value['tags'])
            self.assertIn('dotnet', value['tags'])
            self.assertNotIn('dotnet-host:foundation', value['tags'])
            self.assertEqual(before, snapshot(root))

    def test_standalone_governance_reads_focused_guidance_without_old_state_or_dotnet(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            installed = root / '.specify/extensions/program-kit-governance'
            shutil.copytree(ROOT / 'extensions/program-kit-governance', installed)
            chosen = feature(root)
            old = root / 'docs/architecture/bootstrap-decisions.json'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'\xff old receipt')
            before = snapshot(root)
            # Trap reads of historical authority and engineering execution in a
            # fresh interpreter. This proves independence beyond output wording.
            code = '''import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import phase_obligations as phase
root, feature = Path(sys.argv[2]), Path(sys.argv[3])
original = Path.open
def guarded(path, *args, **kwargs):
    if path.name in {'bootstrap-decisions.json', 'bootstrap-prerequisites.json', 'confirmation.json', 'review-basis.json'}:
        raise AssertionError('Read retired authority: ' + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, 'open', guarded), patch('subprocess.run', side_effect=AssertionError('Guidance executed a process')):
    value = phase.project(root, feature, 'implementation')
    value['requirements'] = [row for row in value['requirements'] if row['id'] == 'api-contracts']
    print(phase.render(value, 'implementation', True))
assert 'dotnet_adapter' not in sys.modules
assert 'task_draft' not in sys.modules
'''
            result = run(root, [sys.executable, '-B', '-c', code, installed / 'scripts', root, chosen])
            self.assertIn('program-kit-governance/references/modularity-and-contracts.md', result.stdout)
            self.assertNotIn('Do not duplicate either', result.stdout)
            self.assertIn('not installed', result.stdout)
            self.assertEqual(before, snapshot(root))

    def test_focus_paging_preserves_large_unicode_reference(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        content = ('Concrete local choice: café / 请求; actual source attribution.\n' * 1000)
        value = {'requirements': [{'id': 'local-example'}]}
        with patch.object(phase, 'constraints', return_value={'local-example': [content]}):
            rendered = phase.bounded_render(value, 'planning', detailed=True)
        pages = []
        index = 1
        while True:
            page = phase.text_page(rendered, index, 1000)
            pages.append(page.split('\n', 1)[1])
            if f'Continue the same command with --page {index + 1}.' not in page.split('\n', 1)[0]:
                break
            index += 1
        self.assertEqual(rendered, ''.join(pages))
        self.assertIn(content, rendered)


class PlanningGuidanceTests(unittest.TestCase):
    def test_dutch_browser_intent_routes_ui_without_selecting_a_stack(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        cases = (
            'Nederlandse browserroute voor telefoon en computer.',
            'De browserapp toont de berekening.',
            'Browserondersteuning voor telefoon en computer is vereist.',
            'Een browserapplicatie met toegankelijke bediening.',
            'Een browserapp zonder database.',
            '## Buiten scope\nEen database.\n## Binnen scope\nEen browserroute.',
        )
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = root / 'specs/001-calculation'; chosen.mkdir(parents=True)
            for prose in cases:
                with self.subTest(prose=prose):
                    (chosen / 'spec.md').write_text(prose, encoding='utf-8')
                    before = snapshot(root)
                    for action in ('planning', 'tasks', 'implementation', 'delivery'):
                        value = phase.project(root, chosen, action)
                        self.assertIn('web', value['responsibilities'])
                        self.assertIn('browser-experience', {row['id'] for row in value['requirements']})
                        self.assertTrue({'dotnet', 'typescript', 'api', 'persistence'}.isdisjoint(value['responsibilities']))
                    self.assertEqual(before, snapshot(root))

    def test_dutch_exclusions_and_unrelated_compounds_do_not_invent_browser_scope(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        cases = (
            'Geen browserapp. Bereken onderdelen met een CLI.',
            'Een CLI zonder browserroute.',
            'Browserondersteuning is niet vereist.',
            'De browserapplicatie is uitgesteld.',
            '## Buiten scope\nNederlandse browserroute.\n## Binnen scope\nCLI-berekeningen.',
            '## Toekomstig werk\nEen browserapp.',
            'Een bestandsbrowser ordent lokale bestanden.',
            'Een .NET API zonder browserroute.',
        )
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = root / 'specs/001-calculation'; chosen.mkdir(parents=True)
            for prose in cases:
                with self.subTest(prose=prose):
                    (chosen / 'spec.md').write_text(prose, encoding='utf-8')
                    before = snapshot(root)
                    value = phase.project(root, chosen, 'planning')
                    self.assertNotIn('browser-experience', {row['id'] for row in value['requirements']})
                    if '.NET API' in prose:
                        self.assertIn('http-operation-contracts', {row['id'] for row in value['requirements']})
                    self.assertEqual(before, snapshot(root))

    def test_architecture_guidance_preserves_ratification_without_receipt_gates(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            constitution = root / '.specify/memory/constitution.md'; constitution.parent.mkdir(parents=True)
            constitution.write_text('# Constitution\n**Status**: Ratified\nVersion: 0.2.0\n'
                                   'Human ratification: 2026-10-27. Amendments require explicit review.\n')
            before = snapshot(root)
            value = phase.check(root, chosen, 'planning')
            requirements = [row for row in value['requirements'] if row['id'] == 'architecture-authority']
            self.assertEqual(1, len(requirements))
            rendered = phase.render({**value, 'requirements': requirements}, 'planning', detailed=True)
            output = ' '.join(rendered.split())
            self.assertIn('last ratified constitution remains the governing baseline', output)
            self.assertIn('explicit human ratification', output)
            self.assertIn('individual ADR decisions', output)
            self.assertIn('does not require amending or re-ratifying', output)
            for obsolete in ('final architecture gate hash-binds', 'Drafting revokes stale ratification',
                             'dedicated human gate followed by hash-bound validation'):
                self.assertNotIn(obsolete, output)
            self.assertEqual(before, snapshot(root))


class FrameworkGuidanceTests(unittest.TestCase):
    def test_first_operation_constraints_are_canonical_scoped_and_bounded(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        from knowledge_sources import resolve
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            (chosen / 'plan.md').write_text('C# HTTP API with PostgreSQL, React TypeScript and queued inspection.')
            before = snapshot(root)
            value = phase.check(root, chosen, 'implementation')
            rendered = phase.render(value, 'implementation')
            for identity in ('principle.first-operation-source-review', 'principle.project-local-placement',
                             'principle.decision-time-budget', 'principle.typescript-runtime-admission',
                             'principle.runtime-time-and-io', 'principle.invocation-layout'):
                canonical = resolve(phase.catalog(), identity, extensions=ROOT / 'extensions')
                self.assertIn(canonical['text'], rendered, identity)
                self.assertIn('Canonical source: ' + canonical['provenance']['path'], rendered)
            # Measured assembled context, not a truncating production limit. The
            # essential operation decisions must appear before paginated detail.
            self.assertLess(len(rendered.encode('utf-8')), 22000)
            first = phase.text_page(rendered)
            for phrase in ('scattered state strings', 'Core accepts admitted policy',
                           'one abstraction level', 'project-local placement', 'complete execution deadline'):
                self.assertIn(phrase, first)
            self.assertEqual(before, snapshot(root))
            (chosen / 'plan.md').write_text('Rust pure label normalization.')
            scoped = phase.render(phase.check(root, chosen, 'implementation'), 'implementation')
            self.assertNotIn('## Current operation: principle.typescript-runtime-admission', scoped)
            self.assertNotIn('## .NET host decision review', scoped)
            self.assertNotIn('## Current operation: principle.invocation-layout', scoped)
            self.assertNotIn('## Current operation: principle.runtime-time-and-io', scoped)

    def test_foundation_resume_discovers_missing_composition_without_running_setup(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            decisions = root / 'docs/architecture/decisions'; decisions.mkdir(parents=True)
            decision = decisions / '0001-host.md'
            decision.write_text('# Host\nStatus: Accepted\n\n## Decision\nUse Orbyss.Foundation.Host with CShells.\n')
            tags = {'all', 'dotnet', 'api'}
            before = snapshot(root)
            with patch('subprocess.run', side_effect=AssertionError('Guidance started an application')):
                value = phase.model(root, chosen, 'implementation', selected_tags=tags)
                output = phase.render(value, 'implementation')
            self.assertEqual('absent', value['context']['composition']['state'])
            for expected in ('eng/foundation-composition.json: absent', 'composition_migrate.py --proposal',
                             'configuration-only', 'legacy --web-profile', 'Metadata/exporter hashes',
                             'exact pins', 'adds no approval receipt'):
                self.assertIn(expected, output)
            self.assertNotIn('canProceed', value)
            self.assertEqual(before, snapshot(root))
            (root / 'eng').mkdir()
            active = root / 'eng/foundation-composition.json'
            active.write_text('{"schemaVersion":2,"resources":[]}')
            before = snapshot(root)
            with patch('subprocess.run', side_effect=AssertionError('Resume reran supplier tests')):
                value = phase.model(root, chosen, 'implementation', selected_tags=tags)
                output = phase.render(value, 'implementation')
            self.assertEqual('present', value['context']['composition']['state'])
            self.assertIn('Presence is not readiness', output)
            self.assertIn('rerun only checks whose relevant inputs changed', output)
            self.assertEqual(before, snapshot(root))
            active.write_text('{"schemaVersion":1}')
            self.assertEqual('legacy-or-unknown', phase.composition_context(root, tags)['state'])
            active.write_text('broken JSON')
            self.assertEqual('unreadable', phase.composition_context(root, tags)['state'])
            decision.write_text('# Host\nStatus: Proposed\n\n## Decision\nUse Orbyss.Foundation.Host.\n')
            self.assertIsNone(phase.composition_context(root, tags))
            decision.write_text('# Host\nStatus: Accepted\n\n## Decision\nUse a conventional ASP.NET host instead of Foundation Host.\n')
            self.assertIsNone(phase.composition_context(root, tags))
            for text in ('Do not use Foundation Host. Use the existing ASP.NET host.',
                         "Don't use Orbyss.Foundation.Host.", 'Reject Foundation Host; use an existing host.'):
                decision.write_text('# Host\nStatus: Accepted\n\n## Decision\n' + text + '\n')
                self.assertIsNone(phase.composition_context(root, tags))
            decision.write_text('# Host\nStatus: Accepted\n\n## Decision\nUse Foundation Host, not a custom host.\n')
            self.assertIsNotNone(phase.composition_context(root, tags))
            decision.write_text('# Host\nStatus: Accepted\n\n## Decision\nUse Orbyss.Foundation.Host.\n')
            self.assertIsNone(phase.composition_context(root, {'all', 'web'}))
            self.assertIsNone(phase.composition_context(root, {'all', 'dotnet'}))

    def test_ef_deployment_constraints_do_not_select_a_replacement_engine(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            (chosen / 'plan.md').write_text(
                '# Plan\n.NET EF Core PostgreSQL persistence. Separate deployment credentials; '
                'least-privilege runtime and no startup DDL.\n'
                'Proposed T009: build a handwritten migration executable with a custom journal.\n')
            before = snapshot(root)
            for action in phase.PHASES:
                value = phase.check(root, chosen, action)
                first = phase.text_page(phase.render(value, action))
                focused = phase.render({**value, 'requirements': [row for row in value['requirements']
                    if row['id'] == 'persistence-adoption']}, action, True)
                for output in (first, focused):
                    for expected in ('model snapshot', '__EFMigrationsHistory', 'IDesignTimeDbContextFactory',
                                     'do not select a new migration engine', 'separate EF migrations assembly'):
                        self.assertIn(expected, ' '.join(output.split()))
                self.assertIn('assistant-authored task', first.lower())
                self.assertNotIn('deploy the product schema and journal', focused)
                self.assertNotIn('canProceed', value)
            self.assertEqual(before, snapshot(root))

    def test_native_mechanism_review_also_reaches_custom_stacks_without_ef(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root); before = snapshot(root)
            value = phase.check(root, chosen, 'planning')
            output = phase.render(value, 'planning')
            self.assertIn('concrete unmet requirement', output)
            self.assertIn('supported extension points', output)
            self.assertNotIn('__EFMigrationsHistory', output)
            self.assertNotIn('dotnet', value['responsibilities'])
            self.assertEqual(before, snapshot(root))

    def test_sqlite_guidance_preserves_provider_limits_and_valid_sql_extensions(self):
        sys.path.insert(0, str(SCRIPTS))
        import phase_obligations as phase
        with FixtureDirectory() as directory:
            root = Path(directory); chosen = feature(root)
            (chosen / 'plan.md').write_text('# Plan\nC# with EF Core SQLite persistence.\n')
            value = phase.check(root, chosen, 'planning')
            output = ' '.join(phase.render(value, 'planning').split())
            self.assertIn('SQLite cannot', output)
            self.assertIn('SQL inside an EF migration', output)
            self.assertIn('concrete unmet requirement', output)


if __name__ == '__main__':
    unittest.main()

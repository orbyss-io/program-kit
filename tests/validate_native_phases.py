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


class NativePhaseTests(unittest.TestCase):
    def test_native_commands_survive_preset_and_plain_tasks_resume(self):
        from specify_cli._assets import get_speckit_version
        from specify_cli.events import refresh_integration_events
        from specify_cli.extensions import ExtensionManager
        from specify_cli.presets import PresetManager
        with FixtureDirectory() as directory:
            root = Path(directory)
            site = Path(__import__('specify_cli').__file__).parent.parent
            bridge = [sys.executable, '-B', ROOT / 'scripts/invoke_specify.py', '--site-packages', site, '--']
            run(root, [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                       '--script', 'py', '--ignore-agent-tools'])
            skills = root / '.agents/skills'
            original = {name: (skills / f'speckit-{name}/SKILL.md').read_text(encoding='utf-8').split('---', 2)[2].strip()
                        for name in ('tasks', 'implement', 'analyze')}
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
            for name, native in original.items():
                installed = (skills / f'speckit-{name}/SKILL.md').read_text(encoding='utf-8')
                self.assertIn(native, installed, 'Preset replaced the native command: ' + name)
                marker = {'tasks': '## Program Kit task guidance', 'implement': '## Program Kit implementation guidance',
                          'analyze': '## Program Kit operation review'}[name]
                self.assertEqual(1, installed.count(marker))
                self.assertNotIn('task_draft.py', installed)
            implementation = (skills / 'speckit-implement/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('Pause dependent product work until actual acceptance', implementation)
            self.assertIn('silence', implementation.lower())
            tasks = (skills / 'speckit-tasks/SKILL.md').read_text(encoding='utf-8')
            for wording in ('finish the native `hooks.after_tasks` dispatch', '$speckit-analyze',
                            'not execution', 'Returning from architecture-check',
                            'do not force-enable', 'hooks actually invoked'):
                self.assertIn(wording, tasks)
            self.assertIn('Emitting the block alone does not run the hook', tasks)
            config = executor.get_project_config()
            config['hooks']['after_tasks'][1]['enabled'] = False
            executor.save_project_config(config)
            self.assertEqual(['speckit.program-kit-governance.architecture-check'],
                             [row['command'] for row in executor.check_hooks_for_event('after_tasks')['hooks']])
            config['hooks']['after_tasks'][1]['enabled'] = True
            executor.save_project_config(config)
            chosen = feature(root)
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
            self.assertIn('specs/001-request/plan.md', data['localGuidance'])


class KnowledgeTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()

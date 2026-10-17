"""Actual native all-phase refresh in four disposable pre-implementation consumers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'extensions/program-kit-governance/scripts')]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
from owned_scratch import owned_scratch, filesystem_path
import upgrade_program_kit as upgrade
import consumer_upgrade as flow
from specify_cli.integrations.manifest import IntegrationManifest

RUN = ROOT / 'artifacts/tests/phase-refresh' / uuid.uuid4().hex


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativePhaseRefreshTests(unittest.TestCase):
    def setUp(self):
        # Keep the complete historical profile tree. Native Python filesystem
        # operations need an extended root on Windows; shortening the fixture's
        # data or changing the host long-path policy would hide the boundary.
        scratch = self.enterContext(owned_scratch(ROOT, 'validation-fixture'))
        self.base = Path(filesystem_path(scratch))
        self.root = self.base / 'consumer'
        self.root.mkdir()
        self.cli = [sys.executable, str(ROOT / 'scripts/invoke_specify.py'), '--site-packages',
                    str(Path(__import__('specify_cli').__file__).parent.parent), '--']
        self.previous = os.environ.get('SPECIFY_INIT_DIR')
        os.environ['SPECIFY_INIT_DIR'] = str(self.root)
        self.addCleanup(self.restore_environment)
        self.invoke(['init', '.', '--force', '--non-interactive', '--integration', 'codex',
                     '--script', 'py', '--ignore-agent-tools'])
        for name in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
            self.invoke(['extension', 'add', str(ROOT / 'extensions' / name), '--dev'])
        self.invoke(['preset', 'add', '--dev', str(ROOT / 'presets/program-kit-governance-preset')])

    def restore_environment(self):
        if self.previous is None:
            os.environ.pop('SPECIFY_INIT_DIR', None)
        else:
            os.environ['SPECIFY_INIT_DIR'] = self.previous

    def invoke(self, arguments):
        result = subprocess.run(self.cli + arguments, cwd=self.root, capture_output=True,
                                text=True, encoding='utf-8', timeout=180)
        RUN.mkdir(parents=True, exist_ok=True)
        number = len(list(RUN.glob('native-*.log')))
        (RUN / f'native-{number:03d}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def seed(self, phase):
        retained = {
            'docs/architecture/building-block-selection.json': '{"selectedProfile":"fixture-exact-pin"}\n',
            'packages.lock.json': '{"fixture":"retained lock bytes"}\n',
            'contracts/openapi/fixture.baseline.json': '{"openapi":"3.1.0","paths":{}}\n',
            'artifacts/history/failed-proof.log': 'Original failure obligation, no acceptance claimed\n',
        }
        if phase != 'before-specification':
            retained['specs/001-example/spec.md'] = '# Accepted fictional specification\nRetain intent.\n'
            retained['specs/001-example/clarifications.md'] = 'Fictional accepted clarification\n'
        if phase in {'after-plan', 'after-tasks-analysis'}:
            retained['specs/001-example/plan.md'] = '# Fictional retained plan\nOriginal implementation baseline\n'
        if phase == 'after-tasks-analysis':
            retained['specs/001-example/tasks.md'] = ('- [ ] T001 Preserve original baseline\n'
                                                     '- [ ] T007 Focused prerequisite\n'
                                                     '- [ ] T012 Affected after T009; depends T007,T009\n')
            retained['specs/001-example/analysis.md'] = 'Pending failure/review remains pending\n'
        for relative, contents in retained.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding='utf-8')
        return {relative: digest(self.root / relative) for relative in retained}

    def test_four_preimplementation_phases_restore_core_and_retain_artifacts(self):
        # One installed native baseline; each scenario has an identical missing
        # core output. Existing native ownership admits its regeneration.
        rows = []
        for phase in ('before-specification', 'after-specification-clarification',
                      'after-plan', 'after-tasks-analysis'):
            retained = self.seed(phase)
            core = self.root / '.agents/skills/speckit-checklist/SKILL.md'
            pristine = core.read_bytes()
            core.unlink()
            started = time.perf_counter()
            plan = upgrade.phase_refresh_plan(self.root, ROOT)
            prepared = time.perf_counter() - started
            folder = RUN / phase
            started = time.perf_counter()
            upgrade.refresh_phase_integrations(self.root, ROOT, self.cli, plan, folder, 1, 2)
            elapsed = time.perf_counter() - started
            self.assertEqual(pristine, core.read_bytes())
            self.assertEqual(retained, {p: digest(self.root / p) for p in retained})
            manifest = IntegrationManifest.load('codex', self.root)
            self.assertFalse(manifest.check_modified())
            registry = json.loads((self.root / '.specify/extensions/.registry').read_text())
            self.assertEqual({'program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'},
                             set(registry['extensions']))
            for name in registry['extensions']:
                from specify_cli.extensions import ExtensionManifest
                source = ExtensionManifest(self.root / '.specify/extensions' / name / 'extension.yml')
                if source.commands:
                    self.assertTrue(registry['extensions'][name]['registered_commands'].get('codex'), name)
            # Check every core native phase, including phases outside the saved
            # artifact's current stage. Native preset rendering remains in effect.
            for name in ('specify', 'clarify', 'plan', 'tasks', 'analyze', 'implement', 'checklist', 'constitution'):
                self.assertTrue((self.root / f'.agents/skills/speckit-{name}/SKILL.md').is_file(), name)
            for name in ('tasks', 'implement', 'analyze'):
                relative = f'.agents/skills/speckit-{name}/SKILL.md'
                self.assertEqual(flow.preset_baseline(self.root, relative, 'codex'), digest(self.root / relative))
            rows.append({'phase': phase, 'preparationSeconds': round(prepared, 3),
                         'nativeRefreshSeconds': round(elapsed, 3), 'retainedHashes': retained,
                         'receipt': str(folder / 'phase-refresh.json')})
        (RUN / 'matrix.json').write_text(json.dumps({'schemaVersion': 1, 'scenarios': rows,
            'scope': 'Native installed command/skill refresh and byte retention; fictional pre-implementation artifacts',
            'caches': 'Existing installed Spec Kit and native bundled templates; no package restores or services',
            'businessBuildToOperationMeasured': False, 'codingAgentReasoningMeasured': False}, indent=2) + '\n', encoding='utf-8')

    def test_manual_core_and_preset_customizations_refuse_without_writes(self):
        for name in ('checklist', 'plan'):
            output = self.root / f'.agents/skills/speckit-{name}/SKILL.md'
            pristine = output.read_bytes()
            output.write_bytes(pristine + b'\nConsumer customization to preserve\n')
            before = {str(p.relative_to(self.root)): digest(p) for p in self.root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(upgrade.UpgradeError, 'PKU134.*customization'):
                upgrade.phase_refresh_plan(self.root, ROOT)
            self.assertEqual(before, {str(p.relative_to(self.root)): digest(p) for p in self.root.rglob('*') if p.is_file()})
            output.write_bytes(pristine)

    def test_secondary_native_integration_refresh_restores_default(self):
        self.invoke(['integration', 'install', 'copilot', '--force'])
        plan = upgrade.phase_refresh_plan(self.root, ROOT)
        original = plan['defaultIntegration']
        upgrade.refresh_phase_integrations(self.root, ROOT, self.cli, plan, RUN / 'multiple', 1, 5)
        self.assertEqual(original, upgrade.selected_integration(self.root, 'auto'))
        result = json.loads((RUN / 'multiple/phase-refresh.json').read_text())
        self.assertEqual({'codex', 'copilot'}, {row['integration'] for row in result['results']})

    def test_original_native_interpreter_choice_survives_alias_loss_without_execution(self):
        from unittest.mock import patch
        import render_profile
        from specify_cli.integrations.base import IntegrationBase
        # The native producer selects an existing project venv path without
        # executing it. This records actual generation, not executable readiness.
        candidate=self.root/'.venv/bin/python';candidate.parent.mkdir(parents=True)
        candidate.write_text('deliberately unavailable runtime; generation must not execute it')
        untouched='.agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md'
        untouched_profile=render_profile.profile(self.root,untouched)
        self.invoke(['preset','remove','program-kit-governance-preset'])
        self.invoke(['preset','add','--dev',str(ROOT/'presets/program-kit-governance-preset')])
        relative='.agents/skills/speckit-analyze/SKILL.md'
        original=(self.root/relative).read_bytes()
        generation=render_profile.profile(self.root,relative)
        self.assertEqual(untouched_profile,render_profile.profile(self.root,untouched))
        self.assertEqual('.venv/bin/python',generation['interpreter'])
        candidate.unlink()
        with patch.object(IntegrationBase,'resolve_python_interpreter',side_effect=AssertionError('historical rendering probed current PATH')):
            self.assertEqual(digest(self.root/relative),flow.preset_baseline(self.root,relative,'codex'))
        # Today's real resolver independently observes that the original path is gone.
        self.assertNotEqual('.venv/bin/python',IntegrationBase.resolve_python_interpreter(self.root))
        self.assertEqual(original,(self.root/relative).read_bytes())
        history=self.root/'.specify/program-kit/render-profiles'
        moved=self.root/'.specify/program-kit/original-render-profiles';history.rename(moved)
        self.assertIsNone(render_profile.profile(self.root,relative))
        self.assertNotEqual(digest(self.root/relative),flow.preset_baseline(self.root,relative,'codex'))
        self.assertFalse(history.exists(),'Historical inspection must not manufacture original provenance')
        moved.rename(history)
        source=self.root/'.specify/presets/program-kit-governance-preset/commands/speckit.analyze.md'
        source_bytes=source.read_bytes();source.write_bytes(source_bytes+b'\nChanged source obligation\n')
        self.assertNotEqual(digest(self.root/relative),flow.preset_baseline(self.root,relative,'codex'))
        source.write_bytes(source_bytes)
        records,head=render_profile.history(self.root)
        retained={file.name:file.read_bytes() for file in (self.root/'.specify/program-kit/render-profiles').iterdir()}
        # A new native refresh records only its actual new writes and retains originals.
        import initialize_device
        launcher=Path(shutil.which('specify'))
        self.assertEqual(0,initialize_device.invoke_native(self.root,'v'+(ROOT/'VERSION').read_text().strip(),ROOT,
                                                         launcher,['integration','use','codex']))
        self.assertNotEqual(head,render_profile.history(self.root)[1])
        for name,contents in retained.items():
            if name!='head.json':self.assertEqual(contents,(self.root/'.specify/program-kit/render-profiles'/name).read_bytes())
        output=self.root/relative;output.write_bytes(output.read_bytes()+b'\nconsumer change\n')
        self.assertNotEqual(digest(output),flow.preset_baseline(self.root,relative,'codex'))
        # No original record is synthesized for an older unrecorded install.
        history=self.root/'.specify/program-kit/render-profiles'
        moved=self.root/'.specify/program-kit/original-render-profiles';history.rename(moved)
        self.assertIsNone(render_profile.profile(self.root,relative))
        self.assertNotEqual(digest(output),flow.preset_baseline(self.root,relative,'codex'))
        moved.rename(history)
        retained=RUN/'historical-profile';retained.mkdir(parents=True)
        shutil.copytree(history,retained/'original-records')
        record=history/Path(render_profile.history(self.root)[1]['path']).name
        record.write_bytes(record.read_bytes()+b' ')
        with self.assertRaisesRegex(render_profile.RenderProfileError,'changed or disappeared'):
            render_profile.profile(self.root,relative)
        (retained/'results.json').write_text(json.dumps({'status':'passed','originalInterpreter':generation['interpreter'],
            'originalOutputSha256':generation['sha256'],'scope':'Actual native generation; no historical executable execution or readiness claim',
            'cases':['original-native-venv-choice','unavailable-original-executable-independent-of-historical-match',
                     'partial-refresh-retains-untouched-output-profile','changed-source-refuses-old-profile',
                     'missing-history-no-backfill','tampered-history-rejected','consumer-edit-preserved',
                     'native-initializer-helper-captures-refresh','immutable-original-records-retained']},indent=2),encoding='utf-8')


if __name__ == '__main__':
    unittest.main()

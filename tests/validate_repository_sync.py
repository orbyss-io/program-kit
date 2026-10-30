from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions/program-kit-governance/scripts"))
import repository_sync as sync
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
from owned_scratch import owned_scratch, filesystem_path


class CoordinatorTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows extended source-root regression')
    def test_installed_sync_reads_declared_parent_source_roots_with_extended_paths(self):
        with owned_scratch(ROOT, 'validation-fixture') as scratch:
            directory = Path(filesystem_path(scratch))
            target = directory / 'consumer'
            installed = target / '.specify/extensions/program-kit-dotnet'
            shutil.copytree(ROOT / 'extensions/program-kit-dotnet', installed,
                            ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ROOT / 'extensions/program-kit-building-blocks',
                            installed.with_name('program-kit-building-blocks'),
                            ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ROOT / 'extensions/program-kit-governance',
                            installed.with_name('program-kit-governance'),
                            ignore=shutil.ignore_patterns('__pycache__'))
            before = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in target.rglob('*') if p.is_file()}
            result = subprocess.run([sys.executable, str(installed / 'scripts/dotnet_sync.py'),
                '--target', str(target), '--profile-selected', '--web-profile', 'none', '--check', '--json'],
                capture_output=True, text=True, encoding='utf-8', timeout=90)
            self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
            self.assertTrue(result.stdout.strip(), result.stderr)
            plan = json.loads(result.stdout)
            self.assertFalse(plan['conflicts'])
            self.assertIn('scripts/composition_model.py', {row['path'] for row in plan['actions']})
            self.assertEqual(before, {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in target.rglob('*') if p.is_file()})

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="program-kit-repository-sync-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.decisions = self.root / "docs/architecture/bootstrap-decisions.json"
        self.decisions.parent.mkdir(parents=True)
        self.decisions.write_text(json.dumps({"selected_profiles": ["typescript-web"]}), encoding="utf-8")

    def test_javascript_planning_does_not_invoke_dotnet_or_materialize_files(self):
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        with patch.object(sync, "run") as run:
            plan = sync.describe(self.root, "planning")
            run.assert_not_called()
        self.assertEqual([item["adapter"] for item in plan["operations"]], ["javascript"])
        self.assertEqual(before, sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*")))

    def test_plain_javascript_feature_uses_actual_package_and_consumer_pins(self):
        self.decisions.unlink()
        feature = self.root / 'specs/new-web'
        feature.mkdir(parents=True)
        (feature / 'plan.md').write_text('# Plan\nImplement web/src/app.ts through web/package.json\n')
        sync.write(self.root / 'web/package.json', {'dependencies': {'react': '19.2.8'}})
        (self.root / '.nvmrc').write_text('22.19.0')
        (self.root / '.npm-version').write_text('10.9.3')
        setup = sync.context(self.root, 'planning', 'specs/new-web')
        self.assertTrue(setup['javascript'])
        self.assertFalse(setup['dotnet'])
        self.assertEqual({'node': '22.19.0', 'npm': '10.9.3'}, setup['toolchainPins'])
        self.assertIn('web/package.json', setup['authorityInputs'])
        self.assertFalse((feature / 'artifact-ownership.json').exists())
        (self.root / '.npm-version').unlink()
        with self.assertRaisesRegex(ValueError, 'actual .npm-version'):
            sync.context(self.root, 'planning', 'specs/new-web')

    def test_plain_dotnet_tasks_select_actual_generator_plan_without_old_register(self):
        self.decisions.unlink()
        feature = self.root / 'specs/new-requests'
        feature.mkdir(parents=True)
        (feature / 'tasks.md').write_text('- [ ] T001 Create src/Requests/Requests.csproj\n', encoding='utf-8')
        model = json.loads((ROOT / 'extensions/program-kit-governance/references/architecture-map-minimal.json').read_text())
        sync.write(self.root / 'docs/architecture/architecture-map.json', model)
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        plan = sync.describe(self.root, 'planning', 'specs/new-requests')
        self.assertTrue(plan['context']['dotnet'])
        operation = next(item for item in plan['operations'] if item['adapter'] == 'dotnet')
        self.assertIn('scripts/composition_model.py', {row['path'] for row in operation['plan']['actions']})
        self.assertFalse(self.decisions.exists())
        self.assertEqual(before, {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_feature_markdown_links_resolve_from_source_without_escaping_setup_scope(self):
        self.decisions.unlink()
        feature = self.root / 'specs/reviewed'
        feature.mkdir(parents=True)
        (feature / 'tasks.md').write_text('[Constitution](../../.specify/memory/constitution.md)\n'
                                         '[Project](../../src/Feature/Feature.csproj#setup)\n'
                                         'Create src/Other/Other.csproj.\n'
                                         '[External](https://example.invalid/docs/ignored.csproj)\n')
        setup = sync.context(self.root, 'planning', 'specs/reviewed')
        self.assertIn('src/Feature/Feature.csproj', setup['authorityInputs'])
        self.assertIn('src/Other/Other.csproj', setup['authorityInputs'])
        self.assertNotIn('.specify/memory/constitution.md', setup['authorityInputs'])
        self.assertNotIn('docs/ignored.csproj', setup['authorityInputs'])
        (feature / 'tasks.md').write_text('[Outside](../../../outside/project.csproj)')
        with self.assertRaisesRegex(ValueError, 'Markdown link escapes repository'):
            sync.context(self.root, 'planning', 'specs/reviewed')
        (feature / 'tasks.md').write_text('Create `../outside/project.csproj`.')
        with self.assertRaisesRegex(ValueError, 'feature task path escapes repository'):
            sync.context(self.root, 'planning', 'specs/reviewed')
        for destination in ('file:///C:/outside/project.csproj', 'C:/outside/project.csproj',
                            '//server/share/project.csproj', '%2e%2e/%2e%2e/%2e%2e/outside/project.csproj'):
            (feature / 'tasks.md').write_text('[Outside](' + destination + ')')
            with self.assertRaisesRegex(ValueError, 'Markdown link'):
                sync.context(self.root, 'planning', 'specs/reviewed')

    def test_bootstrap_records_requirements_without_applying_them(self):
        plan = sync.describe(self.root, "bootstrap")
        self.assertTrue(plan["context"]["javascript"])
        self.assertEqual(plan["operations"], [])
        self.assertFalse((self.root / "config/program-kit").exists())

    def test_upgrade_does_not_create_previously_unmaterialized_baseline(self):
        self.decisions.write_text(json.dumps({"selected_profiles": ["dotnet", "typescript-web"]}), encoding="utf-8")
        with patch.object(sync, "run") as run:
            plan = sync.describe(self.root, "upgrade")
            run.assert_not_called()
        self.assertFalse(plan["context"]["dotnet"])
        self.assertEqual(plan["operations"], [])

    def test_authority_and_pin_changes_invalidate_reviewed_plan(self):
        first = sync.describe(self.root, "planning")["planDigest"]
        self.decisions.write_text(json.dumps({"selected_profiles": ["typescript-web"], "choices": ["changed"]}), encoding="utf-8")
        self.assertNotEqual(first, sync.describe(self.root, "planning")["planDigest"])
        self.decisions.write_text(json.dumps({"selected_profiles": ["typescript-web"], "toolchain": {"source": "override", "pins": {"node": "99.0.0"}}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "rationale"):
            sync.describe(self.root, "planning")

    def test_wrong_toolchain_evidence_is_scheduled_for_audit(self):
        sync.write(self.root / "artifacts/program-kit/toolchain.json", {"satisfied": True, "required": {"node": "0.0.0", "npm": "0.0.0"}})
        self.assertTrue(sync.describe(self.root, "planning")["operations"][0]["required"])

    def test_failed_operation_preserves_an_incomplete_receipt(self):
        plan = sync.describe(self.root, "planning")
        with patch.object(sync, "audit_toolchain", side_effect=ValueError("test toolchain missing")):
            with self.assertRaisesRegex(ValueError, "toolchain missing"):
                sync.apply(self.root, plan)
        receipt = sync.load(self.root / ".program-kit/sync/receipt.json")
        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["operations"][0]["status"], "failed")
        self.assertEqual(receipt["reviewedPlanDigest"], plan["planDigest"])

    def test_feature_path_must_stay_inside_repository(self):
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            sync.describe(self.root, "planning", "../outside")

    def test_task_completion_does_not_change_setup_authority_but_design_does(self):
        tasks = self.root / 'specs/RM01/tasks.md'
        tasks.parent.mkdir(parents=True)
        tasks.write_text('- [ ] T001 Create the approved skeleton.\n', encoding='utf-8')
        first = sync.describe(self.root, 'planning', 'specs/RM01')['planDigest']
        tasks.write_text('- [x] T001 Create the approved skeleton.\n', encoding='utf-8')
        self.assertEqual(first, sync.describe(self.root, 'planning', 'specs/RM01')['planDigest'])
        tasks.write_text('- [x] T001 Create an unapproved skeleton.\n', encoding='utf-8')
        self.assertNotEqual(first, sync.describe(self.root, 'planning', 'specs/RM01')['planDigest'])

    def test_authoring_receipts_do_not_change_selected_setup_inputs(self):
        config = self.root / '.specify/extensions/program-kit-governance/program-kit-governance-config.yml'
        config.parent.mkdir(parents=True)
        config.write_text('constitution:\n  ratification: governance/ratification.json\narchitecture:\n  decisions: governance/decisions\n', encoding='utf-8')
        sync.write(self.root / 'governance/ratification.json', {'status':'Ratified'})
        plan = sync.describe(self.root,'planning')
        self.assertNotIn('governance/ratification.json', plan['context']['authorityInputs'])
        self.assertNotIn('governance/decisions/bootstrap-baseline.md', plan['context']['authorityInputs'])
        sync.write(self.root / 'governance/ratification.json', {'status':'Draft'})
        self.assertEqual(plan['planDigest'], sync.describe(self.root,'planning')['planDigest'])
        self.decisions.write_text(json.dumps({'selected_profiles': ['typescript-web'], 'choices': ['actual changed input']}))
        self.assertNotEqual(plan['planDigest'], sync.describe(self.root,'planning')['planDigest'])

    def test_live_seed_is_compatible_and_original_consumer_conflict_is_preserved(self):
        seeds = (('internal-forms-workspace/v1', True), ('repository-sync/v1/bootstrap-seed', False))
        for index, (seed, conflict) in enumerate(seeds):
            target = self.root / str(index)
            shutil.copytree(ROOT / 'tests/live/scenarios' / seed / 'fixture', target)
            before = {path.relative_to(target): path.read_bytes() for path in target.rglob('*') if path.is_file()}
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(target), '--profile-selected', '--check', '--json']
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            plan = json.loads(result.stdout)
            self.assertEqual(bool(plan['conflicts']), conflict, result.stdout + result.stderr)
            self.assertEqual(before, {path.relative_to(target): path.read_bytes() for path in target.rglob('*') if path.is_file()})
            if conflict:
                self.assertEqual([item['path'] for item in plan['conflicts']], ['Dockerfile'])
            else:
                self.assertIn(result.returncode, (0, 1), result.stderr)


if __name__ == "__main__":
    unittest.main()

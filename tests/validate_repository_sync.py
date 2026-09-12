from __future__ import annotations

import json
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


class CoordinatorTests(unittest.TestCase):
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

    def test_bootstrap_records_requirements_without_applying_them(self):
        plan = sync.describe(self.root, "bootstrap")
        self.assertTrue(plan["context"]["javascript"])
        self.assertEqual(plan["operations"], [])
        self.assertFalse((self.root / ".program-kit").exists())

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
        sync.write(self.root / ".program-kit/evidence/toolchain.json", {"satisfied": True, "required": {"node": "0.0.0", "npm": "0.0.0"}})
        self.assertTrue(sync.describe(self.root, "planning")["operations"][0]["required"])

    def test_failed_operation_preserves_an_incomplete_receipt(self):
        plan = sync.describe(self.root, "planning")
        with patch.object(sync, "audit_javascript", side_effect=ValueError("test toolchain missing")):
            with self.assertRaisesRegex(ValueError, "toolchain missing"):
                sync.apply(self.root, plan, validate_authority=False)
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

    def test_configured_ratification_and_baseline_are_bound_to_plan(self):
        config = self.root / '.specify/extensions/program-kit-governance/program-kit-governance-config.yml'
        config.parent.mkdir(parents=True)
        config.write_text('constitution:\n  ratification: governance/ratification.json\narchitecture:\n  decisions: governance/decisions\n', encoding='utf-8')
        sync.write(self.root / 'governance/ratification.json', {'status':'Ratified'})
        plan = sync.describe(self.root,'planning')
        self.assertIn('governance/ratification.json', plan['context']['authorityInputs'])
        self.assertIn('governance/decisions/bootstrap-baseline.md', plan['context']['authorityInputs'])
        sync.write(self.root / 'governance/ratification.json', {'status':'Draft'})
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

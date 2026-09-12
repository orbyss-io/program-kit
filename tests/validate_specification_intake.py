"""Bounded offline feature-grilling gate regressions; no coding agent is started."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
import specify_cli
from specify_cli.extensions import ExtensionManager

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "extensions/program-kit-governance/scripts"
sys.path.insert(0, str(SCRIPTS))
import specification_intake as intake


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature-intake-")
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name).resolve()
        previous = Path.cwd()
        os.chdir(self.repository)
        self.addCleanup(os.chdir, previous)
        for name in ("validate_installation", "validate_ratification", "configure_paths"):
            mocked = patch.object(intake.governance, name)
            mocked.start()
            self.addCleanup(mocked.stop)
        self.records = [{"id": "SPC-001", "title": "Invoice export", "Status": "Ready",
                         "Scope": "Own invoices", "Required Accepted ADRs": "none"}]
        mocked = patch.object(intake.governance, "validate_roadmap", side_effect=lambda ready: self.records)
        mocked.start()
        self.addCleanup(mocked.stop)
        for path in (intake.governance.CONSTITUTION, intake.governance.ARCHITECTURE):
            full = self.repository / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text("Accepted source", encoding="utf-8")
        self.path = intake.begin(self.repository, "SPC-001", "Export my invoices")
        self.brief = intake.read(self.path)
        self.brief.update({key: "Reviewed " + key for key in intake.FIELDS})
        self.brief["decisions"] = [{"id": "Q1", "question": "Whose invoices?", "answer": "Own account",
                                    "provenance": "User turn 2", "rationale": "Ownership boundary",
                                    "dependsOn": [], "disposition": "answered", "blocking": True}]
        self.save()

    def save(self):
        intake.atomic_write(self.path, self.brief)

    def confirm(self):
        review = intake.review(self.repository, "SPC-001")
        intake.confirm(self.repository, "SPC-001", review["reviewHash"], "User turn 4", "I confirm this brief")
        return intake.check(self.repository, "SPC-001")

    def test_confirmation_and_resume_without_setup_side_effects(self):
        original = self.path.read_bytes()
        self.assertEqual(intake.begin(self.repository, "SPC-001", "New request must be compared"), self.path)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(OSError):
            intake.check(self.repository, "SPC-001")
        review = intake.review(self.repository, "SPC-001")
        with self.assertRaises(OSError):
            intake.check(self.repository, "SPC-001")
        with self.assertRaises(ValueError):
            intake.confirm(self.repository, "SPC-001", "0" * 64, "turn 4", "yes")
        with self.assertRaises(ValueError):
            intake.confirm(self.repository, "SPC-001", review["reviewHash"], "", "")
        self.confirm()
        for path in ("specs", ".git", ".specify/feature.json"):
            self.assertFalse((self.repository / path).exists())

    def test_mutation_invalidates_confirmation_and_can_be_reconfirmed(self):
        self.confirm()
        self.brief["scope"] = "Include archived invoices"
        self.save()
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        intake.review(self.repository, "SPC-001")
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.confirm()

    def test_tampered_review_and_copied_receipt_block(self):
        self.confirm()
        review = self.path.with_name("review.md")
        review.write_text("Different synthesis", encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.confirm()
        receipt = intake.read(self.path.with_name("confirmation.json"))
        receipt["roadmapEntry"] = "SPC-002"
        intake.atomic_write(self.path.with_name("confirmation.json"), receipt)
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")

    def test_selected_entry_and_governance_changes(self):
        self.confirm()
        self.records.append({"id": "SPC-002", "Status": "Ready"})
        intake.check(self.repository, "SPC-001")
        self.records[0]["Status"] = "Blocked"
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.records[0]["Status"] = "Active"
        with self.assertRaises(OSError):
            intake.check(self.repository, "SPC-001")
        spec = self.repository / "specs/001-export/spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("- **Specification roadmap entry**: SPC-001 Invoice export\n", encoding="utf-8")
        intake.atomic_write(self.repository / ".specify/feature.json", {"feature_directory": "specs/001-export"})
        intake.check(self.repository, "SPC-001")
        self.records[0]["Scope"] = "All accounts"
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")
        self.confirm()
        (self.repository / intake.governance.CONSTITUTION).write_text("Amended source", encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check(self.repository, "SPC-001")

    def test_incomplete_and_blocking_decisions_cannot_be_reviewed(self):
        for modification in ({"disposition": "open"}, {"disposition": "deferred", "owner": "team", "trigger": "plan"},
                             {"dependsOn": ["missing"]}, {"dependsOn": ["Q1"]}, {"provenance": ""}):
            with self.subTest(modification=modification):
                brief = copy.deepcopy(self.brief)
                brief["decisions"][0].update(modification)
                with self.assertRaises(ValueError):
                    intake.validate_brief(brief, "SPC-001")
        self.brief["decisions"][0].update(disposition="deferred", blocking=False, owner="Planning owner", trigger="Before plan approval")
        self.save()
        self.confirm()
        self.brief["decisions"].append({**self.brief["decisions"][0], "id": "Q2", "disposition": "answered", "dependsOn": ["Q1"]})
        with self.assertRaises(ValueError):
            intake.validate_brief(self.brief, "SPC-001")

    def test_spec_reference_cannot_bypass_confirmation(self):
        result = self.confirm()
        spec = self.repository / "specs/001-export/spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("Existing spec with no intake", encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check_spec(self.repository, spec)
        text = ("- **Specification roadmap entry**: SPC-001 Invoice export\n"
                f"- **Confirmed intake brief**: {result['brief']}\n"
                f"- **Confirmed intake SHA256**: {result['briefHash']}\n")
        spec.write_text(text, encoding="utf-8")
        intake.check_spec(self.repository, spec)
        spec.write_text(text.replace(result["briefHash"], "0" * 64), encoding="utf-8")
        with self.assertRaises(ValueError):
            intake.check_spec(self.repository, spec)

    def test_path_escape_rejected(self):
        for entry in ("../escape", "A/../../escape", "", "SPC-001/child"):
            with self.assertRaises(ValueError):
                intake.directory(self.repository, entry)

    def test_context_requires_valid_installation_and_ratification(self):
        for operation in ("validate_installation", "validate_ratification", "validate_roadmap"):
            with self.subTest(operation=operation), patch.object(intake.governance, operation, side_effect=ValueError("Blocked governance")):
                with self.assertRaisesRegex(ValueError, "Blocked governance"):
                    intake.begin(self.repository, "SPC-001", "Resume")

    def test_dependency_cycles_and_missing_review_fields(self):
        self.brief["decisions"][0]["dependsOn"] = ["Q2"]
        self.brief["decisions"].append({**self.brief["decisions"][0], "id": "Q2", "dependsOn": ["Q1"]})
        with self.assertRaisesRegex(ValueError, "cycle"):
            intake.validate_brief(self.brief, "SPC-001")
        self.brief["acceptanceCriteria"] = ""
        with self.assertRaisesRegex(ValueError, "acceptanceCriteria"):
            intake.validate_brief(self.brief, "SPC-001")

    def test_preflight_cannot_continue_without_intake(self):
        feature = self.repository / "specs/001-export"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("Old spec", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "implementation_preflight.py"),
                                 "--repository", str(self.repository), "--feature-dir", str(feature)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Specification intake blocked", result.stderr)


class HookContractTests(unittest.TestCase):
    def test_installed_and_reinstalled_hooks_and_skill(self):
        with tempfile.TemporaryDirectory(prefix="feature-intake-install-") as value:
            repository = Path(value)
            (repository / ".specify").mkdir()
            intake.atomic_write(repository / ".specify/init-options.json", {"ai": "codex", "ai_skills": True})
            (repository / ".agents/skills").mkdir(parents=True)
            config = repository / ".specify/extensions.yml"
            config.write_text(yaml.safe_dump({"settings": {"auto_execute_hooks": True}, "hooks": {"before_specify": [
                {"extension": "consumer", "command": "consumer.branch", "priority": 50, "enabled": True, "optional": False},
            ]}}), encoding="utf-8")
            manager = ExtensionManager(repository)
            for force in (False, True):
                manager.install_from_directory(SCRIPTS.parent, "1.0.1", force=force)
                hooks = yaml.safe_load(config.read_text(encoding="utf-8"))["hooks"]["before_specify"]
                owned = [h for h in hooks if h["extension"] == "program-kit-governance"]
                self.assertEqual([h["command"] for h in owned], ["speckit.program-kit-governance.architecture-check",
                                                                 "speckit.program-kit-governance.specification-intake"])
                self.assertEqual(len([h for h in hooks if h["extension"] == "consumer"]), 1)
                for hook in owned:
                    self.assertIs(hook["optional"], False)
                    self.assertIs(hook["enabled"], True)
                    self.assertIsNone(hook["condition"])
            skill = repository / ".agents/skills/speckit-program-kit-governance-specification-intake/SKILL.md"
            content = skill.read_text(encoding="utf-8")
            self.assertIn(".specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md", content)
            self.assertTrue((repository / ".specify/extensions/program-kit-governance/scripts/specification_intake.py").is_file())

    def test_mandatory_order_and_core_execution_boundary(self):
        manifest = yaml.safe_load((SCRIPTS.parent / "extension.yml").read_text(encoding="utf-8"))
        hooks = manifest["hooks"]["before_specify"]
        self.assertEqual([h["command"] for h in hooks], ["speckit.program-kit-governance.architecture-check",
                                                       "speckit.program-kit-governance.specification-intake"])
        self.assertEqual([h["priority"] for h in hooks], [5, 10])
        for hook in hooks:
            self.assertIs(hook["enabled"], True)
            self.assertIs(hook["optional"], False)
            self.assertIsNone(hook["condition"])
        core = Path(specify_cli.__file__).parent / "core_pack/commands/specify.md"
        text = core.read_text(encoding="utf-8")
        self.assertLess(text.index("hooks.before_specify"), text.index("## Outline"))
        self.assertLess(text.index("MUST actually invoke the hook and wait"), text.index("## Outline"))
        self.assertLess(text.index("## Outline"), text.index("mkdir -p SPECIFY_FEATURE_DIRECTORY"))


if __name__ == "__main__":
    unittest.main()

"""Regression coverage for managed sign-in adopted after technology-neutral intake."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions/program-kit-governance/scripts"))
import bootstrap_context as context
from bootstrap_profiles import effective_stage_intake, validate_profile_dependencies
from json_schema import validate_value
from validate_bootstrap_context import seed_project, write_json
import validate_bootstrap_semantics as semantic


def decisions(profile="bff-cookie-v1"):
    return {
        "selected_profiles": ["dotnet", "browser-web"],
        "dotnet": {"host_runtime": "Orbyss.Foundation.Host", "program_kit_host_opt_out": False},
        "web": {"browser_ui": True, "secure_profile": profile},
    }


class ProfileRoutingTests(unittest.TestCase):
    def test_incomplete_managed_browser_cannot_pass(self):
        for profile in ("bff-cookie-v1", "spa-pkce-v1"):
            value = decisions(profile)
            value["selected_profiles"] = ["ui-experience-v1"]
            with self.assertRaisesRegex(ValueError, "browser-web"):
                validate_profile_dependencies(value)
            value["selected_profiles"].append("browser-web")
            with self.assertRaisesRegex(ValueError, "require dotnet"):
                validate_profile_dependencies(value)
            value["selected_profiles"].append("dotnet")
            validate_profile_dependencies(value)

    def test_anonymous_browser_does_not_require_dotnet(self):
        value = {"selected_profiles": ["browser-web"], "web": {"browser_ui": True, "secure_profile": "none-v1"}}
        validate_profile_dependencies(value)
        intake = {"routing": {"languages": [], "frameworks": [], "capabilities": ["authenticated-browser-bff"]}}
        routed = effective_stage_intake(intake, value)
        self.assertNotIn("dotnet-host-runtime", routed["routing"]["capabilities"])
        self.assertNotIn("authenticated-browser-bff", routed["routing"]["capabilities"])
        self.assertEqual(routed["routing"]["languages"], [])

    def test_opt_out_and_explicit_pkce_replace_stale_intake_suggestions(self):
        intake = {"routing": {"languages": [], "capabilities": ["dotnet-host-runtime", "authenticated-browser-bff"]}}
        value = decisions("spa-pkce-v1")
        value["dotnet"] = {"host_runtime": "Custom.Host", "program_kit_host_opt_out": True}
        original = copy.deepcopy(intake)
        routed = effective_stage_intake(intake, value)
        self.assertEqual(routed["routing"]["capabilities"], ["browser-spa-pkce"])
        self.assertEqual(intake, original)

    def test_generated_handoff_from_language_neutral_intake(self):
        with tempfile.TemporaryDirectory(prefix="program-kit-profile-routing-") as directory:
            project = Path(directory)
            seed_project(project, context, semantic, "profiles")
            intake_path = project / context.INTAKE_PATH
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            intake["routing"]["languages"] = []
            intake["routing"]["frameworks"] = []
            intake["routing"]["capabilities"] = ["authenticated-browser-bff"]
            write_json(intake_path, intake)
            original = intake_path.read_bytes()
            register = project / "docs/architecture/bootstrap-decisions.json"
            value = decisions()
            write_json(register, value)
            for relative in (context.DOTNET_SDK_MANIFEST, context.NODE_VERSION_MANIFEST,
                             context.WEB_PACKAGE_MANIFEST, context.WEB_PACKAGE_LOCK):
                target = project / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / str(relative).replace(".specify\\", "").replace(".specify/", ""), target)
            _, assessment = context.build_context(project, "profiles", "assessment")
            self.assertIn("Foundation/.NET", assessment["stage_plan"]["managed_web_dependency"]["rule"])
            self.assertTrue(set(context.DOTNET_REFERENCES).issubset(assessment["reading_policy"]["allowed_sources"]))
            _, research = context.build_context(project, "profiles", "research")
            self.assertIn("dotnet-sdk", research["managed_profile_pins"]["pins"])
            value["toolchain"] = {"source": "program-kit-default", "pins": research["managed_profile_pins"]["pins"], "override_reason": ""}
            write_json(register, value)
            # This fixture crosses from editable research into approved architecture.
            # Model that approval only after the researched pins have been selected.
            write_json(project / '.specify/governance/bootstrap-assessment-approval.json', {
                'status': 'Approved', 'artifacts': {
                    'docs/architecture/bootstrap-decisions.json': context.sha256_file(register)}})
            _, architecture = context.build_context(project, "profiles", "architecture")
            blocks = architecture["stage_plan"]["building_blocks"]
            self.assertEqual(blocks["suggested_compositions"], ["api_baseline", "browser_bff"])
            self.assertIn("--capability dotnet-host-runtime", blocks["draft_command"])
            self.assertEqual(blocks["composition_contracts"]["api_baseline"]["target_slots"]["host"]["kind"], "host-image")
            self.assertIn("foundation-host", blocks["composition_contracts"]["api_baseline"]["option_groups"][0]["options"])
            self.assertEqual(architecture["authorities"]["assessment_decisions"]["toolchain"], value["toolchain"])
            self.assertTrue(architecture["runtime_release"]["managed_host"]["version"])
            self.assertEqual(intake_path.read_bytes(), original)
            self.assertEqual(architecture["intake"]["routing"]["languages"], [])
            schema_path = ROOT / "extensions/program-kit-governance/references/bootstrap-context.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            for brief in (assessment, research, architecture):
                result = validate_value(brief, schema, schema_path)
                self.assertTrue(result["valid"], result["errors"])
            # The producer's own terminal check must reject the historical defect,
            # before a research dispatch or human approval can consume it.
            value["selected_profiles"] = ["ui-experience-v1"]
            write_json(register, value)
            with self.assertRaisesRegex(context.ContextError, "browser-web"):
                context.validate_stage_output(project, "assessment", "profiles")
            with self.assertRaisesRegex(context.ContextError, "browser-web"):
                context.build_context(project, "profiles", "research")


if __name__ == "__main__":
    unittest.main()

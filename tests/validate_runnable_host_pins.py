"""Offline central-package resolution and fail-closed runnable-host staging regressions."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files"
sys.path.insert(0, str(TEMPLATES / ".program-kit/eng"))
import runnable_host as host
sys.path.insert(0, str(ROOT / "extensions/program-kit-building-blocks/scripts"))
import building_blocks


class CentralPinsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="program-kit-central-pins-")
        self.addCleanup(self.temp.cleanup)
        self.repository = Path(self.temp.name)
        self.props = self.repository / "Directory.Packages.props"
        self.props.write_bytes((ROOT / "tests/fixtures/runnable-host/central-package-pins/Directory.Packages.props").read_bytes())
        self.original = self.props.read_text(encoding="utf-8")
        self.managed = self.repository / ".program-kit/eng/ProgramKit.Packages.props"
        self.managed.parent.mkdir(parents=True)
        shutil.copyfile(TEMPLATES / ".program-kit/eng/ProgramKit.Packages.props", self.managed)
        self.features = {identity: {} for identity in (
            "Orbyss.Foundation.WebDefaults", "Orbyss.Foundation.Web.ProblemDetails", "Orbyss.Foundation.Web.OpenApi",
        )}
        (self.repository / "shells.json").write_text(json.dumps({"CShells": {"Shells": {"default": {"Features": self.features}}}}), encoding="utf-8")
        (self.repository / "hostsettings.json").write_text("{}\n", encoding="utf-8")
        (self.repository / "NuGet.config").write_text('<configuration><packageSources /></configuration>', encoding="utf-8")
        self.packages = self.repository / "artifacts/packages"
        self.packages.mkdir(parents=True)
        self.output = self.repository / "artifacts/runnable-host"
        self.downloads = []
        self.addCleanup(patch.stopall)
        patch.object(host, "package_base_addresses", return_value=["https://example.invalid/flat"]).start()
        patch.object(host, "download_package", side_effect=self.download).start()

    def package(self, destination, identity, version, dependencies=""):
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr(identity + ".nuspec", f"<package><metadata><id>{identity}</id><version>{version}</version>{dependencies}</metadata></package>")

    def download(self, identity, version, bases, destination):
        self.downloads.append((identity, version))
        self.package(destination, identity, version)

    def stage(self):
        host.stage(self.repository, self.packages, self.output)

    def evidence(self):
        return json.loads((self.repository / host.runtime_closure.EVIDENCE).read_text(encoding="utf-8"))

    def test_real_imported_consumer_layout_stages_and_verifies_closure(self):
        self.assertNotIn("Orbyss.Foundation.Web.OpenApi", self.managed.read_text(encoding="utf-8"))
        self.stage()
        expected = {(identity, "0.1.0") for identity in self.features} | host.BUILT_IN_FEATURE_RUNTIME_PACKAGES["Orbyss.Foundation.Web.OpenApi"]
        self.assertEqual(set(self.downloads), expected)
        evidence = host.runtime_closure.validate(self.repository, self.output, self.repository / host.runtime_closure.EVIDENCE, host.PROGRAM_KIT_VERSION)
        self.assertTrue(evidence["satisfied"])
        self.assertEqual(len(evidence["packages"]), len(expected))
        self.assertEqual(self.props.read_text(encoding="utf-8"), self.original)

    def test_optional_selected_import_and_nested_literal_import(self):
        selected = self.managed.with_name("ProgramKit.BuildingBlocks.props")
        selected.write_text('<Project><Import Project="selected.props" /></Project>', encoding="utf-8")
        selected.with_name("selected.props").write_text('<Project><ItemGroup><PackageVersion Include="Orbyss.Foundation.Tasks"><Version>0.1.0</Version></PackageVersion></ItemGroup></Project>', encoding="utf-8")
        self.assertEqual(host.central_package_versions(self.repository)["orbyss.foundation.tasks"], "0.1.0")

    def test_actual_building_block_generated_props_stages_selected_feature(self):
        self.managed.with_name("ProgramKit.BuildingBlocks.props").write_text(
            building_blocks.render_central_pins([{"packageId": "Orbyss.Foundation.Tasks", "version": "0.1.0"}]),
            encoding="utf-8",
        )
        self.features["FoundationTasks"] = {}
        (self.repository / "shells.json").write_text(
            json.dumps({"CShells": {"Shells": {"default": {"Features": self.features}}}}), encoding="utf-8",
        )
        self.stage()
        self.assertIn(("Orbyss.Foundation.Tasks", "0.1.0"), self.downloads)
        self.assertTrue(self.evidence()["satisfied"])

    def test_unsupported_and_ambiguous_pins_fail_before_download(self):
        pin = '<PackageVersion Include="Orbyss.Foundation.Web.OpenApi" Version="0.1.0" />'
        cases = {
            "missing": self.original.replace(pin, ""),
            "conflicting": self.original.replace(pin, pin + pin.replace('0.1.0', '0.2.0')),
            "duplicate-case": self.original.replace(pin, pin + pin.replace('Orbyss.Foundation.Web.OpenApi', 'orbyss.foundation.web.openapi')),
            "property": self.original.replace(pin, pin.replace('0.1.0', '$(FeatureVersion)')),
            "floating": self.original.replace(pin, pin.replace('0.1.0', '0.1.*')),
            "range": self.original.replace(pin, pin.replace('0.1.0', '[0.1.0,0.2.0)')),
            "conditional-item": self.original.replace(pin, pin.replace('/>', 'Condition="false" />')),
            "conditional-group": self.original.replace('<ItemGroup>', '<ItemGroup Condition="false">'),
            "update": self.original.replace(pin, pin.replace('Include=', 'Update=')),
            "remove": self.original.replace(pin, '<PackageVersion Remove="Orbyss.Foundation.Web.OpenApi" />'),
            "missing-import": self.original.replace('ProgramKit.Packages.props', 'Missing.props'),
            "wildcard-import": self.original.replace('ProgramKit.Packages.props', '*.props'),
            "property-import": self.original.replace('ProgramKit.Packages.props', '$(PropsFile)'),
            "external-import": self.original.replace('.program-kit/eng/ProgramKit.Packages.props', '../outside.props'),
            "cycle": self.original.replace('.program-kit/eng/ProgramKit.Packages.props', 'Directory.Packages.props'),
            "conditional-import": self.original.replace("Exists('.program-kit/eng/ProgramKit.BuildingBlocks.props')", 'false'),
            "choose": '<Project><Choose /></Project>',
            "disabled-cpm": self.original.replace('Centrally>true', 'Centrally>false'),
        }
        for label, text in cases.items():
            with self.subTest(case=label):
                self.props.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "PKR019"):
                    self.stage()
                self.assertFalse(self.evidence()["satisfied"])
                self.assertEqual(self.downloads, [])
                self.assertFalse(self.output.exists())

    def test_unimported_managed_pin_is_not_authority(self):
        self.props.write_text('<Project />', encoding="utf-8")
        self.managed.write_text('<Project><ItemGroup><PackageVersion Include="Orbyss.Foundation.Web.OpenApi" Version="0.1.0" /></ItemGroup></Project>', encoding="utf-8")
        self.assertEqual(host.central_package_versions(self.repository), {})
        with self.assertRaisesRegex(ValueError, "PKR019"):
            self.stage()

    def test_import_conflict_is_not_overridden_by_consumer_pin(self):
        self.managed.write_text('<Project><ItemGroup><PackageVersion Include="Orbyss.Foundation.Web.OpenApi" Version="0.2.0" /></ItemGroup></Project>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate/conflicting"):
            self.stage()

    def test_existing_stage_preserved_and_evidence_invalidated_on_pin_failure(self):
        self.stage()
        before = {p.relative_to(self.output).as_posix(): p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        self.props.write_text(self.original.replace('Version="0.1.0"', 'Version="*"'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PKR019"):
            self.stage()
        self.assertFalse(self.evidence()["satisfied"])
        self.assertEqual(before, {p.relative_to(self.output).as_posix(): p.read_bytes() for p in self.output.rglob('*') if p.is_file()})

    def test_packed_builtin_conflicting_version_is_rejected(self):
        self.package(self.packages / 'wrong.nupkg', 'Orbyss.Foundation.Web.OpenApi', '0.2.0')
        with self.assertRaisesRegex(ValueError, "PKR019.*conflicts"):
            self.stage()
        self.assertEqual(self.downloads, [])

    def test_restore_assets_conflicting_version_is_rejected(self):
        with patch.object(host, 'runtime_dependencies', return_value={('Orbyss.Foundation.Web.OpenApi', '0.2.0')}):
            with self.assertRaisesRegex(ValueError, "PKR019.*conflicts"):
                self.stage()

    def test_transitive_dependency_cannot_upgrade_builtin_pin(self):
        self.package(self.packages / 'application.nupkg', 'Fixture.Application', '1.0.0',
                     '<dependencies><dependency id="Orbyss.Foundation.Web.OpenApi" version="0.2.0" /></dependencies>')
        with self.assertRaisesRegex(ValueError, "PKR019 dependency requires"):
            self.stage()
        self.assertFalse(self.evidence()['satisfied'])
        self.assertNotIn(('Orbyss.Foundation.Web.OpenApi', '0.2.0'), self.downloads)

    def test_wrong_downloaded_builtin_identity_fails_before_success_evidence(self):
        def wrong(identity, version, bases, destination):
            self.package(destination, identity, '9.0.0' if identity == 'Orbyss.Foundation.Web.OpenApi' else version)
        with patch.object(host, 'download_package', side_effect=wrong):
            with self.assertRaisesRegex(ValueError, "PKR019 staged package"):
                self.stage()
        self.assertFalse(self.evidence()['satisfied'])


if __name__ == '__main__':
    unittest.main()

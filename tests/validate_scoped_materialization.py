from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from validate_building_blocks import CATALOG, RESOLVER, accepted_fixture, load_module, refresh_registration, write_json


class ScopedMaterializationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module(RESOLVER)
        self.temp = tempfile.TemporaryDirectory(prefix="program-kit-scope-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.selection, self.architecture = accepted_fixture(self.module, self.root, self.catalog)
        document = json.loads(self.selection.read_text())
        future = copy.deepcopy(document["targets"][0])
        future.update(id="future-feature", path="src/Future/Future.csproj")
        document["targets"].append(future)
        instance = copy.deepcopy(document["instances"][0])
        instance.update(id="future-domain-events")
        instance["targetBindings"]["dotnet"] = "future-feature"
        document["instances"].append(instance)
        write_json(self.selection, document)
        refresh_registration(self.selection, self.architecture)

    def plan(self):
        full = self.module.resolve(self.root, self.selection, CATALOG, "0.11.0")
        return self.module.materialized_plan(self.root, full)

    def test_existing_feature_applies_without_future_scaffolding_or_activation(self):
        plan = self.plan()
        self.assertEqual(plan["deferredInstances"], ["future-domain-events"])
        self.assertNotIn("future-feature", {target["id"] for target in plan["targets"]})
        self.assertTrue(all(not activation["origin"].startswith("future-") for activation in plan["activations"]))
        lock = self.root / ".program-kit/building-blocks.lock.json"
        self.module.apply_materialization(self.root, lock, plan, self.catalog)
        self.module.check_materialization(self.root, plan)
        self.assertFalse((self.root / "src/Future").exists())
        self.assertEqual(self.plan(), plan)

    def test_creating_approved_future_skeleton_changes_plan_without_implicit_creation(self):
        before = self.plan()
        future = self.root / "src/Future/Future.csproj"
        self.assertFalse(future.exists())
        future.parent.mkdir(parents=True)
        future.write_text('<Project Sdk="Microsoft.NET.Sdk" />', encoding="utf-8")
        after = self.plan()
        self.assertNotEqual(before["planDigest"], after["planDigest"])
        self.assertEqual(after["deferredInstances"], [])
        self.assertIn("future-feature", {target["id"] for target in after["targets"]})

    def test_all_planned_has_no_materialization(self):
        (self.root / "src/Test.Feature/Test.Feature.csproj").unlink()
        plan = self.plan()
        self.assertEqual(plan["targets"], [])
        self.assertEqual(plan["activations"], [])
        self.assertEqual(plan["managedOutputs"], [])

    def test_invalid_authority_still_blocks_scoped_resolution(self):
        document = json.loads(self.selection.read_text())
        document["authority"]["rationale"] = "changed without registration"
        write_json(self.selection, document)
        with self.assertRaises(self.module.ResolverError):
            self.plan()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions/program-kit-governance/scripts"))
import package_execution as packages
import npm_graph
import npm_metadata


class PackageExecutionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="program-kit-package-execution-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.evidence = self.root / "toolchain.json"
        self.evidence.write_text('{}\n', encoding="utf-8")
        self.log = self.root / "calls.json"
        self.fake = self.root / "fake_npm.py"
        self.fake.write_text(
            "import json,os,pathlib,sys\n"
            "config=pathlib.Path(os.environ['NPM_CONFIG_USERCONFIG']).read_text()\n"
            "assert '${PROGRAM_KIT_NPM_TOKEN}' in config\n"
            "assert os.environ['PROGRAM_KIT_NPM_TOKEN'] not in config\n"
            "assert '--@orbyss-io:registry=https://npm.pkg.github.com/' in sys.argv\n"
            "assert '--strict-ssl=true' in sys.argv\n"
            "pathlib.Path(os.environ['TEST_PACKAGE_CALLS']).write_text(json.dumps({'args':sys.argv,'config':config,'cwd':str(pathlib.Path.cwd())}))\n"
            "pathlib.Path('package-lock.json').write_text('{\"lockfileVersion\":3}')\n"
            "print('metadata or graph result')\n", encoding="utf-8")
        self.runtime = types.SimpleNamespace(context=lambda *_: ([sys.executable, str(self.fake)], os.environ.copy()))
        self.manifest = self.root / "candidate.json"
        self.manifest.write_text(json.dumps({"dependencies": {"@orbyss-io/forms-react": "0.1.1", "react": "19.2.8"}}), encoding="utf-8")

    def test_first_isolated_lookup_has_catalog_route_and_no_dotnet_prerequisite(self):
        graph = self.root / "graph.json"
        self.assertFalse((self.root / ".program-kit/eng").exists())
        with patch.dict(os.environ, {"PROGRAM_KIT_NPM_TOKEN": "synthetic-token", "TEST_PACKAGE_CALLS": str(self.log)}), patch.object(packages, "javascript_runtime", return_value=self.runtime):
            npm_graph.resolve(self.manifest, self.root, self.evidence, "", graph, 10)
        record = json.loads(self.log.read_text())
        self.assertNotEqual(record["cwd"], str(self.root))
        proof = json.loads(graph.read_text())
        self.assertTrue(proof["satisfied"])
        self.assertNotIn("synthetic-token", graph.read_text())
        self.assertIn("PROGRAM_KIT_NPM_TOKEN", graph.read_text())
        self.assertFalse((self.root / "package-lock.json").exists())

    def test_missing_access_stops_before_first_process_and_invalidates_prior_attempt(self):
        graph = self.root / "graph.json"
        graph.write_text('{"satisfied":true}', encoding="utf-8")
        with patch.dict(os.environ, {}, clear=True), patch.object(packages.subprocess, "run") as child:
            with self.assertRaisesRegex(ValueError, "missing-access"):
                npm_graph.resolve(self.manifest, self.root, self.evidence, "", graph, 10)
            child.assert_not_called()
        self.assertFalse(json.loads(graph.read_text())["satisfied"])

    def test_unchanged_graph_reuses_proof_and_changed_manifest_renews(self):
        graph = self.root / "graph.json"
        with patch.dict(os.environ, {"PROGRAM_KIT_NPM_TOKEN": "synthetic-token", "TEST_PACKAGE_CALLS": str(self.log)}), patch.object(packages, "javascript_runtime", return_value=self.runtime):
            npm_graph.resolve(self.manifest, self.root, self.evidence, "", graph, 10)
            proof = graph.read_bytes()
            with patch.object(packages, "execute", side_effect=AssertionError("unchanged graph repeated network")):
                npm_graph.resolve(self.manifest, self.root, self.evidence, "", graph, 10)
            self.assertEqual(graph.read_bytes(), proof)
            self.manifest.write_text('{"dependencies":{"react":"19.2.9"}}', encoding="utf-8")
            with patch.object(packages, "execute", side_effect=ValueError("changed candidate renewed")):
                with self.assertRaisesRegex(ValueError, "renewed"):
                    npm_graph.resolve(self.manifest, self.root, self.evidence, "", graph, 10)
            self.assertFalse(json.loads(graph.read_text())["satisfied"])

    def test_strict_policy_cannot_be_overridden_by_caller(self):
        with patch.object(packages, "javascript_runtime", return_value=self.runtime):
            for flag in ("--force", "--legacy-peer-deps", "--strict-ssl=false", "--ignore-scripts=false"):
                with self.assertRaisesRegex(ValueError, "cannot bypass"):
                    packages.execute(self.root, self.evidence, ["react"], ["install", flag], self.root, 10)

    def test_known_registry_does_not_fall_back_to_public(self):
        route = packages.routes(["@orbyss-io/forms-react"])
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]["registry"], "https://npm.pkg.github.com/")
        self.assertEqual(packages.routes(["react"])[0]["registry"], "https://registry.npmjs.org/")

    def test_source_conflict_and_credential_in_url_rejected_before_network(self):
        source = {"ecosystem": "npm", "patterns": ["@example/*"], "url": "https://example.invalid/"}
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            packages.routes(["@example/package"], {"sources": {"one": source, "two": source}})
        source["url"] = "https://user:secret@example.invalid/"
        with self.assertRaisesRegex(ValueError, "secure registry URL"):
            packages.routes(["@example/package"], {"sources": {"one": source}})

    def test_failure_causes_do_not_misdiagnose_missing_package_as_peer_conflict(self):
        for message, category in (("E404", "package-unavailable"), ("ERESOLVE", "incompatible-graph"),
                                  ("E403", "access-denied"), ("SELF_SIGNED_CERT_IN_CHAIN", "trust"),
                                  ("ECONNRESET", "network")):
            self.assertEqual(packages.classify_failure(message), category)

    def test_failure_output_redacts_credential(self):
        with patch.dict(os.environ, {"PROGRAM_KIT_NPM_TOKEN": "synthetic-token"}):
            output = packages.redact("E403 synthetic-token https://user:password@example.invalid", packages.routes(["@orbyss-io/forms-react"]))
        self.assertNotIn("synthetic-token", output)
        self.assertNotIn("password", output)

    def test_metadata_and_restore_use_identical_context(self):
        with patch.dict(os.environ, {"PROGRAM_KIT_NPM_TOKEN": "synthetic-token", "TEST_PACKAGE_CALLS": str(self.log)}), patch.object(packages, "javascript_runtime", return_value=self.runtime):
            _, metadata = packages.execute(self.root, self.evidence, ["@orbyss-io/forms-react"], ["view", "@orbyss-io/forms-react@0.1.1", "--json"], self.root, 10)
            _, restore = packages.execute(self.root, self.evidence, ["@orbyss-io/forms-react"], ["ci", "--ignore-scripts"], self.root, 10)
        self.assertEqual(metadata["contextDigest"], restore["contextDigest"])

    def test_inherited_ca_is_bound_to_readiness_and_execution(self):
        certificate = self.root / 'organization-ca.pem'
        certificate.write_text('test certificate one', encoding='utf-8')
        with patch.dict(os.environ, {'NODE_EXTRA_CA_CERTS': str(certificate)}), patch.object(packages, 'javascript_runtime', return_value=self.runtime):
            before = packages.context_proof(self.root, self.evidence, ['react'])
            with packages.execution_context(self.root, self.evidence, ['react']) as (_, _, actual):
                self.assertEqual(before['contextDigest'], actual['contextDigest'])
            certificate.write_text('test certificate two', encoding='utf-8')
            self.assertNotEqual(before['contextDigest'], packages.context_proof(self.root, self.evidence, ['react'])['contextDigest'])

    def test_metadata_rejects_wrong_version_and_retains_failed_evidence(self):
        path = self.root / "metadata.json"
        result = subprocess.CompletedProcess([], 0, json.dumps({"name": "react", "version": "19.2.7"}), "")
        with patch.object(packages, "execute", return_value=(result, {})):
            with self.assertRaisesRegex(ValueError, "different package or version"):
                npm_metadata.resolve(self.root, "react", "19.2.8", self.evidence, path, 10)
        self.assertFalse(json.loads(path.read_text())["satisfied"])

    def test_metadata_requires_exact_pins_before_process(self):
        with patch.object(packages, "execute") as execute:
            for version in ("latest", "^19.2.8", "19.x", "19.2.8 --force"):
                with self.assertRaisesRegex(ValueError, "exact npm version"):
                    npm_metadata.resolve(self.root, "react", version, self.evidence, self.root / "metadata.json", 10)
            execute.assert_not_called()

    def test_metadata_records_matching_registry_result(self):
        path = self.root / "metadata.json"
        result = subprocess.CompletedProcess([], 0, json.dumps({"name": "react", "version": "19.2.8", "peerDependencies": {}}), "")
        with patch.object(packages, "execute", return_value=(result, {"contextDigest": "test"})):
            npm_metadata.resolve(self.root, "react", "19.2.8", self.evidence, path, 10)
        proof = json.loads(path.read_text())
        self.assertTrue(proof["satisfied"])
        self.assertEqual(proof["metadataSha256"], packages.canonical_hash(proof["metadata"]))


if __name__ == "__main__":
    unittest.main()

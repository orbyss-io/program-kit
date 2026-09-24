from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_sync_live_review import SCENARIO, prepare
from live.v2.sync_comparison import MATCHED_INPUTS, METRICS, compare, validated_report
from live.v2.sync_oracles import capture_consumer_edits, verify_consumer_edits, verify_future_targets, verify_codex_sync_commands
from live.v2.common import canonical_sha256


class LiveFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="program-kit-sync-review-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = json.loads((SCENARIO / "cases.json").read_text(encoding="utf-8"))

    def report(self, case_id, count):
        # Synthetic evidence exercises the comparator; it is never exported as live acceptance.
        directory = self.root / case_id
        directory.mkdir()
        evidence = directory / "synthetic-test-evidence.txt"
        evidence.write_text("UNIT TEST ONLY\n", encoding="utf-8")
        reference = {"path": evidence.name, "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}
        case = next(value for value in self.cases["cases"] if value["id"] == case_id)
        value = {
            "caseId": case_id, "status": "passed", "execution": "paid-live-v2",
            "bindings": {**dict.fromkeys(MATCHED_INPUTS, "same-test-binding"),
                         "releaseReceiptSha256": hashlib.sha256(case_id.encode()).hexdigest(), "checkpointDigest": "test-checkpoint"},
            **{key: reference for key in ("authorization", "workerStdout", "workerStderr", "independentValidation")},
            "assertions": {key: {"passed": True, "evidence": reference} for key in case["assertions"]},
            "metrics": {key: {"count": count, "rationale": "Synthetic comparator test", "evidence": [reference]} for key in METRICS},
        }
        def record(name, content):
            target = directory / name
            self.write(target, content)
            return {'path':name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        phase = 'upgrade-consumer' if case_id == 'upgrade-candidate' else 'feature-delivery'
        profile = {'integration':'codex','launcherVersion':'unit-test-only','model':'same-test-binding','reasoningEffort':'same-test-binding','sandbox':'workspace-write','timeoutSeconds':60}
        authorization = {'schemaVersion':'2.0','authorizationId':'00000000-0000-0000-0000-000000000001','nonce':'a'*64,
                         'phase':phase,'scenario':{'id':'unit-test-only','version':'1','digest':'a'*64},
                         'candidate':{'releaseReceipt':'unit-test-only','releaseReceiptSha256':value['bindings']['releaseReceiptSha256']},
                         'checkpoint':{'checkpointId':'unit-test-parent','digest':'b'*64},'agentProfile':profile,
                         'limits':{'maximumPaidSessions':1,'workerNetwork':'model-transport-only','restoreNetworkOwner':'supervisor'},
                         'issuedAt':'2000-01-01T00:00:00+00:00','expiresAt':'2000-01-01T00:01:00+00:00'}
        value['authorization'] = record('synthetic-consumed-authorization.json', authorization)
        checkpoint = {'schemaVersion':'2.0','status':'checkpoint-created','checkpointId':'unit-test-child','phase':phase,
                      'parent':'unit-test-parent','candidate':value['bindings']['releaseReceiptSha256'], 'scenario':'a'*64,
                      'expectation':'b'*64,'architectureMapSha256':'c'*64,'selectionSha256':'d'*64,'files':[],'createdAt':'2000-01-01'}
        value['checkpoint'] = record('synthetic-checkpoint.json', checkpoint)
        value['bindings']['checkpointDigest'] = value['checkpoint']['sha256']
        run = {'schemaVersion':'2.0','runId':'unit-test-only','phase':phase,'status':'checkpoint-created','causes':[],
               'authorization':{'authorizationId':authorization['authorizationId'],'authorizationSha256':canonical_sha256(authorization)},
               'candidate':authorization['candidate'],'scenario':authorization['scenario'],'agentProfile':profile,
               'process':{'exitCode':0,'cleanupComplete':True,'logsDrained':True},
               'logs':[{'object':{'sha256':reference['sha256']}}]*2, 'receipts':[],
               'workspace':'artifacts/live-v2-w/abcdef12','startedAt':'2000-01-01','finishedAt':'2000-01-01'}
        run['manifestSha256'] = canonical_sha256(run)
        value['liveRunManifest'] = record('synthetic-run.json',run)
        value['independentValidation'] = record('synthetic-independent.json',{'status':'passed','functionalAcceptance':True})
        path = directory / "report.json"
        self.write(path, value)
        return path, value

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_preparation_is_reproducible_and_never_authorization(self):
        first, second = prepare(), prepare()
        self.assertEqual(first, second)
        self.assertFalse(first["authorizationIssued"])
        self.assertEqual(first["paidSessionsStarted"], 0)
        self.assertEqual({case["id"] for case in first["cases"]}, {"fresh-baseline", "fresh-candidate", "upgrade-candidate"})
        self.assertEqual(first["stageRunner"], "scripts/Test-LiveRepositorySync.ps1")
        self.assertIn("functionalAcceptanceEvidence", first["unboundRequirements"])

    def test_preparation_binds_request_and_seed(self):
        import shutil
        scenario_root = self.root / "scenarios"
        fixture = scenario_root / "repository-sync/v1"
        seed = fixture / "bootstrap-seed"
        shutil.copytree(SCENARIO, fixture)
        before = prepare(fixture)["fixtureDigest"]
        (fixture / "PROJECT_REQUEST.md").write_text("changed feature", encoding="utf-8")
        changed = prepare(fixture)["fixtureDigest"]
        self.assertNotEqual(before, changed)
        (seed / "fixture/PROJECT_REQUEST.md").write_text("changed seed", encoding="utf-8")
        self.assertNotEqual(changed, prepare(fixture)["fixtureDigest"])

    def test_successful_matching_runs_report_actual_deltas(self):
        baseline, _ = self.report("fresh-baseline", 3)
        candidate, _ = self.report("fresh-candidate", 0)
        result = compare(baseline, candidate, self.cases)
        self.assertTrue(result["observedImprovement"])
        self.assertEqual(result["measurements"]["setupDiscoveryCommands"]["delta"], -3)

    def test_unknown_is_not_zero_or_improvement(self):
        baseline, _ = self.report("fresh-baseline", 3)
        candidate, value = self.report("fresh-candidate", 0)
        value["metrics"]["wrongRegistryRequests"]["count"] = None
        self.write(candidate, value)
        result = compare(baseline, candidate, self.cases)
        self.assertFalse(result["observedImprovement"])
        self.assertIsNone(result["measurements"]["wrongRegistryRequests"]["delta"])

    def test_failed_incomplete_unmatched_and_tampered_runs_cannot_claim_improvement(self):
        baseline, _ = self.report("fresh-baseline", 3)
        candidate, original = self.report("fresh-candidate", 0)
        for mutation in (
            lambda value: value.update(status="failed"),
            lambda value: value.update(execution="deterministic"),
            lambda value: value["assertions"].pop("strict-package-evidence"),
            lambda value: value["bindings"].update(model="different-model"),
            lambda value: value["metrics"]["setupFailures"].update(count=-1),
            lambda value: value["metrics"]["setupFailures"].update(evidence=[]),
        ):
            value = copy.deepcopy(original)
            mutation(value)
            self.write(candidate, value)
            with self.assertRaises(ValueError):
                compare(baseline, candidate, self.cases)
        self.write(candidate, original)
        (candidate.parent / "synthetic-test-evidence.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash changed"):
            compare(baseline, candidate, self.cases)

    def test_regression_is_visible_even_when_candidate_meets_zero_requirements(self):
        baseline, _ = self.report("fresh-baseline", 3)
        candidate, value = self.report("fresh-candidate", 0)
        value["metrics"]["humanInterventions"]["count"] = 4
        self.write(candidate, value)
        result = compare(baseline, candidate, self.cases)
        self.assertFalse(result["observedImprovement"])
        self.assertEqual(result["increasesRequiringReview"], ["humanInterventions"])

    def test_upgrade_requires_its_own_oracles(self):
        path, value = self.report("upgrade-candidate", 0)
        value["assertions"]["consumer-edits-preserved"]["passed"] = False
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, "consumer-edits-preserved"):
            validated_report(path, self.cases)

    def test_upgrade_oracle_detects_real_consumer_edit_loss(self):
        import shutil
        overlay = SCENARIO / "upgrade-overlay"
        project = self.root / "consumer"
        shutil.copytree(overlay, project)
        before = capture_consumer_edits(project, overlay)
        verify_consumer_edits(project, before)
        (project / "config/consumer-upgrade-marker.json").write_text('{}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "consumer-owned"):
            verify_consumer_edits(project, before)

    def test_future_target_oracle_detects_an_empty_scaffold_directory(self):
        verify_future_targets(self.root, SCENARIO / "future-targets.json")
        (self.root / "web/reporting").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "Future feature"):
            verify_future_targets(self.root, SCENARIO / "future-targets.json")

    def test_upgrade_command_oracle_requires_replacement_and_removal(self):
        with self.assertRaisesRegex(ValueError, "not installed"):
            verify_codex_sync_commands(self.root)
        skills = self.root / ".agents/skills"
        current = skills / "speckit-program-kit-governance-sync"
        current.mkdir(parents=True)
        (current / "SKILL.md").write_text("current", encoding="utf-8")
        verify_codex_sync_commands(self.root)
        (skills / "speckit-program-kit-dotnet-sync").mkdir()
        with self.assertRaisesRegex(ValueError, "Obsolete"):
            verify_codex_sync_commands(self.root)


if __name__ == "__main__":
    unittest.main()

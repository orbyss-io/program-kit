"""Offline contract and failure tests; never authenticates or calls a provider."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "extensions/program-kit-governance/scripts"))
import json_schema
from scripts.delivery_phase0 import contract as c, examples, schema
from scripts.delivery_phase0.providers import Store


class DeliveryContractTests(unittest.TestCase):
    def setUp(self):
        self.examples = examples.build()
        self.by_kind = {r["recordType"]: r for r in self.examples}
        self.schema = schema.build()
        self.state = {"claims": {}, "operations": {}}
        self.actor = {"providerId": "human", "accountableHumanId": "owner", "executionId": "worker-1"}
        self.basis = {"businessRevision": "v1", "profileRevision": "a" * 40}

    def validate(self, value):
        return json_schema.validate_value(value, self.schema)["valid"]

    def test_generated_contracts_and_all_examples(self):
        self.assertEqual(json.loads((ROOT / "docs/delivery/contracts.schema.json").read_text()), self.schema)
        self.assertEqual(json.loads((ROOT / "docs/delivery/examples.json").read_text()), self.examples)
        for example in self.examples:
            with self.subTest(kind=example["recordType"]):
                self.assertTrue(self.validate(example))
                c.validate_semantics(example)

    def test_disabled_has_no_provider_or_coordinator(self):
        self.assertTrue(self.validate(self.examples[0]))
        self.assertFalse(self.validate(dict(self.examples[0], provider="local")))

    def test_versions_credentials_and_unknown_fields_rejected(self):
        for changes in ({"schemaVersion": 2}, {"token": "not-a-secret"}, {"unexpected": "field"}):
            self.assertFalse(self.validate(dict(self.examples[1], **changes)))

    def test_provider_edition_and_profile_binding(self):
        profile, binding = self.examples[1:3]
        c.check_binding(profile, binding)
        with self.assertRaises(c.Conflict):
            c.check_binding(profile, dict(binding, profileRevision="b" * 40))
        with self.assertRaises(c.Conflict):
            c.validate_semantics(dict(profile, edition="github.com"))

    def test_approval_is_bound_to_both_payload_and_inputs(self):
        proposal = self.by_kind["proposal"]
        for changes in ({"payloadFingerprint": "new"}, {"inputFingerprint": "new"}, {"approval": None}):
            changed = dict(proposal, **changes)
            if changed["approval"] is None:
                changed.pop("approval")
            with self.assertRaises(c.Conflict):
                c.validate_semantics(changed)

    def test_incomplete_or_changed_observation_blocks_readiness(self):
        observed = self.by_kind["observation"]
        for field in observed["coverage"]:
            for status in ("unknown", "incomplete"):
                changed = deepcopy(observed)
                changed["coverage"][field] = status
                with self.assertRaises(c.Conflict):
                    c.validate_semantics(changed)
        with self.assertRaises(c.Conflict):
            c.validate_semantics(dict(observed, businessFingerprint="new-scope"))

    def test_provider_failure_fixtures_never_establish_presence(self):
        cases = json.loads((ROOT / "tests/fixtures/delivery-phase0-observations.json").read_text())
        for case in cases:
            self.assertEqual(c.observation_status(case["httpStatus"], case["complete"], case.get("deletionConfirmed", False)), case["expected"])

    def test_existing_claim_and_exclusive_resource_block_new_admission(self):
        state = c.admit(self.state, "A", self.actor, self.basis, ["db-migration"])
        for work in ("A", "B"):
            with self.assertRaises(c.Conflict):
                c.admit(state, work, dict(self.actor, executionId="worker-2"), self.basis, ["db-migration"])
        c.admit(state, "B", self.actor, self.basis, ["other-resource"])
        self.assertEqual(self.state, {"claims": {}, "operations": {}})

    def test_takeover_and_release_fence_old_sessions(self):
        first = c.admit(self.state, "A", self.actor, self.basis)
        with self.assertRaises(c.Conflict):
            c.admit(first, "A", self.actor, self.basis, takeover=True)
        second_actor = dict(self.actor, executionId="worker-2")
        second = c.admit(first, "A", second_actor, self.basis, takeover=True, authorized=True)
        with self.assertRaises(c.Conflict):
            c.checkpoint(second, "A", 1, "worker-1", self.basis)
        with self.assertRaises(c.Conflict):
            c.release(second, "A", 1, "worker-1", self.basis)
        released = c.release(second, "A", 2, "worker-2", self.basis)
        third = c.admit(released, "A", self.actor, self.basis)
        self.assertEqual(third["claims"]["A"]["generation"], 3)

    def test_changed_basis_stops_current_worker(self):
        state = c.admit(self.state, "A", self.actor, self.basis)
        with self.assertRaises(c.Conflict):
            c.checkpoint(state, "A", 1, "worker-1", dict(self.basis, businessRevision="v2"))

    def test_empty_search_does_not_authorize_recreate(self):
        operation = c.dispatch(dict(self.by_kind["operation"], state="prepared"))
        for complete in (True, False):
            unknown = c.recover(operation, [], complete)
            self.assertEqual(unknown["state"], "outcome_unknown")
            with self.assertRaises(c.Conflict):
                c.dispatch(unknown)

    def test_recovery_requires_unique_complete_matching_payload(self):
        operation = dict(self.by_kind["operation"], state="dispatched")
        matching = dict(operation, providerId="23")
        self.assertEqual(c.recover(operation, [matching], True)["state"], "applied")
        self.assertEqual(c.recover(operation, [matching], False)["state"], "outcome_unknown")
        self.assertEqual(c.recover(operation, [matching, dict(matching, providerId="24")], True)["state"], "conflict")
        self.assertEqual(c.recover(operation, [dict(matching, payloadFingerprint="human-edited")], True)["state"], "conflict")

    def test_upstream_closure_and_stale_evidence_do_not_clear_dependency(self):
        dep, evidence = self.by_kind["dependency"], self.by_kind["evidence"]
        self.assertFalse(c.evidence_satisfies(dep, [], "a" * 40, "v2"))
        self.assertTrue(c.evidence_satisfies(dep, [evidence], "a" * 40, "v2"))
        self.assertFalse(c.evidence_satisfies(dep, [evidence], "b" * 40, "v2"))
        self.assertFalse(c.evidence_satisfies(dep, [evidence], "a" * 40, "v3"))

    def footprint_pair(self):
        left = deepcopy(self.by_kind["footprint"])
        left.update(resources=[], generatedSources={})
        right = deepcopy(left)
        right["writePaths"] = ["src/payments/view.py"]
        return left, right

    def test_same_category_disjoint_files_remain_eligible(self):
        left, right = self.footprint_pair()
        self.assertEqual(c.compatibility(left, right)["verdict"], "no_known_conflict")

    def test_overlapping_files_are_advisory_and_generated_sources_count(self):
        left, right = self.footprint_pair()
        right["generatedSources"] = {"generated/client.py": left["writePaths"][0]}
        self.assertEqual(c.compatibility(left, right)["verdict"], "advisory")

    def test_cross_repo_incompatible_contract_requires_coordination(self):
        left, right = self.footprint_pair()
        right["repositoryId"] = "checkout-web"
        left["resources"] = [{"id": "payment-api", "mode": "change", "contractRevision": "v2"}]
        right["resources"] = [{"id": "payment-api", "mode": "read", "contractRevision": "v1"}]
        self.assertEqual(c.compatibility(left, right)["verdict"], "coordinate")

    def test_missing_stale_and_uncertain_globs_are_not_independent(self):
        left, right = self.footprint_pair()
        for changes in ({"coverage": "incomplete"}, {"baseCommit": "c" * 40}, {"writePaths": []}, {"writePaths": ["src/*/unknown?.py"]}):
            self.assertEqual(c.compatibility(left, dict(right, **changes))["verdict"], "unknown")

    def test_scope_expansion_reassesses_compatibility(self):
        left, right = self.footprint_pair()
        self.assertEqual(c.compatibility(left, right)["verdict"], "no_known_conflict")
        right["writePaths"].extend(left["writePaths"])
        right["basis"] = "observed"
        self.assertEqual(c.compatibility(left, right)["verdict"], "advisory")

    def test_unsafe_relative_paths_are_rejected(self):
        footprint = self.by_kind["footprint"]
        for path in ("../secret", "/absolute", "src/../../secret", "src\\secret", "C:/secret"):
            self.assertFalse(self.validate(dict(footprint, writePaths=[path])))

    def test_lagging_ref_read_does_not_erase_acknowledged_commit(self):
        import base64
        store = Store.__new__(Store)
        store.provider, store.prefix = "github", "/repos/synthetic/probe"
        store.journal = {"setup_id": "space"}
        store._acknowledged_head = "new"
        store.head = Mock(return_value="old")
        state = {"space": "space", "claims": {"A": "acknowledged"}}
        store.api = Mock()
        store.api.request.side_effect = [{"status": "behind"}, {"content": base64.b64encode(json.dumps(state).encode()).decode()}]
        head, value = store.read()
        self.assertEqual((head, value), ("new", state))
        self.assertIn("ref=new", store.api.request.call_args.args[1])

    def test_diverged_coordinator_history_blocks_writes(self):
        store = Store.__new__(Store)
        store.provider, store.prefix, store._acknowledged_head = "github", "/repos/synthetic/probe", "known"
        store.head = Mock(return_value="replacement")
        store.api = Mock()
        store.api.request.return_value = {"status": "diverged"}
        with self.assertRaises(RuntimeError):
            store.read()


if __name__ == "__main__":
    unittest.main()
